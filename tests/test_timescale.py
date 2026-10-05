"""Parquet edge cases plus optional real TimescaleDB load/reload/corruption tests."""
from datetime import datetime, timezone
import importlib.util
import os
from pathlib import Path
import sys

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

APP = Path(__file__).parents[1] / 'docker/timescale-load'
sys.path.insert(0, str(APP))
from meteo import FIELDS, connect, normalize, parquet_file, source_rows
from load_meteo import load
from check_meteo import verify
from diagnose_meteo import diagnose


def fixture_file(path):
    values = {}
    for parquet_name, sql_name, kind in FIELDS:
        if sql_name == 'station':
            values[parquet_name] = ['07005', '07005', '07005']
        elif sql_name == 'observed_at':
            # Same station/time twice is deliberate: no silent loss of duplicates.
            values[parquet_name] = [datetime(2020, 1, 1), datetime(2020, 1, 1), datetime(2020, 2, 1)]
        elif kind == 'text':
            values[parquet_name] = ['Été "test"\nA', None, 'nuit']
        elif kind == 'double precision':
            values[parquet_name] = [1.125, None, float('nan')]
        else:
            values[parquet_name] = [1, None, 202001]
    pq.write_table(pa.table(values), path, compression='gzip')
    return path


def test_preserve_rows_station_text_nulls_and_utc(tmp_path):
    path = fixture_file(tmp_path / 'meteo.gzip')
    rows = list(source_rows(path, batch_size=1))
    assert parquet_file(path).metadata.num_rows == 3
    assert [ordinal for ordinal, _ in rows] == [0, 1, 2]
    assert rows[0][1][0] == '07005'
    assert rows[0][1][1] == datetime(2020, 1, 1, tzinfo=timezone.utc)
    assert rows[0][1][2] == 'Été "test"\nA'
    assert rows[0][1][:2] == rows[1][1][:2]
    assert rows[1][1][3] is None and rows[2][1][3] is None


def test_reject_invalid_schema_and_keys(tmp_path):
    path = tmp_path / 'invalid.gzip'
    pq.write_table(pa.table({'Station': ['07005']}), path)
    with pytest.raises(ValueError, match='Unexpected Parquet'):
        list(source_rows(path))
    good = list(source_rows(fixture_file(tmp_path / 'good.gzip')))[0][1]
    with pytest.raises(ValueError, match='Station'):
        normalize((None,) + good[1:])
    with pytest.raises(ValueError, match='DateHeure'):
        normalize((good[0], None) + good[2:])
    with pytest.raises(ValueError, match='Infinite'):
        normalize(good[:3] + (float('inf'),) + good[4:])


@pytest.mark.skipif(os.getenv('TIMESCALE_INTEGRATION_TEST') != '1', reason='Requires a live TimescaleDB server')
def test_live_reload_corruption_and_rollback(tmp_path):
    path = fixture_file(tmp_path / 'meteo.gzip')
    other = fixture_file(tmp_path / 'other.gzip')
    source = 'pytest/test_meteo.gzip'
    other_source = 'pytest/other.gzip'
    try:
        assert load(path, source)['rows'] == 3
        assert verify(path, source)['rows_verified'] == 3
        assert diagnose()['status'] == 'PASS'
        assert load(path, source)['rows'] == 3
        assert verify(path, source)['rows_verified'] == 3
        load(other, other_source)
        # Detect a value error even though total row count is unchanged.
        with connect() as conn:
            conn.execute('UPDATE meteo.observations SET temperature = 999 WHERE source_name = %s AND source_row = 0', (source,))
        with pytest.raises(RuntimeError, match='Content mismatch'):
            verify(path, source)
        load(path, source)
        assert verify(path, source)['rows_verified'] == 3
        # Invalid input must roll back the import, preserving the last valid dataset.
        values = pq.read_table(path).to_pydict()
        values['Station'][1] = None
        invalid = tmp_path / 'invalid.gzip'
        pq.write_table(pa.table(values), invalid)
        with pytest.raises(ValueError, match='Station'):
            load(invalid, source)
        assert verify(path, source)['rows_verified'] == 3
        assert verify(other, other_source)['rows_verified'] == 3
    finally:
        with connect() as conn:
            conn.execute('DELETE FROM meteo.observations WHERE source_name IN (%s, %s)', (source, other_source))
            conn.execute('DELETE FROM meteo.ingestions WHERE source_name IN (%s, %s)', (source, other_source))


def test_portal_and_pgadmin_share_timescale_configuration(monkeypatch):
    import yaml
    root = Path(__file__).parents[1]
    services = yaml.safe_load((root / 'compose.yaml').read_text())['services']
    for name, value in services['dashboard']['environment'].items():
        default = value.split(':-', 1)[1][:-1] if value.startswith('${') else value
        monkeypatch.setenv(name, default)
    monkeypatch.setenv('TIMESCALE_DB', 'weather_custom')
    monkeypatch.setenv('TIMESCALE_USER', 'learner')
    spec = importlib.util.spec_from_file_location('timescale_portal', root / 'dashboard/server.py')
    portal = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(portal)
    html = portal.render().decode()
    assert 'TimescaleDB météo' in html and 'timescaledb:5432' in html
    assert 'weather_custom' in html and 'learner' in html
    spec = importlib.util.spec_from_file_location('pgadmin_servers', root / 'docker/bootstrap/pgadmin.py')
    pgadmin = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pgadmin)
    server = pgadmin.servers()['Servers']['2']
    assert server['Host'] == 'timescaledb' and server['Port'] == 5432
    assert server['MaintenanceDB'] == 'weather_custom'
    assert server['Username'] == 'learner'
    assert services['timescale-check']['environment'] == services['timescale-load']['environment']
    assert './data/meteo.gzip:/data/meteo.gzip:ro' in services['timescale-load']['volumes']
    assert 'full' in services['timescale-load']['profiles']
