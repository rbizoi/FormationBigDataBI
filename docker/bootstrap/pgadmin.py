"""Pre-register the PostgreSQL source server in the shared pgAdmin GUI."""
import json
import os
from pathlib import Path


def servers():
    return {'Servers': {
        '1': {'Name': 'PostgreSQL formation', 'Group': 'Formation', 'Host': 'postgres-source', 'Port': 5432, 'MaintenanceDB': os.environ['POSTGRES_DB'], 'Username': os.environ['POSTGRES_USER'], 'SSLMode': 'prefer'},
    }}


if __name__ == '__main__':
    Path('/config/servers.json').write_text(json.dumps(servers(), ensure_ascii=False))
