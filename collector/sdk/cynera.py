"""
CYNERA APM Python SDK
Lightweight, privacy-first application performance and exception tracking.
"""

import time
import traceback
import threading
import queue
import urllib.request
import json
import re
from typing import Optional, Dict, Any

SENSITIVE_KEYS = re.compile(r"(password|token|secret|api[_-]?key|auth|bearer|credit|card)", re.I)

def sanitize_dict(d: Any) -> Any:
    if isinstance(d, dict):
        return {
            k: "[REDACTED]" if SENSITIVE_KEYS.search(str(k)) else sanitize_dict(v)
            for k, v in d.items()
        }
    elif isinstance(d, list):
        return [sanitize_dict(item) for item in d]
    elif isinstance(d, str):
        # Redact JWT-like strings or auth headers
        if d.lower().startswith("bearer ") or len(d) > 80 and "." in d:
            return "[REDACTED_CREDENTIAL]"
    return d

class CyneraAPM:
    _instance = None

    def __init__(
        self,
        api_key: str,
        service_name: str,
        base_url: str = "http://localhost:8000",
        environment: str = "production",
        flush_interval: float = 5.0
    ):
        self.api_key = api_key
        self.service_name = service_name
        self.base_url = base_url.rstrip("/")
        self.environment = environment
        self.flush_interval = flush_interval
        self._queue = queue.Queue(maxsize=1000)
        self._stop_event = threading.Event()
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
        CyneraAPM._instance = self

    @classmethod
    def get_instance(cls) -> Optional["CyneraAPM"]:
        return cls._instance

    def capture_exception(
        self,
        exc: Exception,
        context: Optional[Dict[str, Any]] = None,
        level: str = "error"
    ):
        """Captures an unhandled or handled exception with stack trace."""
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        event = {
            "type": "exception",
            "service_name": self.service_name,
            "environment": self.environment,
            "exception_type": type(exc).__name__,
            "message": str(exc),
            "stack_trace": tb,
            "level": level,
            "timestamp": time.time(),
            "context": sanitize_dict(context or {})
        }
        self._enqueue(event)

    def track_request(
        self,
        endpoint: str,
        method: str = "GET",
        status_code: int = 200,
        duration_ms: float = 0.0,
        error: Optional[str] = None
    ):
        """Records HTTP request throughput, latency, and error status."""
        event = {
            "type": "request",
            "service_name": self.service_name,
            "environment": self.environment,
            "endpoint": endpoint,
            "method": method.upper(),
            "status_code": status_code,
            "duration_ms": duration_ms,
            "error": error,
            "timestamp": time.time()
        }
        self._enqueue(event)

    def _enqueue(self, item: Dict[str, Any]):
        try:
            self._queue.put_nowait(item)
        except queue.Full:
            pass  # Drop if overwhelmed to protect application stability

    def _worker_loop(self):
        while not self._stop_event.is_set():
            batch = []
            try:
                # Collect items up to 50 or wait flush interval
                start = time.time()
                while len(batch) < 50 and (time.time() - start) < self.flush_interval:
                    try:
                        item = self._queue.get(timeout=0.5)
                        batch.append(item)
                    except queue.Empty:
                        break
            except Exception:
                pass

            if batch:
                self._send_batch(batch)
            time.sleep(1.0)

    def _send_batch(self, batch):
        url = f"{self.base_url}/api/apm/ingest"
        payload = json.dumps({
            "service_name": self.service_name,
            "environment": self.environment,
            "events": batch
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "X-CYNERA-API-KEY": self.api_key,
                "User-Agent": "Cynera-Python-SDK/1.0"
            },
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                pass
        except Exception:
            pass  # Fail silent, do not crash host application

    def close(self):
        self._stop_event.set()
        if self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)

