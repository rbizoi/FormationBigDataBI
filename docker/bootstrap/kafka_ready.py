"""Wait for usable leaders and in-sync replicas, including existing topics."""
import json
import time


def partition_problems(metadata, topics):
    problems = []
    for name in topics:
        topic = metadata.topics.get(name)
        if topic is None or topic.error or not topic.partitions:
            problems.append({'topic': name, 'error': str(topic.error) if topic else 'missing'})
            continue
        for number, part in topic.partitions.items():
            if part.error or part.leader < 0 or part.leader not in metadata.brokers or part.leader not in part.isrs:
                problems.append({'topic': name, 'partition': number, 'leader': part.leader,
                                 'replicas': part.replicas, 'isrs': part.isrs, 'error': str(part.error)})
    return problems


def wait_ready(admin, topics, timeout=120):
    deadline = time.monotonic() + timeout
    problems = []
    while time.monotonic() < deadline:
        try:
            problems = partition_problems(admin.list_topics(timeout=min(10, max(1, deadline-time.monotonic()))), topics)
            if not problems:
                return
        except Exception as exc:
            problems = [{'error': str(exc)}]
        time.sleep(min(2, max(0, deadline-time.monotonic())))
    raise RuntimeError('KAFKA_PARTITIONS_NOT_READY ' + json.dumps(problems) +
                       '; inspect kafka logs, disk and container OOM state; no data was deleted')
