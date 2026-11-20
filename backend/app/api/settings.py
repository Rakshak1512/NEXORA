from fastapi import APIRouter

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("")
def get_settings():
    return {
        "organization": {
            "name": "AcroGlobal Financial",
            "tier": "Enterprise Multi-Tenant",
            "retention_days": 90
        },
        "thresholds": {
            "cpu_warning_pct": 75.0,
            "cpu_critical_pct": 90.0,
            "memory_warning_pct": 80.0,
            "memory_critical_pct": 90.0,
            "disk_warning_pct": 85.0,
            "disk_critical_pct": 95.0,
            "latency_warning_ms": 100.0,
            "latency_critical_ms": 200.0,
            "packet_loss_warning_pct": 1.0,
            "packet_loss_critical_pct": 5.0
        },
        "aiops": {
            "isolation_forest_enabled": True,
            "correlation_window_seconds": 90,
            "autonomous_remediation_mode": "POLICY_CHECKED_HUMAN_APPROVAL",
            "llm_enrichment_mode": "METADATA_ONLY_FALLBACK"
        },
        "collector_security": {
            "local_redaction_strictness": "MAXIMUM",
            "allowlist_strictness": "ENFORCED",
            "raw_log_egress": "BLOCKED_AT_PERIMETER"
        }
    }

