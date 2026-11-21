import React, { useState, useEffect } from 'react';
import { 
  AlertOctagon, CheckCircle2, Clock, AlertTriangle, 
  ShieldAlert, RefreshCw, Check, Filter, Search,
  AlertCircle, X
} from 'lucide-react';
import api from '../services/api';
import Button from '../components/common/Button';

const AlertCenterView = () => {
  const [alerts, setAlerts] = useState([]);
  const [summary, setSummary] = useState({ total_active: 0, critical: 0, warning: 0, info: 0 });
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('active');
  const [actingId, setActingId] = useState(null);
  const [actionFeedback, setActionFeedback] = useState(null);

  const fetchAlerts = async () => {
    try {
      const [alertsRes, sumRes] = await Promise.all([
        api.get(`/alerts?alert_status=${statusFilter}${severityFilter !== 'ALL' ? `&severity=${severityFilter}` : ''}`),
        api.get('/alerts/summary')
      ]);
      setAlerts(alertsRes.data);
      setSummary(sumRes.data);
    } catch (err) {
      console.error('Failed to fetch alerts', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 15000);
    return () => clearInterval(interval);
  }, [severityFilter, statusFilter]);

  const handleAcknowledge = async (id) => {
    setActingId(id);
    setActionFeedback(null);
    try {
      await api.post(`/alerts/${id}/acknowledge`);
      setActionFeedback({ type: 'success', message: 'Alert acknowledged successfully.' });
      fetchAlerts();
    } catch (err) {
      setActionFeedback({ type: 'error', message: err.response?.data?.detail || 'Failed to acknowledge alert' });
    } finally {
      setActingId(null);
    }
  };

  const handleResolve = async (id) => {
    setActingId(id);
    setActionFeedback(null);
    try {
      await api.post(`/alerts/${id}/resolve`);
      setActionFeedback({ type: 'success', message: 'Alert marked as resolved.' });
      fetchAlerts();
    } catch (err) {
      setActionFeedback({ type: 'error', message: err.response?.data?.detail || 'Failed to resolve alert' });
    } finally {
      setActingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <AlertOctagon className="w-5 h-5 text-rose-400" />
            Centralized Alert Center
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Correlated real-time incident notifications across Website, Infrastructure, Network, APM, and Database layers.
          </p>
        </div>

        <Button variant="outline" onClick={fetchAlerts} className="flex items-center gap-2 text-xs">
          <RefreshCw className="w-3.5 h-3.5 text-cyan-400" />
          <span>Refresh Alerts</span>
        </Button>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-panel p-4 rounded-xl border border-[#1A2740]">
          <span className="text-xs text-slate-400 font-medium">Active Alerts</span>
          <p className="text-2xl font-bold text-slate-100 mt-2 font-mono">{summary.total_active}</p>
          <span className="text-[10px] text-slate-500">Unresolved operational events</span>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-[#1A2740]">
          <span className="text-xs text-slate-400 font-medium">Critical Severity</span>
          <p className="text-2xl font-bold text-rose-400 mt-2 font-mono">{summary.critical}</p>
          <span className="text-[10px] text-rose-500/80">Immediate attention needed</span>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-[#1A2740]">
          <span className="text-xs text-slate-400 font-medium">Warning Severity</span>
          <p className="text-2xl font-bold text-amber-400 mt-2 font-mono">{summary.warning}</p>
          <span className="text-[10px] text-amber-500/80">Anomaly thresholds reached</span>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-[#1A2740]">
          <span className="text-xs text-slate-400 font-medium">Info / Normal</span>
          <p className="text-2xl font-bold text-cyan-400 mt-2 font-mono">{summary.info}</p>
          <span className="text-[10px] text-slate-500">Informational system logs</span>
        </div>
      </div>

      {/* Action Feedback Banner */}
      {actionFeedback && (
        <div className={`p-3.5 rounded-xl border flex items-center justify-between text-xs ${
          actionFeedback.type === 'success' 
            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' 
            : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
        }`}>
          <div className="flex items-center gap-2">
            {actionFeedback.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 shrink-0" />
            )}
            <span>{actionFeedback.message}</span>
          </div>
          <button 
            onClick={() => setActionFeedback(null)} 
            className="text-slate-400 hover:text-white p-1"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Filters Bar */}
      <div className="glass-panel p-3 rounded-xl border border-[#1A2740] flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">Status:</span>
          {['active', 'acknowledged', 'resolved'].map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1 rounded-lg text-xs font-medium capitalize transition ${
                statusFilter === s
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                  : 'text-slate-400 hover:text-white bg-[#070C14] border border-[#1A2740]'
              }`}
            >
              {s}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">Severity:</span>
          {['ALL', 'critical', 'warning', 'info'].map((sev) => (
            <button
              key={sev}
              onClick={() => setSeverityFilter(sev)}
              className={`px-3 py-1 rounded-lg text-xs font-medium uppercase transition ${
                severityFilter === sev
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                  : 'text-slate-400 hover:text-white bg-[#070C14] border border-[#1A2740]'
              }`}
            >
              {sev}
            </button>
          ))}
        </div>
      </div>

      {/* Alerts Feed */}
      {loading ? (
        <div className="glass-panel p-10 rounded-xl border border-[#1A2740] text-center text-xs text-slate-400 font-mono">
          Loading system alerts...
        </div>
      ) : alerts.length === 0 ? (
        <div className="glass-panel p-12 rounded-xl border border-[#1A2740] text-center">
          <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto mb-3" />
          <h3 className="text-sm font-semibold text-slate-200">All Systems Operational</h3>
          <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
            No {statusFilter} alerts matched your current filter criteria. Fleet health is stable.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {alerts.map((alt) => (
            <div
              key={alt.id}
              className={`glass-panel p-4 rounded-xl border transition flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
                alt.severity === 'critical'
                  ? 'border-rose-500/40 bg-rose-950/10'
                  : alt.severity === 'warning'
                  ? 'border-amber-500/30 bg-amber-950/10'
                  : 'border-[#1A2740]'
              }`}
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2.5">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono uppercase ${
                    alt.severity === 'critical'
                      ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                      : alt.severity === 'warning'
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                      : 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                  }`}>
                    {alt.severity}
                  </span>
                  <span className="text-xs font-mono text-slate-400 px-1.5 py-0.5 rounded bg-[#070C14] border border-[#1A2740]">
                    {alt.source || alt.category || 'SYSTEM'}
                  </span>
                  <h3 className="text-sm font-bold text-slate-100">{alt.title}</h3>
                </div>
                <p className="text-xs text-slate-300">{alt.message}</p>
                <div className="flex items-center gap-4 text-[10px] font-mono text-slate-500 pt-1">
                  <span>Triggered: {new Date(alt.created_at).toLocaleString()}</span>
                  {alt.entity_id && <span>Entity: {alt.entity_id}</span>}
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                {!alt.acknowledged && alt.status === 'active' && (
                  <Button
                    variant="outline"
                    onClick={() => handleAcknowledge(alt.id)}
                    className="text-xs py-1.5 px-3"
                  >
                    Acknowledge
                  </Button>
                )}

                {alt.status !== 'resolved' && (
                  <Button
                    variant="primary"
                    onClick={() => handleResolve(alt.id)}
                    className="text-xs py-1.5 px-3 flex items-center gap-1.5"
                  >
                    <Check className="w-3.5 h-3.5" />
                    <span>Resolve</span>
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AlertCenterView;

