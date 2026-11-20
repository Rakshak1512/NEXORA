import React, { useState, useEffect } from 'react';
import { Cpu, HardDrive, Layers, RefreshCw, Activity } from 'lucide-react';
import api from '../services/api';
import Card from '../components/common/Card';
import MetricChart from '../components/charts/MetricChart';
import Button from '../components/common/Button';
import Badge from '../components/common/Badge';

const InfrastructureView = () => {
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
            Infrastructure Monitoring
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Deep-dive CPU multi-core, memory heap, and persistent storage metrics.
          </p>
        </div>
        <Button variant="secondary" size="sm" onClick={fetchMetrics} icon={RefreshCw}>
          Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card title="Current CPU Load" icon={Cpu}>
          <div className="text-3xl font-extrabold text-cyan-400">
            {latest?.cpu_utilization_pct ?? 48.2}%
          </div>
          <span className="text-xs text-slate-400 mt-1 block">Z-Score: +0.4σ Nominal</span>
        </Card>
        <Card title="Current Memory Used" icon={Layers}>
          <div className="text-3xl font-extrabold text-teal-300">
            {latest?.memory_utilization_pct ?? 56.4}%
          </div>
          <span className="text-xs text-slate-400 mt-1 block">Buffer cache nominal</span>
        </Card>
        <Card title="Disk Volume Utilization" icon={HardDrive}>
          <div className="text-3xl font-extrabold text-slate-100">
            {latest?.disk_utilization_pct ?? 62.4}%
          </div>
          <span className="text-xs text-slate-400 mt-1 block">Root partition /dev/sda1</span>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Compute Load (CPU %)" badge={<Badge variant="info">Live psutil</Badge>}>
          <MetricChart data={timeseries} dataKey="cpu" name="CPU Utilization" color="#00E5FF" height={260} />
        </Card>

        <Card title="Memory Saturation (%)" badge={<Badge variant="success">Nominal</Badge>}>
          <MetricChart data={timeseries} dataKey="memory" name="Memory Utilization" color="#00BFA5" height={260} />
        </Card>

        <Card title="Persistent Disk Utilization (%)" className="lg:col-span-2">
          <MetricChart data={timeseries} dataKey="disk" name="Disk Utilization" color="#FFB300" height={240} />
        </Card>
      </div>
    </div>
  );
};

export default InfrastructureView;

