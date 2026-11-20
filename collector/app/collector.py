import time
import uuid
from typing import Dict, Any, Optional
from .config import config
from .telemetry import TelemetryEngine
from .security_monitor import LocalSecurityMonitor
from .redactor import LocalDataRedactor
from .allowlist import MetadataAllowlistValidator
from .egress_proof import EgressProofBuilder
from .queue_manager import PersistentQueueManager
from .sender import TelemetrySender

class LocalCollectorEngine:
    """
    LOCAL COLLECTOR ENGINE
    Coordinates collection, secret redaction, allowlist enforcement,
    local egress proof generation, and reliable delivery via persistent queue.
    """
    def __init__(self):
        self.telemetry = TelemetryEngine()
        self.security = LocalSecurityMonitor()
        self.queue = PersistentQueueManager(config.LOCAL_QUEUE_PATH)
        self.sender = TelemetrySender()
        self.active_scenario: Optional[str] = None
        self.outage_simulation: bool = False

    def set_scenario(self, scenario_name: Optional[str]):
        """Sets a synthetic test scenario (CPU spike, memory leak, network partition, etc.)."""
        self.active_scenario = scenario_name
        if scenario_name == "saas_outage":
            self.outage_simulation = True
        elif scenario_name == "recovery_after_outage":
            self.outage_simulation = False

    def process_cycle(self) -> Dict[str, Any]:
        """
        Executes one complete cycle:
        1. Gather real infrastructure telemetry + security summaries
        2. Apply synthetic scenario if active
        3. Locally scan and REDACT all secrets
        4. Validate against STRICT METADATA ALLOWLIST
        5. Build Egress Proof Record
        6. Queue locally in SQLite
        7. Flush persistent queue to backend
        """
        payload_id = f"payload-{uuid.uuid4().hex[:12]}"
        now_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # 1. Gather raw data
        infra = self.telemetry.collect_infrastructure()
        sec = self.security.simulate_or_observe_event(
            force_burst=(self.active_scenario == "failed_logins")
        )

        # 2. Modify if scenario active
        if self.active_scenario == "cpu_spike":
            infra["cpu_utilization_pct"] = 96.4
            infra["health_state"] = "POOR"
            infra["health_reason"] = "Extreme CPU saturation spike: 96.4% on main thread pool"
        elif self.active_scenario == "memory_spike":
            infra["memory_utilization_pct"] = 92.1
            infra["health_state"] = "POOR"
            infra["health_reason"] = "Critical memory heap saturation: 92.1%"
        elif self.active_scenario == "disk_spike":
            infra["disk_utilization_pct"] = 94.8
            infra["health_state"] = "POOR"
            infra["health_reason"] = "Storage volume near exhaustion: 94.8%"
        elif self.active_scenario == "network_latency_spike":
            infra["latency_ms"] = 285.0
            infra["health_state"] = "FAIR"
            infra["health_reason"] = "High cross-regional gateway latency: 285ms"
        elif self.active_scenario == "packet_loss_spike":
            infra["packet_loss_pct"] = 6.4
            infra["health_state"] = "POOR"
            infra["health_reason"] = "Packet drop threshold breached: 6.4%"

        # Include sample raw local event containing secret candidates to prove local redaction
        local_raw_sample = {
            **infra,
            **sec,
            "raw_db_connection": "postgres://cicada_admin:SuperSecretPassword123!@10.0.1.25:5432/core_db",
            "internal_jwt_token": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.fake_token_example",
            "aws_collector_key": "AKIAIOSFODNN7EXAMPLE",
            "admin_contact_email": "ops-lead@internal-corp.local",
            "unauthorized_internal_debug_dump": "dump_var_12345",
        }

        # 3. REDACT
        sanitized_data, redactions_count, detected_secret_types = LocalDataRedactor.sanitize_dictionary(local_raw_sample)

        # 4. ALLOWLIST VALIDATION
        approved_outgoing, rejected_keys, is_valid = MetadataAllowlistValidator.filter_and_validate({
            "payload_id": payload_id,
            "collector_id": config.COLLECTOR_ID,
            "tenant_id": config.TENANT_ID,
            "timestamp_utc": now_utc,
            "version": config.VERSION,
            **sanitized_data,
            "is_simulated": self.active_scenario is not None,
            "scenario_name": self.active_scenario or "nominal_live"
        })

        # 5. GENERATE CRYPTOGRAPHIC EGRESS PROOF
        egress_proof = EgressProofBuilder.create_proof_record(
            payload_id=payload_id,
            collector_id=config.COLLECTOR_ID,
            tenant_id=config.TENANT_ID,
            destination_endpoint=f"{config.BACKEND_URL}/api/telemetry/ingest",
            local_raw_sample=local_raw_sample,
            redacted_fields_count=redactions_count,
            redacted_field_types=detected_secret_types,
            rejected_keys=rejected_keys,
            outgoing_clean_payload=approved_outgoing
        )

        # 6. ENQUEUE IN SQLITE
        self.queue.enqueue(payload_id, "telemetry", approved_outgoing)
        self.queue.enqueue(f"proof-{payload_id}", "egress_proof", egress_proof)

        # 7. FLUSH QUEUE IF NOT IN SIMULATED OUTAGE
        if not self.outage_simulation:
            self.flush_queue()

        return {
            "payload_id": payload_id,
            "queue_depth": self.queue.get_queue_depth(),
            "outgoing_payload": approved_outgoing,
            "egress_proof": egress_proof
        }

    def flush_queue(self):
        """Processes backlog from SQLite queue to SaaS with idempotency."""
        pending = self.queue.get_pending(limit=20)
        for item in pending:
            p_id = item["payload_id"]
            p_type = item["payload_type"]
            data = item["data"]

            if p_type == "telemetry":
                success, code, msg = self.sender.send_telemetry(data)
            elif p_type == "egress_proof":
                success, code, msg = self.sender.send_egress_proof(data)
            else:
                success = True

            if success:
                self.queue.mark_delivered(p_id)
            else:
                self.queue.increment_retry(item["id"])
                # Break to respect backoff order on failure
                break

