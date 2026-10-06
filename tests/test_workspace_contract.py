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
        for volume in ['spark-data:/opt/spark/donnees', 'spark-jobs:/opt/spark/jobs']:
            assert volume + (':ro' if readonly else '') in service['volumes'], name
        assert service['depends_on']['workspace-init']['condition'] == 'service_completed_successfully'
    assert services['integration-check']['user'] == 'spark'
    assert services['airflow-check']['user'] == 'airflow'
    assert './donnees:/seed/data:ro' in services['objectstore-init']['volumes']
    assert './donnees:/seed/donnees:ro' in services['workspace-init']['volumes']
    for dockerfile in ['spark/runtime/Dockerfile', 'docker/airflow/Dockerfile']:
        text = (root / dockerfile).read_text()
        for name in ['donnees', 'jobs']:
            assert f'ln -s /opt/spark/{name} /home/spark/{name}' in text


def test_spark_donnees_path_is_consistent_in_scripts_and_notebooks():
    root = Path(__file__).parents[1]
    old_opt = '/opt/spark/' + 'data'
    old_home = '/home/spark/' + 'data'
    files = [*root.rglob('*.py'), *root.rglob('*.ipynb'), *root.rglob('*.md')]
    files += [root / 'compose.yaml', root / 'spark/runtime/Dockerfile', root / 'docker/airflow/Dockerfile']
    for path in files:
        if not path.is_file():
            continue
        text = path.read_text(encoding='utf-8')
        assert old_opt not in text, f'old Spark data path in {path.relative_to(root)}'
        assert old_home not in text, f'old Spark home data path in {path.relative_to(root)}'
    compose = yaml.safe_load((root / 'compose.yaml').read_text())
    services = compose['services']
    assert './donnees:/seed/donnees:ro' in services['workspace-init']['volumes']
    assert 'spark-data:/opt/spark/donnees' in services['spark-master']['volumes']
