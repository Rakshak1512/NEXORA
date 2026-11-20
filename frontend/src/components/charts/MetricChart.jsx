import React from 'react';
import { 
  ResponsiveContainer, AreaChart, Area, XAxis, 
  YAxis, Tooltip, CartesianGrid 
} from 'recharts';

const CustomTooltip = ({ active, payload, label, unit }) => {
  if (active && payload && payload.length) {
    return (
      <div className="glass-panel p-2.5 rounded-lg border border-[#1A2740] text-xs shadow-xl">
        <p className="text-slate-400 font-mono">{label}</p>
        <p className="text-cyan-400 font-semibold mt-1">
          {payload[0].name}: {payload[0].value} {unit}
        </p>
      </div>
    );
  }
  return null;
};

const MetricChart = ({ data, dataKey, name, unit = "%", color = "#00E5FF", height = 220 }) => {
  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer>
        <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id={`grad-${dataKey}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.4} />
              <stop offset="95%" stopColor={color} stopOpacity={0.0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1A2740" vertical={false} />
          <XAxis dataKey="timestamp" stroke="#64748B" fontSize={11} tickLine={false} />
          <YAxis stroke="#64748B" fontSize={11} tickLine={false} domain={[0, 'auto']} />
          <Tooltip content={<CustomTooltip unit={unit} />} />
          <Area
            type="monotone"
            dataKey={dataKey}
            name={name}
            stroke={color}
            strokeWidth={2}
            fillOpacity={1}
            fill={`url(#grad-${dataKey})`}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default MetricChart;

