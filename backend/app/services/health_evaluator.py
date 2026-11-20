import datetime
from sqlalchemy.orm import Session
from ..models.models import Collector, InfrastructureMetric

def check_stale_collectors(db: Session):
    """
    STALE DATA DETECTION
    If collector heartbeat is older than 60 seconds:
    - Downgrades collector status to 'offline'
    - Updates monitored systems to 'POOR' with clear explanation
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    threshold = now - datetime.timedelta(seconds=60)

    stale_collectors = db.query(Collector).filter(
        Collector.last_seen_at < threshold,
        Collector.status != "offline"
    ).all()

    for col in stale_collectors:
        col.status = "offline"
        # Record poor state in latest metric
        latest_metric = db.query(InfrastructureMetric).filter(
            InfrastructureMetric.collector_id == col.id
        ).order_by(InfrastructureMetric.recorded_at.desc()).first()

        if latest_metric:
            latest_metric.health_state = "POOR"
            latest_metric.health_reason = f"Collector heartbeat missing for >60s. Stale data detected."

    if stale_collectors:
        db.commit()

