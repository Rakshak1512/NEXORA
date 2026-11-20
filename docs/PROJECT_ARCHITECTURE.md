# CYNERA — Technical Architecture & Component Specification
**Platform:** CYNERA (*Cyber Network Evaluation and Risk Analytics*)  
**Tagline:** *See More. Secure More.*  
**System Architecture:** Hybrid Two-Tier Enterprise Observability Platform  
**Version:** 1.4.2

---

## 1. System Architecture Overview

CYNERA is built as a hybrid observability platform serving two complementary operational models:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CYNERA SAAS PLATFORM                            │
├───────────────────────────────────────┬────────────────────────────────┤
│      PRODUCT A: ZERO-TOUCH PUBLIC     │   PRODUCT B: ZERO-TRUST PRIVATE │
│         WEBSITE & API MONITORING      │     INTERNAL INFRASTRUCTURE   │
│                                       │                                │
│  • Public Website Latency & Uptime    │  • Tier 1 Local Edge Collector │
│  • SSL/TLS Certificate Expiry Days    │  • Host CPU / Memory / Disk    │
│  • DNS Status & Resolution Latency    │  • TCP/IP Fleet & SNMP Probing │
│  • Sub-path Health Probes             │  • APM SDK Microservice Traces │
│  • SSRF-Guarded Outbound Checkers     │  • Database Pool & Query Sat.  │
│  • Zero Software Install Required     │  • Local Regex Redaction Proof │
└───────────────────────────────────────┴────────────────────────────────┘
                                  │
                                  ▼
      ┌────────────────────────────────────────────────────────────┐
      │                   CYNERA CLOUD BACKEND                     │
      │                  (FastAPI Python 3.11)                     │
      │                                                            │
      │  • Multi-Tenant Isolation Engine (Organization / Tenant)   │
      │  • Gaussian Anomaly Detection & AIOps Event Correlator     │
      │  • Transparent Explainable Recommendations Engine         │
      │  • Remediation Approval Center with 30s Rollback Guard     │
      │  • Webhook Delivery Engine (HMAC-SHA256 Signatures)        │
      │  • Resend Transactional Email & Cryptographic OTP Engine   │
      │  • Supabase PostgreSQL Connection Pooler (SQLAlchemy)      │
      └────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
      ┌────────────────────────────────────────────────────────────┐
      │                    CYNERA WEB CONSOLE                      │
      │                    (React 18 + Vite)                       │
      │                                                            │
      │  • Dark Enterprise Security Theme (Tailwind CSS)           │
      │  • 24 Specialized Enterprise Observability Views           │
      │  • Real-Time WebSockets Telemetry & Chart Streams          │
      │  • Client-Side Egress Proof SHA-256 Verifier               │
      └────────────────────────────────────────────────────────────┘
```

---

## 2. Core Subsystems

### Subsystem 1: Zero-Touch Website Prober (`backend/app/services/website_checker.py`)
- Executes non-invasive HTTP/HTTPS health checks, certificate validity queries, and DNS resolutions.
- **SSRF Protection:** Enforces strict socket-level IP validation using `ssrf_guard.py` before initiating outbound connections. Blocks loopback (`127.0.0.1`), private subnets (`10.0.0.0/8`, `192.168.0.0/16`, `172.16.0.0/12`), and link-local cloud metadata addresses (`169.254.169.254`).
- **Scheduling:** Background scheduler (`website_scheduler.py`) queries registered websites at configured intervals (30s, 60s, 300s).

### Subsystem 2: Tier 1 Edge Telemetry Collector (`collector/`)
- Lightweight agent deployed on client nodes or Kubernetes worker pods.
- Collects system CPU, RAM, disk, process count, and network socket metrics using `psutil`.
- **Privacy-First Egress:** Passes raw system data through `redactor.py` (scrubbing passwords, bearer tokens, AWS credentials, and connection strings) and filters through `allowlist.py`.
- **Egress Proof:** Computes SHA-256 hash of the scrubbed payload and transmits it alongside telemetry to the backend.
- **Resilience:** Features local SQLite queue (`collector/data/local_buffer.db`) with exponential backoff retry to buffer telemetry during network outages.

### Subsystem 3: Network Monitoring & IP Fleet Engine (`collector/app/network_monitor.py` & `backend/app/api/network.py`)
- Monitors authorized enterprise hardware (servers, switches, routers, firewalls).
- Protocols supported:
  - **ICMP Ping:** Real-time round-trip latency and packet loss detection.
  - **TCP Port Monitoring:** Verifies port availability (e.g., 22, 80, 443, 5432).
  - **SNMPv3 & SSH Metadata:** Collects sanitized device status metrics without exposing credentials to the frontend.

### Subsystem 4: AIOps Anomaly Engine & Event Correlator (`backend/app/api/incidents.py`)
- Analyzes timeseries telemetry streams against rolling historical baselines.
- Calculates Gaussian deviation ($Z$-scores) across multiple metrics (e.g., simultaneous CPU spikes, packet loss jumps, and authentication failures).
- Correlates multi-signal anomalies into unified Incident tickets to eliminate alert fatigue.
- Generates explainable, deterministic remediation recommendations with simulated dry-run plans and rollback safeguards.

### Subsystem 5: Multi-Tenant Database Layer (`backend/app/database.py`)
- Primary storage in Supabase PostgreSQL with pooled connections (`pool_size=10`, `max_overflow=20`, `pool_recycle=1800`, `pool_pre_ping=True`).
- Strictly enforces tenant isolation via `organization_id` on every query.
- Gracefully handles missing database credentials by returning `HTTP 503 BLOCKED_BY_CONFIGURATION` instead of silently corrupting state.

### Subsystem 6: Frontend Single-Page Application (`frontend/`)
- Built with React 18, Vite, Lucide Icons, and Tailwind CSS.
- Features 24 fully-audited views covering overview dashboards, website deep-dives, infrastructure, network fleet, security threats, AIOps correlation, approvals, reports, and developer API settings.

