"""Load the eBrasil silver dimensions and facts into Apache Druid."""
from __future__ import annotations

import json
import os
import sys
import time

import boto3
import requests
from botocore.config import Config

S3_BUCKET = "lakehouse"
MANIFEST_KEY = "silver/ebrasil/model-manifest.json"
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://objectstore:9000")
DRUID = os.getenv("DRUID_URL", "http://druid-router:8888")
S3 = boto3.client("s3", endpoint_url=S3_ENDPOINT,
    aws_access_key_id=os.getenv("S3_ACCESS_KEY", "labadmin"),
    aws_secret_access_key=os.getenv("S3_SECRET_KEY", "TRAINING_ONLY_S3_PASSWORD"),
    region_name=os.getenv("AWS_REGION", "us-east-1"),
    config=Config(signature_version="s3v4", s3={"addressing_style": "path"}))
HTTP = requests.Session()

def request(method, path, **kwargs):
    response = HTTP.request(method, DRUID + path, timeout=60, **kwargs)
    response.raise_for_status()
    return response

def wait_router():
    deadline = time.monotonic() + 600
    while True:
        try:
            request("GET", "/status/health")
            return
        except requests.RequestException:
            if time.monotonic() >= deadline:
                raise
            time.sleep(5)

def get_manifest():
    return json.loads(S3.get_object(Bucket=S3_BUCKET, Key=MANIFEST_KEY)["Body"].read())

def object_uris(table):
    prefix = f"silver/ebrasil/druid/{table}/"
    keys = []
    pager = S3.get_paginator("list_objects_v2")
    for page in pager.paginate(Bucket=S3_BUCKET, Prefix=prefix):
        keys.extend(item["Key"] for item in page.get("Contents", [])
                    if item["Key"].endswith(".json"))
    if not keys:
        raise RuntimeError(f"No Druid JSON input objects at s3://{S3_BUCKET}/{prefix}")
    return [f"s3://{S3_BUCKET}/{key}" for key in sorted(keys)]

def task_spec(table, definition):
    dimension_types = definition.get("dimension_types", {})
    dimensions = [
        {"type": dimension_types.get(name, "string"), "name": name}
        for name in definition["dimensions"]
    ]
    schema = {
        "dataSource": table,
        "timestampSpec": {"column": "event_ts", "format": "iso"},
        "dimensionsSpec": {"dimensions": dimensions},
        # These datasources are row-grain (rollup=false); aggregators here
        # would replace original numeric values with pre-aggregated values.
        "metricsSpec": [],
        "granularitySpec": {"type": "uniform", "segmentGranularity": "DAY",
                            "queryGranularity": "NONE", "rollup": False},
    }
    return {
        "type": "index_parallel",
        "id": f"ebrasil-{table}-{int(time.time())}",
        "spec": {
            "dataSchema": schema,
            "ioConfig": {"type": "index_parallel",
                         "inputSource": {"type": "s3", "uris": object_uris(table)},
                         "inputFormat": {"type": "json"},
                         "appendToExisting": False},
            "tuningConfig": {"type": "index_parallel", "maxNumConcurrentSubTasks": 1},
        },
    }

def wait_until_queryable(table, expected_rows, timeout_seconds=180):
    """Wait until the Broker can query all rows published by the indexing task."""
    deadline = time.monotonic() + timeout_seconds
    last_error = "No result returned"
    sql = f'SELECT COUNT(*) AS n FROM "{table}"'
    while True:
        try:
            result = request("POST", "/druid/v2/sql", json={"query": sql}).json()
            if result and int(result[0].get("n", -1)) == int(expected_rows):
                return
            actual = result[0].get("n") if result else "no rows"
            last_error = f"query returned {actual} rows; expected {expected_rows}"
        except requests.HTTPError as exc:
            response = exc.response
            if response is None or response.status_code not in (400, 503):
                raise
            last_error = f"HTTP {response.status_code}: {response.text[:1000]}"
        except requests.RequestException as exc:
            last_error = str(exc)
        if time.monotonic() >= deadline:
            raise TimeoutError(
                f"Druid datasource {table} was not queryable within "
                f"{timeout_seconds}s: {last_error}"
            )
        time.sleep(5)


def validate_fact_payment_dimensions():
    categories = request(
        "POST", "/druid/v2/sql",
        json={"query": 'SELECT payment_type, COUNT(*) AS n '
                       'FROM "fact_payment" GROUP BY payment_type'},
    ).json()
    values = {str(row.get("payment_type", "")).strip().lower() for row in categories}
    if len(values) < 2 or "aggregated" in values or "" in values:
        raise RuntimeError(
            "fact_payment lost its payment_type dimension: "
            f"expected multiple raw values, found {sorted(values)}"
        )

    numeric = request(
        "POST", "/druid/v2/sql",
        json={"query": 'SELECT MIN(installments) AS min_installments, '
                       'MAX(payment_value) AS max_payment_value '
                       'FROM "fact_payment"'},
    ).json()
    if not numeric or numeric[0].get("min_installments") is None \
            or numeric[0].get("max_payment_value") is None:
        raise RuntimeError(
            "fact_payment numeric dimensions installments/payment_value "
            "are not queryable"
        )


def ingest_table(table, definition):
    if table == "fact_payment":
        required = {"payment_type", "installments", "payment_value"}
        missing = required - set(definition["dimensions"])
        if missing:
            raise RuntimeError(
                f"fact_payment manifest is missing raw dimensions: {sorted(missing)}"
            )
    body = task_spec(table, definition)
    task_id = request("POST", "/druid/indexer/v1/task", json=body).json()["task"]
    deadline = time.monotonic() + 1800
    while True:
        status = request("GET", f"/druid/indexer/v1/task/{task_id}/status").json()
        state = status.get("status", {}).get("status")
        if state == "SUCCESS":
            wait_until_queryable(table, definition["rows"])
            if table == "fact_payment":
                validate_fact_payment_dimensions()
            print(f"DRUID_EBRASIL_TABLE_OK datasource={table} rows={definition['rows']}", flush=True)
            return
        if state == "FAILED":
            details = request("GET", f"/druid/indexer/v1/task/{task_id}/reports").text
            raise RuntimeError(f"Druid ingestion failed for {table}: {details[:4000]}")
        if time.monotonic() >= deadline:
            raise TimeoutError(f"Druid task timed out: {task_id} datasource={table}")
        time.sleep(5)

def main():
    wait_router()
    model = get_manifest()
    for table, definition in model["tables"].items():
        ingest_table(table, definition)
    print(f"DRUID_EBRASIL_MODEL_OK datasources={len(model['tables'])}", flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"DRUID_EBRASIL_INIT_FAIL: {exc}", file=sys.stderr, flush=True)
        raise
