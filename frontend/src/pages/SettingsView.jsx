import React, { useState, useEffect } from 'react';
import { Settings, Shield, Sliders, Save, CheckCircle2, AlertTriangle } from 'lucide-react';
import api from '../services/api';
import Card from '../components/common/Card';
import Button from '../components/common/Button';

const SettingsView = () => {
  const [settings, setSettings] = useState(null);
  const [saving, setSaving] = useState(false);
  const [cpuCritical, setCpuCritical] = useState(90);
  const [memWarning, setMemWarning] = useState(80);
  const [latencyWarning, setLatencyWarning] = useState(100);
  const [actionFeedback, setActionFeedback] = useState(null);

  useEffect(() => {
    api.get('/settings').then(res => {
      setSettings(res.data);
      if (res.data?.thresholds) {
        setCpuCritical(res.data.thresholds.cpu_critical_pct ?? 90);
        setMemWarning(res.data.thresholds.memory_warning_pct ?? 80);
        setLatencyWarning(res.data.thresholds.latency_warning_ms ?? 100);
      }
    }).catch(console.error);
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setActionFeedback(null);
    try {
      await api.post('/settings', {
        thresholds: {
          cpu_critical_pct: parseFloat(cpuCritical),
          memory_warning_pct: parseFloat(memWarning),
          latency_warning_ms: parseFloat(latencyWarning)
        }
      });
      setActionFeedback({
        type: 'success',
        message: 'Platform thresholds and policy settings persisted successfully.'
      });
      setTimeout(() => setActionFeedback(null), 4000);
    } catch (err) {
      setActionFeedback({
        type: 'error',
        message: err.response?.data?.detail || 'Failed to persist settings.'
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            Platform Settings & Thresholds
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Configure AIOps sensitivity, alert thresholds, and local redaction rules.
          </p>
        </div>
        <Button variant="primary" size="sm" onClick={handleSave} disabled={saving} icon={Save}>
          {saving ? 'Saving...' : 'Save Configuration'}
        </Button>
      </div>

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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="AIOps Alert Thresholds" icon={Sliders}>
          <div className="space-y-3 text-xs">
            <div>
              <label className="block text-slate-400 mb-1">CPU Critical Threshold (%)</label>
              <input 
                type="number" 
                value={cpuCritical} 
                onChange={(e) => setCpuCritical(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-[#070C14] border border-[#1A2740] text-slate-200 focus:border-cyan-400 outline-none" 
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Memory Warning Threshold (%)</label>
              <input 
                type="number" 
                value={memWarning} 
                onChange={(e) => setMemWarning(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-[#070C14] border border-[#1A2740] text-slate-200 focus:border-cyan-400 outline-none" 
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Transit Latency Warning (ms)</label>
              <input 
                type="number" 
                value={latencyWarning} 
                onChange={(e) => setLatencyWarning(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-[#070C14] border border-[#1A2740] text-slate-200 focus:border-cyan-400 outline-none" 
              />
            </div>
          </div>
        </Card>

        <Card title="Perimeter Security & Redaction Strictness" icon={Shield}>
          <div className="space-y-3 text-xs text-slate-300">
            <div className="p-3 rounded-lg bg-[#070C14] border border-[#1A2740]">
              <span className="font-semibold text-cyan-400 block mb-0.5">Local Redactor Mode: MAXIMUM</span>
              <p className="text-[11px] text-slate-400">AWS Keys, Bearer Tokens, Passwords, and Connection Strings scrubbed locally.</p>
            </div>
            <div className="p-3 rounded-lg bg-[#070C14] border border-[#1A2740]">
              <span className="font-semibold text-teal-300 block mb-0.5">Allowlist Enforcement: STRICT</span>
              <p className="text-[11px] text-slate-400">Non-allowlisted keys are unconditionally rejected before queue insertion.</p>
            </div>
            <div className="p-3 rounded-lg bg-[#070C14] border border-[#1A2740]">
              <span className="font-semibold text-emerald-400 block mb-0.5">Autonomous Remediation: SAFE (Human-in-the-Loop)</span>
              <p className="text-[11px] text-slate-400">Operator sign-off required prior to simulated container recycles.</p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default SettingsView;

