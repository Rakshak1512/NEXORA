import React, { useEffect, useState } from 'react';
import { Users, ShieldCheck, Search, RefreshCw, UserPlus, Ban, CheckCircle2 } from 'lucide-react';
import api from '../services/api';

const AdminUsersView = () => {
  const [users, setUsers] = useState([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ email: '', full_name: '', password: '', role: 'Admin' });

  const load = async () => {
    setLoading(true); setError('');
    try { const res = await api.get('/admin/users'); setUsers(res.data || []); }
    catch (e) { setError(e.response?.data?.detail || 'Unable to load users. Super Administrator access is required.'); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const createUser = async (e) => {
    e.preventDefault(); setSaving(true); setError('');
    try {
      await api.post('/admin/users', form);
      setForm({ email: '', full_name: '', password: '', role: 'Admin' });
      await load();
    } catch (e) { setError(e.response?.data?.detail || 'Could not create user.'); }
    finally { setSaving(false); }
  };
  const updateUser = async (user, patch) => {
    setError('');
    try { await api.patch('/admin/users/' + user.id, patch); await load(); }
    catch (e) { setError(e.response?.data?.detail || 'Could not update user.'); }
  };
  const visible = users.filter(u => [u.email, u.full_name, u.role].join(' ').toLowerCase().includes(query.toLowerCase()));

  return <div className="p-5 md:p-8 space-y-6 text-slate-100">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div><div className="flex items-center gap-2 text-cyan-400 text-xs font-bold uppercase tracking-widest"><ShieldCheck size={15}/> Platform control</div>
        <h1 className="text-2xl font-bold mt-2">User Administration</h1><p className="text-sm text-slate-400 mt-1">Manage platform accounts, roles and access status.</p></div>
      <button onClick={load} className="flex items-center gap-2 rounded-lg border border-slate-700 px-3 py-2 text-sm hover:border-cyan-500"><RefreshCw size={15}/> Refresh</button>
    </div>
    {error && <div role="alert" className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-300">{error}</div>}
    <form onSubmit={createUser} className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
      <h2 className="font-semibold flex items-center gap-2"><UserPlus size={17}/> Create managed account</h2>
      <div className="grid md:grid-cols-2 gap-3">
        <input required type="text" minLength="2" placeholder="Full name" value={form.full_name} onChange={e=>setForm({...form,full_name:e.target.value})} className="rounded-lg bg-slate-950 border border-slate-700 p-3 text-sm"/>
        <input required type="email" placeholder="Email address" value={form.email} onChange={e=>setForm({...form,email:e.target.value})} className="rounded-lg bg-slate-950 border border-slate-700 p-3 text-sm"/>
        <input required type="password" minLength="12" placeholder="Temporary password (12+ characters)" value={form.password} onChange={e=>setForm({...form,password:e.target.value})} className="rounded-lg bg-slate-950 border border-slate-700 p-3 text-sm"/>
        <select value={form.role} onChange={e=>setForm({...form,role:e.target.value})} className="rounded-lg bg-slate-950 border border-slate-700 p-3 text-sm">
          {['Admin','Organization Owner','Security Analyst','Infrastructure Engineer','Operator','Viewer'].map(r=><option key={r}>{r}</option>)}
        </select>
      </div>
      <button disabled={saving} className="rounded-lg bg-cyan-500 px-4 py-2.5 text-sm font-bold text-slate-950 disabled:opacity-50">{saving?'Creating…':'Create account'}</button>
    </form>
    <section className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 border-b border-slate-800">
        <h2 className="font-semibold flex items-center gap-2"><Users size={17}/> All users <span className="text-xs text-slate-400">({users.length})</span></h2>
        <div className="relative"><Search size={15} className="absolute left-3 top-3 text-slate-500"/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search users…" className="rounded-lg bg-slate-950 border border-slate-700 pl-9 pr-3 py-2 text-sm"/></div>
      </div>
      {loading ? <p className="p-6 text-sm text-slate-400">Loading accounts…</p> : <div className="overflow-x-auto"><table className="w-full text-left text-sm">
        <thead className="text-xs uppercase text-slate-500 bg-slate-950/60"><tr><th className="p-3">User</th><th className="p-3">Role</th><th className="p-3">Verification</th><th className="p-3">Access</th><th className="p-3">Actions</th></tr></thead>
        <tbody>{visible.map(u=><tr key={u.id} className="border-t border-slate-800">
          <td className="p-3"><div className="font-medium">{u.full_name}</div><div className="text-xs text-slate-500">{u.email}</div></td>
          <td className="p-3"><select aria-label={'Role for '+u.email} value={u.role} disabled={u.role==='Super Administrator'} onChange={e=>updateUser(u,{role:e.target.value})} className="rounded bg-slate-950 border border-slate-700 p-2 text-xs">{['Super Administrator','Admin','Organization Owner','Security Analyst','Infrastructure Engineer','Operator','Viewer'].map(r=><option key={r}>{r}</option>)}</select></td>
          <td className="p-3">{u.is_verified?<span className="text-emerald-400 flex items-center gap-1"><CheckCircle2 size={14}/> Verified</span>:<span className="text-amber-400">Pending</span>}</td>
          <td className="p-3">{u.is_active?'Active':'Disabled'}</td>
          <td className="p-3"><button disabled={u.role==='Super Administrator'} onClick={()=>updateUser(u,{is_active:!u.is_active})} className="flex items-center gap-1 text-xs text-cyan-300 disabled:opacity-30"><Ban size={14}/>{u.is_active?'Disable':'Enable'}</button></td>
        </tr>)}</tbody>
      </table>{visible.length===0&&!loading&&<p className="p-6 text-sm text-slate-500">No matching accounts.</p>}</div>}
    </section>
  </div>;
};
export default AdminUsersView;
