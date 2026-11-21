import React, { useEffect, useMemo, useState } from 'react';
import { Play, CheckCircle2, AlertTriangle, WifiOff, Layers, Cpu, HardDrive, ShieldAlert, Sparkles, Database, Activity, RefreshCw } from 'lucide-react';
import api from '../services/api';
import Button from '../components/common/Button';

const iconFor = (id) => {
  if (id.includes('cpu')) return Cpu;
  if (id.includes('memory')) return Layers;
  if (id.includes('disk')) return HardDrive;
  if (id.includes('login') || id.includes('suspicious')) return ShieldAlert;
  if (id.includes('database')) return Database;
  if (id.includes('network') || id.includes('latency') || id.includes('packet') || id.includes('outage') || id.includes('collector')) return WifiOff;
  if (id.includes('normal') || id.includes('recovery')) return CheckCircle2;
  if (id.includes('application')) return Activity;
  return Sparkles;
};

const groupLabel = (group) => ({
  positive: 'Healthy / false-positive checks',
  warning: 'Warning conditions',
  failure: 'Failure and security conditions',
  edge_case: 'Data integrity edge cases',
  recovery: 'Recovery and resilience'
}[group] || 'Other scenarios');

const ScenarioControlView = () => {
  const [cases, setCases] = useState([]);
  const [activeScenario, setActiveScenario] = useState(null);
  const [lastResult, setLastResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [catalogError, setCatalogError] = useState('');

  const loadCatalog = async () => {
    try {
      const res = await api.get('/scenarios/catalog');
      setCases(res.data?.cases || []);
      setCatalogError('');
    } catch (e) {
      setCatalogError(e?.response?.data?.detail || 'Could not load the demo scenario catalog. Check demo mode and API connection.');
    }
  };

  useEffect(() => { loadCatalog(); }, []);

  const groups = useMemo(() => {
    const order = ['positive', 'warning', 'failure', 'edge_case', 'recovery'];
    return order.map(group => ({ group, items: cases.filter(item => item.group === group) })).filter(x => x.items.length);
  }, [cases]);

  const trigger = async (scenarioId) => {
    setActiveScenario(scenarioId);
    setLoading(true);
    setLastResult(null);
    try {
      const res = await api.post('/scenarios/trigger', { scenario: scenarioId });
      setLastResult(res.data);
    } catch (e) {
      setLastResult({
        scenario: scenarioId,
        error: e?.response?.data?.detail || 'Scenario trigger failed or endpoint unreachable.',
        status_code: e?.response?.status || null
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            Scenario Control Center
            <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
              {cases.length} SYNTHETIC TESTS
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Run controlled demo telemetry through CYNERA's ingestion and detection pipeline. These scenarios do not touch real infrastructure.
          </p>
        </div>
        <Button variant="secondary" size="sm" icon={RefreshCw} onClick={loadCatalog}>Refresh cases</Button>
      </div>

      {catalogError && <div className="p-3 rounded-xl border border-amber-500/30 bg-amber-500/10 text-amber-200 text-sm">{catalogError}</div>}

      {lastResult && (
        <div className="p-4 rounded-xl bg-[#0D1524] border border-cyan-500/40 text-xs font-mono">
          <div className="text-cyan-400 font-bold mb-2">Scenario execution result</div>
          <pre className="text-slate-300 whitespace-pre-wrap break-words">{JSON.stringify(lastResult, null, 2)}</pre>
          <p className="mt-3 text-amber-300">Injection success is not proof of detection. Verify generated alerts and incidents to determine whether the expected detection occurred.</p>
        </div>
      )}

      {groups.map(({ group, items }) => (
        <section key={group} className="space-y-3">
          <h2 className="text-sm font-semibold text-slate-200">{groupLabel(group)}</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {items.map(sc => {
              const Icon = iconFor(sc.id);
              const isCurrent = activeScenario === sc.id;
              return (
                <div key={sc.id} className={`p-4 rounded-xl glass-panel border transition-all ${isCurrent ? 'border-cyan-400 shadow-lg shadow-cyan-500/10' : 'border-[#1A2740] hover:border-slate-700'}`}>
                  <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400"><Icon className="w-4 h-4" /></div>
                    <h3 className="font-semibold text-slate-200 text-xs">{sc.name}</h3>
                  </div>
                  <p className="text-[11px] text-slate-400 mb-2">{sc.input}</p>
                  <p className="text-[11px] text-cyan-300 mb-4">Expected: {sc.expected_detection}</p>
                  <Button variant={isCurrent ? "primary" : "secondary"} size="sm" icon={Play}
                    disabled={loading} onClick={() => trigger(sc.id)} className="w-full text-xs">
                    {loading && isCurrent ? 'Running test...' : 'Run demo test'}
                  </Button>
                </div>
              );
            })}
          </div>
        </section>
      ))}
      {!cases.length && !catalogError && <div className="text-sm text-slate-400">Loading synthetic scenarios...</div>}
    </div>
  );
};

export default ScenarioControlView;
