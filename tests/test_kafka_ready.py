from pathlib import Path
import sys
from types import SimpleNamespace as NS
sys.path.insert(0, str(Path(__file__).parents[1] / 'docker/bootstrap'))
from kafka_ready import partition_problems


def test_existing_topic_without_leader_is_not_ready():
    part = NS(error=None, leader=-1, replicas=[1], isrs=[])
    metadata = NS(brokers={1: object()}, topics={'sales.raw': NS(error=None, partitions={2: part})})
    assert partition_problems(metadata, ['sales.raw'])[0]['leader'] == -1
    part.leader = 1
    assert partition_problems(metadata, ['sales.raw'])
    part.isrs = [1]
    assert not partition_problems(metadata, ['sales.raw'])
    assert partition_problems(metadata, ['missing'])
