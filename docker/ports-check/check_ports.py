"""Check resolved Compose ports through the same Docker engine that will publish them."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import uuid


def docker(*args, check=True):
    result = subprocess.run(['docker', *args], text=True, capture_output=True, timeout=180)
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result


def bindings(config):
    rows = []
    for service, definition in config['services'].items():
        for port in definition.get('ports', []):
            if not isinstance(port, dict):
                raise ValueError('Use normalized docker compose config JSON')
            published = str(port.get('published', ''))
            if not published.isdigit() or not 1 <= int(published) <= 65535:
                raise ValueError(f'{service}: fixed host port required: {published}')
            rows.append({'service': service, 'host_ip': port.get('host_ip', '0.0.0.0'), 'published': int(published), 'target': int(port['target']), 'protocol': port.get('protocol', 'tcp')})
    return rows


def overlaps(a, b):
    return a == b or a in ('', '0.0.0.0', '::') or b in ('', '0.0.0.0', '::')


def duplicate_errors(rows):
    errors = []
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            if a['published'] == b['published'] and a['protocol'] == b['protocol'] and overlaps(a['host_ip'], b['host_ip']):
                errors.append(f"{a['service']} / {b['service']}: duplicate {a['published']}/{a['protocol']}")
    return errors


def running_bindings():
    ids = docker('ps', '-q').stdout.split()
    containers = json.loads(docker('inspect', *ids).stdout) if ids else []
    rows = []
    for container in containers:
        labels = container.get('Config', {}).get('Labels') or {}
        for target, values in (container.get('NetworkSettings', {}).get('Ports') or {}).items():
            internal, protocol = target.split('/')
            for value in values or []:
                rows.append({'host_ip': value['HostIp'], 'published': int(value['HostPort']), 'target': int(internal), 'protocol': protocol, 'project': labels.get('com.docker.compose.project'), 'service': labels.get('com.docker.compose.service'), 'container': container['Name'].lstrip('/')})
    return rows


def owner(row, running, project):
    matches = [r for r in running if r['published'] == row['published'] and r['protocol'] == row['protocol'] and overlaps(r['host_ip'], row['host_ip'])]
    if not matches:
        return None
    if all(r['project'] == project and r['service'] == row['service'] and r['target'] == row['target'] for r in matches):
        return {'status': 'ALREADY_RUNNING', 'detail': ', '.join(r['container'] for r in matches)}
    return {'status': 'FAIL', 'detail': 'Occupied by ' + ', '.join(r['container'] + ' (project=' + str(r['project']) + ')' for r in matches)}


def probe(row):
    # A bind inside this checker would examine its own container, not the host.
    # Ask the engine to publish a disposable container instead (Desktop included).
    name = 'formation-port-probe-' + uuid.uuid4().hex
    published = f"{row['host_ip']}:{row['published']}:1/{row['protocol']}"
    try:
        result = docker('run', '--rm', '--name', name, '--label', 'formation.port-probe=1', '--read-only', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--publish', published, 'alpine:3.22.5', 'true', check=False)
        return {'status': 'FREE' if result.returncode == 0 else 'FAIL', 'detail': 'Engine publication succeeded' if result.returncode == 0 else result.stderr.strip()}
    finally:
        # Only this UUID-named probe is removed, even after a failed publication.
        docker('rm', '-f', name, check=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--services', nargs='*', help='Limit live probes; all configured duplicates are still checked')
    parser.add_argument('--report', default='/reports/ports-check.json')
    args = parser.parse_args()
    report = {'status': 'FAIL', 'results': [], 'errors': []}
    try:
        command = ['compose', '--project-directory', '/project', '-f', '/project/compose.yaml', '--profile', 'full', 'config', '--format', 'json']
        config = json.loads(docker(*command).stdout)
        report['project'] = config['name']
        rows = bindings(config)
        report['errors'] = duplicate_errors(rows)
        if report['errors']:
            raise ValueError('Duplicate ports in the resolved configuration')
        if args.services:
            unknown = set(args.services) - set(config['services'])
            if unknown:
                raise ValueError(f'Unknown services: {sorted(unknown)}')
            rows = [r for r in rows if r['service'] in args.services]
        running = running_bindings()
        needs_probe = any(owner(row, running, config['name']) is None for row in rows)
        if needs_probe:
            if docker('image', 'inspect', 'alpine:3.22.5', check=False).returncode:
                docker('pull', 'alpine:3.22.5')
        for row in rows:
            result = dict(row, **(owner(row, running, config['name']) or probe(row)))
            report['results'].append(result)
            print(json.dumps(result, ensure_ascii=False), flush=True)
        report['status'] = 'FAIL' if any(r['status'] == 'FAIL' for r in report['results']) else 'PASS'
    except Exception as exc:
        report['errors'].append(str(exc))
    destination = Path(args.report)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print('PORTS_CHECK_' + report['status'], flush=True)
    if report['errors']:
        print(json.dumps(report['errors'], ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
