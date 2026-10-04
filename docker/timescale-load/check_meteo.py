"""Read-only verification: extension, hypertable, manifest and every field of every row."""
import argparse
from datetime import datetime, timezone
from itertools import zip_longest
import json
from pathlib import Path
import sys
import time
from meteo import COLUMNS, SOURCE_NAME, connect, parquet_file, source_rows, source_sha256


def verify(path, source_name=SOURCE_NAME):
    started = time.monotonic()
    expected = parquet_file(path).metadata.num_rows
    digest = source_sha256(path)
    with connect() as conn:
        conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        conn.execute('SELECT pg_advisory_xact_lock_shared(hashtextextended(%s, 0))', (source_name,))
        extension = conn.execute("SELECT extversion FROM pg_extension WHERE extname = 'timescaledb'").fetchone()
        if not extension:
            raise RuntimeError('TimescaleDB extension missing')
        hypertable = conn.execute("SELECT count(*) FROM timescaledb_information.hypertables WHERE hypertable_schema = 'meteo' AND hypertable_name = 'observations'").fetchone()[0]
        if hypertable != 1:
            raise RuntimeError('meteo.observations is not a hypertable')
        manifest = conn.execute('SELECT source_sha256, row_count FROM meteo.ingestions WHERE source_name = %s', (source_name,)).fetchone()
        if manifest != (digest, expected):
            raise RuntimeError('Ingestion manifest does not match the source')
        summary = conn.execute('SELECT count(*), count(DISTINCT station), min(observed_at), max(observed_at) FROM meteo.observations WHERE source_name = %s', (source_name,)).fetchone()
        if summary[0] != expected:
            raise RuntimeError(f'Row count differs: expected={expected}, actual={summary[0]}')
        count = 0
        # Server-side cursor: comparison never materializes the entire database.
        with conn.cursor(name='verify_meteo') as cursor:
            cursor.itersize = 8192
            cursor.execute('SELECT source_row, source_sha256, ' + ', '.join(COLUMNS) + ' FROM meteo.observations WHERE source_name = %s ORDER BY source_row', (source_name,))
            for local, remote in zip_longest(source_rows(path), cursor):
                if local is None or remote is None:
                    raise RuntimeError('Incomplete source or database stream')
                ordinal, row = local
                if remote[0] != ordinal or remote[1] != digest or tuple(remote[2:]) != row:
                    raise RuntimeError(f'Content mismatch at source row {ordinal}')
                count += 1
        if count != expected or source_sha256(path) != digest:
            raise RuntimeError('Source changed during verification')
    return {'status': 'PASS', 'source': source_name, 'source_sha256': digest, 'rows_verified': count, 'columns_verified': len(COLUMNS), 'stations': summary[1], 'first_observation': summary[2].isoformat(), 'last_observation': summary[3].isoformat(), 'timescaledb_version': extension[0], 'seconds': round(time.monotonic() - started, 2)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', default='/data/meteo.gzip')
    parser.add_argument('--report', default='/reports/timescale-check.json')
    args = parser.parse_args()
    try:
        report = verify(args.source)
    except Exception as exc:
        report = {'status': 'FAIL', 'error': str(exc)}
    report['finished_at'] = datetime.now(timezone.utc).isoformat()
    # Print the result even when writing the report fails; failure must be non-zero.
    print(json.dumps(report, ensure_ascii=False), flush=True)
    try:
        destination = Path(args.report)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    except OSError as exc:
        print('REPORT_WRITE_FAIL ' + str(exc), file=sys.stderr)
        return 1
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
