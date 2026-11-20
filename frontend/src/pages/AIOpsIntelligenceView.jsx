import React, { useState, useEffect } from 'react';
import { BrainCircuit, Sparkles, CheckCircle2, AlertOctagon, RefreshCw, BarChart2, Layers } from 'lucide-react';
import api from '../services/api';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import Button from '../components/common/Button';

const AIOpsIntelligenceView = () => {
  const [status, setStatus] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchAIOps = async () => {
    try {
      const [sRes, aRes] = await Promise.all([
        api.get('/aiops/status'),
        api.get('/alerts')
      ]);
      setStatus(sRes.data);
      setAlerts(aRes.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAIOps();
    const interval = setInterval(fetchAIOps, 8000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            AIOps Intelligence Pipeline
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Multivariate anomaly detection, temporal event correlation, and explainable causal inference.
          </p>
        </div>
        <Button variant="secondary" size="sm" onClick={fetchAIOps} icon={RefreshCw}>
          Refresh Models
        </Button>
      </div>

      {/* Model Status Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <Card title="Anomaly Engine" icon={BrainCircuit}>
          <div className="text-xl font-bold text-cyan-400">Ensemble Mode</div>
          <span className="text-[11px] text-slate-400 mt-1 block">Z-Score + Isolation Forest</span>
        </Card>
        <Card title="Correlation Window" icon={Layers}>
          <div className="text-2xl font-bold text-teal-300">90 Seconds</div>
          <span className="text-[11px] text-slate-400 mt-1 block">Temporal graph clustering</span>
        </Card>
        <Card title="Detected Anomalies" icon={AlertOctagon}>
          <div className="text-2xl font-bold text-amber-400">{alerts.length}</div>
          <span className="text-[11px] text-slate-400 mt-1 block">Since service initialization</span>
        </Card>
        <Card title="Mean Confidence" icon={Sparkles}>
          <div className="text-2xl font-bold text-emerald-400">
            {status?.average_confidence_score ?? 94.8}%
          </div>
          <span className="text-[11px] text-slate-400 mt-1 block">Deterministic causal score</span>
        </Card>
      </div>

      {/* Explanation Architecture */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Anomaly Detection Pipeline" subtitle="How CICADA OBSERVE identifies outliers without seeing raw logs">
          <div className="space-y-4 text-xs text-slate-300">
            <div className="p-3.5 rounded-xl bg-[#070C14] border border-[#1A2740]">
              <div className="font-semibold text-cyan-400 mb-1">1. Moving Statistical Baseline (Z-Score & IQR)</div>
              <p className="text-slate-400 leading-relaxed">
                Continually computes 200-sample rolling mean and standard deviations per metric. Triggers alerts when signals exceed 3.0σ deviation.
              </p>
            </div>
            <div className="p-3.5 rounded-xl bg-[#070C14] border border-[#1A2740]">
              <div className="font-semibold text-teal-300 mb-1">2. Scikit-Learn Isolation Forest</div>
              <p className="text-slate-400 leading-relaxed">
                Evaluates 6-dimensional vectors [CPU, Memory, Disk, Latency, Loss, Auth Failure]. Identifies subtle compound failures that escape simple static thresholds.
              </p>
            </div>
            <div className="p-3.5 rounded-xl bg-[#070C14] border border-[#1A2740]">
              <div className="font-semibold text-emerald-400 mb-1">3. Privacy Guarantee</div>
              <p className="text-slate-400 leading-relaxed">
                Models operate purely on numerical quantities and categorical summaries. No customer text, SQL query strings, or IP addresses are ingested.
              </p>
            </div>
          </div>
        </Card>

        <Card title="Event Correlation & Incident Graph" subtitle="Noise reduction: collapsing alert storms into single actionable incidents">
          <div className="p-4 rounded-xl bg-[#070C14] border border-[#1A2740] font-mono text-xs space-y-3">
            <div className="text-slate-400">Incoming Alert Cluster:</div>
            <div className="flex flex-col gap-1.5 pl-3 border-l-2 border-cyan-500/40 text-slate-300">
              <span className="text-rose-400">[02:40:12] CPU_SATURATION on col-prod-core-01 (96.4%)</span>
              <span className="text-amber-400">[02:40:18] LATENCY_DEGRADATION on col-prod-core-01 (215ms)</span>
              <span className="text-teal-300">[02:40:24] GC_PAUSE_ALERT on col-prod-core-01 (&gt;800ms)</span>
            </div>
            <div className="pt-2 border-t border-[#1A2740] text-emerald-400">
              Correlator Decision: Merged into 1 unified incident:
              <div className="text-slate-200 mt-1 font-sans font-bold">
                INC-2026-0042: Worker Pool Exhaustion & Cascading Latency
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default AIOpsIntelligenceView;

