import React from 'react';
import { 
  Bell, Sun, Moon, Search, LogOut, ShieldCheck, 
  Menu, User, Server
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import { useWebSocket } from '../../context/WebSocketContext';

const Navbar = ({ onMenuClick }) => {
  const { user, logout } = useAuth();
  const { isDark, toggleTheme } = useTheme();
  const { isConnected } = useWebSocket();

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

        <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#070C14]/60 border border-[#1A2740] text-xs text-slate-400">
          <Server className="w-3.5 h-3.5 text-cyan-400" />
          <span>Tenant: <strong className="text-slate-200">North America (US-East)</strong></span>
        </div>
      </div>

      {/* Right controls */}
      <div className="flex items-center gap-3.5">
        {/* Real-time WS status indicator */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono bg-[#070C14]/70 border border-[#1A2740]">
          <span className={`h-2 w-2 rounded-full ${isConnected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
          <span className="text-slate-400 hidden sm:inline">{isConnected ? 'LIVE WS CONNECTED' : 'WS RECONNECTING'}</span>
        </div>

        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          title="Toggle Light/Dark Theme"
          className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 transition cursor-pointer"
        >
          {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-cyan-400" />}
        </button>

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

