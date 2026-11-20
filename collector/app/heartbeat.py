import time
import psutil
from .config import config
from .sender import TelemetrySender
from .queue_manager import PersistentQueueManager

class CollectorHeartbeat:
    """
    HEARTBEAT MANAGER
    Transmits collector health, uptime, and local queue depth to backend.
    Enables SaaS to detect collector offline within 60s.
    """
    def __init__(self, queue: PersistentQueueManager):
        self.queue = queue
        self.sender = TelemetrySender()
        self.boot_time = psutil.boot_time()

    def send(self, status: str = "online") -> bool:
        uptime = int(time.time() - self.boot_time)
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().used / (1024 * 1024)

        payload = {
            "collector_id": config.COLLECTOR_ID,
            "tenant_id": config.TENANT_ID,
            "status": status,
            "uptime_seconds": uptime,
            "cpu_usage_pct": round(float(cpu), 2),
            "memory_usage_mb": round(float(mem), 2),
            "queue_backlog_count": self.queue.get_queue_depth(),
            "version": config.VERSION,
            "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        success, code, msg = self.sender.send_heartbeat(payload)
        return success

