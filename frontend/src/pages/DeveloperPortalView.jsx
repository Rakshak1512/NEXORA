import React, { useState, useEffect } from 'react';
import { 
  Key, Code2, Layout, Copy, Check, Plus, Trash2, 
  ExternalLink, ShieldCheck, Terminal, AlertTriangle, Eye, EyeOff, X, Sparkles
} from 'lucide-react';
import api from '../services/api';
import Button from '../components/common/Button';

const DeveloperPortalView = () => {
  const [activeTab, setActiveTab] = useState('keys'); // 'keys', 'docs', 'widgets'
  
  // API Keys state
  const [apiKeys, setApiKeys] = useState([]);
  const [keysLoading, setKeysLoading] = useState(false);
  const [showCreateKeyModal, setShowCreateKeyModal] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [newKeyPerms, setNewKeyPerms] = useState(['read', 'write']);
  const [createdKeySecret, setCreatedKeySecret] = useState(null); // Revealed once!

  // Embed Widgets state
  const [widgets, setWidgets] = useState([]);
  const [widgetsLoading, setWidgetsLoading] = useState(false);
  const [showCreateWidgetModal, setShowCreateWidgetModal] = useState(false);
  const [newWidgetName, setNewWidgetName] = useState('');
  const [newWidgetType, setNewWidgetType] = useState('health_status');

  // Copy helpers
  const [copiedKeyId, setCopiedKeyId] = useState(null);
  const [copiedSnippet, setCopiedSnippet] = useState(false);

  // Active code doc tab
  const [codeLang, setCodeLang] = useState('python'); // 'python', 'curl', 'javascript'

  const fetchKeys = async () => {
    setKeysLoading(true);
    try {
      const res = await api.get('/developer/keys');
      setApiKeys(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setKeysLoading(false);
    }
  };

  const fetchWidgets = async () => {
    setWidgetsLoading(true);
    try {
      const res = await api.get('/developer/widgets');
      setWidgets(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setWidgetsLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'keys') fetchKeys();
    if (activeTab === 'widgets') fetchWidgets();
  }, [activeTab]);

  const handleCreateKey = async (e) => {
    e.preventDefault();
    try {
      const res = await api.post('/developer/keys', {
        name: newKeyName,
        permissions: newKeyPerms
      });
      setCreatedKeySecret(res.data.secret_key);
      setShowCreateKeyModal(false);
      setNewKeyName('');
      fetchKeys();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to create API key');
    }
  };

  const handleDeleteKey = async (id) => {
    if (!window.confirm('Are you sure you want to permanently revoke this API key?')) return;
    try {
      await api.delete(`/developer/keys/${id}`);
      fetchKeys();
    } catch (err) {
      alert('Failed to revoke API key');
    }
  };

  const handleCreateWidget = async (e) => {
    e.preventDefault();
    try {
      await api.post('/developer/widgets', {
        name: newWidgetName,
        widget_type: newWidgetType
      });
      setShowCreateWidgetModal(false);
      setNewWidgetName('');
      fetchWidgets();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to create embed widget');
    }
  };

  const handleDeleteWidget = async (id) => {
    if (!window.confirm('Are you sure you want to deactivate this embed widget token?')) return;
    try {
      await api.delete(`/developer/widgets/${id}`);
      fetchWidgets();
    } catch (err) {
      alert('Failed to delete widget token');
    }
  };

  const copyToClipboard = (text, id = 'snippet') => {
    navigator.clipboard.writeText(text);
    if (id === 'snippet') {
      setCopiedSnippet(true);
      setTimeout(() => setCopiedSnippet(false), 2000);
    } else {
      setCopiedKeyId(id);
      setTimeout(() => setCopiedKeyId(null), 2000);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 glass-panel rounded-2xl border border-[#1A2740] relative overflow-hidden">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 text-xs font-bold uppercase tracking-wider mb-1">
            <Code2 className="w-4 h-4" />
            Integration & Developer Hub
          </div>
          <h1 className="text-xl font-bold text-slate-100">API Keys & Embeddable Monitoring</h1>
          <p className="text-xs text-slate-400 mt-1">
            Integrate CYNERA zero-trust telemetry into your internal developer portals, CI/CD pipelines, and public status pages.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center p-1 rounded-xl bg-[#090F1C] border border-[#1A2740] text-xs">
          <button
            onClick={() => setActiveTab('keys')}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg font-semibold transition ${
              activeTab === 'keys'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Key className="w-3.5 h-3.5" />
            <span>API Keys</span>
          </button>
          <button
            onClick={() => setActiveTab('widgets')}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg font-semibold transition ${
              activeTab === 'widgets'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Layout className="w-3.5 h-3.5" />
            <span>Embed Widgets</span>
          </button>
          <button
            onClick={() => setActiveTab('docs')}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg font-semibold transition ${
              activeTab === 'docs'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Terminal className="w-3.5 h-3.5" />
            <span>REST API Docs</span>
          </button>
        </div>
      </div>

      {/* Secret Key Revealed Once Modal */}
      {createdKeySecret && (
        <div className="p-5 rounded-2xl bg-cyan-950/30 border border-cyan-500/40 relative">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2.5 text-cyan-300 font-bold text-sm">
              <Sparkles className="w-5 h-5 text-cyan-400" />
              New API Key Successfully Generated
            </div>
            <button
              onClick={() => setCreatedKeySecret(null)}
              className="text-slate-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <p className="text-xs text-slate-300 mt-2 leading-relaxed">
            Please copy this key immediately and store it securely. For your organization's security, <strong>it will never be displayed again</strong>.
          </p>

          <div className="mt-3 flex items-center gap-2 p-2.5 rounded-xl bg-[#070C14] border border-cyan-500/30 font-mono text-xs text-cyan-300">
            <span className="flex-1 truncate">{createdKeySecret}</span>
            <Button
              variant="primary"
              size="sm"
              onClick={() => copyToClipboard(createdKeySecret, 'secret')}
              className="shrink-0 flex items-center gap-1.5"
            >
              {copiedKeyId === 'secret' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedKeyId === 'secret' ? 'Copied!' : 'Copy Secret Key'}</span>
            </Button>
          </div>
        </div>
      )}

      {/* TAB 1: API KEYS */}
      {activeTab === 'keys' && (
        <div className="glass-panel rounded-2xl border border-[#1A2740] overflow-hidden">
          <div className="p-5 border-b border-[#1A2740] flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <Key className="w-4 h-4 text-cyan-400" />
                Active Organization API Keys
              </h2>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Machine-to-machine authentication tokens for external ingestion and automation.
              </p>
            </div>
            <Button
              variant="primary"
              size="sm"
              onClick={() => setShowCreateKeyModal(true)}
              className="flex items-center gap-1.5"
            >
              <Plus className="w-4 h-4" />
              <span>Generate API Key</span>
            </Button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#090F1C] text-slate-400 uppercase font-bold text-[10px] border-b border-[#1A2740]">
                <tr>
                  <th className="px-5 py-3">Key Name</th>
                  <th className="px-5 py-3">Prefix</th>
                  <th className="px-5 py-3">Permissions</th>
                  <th className="px-5 py-3">Expires</th>
                  <th className="px-5 py-3">Created</th>
                  <th className="px-5 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1A2740]">
                {apiKeys.map((k) => (
                  <tr key={k.id} className="hover:bg-[#0D1524]/60 transition">
                    <td className="px-5 py-3.5 font-semibold text-slate-200">
                      {k.name}
                    </td>
                    <td className="px-5 py-3.5 font-mono text-cyan-300">
                      {k.key_prefix}
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="flex gap-1">
                        {k.permissions.map((p) => (
                          <span key={p} className="px-2 py-0.5 rounded bg-[#131F36] border border-[#1A2740] text-[10px] text-slate-300 font-mono">
                            {p}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-5 py-3.5 text-slate-400">
                      {k.expires_at ? new Date(k.expires_at).toLocaleDateString() : 'Never'}
                    </td>
                    <td className="px-5 py-3.5 text-slate-400">
                      {new Date(k.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <button
                        onClick={() => handleDeleteKey(k.id)}
                        className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition"
                        title="Revoke key"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 2: EMBED WIDGETS */}
      {activeTab === 'widgets' && (
        <div className="space-y-6">
          <div className="glass-panel rounded-2xl border border-[#1A2740] p-5 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <Layout className="w-4 h-4 text-cyan-400" />
                Embeddable System Health & Incident Badges
              </h2>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Embed real-time zero-trust infrastructure status directly into external websites using a secure scoped iframe.
              </p>
            </div>
            <Button
              variant="primary"
              size="sm"
              onClick={() => setShowCreateWidgetModal(true)}
              className="flex items-center gap-1.5"
            >
              <Plus className="w-4 h-4" />
              <span>Create Embed Widget</span>
            </Button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {widgets.map((w) => (
              <div key={w.id} className="glass-panel p-5 rounded-2xl border border-[#1A2740] space-y-4">
                <div className="flex items-center justify-between">
                  <div className="font-bold text-slate-200 text-sm">{w.name}</div>
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      Active
                    </span>
                    <button
                      onClick={() => handleDeleteWidget(w.id)}
                      className="p-1 rounded text-slate-500 hover:text-rose-400"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Live Preview of the Widget */}
                <div className="p-4 rounded-xl bg-[#070C14] border border-[#1A2740]">
                  <div className="text-[10px] uppercase font-bold tracking-wider text-slate-500 mb-2">Live Preview</div>
                  <div className="p-4 rounded-xl bg-[#090F1C] border border-[#1E293B] shadow-lg">
                    <div className="flex items-center justify-between pb-3 border-b border-[#1E293B]">
                      <div className="flex items-center gap-2">
                        <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                        <span className="text-xs font-bold text-slate-200">ALL SYSTEMS OPERATIONAL</span>
                      </div>
                      <span className="text-[10px] text-cyan-400 font-mono font-semibold">CYNERA VERIFIED</span>
                    </div>
                    <div className="grid grid-cols-3 gap-2 mt-3 text-center">
                      <div className="p-2 rounded-lg bg-[#070C14]">
                        <div className="text-[9px] text-slate-500 uppercase font-semibold">Uptime SLA</div>
                        <div className="text-xs font-bold text-emerald-400 mt-0.5">99.98%</div>
                      </div>
                      <div className="p-2 rounded-lg bg-[#070C14]">
                        <div className="text-[9px] text-slate-500 uppercase font-semibold">Avg Latency</div>
                        <div className="text-xs font-bold text-cyan-300 mt-0.5">1.8 ms</div>
                      </div>
                      <div className="p-2 rounded-lg bg-[#070C14]">
                        <div className="text-[9px] text-slate-500 uppercase font-semibold">Incidents</div>
                        <div className="text-xs font-bold text-slate-300 mt-0.5">0 Active</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* HTML Iframe Snippet */}
                <div>
                  <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
                    <span>Embed Iframe HTML Code:</span>
                    <button
                      onClick={() => copyToClipboard(w.embed_iframe_code, w.id)}
                      className="text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1"
                    >
                      {copiedKeyId === w.id ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copiedKeyId === w.id ? 'Copied' : 'Copy HTML'}</span>
                    </button>
                  </div>
                  <pre className="p-2.5 rounded-xl bg-[#070C14] border border-[#1A2740] font-mono text-[10px] text-slate-300 overflow-x-auto whitespace-pre-wrap">
                    {w.embed_iframe_code}
                  </pre>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 3: REST API DOCUMENTATION */}
      {activeTab === 'docs' && (
        <div className="glass-panel p-6 rounded-2xl border border-[#1A2740] space-y-6">
          <div className="flex items-center justify-between border-b border-[#1A2740] pb-4">
            <div>
              <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <Terminal className="w-5 h-5 text-cyan-400" />
                CYNERA Operational API Reference
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Base URL: <code className="text-cyan-300 font-mono">http://localhost:8000/api</code>
              </p>
            </div>

            <div className="flex items-center gap-2">
              {['python', 'curl', 'javascript'].map((lang) => (
                <button
                  key={lang}
                  onClick={() => setCodeLang(lang)}
                  className={`px-3 py-1 rounded-lg text-xs font-mono font-semibold uppercase transition ${
                    codeLang === lang
                      ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {lang}
                </button>
              ))}
            </div>
          </div>

          {/* Example 1: Ingesting Telemetry */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-200">
              <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-mono text-[10px]">POST</span>
              <span>/telemetry/ingest — Tier 1 Collector Ingestion</span>
            </div>
            <pre className="p-4 rounded-xl bg-[#070C14] border border-[#1A2740] text-xs font-mono text-slate-300 overflow-x-auto">
{codeLang === 'python' ? `import requests

payload = {
    "payload_id": "pl-corp-2026-001",
    "collector_id": "col-acroglobal-01",
    "tenant_id": "11111111-1111-1111-1111-111111111111",
    "timestamp_utc": "2026-11-20T12:00:00Z",
    "cpu_utilization_pct": 24.5,
    "memory_utilization_pct": 52.1,
    "health_state": "EXCELLENT"
}

headers = {"Authorization": "Bearer cyn_live_YOUR_API_KEY"}
res = requests.post("http://localhost:8000/api/telemetry/ingest", json=payload, headers=headers)
print(res.json())` : codeLang === 'curl' ? `curl -X POST http://localhost:8000/api/telemetry/ingest \\
  -H "Authorization: Bearer cyn_live_YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "payload_id": "pl-corp-2026-001",
    "collector_id": "col-acroglobal-01",
    "tenant_id": "11111111-1111-1111-1111-111111111111",
    "timestamp_utc": "2026-11-20T12:00:00Z",
    "cpu_utilization_pct": 24.5,
    "memory_utilization_pct": 52.1,
    "health_state": "EXCELLENT"
  }'` : `const res = await fetch("http://localhost:8000/api/telemetry/ingest", {
  method: "POST",
  headers: {
    "Authorization": "Bearer cyn_live_YOUR_API_KEY",
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    payload_id: "pl-corp-2026-001",
    collector_id: "col-acroglobal-01",
    tenant_id: "11111111-1111-1111-1111-111111111111",
    timestamp_utc: new Date().toISOString(),
    cpu_utilization_pct: 24.5,
    memory_utilization_pct: 52.1,
    health_state: "EXCELLENT"
  })
});
console.log(await res.json());`}
            </pre>
          </div>
        </div>
      )}

      {/* Create Key Modal */}
      {showCreateKeyModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="glass-panel w-full max-w-md p-6 rounded-2xl border border-[#1A2740] shadow-2xl relative">
            <div className="flex items-center justify-between pb-3 border-b border-[#1A2740]">
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <Key className="w-4 h-4 text-cyan-400" />
                Generate New Organization API Key
              </h3>
              <button onClick={() => setShowCreateKeyModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateKey} className="mt-4 space-y-4 text-xs">
              <div>
                <label className="block text-slate-300 font-semibold mb-1">Key Description / Name</label>
                <input
                  type="text"
                  required
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  placeholder="e.g. Production Terraform Provisioner"
                  className="w-full px-3 py-2 rounded-xl bg-[#070C14] border border-[#1A2740] text-slate-100 focus:border-cyan-400 outline-none"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Assigned Scopes</label>
                <div className="space-y-1.5">
                  <label className="flex items-center gap-2 text-slate-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={newKeyPerms.includes('read')}
                      onChange={(e) => {
                        if (e.target.checked) setNewKeyPerms([...newKeyPerms, 'read']);
                        else setNewKeyPerms(newKeyPerms.filter(p => p !== 'read'));
                      }}
                      className="rounded bg-[#070C14] border-[#1A2740] text-cyan-400"
                    />
                    <span>Read (Metrics, Incidents, Egress Proofs)</span>
                  </label>
                  <label className="flex items-center gap-2 text-slate-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={newKeyPerms.includes('write')}
                      onChange={(e) => {
                        if (e.target.checked) setNewKeyPerms([...newKeyPerms, 'write']);
                        else setNewKeyPerms(newKeyPerms.filter(p => p !== 'write'));
                      }}
                      className="rounded bg-[#070C14] border-[#1A2740] text-cyan-400"
                    />
                    <span>Write (Ingest Telemetry, Register Collectors)</span>
                  </label>
                </div>
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <Button variant="secondary" size="sm" type="button" onClick={() => setShowCreateKeyModal(false)}>
                  Cancel
                </Button>
                <Button variant="primary" size="sm" type="submit">
                  Generate Secret Key
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Widget Modal */}
      {showCreateWidgetModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="glass-panel w-full max-w-md p-6 rounded-2xl border border-[#1A2740] shadow-2xl relative">
            <div className="flex items-center justify-between pb-3 border-b border-[#1A2740]">
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <Layout className="w-4 h-4 text-cyan-400" />
                Configure Embeddable Widget
              </h3>
              <button onClick={() => setShowCreateWidgetModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateWidget} className="mt-4 space-y-4 text-xs">
              <div>
                <label className="block text-slate-300 font-semibold mb-1">Widget Display Name</label>
                <input
                  type="text"
                  required
                  value={newWidgetName}
                  onChange={(e) => setNewWidgetName(e.target.value)}
                  placeholder="e.g. Public Customer Portal Badge"
                  className="w-full px-3 py-2 rounded-xl bg-[#070C14] border border-[#1A2740] text-slate-100 focus:border-cyan-400 outline-none"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Widget Type</label>
                <select
                  value={newWidgetType}
                  onChange={(e) => setNewWidgetType(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-[#070C14] border border-[#1A2740] text-slate-100 focus:border-cyan-400 outline-none"
                >
                  <option value="health_status">Overall Health & Uptime Status</option>
                  <option value="incident_summary">Active Incidents & Alerts</option>
                  <option value="collector_fleet">Collector Fleet Online Nodes</option>
                </select>
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <Button variant="secondary" size="sm" type="button" onClick={() => setShowCreateWidgetModal(false)}>
                  Cancel
                </Button>
                <Button variant="primary" size="sm" type="submit">
                  Generate Embed Token
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default DeveloperPortalView;

