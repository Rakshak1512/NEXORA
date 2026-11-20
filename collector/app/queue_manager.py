import os
import sqlite3
import json
import time
from typing import List, Dict, Any, Optional

class PersistentQueueManager:
    """
    SQLITE PERSISTENT LOCAL QUEUE
    Guarantees zero data loss during SaaS network outages.
    Buffered records are preserved on disk and transmitted with exponential backoff.
    """
    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS local_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payload_id TEXT UNIQUE NOT NULL,
                    payload_type TEXT NOT NULL, -- 'telemetry', 'heartbeat', 'egress_proof'
                    payload_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    retry_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'PENDING' -- 'PENDING', 'SENT', 'FAILED'
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON local_queue(status, created_at)")
            conn.commit()

    def enqueue(self, payload_id: str, payload_type: str, data: Dict[str, Any]) -> bool:
        """Atomically enqueues a payload with unique payload_id for idempotency."""
        try:
            with self._get_conn() as conn:
                conn.execute("""
                    INSERT OR IGNORE INTO local_queue (payload_id, payload_type, payload_json, created_at, status)
                    VALUES (?, ?, ?, ?, 'PENDING')
                """, (payload_id, payload_type, json.dumps(data), time.time()))
                conn.commit()
            return True
        except Exception as e:
            print(f"[QueueManager] Enqueue error: {e}")
            return False

    def get_pending(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves unacknowledged queued payloads ordered by arrival time."""
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT id, payload_id, payload_type, payload_json, retry_count
                FROM local_queue
                WHERE status = 'PENDING'
                ORDER BY id ASC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [
                {
                    "id": row["id"],
                    "payload_id": row["payload_id"],
                    "payload_type": row["payload_type"],
                    "data": json.loads(row["payload_json"]),
                    "retry_count": row["retry_count"]
                }
                for row in rows
            ]

    def mark_delivered(self, payload_id: str):
        """Removes delivered record only upon SaaS HTTP 200 acknowledgement."""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM local_queue WHERE payload_id = ?", (payload_id,))
            conn.commit()

    def increment_retry(self, item_id: int):
        with self._get_conn() as conn:
            conn.execute("UPDATE local_queue SET retry_count = retry_count + 1 WHERE id = ?", (item_id,))
            conn.commit()

    def get_queue_depth(self) -> int:
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT COUNT(*) as cnt FROM local_queue WHERE status = 'PENDING'")
            return cursor.fetchone()["cnt"]

