import React, { useState, useEffect } from 'react';
import { 
  Cpu, Activity, AlertOctagon, Terminal, Copy, Check, 
  Layers, Code2, RefreshCw, Zap, Clock, ShieldCheck
} from 'lucide-react';
import api from '../services/api';
import Button from '../components/common/Button';

const ApplicationMonitoringView = () => {
  const [services, setServices] = useState([]);
  const [exceptions, setExceptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedSdkTab, setSelectedSdkTab] = useState('python');
  const [copied, setCopied] = useState(false);
  const [expandedException, setExpandedException] = useState(null);

  const fetchData = async () => {
    try {
      const [svcRes, excRes] = await Promise.all([
        api.get('/apm/services'),
        api.get('/apm/exceptions')
      ]);
      setServices(svcRes.data);
      setExceptions(excRes.data);
    } catch (err) {
      console.error('Failed to fetch APM data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, []);

  const pythonSnippet = `# Install or copy collector/sdk/cynera.py
from cynera import CyneraAPM

# Initialize with your CYNERA API key
apm = CyneraAPM(
    api_key="cyn_live_your_api_key_here",
    service_name="payment-service",
    environment="production",
    base_url="http://localhost:8000"
)

# Automatic or manual error capturing
try:
    risky_operation()
except Exception as e:
    apm.capture_exception(e, context={"user_id": "usr_948", "action": "checkout"})

# Track HTTP request throughput & latency
apm.track_request(endpoint="/api/v1/charge", method="POST", status_code=200, duration_ms=45.2)`;

  const nodeSnippet = `// Install or copy collector/sdk/cynera.js
const CyneraAPM = require('./cynera');

const apm = new CyneraAPM({
  apiKey: 'cyn_live_your_api_key_here',
  serviceName: 'order-api-node',
  environment: 'production',
  baseUrl: 'http://localhost:8000'
});

// Capture unhandled errors or catch blocks
try {
  processOrder();
} catch (err) {
  apm.captureException(err, { orderId: 'ord_1289', amount: 199.50 });
}

// Track HTTP latency & throughput in Express middleware
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    apm.trackRequest(req.path, req.method, res.statusCode, Date.now() - start);
  });
  next();
});`;

  const copyCode = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
              <Layers className="w-5 h-5 text-cyan-400" />
              Application Performance Monitoring (APM)
            </h1>
            <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
              Product C
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Track distributed services, error rates, throughput (RPM), p95 latency, and stack traces via lightweight SDKs.
          </p>
        </div>

        <Button
          variant="outline"
          onClick={fetchData}
          className="flex items-center gap-2 text-xs"
        >
          <RefreshCw className="w-3.5 h-3.5 text-cyan-400" />
          <span>Refresh Services</span>
        </Button>
      </div>

      {/* Services Grid */}
      <div className="space-y-3">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400">
          Registered Microservices & Applications ({services.length})
        </h2>

        {loading ? (
          <div className="glass-panel p-10 rounded-xl border border-[#1A2740] text-center text-xs text-slate-400 font-mono">
            Loading APM services...
          </div>
        ) : services.length === 0 ? (
          <div className="glass-panel p-8 rounded-xl border border-[#1A2740] text-center text-xs text-slate-400">
            No APM services registered yet. Integrate the Cynera SDK below to begin capturing traces and exceptions.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {services.map((svc) => (
              <div key={svc.id} className="glass-panel p-5 rounded-xl border border-[#1A2740] hover:border-cyan-500/40 transition">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-sm font-bold text-slate-100">{svc.name}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-[#070C14] border border-[#1A2740] text-slate-300">
                        {svc.environment}
                      </span>
                      <span className="text-[10px] text-slate-500">{svc.framework || svc.language}</span>
                    </div>
                  </div>

                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold ${
                    svc.status === 'HEALTHY' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/10 text-rose-400'
                  }`}>
                    {svc.status}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 mt-4 pt-3 border-t border-[#1A2740]">
                  <div className="bg-[#070C14] p-2 rounded-lg border border-[#1A2740]">
                    <span className="text-[9px] text-slate-500 block">Throughput</span>
                    <span className="text-xs font-mono font-bold text-slate-200">{svc.throughput_rpm} rpm</span>
                  </div>
                  <div className="bg-[#070C14] p-2 rounded-lg border border-[#1A2740]">
                    <span className="text-[9px] text-slate-500 block">Error Rate</span>
                    <span className={`text-xs font-mono font-bold ${svc.error_rate_percent > 1 ? 'text-rose-400' : 'text-emerald-400'}`}>
                      {svc.error_rate_percent}%
                    </span>
                  </div>
                  <div className="bg-[#070C14] p-2 rounded-lg border border-[#1A2740]">
                    <span className="text-[9px] text-slate-500 block">p95 Latency</span>
                    <span className="text-xs font-mono font-bold text-cyan-400">{svc.p95_latency_ms} ms</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Exception & Error Tracker */}
      <div className="glass-panel p-5 rounded-2xl border border-[#1A2740] space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <AlertOctagon className="w-4 h-4 text-rose-400" />
              Application Exception & Error Tracker
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">Captured stack traces with sensitive credential auto-redaction</p>
          </div>
          <span className="text-xs font-mono text-slate-500">{exceptions.length} recorded events</span>
        </div>

        {exceptions.length === 0 ? (
          <div className="p-8 rounded-xl bg-[#070C14]/40 border border-[#1A2740] text-center text-xs text-slate-500">
            No unhandled exceptions reported in the last 24 hours. Applications are executing cleanly.
          </div>
        ) : (
          <div className="space-y-2">
            {exceptions.map((exc) => (
              <div
                key={exc.id}
                onClick={() => setExpandedException(expandedException === exc.id ? null : exc.id)}
                className="p-3.5 rounded-xl bg-[#070C14] border border-[#1A2740] hover:border-slate-700 cursor-pointer transition space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30">
                      {exc.exception_type}
                    </span>
                    <span className="text-xs font-semibold text-slate-200 truncate max-w-md">{exc.message}</span>
                  </div>
                  <div className="flex items-center gap-3 text-xs font-mono text-slate-400">
                    <span className="text-slate-500">{exc.service_name}</span>
                    <span>{new Date(exc.created_at).toLocaleTimeString()}</span>
                  </div>
                </div>

                {expandedException === exc.id && exc.stack_trace && (
                  <div className="mt-3 p-3 rounded-lg bg-[#040810] border border-[#1A2740] font-mono text-[11px] text-slate-300 overflow-x-auto whitespace-pre">
                    {exc.stack_trace}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Integration Code Guide */}
      <div className="glass-panel p-5 rounded-2xl border border-[#1A2740] space-y-4">
        <div className="flex items-center justify-between border-b border-[#1A2740] pb-3">
          <div className="flex items-center gap-2">
            <Code2 className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-bold text-slate-100">CYNERA SDK Integration Guide</h3>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setSelectedSdkTab('python')}
              className={`px-3 py-1 rounded-lg text-xs font-medium font-mono transition ${
                selectedSdkTab === 'python'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Python
            </button>
            <button
              onClick={() => setSelectedSdkTab('node')}
              className={`px-3 py-1 rounded-lg text-xs font-medium font-mono transition ${
                selectedSdkTab === 'node'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Node.js
            </button>
          </div>
        </div>

        <div className="relative">
          <button
            onClick={() => copyCode(selectedSdkTab === 'python' ? pythonSnippet : nodeSnippet)}
            className="absolute top-3 right-3 p-1.5 rounded-lg bg-[#070C14] hover:bg-cyan-500/20 text-slate-400 hover:text-cyan-300 border border-[#1A2740] transition text-xs flex items-center gap-1.5"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Copied' : 'Copy SDK Code'}</span>
          </button>

          <pre className="p-4 rounded-xl bg-[#040810] border border-[#1A2740] font-mono text-xs text-cyan-300/90 overflow-x-auto leading-relaxed">
            {selectedSdkTab === 'python' ? pythonSnippet : nodeSnippet}
          </pre>
        </div>
      </div>
    </div>
  );
};

export default ApplicationMonitoringView;

