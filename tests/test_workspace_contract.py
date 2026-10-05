"""Check the access policy on every consumer, including Airflow's driver."""
from pathlib import Path
import yaml


def test_workspace_access_and_dependency_contract():
    root = Path(__file__).parents[1]
    compose = yaml.safe_load((root / 'compose.yaml').read_text())
    services = compose['services']
    for name in ['spark-master', 'spark-worker-1', 'spark-worker-2', 'spark-history', 'spark-jupyter', 'integration-check', 'airflow', 'airflow-check']:
        service = services[name]
        readonly = name.startswith('airflow')
        for volume in ['spark-data:/opt/spark/data', 'spark-jobs:/opt/spark/jobs']:
            assert volume + (':ro' if readonly else '') in service['volumes'], name
        assert service['depends_on']['workspace-init']['condition'] == 'service_completed_successfully'
    assert services['integration-check']['user'] == 'spark'
    assert services['airflow-check']['user'] == 'airflow'
    assert './donnees:/seed/data:ro' in services['objectstore-init']['volumes']
    for dockerfile in ['spark/runtime/Dockerfile', 'docker/airflow/Dockerfile']:
        text = (root / dockerfile).read_text()
        for name in ['data', 'jobs']:
            assert f'ln -s /opt/spark/{name} /home/spark/{name}' in text
