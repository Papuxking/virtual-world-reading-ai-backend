import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  getAchievementsDashboard, getAchievementsStats, getPlayers,
  downloadAchievementsCSV, downloadAchievementsExcel,
} from '../services/api';
import {
  Trophy, Search, Filter, Download, ChevronRight,
  BarChart3, Medal, Crown, Star, TrendingUp, Users, Award,
  FileSpreadsheet, FileText, ChevronDown,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell,
} from 'recharts';

const TIER_COLORS = {
  bronce: '#d97706',
  plata: '#64748b',
  oro: '#eab308',
  platino: '#8b5cf6',
};

const TIER_LABELS = {
  bronce: 'Bronce',
  plata: 'Plata',
  oro: 'Oro',
  platino: 'Platino',
};

const CATEGORY_COLORS = {
  progreso: '#3b82f6',
  maestría: '#a855f7',
  exploración: '#14b8a6',
  superación: '#f97316',
};

const TIER_BADGE_CLASS = {
  bronce: 'badge-bronze',
  plata: 'badge-silver',
  oro: 'badge-gold',
  platino: 'badge-platinum',
};

const CATEGORY_BADGE_CLASS = {
  progreso: 'badge-progreso',
  maestría: 'badge-maestria',
  exploración: 'badge-exploracion',
  superación: 'badge-superacion',
};

const API_BASE = import.meta.env.VITE_API_BASE ?? '';

