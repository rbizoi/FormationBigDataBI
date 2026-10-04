"""Atomic batch COPY into a TimescaleDB hypertable; repeat runs replace this source only."""
import argparse
import json
import sys
import time
from meteo import COLUMNS, SOURCE_NAME, connect, create_schema, parquet_file, source_rows, source_sha256


def load(path, source_name=SOURCE_NAME):
    started = time.monotonic()
    count = parquet_file(path).metadata.num_rows
    digest = source_sha256(path)
    with connect() as conn:
        conn.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))', (source_name,))
        create_schema(conn)
        conn.execute('CREATE TEMP TABLE incoming (LIKE meteo.observations) ON COMMIT DROP')
        columns = ', '.join(COLUMNS + ['source_name', 'source_sha256', 'source_row'])
        with conn.cursor().copy('COPY incoming (' + columns + ') FROM STDIN') as copy:
            for ordinal, row in source_rows(path):
                copy.write_row(row + (source_name, digest, ordinal))
                if (ordinal + 1) % 250000 == 0:
                    print(f'COPY_PROGRESS rows={ordinal + 1}/{count}', flush=True)
        loaded = conn.execute('SELECT count(*) FROM incoming').fetchone()[0]
        if loaded != count or source_sha256(path) != digest:
            raise RuntimeError('Source file changed or COPY is incomplete')
        # Scoped replacement preserves other imports/manual records and is transactional.
        conn.execute('DELETE FROM meteo.observations WHERE source_name = %s', (source_name,))
        conn.execute('INSERT INTO meteo.observations (' + columns + ') SELECT ' + columns + ' FROM incoming')
        conn.execute('INSERT INTO meteo.ingestions (source_name, source_sha256, row_count) VALUES (%s, %s, %s) ON CONFLICT (source_name) DO UPDATE SET source_sha256 = EXCLUDED.source_sha256, row_count = EXCLUDED.row_count, loaded_at = now()', (source_name, digest, count))
        conn.execute('ANALYZE meteo.observations')
    return {'status': 'PASS', 'source': source_name, 'source_sha256': digest, 'rows': count, 'seconds': round(time.monotonic() - started, 2)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', default='/data/meteo.gzip')
    args = parser.parse_args()
    try:
        print('TIMESCALE_LOAD_OK ' + json.dumps(load(args.source), ensure_ascii=False))
        return 0
    except Exception as exc:
        print('TIMESCALE_LOAD_FAIL ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
