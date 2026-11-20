import React, { useState, useEffect } from 'react';
import { 
  Webhook, Plus, RefreshCw, Send, CheckCircle2, 
  AlertTriangle, Clock, Trash2, Key, Copy, Check, ExternalLink,
  AlertCircle, X
} from 'lucide-react';
import api from '../services/api';
import Button from '../components/common/Button';

const WebhookManagementView = () => {
  const [webhooks, setWebhooks] = useState([]);
  const [deliveries, setDeliveries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [testingId, setTestingId] = useState(null);
  const [testResult, setTestResult] = useState(null);
  const [copiedSecret, setCopiedSecret] = useState(null);
  const [actionFeedback, setActionFeedback] = useState(null);

  const [form, setForm] = useState({
    name: 'Slack Alerts Webhook',
    url: '',
    events: ['website.down', 'website.recovered', 'incident.created', 'alert.critical'],
    secret: ''
  });
  const [addLoading, setAddLoading] = useState(false);

  const fetchData = async () => {
    try {
      const [whRes, delRes] = await Promise.all([
        api.get('/webhooks'),
        api.get('/webhooks/deliveries')
      ]);
      setWebhooks(whRes.data);
      setDeliveries(delRes.data);
    } catch (err) {
      console.error('Failed to fetch webhooks', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleTestWebhook = async (id) => {
    setTestingId(id);
    setTestResult(null);
    setActionFeedback(null);
    try {
      const res = await api.post(`/webhooks/${id}/test`);
      setTestResult(res.data);
      setActionFeedback({
        type: 'success',
        message: `Webhook ping dispatched successfully (HTTP ${res.data.status_code || 200}).`
      });
      fetchData();
    } catch (err) {
      setTestResult({
        success: false,
        detail: err.response?.data?.detail || 'Webhook test failed'
      });
      setActionFeedback({
        type: 'error',
        message: err.response?.data?.detail || 'Webhook test transmission failed.'
      });
    } finally {
      setTestingId(null);
    }
  };

  const handleDeleteWebhook = async (id, name) => {
    setActionFeedback(null);
    try {
      await api.delete(`/webhooks/${id}`);
      setActionFeedback({
        type: 'success',
        message: `Webhook endpoint "${name || id}" removed successfully.`
      });
      fetchData();
    } catch (err) {
      setActionFeedback({
        type: 'error',
        message: err.response?.data?.detail || 'Failed to delete webhook endpoint.'
      });
    }
  };

  const handleCreateWebhook = async (e) => {
    e.preventDefault();
    setAddLoading(true);
    setActionFeedback(null);
    try {
      await api.post('/webhooks', form);
      setShowAddModal(false);
      const createdName = form.name;
      setForm({
        name: '',
        url: '',
        events: ['website.down', 'website.recovered'],
        secret: ''
      });
      setActionFeedback({
        type: 'success',
        message: `Webhook endpoint "${createdName}" registered with HMAC verification.`
      });
      fetchData();
    } catch (err) {
      setActionFeedback({
        type: 'error',
        message: err.response?.data?.detail || 'Failed to create webhook endpoint.'
      });
    } finally {
      setAddLoading(false);
    }
  };

  const copySecret = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedSecret(id);
    setTimeout(() => setCopiedSecret(null), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Webhook className="w-5 h-5 text-cyan-400" />
            Outbound Webhooks & HMAC Integrations
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Dispatch cryptographically signed HMAC-SHA256 payloads to Slack, PagerDuty, Discord, or internal APIs on incident events.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button variant="outline" onClick={fetchData} className="flex items-center gap-2 text-xs">
            <RefreshCw className="w-3.5 h-3.5 text-cyan-400" />
            <span>Refresh</span>
          </Button>

          <Button variant="primary" onClick={() => setShowAddModal(true)} className="flex items-center gap-2 text-xs">
            <Plus className="w-4 h-4" />
            <span>Create Webhook</span>
          </Button>
        </div>
      </div>

      {/* Action Feedback Banner */}
      {actionFeedback && (
        <div className={`p-4 rounded-xl text-xs flex items-center justify-between border ${
          actionFeedback.type === 'success' 
            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300' 
            : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
        }`}>
          <div className="flex items-center gap-2">
            {actionFeedback.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
            )}
            <span>{actionFeedback.message}</span>
          </div>
          <button 
            onClick={() => setActionFeedback(null)}
            className="text-slate-400 hover:text-slate-200 text-xs px-2 py-0.5"
          >
            ✕
          </button>
        </div>
      )}

      {testResult && (
        <div className={`p-4 rounded-xl text-xs flex items-center justify-between ${
          testResult.success ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-300' : 'bg-rose-500/10 border border-rose-500/30 text-rose-300'
        }`}>
          <div className="flex items-center gap-2">
            {testResult.success ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <AlertTriangle className="w-4 h-4 shrink-0" />}
            <span>{testResult.message || testResult.detail} (HTTP {testResult.status_code || 0}, {testResult.latency_ms || 0} ms)</span>
          </div>
          <button onClick={() => setTestResult(null)} className="font-mono text-xs">✕</button>
        </div>
      )}

      {/* Webhooks List */}
      <div className="space-y-3">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400">
          Configured Webhook Endpoints ({webhooks.length})
        </h2>

        {loading ? (
          <div className="glass-panel p-10 rounded-xl border border-[#1A2740] text-center text-xs text-slate-400 font-mono">
            Loading webhooks...
          </div>
        ) : webhooks.length === 0 ? (
          <div className="glass-panel p-10 rounded-xl border border-[#1A2740] text-center">
            <Webhook className="w-10 h-10 text-slate-600 mx-auto mb-3" />
            <h3 className="text-sm font-semibold text-slate-200">No Webhooks Registered</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              Send autonomous alerts and status updates to your incident management software.
            </p>
            <Button variant="primary" onClick={() => setShowAddModal(true)} className="mt-4 text-xs">
              Add Your First Webhook
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {webhooks.map((wh) => (
              <div key={wh.id} className="glass-panel p-5 rounded-xl border border-[#1A2740] space-y-4">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-sm font-bold text-slate-100">{wh.name}</h3>
                    <p className="text-xs font-mono text-slate-400 truncate max-w-xs mt-0.5" title={wh.url}>
                      {wh.url}
                    </p>
                  </div>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold ${
                    wh.is_active ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' : 'bg-slate-500/10 text-slate-400'
                  }`}>
                    {wh.is_active ? 'ACTIVE' : 'DISABLED'}
                  </span>
                </div>

                <div className="space-y-2">
                  <span className="text-[10px] text-slate-500 font-medium block">Subscribed Events:</span>
                  <div className="flex flex-wrap gap-1.5">
                    {wh.events.map((evt, idx) => (
                      <span key={idx} className="px-2 py-0.5 rounded bg-[#070C14] border border-[#1A2740] text-[10px] font-mono text-cyan-300">
                        {evt}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="p-2.5 rounded-lg bg-[#070C14] border border-[#1A2740] flex items-center justify-between text-xs">
                  <div className="flex items-center gap-1.5 text-slate-400">
                    <Key className="w-3.5 h-3.5 text-cyan-400" />
                    <span className="text-[10px] font-mono">HMAC Secret: ••••••••••••</span>
                  </div>
                  <button
                    onClick={() => copySecret(wh.secret, wh.id)}
                    className="text-[10px] text-cyan-400 hover:underline flex items-center gap-1 font-mono"
                  >
                    {copiedSecret === wh.id ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                    <span>{copiedSecret === wh.id ? 'Copied' : 'Copy'}</span>
                  </button>
                </div>

                <div className="pt-2 border-t border-[#1A2740] flex items-center justify-between">
                  <button
                    onClick={() => handleTestWebhook(wh.id)}
                    disabled={testingId === wh.id}
                    className="px-3 py-1.5 rounded-lg bg-[#070C14] hover:bg-cyan-500/20 text-slate-300 hover:text-cyan-300 border border-[#1A2740] text-xs flex items-center gap-1.5 transition"
                  >
                    <Send className={`w-3 h-3 text-cyan-400 ${testingId === wh.id ? 'animate-spin' : ''}`} />
                    <span>{testingId === wh.id ? 'Sending Ping...' : 'Test Ping Webhook'}</span>
                  </button>

                  <button
                    onClick={() => handleDeleteWebhook(wh.id)}
                    className="p-1.5 rounded text-slate-500 hover:text-rose-400 transition"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recent Deliveries Log */}
      <div className="glass-panel p-5 rounded-2xl border border-[#1A2740] space-y-4">
        <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
          <Clock className="w-4 h-4 text-cyan-400" />
          Recent Delivery Attempts & Status
        </h3>

        {deliveries.length === 0 ? (
          <div className="p-8 rounded-xl bg-[#070C14]/40 border border-[#1A2740] text-center text-xs text-slate-500">
            No webhook delivery attempts recorded yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs font-mono">
              <thead>
                <tr className="border-b border-[#1A2740] text-slate-400 text-left">
                  <th className="py-2.5 px-3">Event Type</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">HTTP Code</th>
                  <th className="py-2.5 px-3">Latency</th>
                  <th className="py-2.5 px-3">Delivered At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1A2740]/50">
                {deliveries.map((del) => (
                  <tr key={del.id} className="hover:bg-[#070C14]/50">
                    <td className="py-2.5 px-3 text-cyan-300">{del.event_type}</td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        del.status === 'success' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'
                      }`}>
                        {del.status}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-300">{del.status_code || '--'}</td>
                    <td className="py-2.5 px-3 text-slate-300">{del.latency_ms ? `${del.latency_ms.toFixed(0)} ms` : '--'}</td>
                    <td className="py-2.5 px-3 text-slate-500">{new Date(del.created_at).toLocaleTimeString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* CREATE WEBHOOK MODAL */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4 backdrop-blur-xs">
          <div className="w-full max-w-md glass-panel p-6 rounded-2xl border border-[#1A2740] shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-[#1A2740] pb-3">
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <Webhook className="w-4 h-4 text-cyan-400" />
                Register Outbound Webhook
              </h3>
              <button onClick={() => setShowAddModal(false)} className="text-slate-400 hover:text-white text-xs font-mono">✕</button>
            </div>

            <form onSubmit={handleCreateWebhook} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Webhook Name</label>
                <input
                  type="text"
                  required
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="Slack Alerts Channel"
                  className="w-full px-3 py-2 rounded-xl bg-[#0B1322] border border-[#1A2740] text-xs text-slate-100 focus:outline-none focus:border-cyan-400"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Destination URL</label>
                <input
                  type="url"
                  required
                  value={form.url}
                  onChange={(e) => setForm({ ...form, url: e.target.value })}
                  placeholder="https://hooks.slack.com/services/..."
                  className="w-full px-3 py-2 rounded-xl bg-[#0B1322] border border-[#1A2740] text-xs text-slate-100 focus:outline-none focus:border-cyan-400"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Subscribed Events</label>
                <div className="grid grid-cols-2 gap-2 text-xs text-slate-300">
                  {['website.down', 'website.recovered', 'incident.created', 'alert.critical'].map((ev) => (
                    <label key={ev} className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={form.events.includes(ev)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setForm({ ...form, events: [...form.events, ev] });
                          } else {
                            setForm({ ...form, events: form.events.filter(x => x !== ev) });
                          }
                        }}
                        className="rounded bg-[#0B1322] border-[#1A2740] text-cyan-400"
                      />
                      <span className="font-mono text-[11px]">{ev}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-[#1A2740]">
                <Button variant="outline" type="button" onClick={() => setShowAddModal(false)} className="text-xs">Cancel</Button>
                <Button variant="primary" type="submit" disabled={addLoading} className="text-xs">Register Webhook</Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default WebhookManagementView;

