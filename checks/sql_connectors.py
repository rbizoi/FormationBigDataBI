"""CI real PostgreSQL + Iceberg REST + S3 federation through Trino."""
import json
import time
from urllib.request import Request, urlopen

BASE = 'http://127.0.0.1:25012'


def query(sql):
    request = Request(BASE+'/v1/statement', data=sql.encode(), headers={'X-Trino-User': 'formation'})
    rows = []
    deadline = time.monotonic()+120
    while True:
        with urlopen(request, timeout=30) as response:
            result = json.load(response)
        if 'error' in result:
            raise RuntimeError(result['error'])
        rows.extend(result.get('data', []))
        if 'nextUri' not in result:
            return rows
        if time.monotonic() > deadline:
            raise TimeoutError(sql)
        # Trino advertises its internal address; this check runs on the Docker host.
        from urllib.parse import urlsplit
        uri = urlsplit(result['nextUri'])
        request = Request(BASE+uri.path+('?' + uri.query if uri.query else ''), headers={'X-Trino-User': 'formation'})
        time.sleep(0.1)


if __name__ == '__main__':
    deadline = time.monotonic()+120
    while True:
        try:
            assert query('SELECT 1') == [[1]]
            break
        except Exception:
            if time.monotonic() >= deadline:
                raise
            time.sleep(2)
    assert query('SELECT count(*) FROM postgresql.public.customers')[0][0] >= 5
    query('CREATE SCHEMA IF NOT EXISTS iceberg.ci')
    query('DROP TABLE IF EXISTS iceberg.ci.integration_sales')
    try:
        query('CREATE TABLE iceberg.ci.integration_sales (customer_id BIGINT, amount DECIMAL(12,2))')
        query('INSERT INTO iceberg.ci.integration_sales SELECT customer_id, CAST(10 AS DECIMAL(12,2)) FROM postgresql.public.customers LIMIT 5')
        assert query('SELECT count(*), sum(amount) FROM iceberg.ci.integration_sales') == [[5, '50.00']]
        assert query('SELECT count(*) FROM iceberg.ci.integration_sales s JOIN postgresql.public.customers c ON s.customer_id=c.customer_id') == [[5]]
        print('SQL_CONNECTORS_PASS PostgreSQL -> Trino -> Iceberg REST + RustFS S3 -> federated join')
    finally:
        query('DROP TABLE IF EXISTS iceberg.ci.integration_sales')
