from typing import Dict, Any, Tuple, List

class MetadataAllowlistValidator:
    """
    STRICT METADATA ALLOWLIST
    Ensures that only vetted telemetry metadata fields can leave the local perimeter.
    Any non-whitelisted payload fields are dropped or rejected before egress.
    """
    APPROVED_METADATA_KEYS = {
        # Identity
        "payload_id",
        "collector_id",
        "tenant_id",
        "timestamp_utc",
        "version",
        "hostname_pseudonym",

        # Infrastructure metrics
        "cpu_utilization_pct",
        "memory_utilization_pct",
        "memory_used_mb",
        "memory_total_mb",
        "disk_utilization_pct",
        "disk_used_gb",
        "disk_total_gb",
        "system_uptime_seconds",
        "process_count",
        "health_state",
        "health_reason",

        # Network metrics
        "bytes_sent_rate_kbps",
        "bytes_recv_rate_kbps",
        "latency_ms",
        "packet_loss_pct",
        "active_connections",
        "connectivity_status",

        # Network Device Check Metadata
        "device_id",
        "device_name",
        "device_type",
        "ip_address",
        "check_type",
        "check_status",
        "open_ports",
        "closed_ports",
        "port_details",
        "metrics_payload",
        "error_message",
        "network_devices_checks",

        # Security summaries (Aggregated stats only, no individual user identifiers)
        "failed_login_count",
        "suspicious_activity_score",
        "security_event_severity",
        "authentication_failure_rate_per_min",
        "pseudonymous_source_cluster",
        "redacted_tokens_detected",
        "summary_description",

        # Scenario tag if simulated
        "is_simulated",
        "scenario_name"
    }

    @classmethod
    def filter_and_validate(cls, raw_payload: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str], bool]:
        """
        Filters dictionary to strictly approved fields.
        Returns: (sanitized_payload, rejected_keys, is_valid)
        """
        filtered = {}
        rejected_keys = []

        for k, v in raw_payload.items():
            if k in cls.APPROVED_METADATA_KEYS:
                filtered[k] = v
            else:
                rejected_keys.append(k)

        # Must at least have payload_id, collector_id, tenant_id, timestamp_utc
        required = {"payload_id", "collector_id", "tenant_id", "timestamp_utc"}
        is_valid = required.issubset(filtered.keys())

        return filtered, rejected_keys, is_valid

