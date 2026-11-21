import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Globe, Plus, RefreshCw, CheckCircle2, AlertTriangle, 
  XCircle, Clock, ShieldCheck, ShieldAlert, ArrowUpRight, 
  Search, ExternalLink, Zap, Lock, Shield, Trash2, AlertCircle, X
} from 'lucide-react';
import api from '../services/api';
import Button from '../components/common/Button';

const WebsiteMonitoringView = () => {
  const [websites, setWebsites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [checkingId, setCheckingId] = useState(null);
  const [actionFeedback, setActionFeedback] = useState(null);
  const [siteToDelete, setSiteToDelete] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  // Add Modal State
  const [showAddModal, setShowAddModal] = useState(false);
  const [addForm, setAddForm] = useState({
    name: '',
    url: '',
    monitoring_interval_seconds: 60,
    check_timeout_seconds: 10,
    http_method: 'GET',
    expected_status_codes: '200,201,301,302',
    follow_redirects: true,
    check_ssl: true,
    ssl_expiry_warning_days: 30
  });
  const [addLoading, setAddLoading] = useState(false);
  const [addError, setAddError] = useState('');

  // Ownership Verify Modal
  const [verifySite, setVerifySite] = useState(null);
  const [verifyMethod, setVerifyMethod] = useState('dns_txt');
  const [verifyLoading, setVerifyLoading] = useState(false);
  const [verifyResult, setVerifyResult] = useState(null);

  const fetchWebsites = async () => {
    try {
      const res = await api.get('/websites');
      setWebsites(res.data);
    } catch (err) {
      console.error('Failed to fetch monitored websites', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchWebsites();
    const interval = setInterval(fetchWebsites, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleManualCheck = async (e, id) => {
    e.preventDefault();
    e.stopPropagation();
    setCheckingId(id);
    setActionFeedback(null);
    try {
      const res = await api.post(`/websites/${id}/check`);
      setActionFeedback({
        type: 'success',
        message: `Synthetic probe completed: ${res.data.new_status} (${res.data.response_time_ms}ms, HTTP ${res.data.status_code || 200})`
      });
      fetchWebsites();
    } catch (err) {
      setActionFeedback({
        type: 'error',
        message: err.response?.data?.detail || 'Manual availability probe failed.'
      });
    } finally {
      setCheckingId(null);
    }
  };

  const handleDeleteWebsite = async (id, name) => {
    setDeletingId(id);
    try {
      await api.delete(`/websites/${id}`);
      setActionFeedback({
        type: 'success',
        message: `Monitored target "${name}" removed successfully.`
      });
      setSiteToDelete(null);
      fetchWebsites();
    } catch (err) {
      setActionFeedback({
        type: 'error',
        message: err.response?.data?.detail || 'Failed to delete monitored target.'
      });
    } finally {
      setDeletingId(null);
    }
  };

  const handleCreateWebsite = async (e) => {
    e.preventDefault();
    setAddError('');

    const targetName = addForm.name.trim();
    const rawUrl = addForm.url.trim();
    if (!targetName) {
      setAddError('Enter a friendly name for this monitoring target.');
      return;
    }
    if (!rawUrl) {
      setAddError('Enter a public website URL, hostname, or public IP address.');
      return;
    }

    // The backend performs authoritative SSRF/DNS validation. Here we only
    // normalise common input forms so users can enter a hostname or public IP.
    let normalisedUrl = rawUrl;
    if (!/^[a-z][a-z0-9+.-]*:\/\//i.test(normalisedUrl)) {
      if (normalisedUrl.includes(':') && !normalisedUrl.startsWith('[')) {
        const ipv6Candidate = normalisedUrl.replace(/^\[|\]$/g, '');
        if (ipv6Candidate.split(':').length > 2 && /^[0-9a-f:.]+$/i.test(ipv6Candidate)) {
          normalisedUrl = `https://[${ipv6Candidate}]`;
        } else {
          normalisedUrl = `https://${normalisedUrl}`;
        }
      } else {
        normalisedUrl = `https://${normalisedUrl}`;
      }
    }

    setAddLoading(true);
    try {
      const payload = {
        ...addForm,
        name: targetName,
        url: normalisedUrl
      };
      await api.post('/websites', payload);
      setShowAddModal(false);
      setAddForm({
        name: '',
        url: '',
        monitoring_interval_seconds: 60,
        check_timeout_seconds: 10,
        http_method: 'GET',
        expected_status_codes: '200,201,301,302',
        follow_redirects: true,
        check_ssl: true,
        ssl_expiry_warning_days: 30
      });
      await fetchWebsites();
      setActionFeedback({
        type: 'success',
        message: 'Website added. Verify domain ownership to enable monitoring.'
      });
    } catch (err) {
      const serverDetail = err.response?.data?.detail;
      if (Array.isArray(serverDetail)) {
        setAddError(serverDetail.map(item => item.msg || String(item)).join(' '));
      } else if (typeof serverDetail === 'string' && serverDetail.trim()) {
        setAddError(serverDetail);
      } else if (!err.response) {
        setAddError('Cannot reach the CYNERA backend. Check your connection and try again.');
      } else {
        setAddError(`Website could not be added (HTTP ${err.response.status}). Check the backend logs for details.`);
      }
    } finally {
      setAddLoading(false);
    }
  };

  const handleVerifyOwnership = async () => {
    if (!verifySite) return;
    setVerifyLoading(true);
    setVerifyResult(null);
    try {
      const res = await api.post(`/websites/${verifySite.id}/verify-ownership`, {
        method: verifyMethod
      });
      setVerifyResult(res.data);
      if (res.data.verified) {
        fetchWebsites();
      }
    } catch (err) {
      setVerifyResult({
        verified: false,
        message: err.response?.data?.detail || 'Verification error occurred'
      });
    } finally {
      setVerifyLoading(false);
    }
  };

  const filteredWebsites = websites.filter(w => {
    const matchesSearch = w.name.toLowerCase().includes(search.toLowerCase()) || 
                          w.url.toLowerCase().includes(search.toLowerCase());
    if (filterStatus === 'ALL') return matchesSearch;
    return matchesSearch && w.status === filterStatus;
  });

  const totalSites = websites.length;
  const onlineSites = websites.filter(w => w.status === 'ONLINE').length;
  const downSites = websites.filter(w => w.status === 'DOWN' || w.status === 'DEGRADED').length;
  const avgUptime = totalSites > 0 
    ? (websites.reduce((acc, w) => acc + (w.uptime_percentage_24h || 100), 0) / totalSites).toFixed(2)
    : '100.00';
  const sslWarningCount = websites.filter(w => w.ssl_days_remaining !== null && w.ssl_days_remaining <= 30).length;

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
              <Globe className="w-5 h-5 text-cyan-400" />
              Website & Synthetic URL Monitoring
            </h1>
            <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
              Zero Collector Required
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Autonomous HTTP/HTTPS uptime probes, SSL/TLS certificate lifespan tracking, and DNS resolution validation.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            onClick={() => { setRefreshing(true); fetchWebsites(); }}
            disabled={refreshing}
            className="flex items-center gap-2 text-xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-cyan-400' : ''}`} />
            <span>Refresh</span>
          </Button>

          <Button
            variant="primary"
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 text-xs shadow-lg shadow-cyan-500/20"
          >
            <Plus className="w-4 h-4" />
            <span>Add Monitored URL</span>
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="glass-panel p-4 rounded-xl border border-[#1A2740]">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">Monitored Targets</span>
            <Globe className="w-4 h-4 text-cyan-400" />
          </div>
          <p className="text-2xl font-bold text-slate-100 mt-2 font-mono">{totalSites}</p>
          <span className="text-[10px] text-slate-500">Autonomous SaaS probes</span>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-[#1A2740]">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">Online & Healthy</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-2xl font-bold text-emerald-400 mt-2 font-mono">{onlineSites}</p>
          <span className="text-[10px] text-emerald-500/80">Operating within SLA</span>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-[#1A2740]">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">Degraded / Down</span>
            <AlertTriangle className="w-4 h-4 text-rose-400" />
          </div>
          <p className="text-2xl font-bold text-rose-400 mt-2 font-mono">{downSites}</p>
          <span className="text-[10px] text-rose-500/80">Requires investigation</span>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-[#1A2740]">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">Avg Uptime (24h)</span>
            <Clock className="w-4 h-4 text-cyan-400" />
          </div>
          <p className="text-2xl font-bold text-cyan-400 mt-2 font-mono">{avgUptime}%</p>
          <span className="text-[10px] text-slate-500">Global fleet SLA</span>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-[#1A2740]">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">SSL Expiry &lt; 30d</span>
            <ShieldAlert className="w-4 h-4 text-amber-400" />
          </div>
          <p className="text-2xl font-bold text-amber-400 mt-2 font-mono">{sslWarningCount}</p>
          <span className="text-[10px] text-amber-500/80">Proactive renewal notice</span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="glass-panel p-3 rounded-xl border border-[#1A2740] flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by domain, URL or service name..."
            className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-[#070C14] border border-[#1A2740] text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          {['ALL', 'ONLINE', 'DEGRADED', 'DOWN', 'PENDING'].map((status) => (
            <button
              key={status}
              onClick={() => setFilterStatus(status)}
              className={`px-3 py-1 rounded-lg text-xs font-medium transition ${
                filterStatus === status
                  ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/30'
                  : 'text-slate-400 hover:text-slate-200 bg-[#070C14] border border-[#1A2740]'
              }`}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      {/* Action Feedback Banner */}
      {actionFeedback && (
        <div className={`p-3.5 rounded-xl border flex items-center justify-between text-xs ${
          actionFeedback.type === 'success' 
            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' 
            : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
        }`}>
          <div className="flex items-center gap-2">
            {actionFeedback.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 shrink-0" />
            )}
            <span>{actionFeedback.message}</span>
          </div>
          <button 
            onClick={() => setActionFeedback(null)} 
            className="text-slate-400 hover:text-white p-1"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Website Cards Grid */}
      {loading ? (
        <div className="glass-panel p-12 rounded-xl border border-[#1A2740] text-center text-slate-400 font-mono text-xs">
          Loading synthetic monitoring targets...
        </div>
      ) : filteredWebsites.length === 0 ? (
        <div className="glass-panel p-12 rounded-xl border border-[#1A2740] text-center">
          <Globe className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <h3 className="text-sm font-semibold text-slate-200">No Monitored Websites Found</h3>
          <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
            Add your company domain or public API endpoints to start autonomous uptime, SSL and DNS monitoring.
          </p>
          <Button
            variant="primary"
            onClick={() => setShowAddModal(true)}
            className="mt-4 text-xs"
          >
            Add Your First Website
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredWebsites.map((site) => (
            <div
              key={site.id}
              className="glass-panel rounded-xl border border-[#1A2740] hover:border-cyan-500/40 transition duration-200 p-5 flex flex-col justify-between group"
            >
              <div>
                {/* Header row */}
                <div className="flex items-start justify-between gap-3">
                  <div className="truncate">
                    <h3 className="text-sm font-bold text-slate-100 truncate group-hover:text-cyan-300 transition">
                      {site.name}
                    </h3>
                    <a
                      href={site.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-slate-400 hover:text-cyan-400 font-mono flex items-center gap-1 mt-0.5 truncate"
                    >
                      <span className="truncate">{site.url}</span>
                      <ExternalLink className="w-3 h-3 shrink-0" />
                    </a>
                  </div>

                  {/* Status Badge */}
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold font-mono tracking-wider shrink-0 ${
                    site.status === 'ONLINE'
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                      : site.status === 'DOWN'
                      ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                      : site.status === 'DEGRADED'
                      ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                      : 'bg-slate-500/10 text-slate-400 border border-slate-500/30'
                  }`}>
                    {site.status}
                  </span>
                </div>

                {/* Metrics Grid */}
                <div className="grid grid-cols-3 gap-2 mt-4 pt-4 border-t border-[#1A2740]/60">
                  <div className="bg-[#070C14]/60 p-2 rounded-lg border border-[#1A2740]">
                    <span className="text-[10px] text-slate-500 block">Response Time</span>
                    <span className="text-xs font-mono font-bold text-slate-200">
                      {site.last_response_time_ms ? `${site.last_response_time_ms.toFixed(0)} ms` : '--'}
                    </span>
                  </div>

                  <div className="bg-[#070C14]/60 p-2 rounded-lg border border-[#1A2740]">
                    <span className="text-[10px] text-slate-500 block">24h Uptime</span>
                    <span className="text-xs font-mono font-bold text-emerald-400">
                      {site.uptime_percentage_24h !== null ? `${site.uptime_percentage_24h.toFixed(1)}%` : '100%'}
                    </span>
                  </div>

                  <div className="bg-[#070C14]/60 p-2 rounded-lg border border-[#1A2740]">
                    <span className="text-[10px] text-slate-500 block">HTTP Code</span>
                    <span className="text-xs font-mono font-bold text-cyan-400">
                      {site.last_status_code || '--'}
                    </span>
                  </div>
                </div>

                {/* SSL Certificate Badge */}
                {site.check_ssl && (
                  <div className="mt-3 flex items-center justify-between text-xs p-2 rounded-lg bg-[#070C14]/40 border border-[#1A2740]">
                    <div className="flex items-center gap-1.5 text-slate-300">
                      <Lock className="w-3.5 h-3.5 text-cyan-400" />
                      <span className="text-[11px] truncate max-w-[140px]" title={site.ssl_issuer || 'SSL Enabled'}>
                        {site.ssl_issuer || 'TLS Certificate'}
                      </span>
                    </div>
                    {site.ssl_days_remaining !== null ? (
                      <span className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
                        site.ssl_days_remaining <= 14
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                          : site.ssl_days_remaining <= 30
                          ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                          : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      }`}>
                        {site.ssl_days_remaining}d left
                      </span>
                    ) : (
                      <span className="text-[10px] text-slate-500">Checking...</span>
                    )}
                  </div>
                )}
              </div>

              {/* Card Footer Actions */}
              <div className="mt-4 pt-3 border-t border-[#1A2740] flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <button
                    onClick={(e) => handleManualCheck(e, site.id)}
                    disabled={checkingId === site.id}
                    title="Run On-Demand Synthetic Check"
                    className="p-1.5 rounded-lg bg-[#070C14] hover:bg-cyan-500/20 text-slate-400 hover:text-cyan-300 border border-[#1A2740] transition text-[11px] flex items-center gap-1 cursor-pointer"
                  >
                    {checkingId === site.id ? (
                      <RefreshCw className="w-3 h-3 text-cyan-400 animate-spin" />
                    ) : (
                      <Zap className="w-3 h-3 text-cyan-400" />
                    )}
                    <span>{checkingId === site.id ? 'Checking...' : 'Check'}</span>
                  </button>

                  {!site.is_verified && (
                    <button
                      onClick={() => { setVerifySite(site); setVerifyResult(null); }}
                      className="text-[10px] text-amber-400 hover:underline flex items-center gap-1"
                    >
                      <ShieldAlert className="w-3 h-3" />
                      <span>Verify Domain</span>
                    </button>
                  )}
                  {site.is_verified && (
                    <span className="text-[10px] text-cyan-400/80 flex items-center gap-1 font-mono">
                      <ShieldCheck className="w-3 h-3 text-cyan-400" />
                      <span>Verified</span>
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setSiteToDelete(site)}
                    title="Remove Monitored Target"
                    className="p-1.5 rounded-lg bg-[#070C14] hover:bg-rose-500/20 text-slate-500 hover:text-rose-400 border border-[#1A2740] transition text-[11px] cursor-pointer"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>

                  <Link
                    to={`/websites/${site.id}`}
                    className="inline-flex items-center gap-1 text-xs font-semibold text-cyan-400 hover:text-cyan-300 transition"
                  >
                    <span>Details</span>
                    <ArrowUpRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ADD WEBSITE MODAL */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4 backdrop-blur-xs">
          <div className="w-full max-w-lg glass-panel p-6 rounded-2xl border border-[#1A2740] shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-[#1A2740] pb-3">
              <div className="flex items-center gap-2">
                <Globe className="w-5 h-5 text-cyan-400" />
                <h3 className="text-sm font-bold text-slate-100">Add Monitored Website / Public URL</h3>
              </div>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-white text-xs font-mono"
              >
                ✕
              </button>
            </div>

            {addError && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{addError}</span>
              </div>
            )}

            <form onSubmit={handleCreateWebsite} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Target Public URL <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  required
                  autoComplete="url"
                  value={addForm.url}
                  onChange={(e) => setAddForm({ ...addForm, url: e.target.value })}
                  placeholder="https://example.com, example.com, or a public IP"
                  className="w-full px-3.5 py-2 rounded-xl bg-[#0B1322] border border-[#1A2740] text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:border-cyan-400"
                />
                <span className="text-[10px] text-slate-500 mt-1 block">
                  Enter a public domain or public IP. HTTPS is added automatically when omitted; localhost and private IP ranges stay blocked.
                </span>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Friendly Target Name <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={addForm.name}
                  onChange={(e) => setAddForm({ ...addForm, name: e.target.value })}
                  placeholder="Acme Production Website"
                  className="w-full px-3.5 py-2 rounded-xl bg-[#0B1322] border border-[#1A2740] text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:border-cyan-400"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Check Interval
                  </label>
                  <select
                    value={addForm.monitoring_interval_seconds}
                    onChange={(e) => setAddForm({ ...addForm, monitoring_interval_seconds: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 rounded-xl bg-[#0B1322] border border-[#1A2740] text-xs text-slate-100 focus:outline-none focus:border-cyan-400"
                  >
                    <option value={30}>Every 30 seconds</option>
                    <option value={60}>Every 1 minute</option>
                    <option value={300}>Every 5 minutes</option>
                    <option value={600}>Every 10 minutes</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Check Timeout (s)
                  </label>
                  <input
                    type="number"
                    min={2}
                    max={30}
                    value={addForm.check_timeout_seconds}
                    onChange={(e) => setAddForm({ ...addForm, check_timeout_seconds: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 rounded-xl bg-[#0B1322] border border-[#1A2740] text-xs text-slate-100 focus:outline-none focus:border-cyan-400"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Expected HTTP Codes
                  </label>
                  <input
                    type="text"
                    value={addForm.expected_status_codes}
                    onChange={(e) => setAddForm({ ...addForm, expected_status_codes: e.target.value })}
                    placeholder="200,201,301,302"
                    className="w-full px-3 py-2 rounded-xl bg-[#0B1322] border border-[#1A2740] text-xs text-slate-100 focus:outline-none focus:border-cyan-400"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    SSL Expiry Warning (Days)
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={90}
                    value={addForm.ssl_expiry_warning_days}
                    onChange={(e) => setAddForm({ ...addForm, ssl_expiry_warning_days: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 rounded-xl bg-[#0B1322] border border-[#1A2740] text-xs text-slate-100 focus:outline-none focus:border-cyan-400"
                  />
                </div>
              </div>

              <div className="flex items-center gap-4 pt-1">
                <label className="flex items-center gap-2 text-xs text-slate-300">
                  <input
                    type="checkbox"
                    checked={addForm.check_ssl}
                    onChange={(e) => setAddForm({ ...addForm, check_ssl: e.target.checked })}
                    className="rounded bg-[#0B1322] border-[#1A2740] text-cyan-400"
                  />
                  <span>Inspect SSL/TLS Cert</span>
                </label>

                <label className="flex items-center gap-2 text-xs text-slate-300">
                  <input
                    type="checkbox"
                    checked={addForm.follow_redirects}
                    onChange={(e) => setAddForm({ ...addForm, follow_redirects: e.target.checked })}
                    className="rounded bg-[#0B1322] border-[#1A2740] text-cyan-400"
                  />
                  <span>Follow Redirects</span>
                </label>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#1A2740]">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowAddModal(false)}
                  className="text-xs"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  disabled={addLoading}
                  className="text-xs"
                >
                  {addLoading ? 'Validating & Adding...' : 'Start Monitoring Target'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* OWNERSHIP VERIFICATION MODAL */}
      {verifySite && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4 backdrop-blur-xs">
          <div className="w-full max-w-lg glass-panel p-6 rounded-2xl border border-[#1A2740] shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-[#1A2740] pb-3">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-cyan-400" />
                <h3 className="text-sm font-bold text-slate-100">Domain Ownership Verification</h3>
              </div>
              <button
                onClick={() => setVerifySite(null)}
                className="text-slate-400 hover:text-white text-xs font-mono"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-300">
              Verify ownership of <span className="font-bold text-cyan-400">{verifySite.url}</span> to unlock advanced synthetic tests and status badges.
            </p>

            {verifyResult && (
              <div className={`p-3 rounded-xl text-xs flex items-center gap-2 ${
                verifyResult.verified 
                  ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-300' 
                  : 'bg-rose-500/10 border border-rose-500/30 text-rose-300'
              }`}>
                {verifyResult.verified ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <AlertTriangle className="w-4 h-4 shrink-0" />}
                <span>{verifyResult.message}</span>
              </div>
            )}

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Verification Method
                </label>
                <select
                  value={verifyMethod}
                  onChange={(e) => setVerifyMethod(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-[#0B1322] border border-[#1A2740] text-xs text-slate-100 focus:outline-none focus:border-cyan-400"
                >
                  <option value="dns_txt">DNS TXT Record</option>
                  <option value="http_file">HTTP Well-Known File</option>
                  <option value="meta_tag">HTML Verification Meta Tag</option>
                </select>
              </div>

              {verifyMethod === 'dns_txt' && (
                <div className="p-3 rounded-xl bg-[#070C14] border border-[#1A2740] space-y-1">
                  <span className="text-[10px] text-slate-500 font-mono">Create TXT record at apex:</span>
                  <p className="text-xs font-mono text-cyan-300 select-all break-all">
                    cynera-site-verification={verifySite.verification_token}
                  </p>
                </div>
              )}

              {verifyMethod === 'meta_tag' && (
                <div className="p-3 rounded-xl bg-[#070C14] border border-[#1A2740] space-y-1">
                  <span className="text-[10px] text-slate-500 font-mono">Add this tag inside the website's HTML head:</span>
                  <p className="text-xs font-mono text-cyan-300 select-all break-all">&lt;meta name=\"cynera-verification\" content=\"{verifySite.verification_token}\" /&gt;</p>
                </div>
              )}

              {verifyMethod === 'http_file' && (
                <div className="p-3 rounded-xl bg-[#070C14] border border-[#1A2740] space-y-1">
                  <span className="text-[10px] text-slate-500 font-mono">Host public file at:</span>
                  <p className="text-xs font-mono text-cyan-300 break-all">
                    {verifySite.url}/.well-known/cynera-verify.txt
                  </p>
                  <span className="text-[10px] text-slate-500 font-mono block mt-2">File content:</span>
                  <p className="text-xs font-mono text-cyan-300 select-all">
                    {verifySite.verification_token}
                  </p>
                </div>
              )}
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#1A2740]">
              <Button
                variant="outline"
                onClick={() => setVerifySite(null)}
                className="text-xs"
              >
                Close
              </Button>
              <Button
                variant="primary"
                onClick={handleVerifyOwnership}
                disabled={verifyLoading}
                className="text-xs"
              >
                {verifyLoading ? 'Verifying...' : 'Validate Verification'}
              </Button>
            </div>
          </div>
        </div>
      )}
      {/* DELETE CONFIRMATION MODAL */}
      {siteToDelete && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4 backdrop-blur-xs">
          <div className="w-full max-w-md glass-panel p-6 rounded-2xl border border-rose-500/30 shadow-2xl space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-rose-500/20 border border-rose-500/30 flex items-center justify-center text-rose-400 shrink-0">
                <Trash2 className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-100">Remove Monitored Website</h3>
                <p className="text-xs text-slate-400">This will stop all synthetic checks and delete historical metrics.</p>
              </div>
            </div>

            <p className="text-xs text-slate-300 bg-[#070C14] p-3 rounded-lg border border-[#1A2740]">
              Are you sure you want to remove <strong className="text-slate-100">{siteToDelete.name}</strong> (<span className="text-cyan-400 font-mono">{siteToDelete.url}</span>)?
            </p>

            <div className="flex items-center justify-end gap-3 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSiteToDelete(null)}
                disabled={deletingId === siteToDelete.id}
              >
                Cancel
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={() => handleDeleteWebsite(siteToDelete.id, siteToDelete.name)}
                disabled={deletingId === siteToDelete.id}
              >
                {deletingId === siteToDelete.id ? 'Removing...' : 'Confirm Remove'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WebsiteMonitoringView;

