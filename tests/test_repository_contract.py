from pathlib import Path
import ast
import importlib.util
import os
import yaml

ROOT = Path(__file__).parents[1]
REMOVED = {'timescaledb','timescale-load','timescale-check','timescale-reports-init','logstash','elasticsearch','kibana'}


def test_remaining_services_and_donnees_mounts():
    compose = yaml.safe_load((ROOT/'compose.yaml').read_text())
    services = compose['services']
    assert not REMOVED.intersection(services)
    assert not (ROOT/'data').exists() and (ROOT/'donnees/input/sales.csv').is_file()
    for name, definition in services.items():
        assert set(definition.get('depends_on', {})) <= services.keys(), name
        for volume in definition.get('volumes', []):
            source = volume.split(':')[0]
            assert not source.startswith('./data')
            if source.startswith('./'):
                assert (ROOT/source).exists(), (name, source)
    for name in ['workspace-init','objectstore-init','file-producer','web-log-producer','mock-opendata']:
        assert any(v.startswith('./donnees:') for v in services[name]['volumes']), name
    assert 'donnees' in (ROOT/'.dockerignore').read_text().splitlines()


def test_portal_pgadmin_and_checks_match_remaining_stack(monkeypatch):
    monkeypatch.setenv('POSTGRES_DB','formation')
    monkeypatch.setenv('POSTGRES_USER','formation')
    monkeypatch.setenv('POSTGRES_PASSWORD','formation')
    for filename in ['dashboard/server.py','docker/bootstrap/pgadmin.py']:
        spec=importlib.util.spec_from_file_location('contract',ROOT/filename)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        if hasattr(module,'servers'):
            assert [s['Host'] for s in module.servers()['Servers'].values()] == ['postgres-source']
        else:
            html=module.render().decode()
            assert 'Trino' in html and 'Superset' in html
            assert not any(term in html.lower() for term in REMOVED)
    source=(ROOT/'checks/integration.py').read_text()
    ast.parse(source)
    assert not any(term in source.lower() for term in REMOVED)
    for function in ['verify_trino','verify_druid','verify_superset','kafka_roundtrip','s3_roundtrip']:
        assert 'def '+function+'(' in source
