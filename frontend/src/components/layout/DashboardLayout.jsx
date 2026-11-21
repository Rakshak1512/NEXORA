import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { FlaskConical, CheckCircle2 } from 'lucide-react';
import Sidebar from './Sidebar';
import Navbar from './Navbar';
import { useAuth } from '../../context/AuthContext';

const fieldLabel = (el) => {
  const linked = el.id ? document.querySelector(`label[for="${el.id}"]`) : null;
  return [linked?.textContent, el.getAttribute('aria-label'), el.name, el.id, el.placeholder]
    .filter(Boolean).join(' ').toLowerCase();
};

const sampleFor = (el) => {
  const key = fieldLabel(el);
  if (/password|secret|token|api.?key|credential|private.?key|authorization/.test(key)) return null;
  if (/email/.test(key)) return 'demo.operator@example.invalid';
  if (/url|website|endpoint|callback/.test(key)) return 'https://example.com';
  if (/ip address|ip_address|host ip/.test(key)) return '192.0.2.10';
  if (/hostname|host name|host/.test(key)) return 'demo-host-01.example.invalid';
  if (/port/.test(key)) return '443';
  if (/database.?name/.test(key)) return 'cynera_demo';
  if (/username|user name/.test(key)) return 'demo_readonly';
  if (/organization|company|workspace/.test(key)) return 'Northstar Demo Organization';
  if (/full.?name|contact.?name|owner.?name/.test(key)) return 'Alex Morgan';
  if (/phone/.test(key)) return '+1 202 555 0142';
  if (/description|notes|message|reason|summary/.test(key)) return 'Synthetic demo configuration for validating the CYNERA workflow. No production system or credentials are connected.';
  if (/threshold|cpu|memory|utilization/.test(key)) return '85';
  if (/interval|timeout|duration|seconds/.test(key)) return '60';
  if (/name|title|service|device|collector|integration|rule/.test(key)) return 'Demo Infrastructure Node';
  if (el.type === 'number') return '10';
  if (el.type === 'date') return '2026-11-21';
  if (el.type === 'datetime-local') return '2026-11-21T10:00';
  if (el.type === 'url') return 'https://example.com';
  if (el.type === 'email') return 'demo.operator@example.invalid';
  if (el.type === 'tel') return '+1 202 555 0142';
  if (el.tagName === 'TEXTAREA') return 'Synthetic demo details. No production credentials or external integrations are configured.';
  return 'Demo value';
};

const DemoFormFill = () => {
  const [message, setMessage] = useState('');
  const fillVisibleForm = () => {
    const candidates = [...document.querySelectorAll('input, textarea, select')].filter((el) =>
      !el.disabled && el.type !== 'hidden' && el.type !== 'password' &&
      el.getClientRects().length && !el.readOnly &&
      !/search|filter/i.test(fieldLabel(el))
    );
    let filled = 0;
    candidates.forEach((el) => {
      if (el.type === 'checkbox' || el.type === 'radio' || el.type === 'file') return;
      let value;
      if (el.tagName === 'SELECT') {
        const option = [...el.options].find((item) => item.value && !item.disabled && !/select|choose|none/i.test(item.text));
        if (!option) return;
        value = option.value;
      } else {
        value = sampleFor(el);
        if (value === null) return;
        if (el.type === 'number') {
          const min = el.min !== '' ? Number(el.min) : 1;
          const max = el.max !== '' ? Number(el.max) : 100;
          value = String(Math.min(max, Math.max(min, Number(value) || min)));
        }
        if (el.maxLength > 0) value = value.slice(0, el.maxLength);
      }
      const proto = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype :
        el.tagName === 'SELECT' ? HTMLSelectElement.prototype : HTMLInputElement.prototype;
      const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
      setter ? setter.call(el, value) : (el.value = value);
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
      filled += 1;
    });
    setMessage(filled ? `Filled ${filled} visible field${filled === 1 ? '' : 's'} with synthetic examples. Review before saving.` : 'Open an Add or Edit form first. Passwords, API keys and secrets are never autofilled.');
    window.setTimeout(() => setMessage(''), 5000);
  };

  return (
    <div className="fixed bottom-5 right-5 z-[80] flex flex-col items-end gap-2">
      {message && <div role="status" className="max-w-xs rounded-lg border border-cyan-500/30 bg-[#0D1524] px-3 py-2 text-[11px] text-slate-200 shadow-xl">{message}</div>}
      <button type="button" onClick={fillVisibleForm} className="inline-flex items-center gap-2 rounded-full border border-cyan-400/40 bg-[#0D1524]/95 px-4 py-3 text-xs font-semibold text-cyan-200 shadow-xl shadow-cyan-950/40 backdrop-blur hover:border-cyan-300 hover:bg-cyan-950/80 transition">
        <FlaskConical className="h-4 w-4" /> Fill demo fields
      </button>
    </div>
  );
};

const DashboardLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-[#070C14] text-slate-100 flex">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 lg:pl-64 flex flex-col min-w-0">
        <Navbar onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 p-4 md:p-6 lg:p-8 max-w-7xl w-full mx-auto space-y-6">
          {user?.is_demo && (
            <div role="status" className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 flex flex-wrap items-center justify-between gap-2">
              <div><p className="text-xs font-bold uppercase tracking-wider text-amber-300">DEMO WORKSPACE — SYNTHETIC DATA</p><p className="text-[11px] text-amber-100/80 mt-1">Sample warnings, failures and recovery events are for demonstration only. No real customer systems are being monitored.</p></div>
              <span className="text-[10px] rounded-md border border-amber-400/30 px-2 py-1 text-amber-200">DEMO MODE</span>
            </div>
          )}
          <Outlet />
        </main>
      </div>
      {user?.is_demo && <DemoFormFill />}
    </div>
  );
};

export default DashboardLayout;
