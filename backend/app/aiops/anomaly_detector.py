import numpy as np
from sklearn.ensemble import IsolationForest
from typing import Dict, Any, List, Optional

class AIOpsAnomalyDetector:
    """
    AIOPS MULTI-VARIATE ANOMALY DETECTOR
    Combines rolling statistical baselines (Z-Score & IQR) with
    Scikit-learn Isolation Forest on multidimensional telemetry vectors.
    """
    def __init__(self):
        # Baseline historical values for cold start
        self.history_window: List[List[float]] = []
        self.max_history = 200
        self.iso_forest = IsolationForest(contamination=0.05, random_state=42)
        self.is_fitted = False

        # Seed with initial baseline distribution (normal variance)
        np.random.seed(42)
        for _ in range(50):
            cpu = np.random.normal(45.0, 5.0)
            mem = np.random.normal(55.0, 4.0)
            disk = np.random.normal(60.0, 2.0)
            lat = np.random.normal(20.0, 3.0)
            loss = max(0.0, np.random.normal(0.01, 0.02))
            auth_fail = max(0, int(np.random.normal(1.0, 0.5)))
            self.history_window.append([cpu, mem, disk, lat, loss, auth_fail])

        self._fit_model()

    def _fit_model(self):
        if len(self.history_window) >= 30:
            X = np.array(self.history_window)
            self.iso_forest.fit(X)
            self.is_fitted = True

    def analyze(self, telemetry: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evaluates incoming telemetry payload against statistical and ML baselines.
        Returns list of detected anomalies.
        """
        anomalies = []

        cpu = float(telemetry.get("cpu_utilization_pct", 0.0))
        mem = float(telemetry.get("memory_utilization_pct", 0.0))
        disk = float(telemetry.get("disk_utilization_pct", 0.0))
        lat = float(telemetry.get("latency_ms", 0.0))
        loss = float(telemetry.get("packet_loss_pct", 0.0))
        auth_fail = float(telemetry.get("failed_login_count", 0))

        # Add to rolling history
        self.history_window.append([cpu, mem, disk, lat, loss, auth_fail])
        if len(self.history_window) > self.max_history:
            self.history_window.pop(0)

        # 1. Statistical Threshold & Z-Score Analysis
        hist = np.array(self.history_window)
        means = np.mean(hist, axis=0)
        stds = np.std(hist, axis=0) + 1e-6 # prevent division by zero

        # CPU check
        cpu_z = (cpu - means[0]) / stds[0]
        if cpu > 85.0 or cpu_z > 3.0:
            anomalies.append({
                "alert_type": "CPU_SATURATION",
                "severity": "CRITICAL" if cpu > 92 else "HIGH",
                "metric_name": "cpu_utilization_pct",
                "metric_value": cpu,
                "threshold_value": 85.0,
                "message": f"CPU saturation spike detected: {cpu}% (Z-score: {cpu_z:.2f}σ above baseline)"
            })

        # Memory check
        mem_z = (mem - means[1]) / stds[1]
        if mem > 85.0 or mem_z > 3.0:
            anomalies.append({
                "alert_type": "MEMORY_LEAK_BURST",
                "severity": "CRITICAL" if mem > 90 else "HIGH",
                "metric_name": "memory_utilization_pct",
                "metric_value": mem,
                "threshold_value": 85.0,
                "message": f"Memory buffer saturation: {mem}% (Z-score: {mem_z:.2f}σ above baseline)"
            })

        # Disk check
        if disk > 90.0:
            anomalies.append({
                "alert_type": "STORAGE_EXHAUSTION",
                "severity": "CRITICAL" if disk > 95 else "HIGH",
                "metric_name": "disk_utilization_pct",
                "metric_value": disk,
                "threshold_value": 90.0,
                "message": f"Disk utilization critical: {disk}% storage consumed"
            })

        # Network Latency check
        lat_z = (lat - means[3]) / stds[3]
        if lat > 150.0 or lat_z > 3.5:
            anomalies.append({
                "alert_type": "LATENCY_DEGRADATION",
                "severity": "HIGH",
                "metric_name": "latency_ms",
                "metric_value": lat,
                "threshold_value": 150.0,
                "message": f"Network transit latency surge: {lat}ms (+{lat_z:.1f}σ deviation)"
            })

        # Packet Loss check
        if loss > 3.0:
            anomalies.append({
                "alert_type": "PACKET_LOSS_SURGE",
                "severity": "CRITICAL" if loss > 5.0 else "HIGH",
                "metric_name": "packet_loss_pct",
                "metric_value": loss,
                "threshold_value": 3.0,
                "message": f"Elevated packet drop rate: {loss}% transmission failure"
            })

        # Security Auth failure check
        if auth_fail > 15:
            anomalies.append({
                "alert_type": "AUTHENTICATION_BURST",
                "severity": "CRITICAL" if auth_fail > 40 else "HIGH",
                "metric_name": "failed_login_count",
                "metric_value": float(auth_fail),
                "threshold_value": 15.0,
                "message": f"Suspicious login failure burst: {auth_fail} failed attempts in current window"
            })

        # 2. Scikit-learn Isolation Forest Multivariate Outlier Check
        if self.is_fitted and not anomalies:
            vec = np.array([[cpu, mem, disk, lat, loss, auth_fail]])
            pred = self.iso_forest.predict(vec)[0]
            if pred == -1: # Outlier detected by Isolation Forest
                score = self.iso_forest.score_samples(vec)[0]
                anomalies.append({
                    "alert_type": "MULTIVARIATE_ANOMALY",
                    "severity": "MEDIUM",
                    "metric_name": "isolation_forest_score",
                    "metric_value": round(float(score), 4),
                    "threshold_value": 0.0,
                    "message": f"Subtle cross-metric anomalous trajectory flagged by Isolation Forest (score: {score:.3f})"
                })

        return anomalies

    def analyze_network_device(self, check: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluates network device probe results for unreachability, closed ports, and latency degradation."""
        anomalies = []
        status = check.get("check_status", check.get("status", "ONLINE"))
        loss = float(check.get("packet_loss_pct", 0.0))
        lat = float(check.get("latency_ms", 0.0))
        dev_name = check.get("device_name", check.get("name", check.get("ip_address", "Device")))
        ip = check.get("ip_address", "")
        closed_ports = check.get("closed_ports", [])

        if status == "UNREACHABLE" or loss >= 99.0:
            anomalies.append({
                "alert_type": "NETWORK_DEVICE_UNREACHABLE",
                "severity": "CRITICAL",
                "metric_name": "packet_loss_pct",
                "metric_value": loss,
                "threshold_value": 10.0,
                "message": f"Network device '{dev_name}' ({ip}) is completely unreachable. 100% packet loss detected."
            })
        elif loss > 10.0:
            anomalies.append({
                "alert_type": "PACKET_LOSS_SPIKE",
                "severity": "HIGH",
                "metric_name": "packet_loss_pct",
                "metric_value": loss,
                "threshold_value": 10.0,
                "message": f"High packet drop rate on '{dev_name}' ({ip}): {loss}% packets dropped."
            })

        if closed_ports and status != "UNREACHABLE":
            anomalies.append({
                "alert_type": "NETWORK_SERVICE_DEGRADED",
                "severity": "HIGH",
                "metric_name": "closed_tcp_ports",
                "metric_value": float(len(closed_ports)),
                "threshold_value": 0.0,
                "message": f"Monitored TCP service ports unavailable on '{dev_name}' ({ip}): ports {closed_ports} refused connection."
            })

        if lat > 150.0:
            anomalies.append({
                "alert_type": "LATENCY_SPIKE",
                "severity": "MEDIUM",
                "metric_name": "latency_ms",
                "metric_value": lat,
                "threshold_value": 150.0,
                "message": f"Elevated network transit latency to '{dev_name}' ({ip}): {lat}ms."
            })

        return anomalies

anomaly_detector = AIOpsAnomalyDetector()

