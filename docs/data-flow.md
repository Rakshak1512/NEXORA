# Telemetry & AIOps Data Flow

## 1. Local Hardware Sampling
- The collector samples system metrics using `psutil`:
  - `cpu_utilization_pct`: 1-second sampled CPU utilization across cores.
  - `memory_utilization_pct`: RAM consumption.
  - `disk_utilization_pct`: Storage consumption of the host volume.
  - `bytes_sent_rate_kbps` / `bytes_recv_rate_kbps`: Delta throughput.
  - `latency_ms` / `packet_loss_pct`: Network health probe metrics.

## 2. Redaction & Allowlist Filtering
1. The collector aggregates infrastructure metrics with local authentication failure events.
2. The dictionary is scanned recursively by `LocalDataRedactor`:
   - Password key names and values matched with `[REDACTED_PASSWORD]`.
   - Bearer tokens matched with `[REDACTED_BEARER_TOKEN]`.
   - AWS access keys (`AKIA...`) matched with `[REDACTED_AWS_ACCESS_KEY]`.
   - Connection strings (`postgres://...`) matched with `[REDACTED_CONN_STRING]`.
3. `MetadataAllowlistValidator` strips any keys not on the explicit whitelist:
   `approved_keys = { payload_id, collector_id, tenant_id, timestamp_utc, cpu_utilization_pct, ... }`
4. Cryptographic Proof is computed: `SHA256(canonical_json(outgoing_payload))`.

## 3. Persistent Buffering
- The clean metadata is stored in `local_buffer.db` SQLite table:
  ```sql
  INSERT INTO local_queue (payload_id, payload_type, payload_json, status)
  VALUES ('p-1234', 'telemetry', '{...}', 'PENDING');
  ```
- If the central backend is unreachable, records remain safely buffered in SQLite with an exponential backoff retry loop.

## 4. Ingestion & Anomaly Analysis
- The FastAPI `/api/telemetry/ingest` endpoint:
  1. Checks idempotency: `SELECT 1 FROM infrastructure_metrics WHERE payload_id = :id`. If found, ignores duplicate.
  2. Saves clean metrics to relational tables.
  3. Dispatches payload to `AIOpsAnomalyDetector`:
     - Computes Z-Scores against 200-sample sliding baseline.
     - Runs Scikit-learn `IsolationForest` on multi-metric vector.
  4. Dispatches detected alerts to `EventCorrelator`:
     - Groups alerts occurring on the same collector within a 90-second sliding window into a unified incident.
  5. Generates explainable root cause and remediation recommendations.
  6. Broadcasts metrics and alerts via WebSocket to connected operators.

