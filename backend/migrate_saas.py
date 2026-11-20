import sqlite3
import os
import sys

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.database import engine, Base
from app.models.models import (
    Organization, Tenant, Profile, OrganizationMembership, OTPChallenge,
    APIKey, EmbedWidgetToken, Notification, ReportRecord,
    MonitoredWebsite, WebsiteCheckResult, WebsiteEndpoint,
    ApplicationService, ApplicationEvent, DatabaseIntegration, DatabaseMetric,
    Alert, Webhook, WebhookDelivery,
    Collector, CollectorHeartbeat, InfrastructureMetric, NetworkMetric,
    SecuritySummary, EgressMetadata, IncidentAlert, Incident,
    AIRecommendation, RemediationApproval, SystemAuditLog,
    PerformanceBenchmark, NetworkDevice, NetworkCheckResult
)

print(f"[Migration] Creating all missing tables on database...")
Base.metadata.create_all(bind=engine)
print(f"[Migration] Tables created successfully!")

