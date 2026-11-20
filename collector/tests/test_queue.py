import os
import tempfile
import pytest
from app.queue_manager import PersistentQueueManager

def test_queue_enqueue_and_delivery():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_buffer.db")
    queue = PersistentQueueManager(db_path)

    # 1. Enqueue
    data = {"cpu": 45.0, "mem": 60.0}
    ok = queue.enqueue("p-001", "telemetry", data)
    assert ok is True
    assert queue.get_queue_depth() == 1

    # 2. Duplicate idempotent prevention
    ok_dup = queue.enqueue("p-001", "telemetry", data)
    assert queue.get_queue_depth() == 1

    # 3. Retrieve pending
    pending = queue.get_pending(limit=10)
    assert len(pending) == 1
    assert pending[0]["payload_id"] == "p-001"
    assert pending[0]["data"]["cpu"] == 45.0

    # 4. Mark delivered
    queue.mark_delivered("p-001")
    assert queue.get_queue_depth() == 0

