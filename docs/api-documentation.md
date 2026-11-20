# API Documentation

The central SaaS backend exposes clean REST APIs and a WebSocket stream at `http://localhost:8000`. Interactive OpenAPI documentation is accessible at `http://localhost:8000/docs`.

## Key Endpoints

### Authentication (`/api/auth`)
- `POST /api/auth/register`: Register new operator or tenant administrator.
- `POST /api/auth/login`: Authenticate and receive JWT access token.
- `GET /api/auth/me`: Retrieve authenticated user profile and roles.
- `POST /api/auth/forgot-password`: Request password reset instructions.

### Collectors (`/api/collectors`)
- `GET /api/collectors`: List all enrolled collectors with status and last heartbeat.
- `GET /api/collectors/{id}`: Detailed collector telemetry and version info.
- `POST /api/collectors/heartbeat`: Collector daemon heartbeat ping.

### Telemetry (`/api/telemetry`)
- `POST /api/telemetry/ingest`: Ingest approved metadata with duplicate prevention.
- `GET /api/telemetry/latest`: Retrieve most recent telemetry across clusters.

### Metrics (`/api/metrics`)
- `GET /api/metrics/summary`: Complete command dashboard metrics summary.
- `GET /api/metrics/timeseries`: Historical time-series data for CPU, memory, latency, and packet loss.

### Incidents & Alerts (`/api/incidents`, `/api/alerts`)
- `GET /api/incidents`: Correlated incidents with severity, status, and AI recommendations.
- `GET /api/incidents/{id}`: Incident details with causal signals and alerts.
- `PATCH /api/incidents/{id}`: Update incident status (Investigating, Acknowledged, Resolved).
- `GET /api/alerts`: Raw detected anomaly alerts.

### Egress Proof Center (`/api/egress`)
- `POST /api/egress/record`: Store cryptographic proof of outgoing payload.
- `GET /api/egress/records`: List historical egress proofs.
- `GET /api/egress/records/{payload_id}`: Inspect 3-tier redaction proof.

### Remediation Approvals (`/api/approvals`)
- `GET /api/approvals`: List pending and actioned remediation approvals.
- `POST /api/approvals/{id}/action`: Operator sign-off (APPROVE / REJECT) with simulated execution.

### Scenarios (`/api/scenarios`)
- `POST /api/scenarios/trigger`: Trigger any of the 13 live hackathon failure injections.

### WebSocket Stream
- `ws://localhost:8000/ws`: Real-time bi-directional telemetry broadcast.

