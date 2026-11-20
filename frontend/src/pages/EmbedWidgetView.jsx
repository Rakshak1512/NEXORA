import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { ShieldCheck, Server, AlertTriangle, CheckCircle2, Activity, Clock } from 'lucide-react';
import axios from 'axios';
import { API_BASE_URL } from '../services/api';

const statusConfig = {
  ALL_SYSTEMS_OPERATIONAL: {
    label: 'All Systems Operational',
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/10',
    border: 'border-emerald-500/30',
    dot: 'bg-emerald-400',
    icon: CheckCircle2
  },
  DEGRADED_PERFORMANCE: {
    label: 'Degraded Performance',
    color: 'text-amber-400',
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/30',
    dot: 'bg-amber-400',
    icon: AlertTriangle
  },
  MAJOR_OUTAGE: {
    label: 'Major Outage Reported',
    color: 'text-rose-400',
    bg: 'bg-rose-500/10',
    border: 'border-rose-500/30',
    dot: 'bg-rose-400',
    icon: AlertTriangle
  }
};

const EmbedWidgetView = () => {
  const { token } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchWidgetData = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/api/v1/embed/${token}`);
      setData(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Widget unavailable or token expired.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWidgetData();
    const interval = setInterval(fetchWidgetData, 10000);
    return () => clearInterval(interval);
  }, [token]);

  if (loading) {
    return (
      <div className="w-full h-full min-h-[220px] bg-[#070C14] flex items-center justify-center text-xs font-mono text-cyan-400">
        Loading live telemetry...
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="w-full h-full min-h-[220px] bg-[#070C14] border border-rose-500/30 p-5 rounded-2xl flex flex-col items-center justify-center text-center">
        <AlertTriangle className="w-8 h-8 text-rose-400 mb-2" />
        <p className="text-xs font-semibold text-rose-300">{error || 'Widget Inactive'}</p>
        <p className="text-[10px] text-slate-500 mt-1">Contact your system administrator.</p>
      </div>
    );
  }

  const currentStatus = statusConfig[data.status] || statusConfig.ALL_SYSTEMS_OPERATIONAL;
  const StatusIcon = currentStatus.icon;

  return (
    <div className="w-full h-full min-h-[220px] bg-[#090F1C] border border-[#1E293B] p-5 rounded-2xl text-slate-100 flex flex-col justify-between shadow-2xl font-sans select-none">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-[#1E293B]">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-lg bg-cyan-500/20 border border-cyan-500/30 flex items-center justify-center">
            <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
          </div>
          <div>
            <div className="text-xs font-bold text-slate-200 leading-tight">{data.organization_name}</div>
            <div className="text-[9px] text-slate-400">Infrastructure Health</div>
          </div>
        </div>

        <div className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider flex items-center gap-1.5 border ${currentStatus.bg} ${currentStatus.border} ${currentStatus.color}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${currentStatus.dot} animate-pulse`} />
          <span>{currentStatus.label}</span>
        </div>
      </div>

      {/* Metric Counters */}
      <div className="grid grid-cols-3 gap-2.5 my-3">
        <div className="p-2.5 rounded-xl bg-[#060A12] border border-[#1A2740] text-center">
          <div className="text-[9px] font-semibold uppercase tracking-wider text-slate-500">Node Fleet</div>
          <div className="text-sm font-bold text-slate-100 mt-0.5 flex items-center justify-center gap-1">
            <Server className="w-3 h-3 text-cyan-400" />
            <span>{data.online_collectors_count} / {data.total_collectors_count || 1}</span>
          </div>
          <div className="text-[9px] text-emerald-400 mt-0.5">Online</div>
        </div>

        <div className="p-2.5 rounded-xl bg-[#060A12] border border-[#1A2740] text-center">
          <div className="text-[9px] font-semibold uppercase tracking-wider text-slate-500">Latency</div>
          <div className="text-sm font-bold text-cyan-300 mt-0.5 flex items-center justify-center gap-1">
            <Activity className="w-3 h-3 text-cyan-400" />
            <span>{data.network_latency_ms} ms</span>
          </div>
          <div className="text-[9px] text-slate-400 mt-0.5">Internal Network</div>
        </div>

        <div className="p-2.5 rounded-xl bg-[#060A12] border border-[#1A2740] text-center">
          <div className="text-[9px] font-semibold uppercase tracking-wider text-slate-500">Incidents</div>
          <div className={`text-sm font-bold mt-0.5 ${data.active_incidents_count === 0 ? 'text-emerald-400' : 'text-amber-400'}`}>
            {data.active_incidents_count} Active
          </div>
          <div className="text-[9px] text-slate-400 mt-0.5">AIOps Correlated</div>
        </div>
      </div>

      {/* Footer Branding */}
      <div className="pt-2 border-t border-[#1E293B] flex items-center justify-between text-[9px] text-slate-500">
        <div className="flex items-center gap-1">
          <Clock className="w-2.5 h-2.5" />
          <span>Updated {new Date(data.last_updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
        </div>
        <div className="font-semibold text-cyan-400 tracking-wider">
          CYNERA &bull; ZERO-TRUST EGRESS
        </div>
      </div>
    </div>
  );
};

export default EmbedWidgetView;
