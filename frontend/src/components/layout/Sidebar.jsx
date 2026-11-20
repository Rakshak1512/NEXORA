import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, Server, Cpu, Network, Shield, 
  FileCheck2, BrainCircuit, AlertOctagon, Sparkles, 
  CheckSquare, Globe, BarChart3, History, Sliders, 
  Settings, X, ShieldAlert, Building2, Key, FileText,
  Layers, Database, BellRing, Webhook, ShieldCheck, Users
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const navGroups = [
  {
    title: 'Core Observability',
    items: [
      { path: '/dashboard', label: 'Overview', icon: LayoutDashboard },
      { path: '/websites', label: 'Websites & Security', icon: Globe },
      { path: '/alerts', label: 'Alert Center', icon: BellRing }
    ]
  },
  {
    title: 'Infrastructure & APM',
    items: [
      { path: '/applications', label: 'APM & Services', icon: Layers },
      { path: '/databases', label: 'Databases', icon: Database },
      { path: '/infrastructure', label: 'Infrastructure', icon: Cpu },
      { path: '/network', label: 'Network Probes', icon: Network },
      { path: '/collectors', label: 'Edge Collectors', icon: Server }
    ]
  },
  {
    title: 'AI & Zero Trust',
    items: [
      { path: '/aiops', label: 'AIOps Engine', icon: BrainCircuit },
      { path: '/incidents', label: 'Incidents', icon: AlertOctagon },
      { path: '/recommendations', label: 'AI Remediation', icon: Sparkles },
      { path: '/egress-proof', label: 'Zero-Trust Egress', icon: FileCheck2, highlight: true },\n      { path: '/security-center', label: 'Security Center', icon: ShieldCheck }
    ]
  },
  {
    title: 'Audits & Management',
    items: [
      { path: '/reports', label: 'PDF Reports & Audits', icon: FileText },
      { path: '/organization', label: 'Team & Organization', icon: Building2 },
      { path: '/developer', label: 'API Keys & Integration', icon: Key },
      { path: '/webhooks', label: 'Webhooks & HMAC', icon: Webhook },
      { path: '/settings', label: 'Settings', icon: Settings }
    ]
  },
  {
    title: 'Super Admin',
    adminOnly: true,
    items: [
      { path: '/approvals', label: 'Approval Registry', icon: CheckSquare },
      { path: '/global', label: 'Global Operations', icon: Globe },
      { path: '/analytics', label: 'Platform Benchmarks', icon: BarChart3 },
      { path: '/audit-logs', label: 'System Audit Logs', icon: History },
      { path: '/scenarios', label: 'Fault Simulation', icon: Sliders },
      { path: '/admin/users', label: 'User Administration', icon: Users }
    ]
  }
];

const Sidebar = ({ isOpen, onClose }) => {
  const { user } = useAuth();
  const isSuperAdmin = user?.role === 'Super Administrator';
  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div 
          onClick={onClose}
          className="fixed inset-0 bg-black/60 z-40 lg:hidden backdrop-blur-xs" 
        />
      )}

      <aside className={`fixed top-0 bottom-0 left-0 z-50 w-64 glass-panel border-r border-[#1A2740] flex flex-col transition-transform duration-300 lg:translate-x-0 ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      }`}>
        {/* Brand Header */}
        <div className="h-16 px-5 border-b border-[#1A2740] flex items-center justify-between">
          <NavLink to="/dashboard" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-teal-400 flex items-center justify-center p-1.5 shadow-lg shadow-cyan-500/20">
              <ShieldAlert className="w-full h-full text-slate-950 font-bold" />
            </div>
            <div>
              <span className="font-extrabold text-base tracking-wider text-slate-100 flex items-center gap-1">
                CYNERA <span className="text-cyan-400 font-mono text-xs px-1 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/20">AIOPS</span>
              </span>
              <p className="text-[9px] text-slate-400 font-medium truncate max-w-[140px]" title="Cyber Network Evaluation and Risk Analytics">
                Cyber Network Eval & Risk Analytics
              </p>
            </div>
          </NavLink>
          <button 
            onClick={onClose}
            className="lg:hidden p-1.5 rounded-lg text-slate-400 hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation list */}
        <nav className="flex-1 px-3 py-3 space-y-4 overflow-y-auto">
          {navGroups.map((group) => {
            if (group.adminOnly && !isSuperAdmin) return null;
            return (
              <div key={group.title} className="space-y-1">
                <div className="px-3 text-[10px] uppercase font-bold tracking-wider text-slate-500">
                  {group.title}
                </div>
                {group.items.map((item) => {
                  const Icon = item.icon;
                  return (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      onClick={onClose}
                      className={({ isActive }) => `
                        flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition-all duration-150 group
                        ${isActive 
                          ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/30 font-semibold shadow-xs' 
                          : 'text-slate-400 hover:text-slate-200 hover:bg-[#131F36]'
                        }
                        ${item.highlight ? 'border border-cyan-500/20 bg-cyan-950/20' : ''}
                      `}
                    >
                      <Icon className={`w-4 h-4 transition-colors group-hover:text-cyan-400 ${item.highlight ? 'text-cyan-400' : ''}`} />
                      <span className="truncate">{item.label}</span>
                      {item.highlight && (
                        <span className="ml-auto text-[9px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300">
                          Proof
                        </span>
                      )}
                    </NavLink>
                  );
                })}
              </div>
            );
          })}
        </nav>

        {/* Footer info badge */}
        <div className="p-3 border-t border-[#1A2740] bg-[#070C14]/40">
          <div className="rounded-lg p-2.5 bg-[#0D1524] border border-[#1A2740] text-center">
            <p className="text-[11px] font-semibold text-slate-300">Two-Tier Architecture</p>
            <p className="text-[10px] text-slate-500 mt-0.5">Raw Logs Kept Local</p>
            <div className="mt-2 flex items-center justify-center gap-1.5 text-[10px] text-emerald-400 font-mono">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>METADATA ONLY</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;

