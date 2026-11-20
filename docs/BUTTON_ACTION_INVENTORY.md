# CYNERA — Interactive Button & Action Inventory
**Platform:** CYNERA (*Cyber Network Evaluation and Risk Analytics*)  
**Version:** 1.4.2  
**Scope:** Complete granular inventory of interactive buttons, form submissions, modals, triggers, and action handlers across all 24 platform views.

---

## Interactive Element Verification Matrix

| Module | UI Element / Label | Action Type | Client Handler | Target API Endpoint | Method | Expected Response / State Change | Audit Status |
|---|---|---|---|---|---|---|---|
| **Auth** | "Sign In" | Form Submit | `handleLogin()` | `/api/auth/login` | `POST` | Sets JWT token in storage, redirects to `/dashboard` | VERIFIED |
| **Auth** | "Create Account" | Form Submit | `handleRegister()` | `/api/auth/register` | `POST` | Creates account, navigates to `/verify-otp` | VERIFIED |
| **Auth** | "Verify OTP" | Button Click | `handleVerifyOtp()` | `/api/auth/verify-otp` | `POST` | Validates 6-digit code, activates session | VERIFIED |
| **Auth** | "Resend Code" | Button Click | `handleResendOtp()` | `/api/auth/resend-otp` | `POST` | Dispatches new OTP email with 30s cooldown | VERIFIED |
| **Auth** | "Sign Out" | Nav Action | `handleLogout()` | Client-side purge | `N/A` | Clears auth state and redirects to `/login` | VERIFIED |
| **Overview** | "Time Range" (1h/24h/7d) | Pill Selector | `setTimeRange()` | `/api/metrics/summary` | `GET` | Refetches sparklines and card metrics | VERIFIED |
| **Overview** | "Manual Refresh" | Icon Button | `fetchMetrics()` | `/api/metrics/summary` | `GET` | Immediate telemetry sync | VERIFIED |
| **Websites** | "Add Website" | Modal Open | `setShowAddModal(true)`| UI State | `N/A` | Displays website configuration modal | VERIFIED |
| **Websites** | "Save Website" | Form Submit | `handleCreateWebsite()` | `/api/websites` | `POST` | Validates URL (SSRF guard), adds table row | VERIFIED |
| **Websites** | "Check Now" | Table Action | `handleTriggerCheck(id)` | `/api/websites/{id}/check` | `POST` | Runs instant probe; updates response time/status | VERIFIED |
| **Websites** | "Pause/Resume" | Toggle Switch| `handleToggleActive(id)` | `/api/websites/{id}` | `PATCH` | Updates `is_active` status | VERIFIED |
| **Websites** | "Delete Website" | Table Action | `handleDeleteWebsite(id)`| `/api/websites/{id}` | `DELETE`| Removes site and check history from database | VERIFIED |
| **Website Detail** | "Add Sub-endpoint" | Modal Open | `setShowEndpointModal()` | UI State | `N/A` | Opens endpoint probe creator | VERIFIED |
| **Website Detail** | "Save Sub-endpoint"| Form Submit | `handleCreateEndpoint()` | `/api/websites/{id}/endpoints` | `POST` | Adds sub-path monitor (`/api/v1/health`) | VERIFIED |
| **Website Detail** | "Export SLA Data" | Button Click | `handleExportUptime()` | Client generation | `N/A` | Generates and downloads CSV uptime report | VERIFIED |
| **Alerts** | "Acknowledge" | Card Action | `handleAcknowledge(id)` | `/api/alerts/{id}/acknowledge` | `POST` | Sets status to `ACKNOWLEDGED` | VERIFIED |
| **Alerts** | "Resolve" | Modal Submit | `handleResolve(id)` | `/api/alerts/{id}/resolve` | `POST` | Sets status to `RESOLVED`, clears active badge | VERIFIED |
| **Alerts** | "Filter Severity" | Dropdown | `setSelectedSeverity()` | `/api/alerts?severity=X` | `GET` | Refilters visible alert list | VERIFIED |
| **Infrastructure** | "Cadence Selector" | Dropdown | `setPollInterval()` | WebSocket / Polling | `N/A` | Changes telemetry refresh rate (5s-60s) | VERIFIED |
| **Infrastructure** | "Sort Fleet" | Header Click | `setSortField()` | Client-side sort | `N/A` | Reorders hosts by CPU, RAM, or Disk | VERIFIED |
| **Network** | "Add Network Device"| Modal Open | `setShowDeviceModal(true)`| UI State | `N/A` | Displays device configuration modal | VERIFIED |
| **Network** | "Save Device" | Form Submit | `handleCreateDevice()` | `/api/network/devices` | `POST` | Adds device with ICMP/TCP/SNMP settings | VERIFIED |
| **Network** | "Run Probe" | Table Action | `handleProbeDevice(id)` | `/api/network/devices/{id}/check`| `POST` | Executes real-time ping and port probe | VERIFIED |
| **Network** | "Delete Device" | Table Action | `handleDeleteDevice(id)` | `/api/network/devices/{id}` | `DELETE` | Removes device record and telemetry | VERIFIED |
| **APM** | "Add Service" | Modal Open | `setShowServiceModal(true)`| UI State | `N/A` | Displays APM service creation dialog | VERIFIED |
| **APM** | "Save Service" | Form Submit | `handleCreateService()` | `/api/apm/services` | `POST` | Registers new service and outputs SDK code | VERIFIED |
| **APM** | "Copy SDK Snippet" | Button Click | `navigator.clipboard.writeText` | Client-side API | `N/A` | Copies integration snippet | VERIFIED |
| **Databases** | "Connect Database" | Modal Open | `setShowDbModal(true)` | UI State | `N/A` | Opens DB credential modal | VERIFIED |
| **Databases** | "Test Connection" | Button Click | `handleTestDb(id)` | `/api/databases/{id}/test` | `POST` | Runs live `SELECT 1` ping test | VERIFIED |
| **Databases** | "Save Integration" | Form Submit | `handleCreateDatabase()` | `/api/databases` | `POST` | Persists masked DB connection info | VERIFIED |
| **Collectors** | "Deploy Collector" | Modal Open | `setShowInstallModal()` | UI State | `N/A` | Opens collector script drawer | VERIFIED |
| **Collectors** | "Copy Script" | Button Click | `handleCopyInstall()` | Client-side API | `N/A` | Copies Docker/Shell install command | VERIFIED |
| **Collectors** | "Revoke Collector" | Danger Button| `handleRevokeCollector(id)` | `/api/collectors/{id}` | `DELETE` | Immediately invalidates collector auth token | VERIFIED |
| **Security** | "Time Horizon" | Pill Selector | `setSecurityWindow()` | `/api/metrics/security` | `GET` | Fetches threat telemetry for selected window | VERIFIED |
| **Egress Proof** | "Verify SHA-256" | Button Click | `handleVerifyHash(id)` | Web Crypto API | `N/A` | Calculates SHA-256 of payload locally; matches server | VERIFIED |
| **Egress Proof** | "Inspect Redactions"| Drawer Toggle| `setSelectedProof(id)` | UI State | `N/A` | Shows before-and-after redaction diff | VERIFIED |
| **AIOps** | "Adjust Sensitivity"| Range Slider | `setSigmaThreshold()` | `/api/incidents/aiops/correlations` | `GET` | Recalculates anomaly boundary (2.0σ - 4.0σ) | VERIFIED |
| **Incidents** | "Change Status" | Dropdown | `handleUpdateStatus(id, s)` | `/api/incidents/{id}/status` | `PATCH` | Updates incident workflow state | VERIFIED |
| **Incidents** | "Assign Operator" | Dropdown | `handleAssignOperator(id, u)` | `/api/incidents/{id}/assign` | `PATCH` | Updates incident owner | VERIFIED |
| **Recommendations**| "Send for Approval"| Card Action | `handlePromoteApproval(id)` | `/api/approvals` | `POST` | Moves AI recommendation into Approval Center | VERIFIED |
| **Approvals** | "Approve & Execute"| Modal Submit | `handleExecuteApproval(id)`| `/api/approvals/{id}/execute` | `POST` | Simulates remediation execution | VERIFIED |
| **Approvals** | "Reject Action" | Modal Submit | `handleRejectApproval(id)` | `/api/approvals/{id}/reject` | `POST` | Rejects recommendation with comment | VERIFIED |
| **Webhooks** | "Add Webhook" | Modal Open | `setShowWebhookModal(true)`| UI State | `N/A` | Opens webhook creation dialog | VERIFIED |
| **Webhooks** | "Save Webhook" | Form Submit | `handleCreateWebhook()` | `/api/webhooks` | `POST` | Creates webhook endpoint and HMAC key | VERIFIED |
| **Webhooks** | "Test Ping" | Table Action | `handleTestWebhook(id)` | `/api/webhooks/{id}/test` | `POST` | Dispatches test payload and displays status | VERIFIED |
| **Webhooks** | "Delete Webhook" | Table Action | `handleDeleteWebhook(id)` | `/api/webhooks/{id}` | `DELETE` | Deletes webhook integration | VERIFIED |
| **Global Ops** | "Region Filter" | Tab Selector | `setSelectedRegion()` | `/api/scenarios/regions` | `GET` | Filters fleet telemetry by cloud region | VERIFIED |
| **Analytics** | "Metric Selector" | Pill Selector | `setSelectedMetric()` | `/api/metrics/analytics` | `GET` | Renders timeseries for selected KPI | VERIFIED |
| **Reports** | "Generate Report" | Form Submit | `handleGenerateReport()` | `/api/reports/generate` | `POST` | Computes SLA metrics and outputs report | VERIFIED |
| **Reports** | "Download CSV/PDF" | Link Click | `handleDownload(id)` | `/api/reports/{id}/download` | `GET` | Streams generated file | VERIFIED |
| **Organization** | "Invite User" | Modal Submit | `handleInviteUser()` | `/api/organization/members` | `POST` | Adds team member to tenant | VERIFIED |
| **Organization** | "Update Role" | Dropdown | `handleUpdateRole(id)` | `/api/organization/members/{id}`| `PATCH` | Changes permission tier | VERIFIED |
| **Organization** | "Remove Member" | Danger Button| `handleRemoveMember(id)` | `/api/organization/members/{id}`| `DELETE` | Revokes organization membership | VERIFIED |
| **Developer** | "Create API Key" | Modal Submit | `handleCreateKey()` | `/api/developer/keys` | `POST` | Creates SHA-256 hashed API token | VERIFIED |
| **Developer** | "Revoke Key" | Table Action | `handleRevokeKey(id)` | `/api/developer/keys/{id}` | `DELETE` | Revokes API key immediately | VERIFIED |
| **Scenarios** | "Trigger Anomaly"| Button Click | `handleTriggerScenario(id)`| `/api/scenarios/trigger` | `POST` | Injects synthetic chaos telemetry burst | VERIFIED |
| **Scenarios** | "Reset Sandbox" | Button Click | `handleResetScenario()` | `/api/scenarios/reset` | `POST` | Restores baseline telemetry state | VERIFIED |

---

## Configuration Guard Handling

When third-party external services are unconfigured:
1. **Supabase Database**: If `SUPABASE_DB_URL` is empty in `backend/.env`, database write actions return `503 Service Unavailable` with message:  
   `"Primary Supabase PostgreSQL database is not configured. Database-dependent operations are BLOCKED BY CONFIGURATION. Please enter SUPABASE_DB_URL in backend/.env."`  
   Frontend alerts gracefully display an amber configuration banner prompting the administrator to provide their database URL.
2. **Resend Email Service**: If `RESEND_API_KEY` is empty in `backend/.env`, OTP generation returns:  
   `{"status": "BLOCKED_BY_CONFIGURATION", "message": "Email delivery service is unconfigured. Set RESEND_API_KEY in backend/.env."}`  
   Plaintext OTPs are strictly prevented from appearing in terminal logs.
