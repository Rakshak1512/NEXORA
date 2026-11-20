# CYNERA — Two-Tier System Architecture
## Cyber Network Evaluation and Risk Analytics

CYNERA delivers a privacy-first, enterprise-grade AIOps observability platform structured around an uncompromised Two-Tier Architecture.
See More. Secure More.

```
+-------------------------------------------------------------------------+
|                  TIER 1: CUSTOMER ON-PREMISES / VPC                     |
|                                                                         |
|  +-------------------------------------------------------------------+  |
|  |                     Python Local Collector                        |  |
|  |                                                                   |  |
|  |   [psutil Hardware Engine] ----------> [Local Security Monitor]   |  |
|  |       (CPU, Mem, Disk, Net)                (Auth Failure Rates)   |  |
|  |                 |                                   |             |  |
|  |                 v                                   v             |  |
|  |   +-----------------------------------------------------------+   |  |
|  |   |           Local Secret Redactor (Regex Engine)            |   |  |
|  |   |    (AWS Keys, Passwords, Tokens, Conn Strings Neutralized)|   |  |
|  |   +-----------------------------------------------------------+   |  |
|  |                                 |                                 |  |
|  |                                 v                                 |  |
|  |   +-----------------------------------------------------------+   |  |
|  |   |            Strict Metadata Allowlist Validator            |   |  |
|  |   |       (Only 18 Approved Categorical/Numerical Keys Pass)  |   |  |
|  |   +-----------------------------------------------------------+   |  |
|  |                                 |                                 |  |
|  |            +--------------------+--------------------+            |  |
|  |            |                                         |            |  |
|  |            v                                         v            |  |
|  |   [Egress Proof Generator]                 [SQLite Persistent Q]  |  |
|  |   (SHA-256 Payload Hash,                    (Transactional Buffer)|  |
|  |    Local Sample vs Egress)                           |            |  |
|  +------------------------------------------------------|------------+  |
+---------------------------------------------------------|---------------+
                                                          | (HTTPS / HMAC Auth)
                                                          | Approved Metadata Only
                                                          v
+-------------------------------------------------------------------------+
|                  TIER 2: CENTRAL SAAS OBSERVABILITY PLATFORM            |
|                                                                         |
|  +-------------------------------------------------------------------+  |
|  |                   FastAPI High-Throughput Ingestion               |  |
|  |           (Duplicate Elimination via Idempotent Payload IDs)      |  |
|  +-------------------------------------------------------------------+  |
|            |                              |                             |
|            v                              v                             v
|   +------------------+          +--------------------+        +---------------+
|   | Supabase Postgres|          | AIOps Intelligence |        | WebSocket Hub |
|   | (RLS Enforced,   |          | - Z-Score Baseline |        | (Real-time    |
|   |  Tenants, Proofs)|          | - Isolation Forest |        |  Broadcasts to|
|   +------------------+          | - Temporal Cluster |        |  Dashboards)  |
|                                 | - Explainable Recs |        +---------------+
|                                 +--------------------+                |
|                                           |                           v
|                                           v                   +---------------+
|                                 [Remediation Approvals] ----->| React SaaS UI |
|                                 (Safe Human-in-the-Loop)      | (15 Modules)  |
+-------------------------------------------------------------------------------+
```

## Tier 1 Principles
- **Perimeter Isolation**: Raw system logs, environment variables, credentials, and customer personal identifiable information (PII) never leave the local machine.
- **Persistent Local Queue**: Telemetry payloads are written to an on-disk SQLite buffer before transmission. Outages or network jitter never cause dropped records.
- **Cryptographic Egress Audit**: Every outgoing transmission produces an immutable audit record containing the SHA-256 hash of the sanitized payload.

## Tier 2 Principles
- **Metadata Only Ingestion**: The cloud API strictly validates that payloads conform to the allowlist schema.
- **Tenant Isolation**: Row-Level Security (RLS) ensures that tenants can only query telemetry, incidents, and approvals originating from their registered collectors.
- **Safe Autonomous Operations**: Recommended remediation actions (such as worker pool recycles or adaptive rate limiting) require explicit operator sign-off before simulated execution.

