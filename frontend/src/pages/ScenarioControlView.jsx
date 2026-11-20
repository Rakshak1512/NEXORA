import React, { useState } from 'react';
import { 
  Sliders, Play, CheckCircle2, AlertOctagon, 
  WifiOff, Layers, Cpu, HardDrive, ShieldAlert, Sparkles 
} from 'lucide-react';
import api from '../services/api';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import Badge from '../components/common/Badge';

/**
 * 13 MANDATORY HACKATHON TEST SCENARIOS:
 * 1. Normal system operation
 * 2. CPU spike
 * 3. Memory spike
 * 4. Disk spike
 * 5. Network latency increase
 * 6. Packet loss increase
 * 7. Repeated failed logins
 * 8. Collector offline
 * 9. SaaS outage
 * 10. Recovery after outage
 * 11. Duplicate payload
 * 12. Out-of-order payload
 * 13. Multiple alerts for one incident
 */
const ScenarioControlView = () => {
  const [activeScenario, setActiveScenario] = useState(null);
  const [lastResult, setLastResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const scenarios = [
    { id: 'normal', name: '1. Normal System Operation', icon: CheckCircle2, desc: 'Nominal telemetry operating within baseline sigma.' },
    { id: 'cpu_spike', name: '2. CPU Saturation Spike', icon: Cpu, desc: 'Surges CPU to 97.4%, triggering anomaly detector.' },
    { id: 'memory_spike', name: '3. Memory Heap Saturation', icon: Layers, desc: 'Surges memory utilization to 94.2%.' },
    { id: 'disk_spike', name: '4. Disk Storage Exhaustion', icon: HardDrive, desc: 'Fills persistent disk volume to 96.8%.' },
    { id: 'latency_increase', name: '5. Network Latency Increase', icon: Sliders, desc: 'Surges cross-regional latency to 312ms.' },
    { id: 'packet_loss_increase', name: '6. Packet Loss Surge', icon: AlertOctagon, desc: 'Surges packet drop rate to 7.8%.' },
    { id: 'failed_logins', name: '7. Repeated Failed Logins', icon: ShieldAlert, desc: 'Simulates credential stuffing burst (65 failures/min).' },
    { id: 'collector_offline', name: '8. Collector Offline Watchdog', icon: WifiOff, desc: 'Halts heartbeats to test 60s auto-downgrade.' },
    { id: 'saas_outage', name: '9. SaaS Outage Simulation', icon: WifiOff, desc: 'Tests Tier 1 SQLite persistent buffering on disk.' },
    { id: 'recovery_after_outage', name: '10. Recovery After Outage', icon: CheckCircle2, desc: 'Re-establishes connection and flushes backlog.' },
    { id: 'duplicate_payload', name: '11. Duplicate Payload Idempotency', icon: Sliders, desc: 'Submits identical payload_id twice to verify zero dupes.' },
    { id: 'out_of_order_payload', name: '12. Out-of-Order Timestamp', icon: Sliders, desc: 'Submits earlier UTC event to verify event-time sorting.' },
    { id: 'multi_alert_single_incident', name: '13. Multiple Alerts for 1 Incident', icon: Sparkles, desc: 'Compound CPU + memory + latency spike correlated into one incident.' },
  ];

  const trigger = async (scenarioId) => {
    setActiveScenario(scenarioId);
    setLoading(true);
    setLastResult(null);
    try {
      const res = await api.post('/scenarios/trigger', { scenario: scenarioId });
      setLastResult(res.data);
    } catch (e) {
      console.error(e);
      setLastResult({ error: "Scenario trigger failed or endpoint unreachable." });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
          Scenario Control Center
          <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
            13 LIVE SCENARIOS
          </span>
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Trigger live failure injections to test end-to-end AIOps correlation, redaction, and autonomous remediation.
        </p>
      </div>

      {lastResult && (
        <div className="p-4 rounded-xl bg-[#0D1524] border border-cyan-500/40 text-xs font-mono">
          <div className="text-cyan-400 font-bold mb-1">Scenario Result:</div>
          <pre className="text-slate-300 whitespace-pre-wrap">{JSON.stringify(lastResult, null, 2)}</pre>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {scenarios.map(sc => {
          const Icon = sc.icon;
          const isCurrent = activeScenario === sc.id;
          return (
            <div 
              key={sc.id}
              className={`p-4 rounded-xl glass-panel border transition-all ${
                isCurrent ? 'border-cyan-400 shadow-lg shadow-cyan-500/10' : 'border-[#1A2740] hover:border-slate-700'
              }`}
            >
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400">
                  <Icon className="w-4 h-4" />
                </div>
                <h4 className="font-semibold text-slate-200 text-xs">{sc.name}</h4>
              </div>
              <p className="text-[11px] text-slate-400 mb-4 h-8">{sc.desc}</p>
              <Button
                variant={isCurrent ? "primary" : "secondary"}
                size="sm"
                icon={Play}
                disabled={loading && isCurrent}
                onClick={() => trigger(sc.id)}
                className="w-full text-xs"
              >
                {loading && isCurrent ? 'Injecting...' : 'Inject Scenario'}
              </Button>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ScenarioControlView;

