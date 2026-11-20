import React, { useState, useEffect } from 'react';
import { Settings, Shield, Sliders, Save, CheckCircle2 } from 'lucide-react';
import api from '../services/api';
import Card from '../components/common/Card';
import Button from '../components/common/Button';

const SettingsView = () => {
  const [settings, setSettings] = useState(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.get('/settings').then(res => setSettings(res.data)).catch(console.error);
  }, []);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
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
        <Button variant="primary" size="sm" onClick={handleSave} icon={Save}>
          {saved ? 'Saved Successfully!' : 'Save Configuration'}
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="AIOps Alert Thresholds" icon={Sliders}>
          <div className="space-y-3 text-xs">
            <div>
              <label className="block text-slate-400 mb-1">CPU Critical Threshold (%)</label>
              <input type="number" defaultValue={90} className="w-full px-3 py-2 rounded-lg bg-[#070C14] border border-[#1A2740] text-slate-200" />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Memory Warning Threshold (%)</label>
              <input type="number" defaultValue={80} className="w-full px-3 py-2 rounded-lg bg-[#070C14] border border-[#1A2740] text-slate-200" />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Transit Latency Warning (ms)</label>
              <input type="number" defaultValue={100} className="w-full px-3 py-2 rounded-lg bg-[#070C14] border border-[#1A2740] text-slate-200" />
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

