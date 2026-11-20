import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { ShieldCheck, Mail, AlertCircle, ArrowRight, RotateCw, CheckCircle2 } from 'lucide-react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import Button from '../components/common/Button';

const OtpVerification = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { setSession } = useAuth();

  const queryParams = new URLSearchParams(location.search);
  const email = queryParams.get('email') || '';
  const purpose = queryParams.get('purpose') || 'signup';
  const orgName = queryParams.get('org') || '';

  const [otpDigits, setOtpDigits] = useState(['', '', '', '', '', '']);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [loading, setLoading] = useState(false);
  const [cooldown, setCooldown] = useState(60);
  const [resending, setResending] = useState(false);

  const inputRefs = useRef([]);

  // Cooldown countdown timer
  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setInterval(() => {
      setCooldown((prev) => prev - 1);
    }, 1000);
    return () => clearInterval(timer);
  }, [cooldown]);

  // Focus the first input on initial load
  useEffect(() => {
    if (inputRefs.current[0]) {
      inputRefs.current[0].focus();
    }
  }, []);

  const handleChange = (index, value) => {
    // Only allow single numeric character
    const sanitized = value.replace(/[^0-9]/g, '');
    const newDigits = [...otpDigits];

    if (sanitized.length > 0) {
      newDigits[index] = sanitized[sanitized.length - 1];
      setOtpDigits(newDigits);
      // Move to next input if available
      if (index < 5 && inputRefs.current[index + 1]) {
        inputRefs.current[index + 1].focus();
      }
    } else {
      newDigits[index] = '';
      setOtpDigits(newDigits);
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !otpDigits[index] && index > 0) {
      // Move back to previous input
      if (inputRefs.current[index - 1]) {
        inputRefs.current[index - 1].focus();
      }
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').trim().replace(/[^0-9]/g, '');
    if (!pastedData) return;

    const newDigits = [...otpDigits];
    for (let i = 0; i < 6; i++) {
      if (i < pastedData.length) {
        newDigits[i] = pastedData[i];
      }
    }
    setOtpDigits(newDigits);

    // Focus last filled or 6th input
    const nextIdx = Math.min(pastedData.length, 5);
    if (inputRefs.current[nextIdx]) {
      inputRefs.current[nextIdx].focus();
    }
  };

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    setError('');
    setSuccessMsg('');

    const fullCode = otpDigits.join('');
    if (fullCode.length !== 6) {
      setError('Please enter all 6 digits of your verification code.');
      return;
    }

    setLoading(true);
    try {
      const res = await api.post('/auth/verify-otp', {
        email,
        otp: fullCode,
        purpose
      });

      const data = res.data;
      if (data.status === 'verified') {
        setSuccessMsg('Verification successful! Initializing your workspace...');
        
        if (data.access_token && data.user) {
          setSession(data.access_token, data.user, data.organization);
          setTimeout(() => {
            navigate('/dashboard');
          }, 800);
        } else if (purpose === 'password_reset') {
          setTimeout(() => {
            navigate(`/reset-password?email=${encodeURIComponent(email)}&otp=${fullCode}`);
          }, 800);
        } else {
          setTimeout(() => {
            navigate('/login');
          }, 800);
        }
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Verification failed. Please check the code and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (cooldown > 0 || resending) return;
    setError('');
    setSuccessMsg('');
    setResending(true);

    try {
      const res = await api.post('/auth/resend-otp', {
        email,
        purpose
      });
      setSuccessMsg(res.data.message || 'A refreshed 6-digit code has been dispatched.');
      setCooldown(60);
      setOtpDigits(['', '', '', '', '', '']);
      if (inputRefs.current[0]) inputRefs.current[0].focus();
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not resend verification code. Please wait.');
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#070C14] flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-cyan-500/10 blur-[140px] rounded-full pointer-events-none" />

      <div className="w-full max-w-md glass-panel p-8 md:p-10 rounded-2xl border border-[#1A2740] shadow-2xl relative z-10 text-center">
        {/* Header Icon */}
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-tr from-cyan-500/20 to-teal-400/20 border border-cyan-500/30 text-cyan-400 mb-5 shadow-lg shadow-cyan-500/10">
          <Mail className="w-7 h-7" />
        </div>

        <h2 className="text-xl md:text-2xl font-bold text-slate-100">Verify Corporate Email</h2>
        <p className="text-xs text-slate-400 mt-2 leading-relaxed">
          We sent a 6-digit cryptographic security code to:
          <br />
          <span className="font-mono font-semibold text-cyan-300 text-sm">{email || 'your email'}</span>
        </p>

        {orgName && (
          <div className="mt-3 inline-block px-3 py-1 rounded-full bg-[#0D1524] border border-[#1A2740] text-[11px] text-slate-300 font-medium">
            Workspace: <span className="text-cyan-400 font-semibold">{orgName}</span>
          </div>
        )}

        {error && (
          <div className="mt-5 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center gap-2.5 text-rose-400 text-xs text-left">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {successMsg && (
          <div className="mt-5 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center gap-2.5 text-emerald-400 text-xs text-left">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* 6 Digit Inputs */}
        <form onSubmit={handleSubmit} className="mt-8 space-y-6">
          <div className="flex items-center justify-center gap-2.5 sm:gap-3" onPaste={handlePaste}>
            {otpDigits.map((digit, idx) => (
              <input
                key={idx}
                ref={(el) => (inputRefs.current[idx] = el)}
                type="text"
                inputMode="numeric"
                maxLength={1}
                value={digit}
                onChange={(e) => handleChange(idx, e.target.value)}
                onKeyDown={(e) => handleKeyDown(idx, e)}
                className={`w-11 h-14 sm:w-12 sm:h-16 text-center text-xl sm:text-2xl font-mono font-bold rounded-xl bg-[#090F1C] border transition-all duration-200 outline-none ${
                  digit
                    ? 'border-cyan-400 text-cyan-300 shadow-md shadow-cyan-500/10'
                    : 'border-[#1A2740] text-slate-100 focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400'
                }`}
              />
            ))}
          </div>

          <Button
            type="submit"
            variant="primary"
            className="w-full py-3 flex items-center justify-center gap-2 text-sm font-semibold rounded-xl"
            disabled={loading || otpDigits.join('').length !== 6}
          >
            {loading ? (
              'Verifying Code...'
            ) : (
              <>
                <span>Confirm & Enter Workspace</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </Button>
        </form>

        {/* Resend Cooldown Counter */}
        <div className="mt-6 pt-5 border-t border-[#1A2740] flex items-center justify-between text-xs text-slate-400">
          <span>Didn't receive the code?</span>
          <button
            type="button"
            onClick={handleResend}
            disabled={cooldown > 0 || resending}
            className={`font-semibold flex items-center gap-1.5 transition ${
              cooldown > 0 || resending
                ? 'text-slate-600 cursor-not-allowed'
                : 'text-cyan-400 hover:text-cyan-300 hover:underline cursor-pointer'
            }`}
          >
            <RotateCw className={`w-3.5 h-3.5 ${resending ? 'animate-spin' : ''}`} />
            {cooldown > 0 ? `Resend in ${cooldown}s` : 'Resend Code'}
          </button>
        </div>

        <div className="mt-5 text-center">
          <Link to="/register" className="text-xs text-slate-500 hover:text-slate-300 transition">
            &larr; Return to registration
          </Link>
        </div>
      </div>
    </div>
  );
};

export default OtpVerification;

