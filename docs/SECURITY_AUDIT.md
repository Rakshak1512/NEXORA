# CYNERA — Enterprise Security Audit & Zero-Trust Verification
**Platform:** CYNERA (*Cyber Network Evaluation and Risk Analytics*)  
**Version:** 1.4.2  
**Audit Scope:** Multi-Tenant Isolation, SSRF Safeguards, Egress Proof Architecture, Authentication & OTP Security, Cryptographic Primitives, and API Protection.

---

## 1. Zero-Trust Architecture & Egress Proof Model

CYNERA enforces strict privacy-first telemetry egress at Tier 1 Edge Collectors prior to network transmission:
1. **Local Redaction Pipeline**:
   - Telemetry data collected on client nodes passes through regex-based masking engines before serialization.
   - Credentials, Authorization headers, Bearer tokens, private keys, database connection URIs, and passwords are fully redacted locally.
2. **Schema Allowlisting**:
   - Outbound collector payloads are strictly filtered against a strict allowlist. Unauthorized keys or arbitrary data structures injected into telemetry envelopes are dropped before transit.
3. **Cryptographic Egress Audit Trails**:
   - Each outbound batch generates a verifiable cryptographic SHA-256 digest (`payload_hash_sha256`) of the scrubbed payload.
   - The platform UI at `/egress-proof` allows auditors to compare the raw sanitized preview against the received JSON and independently compute the SHA-256 hash in their browser using the Web Crypto API.

---

## 2. Server-Side Request Forgery (SSRF) Defense

For zero-collector website monitoring, CYNERA implements strict IP range filtering and URL sanitization:
- **Loopback Blocking**: `127.0.0.0/8`, `::1`
- **Private Subnets Blocking**: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`
- **Link-Local & Cloud Metadata Blocking**: `169.254.0.0/16` (protects AWS/GCP/Azure instance metadata endpoints like `http://169.254.169.254/latest/meta-data/`)
- **Carrier-Grade NAT & Broadcast**: `100.64.0.0/10`, `224.0.0.0/4`, `240.0.0.0/4`
- **DNS Rebinding Guard**: Hostnames are resolved to IP addresses and validated prior to executing HTTP/HTTPS socket connections. Redirects are checked at every hop.

---

## 3. Authentication, Password Hashing & OTP Lifecycle

1. **Password Security**:
   - Passwords are encrypted using salted `bcrypt` hashes (`Passlib` crypt context). Plaintext passwords are never stored or cached.
2. **Cryptographic OTP Generation**:
   - 6-digit OTP codes are generated using cryptographically secure pseudorandom number generators (`secrets.randbelow(900000) + 100000`).
   - OTP codes are hashed via HMAC-SHA256 (`OTP_HASH_SECRET`) before being written to persistent storage. Plaintext OTP codes are never logged to console outputs or server files.
   - Expiration window is strictly enforced at 5 minutes (`OTP_EXPIRY_MINUTES = 5`).
3. **JWT Access & Refresh Tokens**:
   - Ephemeral HS256 JWT tokens containing `sub` (User ID), `email`, `role`, `tenant_id`, and `org_id`.
   - All protected routes validate bearer tokens using `get_current_user` dependency.

---

## 4. Multi-Tenant Isolation & Row-Level Authorization

- **Tenant Scoping**: All core database models (`monitored_websites`, `network_devices`, `application_services`, `database_integrations`, `alerts`, `incidents`, `collectors`, `api_keys`, `webhooks`) enforce mandatory foreign key constraints to `organizations.id` or `tenants.id`.
- **Query Boundary**: All database queries filter explicitly by `organization_id = current_user.organization_id`. Cross-tenant record access is blocked with `403 Forbidden` or `404 Not Found`.

---

## 5. Webhook Security & Signatures

- Outbound webhooks include an `X-Cynera-Signature` header computed as:
  $$\text{Signature} = \text{HMAC-SHA256}(\text{payload\_bytes}, \text{webhook\_secret})$$
- Consumers can verify authenticity and integrity before accepting alerts or incident notifications.
