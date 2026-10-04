"""Pre-register both PostgreSQL-compatible servers in the shared pgAdmin GUI."""
import json
import os
from pathlib import Path


def servers():
    return {'Servers': {
        '1': {'Name': 'PostgreSQL formation', 'Group': 'Formation', 'Host': 'postgres-source', 'Port': 5432, 'MaintenanceDB': os.environ['POSTGRES_DB'], 'Username': os.environ['POSTGRES_USER'], 'SSLMode': 'prefer'},
        '2': {'Name': 'TimescaleDB météo', 'Group': 'Formation', 'Host': 'timescaledb', 'Port': 5432, 'MaintenanceDB': os.getenv('TIMESCALE_DB', 'meteo'), 'Username': os.getenv('TIMESCALE_USER', 'meteo'), 'SSLMode': 'prefer'},
    }}


if __name__ == '__main__':
    Path('/config/servers.json').write_text(json.dumps(servers(), ensure_ascii=False))