export default function AchievementsPage() {
  const navigate = useNavigate();
  const [achievements, setAchievements] = useState([]);
  const [stats, setStats] = useState(null);
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showExportMenu, setShowExportMenu] = useState(false);

  // Filtros
  const [search, setSearch] = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  const [filterTier, setFilterTier] = useState('');
  const [filterPlayerId, setFilterPlayerId] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [sortBy, setSortBy] = useState('display_order');
  const [sortOrder, setSortOrder] = useState('asc');

  const loadData = useCallback(async () => {
    try {
      const [statsData, playersData] = await Promise.all([
        getAchievementsStats(),
        getPlayers(),
      ]);
      setStats(statsData);
      setPlayers(playersData);
    } catch (err) {
      console.error('Error loading data:', err);
    }
  }, []);

  const loadAchievements = useCallback(async () => {
    try {
      const filters = {};
      if (search) filters.q = search;
      if (filterCategory) filters.category = filterCategory;
      if (filterTier) filters.tier = filterTier;
      if (filterPlayerId) filters.player_id = filterPlayerId;
      if (filterStatus && filterPlayerId) filters.unlock_status = filterStatus;
      filters.sort = sortBy;
      filters.order = sortOrder;

      const data = await getAchievementsDashboard(filters);
      setAchievements(data);
    } catch (err) {
      console.error('Error loading achievements:', err);
    } finally {
      setLoading(false);
    }
  }, [search, filterCategory, filterTier, filterPlayerId, filterStatus, sortBy, sortOrder]);

  useEffect(() => { loadData(); }, [loadData]);
  useEffect(() => { loadAchievements(); }, [loadAchievements]);

  // Debounced search
  const [searchTimeout, setSearchTimeout] = useState(null);
  function handleSearch(value) {
    if (searchTimeout) clearTimeout(searchTimeout);
    const timeout = setTimeout(() => setSearch(value), 300);
    setSearchTimeout(timeout);
  }

  // Chart data
  const categoryData = stats
    ? Object.entries(stats.distribution_by_category).map(([name, count]) => ({
      name: name.charAt(0).toUpperCase() + name.slice(1),
      count,
      color: CATEGORY_COLORS[name] || '#6366f1',
    }))
    : [];

  const tierData = stats
    ? Object.entries(stats.distribution_by_tier).map(([name, count]) => ({
      name: TIER_LABELS[name] || name,
      rawName: name,
      count,
      color: TIER_COLORS[name] || '#6366f1',
    }))
    : [];

  const topData = stats?.top_unlocked?.map(item => ({
    name: item.icon + ' ' + item.name.replace(/^[^\s]+\s/, '').substring(0, 15),
    fullName: item.name,
    count: item.unlock_count,
    percentage: item.percentage,
  })) || [];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-3 border-primary-500/30 border-t-primary-500 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-800 dark:text-white flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center shadow-lg shadow-amber-500/20">
              <Trophy className="w-5 h-5 text-white" />
            </div>
            Logros y Medallas
          </h1>
          <p className="text-slate-500 dark:text-gray-400 mt-1">
            Gestión del catálogo de logros, medallas e imágenes
          </p>
        </div>

        {/* Export Button */}
        <div className="relative">
          <button
            onClick={() => setShowExportMenu(!showExportMenu)}
            className="btn-primary flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            Exportar
            <ChevronDown className="w-3.5 h-3.5" />
          </button>
          {showExportMenu && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setShowExportMenu(false)} />
              <div className="absolute right-0 top-full mt-2 w-52 bg-white dark:bg-surface-800 border border-slate-200 dark:border-white/10 rounded-xl shadow-xl z-20 py-1 animate-slide-up">
                <button
                  onClick={() => { downloadAchievementsCSV({ category: filterCategory, tier: filterTier }); setShowExportMenu(false); }}
                  className="flex items-center gap-2.5 w-full px-4 py-2.5 text-sm text-slate-700 dark:text-gray-300 hover:bg-slate-50 dark:hover:bg-white/5 transition-colors"
                >
                  <FileText className="w-4 h-4 text-emerald-500" />
                  Exportar CSV
                </button>
                <button
                  onClick={() => { downloadAchievementsExcel({ category: filterCategory, tier: filterTier }); setShowExportMenu(false); }}
                  className="flex items-center gap-2.5 w-full px-4 py-2.5 text-sm text-slate-700 dark:text-gray-300 hover:bg-slate-50 dark:hover:bg-white/5 transition-colors"
                >
                  <FileSpreadsheet className="w-4 h-4 text-primary-500" />
                  Exportar Excel
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<Trophy className="w-5 h-5" />}
          label="Total Logros Activos"
          value={stats?.total_active || 0}
          color="from-amber-500 to-orange-500"
        />
        <StatCard
          icon={<Medal className="w-5 h-5" />}
          label="Total Desbloqueos"
          value={stats?.total_unlocks || 0}
          color="from-primary-500 to-violet-500"
        />
        <StatCard
          icon={<Users className="w-5 h-5" />}
          label="Jugadores con Logros"
          value={stats?.unique_players_with_unlocks || 0}
          color="from-emerald-500 to-teal-500"
        />
        <StatCard
          icon={<TrendingUp className="w-5 h-5" />}
          label="% Desbloqueo Promedio"
          value={`${stats?.average_unlock_percentage || 0}%`}
          color="from-sky-500 to-cyan-500"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Distribution by Category */}
        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-slate-700 dark:text-gray-300 mb-4 flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-primary-500 dark:text-primary-400" />
            Distribución por Categoría
          </h3>
          <div className="h-52">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={categoryData}
                  dataKey="count"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={75}
                  innerRadius={40}
                  strokeWidth={0}
                >
                  {categoryData.map((entry, index) => (
                    <Cell key={index} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: 'var(--tooltip-bg)',
                    border: '1px solid var(--tooltip-border)',
                    borderRadius: '12px',
                    color: 'var(--tooltip-text)',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="space-y-1.5 mt-2">
            {categoryData.map(c => (
              <div key={c.name} className="flex items-center gap-2 text-xs">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: c.color }} />
                <span className="text-slate-500 dark:text-gray-400">{c.name}</span>
                <span className="text-slate-700 dark:text-gray-300 font-medium ml-auto">{c.count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Distribution by Tier */}
        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-slate-700 dark:text-gray-300 mb-4 flex items-center gap-2">
            <Crown className="w-4 h-4 text-yellow-500 dark:text-yellow-400" />
            Distribución por Tier
          </h3>
          <div className="h-52">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={tierData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
                <XAxis type="number" stroke="var(--chart-axis)" fontSize={12} />
                <YAxis type="category" dataKey="name" stroke="var(--chart-axis)" fontSize={12} width={60} />
                <Tooltip
                  contentStyle={{
                    background: 'var(--tooltip-bg)',
                    border: '1px solid var(--tooltip-border)',
                    borderRadius: '12px',
                    color: 'var(--tooltip-text)',
                  }}
                />
                <Bar dataKey="count" radius={[0, 6, 6, 0]}>
                  {tierData.map((entry, index) => (
                    <Cell key={index} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Unlocked */}
        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-slate-700 dark:text-gray-300 mb-4 flex items-center gap-2">
            <Star className="w-4 h-4 text-amber-500 dark:text-amber-400" />
            Top Más Desbloqueados
          </h3>
          <div className="space-y-3">
            {topData.map((item, i) => (
              <div key={i} className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-600 dark:text-gray-300 font-medium truncate max-w-[70%]">{item.name}</span>
                  <span className="text-slate-500 dark:text-gray-400">{item.count} ({item.percentage}%)</span>
                </div>
                <div className="progress-bar">
                  <div
                    className="progress-bar-fill bg-gradient-to-r from-primary-500 to-violet-500"
                    style={{ width: `${Math.min(item.percentage, 100)}%` }}
                  />
                </div>
              </div>
            ))}
            {topData.length === 0 && (
              <p className="text-xs text-slate-400 dark:text-gray-500 text-center py-8">Sin datos de desbloqueos</p>
            )}
          </div>
        </div>
      </div>

      {/* Filters & Table */}
      <div className="glass-card overflow-hidden">
        {/* Filter Bar */}
        <div className="p-6 border-b border-slate-200/50 dark:border-white/5 space-y-4">
          <div className="flex flex-col lg:flex-row items-start lg:items-center gap-4">
            <h3 className="text-lg font-semibold text-slate-800 dark:text-white flex items-center gap-2 shrink-0">
              <Award className="w-5 h-5 text-primary-500 dark:text-primary-400" />
              Catálogo
            </h3>

            {/* Search */}
            <div className="relative flex-1 max-w-sm w-full">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 dark:text-gray-500" />
              <input
                type="text"
                onChange={(e) => handleSearch(e.target.value)}
                placeholder="Buscar por nombre..."
                className="input-field pl-10 text-sm"
                id="achievements-search"
              />
            </div>

            {/* Filters */}
            <div className="flex flex-wrap items-center gap-2">
              <div className="flex items-center gap-1.5">
                <Filter className="w-3.5 h-3.5 text-slate-400" />
              </div>

              <select
                value={filterCategory}
                onChange={(e) => setFilterCategory(e.target.value)}
                className="input-field text-sm py-1.5 px-3 w-auto min-w-[120px]"
                id="filter-category"
              >
                <option value="">Categoría</option>
                <option value="progreso">Progreso</option>
                <option value="maestría">Maestría</option>
                <option value="exploración">Exploración</option>
                <option value="superación">Superación</option>
              </select>

              <select
                value={filterTier}
                onChange={(e) => setFilterTier(e.target.value)}
                className="input-field text-sm py-1.5 px-3 w-auto min-w-[100px]"
                id="filter-tier"
              >
                <option value="">Tier</option>
                <option value="bronce">Bronce</option>
                <option value="plata">Plata</option>
                <option value="oro">Oro</option>
                <option value="platino">Platino</option>
              </select>

              <select
                value={filterPlayerId}
                onChange={(e) => { setFilterPlayerId(e.target.value); if (!e.target.value) setFilterStatus(''); }}
                className="input-field text-sm py-1.5 px-3 w-auto min-w-[140px]"
                id="filter-player"
              >
                <option value="">Jugador</option>
                {players.map(p => (
                  <option key={p.id} value={p.id}>{p.display_name}</option>
                ))}
              </select>

              {filterPlayerId && (
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="input-field text-sm py-1.5 px-3 w-auto min-w-[120px] animate-slide-up"
                  id="filter-status"
                >
                  <option value="">Estado</option>
                  <option value="unlocked">Desbloqueado</option>
                  <option value="locked">Pendiente</option>
                </select>
              )}

              <select
                value={`${sortBy}-${sortOrder}`}
                onChange={(e) => {
                  const [s, o] = e.target.value.split('-');
                  setSortBy(s);
                  setSortOrder(o);
                }}
                className="input-field text-sm py-1.5 px-3 w-auto min-w-[130px]"
                id="sort-achievements"
              >
                <option value="display_order-asc">Orden ↑</option>
                <option value="display_order-desc">Orden ↓</option>
                <option value="name-asc">Nombre A-Z</option>
                <option value="name-desc">Nombre Z-A</option>
                <option value="unlock_count-desc">Más desbloqueados</option>
                <option value="unlock_count-asc">Menos desbloqueados</option>
                <option value="medal_tier-asc">Tier ↑</option>
                <option value="medal_tier-desc">Tier ↓</option>
              </select>
            </div>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full" id="achievements-table">
            <thead>
              <tr className="border-b border-slate-200/50 dark:border-white/5">
                <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 dark:text-gray-400 uppercase tracking-wider">Medalla</th>
                <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 dark:text-gray-400 uppercase tracking-wider">Logro</th>
                <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 dark:text-gray-400 uppercase tracking-wider">Categoría</th>
                <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 dark:text-gray-400 uppercase tracking-wider">Tier</th>
                <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 dark:text-gray-400 uppercase tracking-wider min-w-[200px]">Desbloqueo</th>
                {filterPlayerId && (
                  <th className="text-center px-6 py-3 text-xs font-semibold text-slate-500 dark:text-gray-400 uppercase tracking-wider">Estado</th>
                )}
                <th className="px-6 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-white/5">
              {achievements.map((ach, i) => (
                <tr
                  key={ach.id}
                  onClick={() => navigate(`/achievements/${ach.id}`)}
                  className="table-row-hover cursor-pointer animate-card-in"
                  style={{ animationDelay: `${i * 30}ms` }}
                >
                  {/* Medal Image */}
                  <td className="px-6 py-4">
                    <div className="w-12 h-12 rounded-xl bg-slate-100 dark:bg-white/5 flex items-center justify-center overflow-hidden border border-slate-200/50 dark:border-white/10">
                      {ach.medal_image_path ? (
                        <img
                          src={`${API_BASE}${ach.medal_image_path}`}
                          alt={ach.medal_name}
                          className="w-full h-full object-cover"
                          onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex'; }}
                        />
                      ) : null}
                      <span
                        className="text-2xl"
                        style={ach.medal_image_path ? { display: 'none' } : {}}
                      >
                        {ach.medal_placeholder_emoji || ach.icon}
                      </span>
                    </div>
                  </td>

                  {/* Name & Description */}
                  <td className="px-6 py-4 max-w-[250px]">
                    <p className="font-semibold text-slate-700 dark:text-gray-200 truncate">{ach.name}</p>
                    <p className="text-xs text-slate-400 dark:text-gray-500 truncate mt-0.5">{ach.medal_name}</p>
                  </td>

                  {/* Category */}
                  <td className="px-6 py-4">
                    <span className={CATEGORY_BADGE_CLASS[ach.category] || 'badge-info'}>
                      {ach.category.charAt(0).toUpperCase() + ach.category.slice(1)}
                    </span>
                  </td>

                  {/* Tier */}
                  <td className="px-6 py-4">
                    <span className={TIER_BADGE_CLASS[ach.medal_tier] || 'badge-info'}>
                      {TIER_LABELS[ach.medal_tier] || ach.medal_tier}
                    </span>
                  </td>

                  {/* Unlock Stats */}
                  <td className="px-6 py-4">
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-600 dark:text-gray-300 font-medium">
                          {ach.unlock_count}/{ach.total_players} jugadores
                        </span>
                        <span className="text-slate-500 dark:text-gray-400 font-bold">
                          {ach.unlock_percentage}%
                        </span>
                      </div>
                      <div className="progress-bar">
                        <div
                          className="progress-bar-fill"
                          style={{
                            width: `${Math.min(ach.unlock_percentage, 100)}%`,
                            background: `linear-gradient(90deg, ${TIER_COLORS[ach.medal_tier] || '#6366f1'}, ${TIER_COLORS[ach.medal_tier] || '#8b5cf6'}bb)`,
                          }}
                        />
                      </div>
                    </div>
                  </td>

                  {/* Player unlock status */}
                  {filterPlayerId && (
                    <td className="px-6 py-4 text-center">
                      {ach.is_unlocked_by_player ? (
                        <span className="badge-success">✓ Desbloqueado</span>
                      ) : (
                        <span className="badge-locked">🔒 Pendiente</span>
                      )}
                    </td>
                  )}

                  <td className="px-6 py-4">
                    <ChevronRight className="w-4 h-4 text-slate-400 dark:text-gray-500" />
                  </td>
                </tr>
              ))}
              {achievements.length === 0 && (
                <tr>
                  <td colSpan={filterPlayerId ? 7 : 6} className="px-6 py-16 text-center text-slate-400 dark:text-gray-500">
                    <Trophy className="w-8 h-8 mx-auto mb-2 opacity-30" />
                    No se encontraron logros con los filtros seleccionados
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon, label, value, color }) {
  return (
    <div className="stat-card group">
      <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center shadow-md mb-3 text-white`}>
        {icon}
      </div>
      <p className="text-2xl font-extrabold text-slate-800 dark:text-white">{value}</p>
      <p className="text-xs font-semibold text-slate-400 dark:text-gray-400 mt-1">{label}</p>
    </div>
  );
}
