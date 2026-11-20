import React, { useState, useEffect } from 'react';
import { History, Shield, RefreshCw } from 'lucide-react';
import api from '../services/api';
import Card from '../components/common/Card';
import Table from '../components/common/Table';
import Badge from '../components/common/Badge';
import Button from '../components/common/Button';

const AuditLogsView = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchLogs = async () => {
    try {
      const res = await api.get('/audit/logs');
      setLogs(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            System Compliance & Audit Ledger
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Immutable log of operator approvals, status modifications, and system events.
          </p>
        </div>
        <Button variant="secondary" size="sm" onClick={fetchLogs} icon={RefreshCw}>
          Refresh
        </Button>
      </div>

      <Card title="Operator Actions & Governance Log">
        <Table headers={["Log ID", "Action", "Entity Type", "Entity ID", "Details", "Timestamp"]}>
          {logs.map(l => (
            <tr key={l.id} className="hover:bg-slate-800/30 transition font-mono text-xs">
              <td className="px-5 py-3 text-cyan-400 font-bold">{l.id.slice(0, 8)}...</td>
              <td className="px-5 py-3 text-slate-200">
                <Badge variant={l.action.includes('APPROVED') ? 'success' : 'neutral'}>
                  {l.action}
                </Badge>
              </td>
              <td className="px-5 py-3 text-slate-400">{l.entity_type}</td>
              <td className="px-5 py-3 text-slate-400 truncate max-w-[120px]">{l.entity_id}</td>
              <td className="px-5 py-3 text-slate-300 truncate max-w-[200px]">{JSON.stringify(l.details)}</td>
              <td className="px-5 py-3 text-slate-400">
                {l.created_at ? new Date(l.created_at).toLocaleTimeString() : 'N/A'}
              </td>
            </tr>
          ))}
        </Table>
      </Card>
    </div>
  );
};

export default AuditLogsView;

