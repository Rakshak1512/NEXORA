import React, { useState, useEffect, useRef } from 'react';
import { 
  Bell, Search, LogOut, ShieldCheck, 
  Menu, User, Server, Building2, Check, CheckCheck, ExternalLink, X
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useWebSocket } from '../../context/WebSocketContext';
import api from '../../services/api';

const Navbar = ({ onMenuClick }) => {
  const { user, organization, logout } = useAuth();
  const { isConnected } = useWebSocket();

  // Notification state
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showNotifDropdown, setShowNotifDropdown] = useState(false);
  const notifRef = useRef(null);

  const fetchNotifications = async () => {
    try {
      const res = await api.get('/notifications');
      setNotifications(res.data);
      const unread = res.data.filter(n => !n.is_read).length;
      setUnreadCount(unread);
    } catch (e) {
      // Ignore background notification fetch errors
    }
  };

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 15000);
    return () => clearInterval(interval);
  }, []);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (notifRef.current && !notifRef.current.contains(e.target)) {
        setShowNotifDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleMarkAllRead = async () => {
    try {
      await api.post('/notifications/read-all');
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (e) {}
  };

  const handleMarkRead = async (id) => {
    try {
      await api.post(`/notifications/${id}/read`);
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (e) {}
  };

  return (
    <header className="sticky top-0 z-30 h-16 border-b border-[#1A2740] glass-panel px-4 md:px-6 flex items-center justify-between">
      {/* Left side */}
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          className="lg:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Organization & Tenant badge */}
        <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#070C14]/60 border border-[#1A2740] text-xs text-slate-400">
          <Building2 className="w-3.5 h-3.5 text-cyan-400" />
          <span>Org: <strong className="text-slate-200">{organization?.name || 'AcroGlobal Financial'}</strong></span>
          <span className="text-slate-600">|</span>
          <span>Tenant: <strong className="text-slate-300">Primary Cloud</strong></span>
        </div>
      </div>

      {/* Right controls */}
      <div className="flex items-center gap-3.5">
        {/* Real-time WS status indicator */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono bg-[#070C14]/70 border border-[#1A2740]">
          <span className={`h-2 w-2 rounded-full ${isConnected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
          <span className="text-slate-400 hidden md:inline">{isConnected ? 'LIVE WS CONNECTED' : 'WS RECONNECTING'}</span>
        </div>

        {/* Notification Bell */}
        <div className="relative" ref={notifRef}>
          <button
            onClick={() => setShowNotifDropdown(!showNotifDropdown)}
            className="p-2 rounded-xl bg-[#070C14]/60 border border-[#1A2740] text-slate-300 hover:text-white hover:border-cyan-500/40 transition relative cursor-pointer"
            title="Notifications"
          >
            <Bell className="w-4 h-4" />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 bg-cyan-500 text-slate-950 font-extrabold text-[9px] rounded-full flex items-center justify-center animate-bounce">
                {unreadCount}
              </span>
            )}
          </button>

          {/* Dropdown Menu */}
          {showNotifDropdown && (
            <div className="absolute right-0 mt-2 w-80 sm:w-96 glass-panel rounded-2xl border border-[#1A2740] shadow-2xl p-4 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
              <div className="flex items-center justify-between pb-3 border-b border-[#1A2740]">
                <div className="flex items-center gap-2">
                  <Bell className="w-4 h-4 text-cyan-400" />
                  <span className="text-xs font-bold text-slate-100">Notifications</span>
                  {unreadCount > 0 && (
                    <span className="px-1.5 py-0.2 bg-cyan-500/20 text-cyan-300 rounded text-[10px] font-bold">
                      {unreadCount} new
                    </span>
                  )}
                </div>
                {unreadCount > 0 && (
                  <button
                    onClick={handleMarkAllRead}
                    className="text-[10px] text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-semibold cursor-pointer"
                  >
                    <CheckCheck className="w-3 h-3" />
                    Mark all read
                  </button>
                )}
              </div>

              <div className="max-h-72 overflow-y-auto divide-y divide-[#1A2740]/60 my-2 space-y-1">
                {notifications.length === 0 ? (
                  <div className="py-6 text-center text-xs text-slate-500">
                    No new notifications
                  </div>
                ) : (
                  notifications.map((n) => (
                    <div
                      key={n.id}
                      className={`p-2.5 rounded-xl transition ${n.is_read ? 'opacity-60 hover:opacity-100' : 'bg-cyan-950/20 border border-cyan-500/20'}`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="font-semibold text-xs text-slate-200">{n.title}</div>
                        {!n.is_read && (
                          <button
                            onClick={() => handleMarkRead(n.id)}
                            className="p-1 rounded text-slate-500 hover:text-cyan-400"
                            title="Mark read"
                          >
                            <Check className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">{n.message}</p>
                      <div className="text-[9px] text-slate-500 font-mono mt-1.5">
                        {new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* User profile dropdown / logout */}
        <div className="flex items-center gap-3 pl-3 border-l border-[#1A2740]">
          <div className="text-right hidden sm:block">
            <div className="text-xs font-semibold text-slate-200">{user?.full_name || 'Alex Vance'}</div>
            <div className="text-[10px] text-cyan-400 font-medium tracking-wide uppercase">{user?.role || 'Super Administrator'}</div>
          </div>
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-600 to-teal-400 flex items-center justify-center text-slate-950 font-bold text-xs shadow-md shadow-cyan-500/20">
            {user?.full_name ? user.full_name.charAt(0) : 'A'}
          </div>
          <button
            onClick={logout}
            title="Log out"
            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition cursor-pointer"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
