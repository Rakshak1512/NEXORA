import React, { useState, useEffect } from 'react';
import { Server, RefreshCw, CheckCircle2, AlertTriangle, Shield, Clock } from 'lucide-react';
import api from '../services/api';
import Card from '../components/common/Card';
import Table from '../components/common/Table';
import Badge from '../components/common/Badge';
import Button from '../components/common/Button';

const CollectorsView = () => {
  const [collectors, setCollectors] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchCollectors = async () => {
    try {
      const res = await api.get('/collectors');
      setCollectors(res.data);
    } catch (e) {
      console.error("Failed to fetch collectors", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCollectors();
    const interval = setInterval(fetchCollectors, 8000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            Collector Fleet Management
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Tier 1 on-premises Python collectors reporting heartbeats and local buffer health.
          </p>
        </div>

        <Button
          variant="secondary"
          size="sm"
          onClick={fetchCollectors}
          icon={RefreshCw}
        >
          Refresh Fleet
        </Button>
      </div>

      {/* Fleet Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-400">Total Enrolled Agents</span>
            <div className="text-2xl font-bold text-slate-100 mt-1">{collectors.length}</div>
          </div>
          <div className="p-3 rounded-xl bg-cyan-500/10 text-cyan-400">
            <Server className="w-6 h-6" />
          </div>
        </Card>

        <Card className="flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-400">Online & Streaming</span>
            <div className="text-2xl font-bold text-emerald-400 mt-1">
              {collectors.filter(c => c.status === 'online').length}
            </div>
          </div>
          <div className="p-3 rounded-xl bg-emerald-500/10 text-emerald-400">
            <CheckCircle2 className="w-6 h-6" />
          </div>
        </Card>

        <Card className="flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-400">Offline Watchdog Alerts</span>
            <div className="text-2xl font-bold text-rose-400 mt-1">
              {collectors.filter(c => c.status === 'offline').length}
            </div>
          </div>
          <div className="p-3 rounded-xl bg-rose-500/10 text-rose-400">
            <AlertTriangle className="w-6 h-6" />
          </div>
        </Card>
      </div>

      {/* Fleet Table */}
      <Card title="Active Enrolled Telemetry Daemons" subtitle="Heartbeat status evaluated every 15s; auto-downgraded to offline if missing > 60s">
        <Table headers={["Collector ID", "Node Name", "Pseudonymous Host", "Version", "Cadence", "Status", "Last Seen"]}>
          {collectors.map(c => (
            <tr key={c.id} className="hover:bg-slate-800/30 transition">
              <td className="px-5 py-3.5 font-mono text-cyan-400 font-medium">{c.id}</td>
              <td className="px-5 py-3.5 text-slate-200">{c.name}</td>
              <td className="px-5 py-3.5 font-mono text-xs text-slate-400">{c.ip_address_pseudonym}</td>
              <td className="px-5 py-3.5 text-xs text-slate-300 font-mono">v{c.version}</td>
              <td className="px-5 py-3.5 text-xs text-slate-400">{c.collection_interval_seconds}s</td>
              <td className="px-5 py-3.5">
                <Badge variant={c.status === 'online' ? 'success' : 'danger'}>
                  {c.status.toUpperCase()}
                </Badge>
              </td>
              <td className="px-5 py-3.5 text-xs text-slate-400 font-mono">
                {c.last_seen_at ? new Date(c.last_seen_at).toLocaleTimeString() : 'Never'}
              </td>
            </tr>
          ))}
        </Table>
      </Card>
    </div>
  );
};

export default CollectorsView;

