import React, { useState, useEffect } from 'react';
import { 
  Network, Server, Cpu, Router, Shield, Activity, 
  RefreshCw, Plus, Edit2, Trash2, CheckCircle2, 
  AlertTriangle, AlertOctagon, XCircle, Clock, 
  Radio, Laptop, Info, Copy, Check, X
} from 'lucide-react';
import api from '../services/api';
import Card from '../components/common/Card';
import MetricChart from '../components/charts/MetricChart';
import Button from '../components/common/Button';
import Badge from '../components/common/Badge';
import { useWebSocket } from '../context/WebSocketContext';

const getDeviceIcon = (type) => {
  switch (type) {
    case 'Router': return Router;
    case 'Firewall': return Shield;
    case 'Switch': return Network;
    case 'Workstation': return Laptop;
    default: return Server;
  }
};

const getStatusBadge = (status) => {
  switch (status) {
    case 'ONLINE':
      return <Badge variant="success">ONLINE</Badge>;
    case 'DEGRADED':
      return <Badge variant="warning">DEGRADED</Badge>;
    case 'UNREACHABLE':
    case 'OFFLINE':
      return <Badge variant="danger">UNREACHABLE</Badge>;
    default:
      return <Badge variant="neutral">UNKNOWN</Badge>;
  }
};

