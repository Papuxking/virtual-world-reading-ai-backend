import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { clearToken, getStoredUser } from '../services/api';
import { LayoutDashboard, LogOut, Gamepad2, Users } from 'lucide-react';

export default function DashboardLayout() {
  const navigate = useNavigate();
  const user = getStoredUser();

  function handleLogout() {
    clearToken();
    navigate('/login');
  }

  return (
    <div className="min-h-screen flex bg-surface-900">
      {/* Sidebar */}
      <aside className="w-64 bg-surface-800/50 border-r border-white/5 flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-white/5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-violet-500 flex items-center justify-center shadow-lg shadow-primary-500/20">
              <Gamepad2 className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-white leading-tight">Mundo Virtual</h1>
              <p className="text-xs text-gray-500">Dashboard Admin</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-primary-600/20 text-primary-400 border border-primary-500/20'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
              }`
            }
          >
            <LayoutDashboard className="w-5 h-5" />
            Vista General
          </NavLink>
        </nav>

        {/* User info */}
        <div className="p-4 border-t border-white/5">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center">
              <Users className="w-4 h-4 text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-200 truncate">{user?.display_name || 'Admin'}</p>
              <p className="text-xs text-gray-500 truncate">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 w-full px-3 py-2 text-sm text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Cerrar sesión
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <div className="p-8 max-w-7xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
