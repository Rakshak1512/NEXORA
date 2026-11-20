import React, { useState, useEffect } from 'react';
import { 
  Building2, Users, UserPlus, Shield, Globe, Briefcase, 
  CheckCircle2, AlertCircle, Trash2, Edit3, ShieldAlert, Sparkles, X, Mail
} from 'lucide-react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import Button from '../components/common/Button';

const roleBadgeColors = {
  'Super Administrator': 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  'Organization Owner': 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  'Admin': 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
  'Organization Administrator': 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
  'Security Analyst': 'bg-rose-500/10 text-rose-400 border-rose-500/20',
  'Infrastructure Engineer': 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  'Operator': 'bg-teal-500/10 text-teal-400 border-teal-500/20',
  'Viewer': 'bg-slate-500/10 text-slate-400 border-slate-500/20'
};

const OrganizationManagementView = () => {
  const { user } = useAuth();
  const [org, setOrg] = useState(null);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Invite modal state
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteName, setInviteName] = useState('');
  const [inviteRole, setInviteRole] = useState('Infrastructure Engineer');
  const [inviteTitle, setInviteTitle] = useState('Site Reliability Engineer');
  const [inviteLoading, setInviteLoading] = useState(false);

  // Edit org modal state
  const [showEditOrgModal, setShowEditOrgModal] = useState(false);
  const [editName, setEditName] = useState('');
  const [editIndustry, setEditIndustry] = useState('');
  const [editWebsite, setEditWebsite] = useState('');
  const [editCountry, setEditCountry] = useState('');
  const [editSize, setEditSize] = useState('');
  const [editLoading, setEditLoading] = useState(false);

  const fetchOrgAndMembers = async () => {
    setLoading(true);
    try {
      const [orgRes, memRes] = await Promise.all([
        api.get('/organization/current'),
        api.get('/organization/members')
      ]);
      setOrg(orgRes.data);
      setMembers(memRes.data);
      setEditName(orgRes.data.name || '');
      setEditIndustry(orgRes.data.industry || 'Technology');
      setEditWebsite(orgRes.data.website || '');
      setEditCountry(orgRes.data.country || 'Global');
      setEditSize(orgRes.data.org_size || '10-50');
    } catch (err) {
      console.error(err);
      setError('Could not load organization details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrgAndMembers();
  }, []);

  const handleInviteSubmit = async (e) => {
    e.preventDefault();
    setInviteLoading(true);
    setError('');
    setSuccessMsg('');
    try {
      const res = await api.post('/organization/members/invite', {
        email: inviteEmail,
        full_name: inviteName,
        role: inviteRole,
        job_title: inviteTitle
      });
      setSuccessMsg(`Invitation dispatched to ${inviteEmail}.`);
      setShowInviteModal(false);
      setInviteEmail('');
      setInviteName('');
      fetchOrgAndMembers();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to dispatch invitation.');
    } finally {
      setInviteLoading(false);
    }
  };

  const handleUpdateRole = async (memberId, newRole) => {
    try {
      await api.patch(`/organization/members/${memberId}`, { role: newRole });
      setSuccessMsg(`Role updated to ${newRole}.`);
      fetchOrgAndMembers();
    } catch (err) {
      setError('Failed to update member role.');
    }
  };

  const handleRemoveMember = async (memberId) => {
    if (!window.confirm('Are you sure you want to remove this member from the organization?')) return;
    try {
      await api.delete(`/organization/members/${memberId}`);
      setSuccessMsg('Member removed from organization.');
      fetchOrgAndMembers();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to remove member.');
    }
  };

  const handleSaveOrg = async (e) => {
    e.preventDefault();
    setEditLoading(true);
    try {
      const res = await api.patch('/organization/current', {
        name: editName,
        industry: editIndustry,
        website: editWebsite,
        country: editCountry,
        org_size: editSize
      });
      setOrg(res.data);
      setShowEditOrgModal(false);
      setSuccessMsg('Organization profile updated.');
    } catch (err) {
      setError('Failed to update organization profile.');
    } finally {
      setEditLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 glass-panel rounded-2xl border border-[#1A2740] relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-cyan-500/5 blur-[90px] rounded-full pointer-events-none" />

        <div className="flex items-start gap-4">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-cyan-500/20 to-teal-400/20 border border-cyan-500/30 flex items-center justify-center shrink-0 shadow-lg shadow-cyan-500/10">
            <Building2 className="w-7 h-7 text-cyan-400" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-xl font-bold text-slate-100">{org?.name || 'Enterprise Workspace'}</h1>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-cyan-500/15 border border-cyan-500/30 text-cyan-300">
                {org?.plan || 'ENTERPRISE'}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1 flex items-center gap-3">
              <span>Slug: <strong className="text-slate-300 font-mono">{org?.slug || 'acroglobal'}</strong></span>
              <span>&bull;</span>
              <span>Industry: <strong className="text-slate-300">{org?.industry || 'Technology'}</strong></span>
              <span>&bull;</span>
              <span>Team Size: <strong className="text-slate-300">{org?.org_size || '10-50'}</strong></span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setShowEditOrgModal(true)}
            className="flex items-center gap-1.5"
          >
            <Edit3 className="w-4 h-4" />
            <span>Edit Workspace</span>
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setShowInviteModal(true)}
            className="flex items-center gap-1.5"
          >
            <UserPlus className="w-4 h-4" />
            <span>Invite Team Member</span>
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center gap-2.5 text-rose-400 text-xs">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {successMsg && (
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center gap-2.5 text-emerald-400 text-xs">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Security Architecture & Entitlements Badge */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-[#090F1C] border border-[#1A2740]">
          <div className="text-[10px] uppercase font-bold tracking-wider text-slate-500">Tier 1 Collectors</div>
          <div className="text-lg font-bold text-slate-100 mt-1">Unlimited Fleet</div>
          <div className="text-[11px] text-emerald-400 mt-0.5">Zero per-node licensing fee</div>
        </div>
        <div className="p-4 rounded-xl bg-[#090F1C] border border-[#1A2740]">
          <div className="text-[10px] uppercase font-bold tracking-wider text-slate-500">Egress Verification</div>
          <div className="text-lg font-bold text-slate-100 mt-1">100% Zero-Trust</div>
          <div className="text-[11px] text-cyan-400 mt-0.5">SHA-256 allowlist proofing</div>
        </div>
        <div className="p-4 rounded-xl bg-[#090F1C] border border-[#1A2740]">
          <div className="text-[10px] uppercase font-bold tracking-wider text-slate-500">AIOps Intelligence</div>
          <div className="text-lg font-bold text-slate-100 mt-1">Autonomous Correlation</div>
          <div className="text-[11px] text-purple-400 mt-0.5">Explainable root cause analysis</div>
        </div>
        <div className="p-4 rounded-xl bg-[#090F1C] border border-[#1A2740]">
          <div className="text-[10px] uppercase font-bold tracking-wider text-slate-500">Team Governance</div>
          <div className="text-lg font-bold text-slate-100 mt-1">Role-Based RBAC</div>
          <div className="text-[11px] text-teal-400 mt-0.5">{members.length} Active Collaborators</div>
        </div>
      </div>

      {/* Member Management Table */}
      <div className="glass-panel rounded-2xl border border-[#1A2740] overflow-hidden">
        <div className="p-5 border-b border-[#1A2740] flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <Users className="w-4 h-4 text-cyan-400" />
              Organization Members & Collaborators
            </h2>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Manage operators, security analysts, and administrators authorized to access telemetry.
            </p>
          </div>
          <span className="text-xs text-slate-400">Total: <strong className="text-slate-200">{members.length}</strong></span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#090F1C] text-slate-400 uppercase font-bold text-[10px] border-b border-[#1A2740]">
              <tr>
                <th className="px-5 py-3">Member</th>
                <th className="px-5 py-3">Role</th>
                <th className="px-5 py-3">Job Title</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3">Joined Date</th>
                <th className="px-5 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1A2740]">
              {members.map((m) => (
                <tr key={m.membership_id || m.user_id} className="hover:bg-[#0D1524]/60 transition">
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-cyan-950 border border-cyan-500/30 text-cyan-300 font-bold text-xs flex items-center justify-center shrink-0">
                        {m.full_name?.charAt(0) || 'U'}
                      </div>
                      <div>
                        <div className="font-semibold text-slate-200 flex items-center gap-1.5">
                          {m.full_name}
                          {m.user_id === user?.id && (
                            <span className="text-[9px] bg-slate-800 text-slate-400 px-1.5 py-0.2 rounded">You</span>
                          )}
                        </div>
                        <div className="text-[11px] text-slate-400 font-mono">{m.email}</div>
                      </div>
                    </div>
                  </td>

                  <td className="px-5 py-3.5">
                    <select
                      value={m.role}
                      onChange={(e) => handleUpdateRole(m.membership_id, e.target.value)}
                      disabled={m.user_id === user?.id && m.role === 'Organization Owner'}
                      className={`px-2.5 py-1 rounded-lg border text-[11px] font-semibold outline-none transition bg-[#070C14] ${
                        roleBadgeColors[m.role] || 'border-[#1A2740] text-slate-300'
                      }`}
                    >
                      <option value="Organization Owner">Organization Owner</option>
                      <option value="Admin">Admin</option>
                      <option value="Security Analyst">Security Analyst</option>
                      <option value="Infrastructure Engineer">Infrastructure Engineer</option>
                      <option value="Operator">Operator</option>
                      <option value="Viewer">Viewer</option>
                    </select>
                  </td>

                  <td className="px-5 py-3.5 text-slate-300">
                    {m.job_title || 'Systems Engineer'}
                  </td>

                  <td className="px-5 py-3.5">
                    <span className="inline-flex items-center gap-1.5 text-[11px] text-emerald-400 font-medium">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                      Active
                    </span>
                  </td>

                  <td className="px-5 py-3.5 text-slate-400 font-mono text-[11px]">
                    {m.created_at ? new Date(m.created_at).toLocaleDateString() : 'Just now'}
                  </td>

                  <td className="px-5 py-3.5 text-right">
                    {m.user_id !== user?.id && (
                      <button
                        onClick={() => handleRemoveMember(m.membership_id)}
                        className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition"
                        title="Remove member"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Invite Member Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="glass-panel w-full max-w-md p-6 rounded-2xl border border-[#1A2740] shadow-2xl relative">
            <div className="flex items-center justify-between pb-3 border-b border-[#1A2740]">
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <UserPlus className="w-4 h-4 text-cyan-400" />
                Invite Team Member
              </h3>
              <button onClick={() => setShowInviteModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleInviteSubmit} className="mt-4 space-y-4 text-xs">
              <div>
                <label className="block text-slate-300 font-semibold mb-1">Corporate Email Address</label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="email"
                    required
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    placeholder="colleague@company.com"
                    className="w-full pl-9 pr-3 py-2 rounded-xl bg-[#070C14] border border-[#1A2740] text-slate-100 focus:border-cyan-400 outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  value={inviteName}
                  onChange={(e) => setInviteName(e.target.value)}
                  placeholder="Helena Vance"
                  className="w-full px-3 py-2 rounded-xl bg-[#070C14] border border-[#1A2740] text-slate-100 focus:border-cyan-400 outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Assigned Role</label>
                  <select
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-[#070C14] border border-[#1A2740] text-slate-100 focus:border-cyan-400 outline-none"
                  >
                    <option value="Admin">Admin</option>
                    <option value="Security Analyst">Security Analyst</option>
                    <option value="Infrastructure Engineer">Infrastructure Engineer</option>
                    <option value="Operator">Operator</option>
                    <option value="Viewer">Viewer</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Job Title</label>
                  <input
                    type="text"
                    value={inviteTitle}
                    onChange={(e) => setInviteTitle(e.target.value)}
                    placeholder="SOC Lead"
                    className="w-full px-3 py-2 rounded-xl bg-[#070C14] border border-[#1A2740] text-slate-100 focus:border-cyan-400 outline-none"
                  />
                </div>
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <Button variant="secondary" size="sm" type="button" onClick={() => setShowInviteModal(false)}>
                  Cancel
                </Button>
                <Button variant="primary" size="sm" type="submit" disabled={inviteLoading}>
                  {inviteLoading ? 'Sending Invitation...' : 'Send Invitation'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Workspace Modal */}
      {showEditOrgModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="glass-panel w-full max-w-md p-6 rounded-2xl border border-[#1A2740] shadow-2xl relative">
            <div className="flex items-center justify-between pb-3 border-b border-[#1A2740]">
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <Building2 className="w-4 h-4 text-cyan-400" />
                Edit Workspace Settings
              </h3>
              <button onClick={() => setShowEditOrgModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSaveOrg} className="mt-4 space-y-4 text-xs">
              <div>
                <label className="block text-slate-300 font-semibold mb-1">Company / Organization Name</label>
                <input
                  type="text"
                  required
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-[#070C14] border border-[#1A2740] text-slate-100 focus:border-cyan-400 outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Industry</label>
                  <select
                    value={editIndustry}
                    onChange={(e) => setEditIndustry(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-[#070C14] border border-[#1A2740] text-slate-100 focus:border-cyan-400 outline-none"
                  >
                    <option value="Technology">Technology</option>
                    <option value="FinTech">FinTech</option>
                    <option value="Healthcare">Healthcare</option>
                    <option value="E-Commerce">E-Commerce</option>
                    <option value="Government">Government</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Team Size</label>
                  <select
                    value={editSize}
                    onChange={(e) => setEditSize(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-[#070C14] border border-[#1A2740] text-slate-100 focus:border-cyan-400 outline-none"
                  >
                    <option value="1-10">1-10</option>
                    <option value="10-50">10-50</option>
                    <option value="50-200">50-200</option>
                    <option value="200-1000">200-1000</option>
                    <option value="1000+">1000+</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Website URL</label>
                <input
                  type="text"
                  value={editWebsite}
                  onChange={(e) => setEditWebsite(e.target.value)}
                  placeholder="https://company.com"
                  className="w-full px-3 py-2 rounded-xl bg-[#070C14] border border-[#1A2740] text-slate-100 focus:border-cyan-400 outline-none"
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <Button variant="secondary" size="sm" type="button" onClick={() => setShowEditOrgModal(false)}>
                  Cancel
                </Button>
                <Button variant="primary" size="sm" type="submit" disabled={editLoading}>
                  {editLoading ? 'Saving...' : 'Save Changes'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default OrganizationManagementView;
