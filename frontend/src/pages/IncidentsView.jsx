import React, { useState, useEffect } from 'react';
import { 
  AlertOctagon, CheckCircle2, Clock, RefreshCw, 
  Sparkles, ArrowRight, ShieldCheck, UserCheck 
} from 'lucide-react';
import api from '../services/api';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import Button from '../components/common/Button';
import Modal from '../components/common/Modal';

const IncidentsView = () => {
  const [incidents, setIncidents] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [filterSeverity, setFilterSeverity] = useState('ALL');
  const [loading, setLoading] = useState(true);

  const fetchIncidents = async () => {
    try {
      const res = await api.get('/incidents');
      setIncidents(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIncidents();
    const interval = setInterval(fetchIncidents, 8000);
    return () => clearInterval(interval);
  }, []);

  const openDetail = async (id) => {
    try {
      const res = await api.get(`/incidents/${id}`);
      setSelectedIncident(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const updateStatus = async (status) => {
    if (!selectedIncident) return;
    try {
      await api.patch(`/incidents/${selectedIncident.id}`, {
        status,
        resolution_notes: `Status changed to ${status} by Operator Console.`
      });
      await openDetail(selectedIncident.id);
      fetchIncidents();
    } catch (e) {
      console.error(e);
    }
  };

  const filtered = incidents.filter(i => {
    if (filterSeverity === 'ALL') return true;
    return i.severity === filterSeverity;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            Incident Management & Correlation
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            AIOps-correlated incidents grouped by temporal proximity and root causes.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-[#0D1524] border border-[#1A2740] text-xs text-slate-200 focus:outline-none"
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
          </select>
          <Button variant="secondary" size="sm" onClick={fetchIncidents} icon={RefreshCw}>
            Refresh
          </Button>
        </div>
      </div>

      {/* Incidents List */}
      <div className="grid grid-cols-1 gap-4">
        {filtered.map(inc => (
          <div 
            key={inc.id}
            className="glass-panel p-5 rounded-2xl border border-[#1A2740] hover:border-cyan-500/40 transition-all cursor-pointer flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
            onClick={() => openDetail(inc.id)}
          >
            <div className="space-y-1.5 flex-1">
              <div className="flex items-center gap-2.5 flex-wrap">
                <span className="font-mono text-cyan-400 font-bold text-xs">{inc.incident_number}</span>
                <Badge variant={inc.severity === 'CRITICAL' ? 'danger' : inc.severity === 'HIGH' ? 'warning' : 'info'}>
                  {inc.severity}
                </Badge>
                <Badge variant={inc.status === 'RESOLVED' ? 'success' : inc.status === 'INVESTIGATING' ? 'warning' : 'neutral'}>
                  {inc.status}
                </Badge>
                {inc.has_ai_recommendation && (
                  <span className="inline-flex items-center gap-1 text-[10px] text-teal-300 font-mono px-2 py-0.5 rounded bg-teal-500/10 border border-teal-500/20">
                    <Sparkles className="w-3 h-3" /> AI Recommendation Ready
                  </span>
                )}
              </div>
              <h3 className="font-semibold text-slate-100 text-sm">{inc.title}</h3>
              <p className="text-xs text-slate-400 line-clamp-1">{inc.description}</p>
            </div>

            <div className="flex items-center gap-4 text-xs font-mono shrink-0">
              <span className="text-slate-400">{inc.created_at ? new Date(inc.created_at).toLocaleTimeString() : ''}</span>
              <Button variant="ghost" size="sm" icon={ArrowRight}>
                View Causal Analysis
              </Button>
            </div>
          </div>
        ))}
      </div>

      {/* Detail Modal */}
      <Modal
        isOpen={!!selectedIncident}
        onClose={() => setSelectedIncident(null)}
        title={selectedIncident ? `${selectedIncident.incident_number}: ${selectedIncident.title}` : ''}
        maxWidth="max-w-3xl"
      >
        {selectedIncident && (
          <div className="space-y-5 text-xs text-slate-300">
            {/* Status & Severity Bar */}
            <div className="flex items-center justify-between p-3.5 rounded-xl bg-[#070C14] border border-[#1A2740]">
              <div className="flex items-center gap-3">
                <Badge variant={selectedIncident.severity === 'CRITICAL' ? 'danger' : 'warning'}>
                  {selectedIncident.severity}
                </Badge>
                <span>Current Status: <strong className="text-cyan-400">{selectedIncident.status}</strong></span>
              </div>
              <div className="flex items-center gap-2">
                {selectedIncident.status !== 'ACKNOWLEDGED' && selectedIncident.status !== 'RESOLVED' && (
                  <Button variant="secondary" size="sm" onClick={() => updateStatus('ACKNOWLEDGED')}>
                    Acknowledge
                  </Button>
                )}
                {selectedIncident.status !== 'RESOLVED' && (
                  <Button variant="success" size="sm" onClick={() => updateStatus('RESOLVED')}>
                    Mark Resolved
                  </Button>
                )}
              </div>
            </div>

            {/* Description */}
            <div>
              <h4 className="font-semibold text-slate-100 uppercase tracking-wider text-[11px] mb-1">
                AIOps Incident Overview
              </h4>
              <p className="text-slate-400 leading-relaxed">{selectedIncident.description}</p>
            </div>

            {/* Correlation Reason */}
            <div className="p-3.5 rounded-xl bg-cyan-950/20 border border-cyan-500/30">
              <span className="font-semibold text-cyan-400 block mb-1">Why Signals Were Correlated:</span>
              <p className="text-slate-300">{selectedIncident.correlation_reason}</p>
            </div>

            {/* AI Recommendation Card */}
            {selectedIncident.recommendation && (
              <div className="p-4 rounded-xl bg-[#0D1524] border border-teal-500/40 space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-teal-300 flex items-center gap-1.5 text-sm">
                    <Sparkles className="w-4 h-4" /> Explainable Root-Cause Recommendation
                  </span>
                  <span className="font-mono text-emerald-400 text-xs">
                    Confidence: {selectedIncident.recommendation.confidence_score}%
                  </span>
                </div>
                <p className="text-slate-300"><strong>Possible Root Cause:</strong> {selectedIncident.recommendation.possible_root_cause}</p>
                <p className="text-slate-400"><strong>Baseline Comparison:</strong> {selectedIncident.recommendation.baseline_comparison}</p>
                <div className="p-3 rounded-lg bg-[#070C14] border border-[#1A2740] text-cyan-300">
                  <strong>Suggested Corrective Action:</strong> {selectedIncident.recommendation.suggested_action}
                </div>
                <p className="text-slate-400"><strong>Rollback Plan:</strong> {selectedIncident.recommendation.rollback_plan}</p>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default IncidentsView;

