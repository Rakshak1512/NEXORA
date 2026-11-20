import React from 'react';
import { Globe, Server, ShieldCheck, MapPin } from 'lucide-react';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';

const GlobalOperationsView = () => {
  const regions = [
    { name: 'North America (US-East)', endpoint: 'https://us-east.cynera.io', latency: '14.2 ms', status: 'ACTIVE', nodes: 3, residency: 'US Data Perimeter' },
    { name: 'Europe West (Frankfurt)', endpoint: 'https://eu-central.cynera.io', latency: '38.5 ms', status: 'ACTIVE', nodes: 1, residency: 'GDPR Perimeter' },
    { name: 'Asia Pacific (Tokyo)', endpoint: 'https://ap-northeast.cynera.io', latency: '72.1 ms', status: 'ACTIVE', nodes: 0, residency: 'AP Data Perimeter' }
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
          Global Operations & Multi-Region Topology
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Multi-tenant data residency enforcement, regional routing endpoints, and UTC event ordering.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {regions.map((r, i) => (
          <Card key={i} title={r.name} icon={MapPin} badge={<Badge variant="success">{r.status}</Badge>}>
            <div className="space-y-3 text-xs text-slate-300">
              <div className="p-3 rounded-lg bg-[#070C14] border border-[#1A2740] font-mono">
                <span className="text-slate-500 block text-[10px]">Regional Ingestion Endpoint:</span>
                <span className="text-cyan-400 truncate block mt-0.5">{r.endpoint}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400">Transit Latency:</span>
                <span className="text-teal-300 font-bold font-mono">{r.latency}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400">Active Node Clusters:</span>
                <span className="text-slate-100 font-semibold">{r.nodes} Nodes</span>
              </div>
              <div className="pt-2 border-t border-[#1A2740] text-[11px] text-emerald-400 font-medium">
                ✓ {r.residency} (Local Residency Strict)
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default GlobalOperationsView;

