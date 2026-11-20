import React from 'react';

const Card = ({
  children,
  title,
  subtitle,
  badge,
  action,
  icon: Icon,
  className = '',
  glow = false
}) => {
  return (
    <div className={`glass-panel rounded-xl p-5 border border-[#1A2740] transition-all duration-200 ${glow ? 'glow-cyan' : ''} ${className}`}>
      {(title || Icon || badge || action) && (
        <div className="flex items-center justify-between pb-3 mb-4 border-b border-[#1A2740]/60">
          <div className="flex items-center gap-2.5">
            {Icon && (
              <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                <Icon className="w-5 h-5" />
              </div>
            )}
            <div>
              {title && <h3 className="font-semibold text-slate-100 text-base">{title}</h3>}
              {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {badge}
            {action}
          </div>
        </div>
      )}
      {children}
    </div>
  );
};

export default Card;

