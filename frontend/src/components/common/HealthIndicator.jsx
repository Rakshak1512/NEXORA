import React from 'react';
import { CheckCircle2, AlertTriangle, AlertCircle, ShieldAlert } from 'lucide-react';

/**
 * 4 MANDATORY HEALTH STATES
 * EXCELLENT: Healthy infrastructure operating within expected baselines.
 * GOOD: Minor deviations without significant service impact.
 * FAIR: Elevated latency, resource utilization, packet loss or recurring warnings.
 * POOR: Collector unavailable, severe service degradation or critical security/network event.
 */
const HealthIndicator = ({ state = 'EXCELLENT', reason, showReason = false, size = 'md' }) => {
  const normState = (state || 'EXCELLENT').toUpperCase();

  const configs = {
    EXCELLENT: {
      label: 'EXCELLENT',
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10',
      border: 'border-emerald-500/30',
      dot: 'bg-emerald-400',
      icon: CheckCircle2,
      desc: 'Healthy infrastructure operating strictly within expected baselines.'
    },
    GOOD: {
      label: 'GOOD',
      color: 'text-cyan-400',
      bg: 'bg-cyan-500/10',
      border: 'border-cyan-500/30',
      dot: 'bg-cyan-400',
      icon: CheckCircle2,
      desc: 'Minor nominal deviations without significant service impact.'
    },
    FAIR: {
      label: 'FAIR',
      color: 'text-amber-400',
      bg: 'bg-amber-500/10',
      border: 'border-amber-500/30',
      dot: 'bg-amber-400',
      icon: AlertTriangle,
      desc: 'Elevated latency, resource utilization, or recurring warnings detected.'
    },
    POOR: {
      label: 'POOR',
      color: 'text-rose-400',
      bg: 'bg-rose-500/10',
      border: 'border-rose-500/30',
      dot: 'bg-rose-400',
      icon: ShieldAlert,
      desc: 'Collector unavailable, severe service degradation, or critical incident breach.'
    }
  };

  const cfg = configs[normState] || configs.EXCELLENT;
  const Icon = cfg.icon;

  return (
    <div className="flex flex-col">
      <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border ${cfg.bg} ${cfg.border} ${cfg.color} text-xs font-semibold tracking-wide uppercase`}>
        <span className="relative flex h-2 w-2">
          <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${cfg.dot}`}></span>
          <span className={`relative inline-flex rounded-full h-2 w-2 ${cfg.dot}`}></span>
        </span>
        <Icon className="w-3.5 h-3.5" />
        <span>{cfg.label}</span>
      </div>
      {showReason && (
        <span className="text-xs text-slate-400 mt-1">
          {reason || cfg.desc}
        </span>
      )}
    </div>
  );
};

export default HealthIndicator;

