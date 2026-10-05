import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from confluent_kafka import Producer

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:19092")
DATA_DIR = Path(os.getenv("DATA_DIR", "/data/input"))
delivery_errors = []
delivered = 0

def on_delivery(error, message):
    global delivered
    if error:
        delivery_errors.append(str(error))
    else:
        delivered += 1

producer = Producer({
    "bootstrap.servers": BOOTSTRAP,
    "acks": "all",
    "enable.idempotence": True,
    "retries": 10,
    "delivery.timeout.ms": 45000,
})


def publish(topic, record, key=None):
    payload = json.dumps(record, ensure_ascii=False, default=str).encode("utf-8")
    while True:
        try:
            producer.produce(topic, key=key, value=payload, on_delivery=on_delivery)
            producer.poll(0)
            return
        except BufferError:
            producer.poll(0.2)


def log(message, **extra):
    publish("application.logs", {
        "@timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "file-producer",
        "level": "INFO",
        "message": message,
        **extra,
    })


sales = pd.read_csv(DATA_DIR / "sales.csv")
for row in sales.to_dict(orient="records"):
    row["ingested_at"] = datetime.now(timezone.utc).isoformat()
    row["source_format"] = "csv"
    publish("sales.raw", row, str(row.get("sale_id", "")))
log("CSV sales published", record_count=len(sales))

customers = pd.read_json(DATA_DIR / "customers.json")
for row in customers.to_dict(orient="records"):
    row["ingested_at"] = datetime.now(timezone.utc).isoformat()
    row["source_format"] = "json"
    publish("customers.raw", row, str(row.get("customer_id", "")))
log("JSON customers published", record_count=len(customers))

catalog = pd.read_excel(DATA_DIR / "catalog.xlsx")
for row in catalog.to_dict(orient="records"):
    row["ingested_at"] = datetime.now(timezone.utc).isoformat()
    row["source_format"] = "xlsx"
    publish("catalog.raw", row, str(row.get("product_id", "")))
log("XLSX catalog published", record_count=len(catalog))

pending = producer.flush(60)
if pending or delivery_errors:
    raise RuntimeError(f"Kafka delivery failed: delivered={delivered}, pending={pending}, errors={delivery_errors[:10]}; inspect kafka partition leaders and broker logs")
print(f"FILE_PRODUCER_OK sales={len(sales)} customers={len(customers)} catalog={len(catalog)}")
