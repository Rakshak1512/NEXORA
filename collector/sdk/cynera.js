/**
 * CYNERA APM Node.js / JavaScript SDK
 * Lightweight, privacy-first application performance and exception tracking.
 */

const http = require('http');
const https = require('https');
const { URL } = require('url');

const SENSITIVE_REGEX = /(password|token|secret|api[_-]?key|auth|bearer|credit|card)/i;

function sanitize(obj) {
  if (obj === null || obj === undefined) return obj;
  if (typeof obj === 'string') {
    if (obj.toLowerCase().startsWith('bearer ') || (obj.length > 80 && obj.includes('.'))) {
      return '[REDACTED_CREDENTIAL]';
    }
    return obj;
  }
  if (Array.isArray(obj)) {
    return obj.map(sanitize);
  }
  if (typeof obj === 'object') {
    const clean = {};
    for (const [k, v] of Object.entries(obj)) {
      clean[k] = SENSITIVE_REGEX.test(k) ? '[REDACTED]' : sanitize(v);
    }
    return clean;
  }
  return obj;
}

class CyneraAPM {
  constructor({ apiKey, serviceName, baseUrl = 'http://localhost:8000', environment = 'production', flushInterval = 5000 }) {
    this.apiKey = apiKey;
    this.serviceName = serviceName;
    this.baseUrl = baseUrl.replace(/\/+$/, '');
    this.environment = environment;
    this.queue = [];
    this.flushInterval = flushInterval;
    this.timer = setInterval(() => this.flush(), this.flushInterval);
    if (this.timer.unref) this.timer.unref();
  }

  captureException(error, context = {}) {
    const event = {
      type: 'exception',
      service_name: this.serviceName,
      environment: this.environment,
      exception_type: error.name || 'Error',
      message: error.message || String(error),
      stack_trace: error.stack || '',
      level: 'error',
      timestamp: Date.now() / 1000,
      context: sanitize(context)
    };
    this.enqueue(event);
  }

  trackRequest(endpoint, method = 'GET', statusCode = 200, durationMs = 0, error = null) {
    const event = {
      type: 'request',
      service_name: this.serviceName,
      environment: this.environment,
      endpoint,
      method: method.toUpperCase(),
      status_code: statusCode,
      duration_ms: durationMs,
      error,
      timestamp: Date.now() / 1000
    };
    this.enqueue(event);
  }

  enqueue(item) {
    if (this.queue.length < 1000) {
      this.queue.push(item);
    }
  }

  flush() {
    if (this.queue.length === 0) return;
    const batch = this.queue.splice(0, 50);
    const payload = JSON.stringify({
      service_name: this.serviceName,
      environment: this.environment,
      events: batch
    });

    try {
      const parsedUrl = new URL(`${this.baseUrl}/api/apm/ingest`);
      const client = parsedUrl.protocol === 'https:' ? https : http;
      const req = client.request(parsedUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(payload),
          'X-CYNERA-API-KEY': this.apiKey,
          'User-Agent': 'Cynera-Node-SDK/1.0'
        },
        timeout: 5000
      }, (res) => {
        res.resume(); // Discard response
      });

      req.on('error', () => {}); // Fail silent
      req.write(payload);
      req.end();
    } catch (e) {
      // Do not crash application
    }
  }

  close() {
    if (this.timer) clearInterval(this.timer);
    this.flush();
  }
}

module.exports = CyneraAPM;

