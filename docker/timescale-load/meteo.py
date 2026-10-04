"""Shared Parquet contract. All 24 fields are preserved; dates are interpreted as UTC."""
from datetime import timezone
import hashlib
import math
import os
from pathlib import Path

import psycopg
import pyarrow.parquet as pq

# Parquet names, SQL names, SQL types. Station is text to preserve leading zeros.
FIELDS = [
    ('Station', 'station', 'text'),
    ('DateHeure', 'observed_at', 'timestamptz'),
    ('Nom', 'station_name', 'text'),
    ('Latitude', 'latitude', 'double precision'),
    ('Longitude', 'longitude', 'double precision'),
    ('Altitude', 'altitude', 'integer'),
    ('Zone', 'zone', 'text'),
    ('DirectionVent', 'wind_direction', 'double precision'),
    ('VitesseVent', 'wind_speed', 'double precision'),
    ('Temperature', 'temperature', 'double precision'),
    ('Humidite', 'humidity', 'double precision'),
    ('Visibilite', 'visibility', 'double precision'),
    ('Pression', 'pressure', 'double precision'),
    ('Precipitation', 'precipitation', 'double precision'),
    ('Heure', 'hour', 'integer'),
    ('Jour', 'day', 'integer'),
    ('Mois', 'month', 'integer'),
    ('Annee', 'year', 'integer'),
    ('Semaine', 'week', 'integer'),
    ('MoisJour', 'month_day', 'integer'),
    ('AnneeMois', 'year_month', 'integer'),
    ('AnneeSemaine', 'year_week', 'bigint'),
    ('AnneeJour', 'year_day', 'integer'),
    ('JourNuit', 'day_night', 'text'),
]
COLUMNS = [name for _, name, _ in FIELDS]
SOURCE_NAME = 'data/meteo.gzip'


def source_sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def parquet_file(path):
    # The suffix .gzip describes internal Parquet compression, not a gzip archive.
    file = pq.ParquetFile(path)
    expected = {name for name, _, _ in FIELDS}
    if set(file.schema_arrow.names) != expected:
        raise ValueError(f'Unexpected Parquet columns: {file.schema_arrow.names}')
    if not file.metadata.num_rows:
        raise ValueError('Empty Parquet file')
    return file


def normalize(values):
    row = list(values)
    if row[0] is None or not isinstance(row[0], str) or not row[0].strip():
        raise ValueError('Station must be a non-empty string')
    if row[1] is None:
        raise ValueError('DateHeure must not be NULL')
    row[1] = row[1].replace(tzinfo=timezone.utc) if row[1].tzinfo is None else row[1].astimezone(timezone.utc)
    for index, value in enumerate(row):
        if isinstance(value, float):
            if math.isnan(value):
                row[index] = None
            elif not math.isfinite(value):
                raise ValueError(f'Infinite value in {FIELDS[index][0]}')
    return tuple(row)


def source_rows(path, batch_size=8192):
    file = parquet_file(path)
    ordinal = 0
    for batch in file.iter_batches(batch_size=batch_size, columns=[p for p, _, _ in FIELDS]):
        columns = [column.to_pylist() for column in batch.columns]
        for values in zip(*columns):
            yield ordinal, normalize(values)
            ordinal += 1


def connect():
    return psycopg.connect(
        host=os.getenv('PGHOST', 'timescaledb'),
        port=int(os.getenv('PGPORT', '5432')),
        dbname=os.getenv('PGDATABASE', 'meteo'),
        user=os.getenv('PGUSER', 'meteo'),
        password=os.getenv('PGPASSWORD', 'formation'),
        connect_timeout=15,
        options='-c timezone=UTC',
    )


def create_schema(conn):
    conn.execute('CREATE EXTENSION IF NOT EXISTS timescaledb')
    conn.execute('CREATE SCHEMA IF NOT EXISTS meteo')
    definitions = ', '.join(name + ' ' + kind + (' NOT NULL' if name in ('station', 'observed_at') else '') for _, name, kind in FIELDS)
    conn.execute('CREATE TABLE IF NOT EXISTS meteo.observations (' + definitions + ', source_name text NOT NULL, source_sha256 text NOT NULL, source_row bigint NOT NULL, PRIMARY KEY (observed_at, source_name, source_row))')
    # The generalized API works on the pinned TimescaleDB release.
    conn.execute("SELECT create_hypertable('meteo.observations', by_range('observed_at', INTERVAL '1 month'), if_not_exists => TRUE)")
    conn.execute('CREATE INDEX IF NOT EXISTS observations_source_row ON meteo.observations (source_name, source_row)')
    conn.execute('CREATE INDEX IF NOT EXISTS observations_station_time ON meteo.observations (station, observed_at DESC)')
    conn.execute('CREATE TABLE IF NOT EXISTS meteo.ingestions (source_name text PRIMARY KEY, source_sha256 text NOT NULL, row_count bigint NOT NULL, loaded_at timestamptz NOT NULL DEFAULT now())')
