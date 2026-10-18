import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAdminStats, getPlayers } from '../services/api';
import { TYPOLOGY_ORDER, TYPOLOGY_COLORS } from '../constants/typologies';
import {
  Users, Target, Star, Activity, Search,
  ChevronRight, TrendingUp, BookOpen, Award, Sparkles,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell,
} from 'recharts';

export default function OverviewPage() {
  const [stats, setStats] = useState(null);
  const [players, setPlayers] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  async function loadData() {
    try {
      const [statsData, playersData] = await Promise.all([
        getAdminStats(),
        getPlayers(),
      ]);
      setStats(statsData);
      setPlayers(playersData);
    } catch (err) {
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // eslint-disable-next-line
    loadData();
  }, []);

  async function handleSearch(value) {
    setSearch(value);
    try {
      const data = await getPlayers(value);
      setPlayers(data);
    } catch (err) {
      console.error('Search error:', err);
    }
  }

  const filteredPlayers = players;

  const typologyData = stats
    ? TYPOLOGY_ORDER.map((t) => ({
        name: t.substring(0, 4) + '.',
        fullName: t,
        sessions: stats.sessions_by_typology[t] || 0,
        color: TYPOLOGY_COLORS[t],
      }))
    : [];

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
      <div>
        <h1 className="text-3xl font-bold text-slate-800 dark:text-white">Vista General</h1>
        <p className="text-slate-500 dark:text-gray-400 mt-1">Resumen del progreso de todos los jugadores</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4">
        <StatCard
          icon={<Users className="w-5 h-5" />}
          label="Jugadores"
          value={stats?.total_players || 0}
          color="from-primary-500 to-indigo-500"
        />
        <StatCard
          icon={<BookOpen className="w-5 h-5" />}
          label="Sesiones"
          value={stats?.total_sessions || 0}
          color="from-violet-500 to-purple-500"
        />
        <StatCard
          icon={<Sparkles className="w-5 h-5" />}
          label="Sesiones de práctica"
          value={stats?.total_practice_sessions || 0}
          color="from-emerald-500 to-green-500"
        />
        <StatCard
          icon={<Star className="w-5 h-5" />}
          label="Puntos Totales"
          value={stats?.total_points?.toLocaleString() || '0'}
          color="from-amber-500 to-orange-500"
        />
        <StatCard
          icon={<Award className="w-5 h-5" />}
          label="Logros y Medallas Otorgadas"
          value={`${stats?.total_achievements || 0} 🏆 / ${stats?.total_achievements || 0} 🏅`}
          color="from-emerald-500 to-teal-500"
        />
        <StatCard
          icon={<Target className="w-5 h-5" />}
          label="Precisión"
          value={`${stats?.average_accuracy || 0}%`}
          color="from-sky-500 to-cyan-500"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sessions by Typology */}
        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-slate-700 dark:text-gray-300 mb-4 flex items-center gap-2">
            <Activity className="w-4 h-4 text-primary-500 dark:text-primary-400" />
            Sesiones por Tipología
          </h3>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={typologyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
                <XAxis dataKey="name" stroke="var(--chart-axis)" fontSize={12} />
                <YAxis stroke="var(--chart-axis)" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    background: 'var(--tooltip-bg)',
                    border: '1px solid var(--tooltip-border)',
                    borderRadius: '12px',
                    color: 'var(--tooltip-text)',
                  }}
                  formatter={(value, name, props) => [value, props.payload.fullName]}
                />
                <Bar dataKey="sessions" radius={[6, 6, 0, 0]}>
                  {typologyData.map((entry, index) => (
                    <Cell key={index} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Typology Distribution Pie */}
        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-slate-700 dark:text-gray-300 mb-4 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-primary-500 dark:text-primary-400" />
            Distribución de Sesiones
          </h3>
          <div className="h-56 flex items-center">
            <ResponsiveContainer width="60%" height="100%">
              <PieChart>
                <Pie
                  data={typologyData.filter((d) => d.sessions > 0)}
                  dataKey="sessions"
                  nameKey="fullName"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  innerRadius={40}
                  strokeWidth={0}
                >
                  {typologyData.map((entry, index) => (
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
            <div className="flex-1 space-y-2">
              {typologyData.map((t) => (
                <div key={t.fullName} className="flex items-center gap-2 text-xs">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: t.color }} />
                  <span className="text-slate-500 dark:text-gray-400">{t.fullName}</span>
                  <span className="text-slate-700 dark:text-gray-300 font-medium ml-auto">{t.sessions}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Players Table */}
      <div className="glass-card overflow-hidden">
        <div className="p-6 border-b border-slate-200/50 dark:border-white/5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <h3 className="text-lg font-semibold text-slate-800 dark:text-white flex items-center gap-2">
            <Users className="w-5 h-5 text-primary-500 dark:text-primary-400" />
            Jugadores
          </h3>
          <div className="relative max-w-sm w-full">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 dark:text-gray-500" />
            <input
              type="text"
              value={search}
              onChange={(e) => handleSearch(e.target.value)}
              placeholder="Buscar por nombre o email..."
              className="input-field pl-10 text-sm"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-200/50 dark:border-white/5">
                <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 dark:text-gray-400 uppercase tracking-wider">Jugador</th>
                <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 dark:text-gray-400 uppercase tracking-wider">Email</th>
                <th className="text-right px-6 py-3 text-xs font-semibold text-slate-500 dark:text-gray-400 uppercase tracking-wider">Puntos</th>
                <th className="text-right px-6 py-3 text-xs font-semibold text-slate-500 dark:text-gray-400 uppercase tracking-wider">Sesiones</th>
                <th className="text-right px-6 py-3 text-xs font-semibold text-slate-500 dark:text-gray-400 uppercase tracking-wider">Logros & Medallas</th>
                <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 dark:text-gray-400 uppercase tracking-wider">Último Acceso</th>
                <th className="px-6 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-white/5">
              {filteredPlayers.map((player) => (
                <tr
                  key={player.id}
                  onClick={() => navigate(`/players/${player.id}`)}
                  className="table-row-hover cursor-pointer"
                >
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold ${
                        player.character === 'women'
                          ? 'bg-pink-500/20 text-pink-500 dark:text-pink-400'
                          : 'bg-sky-500/20 text-sky-600 dark:text-sky-400'
                      }`}>
                        {player.character === 'women' ? '👩' : '👨'}
                      </div>
                      <span className="font-semibold text-slate-700 dark:text-gray-200">{player.display_name}</span>
                      {player.game_over && (
                        <span className="badge-danger text-[10px]">Juego terminado</span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-500 dark:text-gray-400">{player.email}</td>
                  <td className="px-6 py-4 text-right">
                    <span className="font-bold text-amber-600 dark:text-amber-400">{player.total_score.toLocaleString()}</span>
                  </td>
                  <td className="px-6 py-4 text-right text-sm text-slate-600 dark:text-gray-300">{player.total_sessions}</td>
                  <td className="px-6 py-4 text-right">
                    <span className="inline-flex items-center gap-1.5 bg-slate-50 dark:bg-white/[0.04] border border-slate-200 dark:border-white/5 px-2 py-0.5 rounded-lg text-xs font-bold text-slate-700 dark:text-gray-200">
                      <span>{player.total_achievements} 🏆</span>
                      <span className="text-slate-300 dark:text-white/10">|</span>
                      <span>{player.total_achievements} 🏅</span>
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-500 dark:text-gray-400">
                    {player.last_played_at
                      ? new Date(player.last_played_at).toLocaleDateString('es-EC', { day: '2-digit', month: 'short' })
                      : 'Nunca'}
                  </td>
                  <td className="px-6 py-4">
                    <ChevronRight className="w-4 h-4 text-slate-400 dark:text-gray-500" />
                  </td>
                </tr>
              ))}
              {filteredPlayers.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-slate-400 dark:text-gray-500">
                    No se encontraron jugadores
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
