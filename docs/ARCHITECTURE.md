# Architecture

Sources de `donnees` (CSV, JSON, XLSX, PostgreSQL, OpenData, logs) → producteurs → Kafka → Spark → Parquet / Delta / Iceberg sur RustFS S3 → Trino → Superset.

Airflow orchestre les jobs Spark. Druid ingère les ventes depuis Kafka et S3 ; il utilise PostgreSQL pour ses métadonnées, ZooKeeper pour sa coordination et RustFS pour ses segments. Superset interroge PostgreSQL, Trino et Druid. pgAdmin administre PostgreSQL, Kafka UI expose les topics et Jupyter permet les exercices Spark. Le portail regroupe leurs interfaces.

Voir [INTEGRATION_MATRIX.md](INTEGRATION_MATRIX.md) pour les preuves de chaque flux.
