"""Fast read-only diagnosis; run check_meteo.py for exhaustive Parquet comparison."""
import json
from meteo import connect


def diagnose():
    with connect() as conn:
        conn.execute('SET TRANSACTION READ ONLY')
        database, user = conn.execute('SELECT current_database(), current_user').fetchone()
        databases = [row[0] for row in conn.execute('SELECT datname FROM pg_database WHERE NOT datistemplate ORDER BY datname')]
        result = {'database': database, 'user': user, 'databases': databases,
                  'table': 'meteo.observations', 'pgadmin_path': f'Databases > {database} > Schemas > meteo > Tables > observations'}
        exists = conn.execute("SELECT to_regclass('meteo.observations')").fetchone()[0]
        if not exists:
            result.update(status='FAIL', error='Météo table absent: run timescale-load and inspect its exit status/logs')
            return result
        rows, stations, first, last = conn.execute('SELECT count(*), count(DISTINCT station), min(observed_at), max(observed_at) FROM meteo.observations').fetchone()
        result.update(rows=rows, stations=stations, first_observation=str(first), last_observation=str(last))
        extension = conn.execute("SELECT extversion FROM pg_extension WHERE extname='timescaledb'").fetchone()
        hypertable = bool(extension) and bool(conn.execute("SELECT 1 FROM timescaledb_information.hypertables WHERE hypertable_schema='meteo' AND hypertable_name='observations'").fetchone())
        result.update(timescaledb_version=extension[0] if extension else None, hypertable=hypertable,
                      status='PASS' if rows and hypertable else 'FAIL')
        return result


if __name__ == '__main__':
    try:
        report = diagnose()
    except Exception as exc:
        report = {'status': 'FAIL', 'error': str(exc)}
    print(json.dumps(report, ensure_ascii=False))
    raise SystemExit(0 if report['status'] == 'PASS' else 1)
