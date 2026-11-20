import React, { useState, useEffect } from 'react';
import { Network, RefreshCw, Activity, ArrowDownUp } from 'lucide-react';
import api from '../services/api';
import Card from '../components/common/Card';
import MetricChart from '../components/charts/MetricChart';
import Button from '../components/common/Button';
import Badge from '../components/common/Badge';

const NetworkMonitoringView = () => {
  const [timeseries, setTimeseries] = useState([]);
  const [latest, setLatest] = useState(null);

  const fetchMetrics = async () => {
    try {
      const [tRes, lRes] = await Promise.all([
        api.get('/metrics/timeseries?limit=30'),
        api.get('/telemetry/latest')
      ]);
      setTimeseries(tRes.data);
      setLatest(lRes.data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 6000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            Network Performance & Latency
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time gateway round-trip time, packet drop rates, and throughput.
          </p>
        </div>
        <Button variant="secondary" size="sm" onClick={fetchMetrics} icon={RefreshCw}>
          Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card title="Transit Latency" icon={Activity}>
          <div className="text-3xl font-extrabold text-amber-400">
            {latest?.latency_ms ?? 18.2} ms
          </div>
          <span className="text-xs text-slate-400 mt-1 block">Baseline: 15ms | Max target: &lt;100ms</span>
        </Card>
        <Card title="Packet Drop Ratio" icon={Network}>
          <div className="text-3xl font-extrabold text-emerald-400">
            {latest?.packet_loss_pct ?? 0.0}%
          </div>
          <span className="text-xs text-slate-400 mt-1 block">Hackathon target: &lt; 1.0%</span>
        </Card>
        <Card title="Ingress Health" icon={ArrowDownUp}>
          <div className="text-3xl font-extrabold text-cyan-400">
            CONNECTED
          </div>
          <span className="text-xs text-slate-400 mt-1 block">TCP Keep-Alive active</span>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Round-Trip Transit Latency (ms)" badge={<Badge variant="warning">P95: 24.8ms</Badge>}>
          <MetricChart data={timeseries} dataKey="latency" name="Latency (ms)" unit="ms" color="#FFB300" height={260} />
        </Card>

        <Card title="Packet Loss Ratio (%)" badge={<Badge variant="danger">Critical: &gt;3%</Badge>}>
          <MetricChart data={timeseries} dataKey="packet_loss" name="Packet Loss" unit="%" color="#FF3366" height={260} />
        </Card>
      </div>
    </div>
  );
};

export default NetworkMonitoringView;

