"""Remove only resources belonging to this Compose project. Preview by default."""
import argparse
import json
import subprocess


def docker(*args, capture=True):
    return subprocess.run(['docker', *args], check=True, text=True,
                          stdout=subprocess.PIPE if capture else None).stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true', help='Actually delete containers, volumes and removable images')
    args = parser.parse_args()
    compose = ['compose', '--env-file', '.env', '--env-file', 'ports.env', '--profile', '*']
    config = json.loads(docker(*compose, 'config', '--format', 'json'))
    project = config['name']
    if not project:
        raise RuntimeError('Empty project name')
    label = 'com.docker.compose.project=' + project
    containers = docker('ps', '-aq', '--filter', 'label=' + label).split()
    volumes = docker('volume', 'ls', '-q', '--filter', 'label=' + label).split()
    images = {s['image'] for s in config['services'].values() if s.get('image')}
    if containers:
        images.update(c['Image'] for c in json.loads(docker('inspect', *containers)))
    print(json.dumps({'project': project, 'containers': containers, 'volumes': volumes, 'images': sorted(images),
                      'execute': args.execute}, indent=2))
    if not args.execute:
        return 0
    docker(*compose, 'down', '--volumes', '--remove-orphans', capture=False)
    # This also finds named volumes left by services removed from the current YAML.
    remaining = docker('volume', 'ls', '-q', '--filter', 'label=' + label).split()
    for volume in remaining:
        docker('volume', 'rm', volume, capture=False)
    failures = []
    for image in sorted(images):
        if subprocess.run(['docker', 'image', 'inspect', image], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode:
            continue
        # No force: Docker protects images still used by containers of other projects.
        if subprocess.run(['docker', 'image', 'rm', image]).returncode:
            failures.append(image)
    if failures:
        print('Images retained (shared or still referenced): ' + ', '.join(failures))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
