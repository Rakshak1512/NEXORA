import React from 'react';

const Badge = ({ children, variant = 'info', size = 'sm', className = '' }) => {
  const variants = {
    info: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
    success: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
    warning: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
    danger: 'bg-rose-500/15 text-rose-400 border-rose-500/30',
    neutral: 'bg-slate-700/30 text-slate-300 border-slate-600/30',
    purple: 'bg-indigo-500/15 text-indigo-400 border-indigo-500/30'
  };

  const sizes = {
    sm: 'text-xs px-2.5 py-0.5',
    md: 'text-sm px-3 py-1'
  };

  return (
    <span className={`inline-flex items-center font-medium rounded-full border ${variants[variant] || variants.info} ${sizes[size]} ${className}`}>
      {children}
    </span>
  );
};

export default Badge;

