"""Verify source permissions and distributed S3A reads using the existing dataset."""
import hashlib
import json
import os
import uuid
from pathlib import Path
from pyspark.sql import SparkSession

for name in ('donnees', 'jobs'):
    root = Path('/home/spark') / name
    assert root.is_dir() and root.samefile(Path('/opt/spark') / name), root
    for path in root.rglob('*'):
        if path.is_file():
            with path.open('rb') as stream:
                stream.read(1)
    # Airflow mounts the volumes read-only. Spark must actually be able to write.
    if os.getenv('WORKSPACE_EXPECT_WRITE', '1') == '1':
        probe = root / ('.access-' + uuid.uuid4().hex)
        probe.write_text('permission check')
        assert probe.read_text() == 'permission check'
        probe.unlink()

spark = SparkSession.builder.appName('WorkspaceAndS3Verification').getOrCreate()
try:
    # binaryFile executes S3 reads on Spark executors, rather than a boto3 driver.
    rows = spark.read.format('binaryFile').option('recursiveFileLookup', 'true').option('pathGlobFilter', '*').load('s3a://lakehouse/donnees/').selectExpr('path', 'sha2(content, 256) AS digest').collect()
    actual = {row.path.split('/lakehouse/', 1)[1]: row.digest for row in rows}
    local = {'donnees/' + p.relative_to('/home/spark/donnees').as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/home/spark/donnees').rglob('*') if p.is_file()}
    assert actual == local, (set(local) - set(actual), set(actual) - set(local))
    sales = spark.read.option('header', True).csv('s3a://lakehouse/donnees/input/sales.csv')
    assert sales.count() == 2000
    assert sales.select('sale_id').distinct().count() == 2000
    def worker_access(_):
        from pathlib import Path
        import os
        import uuid
        for name in ('donnees', 'jobs'):
            root = Path('/home/spark') / name
            assert root.samefile(Path('/opt/spark') / name)
            for p in root.rglob('*'):
                if p.is_file():
                    with p.open('rb') as f: f.read(1)
            probe = root / ('.worker-' + uuid.uuid4().hex)
            probe.write_text('worker write')
            probe.unlink()
        yield os.getuid()
    uids = spark.sparkContext.parallelize(range(4), 4).mapPartitions(worker_access).collect()
    assert all(uid != 0 for uid in uids), uids
    print('WORKSPACE_S3_OK files=' + str(len(local)) + ' sales=2000 executor_uids=' + json.dumps(uids))
finally:
    spark.stop()
