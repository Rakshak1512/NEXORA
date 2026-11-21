import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ShieldCheck, Lock, Mail, ArrowRight, ArrowLeft, AlertCircle, Shield, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import Button from '../components/common/Button';
import api from '../services/api';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [accountType, setAccountType] = useState('owner');
  const [require2fa, setRequire2fa] = useState(false);
  const [error, setError] = useState('');
  const [autoFillMsg, setAutoFillMsg] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, logout } = useAuth();
  const navigate = useNavigate();

  const handleFillCredentials = (fillEmail, fillPassword, type) => {
    setEmail(fillEmail);
    setPassword(fillPassword);
    setAccountType(type);
    setRequire2fa(false);
    setError('');
    setAutoFillMsg('Demo credentials filled successfully.');
    setTimeout(() => {
      setAutoFillMsg('');
    }, 4000);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await login(email, password, require2fa);
      if (res && res.requireOtp) {
        navigate(`/verify-otp?email=${encodeURIComponent(email)}&purpose=login`);
      } else {
        navigate('/dashboard');
      }
    } catch (err) {
      const msg = err.response?.data?.detail 
        || (err.request ? 'Cannot connect to backend server. Please verify FastAPI is running at http://127.0.0.1:8000.' : err.message) 
        || 'Authentication failed. Please verify credentials.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#070C14] flex items-center justify-center p-4 relative overflow-hidden auth-scene">
      {/* Background Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-cyan-500/10 blur-[120px] rounded-full pointer-events-none" />

      <div className="glass-panel w-full max-w-md p-8 md:p-10 rounded-2xl border border-[#1A2740] shadow-2xl relative z-10 auth-card">
        <Link to="/" className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-cyan-300 transition mb-5"><ArrowLeft className="w-4 h-4" /> Back to landing page</Link>
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2 mb-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-teal-400 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <ShieldCheck className="w-6 h-6 text-slate-950 font-bold" />
            </div>
            <span className="font-extrabold text-2xl tracking-wider text-slate-100">CYNERA</span>
          </Link>
          <h2 className="text-xl md:text-2xl font-bold text-slate-100">Sign In to Platform</h2>
          <p className="text-xs text-slate-400 mt-1">Autonomous Observability & Risk Analytics Platform</p>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center gap-2 text-rose-400 text-xs">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {autoFillMsg && (
          <div className="mb-4 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center gap-2 text-emerald-400 text-xs animate-in fade-in">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{autoFillMsg}</span>
          </div>
        )}

        <div className="grid grid-cols-2 gap-2 mb-5">
          <button type="button" onClick={() => setAccountType('owner')} className={`rounded-lg border px-3 py-2.5 text-xs font-semibold ${accountType === 'owner' ? 'border-cyan-400 bg-cyan-500/10 text-cyan-300' : 'border-[#1A2740] text-slate-400'}`}>Workspace Account</button>
          <button type="button" onClick={() => setAccountType('admin')} className={`rounded-lg border px-3 py-2.5 text-xs font-semibold ${accountType === 'admin' ? 'border-cyan-400 bg-cyan-500/10 text-cyan-300' : 'border-[#1A2740] text-slate-400'}`}>Platform Admin</button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Work Email
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@cynera.io"
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-[#0B1322] border border-[#1A2740] text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition"
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Password
              </label>
              <Link to="/forgot-password" className="text-xs text-cyan-400 hover:underline">
                Forgot password?
              </Link>
            </div>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-[#0B1322] border border-[#1A2740] text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition"
              />
            </div>
          </div>

          {/* 2FA Option */}
          <div className="pt-1 flex items-center gap-2.5">
            <input
              type="checkbox"
              id="require2fa"
              checked={require2fa}
              onChange={(e) => setRequire2fa(e.target.checked)}
              className="w-4 h-4 rounded bg-[#0B1322] border-[#1A2740] text-cyan-400 focus:ring-cyan-400/20"
            />
            <label htmlFor="require2fa" className="text-xs text-slate-300 flex items-center gap-1.5 cursor-pointer">
              <Shield className="w-3.5 h-3.5 text-cyan-400" />
              Verify with 6-digit Email 2FA OTP
            </label>
          </div>

          <Button
            type="submit"
            variant="primary"
            size="lg"
            className="w-full mt-3 py-3 rounded-xl flex items-center justify-center gap-2 font-semibold"
            disabled={loading}
          >
            {loading ? (
              'Authenticating...'
            ) : (
              <>
                <span>Sign In</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </Button>
        </form>

        <div className="mt-6 rounded-xl border border-cyan-500/20 bg-cyan-950/20 p-4">
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs font-bold uppercase tracking-wider text-cyan-300">Demo Accounts</p>
            <span className="text-[10px] text-amber-300">Click to fill</span>
          </div>
          <p className="text-[11px] text-slate-400 mb-3">Select a demo persona to automatically fill credentials, then click <strong>Sign In</strong>.</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {/* Platform Admin Card */}
            <button
              type="button"
              onClick={() => handleFillCredentials('admin@cynera.io', 'Cynera2026!Secure', 'admin')}
              className={`rounded-lg border p-3 text-left transition ${
                email === 'admin@cynera.io' ? 'border-cyan-400 bg-cyan-900/30 ring-1 ring-cyan-400' : 'border-[#1A2740] bg-[#0B1322] hover:border-cyan-500/60'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-100">Platform Admin</span>
                <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300">Super Admin</span>
              </div>
              <span className="block text-[11px] text-slate-400 mt-1 font-mono">admin@cynera.io</span>
              <span className="block text-[10px] text-slate-500 mt-0.5">Platform-wide administration</span>
              <span className="block text-[10px] text-cyan-400 hover:text-cyan-300 font-medium mt-2">
                Auto-fill credentials &rarr;
              </span>
            </button>

            {/* Workspace Account Card */}
            <button
              type="button"
              onClick={() => handleFillCredentials('owner@cynera.io', 'Cynera2026!Secure', 'owner')}
              className={`rounded-lg border p-3 text-left transition ${
                email === 'owner@cynera.io' ? 'border-cyan-400 bg-cyan-900/30 ring-1 ring-cyan-400' : 'border-[#1A2740] bg-[#0B1322] hover:border-cyan-500/60'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-100">Workspace Account</span>
                <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-teal-500/20 text-teal-300">Org Owner</span>
              </div>
              <span className="block text-[11px] text-slate-400 mt-1 font-mono">owner@cynera.io</span>
              <span className="block text-[10px] text-slate-500 mt-0.5">Workspace & telemetry access</span>
              <span className="block text-[10px] text-cyan-400 hover:text-cyan-300 font-medium mt-2">
                Auto-fill credentials &rarr;
              </span>
            </button>
          </div>
        </div>

        <div className="mt-6 text-center text-xs text-slate-400">
          Need a workspace for your company?{' '}
          <Link to="/register" className="text-cyan-400 font-semibold hover:underline">
            Register Organization
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Login;
