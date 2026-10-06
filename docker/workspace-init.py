"""Seed portable Docker volumes; never change permissions on host directories."""
import os
import pwd
import shutil
from pathlib import Path


def initialize(source, target, uid):
    source, target = Path(source), Path(target)
    target.mkdir(parents=True, exist_ok=True)
    if source is not None:
        shutil.copytree(source, target, dirs_exist_ok=True)
    for path in [target, *target.rglob('*')]:
        if path.is_symlink():
            raise RuntimeError(f'Symlinks are not supported in shared workspace: {path}')
        os.chown(path, uid, 0)
        os.chmod(path, 0o2775 if path.is_dir() else 0o664)


if __name__ == '__main__':
    uid = pwd.getpwnam('spark').pw_uid
    initialize('/seed/donnees', '/opt/spark/donnees', uid)
    initialize('/seed/jobs', '/opt/spark/jobs', uid)
    print('WORKSPACE_INIT_OK')
