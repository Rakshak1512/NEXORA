import React, { useState, useEffect } from 'react';
import { CheckSquare, ShieldCheck, Play, XCircle, RefreshCw, Terminal } from 'lucide-react';
import api from '../services/api';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import Button from '../components/common/Button';

/**
 * MANDATORY APPROVAL CENTER & AUTONOMOUS OPERATIONS SIMULATION
 * Workflow:
 * 1. Detect incident
 * 2. Generate recommended action
 * 3. Check applicable policy
 * 4. Request operator approval
 * 5. Approve or reject
 * 6. Simulate execution
 * 7. Generate audit record & display rollback plan
 */
const ApprovalCenterView = () => {
  const [approvals, setApprovals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actingId, setActingId] = useState(null);

  const fetchApprovals = async () => {
    try {
      const res = await api.get('/approvals');
      setApprovals(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApprovals();
    const interval = setInterval(fetchApprovals, 8000);
    return () => clearInterval(interval);
  }, []);

  const handleAction = async (id, action) => {
    setActingId(id);
    try {
      await api.post(`/approvals/${id}/action`, {
        action,
        operator_comments: `Action ${action} confirmed by Operator Console.`
      });
      fetchApprovals();
    } catch (e) {
      console.error(e);
    } finally {
      setActingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            Remediation Approval Center
            <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-teal-500/20 text-teal-300 border border-teal-500/30">
              SAFE AUTONOMOUS OPERATIONS
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Policy-guarded human-in-the-loop approvals. Never runs unverified commands on production systems.
          </p>
        </div>
        <Button variant="secondary" size="sm" onClick={fetchApprovals} icon={RefreshCw}>
          Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-6">
        {approvals.map(app => (
          <Card 
            key={app.id}
            title={`Incident ${app.incident_number} — Target: ${app.target_component}`}
            badge={
              <Badge variant={app.status === 'APPROVED' ? 'success' : app.status === 'REJECTED' ? 'danger' : 'warning'}>
                {app.status}
              </Badge>
            }
          >
            <div className="space-y-4 text-xs text-slate-300">
              <div>
                <span className="font-semibold text-slate-400 block mb-1">Recommended Remediation Action:</span>
                <p className="text-slate-100 font-medium text-sm">{app.action_description}</p>
              </div>

              <div className="p-3.5 rounded-xl bg-[#070C14] border border-[#1A2740] flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <span className="text-slate-400 font-semibold">Policy Gate Evaluation:</span>
                  <div className="font-mono text-emerald-400 text-xs mt-0.5">{app.policy_evaluation_result}</div>
                </div>
                <div className="text-right text-slate-400 font-mono text-[11px]">
                  Requested: {app.requested_at ? new Date(app.requested_at).toLocaleTimeString() : 'N/A'}
                </div>
              </div>

              {/* Execution Log if executed */}
              {app.simulated_execution_log && (
                <div className="p-3.5 rounded-xl bg-[#070C14] border border-cyan-500/30">
                  <div className="flex items-center gap-2 text-cyan-400 font-semibold mb-2">
                    <Terminal className="w-4 h-4" />
                    <span>Safe Execution Simulation & Audit Output:</span>
                  </div>
                  <pre className="font-mono text-[11px] text-slate-300 whitespace-pre-wrap leading-relaxed">
                    {app.simulated_execution_log}
                  </pre>
                </div>
              )}

              {/* Rollback Information */}
              <div className="p-3.5 rounded-xl bg-slate-900/60 border border-[#1A2740]">
                <span className="text-slate-400 font-semibold block mb-0.5">Automated Rollback Guarantee:</span>
                <p className="text-slate-300 text-[11px]">{app.rollback_information}</p>
              </div>

              {/* Action Buttons */}
              {app.status === 'PENDING' && (
                <div className="flex items-center justify-end gap-3 pt-2">
                  <Button
                    variant="danger"
                    size="sm"
                    icon={XCircle}
                    disabled={actingId === app.id}
                    onClick={() => handleAction(app.id, 'REJECT')}
                  >
                    Reject Action
                  </Button>
                  <Button
                    variant="success"
                    size="sm"
                    icon={Play}
                    disabled={actingId === app.id}
                    onClick={() => handleAction(app.id, 'APPROVE')}
                  >
                    {actingId === app.id ? 'Simulating...' : 'Approve & Execute Remediation'}
                  </Button>
                </div>
              )}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default ApprovalCenterView;

