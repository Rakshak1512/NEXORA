import time
import hashlib
from typing import Dict, Any

class LocalSecurityMonitor:
    """
    LOCAL SECURITY MONITOR
    Aggregates sensitive local login activity and system auth events locally.
    Never exposes raw auth logs or passwords; transmits high-level risk summaries only.
    """
    def __init__(self):
        self.failed_login_counter = 0
        self.last_window_reset = time.time()
        self.burst_event_active = False

    def simulate_or_observe_event(self, force_burst: bool = False) -> Dict[str, Any]:
        now = time.time()
        # Reset window every 60 seconds
        if now - self.last_window_reset > 60:
            self.failed_login_counter = 0
            self.last_window_reset = now

        if force_burst:
            self.failed_login_counter += 18
            self.burst_event_active = True
        else:
            self.failed_login_counter += 1

        rate = round(self.failed_login_counter / max(1.0, (now - self.last_window_reset) / 60.0), 2)
        
        severity = "LOW"
        risk_score = 12.0
        desc = "Normal authentication profile across local endpoints."

        if rate > 50:
            severity = "CRITICAL"
            risk_score = 94.5
            desc = "Synchronized credential failure burst detected across edge gateway."
        elif rate > 20:
            severity = "HIGH"
            risk_score = 75.0
            desc = "Elevated failed login rate exceeding 3-sigma baseline."
        elif rate > 5:
            severity = "MEDIUM"
            risk_score = 42.0
            desc = "Occasional authentication retries observed."

        # Compute pseudonymous cluster signature
        cluster_hash = hashlib.sha256(f"cluster-{time.strftime('%Y-%m-%d-%H')}".encode()).hexdigest()[:12]

        return {
            "failed_login_count": self.failed_login_counter,
            "suspicious_activity_score": risk_score,
            "security_event_severity": severity,
            "authentication_failure_rate_per_min": rate,
            "pseudonymous_source_cluster": f"sec-cluster-{cluster_hash}",
            "redacted_tokens_detected": 0,
            "summary_description": desc
        }

