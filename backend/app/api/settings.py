from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter(prefix="/settings", tags=["Settings"])

_runtime_settings = {
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

@router.get("")
def get_settings():
    return _runtime_settings

class SettingsUpdateRequest(BaseModel):
    thresholds: Optional[Dict[str, float]] = None
    aiops: Optional[Dict[str, Any]] = None

@router.post("")
@router.put("")
def update_settings(data: SettingsUpdateRequest):
    if data.thresholds:
        _runtime_settings["thresholds"].update(data.thresholds)
    if data.aiops:
        _runtime_settings["aiops"].update(data.aiops)
    return {"status": "success", "message": "Settings updated successfully", "settings": _runtime_settings}


