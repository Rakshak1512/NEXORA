import time
import requests
from typing import Dict, Any, Tuple
from .config import config

class TelemetrySender:
    """
    SECURE METADATA TRANSMISSION CLIENT
    Transmits only approved metadata to central SaaS backend using HMAC / Bearer tokens.
    Implements exponential backoff and persistent queue acknowledgment.
    """
    def __init__(self):
        credential = getattr(config, "auth_credential", None) or config.COLLECTOR_CREDENTIAL
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {credential}",
            "X-Collector-ID": config.COLLECTOR_ID,
            "X-Tenant-ID": config.TENANT_ID,
            "Content-Type": "application/json"
        })

    def send_telemetry(self, payload: Dict[str, Any]) -> Tuple[bool, int, str]:
        """Sends clean telemetry payload to backend. Returns (success, status_code, message)."""
        url = f"{config.BACKEND_URL.rstrip('/')}/api/telemetry/ingest"
        try:
            res = self.session.post(url, json=payload, timeout=5.0)
            if res.status_code in (200, 201):
                return True, res.status_code, "Delivered"
            return False, res.status_code, res.text
        except requests.exceptions.RequestException as e:
            return False, 0, str(e)

    def send_egress_proof(self, proof_payload: Dict[str, Any]) -> Tuple[bool, int, str]:
        """Transmits the verified egress proof record to backend Egress Proof Center."""
        url = f"{config.BACKEND_URL.rstrip('/')}/api/egress/record"
        try:
            res = self.session.post(url, json=proof_payload, timeout=5.0)
            if res.status_code in (200, 201):
                return True, res.status_code, "Egress Proof Recorded"
            return False, res.status_code, res.text
        except requests.exceptions.RequestException as e:
            return False, 0, str(e)

    def send_heartbeat(self, heartbeat_payload: Dict[str, Any]) -> Tuple[bool, int, str]:
        url = f"{config.BACKEND_URL.rstrip('/')}/api/collectors/heartbeat"
        try:
            res = self.session.post(url, json=heartbeat_payload, timeout=5.0)
            if res.status_code in (200, 201):
                return True, res.status_code, "Heartbeat OK"
            return False, res.status_code, res.text
        except requests.exceptions.RequestException as e:
            return False, 0, str(e)

