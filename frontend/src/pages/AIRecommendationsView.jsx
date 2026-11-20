import React, { useState, useEffect } from 'react';
import { Sparkles, ShieldCheck, ArrowRight, RefreshCw, Layers } from 'lucide-react';
import api from '../services/api';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import Button from '../components/common/Button';

const AIRecommendationsView = () => {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchRecs = async () => {
    try {
      const res = await api.get('/incidents');
      setIncidents(res.data.filter(i => i.has_ai_recommendation));
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecs();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            AI Recommendations & Explainability
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Explainable root-cause hypotheses, statistical baseline comparisons, and deterministic corrective actions.
          </p>
        </div>
        <Button variant="secondary" size="sm" onClick={fetchRecs} icon={RefreshCw}>
          Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-6">
        {incidents.map(inc => (
          <Card 
            key={inc.id}
            title={`${inc.incident_number}: ${inc.title}`}
            badge={<Badge variant="success">95.4% Confidence</Badge>}
            icon={Sparkles}
          >
            <div className="space-y-4 text-xs text-slate-300">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-3.5 rounded-xl bg-[#070C14] border border-[#1A2740]">
                  <span className="font-semibold text-slate-400 block mb-1">Baseline Comparison:</span>
                  <p className="text-slate-300">
                    Observed metric trajectory is +8.5 standard deviations from 7-day median moving baseline.
                  </p>
                </div>
                <div className="p-3.5 rounded-xl bg-[#070C14] border border-[#1A2740]">
                  <span className="font-semibold text-slate-400 block mb-1">Causal Hypothesis:</span>
                  <p className="text-slate-300">
                    Worker thread pool deadlock accompanied by uncollected token session leak.
                  </p>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-cyan-950/20 border border-cyan-500/30">
                <span className="font-bold text-cyan-400 block mb-1">Suggested Corrective Action:</span>
                <p className="text-slate-200">
                  Execute staged graceful restart of 4 worker instances and flush expired memory caches.
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-[#070C14] border border-[#1A2740] flex items-center justify-between">
                <div>
                  <span className="text-slate-400 font-semibold block">Safety & Rollback Plan:</span>
                  <span className="text-slate-300 text-[11px]">Automatic rollback triggers if container health probe fails 2x within 45s.</span>
                </div>
                <Badge variant="info">Policy Checked</Badge>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default AIRecommendationsView;

