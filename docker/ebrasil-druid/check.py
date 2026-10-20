"""Verify the eBrasil bronze copy, silver model and Druid datasources."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import sys

import boto3
import requests
from botocore.config import Config

BUCKET = "lakehouse"
ENDPOINT = os.getenv("S3_ENDPOINT", "http://objectstore:9000")
DRUID = os.getenv("DRUID_URL", "http://druid-router:8888")
S3 = boto3.client("s3", endpoint_url=ENDPOINT,
    aws_access_key_id=os.getenv("S3_ACCESS_KEY", "labadmin"),
    aws_secret_access_key=os.getenv("S3_SECRET_KEY", "TRAINING_ONLY_S3_PASSWORD"),
    region_name=os.getenv("AWS_REGION", "us-east-1"),
    config=Config(signature_version="s3v4", s3={"addressing_style": "path"}))
HTTP = requests.Session()

def check_bronze():
    manifest = json.loads(S3.get_object(Bucket=BUCKET,
        Key="bronze/ebrasil/_manifest.json")["Body"].read())
    if len(manifest) != 8:
        raise AssertionError(f"Expected 8 bronze source files, found {len(manifest)}")
    for filename, expected in manifest.items():
        body = S3.get_object(Bucket=BUCKET, Key=f"bronze/ebrasil/{filename}")["Body"]
        digest = hashlib.file_digest(body, "sha256").hexdigest()
        body.close()
        if digest != expected["sha256"]:
            raise AssertionError(f"Bronze SHA-256 mismatch: {filename}")
    detail = S3.list_objects_v2(Bucket=BUCKET,
        Prefix="bronze/ebrasil/payments_detail/").get("Contents", [])
    if not any(item["Key"].endswith(".parquet") for item in detail):
        raise AssertionError("Missing detailed payment Parquet dataset in bronze")
    print(f"EBRASIL_BRONZE_CHECK_OK files={len(manifest)} payment_detail_parquet=present")

def query(sql):
    response = HTTP.post(DRUID + "/druid/v2/sql",
                         json={"query": sql}, timeout=120)
    if not response.ok:
        raise RuntimeError(
            f"Druid SQL HTTP {response.status_code}: {response.text[:2000]}"
        )
    return response.json()

def source_payment_row_count():
    body = S3.get_object(Bucket=BUCKET,
        Key="donnees/ebrasil/olist_order_payments_dataset.csv")["Body"]
    try:
        reader = csv.DictReader(io.TextIOWrapper(body, encoding="utf-8"))
        return sum(1 for _ in reader)
    finally:
        body.close()


def check_silver_and_druid():
    model = json.loads(S3.get_object(Bucket=BUCKET,
        Key="silver/ebrasil/model-manifest.json")["Body"].read())
    tables = model["tables"]
    expected_tables = {
        "fact_order_item", "fact_order", "fact_payment",
        "fact_logistics", "fact_review", "mart_customer_rfm",
    }
    if set(tables) != expected_tables:
        raise AssertionError(
            f"Expected the six denormalized star tables, found {sorted(tables)}")
    payment_dimensions = set(tables["fact_payment"]["dimensions"])
    if "payment_sequential" not in payment_dimensions:
        raise AssertionError("fact_payment is missing payment_sequential")
    for table, definition in tables.items():
        prefix = f"silver/ebrasil/{table}/"
        objects = S3.list_objects_v2(Bucket=BUCKET, Prefix=prefix).get("Contents", [])
        parquet = [x for x in objects if x["Key"].endswith(".parquet")]
        if not parquet:
            raise AssertionError(f"No silver Parquet part file for {table}")
        rows = query(f'SELECT COUNT(*) AS n FROM "{table}"')[0]["n"]
        if int(rows) != int(definition["rows"]):
            raise AssertionError(
                f"Druid row count mismatch for {table}: {rows} != {definition['rows']}")
    expected_payments = source_payment_row_count()
    actual_payments = int(query('SELECT COUNT(*) AS n FROM "fact_payment"')[0]["n"])
    if actual_payments != expected_payments:
        raise AssertionError(
            f"fact_payment row count mismatch: {actual_payments} != source CSV {expected_payments}"
        )
    duplicate_keys = query(
        'SELECT order_id, payment_sequential, COUNT(*) AS n '
        'FROM "fact_payment" GROUP BY order_id, payment_sequential '
        'HAVING COUNT(*) > 1 LIMIT 1'
    )
    if duplicate_keys:
        raise AssertionError(
            f"fact_payment contains duplicate (order_id, payment_sequential): {duplicate_keys[0]}"
        )
    print(
        f"EBRASIL_SILVER_DRUID_CHECK_OK tables={len(tables)} "
        f"fact_payment_rows={actual_payments}"
    )

def main():
    check_bronze()
    check_silver_and_druid()
    print("EBRASIL_ALL_CHECKS_OK")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"EBRASIL_CHECK_FAIL: {exc}", file=sys.stderr, flush=True)
        raise
