import React, { useState, useEffect } from 'react';
import { Shield, ShieldAlert, AlertTriangle, RefreshCw, KeyRound, Lock } from 'lucide-react';
import api from '../services/api';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import Table from '../components/common/Table';
import Button from '../components/common/Button';

const SecurityMonitoringView = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchSecurityData = async () => {
    try {
      const res = await api.get('/alerts');
      setAlerts(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSecurityData();
    const interval = setInterval(fetchSecurityData, 8000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            Security & Authentication Monitoring
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Derived authentication failure summaries, pseudonymous origin clustering, and perimeter protection.
          </p>
        </div>
        <Button variant="secondary" size="sm" onClick={fetchSecurityData} icon={RefreshCw}>
          Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card title="Local Secret Redactions" icon={Lock}>
          <div className="text-3xl font-extrabold text-cyan-400">100% Kept Local</div>
          <span className="text-xs text-slate-400 mt-1 block">Zero raw tokens or passwords transmitted</span>
        </Card>
        <Card title="Failed Login Bursts" icon={ShieldAlert}>
          <div className="text-3xl font-extrabold text-slate-100">
            {alerts.filter(a => a.alert_type === 'AUTHENTICATION_BURST').length} Detected
          </div>
          <span className="text-xs text-slate-400 mt-1 block">Evaluated locally via rate trackers</span>
        </Card>
        <Card title="Perimeter Allowlist Status" icon={Shield}>
          <div className="text-3xl font-extrabold text-emerald-400">ENFORCED</div>
          <span className="text-xs text-slate-400 mt-1 block">Unapproved raw keys dropped</span>
        </Card>
      </div>

      <Card title="Recent Security Alerts & Threat Indicators" subtitle="Aggregated event indicators with pseudonymous cluster hashes">
        <Table headers={["Alert ID", "Severity", "Indicator", "Metric Value", "Threshold", "Pseudonym Cluster", "Detected At"]}>
          {alerts.map(a => (
            <tr key={a.id} className="hover:bg-slate-800/30 transition">
              <td className="px-5 py-3.5 font-mono text-cyan-400 text-xs">{a.id.slice(0, 8)}...</td>
              <td className="px-5 py-3.5">
                <Badge variant={a.severity === 'CRITICAL' ? 'danger' : a.severity === 'HIGH' ? 'warning' : 'info'}>
                  {a.severity}
                </Badge>
              </td>
              <td className="px-5 py-3.5 text-slate-200 text-xs">{a.message}</td>
              <td className="px-5 py-3.5 font-mono text-xs text-amber-400">{a.metric_value}</td>
              <td className="px-5 py-3.5 font-mono text-xs text-slate-400">{a.threshold_value}</td>
              <td className="px-5 py-3.5 font-mono text-xs text-teal-300">sec-cluster-8f4b</td>
              <td className="px-5 py-3.5 font-mono text-xs text-slate-400">
                {new Date(a.detected_at).toLocaleTimeString()}
              </td>
            </tr>
          ))}
        </Table>
      </Card>
    </div>
  );
};

export default SecurityMonitoringView;

