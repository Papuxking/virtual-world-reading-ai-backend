import { useState, useEffect } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { clearToken, getStoredUser } from '../services/api';
import { LayoutDashboard, LogOut, Gamepad2, Users, Sun, Moon, Menu, X, Trophy } from 'lucide-react';

export default function DashboardLayout() {
  const navigate = useNavigate();
  const user = getStoredUser();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark');

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [theme]);

  function handleLogout() {
    clearToken();
    navigate('/login');
  }

  return (
    <div className="min-h-screen bg-slate-50/50 dark:bg-surface-900 transition-colors duration-300 flex flex-col md:flex-row">
      {/* Mobile Header */}
      <header className="md:hidden flex items-center justify-between px-6 py-4 bg-white dark:bg-surface-800 border-b border-slate-200 dark:border-white/5 shadow-sm transition-colors duration-300">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-violet-500 flex items-center justify-center shadow-md shadow-primary-500/20">
            <Gamepad2 className="w-4 h-4 text-white" />
          </div>
          <span className="text-sm font-bold text-slate-800 dark:text-white leading-tight">Mundo Virtual</span>
        </div>
        <button
          onClick={() => setMobileOpen(true)}
          className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 dark:bg-white/5 dark:hover:bg-white/10 dark:text-gray-300 border border-slate-200 dark:border-white/5 transition-colors"
        >
          <Menu className="w-5 h-5" />
        </button>
      </header>

      {/* Mobile Sidebar Overlay/Drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity duration-300 animate-fade-in"
            onClick={() => setMobileOpen(false)}
          />
          {/* Drawer body */}
          <aside className="relative w-64 max-w-[80vw] bg-white dark:bg-surface-800/95 border-r border-slate-200 dark:border-white/5 flex flex-col h-full z-10 shadow-2xl transition-colors duration-300">
            <div className="absolute top-4 right-4">
              <button
                onClick={() => setMobileOpen(false)}
                className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 dark:bg-white/5 dark:hover:bg-white/10 dark:text-gray-300 border border-slate-200 dark:border-white/5 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <SidebarContent
              user={user}
              theme={theme}
              setTheme={setTheme}
              handleLogout={handleLogout}
              onLinkClick={() => setMobileOpen(false)}
            />
          </aside>
        </div>
      )}

      {/* Desktop Sidebar (Permanent) */}
      <aside className="hidden md:flex w-64 bg-white dark:bg-surface-800/40 border-r border-slate-200/80 dark:border-white/5 flex-col h-screen sticky top-0 transition-colors duration-300">
        <SidebarContent
          user={user}
          theme={theme}
          setTheme={setTheme}
          handleLogout={handleLogout}
        />
      </aside>

      {/* Main content */}
      <main className="flex-1 min-w-0 overflow-y-auto">
        <div className="p-6 sm:p-8 max-w-7xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

function SidebarContent({ user, theme, setTheme, handleLogout, onLinkClick }) {
  return (
    <div className="flex-1 flex flex-col h-full py-6">
      {/* Logo */}
      <div className="px-6 pb-6 border-b border-slate-200 dark:border-white/5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-violet-500 flex items-center justify-center shadow-lg shadow-primary-500/20">
            <Gamepad2 className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-slate-800 dark:text-white leading-tight">Mundo Virtual</h1>
            <p className="text-xs text-slate-400 dark:text-gray-500">Dashboard Admin</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-1">
        <NavLink
          to="/"
          end
          onClick={onLinkClick}
          className={({ isActive }) =>
            `flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-semibold border transition-all duration-200 ${
              isActive
                ? 'bg-primary-600/10 dark:bg-primary-600/20 text-primary-600 dark:text-primary-400 border-primary-500/20 dark:border-primary-500/30'
                : 'text-slate-600 dark:text-gray-400 hover:text-slate-800 dark:hover:text-gray-200 hover:bg-slate-100 dark:hover:bg-white/5 border-transparent'
            }`
          }
        >
          <LayoutDashboard className="w-5 h-5" />
          Vista General
        </NavLink>
        <NavLink
          to="/achievements"
          onClick={onLinkClick}
          className={({ isActive }) =>
            `flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-semibold border transition-all duration-200 ${
              isActive
                ? 'bg-amber-500/10 dark:bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/20 dark:border-amber-500/25'
                : 'text-slate-600 dark:text-gray-400 hover:text-slate-800 dark:hover:text-gray-200 hover:bg-slate-100 dark:hover:bg-white/5 border-transparent'
            }`
          }
        >
          <Trophy className="w-5 h-5" />
          Logros y Medallas
        </NavLink>
      </nav>

      {/* Theme Toggle */}
      <div className="px-4 py-4 border-t border-slate-200 dark:border-white/5">
        <p className="text-[10px] uppercase font-bold tracking-wider text-slate-400 dark:text-gray-500 mb-2 px-2">Tema</p>
        <div className="flex p-1 bg-slate-100 dark:bg-white/5 rounded-xl border border-slate-200/50 dark:border-white/5 transition-all duration-300">
          <button
            onClick={() => setTheme('light')}
            className={`flex-1 flex items-center justify-center gap-2 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 ${
              theme === 'light'
                ? 'bg-white text-primary-600 shadow-sm border border-slate-200/50'
                : 'text-slate-500 dark:text-gray-400 hover:text-slate-800 dark:hover:text-gray-200'
            }`}
          >
            <Sun className="w-3.5 h-3.5" />
            Claro
          </button>
          <button
            onClick={() => setTheme('dark')}
            className={`flex-1 flex items-center justify-center gap-2 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 ${
              theme === 'dark'
                ? 'bg-primary-600 dark:bg-primary-500/20 text-white dark:text-primary-400 shadow-sm dark:shadow-none'
                : 'text-slate-500 dark:text-gray-400 hover:text-slate-800 dark:hover:text-gray-200'
            }`}
          >
            <Moon className="w-3.5 h-3.5" />
            Oscuro
          </button>
        </div>
      </div>

      {/* User Info */}
      <div className="px-4 py-4 border-t border-slate-200 dark:border-white/5">
        <div className="flex items-center gap-3 mb-3 px-2">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center shadow-sm">
            <Users className="w-4 h-4 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-slate-700 dark:text-gray-200 truncate">{user?.display_name || 'Admin'}</p>
            <p className="text-xs text-slate-400 dark:text-gray-500 truncate">{user?.email}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 w-full px-3 py-2 text-sm font-medium text-slate-500 hover:text-red-600 hover:bg-red-50 dark:text-gray-400 dark:hover:text-red-400 dark:hover:bg-red-500/10 rounded-lg transition-colors border border-transparent hover:border-red-100 dark:hover:border-transparent"
        >
          <LogOut className="w-4 h-4" />
          Cerrar sesión
        </button>
      </div>
    </div>
  );
}
