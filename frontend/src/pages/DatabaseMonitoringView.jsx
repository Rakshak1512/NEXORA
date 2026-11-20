import React, { useState, useEffect } from 'react';
import { 
  Database, Plus, RefreshCw, CheckCircle2, AlertTriangle, 
  Activity, Clock, ShieldCheck, Zap, Trash2, Server
} from 'lucide-react';
import api from '../services/api';
import Button from '../components/common/Button';

const DatabaseMonitoringView = () => {
  const [databases, setDatabases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [testingId, setTestingId] = useState(null);

  const [form, setForm] = useState({
    name: '',
    db_type: 'postgresql',
    host: '',
    port: 5432,
    database_name: '',
    username: '',
    password: ''
  });
  const [addLoading, setAddLoading] = useState(false);
  const [addError, setAddError] = useState('');

  const fetchDatabases = async () => {
    try {
      const res = await api.get('/databases');
      setDatabases(res.data);
    } catch (err) {
      console.error('Failed to fetch database integrations', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDatabases();
    const interval = setInterval(fetchDatabases, 20000);
    return () => clearInterval(interval);
  }, []);

  const handleTestConnection = async (id) => {
    setTestingId(id);
    try {
      const res = await api.post(`/databases/${id}/test`);
      alert(res.data.message || 'Diagnostic check succeeded');
      fetchDatabases();
    } catch (err) {
      alert(err.response?.data?.detail || 'Database probe failed');
    } finally {
      setTestingId(null);
    }
  };

  const handleCreateDatabase = async (e) => {
    e.preventDefault();
    setAddError('');
    setAddLoading(true);
    try {
      await api.post('/databases', form);
      setShowAddModal(false);
      setForm({
        name: '',
        db_type: 'postgresql',
        host: '',
        port: 5432,
        database_name: '',
        username: '',
        password: ''
      });
      fetchDatabases();
    } catch (err) {
      setAddError(err.response?.data?.detail || 'Failed to connect database');
    } finally {
      setAddLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
              <Database className="w-5 h-5 text-cyan-400" />
              Database Health & Performance Monitoring
            </h1>
            <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
              Product C
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time connection pool saturation, query latency, slow queries count, and availability for PostgreSQL and MySQL.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button variant="outline" onClick={fetchDatabases} className="flex items-center gap-2 text-xs">
            <RefreshCw className="w-3.5 h-3.5 text-cyan-400" />
            <span>Refresh</span>
          </Button>

          <Button variant="primary" onClick={() => setShowAddModal(true)} className="flex items-center gap-2 text-xs">
            <Plus className="w-4 h-4" />
            <span>Connect Database</span>
          </Button>
        </div>
      </div>

      {/* Database Fleet Grid */}
      {loading ? (
        <div className="glass-panel p-12 rounded-xl border border-[#1A2740] text-center text-xs text-slate-400 font-mono">
          Loading monitored database clusters...
        </div>
      ) : databases.length === 0 ? (
        <div className="glass-panel p-12 rounded-xl border border-[#1A2740] text-center">
          <Database className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <h3 className="text-sm font-semibold text-slate-200">No Databases Connected</h3>
          <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
            Connect your PostgreSQL or MySQL database cluster to monitor connection saturation and query performance.
          </p>
          <Button variant="primary" onClick={() => setShowAddModal(true)} className="mt-4 text-xs">
            Connect First Database
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {databases.map((db) => (
            <div key={db.id} className="glass-panel p-5 rounded-xl border border-[#1A2740] hover:border-cyan-500/40 transition flex flex-col justify-between">
              <div>
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-sm font-bold text-slate-100">{db.name}</h3>
                    <p className="text-xs font-mono text-slate-400 mt-0.5">
                      {db.username}@{db.host}:{db.port}/{db.database_name}
                    </p>
                  </div>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold ${
                    db.status === 'HEALTHY' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/10 text-rose-400'
                  }`}>
                    {db.status}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 mt-4 pt-3 border-t border-[#1A2740]">
                  <div className="bg-[#070C14] p-2.5 rounded-lg border border-[#1A2740]">
                    <span className="text-[10px] text-slate-500 block">Connection Pool</span>
                    <span className="text-xs font-mono font-bold text-slate-200">
                      {db.active_connections} / {db.max_connections} ({db.connection_saturation_percent}%)
                    </span>
                    <div className="w-full bg-[#1A2740] h-1.5 rounded-full mt-1.5 overflow-hidden">
                      <div
                        className={`h-full ${db.connection_saturation_percent > 80 ? 'bg-rose-500' : 'bg-cyan-400'}`}
                        style={{ width: `${Math.min(100, db.connection_saturation_percent)}%` }}
                      />
                    </div>
                  </div>

                  <div className="bg-[#070C14] p-2.5 rounded-lg border border-[#1A2740]">
                    <span className="text-[10px] text-slate-500 block">Avg Query Latency</span>
                    <span className="text-xs font-mono font-bold text-cyan-400">
                      {db.avg_query_latency_ms} ms
                    </span>
                    <span className="text-[10px] text-slate-500 block mt-1">
                      Slow queries: {db.slow_queries_count_24h}
                    </span>
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-[#1A2740] flex items-center justify-between">
                <span className="text-[10px] text-slate-500 font-mono">
                  Checked: {db.last_checked_at ? new Date(db.last_checked_at).toLocaleTimeString() : 'Pending'}
                </span>

                <button
                  onClick={() => handleTestConnection(db.id)}
                  disabled={testingId === db.id}
                  className="px-2.5 py-1 rounded-lg bg-[#070C14] hover:bg-cyan-500/20 text-slate-300 hover:text-cyan-300 border border-[#1A2740] text-xs flex items-center gap-1.5 transition"
                >
                  <Zap className={`w-3 h-3 text-cyan-400 ${testingId === db.id ? 'animate-bounce' : ''}`} />
                  <span>{testingId === db.id ? 'Testing...' : 'Test Connection'}</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* CONNECT DATABASE MODAL */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4 backdrop-blur-xs">
          <div className="w-full max-w-md glass-panel p-6 rounded-2xl border border-[#1A2740] shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-[#1A2740] pb-3">
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <Database className="w-4 h-4 text-cyan-400" />
                Connect Database Cluster
              </h3>
              <button onClick={() => setShowAddModal(false)} className="text-slate-400 hover:text-white text-xs font-mono">✕</button>
            </div>

            {addError && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs">
                {addError}
              </div>
            )}

            <form onSubmit={handleCreateDatabase} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Friendly Cluster Name</label>
                <input
                  type="text"
                  required
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="Primary Postgres Aurora Cluster"
                  className="w-full px-3 py-2 rounded-xl bg-[#0B1322] border border-[#1A2740] text-xs text-slate-100 focus:outline-none focus:border-cyan-400"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Database Engine</label>
                  <select
                    value={form.db_type}
                    onChange={(e) => setForm({ ...form, db_type: e.target.value, port: e.target.value === 'postgresql' ? 5432 : 3306 })}
                    className="w-full px-3 py-2 rounded-xl bg-[#0B1322] border border-[#1A2740] text-xs text-slate-100 focus:outline-none focus:border-cyan-400"
                  >
                    <option value="postgresql">PostgreSQL</option>
                    <option value="mysql">MySQL</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Port</label>
                  <input
                    type="number"
                    required
                    value={form.port}
                    onChange={(e) => setForm({ ...form, port: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 rounded-xl bg-[#0B1322] border border-[#1A2740] text-xs text-slate-100 focus:outline-none focus:border-cyan-400"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Host / Endpoint</label>
                <input
                  type="text"
                  required
                  value={form.host}
                  onChange={(e) => setForm({ ...form, host: e.target.value })}
                  placeholder="db.production.internal or 10.0.4.55"
                  className="w-full px-3 py-2 rounded-xl bg-[#0B1322] border border-[#1A2740] text-xs text-slate-100 focus:outline-none focus:border-cyan-400"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Database Name</label>
                  <input
                    type="text"
                    required
                    value={form.database_name}
                    onChange={(e) => setForm({ ...form, database_name: e.target.value })}
                    placeholder="cynera_prod"
                    className="w-full px-3 py-2 rounded-xl bg-[#0B1322] border border-[#1A2740] text-xs text-slate-100 focus:outline-none focus:border-cyan-400"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Username</label>
                  <input
                    type="text"
                    required
                    value={form.username}
                    onChange={(e) => setForm({ ...form, username: e.target.value })}
                    placeholder="cynera_ro"
                    className="w-full px-3 py-2 rounded-xl bg-[#0B1322] border border-[#1A2740] text-xs text-slate-100 focus:outline-none focus:border-cyan-400"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Password</label>
                <input
                  type="password"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  placeholder="Password (Encrypted at rest)"
                  className="w-full px-3 py-2 rounded-xl bg-[#0B1322] border border-[#1A2740] text-xs text-slate-100 focus:outline-none focus:border-cyan-400"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-[#1A2740]">
                <Button variant="outline" type="button" onClick={() => setShowAddModal(false)} className="text-xs">Cancel</Button>
                <Button variant="primary" type="submit" disabled={addLoading} className="text-xs">Connect & Verify</Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default DatabaseMonitoringView;
