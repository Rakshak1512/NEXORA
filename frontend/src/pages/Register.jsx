import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ShieldCheck, Lock, Mail, User, Building2, Globe, Briefcase, Users, AlertCircle, ArrowRight, CheckCircle2 } from 'lucide-react';
import api from '../services/api';
import Button from '../components/common/Button';

const Register = () => {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [websiteUrl, setWebsiteUrl] = useState('');
  const [orgName, setOrgName] = useState('');
  const [industry, setIndustry] = useState('Technology');
  const [orgSize, setOrgSize] = useState('10-50');
  const [jobTitle, setJobTitle] = useState('Lead Systems Architect');
  const [country, setCountry] = useState('United States');
  const [agreeTerms, setAgreeTerms] = useState(false);
  const [accountType, setAccountType] = useState('owner');

  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  // Password strength check
  const getPasswordStrength = () => {
    if (!password) return 0;
    let score = 0;
    if (password.length >= 8) score += 1;
    if (/[A-Z]/.test(password)) score += 1;
    if (/[0-9]/.test(password)) score += 1;
    if (/[^A-Za-z0-9]/.test(password)) score += 1;
    return score;
  };

  const strength = getPasswordStrength();
  const strengthLabels = ['Weak', 'Fair', 'Good', 'Strong'];
  const strengthColors = ['bg-rose-500', 'bg-amber-500', 'bg-teal-500', 'bg-emerald-500'];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (accountType === 'admin') {
      setError('Platform administrator accounts are invitation-only. Ask an existing Super Administrator to create your account.');
      return;
    }
    if (password.length < 12) {
      setError('Password must be at least 12 characters long.');
      return;
    }
    if (confirmPassword && password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    if (!agreeTerms) {
      setError('Please agree to the CYNERA Terms of Service & Privacy Protocol.');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        full_name: fullName,
        email,
        password,
        confirm_password: confirmPassword || password,
        organization_name: orgName,
        website_url: websiteUrl || undefined,
        industry,
        org_size: orgSize,
        country,
        job_title: jobTitle
      };

      const res = await api.post('/auth/register-org', payload);
      if (res.data.status === 'otp_sent') {
        navigate(`/verify-otp?email=${encodeURIComponent(email)}&purpose=signup&org=${encodeURIComponent(orgName)}`);
      } else {
        navigate('/login');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#070C14] flex items-center justify-center p-4 py-12 relative overflow-hidden">
      {/* Background Glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-cyan-500/10 blur-[150px] rounded-full pointer-events-none" />

      <div className="w-full max-w-2xl glass-panel p-8 md:p-10 rounded-2xl border border-[#1A2740] shadow-2xl relative z-10">
        {/* Header */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2.5 mb-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-teal-400 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <ShieldCheck className="w-6 h-6 text-slate-950 font-bold" />
            </div>
            <span className="font-extrabold text-2xl tracking-wider text-slate-100">CYNERA</span>
          </Link>
          <h2 className="text-xl md:text-2xl font-bold text-slate-100">Create Enterprise Workspace</h2>
          <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
            Self-service onboarding with 6-digit email verification and autonomous zero-trust observability.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-2 mb-5">
          <button type="button" onClick={() => { setAccountType('owner'); setError(''); }} className={"rounded-xl border px-3 py-3 text-xs font-semibold " + (accountType === 'owner' ? 'border-cyan-400 bg-cyan-500/10 text-cyan-300' : 'border-[#1A2740] text-slate-400')}>Workspace Owner</button>
          <button type="button" onClick={() => { setAccountType('admin'); setError(''); }} className={"rounded-xl border px-3 py-3 text-xs font-semibold " + (accountType === 'admin' ? 'border-cyan-400 bg-cyan-500/10 text-cyan-300' : 'border-[#1A2740] text-slate-400')}>Platform Admin</button>
        </div>
        {accountType === 'admin' && <div className="mb-5 rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-xs text-amber-200">Platform administrator registration is invitation-only. For security, you cannot grant yourself administrator privileges. Ask an existing Super Administrator to create your account, then sign in using Platform Admin.</div>}
        {error && (
          <div className="mb-6 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center gap-2.5 text-rose-400 text-xs">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* SECTION 1: Personal Profile */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 border-b border-[#1A2740] pb-2">
              <User className="w-4 h-4 text-cyan-400" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                1. Administrator Profile
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Full Name <span className="text-rose-400">*</span>
                </label>
                <div className="relative">
                  <User className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Alex Vance"
                    className="w-full pl-10 pr-4 py-2 rounded-xl bg-[#0B1322] border border-[#1A2740] text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Corporate Work Email <span className="text-rose-400">*</span>
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="alex@acmecorp.com"
                    className="w-full pl-10 pr-4 py-2 rounded-xl bg-[#0B1322] border border-[#1A2740] text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition"
                  />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Job Title
                </label>
                <div className="relative">
                  <Briefcase className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    value={jobTitle}
                    onChange={(e) => setJobTitle(e.target.value)}
                    placeholder="VP of Infrastructure & Security"
                    className="w-full pl-10 pr-4 py-2 rounded-xl bg-[#0B1322] border border-[#1A2740] text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition"
                  />
                </div>
              </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Password <span className="text-rose-400">*</span>
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Min. 12 characters"
                    className="w-full pl-10 pr-4 py-2 rounded-xl bg-[#0B1322] border border-[#1A2740] text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition"
                  />
                </div>
                {password && (
                  <div className="mt-1.5 flex items-center gap-2">
                    <div className="flex-1 h-1 bg-[#1A2740] rounded-full overflow-hidden flex gap-1">
                      {[1, 2, 3, 4].map((step) => (
                        <div
                          key={step}
                          className={`h-full flex-1 transition-all ${
                            step <= strength ? strengthColors[strength - 1] : 'bg-transparent'
                          }`}
                        />
                      ))}
                    </div>
                    <span className="text-[10px] text-slate-400 font-medium">
                      {strengthLabels[strength - 1] || 'Weak'}
                    </span>
                  </div>
                )}
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Confirm Password <span className="text-rose-400">*</span>
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="password"
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Re-enter password"
                    className="w-full pl-10 pr-4 py-2 rounded-xl bg-[#0B1322] border border-[#1A2740] text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition"
                  />
                </div>
                {confirmPassword && password !== confirmPassword && (
                  <span className="text-[10px] text-rose-400 font-medium mt-1 inline-block">
                    Passwords do not match
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* SECTION 2: Organization Details */}
          <div className="space-y-4 pt-2">
            <div className="flex items-center gap-2 border-b border-[#1A2740] pb-2">
              <Building2 className="w-4 h-4 text-cyan-400" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                2. Organization & Infrastructure Details
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Company / Organization Name <span className="text-rose-400">*</span>
                </label>
                <div className="relative">
                  <Building2 className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    required
                    value={orgName}
                    onChange={(e) => setOrgName(e.target.value)}
                    placeholder="Acme Financial Services"
                    className="w-full pl-10 pr-4 py-2 rounded-xl bg-[#0B1322] border border-[#1A2740] text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Primary Website URL (Optional for Auto-Monitor)
                </label>
                <div className="relative">
                  <Globe className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="url"
                    value={websiteUrl}
                    onChange={(e) => setWebsiteUrl(e.target.value)}
                    placeholder="https://example.com"
                    className="w-full pl-10 pr-4 py-2 rounded-xl bg-[#0B1322] border border-[#1A2740] text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition"
                  />
                </div>
              </div>
            </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Industry Vertical
                </label>
                <select
                  value={industry}
                  onChange={(e) => setIndustry(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl bg-[#0B1322] border border-[#1A2740] text-xs text-slate-100 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition"
                >
                  <option value="Technology">Technology & Cloud SaaS</option>
                  <option value="FinTech">Financial Services & Banking</option>
                  <option value="Healthcare">Healthcare & Life Sciences</option>
                  <option value="E-Commerce">E-Commerce & Retail</option>
                  <option value="Government">Government & Defense</option>
                  <option value="Telecom">Telecommunications</option>
                  <option value="Manufacturing">Manufacturing & IoT</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Company Size
                </label>
                <div className="relative">
                  <Users className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <select
                    value={orgSize}
                    onChange={(e) => setOrgSize(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 rounded-xl bg-[#0B1322] border border-[#1A2740] text-xs text-slate-100 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition"
                  >
                    <option value="1-10">1 - 10 employees (Startup)</option>
                    <option value="10-50">10 - 50 employees (Growing)</option>
                    <option value="50-200">50 - 200 employees (Mid-Market)</option>
                    <option value="200-1000">200 - 1,000 employees (Enterprise)</option>
                    <option value="1000+">1,000+ employees (Global Enterprise)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Primary Country / Region
                </label>
                <div className="relative">
                  <Globe className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    value={country}
                    onChange={(e) => setCountry(e.target.value)}
                    placeholder="United States, Germany, India, etc."
                    className="w-full pl-10 pr-4 py-2 rounded-xl bg-[#0B1322] border border-[#1A2740] text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Privacy Guarantee Box */}
          <div className="p-3.5 rounded-xl bg-cyan-950/20 border border-cyan-500/20 flex items-start gap-3">
            <CheckCircle2 className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
            <div className="text-[11px] text-slate-300 leading-relaxed">
              <span className="font-semibold text-cyan-300">Two-Tier Privacy Architecture:</span> CYNERA runs a local collector inside your network that filters secrets, redacts credentials, and sends only approved metadata to Tier 2. Raw logs never leave your perimeter.
            </div>
          </div>

          {/* Terms checkbox */}
          <div className="flex items-center gap-2.5">
            <input
              type="checkbox"
              id="terms"
              checked={agreeTerms}
              onChange={(e) => setAgreeTerms(e.target.checked)}
              className="w-4 h-4 rounded bg-[#0B1322] border-[#1A2740] text-cyan-400 focus:ring-cyan-400/20"
            />
            <label htmlFor="terms" className="text-xs text-slate-400">
              I agree to the <span className="text-slate-200">CYNERA Enterprise Service Agreement</span> and verify I am authorized to register this organization.
            </label>
          </div>

          {/* Submit Button */}
          <Button
            type="submit"
            variant="primary"
            className="w-full py-3 flex items-center justify-center gap-2 text-sm font-semibold rounded-xl"
            disabled={loading}
          >
            {loading ? (
              'Dispatching Verification Code...'
            ) : (
              <>
                <span>Continue to Email Verification</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </Button>
        </form>

        <div className="mt-6 text-center text-xs text-slate-400">
          Already have an account?{' '}
          <Link to="/login" className="text-cyan-400 font-semibold hover:underline">
            Sign In
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Register;
