# CYNERA — DB Browser for SQLite Inspection Guide

This guide describes how to open, view, and inspect the persistent CYNERA SaaS database using **DB Browser for SQLite** (or any standard SQLite client).

---

## 1. Database File Location

The active persistent database is located at:
```
backend/cynera.db
```
Absolute Windows Path:
```
D:\NEXORA\backend\cynera.db
```

CYNERA uses SQLite with Foreign Key constraints enabled (`PRAGMA foreign_keys = ON;`) and UTC timestamp serialization.

---

## 2. Opening with DB Browser for SQLite

1. Download and install **DB Browser for SQLite** from [sqlitebrowser.org](https://sqlitebrowser.org/) if not already installed.
2. Launch DB Browser for SQLite.
3. Click **"Open Database"** (or press `Ctrl+O`).
4. Navigate to `D:\NEXORA\backend\cynera.db` and open it.
5. Switch between the **Database Structure**, **Browse Data**, and **Execute SQL** tabs.

---

## 3. Core Database Tables & Descriptions

| Table Name | Description | Key Product |
| :--- | :--- | :--- |
| `organizations` | Tenant accounts with company name, slug, domain, industry, and owner | Multi-Tenant Platform |
| `tenants` | Regional cluster or operational workspace subdivisions | Multi-Tenant Platform |
| `profiles` | User accounts with roles (Super Admin, Operator, Admin), hashed passwords | Security & RBAC |
| `otp_challenges` | 6-digit email verification codes for self-signup and 2FA | Auth & Security |
| `monitored_websites` | Public URLs, check intervals, SSL lifespan, DNS status, and SLA % | **Product A** (Website Monitor) |
| `website_check_results` | Historical synthetic HTTP latency, status code, and TLS handshake logs | **Product A** (Website Monitor) |
| `website_endpoints` | Granular API routes (e.g. `/health`, `/api/v1/ping`) per website | **Product A** (Website Monitor) |
| `application_services` | Registered microservices, error rates, throughput RPM, and p95 latency | **Product C** (APM) |
| `application_events` | Sanitized stack traces, exceptions, and latency events | **Product C** (APM) |
| `database_integrations` | PostgreSQL and MySQL connection configs and saturation meters | **Product C** (Databases) |
| `database_metrics` | Periodic connection pool counts, slow queries, and cache hit ratios | **Product C** (Databases) |
| `alerts` | Centralized alert records with severity (`CRITICAL`, `WARNING`, `INFO`) | Central Alert Center |
| `webhooks` | Outbound endpoints with encrypted HMAC secrets and event filters | Integrations |
| `webhook_deliveries` | Audit log of dispatched HTTP webhooks, response codes, and latencies | Integrations |
| `network_devices` | IP-based target hardware (Routers, Switches, Firewalls, Servers) | **Product B** (Network) |
| `network_check_results` | ICMP Ping round-trip, TCP port status, and SNMP safe probe data | **Product B** (Network) |
| `collectors` | Registered Tier 1 local collector instances inside customer environments | **Product B** (Infra) |
| `infrastructure_metrics`| Redacted CPU, memory, disk, and load averages from Tier 1 collectors | **Product B** (Infra) |
| `egress_metadata` | Cryptographic SHA-256 proofs and redaction counts of outgoing packets | **Two-Tier Privacy Proof** |
| `incidents` | Correlated AIOps incidents with root-cause signal groupings | AIOps Intelligence |
| `ai_recommendations` | Explainable, autonomous remediation suggestions with risk ratings | AIOps Intelligence |
| `api_keys` | Hashed enterprise service tokens (`cyn_live_...`) with permission scopes | Developer Portal |
| `embed_widget_tokens` | Public embed tokens (`cyn_embed_...`) for external status badges | Embedded Widgets |

---

## 4. Useful Inspection Queries (Execute SQL Tab)

### A. View Active Monitored Websites & Live Health
```sql
SELECT 
    name, 
    url, 
    status, 
    last_status_code, 
    last_response_time_ms || ' ms' AS latency,
    uptime_percentage_24h || '%' AS uptime_24h,
    ssl_issuer,
    ssl_days_remaining || ' days' AS ssl_remaining,
    dns_resolved_ips
FROM monitored_websites
ORDER BY created_at DESC;
```

### B. View Active Unresolved System Alerts
```sql
SELECT 
    id, 
    title, 
    severity, 
    category, 
    resource_name, 
    status, 
    detected_at 
FROM alerts 
WHERE status != 'RESOLVED' 
ORDER BY detected_at DESC;
```

### C. Inspect Outbound Webhooks & HMAC Delivery History
```sql
SELECT 
    w.name, 
    w.destination_url, 
    d.event_type, 
    d.response_status_code, 
    d.execution_time_ms || ' ms' AS latency, 
    d.status, 
    d.delivered_at
FROM webhook_deliveries d
JOIN webhooks w ON d.webhook_id = w.id
ORDER BY d.delivered_at DESC
LIMIT 20;
```

### D. Verify Two-Tier Privacy & Egress Proofs
```sql
SELECT 
    payload_id, 
    collector_id, 
    bytes_transmitted, 
    redacted_fields_count, 
    payload_hash_sha256, 
    sent_at 
FROM egress_metadata 
ORDER BY sent_at DESC 
LIMIT 10;
```
