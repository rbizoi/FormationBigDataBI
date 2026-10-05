import importlib.util
from pathlib import Path
import re
import yaml

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location('port_check', ROOT / 'docker/ports-check/check_ports.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_duplicates_and_interface_overlap():
    a = {'service': 'a', 'host_ip': '127.0.0.1', 'published': 25001, 'target': 80, 'protocol': 'tcp'}
    b = dict(a, service='b', host_ip='0.0.0.0')
    assert module.duplicate_errors([a, b])
    assert not module.duplicate_errors([a, dict(b, protocol='udp')])
    assert not module.duplicate_errors([a, dict(b, published=25002)])


def test_skip_only_own_matching_service():
    a = {'service': 'dashboard', 'host_ip': '127.0.0.1', 'published': 25021, 'target': 8090, 'protocol': 'tcp'}
    own = dict(a, project='bigdata-training', container='dashboard')
    assert module.owner(a, [own], 'bigdata-training')['status'] == 'ALREADY_RUNNING'
    assert module.owner(a, [dict(own, project='old-training')], 'bigdata-training')['status'] == 'FAIL'
    assert module.owner(a, [dict(own, service='other')], 'bigdata-training')['status'] == 'FAIL'
    assert module.owner(a, [], 'bigdata-training') is None


def test_all_22_default_and_env_ports_are_unique_and_guarded():
    compose = yaml.safe_load((ROOT / 'compose.yaml').read_text())
    planned = dict(line.split('=', 1) for line in (ROOT / 'ports.env').read_text().splitlines() if line and not line.startswith('#'))
    assert len(planned) == 22 and len(set(planned.values())) == 22
    rows = []
    for name, definition in compose['services'].items():
        for published in definition.get('ports', []):
            match = re.fullmatch(r'127\.0\.0\.1:\$\{(\w+):-(\d+)\}:(\d+)', published)
            assert match, published
            key, port, target = match.groups()
            assert planned[key] == port
            assert definition['depends_on']['ports-check']['condition'] == 'service_completed_successfully'
            rows.append({'service': name, 'host_ip': '127.0.0.1', 'published': int(port), 'target': int(target), 'protocol': 'tcp'})
    assert len(rows) == 22 and not module.duplicate_errors(rows)
