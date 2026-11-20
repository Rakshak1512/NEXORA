import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ShieldCheck, Mail, ArrowRight, AlertCircle } from 'lucide-react';
import api from '../services/api';
import Button from '../components/common/Button';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await api.post('/auth/forgot-password', { email });
      navigate(`/verify-otp?email=${encodeURIComponent(email)}&purpose=password_reset`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not process request. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#070C14] flex items-center justify-center p-4 relative overflow-hidden">
      <div className="glass-panel w-full max-w-md p-8 md:p-10 rounded-2xl border border-[#1A2740] shadow-2xl relative z-10">
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2 mb-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-teal-400 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <ShieldCheck className="w-6 h-6 text-slate-950 font-bold" />
            </div>
            <span className="font-extrabold text-2xl tracking-wider text-slate-100">CYNERA</span>
          </Link>
          <h2 className="text-xl md:text-2xl font-bold text-slate-100">Reset Account Password</h2>
          <p className="text-xs text-slate-400 mt-1">We'll dispatch a 6-digit security code to your email</p>
        </div>

        {error && (
          <div className="mb-6 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center gap-2 text-rose-400 text-xs">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Work Email Address
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

          <Button
            type="submit"
            variant="primary"
            size="lg"
            className="w-full py-3 rounded-xl flex items-center justify-center gap-2 font-semibold"
            disabled={loading}
          >
            {loading ? (
              'Dispatching Code...'
            ) : (
              <>
                <span>Send Security Code</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </Button>

          <div className="text-center mt-4">
            <Link to="/login" className="text-xs text-cyan-400 hover:underline">
              &larr; Back to Sign In
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ForgotPassword;