const NetworkMonitoringView = () => {
  const [devices, setDevices] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [checkingId, setCheckingId] = useState(null);
  const [copiedIp, setCopiedIp] = useState(null);

  // Modals state
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingDevice, setEditingDevice] = useState(null);
  const [selectedDeviceHistory, setSelectedDeviceHistory] = useState(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [deviceToDelete, setDeviceToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [actionFeedback, setActionFeedback] = useState(null);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    ip_address: '',
    device_type: 'Server',
    monitoring_methods: ['ping', 'tcp'],
    tcp_ports: '80, 443',
    monitoring_interval_seconds: 30,
    is_active: true
  });
  const [formError, setFormError] = useState('');
  const [formSubmitting, setFormSubmitting] = useState(false);

  const { latestEvent } = useWebSocket();

  const fetchNetworkData = async () => {
    try {
      const [devRes, sumRes] = await Promise.all([
        api.get('/network/devices'),
        api.get('/network/summary')
      ]);
      setDevices(devRes.data);
      setSummary(sumRes.data);
    } catch (e) {
      console.error("Error loading network monitoring data:", e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchNetworkData();
    const interval = setInterval(fetchNetworkData, 6000);
    return () => clearInterval(interval);
  }, []);

  // Handle incoming live websocket events
  useEffect(() => {
    if (latestEvent && (latestEvent.type === "NETWORK_DEVICE_CHECKED" || latestEvent.type === "NETWORK_DEVICE_ADDED")) {
      fetchNetworkData();
    }
  }, [latestEvent]);

  const handleCopyIp = (ip) => {
    navigator.clipboard?.writeText(ip);
    setCopiedIp(ip);
    setTimeout(() => setCopiedIp(null), 2000);
  };

  const handleCheckNow = async (deviceId) => {
    setCheckingId(deviceId);
    try {
      await api.post(`/network/devices/${deviceId}/check-now`);
      await fetchNetworkData();
    } catch (e) {
      console.error("Manual check failed:", e);
    } finally {
      setCheckingId(null);
    }
  };

  const handleOpenAdd = () => {
    setFormData({
      name: '',
      ip_address: '',
      device_type: 'Server',
      monitoring_methods: ['ping', 'tcp'],
      tcp_ports: '80, 443',
      monitoring_interval_seconds: 30,
      is_active: true
    });
    setFormError('');
    setShowAddModal(true);
  };

  const handleOpenEdit = (dev) => {
    setEditingDevice(dev);
    setFormData({
      name: dev.name,
      ip_address: dev.ip_address,
      device_type: dev.device_type,
      monitoring_methods: dev.monitoring_methods || ['ping', 'tcp'],
      tcp_ports: Array.isArray(dev.tcp_ports) ? dev.tcp_ports.join(', ') : '80, 443',
      monitoring_interval_seconds: dev.monitoring_interval_seconds || 30,
      is_active: dev.is_active
    });
    setFormError('');
  };

  const handleDeleteDevice = (dev) => {
    setDeviceToDelete(dev);
  };

  const confirmDeleteDevice = async () => {
    if (!deviceToDelete) return;
    setIsDeleting(true);
    setActionFeedback(null);
    try {
      await api.delete(`/network/devices/${deviceToDelete.id}`);
      setActionFeedback({
        type: 'success',
        message: `Network device "${deviceToDelete.name}" (${deviceToDelete.ip_address}) deleted.`
      });
      setDeviceToDelete(null);
      await fetchNetworkData();
    } catch (e) {
      setActionFeedback({
        type: 'error',
        message: e.response?.data?.detail || 'Failed to delete network device.'
      });
    } finally {
      setIsDeleting(false);
    }
  };

  const handleViewHistory = async (dev) => {
    setSelectedDeviceHistory({ device: dev, history: [] });
    setHistoryLoading(true);
    try {
      const res = await api.get(`/network/devices/${dev.id}/history`);
      setSelectedDeviceHistory({ device: dev, history: res.data.history || [] });
    } catch (e) {
      console.error("Error loading history:", e);
    } finally {
      setHistoryLoading(false);
    }
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    setFormError('');
    setFormSubmitting(true);

    try {
      const parsedPorts = formData.tcp_ports
        .split(',')
        .map(p => parseInt(p.trim(), 10))
        .filter(p => !isNaN(p) && p > 0 && p <= 65535);

      const payload = {
        name: formData.name.trim(),
        ip_address: formData.ip_address.trim(),
        device_type: formData.device_type,
        monitoring_methods: formData.monitoring_methods,
        tcp_ports: parsedPorts,
        monitoring_interval_seconds: parseInt(formData.monitoring_interval_seconds, 10) || 30,
        is_active: formData.is_active
      };

      if (editingDevice) {
        await api.put(`/network/devices/${editingDevice.id}`, payload);
        setEditingDevice(null);
      } else {
        await api.post('/network/devices', payload);
        setShowAddModal(false);
      }
      await fetchNetworkData();
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to save network device.');
    } finally {
      setFormSubmitting(false);
    }
  };

  const toggleMethod = (method) => {
    setFormData(prev => {
      const exists = prev.monitoring_methods.includes(method);
      const next = exists 
        ? prev.monitoring_methods.filter(m => m !== method)
        : [...prev.monitoring_methods, method];
      return { ...prev, monitoring_methods: next };
    });
  };

  return (
    <div className="space-y-6">
      {/* 1. Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            Network Monitoring & Device Management
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Authorized IP-based reachability, ICMP latency, TCP port availability, and perimeter device health.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => { setRefreshing(true); fetchNetworkData(); }}
            icon={RefreshCw}
            disabled={refreshing}
          >
            {refreshing ? 'Updating...' : 'Refresh'}
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={handleOpenAdd}
            icon={Plus}
          >
            Add Network Device
          </Button>
        </div>
      </div>

      {/* Action Feedback Banner */}
      {actionFeedback && (
        <div className={`p-4 rounded-xl text-xs flex items-center justify-between border ${
          actionFeedback.type === 'success' 
            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300' 
            : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
        }`}>
          <div className="flex items-center gap-2">
            {actionFeedback.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
            )}
            <span>{actionFeedback.message}</span>
          </div>
          <button 
            onClick={() => setActionFeedback(null)}
            className="text-slate-400 hover:text-slate-200 text-xs px-2 py-0.5"
          >
            ✕
          </button>
        </div>
      )}

      {/* 2. Key Network Performance Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
        <div className="p-3.5 rounded-xl bg-[#0D1524] border border-[#1A2740]">
          <span className="text-[11px] text-slate-400 font-medium">Registered Devices</span>
          <div className="text-xl font-bold text-slate-100 mt-0.5">{summary?.total_devices ?? devices.length}</div>
          <div className="flex items-center gap-1.5 mt-2 text-[10px] text-emerald-400">
            <Radio className="w-3 h-3 text-cyan-400 animate-pulse" />
            <span>Active monitoring</span>
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-[#0D1524] border border-[#1A2740]">
          <span className="text-[11px] text-slate-400 font-medium">Online Devices</span>
          <div className="text-xl font-bold text-emerald-400 mt-0.5">{summary?.online_devices ?? 0}</div>
          <div className="text-[10px] text-slate-400 mt-2 font-mono">ICMP Echo Responsive</div>
        </div>

        <div className="p-3.5 rounded-xl bg-[#0D1524] border border-[#1A2740]">
          <span className="text-[11px] text-slate-400 font-medium">Unreachable / Offline</span>
          <div className={`text-xl font-bold mt-0.5 ${(summary?.unreachable_devices ?? 0) > 0 ? 'text-rose-400' : 'text-slate-400'}`}>
            {summary?.unreachable_devices ?? 0}
          </div>
          <div className="text-[10px] text-rose-400/80 mt-2 font-mono">Zero-response hosts</div>
        </div>

        <div className="p-3.5 rounded-xl bg-[#0D1524] border border-[#1A2740]">
          <span className="text-[11px] text-slate-400 font-medium">Average Latency</span>
          <div className="text-xl font-bold text-amber-400 mt-0.5">
            {summary?.avg_latency_ms ?? 1.2} ms
          </div>
          <div className="text-[10px] text-slate-400 mt-2">Target &lt; 50ms</div>
        </div>

        <div className="p-3.5 rounded-xl bg-[#0D1524] border border-[#1A2740]">
          <span className="text-[11px] text-slate-400 font-medium">Average Packet Loss</span>
          <div className="text-xl font-bold text-cyan-400 mt-0.5">
            {summary?.avg_packet_loss_pct ?? 0.0}%
          </div>
          <div className="text-[10px] text-slate-400 mt-2">Zero packet drop target</div>
        </div>

        <div className="p-3.5 rounded-xl bg-[#0D1524] border border-[#1A2740]">
          <span className="text-[11px] text-slate-400 font-medium">TCP Port Checks</span>
          <div className="text-xl font-bold text-teal-400 mt-0.5">
            {summary?.total_open_ports ?? 0} / {summary?.total_monitored_ports ?? 0}
          </div>
          <div className="text-[10px] text-slate-400 mt-2">
            {summary?.failed_port_checks ?? 0} closed / blocked
          </div>
        </div>
      </div>

      {/* 3. Registered Network Devices Management Table */}
      <Card 
        title="Authorized Network Devices" 
        subtitle="Manage monitored IP addresses, configure TCP ports, and trigger instant active checks"
        icon={Network}
      >
        {devices.length === 0 ? (
          <div className="py-12 text-center text-slate-400">
            <Network className="w-10 h-10 mx-auto text-slate-600 mb-3" />
            <p className="text-sm font-semibold text-slate-300">No network devices registered yet</p>
            <p className="text-xs text-slate-500 mt-1">Add a server, router, switch or firewall to begin IP-based monitoring.</p>
            <Button variant="primary" size="sm" onClick={handleOpenAdd} className="mt-4" icon={Plus}>
              Add Device
            </Button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#070C14] text-slate-400 uppercase font-mono text-[10px] border-b border-[#1A2740]">
                <tr>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Device Name & Type</th>
                  <th className="py-3 px-4">IP Address</th>
                  <th className="py-3 px-4">Protocols & Ports</th>
                  <th className="py-3 px-4">Latency</th>
                  <th className="py-3 px-4">Packet Loss</th>
                  <th className="py-3 px-4">Last Checked</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1A2740]">
                {devices.map((dev) => {
                  const Icon = getDeviceIcon(dev.device_type);
                  const isChecking = checkingId === dev.id;

                  return (
                    <tr key={dev.id} className="hover:bg-slate-800/30 transition">
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <span className={`w-2 h-2 rounded-full ${
                            dev.status === 'ONLINE' ? 'bg-emerald-400 animate-pulse' :
                            dev.status === 'DEGRADED' ? 'bg-amber-400' : 'bg-rose-500'
                          }`} />
                          {getStatusBadge(dev.status)}
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2.5">
                          <div className="w-7 h-7 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
                            <Icon className="w-3.5 h-3.5" />
                          </div>
                          <div>
                            <div className="font-semibold text-slate-100">{dev.name}</div>
                            <div className="text-[10px] text-slate-400">{dev.device_type}</div>
                          </div>
                        </div>
                      </td>

                      <td className="py-3 px-4 font-mono text-cyan-300">
                        <div className="flex items-center gap-1.5">
                          <span>{dev.ip_address}</span>
                          <button
                            onClick={() => handleCopyIp(dev.ip_address)}
                            title="Copy IP"
                            className="text-slate-500 hover:text-slate-300 transition"
                          >
                            {copiedIp === dev.ip_address ? (
                              <Check className="w-3 h-3 text-emerald-400" />
                            ) : (
                              <Copy className="w-3 h-3" />
                            )}
                          </button>
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        <div className="flex flex-wrap gap-1">
                          {dev.monitoring_methods?.map((m) => (
                            <span 
                              key={m} 
                              className="px-1.5 py-0.5 rounded text-[9px] font-mono uppercase bg-slate-800 border border-[#1A2740] text-slate-300"
                            >
                              {m}
                            </span>
                          ))}
                          {dev.tcp_ports?.length > 0 && (
                            <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-cyan-500/10 border border-cyan-500/20 text-cyan-300">
                              Ports: {dev.tcp_ports.join(', ')}
                            </span>
                          )}
                        </div>
                      </td>

                      <td className="py-3 px-4 font-mono">
                        <span className={dev.last_latency_ms > 100 ? 'text-rose-400 font-bold' : 'text-slate-200'}>
                          {dev.last_latency_ms.toFixed(1)} ms
                        </span>
                      </td>

                      <td className="py-3 px-4 font-mono">
                        <span className={dev.last_packet_loss_pct > 0 ? 'text-rose-400 font-bold' : 'text-emerald-400'}>
                          {dev.last_packet_loss_pct.toFixed(0)}%
                        </span>
                      </td>

                      <td className="py-3 px-4 text-slate-400 text-[11px]">
                        {dev.last_checked_at ? new Date(dev.last_checked_at).toLocaleTimeString() : 'Pending'}
                      </td>

                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => handleCheckNow(dev.id)}
                            disabled={isChecking}
                            title="Trigger instant probe"
                            className="p-1.5 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/20 text-cyan-300 transition cursor-pointer"
                          >
                            <RefreshCw className={`w-3.5 h-3.5 ${isChecking ? 'animate-spin' : ''}`} />
                          </button>

                          <button
                            onClick={() => handleViewHistory(dev)}
                            title="View Monitoring History"
                            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-[#1A2740] transition cursor-pointer"
                          >
                            <Activity className="w-3.5 h-3.5" />
                          </button>

                          <button
                            onClick={() => handleOpenEdit(dev)}
                            title="Edit Device"
                            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-[#1A2740] transition cursor-pointer"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>

                          <button
                            onClick={() => handleDeleteDevice(dev)}
                            title="Delete Device"
                            className="p-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 transition cursor-pointer"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* 4. Recent Network Alerts */}
      <Card title="Recent Network Alerts & Outliers" icon={AlertTriangle}>
        {(!summary?.recent_alerts || summary.recent_alerts.length === 0) ? (
          <div className="py-8 text-center text-slate-500 text-xs">
            <CheckCircle2 className="w-8 h-8 mx-auto text-emerald-400/60 mb-2" />
            Zero active network anomalies detected across all monitored subnets.
          </div>
        ) : (
          <div className="space-y-2">
            {summary.recent_alerts.map((alert) => (
              <div 
                key={alert.id}
                className="p-3 rounded-lg bg-[#070C14] border border-[#1A2740] flex items-center justify-between gap-4"
              >
                <div className="flex items-center gap-2.5">
                  <AlertOctagon className={`w-4 h-4 shrink-0 ${
                    alert.severity === 'CRITICAL' ? 'text-rose-400' : 'text-amber-400'
                  }`} />
                  <div>
                    <span className="font-semibold text-slate-200 text-xs">{alert.alert_type}</span>
                    <p className="text-[11px] text-slate-400 mt-0.5">{alert.message}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <Badge variant={alert.severity === 'CRITICAL' ? 'danger' : 'warning'}>
                    {alert.severity}
                  </Badge>
                  <span className="text-[10px] text-slate-500 font-mono">
                    {alert.detected_at ? new Date(alert.detected_at).toLocaleTimeString() : ''}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* 5. ADD / EDIT DEVICE MODAL */}
      {(showAddModal || editingDevice) && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-[#0D1524] w-full max-w-lg rounded-2xl border border-[#1A2740] shadow-2xl p-6 relative">
            <div className="flex items-center justify-between pb-4 border-b border-[#1A2740] mb-4">
              <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                <Network className="w-5 h-5 text-cyan-400" />
                {editingDevice ? 'Edit Network Device' : 'Register New Network Device'}
              </h3>
              <button 
                onClick={() => { setShowAddModal(false); setEditingDevice(null); }}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {formError && (
              <div className="mb-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs">
                {formError}
              </div>
            )}

            <form onSubmit={handleFormSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                  Device Name
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g. Core-Edge-Router-01"
                  className="w-full px-3 py-2 rounded-lg bg-[#070C14] border border-[#1A2740] text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-cyan-400"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                    IP Address or Hostname
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.ip_address}
                    onChange={(e) => setFormData({ ...formData, ip_address: e.target.value })}
                    placeholder="127.0.0.1 or 10.0.1.1"
                    className="w-full px-3 py-2 rounded-lg bg-[#070C14] border border-[#1A2740] text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-cyan-400 font-mono"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                    Device Type
                  </label>
                  <select
                    value={formData.device_type}
                    onChange={(e) => setFormData({ ...formData, device_type: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-[#070C14] border border-[#1A2740] text-sm text-slate-100 focus:outline-none focus:border-cyan-400"
                  >
                    <option value="Server">Server</option>
                    <option value="Router">Router</option>
                    <option value="Switch">Switch</option>
                    <option value="Firewall">Firewall</option>
                    <option value="Workstation">Workstation</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Authorized Monitoring Methods
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {['ping', 'tcp', 'snmp', 'ssh', 'syslog'].map((m) => {
                    const active = formData.monitoring_methods.includes(m);
                    return (
                      <button
                        type="button"
                        key={m}
                        onClick={() => toggleMethod(m)}
                        className={`px-3 py-1.5 rounded-lg border text-xs font-mono uppercase transition flex items-center justify-between ${
                          active 
                            ? 'bg-cyan-500/10 border-cyan-400 text-cyan-300' 
                            : 'bg-[#070C14] border-[#1A2740] text-slate-400 hover:text-slate-200'
                        }`}
                      >
                        <span>{m}</span>
                        {active && <Check className="w-3.5 h-3.5" />}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                  Monitored TCP Ports (Comma-separated)
                </label>
                <input
                  type="text"
                  value={formData.tcp_ports}
                  onChange={(e) => setFormData({ ...formData, tcp_ports: e.target.value })}
                  placeholder="e.g. 80, 443, 22, 8000"
                  className="w-full px-3 py-2 rounded-lg bg-[#070C14] border border-[#1A2740] text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-cyan-400 font-mono"
                />
                <span className="text-[10px] text-slate-500 mt-1 block">
                  Checks port reachability and connection handshake latency without full payload transmission.
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                    Check Interval (Seconds)
                  </label>
                  <select
                    value={formData.monitoring_interval_seconds}
                    onChange={(e) => setFormData({ ...formData, monitoring_interval_seconds: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-[#070C14] border border-[#1A2740] text-sm text-slate-100 focus:outline-none focus:border-cyan-400"
                  >
                    <option value={10}>10 seconds</option>
                    <option value={15}>15 seconds</option>
                    <option value={30}>30 seconds</option>
                    <option value={60}>60 seconds</option>
                    <option value={300}>5 minutes</option>
                  </select>
                </div>

                <div className="flex items-center gap-3 pt-6">
                  <input
                    type="checkbox"
                    id="is_active"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="w-4 h-4 rounded text-cyan-500 bg-[#070C14] border-[#1A2740]"
                  />
                  <label htmlFor="is_active" className="text-xs font-semibold text-slate-300">
                    Enable Monitoring
                  </label>
                </div>
              </div>

              <div className="pt-4 border-t border-[#1A2740] flex items-center justify-end gap-3">
                <Button 
                  type="button" 
                  variant="ghost" 
                  size="sm" 
                  onClick={() => { setShowAddModal(false); setEditingDevice(null); }}
                >
                  Cancel
                </Button>
                <Button 
                  type="submit" 
                  variant="primary" 
                  size="sm" 
                  disabled={formSubmitting}
                >
                  {formSubmitting ? 'Saving...' : (editingDevice ? 'Update Device' : 'Register Device')}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 6. DEVICE MONITORING HISTORY MODAL */}
      {selectedDeviceHistory && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-[#0D1524] w-full max-w-3xl rounded-2xl border border-[#1A2740] shadow-2xl p-6 relative max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between pb-4 border-b border-[#1A2740] mb-4 shrink-0">
              <div>
                <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                  <Activity className="w-5 h-5 text-cyan-400" />
                  {selectedDeviceHistory.device.name} — Monitoring History
                </h3>
                <span className="text-xs font-mono text-cyan-300">
                  {selectedDeviceHistory.device.ip_address} • {selectedDeviceHistory.device.device_type}
                </span>
              </div>
              <button 
                onClick={() => setSelectedDeviceHistory(null)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="overflow-y-auto space-y-4 pr-1">
              {/* Latency Timeseries Chart */}
              <div className="p-4 rounded-xl bg-[#070C14] border border-[#1A2740]">
                <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider block mb-3">
                  Historical Transit Latency Trend (ms)
                </span>
                {selectedDeviceHistory.history.length > 0 ? (
                  <MetricChart 
                    data={selectedDeviceHistory.history.map(h => ({
                      timestamp: h.recorded_at ? new Date(h.recorded_at).toLocaleTimeString() : '',
                      latency: h.latency_ms,
                      packet_loss: h.packet_loss_pct
                    })).reverse()} 
                    dataKey="latency" 
                    name="Latency" 
                    unit="ms" 
                    color="#00E5FF" 
                    height={180} 
                  />
                ) : (
                  <div className="py-6 text-center text-xs text-slate-500">
                    No historical probe data collected yet.
                  </div>
                )}
              </div>

              {/* Check Result Log Table */}
              <div className="border border-[#1A2740] rounded-xl overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#070C14] text-slate-400 font-mono text-[10px] uppercase border-b border-[#1A2740]">
                    <tr>
                      <th className="py-2.5 px-3">Timestamp</th>
                      <th className="py-2.5 px-3">Status</th>
                      <th className="py-2.5 px-3">Latency</th>
                      <th className="py-2.5 px-3">Packet Loss</th>
                      <th className="py-2.5 px-3">Open TCP Ports</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1A2740]">
                    {selectedDeviceHistory.history.map((rec) => (
                      <tr key={rec.id} className="hover:bg-slate-800/20">
                        <td className="py-2 px-3 text-slate-400 font-mono text-[11px]">
                          {rec.recorded_at ? new Date(rec.recorded_at).toLocaleString() : ''}
                        </td>
                        <td className="py-2 px-3">
                          {getStatusBadge(rec.status)}
                        </td>
                        <td className="py-2 px-3 font-mono text-amber-300">
                          {rec.latency_ms.toFixed(1)} ms
                        </td>
                        <td className="py-2 px-3 font-mono text-cyan-300">
                          {rec.packet_loss_pct.toFixed(0)}%
                        </td>
                        <td className="py-2 px-3 font-mono text-[11px]">
                          {rec.open_ports?.length > 0 ? (
                            <span className="text-emerald-400">
                              {rec.open_ports.join(', ')}
                            </span>
                          ) : (
                            <span className="text-rose-400">None open</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deviceToDelete && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="glass-panel w-full max-w-sm p-6 rounded-2xl border border-rose-500/30 shadow-2xl relative">
            <h3 className="text-sm font-bold text-rose-300 flex items-center gap-2 mb-2">
              <Trash2 className="w-4 h-4 text-rose-400" />
              Delete Network Device
            </h3>
            <p className="text-xs text-slate-300 leading-relaxed mb-4">
              Are you sure you want to delete network device <strong className="text-white">{deviceToDelete.name}</strong> ({deviceToDelete.ip_address})? Active probing and historical metrics will be removed.
            </p>
            <div className="flex justify-end gap-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setDeviceToDelete(null)}
                disabled={isDeleting}
              >
                Cancel
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={confirmDeleteDevice}
                disabled={isDeleting}
              >
                {isDeleting ? 'Deleting...' : 'Confirm Delete'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default NetworkMonitoringView;
