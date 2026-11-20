# Security & Privacy Specification

## Threat Model & Guarantees

### 1. Data Exfiltration Defense
- **Threat**: Accidental leakage of database passwords, JWT tokens, AWS credentials, or PII into SaaS logs.
- **Mitigation**: 
  - Regex pattern detectors running inside customer VPC/on-premises environment.
  - Hard allowlist dropping all arbitrary string logs, query bodies, or debug prints.
  - Verification via Egress Proof Center.

### 2. Collector Authentication & Tamper Prevention
- Every collector communicates over HTTPS using HMAC Bearer authentication tokens.
- Header validation enforces `X-Collector-ID` and `X-Tenant-ID`.
- Incoming telemetry with unregistered or mismatched credentials is rejected with HTTP 403 Forbidden.

### 3. Multi-Tenant Isolation
- Supabase PostgreSQL schema with Row-Level Security (RLS).
- Each tenant's telemetry, incidents, and approvals are keyed to their `tenant_id`.
- APIs filter by tenant boundary, preventing cross-tenant data leakage.

### 4. Safe Autonomous Operations Guardrail
- Autonomous remediation never runs raw destructive shell commands against production infrastructure.
- Recommended actions undergo a strict policy check:
  `POLICY_PASSED_REQUIRES_OPERATOR_SIGN_OFF`
- Human operators must review the action and rollback guarantee before approving execution.

