import { useState, useEffect, useCallback } from 'react';
import {
  getMetricsReadingTime, getMetricsAnswers, getMetricsQuestionAttempts,
  getMetricsNpcInteractions, getMetricsToolUsage, getPlayers,
  downloadMetricsCSV, downloadMetricsExcel,
} from '../services/api';
import { TYPOLOGY_ORDER, TYPOLOGY_COLORS } from '../constants/typologies';
import {
  Clock, CheckCircle, XCircle, MessageCircle, Wrench,
  Download, FileSpreadsheet, Filter, RotateCcw, HelpCircle,
  TrendingUp, BarChart3, AlertTriangle, RefreshCcw,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
} from 'recharts';

const LEVEL_COLORS = {
  Literal: '#22c55e',
  Inferencial: '#f59e0b',
  Critico: '#ef4444',
  Crítico: '#ef4444',
};

const TOOL_COLORS = ['#6366f1', '#8b5cf6', '#ec4899'];

const TABS = [
  { id: 'reading-time', label: 'Tiempos de Lectura', icon: Clock },
  { id: 'answers', label: 'Respuestas', icon: CheckCircle },
  { id: 'question-attempts', label: 'Intentos', icon: HelpCircle },
  { id: 'npc-interactions', label: 'Interacciones NPC', icon: MessageCircle },
  { id: 'tool-usage', label: 'Herramientas', icon: Wrench },
];

export default function MetricsPage() {
  const [activeTab, setActiveTab] = useState('reading-time');
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [players, setPlayers] = useState([]);
  const [filters, setFilters] = useState({
    date_from: '',
    date_to: '',
    player_id: '',
    typology: '',
  });
  const [appliedFilters, setAppliedFilters] = useState({});
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    getPlayers().then(setPlayers).catch(() => {});
  }, []);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const f = appliedFilters;
      let result = null;
      switch (activeTab) {
        case 'reading-time':
          result = await getMetricsReadingTime(f);
          break;
        case 'answers':
          result = await getMetricsAnswers(f);
          break;
        case 'question-attempts':
          result = await getMetricsQuestionAttempts(f);
          break;
        case 'npc-interactions':
          result = await getMetricsNpcInteractions(f);
          break;
        case 'tool-usage':
          result = await getMetricsToolUsage(f);
          break;
        default:
          result = null;
      }
      setData(result);
    } catch (err) {
      console.error('Error loading metrics:', err);
      setError(err.message || 'Error al cargar las métricas. Verifica que la API esté ejecutándose.');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [activeTab, appliedFilters]);

  useEffect(() => { loadData(); }, [loadData]);

  function applyFilters() {
    const clean = {};
    if (filters.date_from) clean.date_from = new Date(filters.date_from).toISOString();
    if (filters.date_to) clean.date_to = new Date(filters.date_to).toISOString();
    if (filters.player_id) clean.player_id = filters.player_id;
    if (filters.typology) clean.typology = filters.typology;
    setAppliedFilters(clean);
  }

  function clearFilters() {
    setFilters({ date_from: '', date_to: '', player_id: '', typology: '' });
    setAppliedFilters({});
  }

  const tooltipStyle = {
    background: 'var(--tooltip-bg)',
    border: '1px solid var(--tooltip-border)',
    borderRadius: '12px',
    color: 'var(--tooltip-text)',
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-800 dark:text-white flex items-center gap-3">
            <BarChart3 className="w-8 h-8 text-primary-500" />
            Métricas y Reportes
          </h1>
          <p className="text-slate-500 dark:text-gray-400 mt-1">Análisis detallado del progreso de jugadores</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold border transition-all ${
              showFilters || Object.keys(appliedFilters).length > 0
                ? 'bg-primary-500/10 text-primary-600 dark:text-primary-400 border-primary-500/20'
                : 'bg-white dark:bg-white/5 text-slate-600 dark:text-gray-400 border-slate-200 dark:border-white/10 hover:bg-slate-50 dark:hover:bg-white/10'
            }`}
          >
            <Filter className="w-4 h-4" />
            Filtros
            {Object.keys(appliedFilters).length > 0 && (
              <span className="w-5 h-5 rounded-full bg-primary-500 text-white text-xs flex items-center justify-center">
                {Object.keys(appliedFilters).length}
              </span>
            )}
          </button>
          <button
            onClick={() => downloadMetricsCSV(activeTab, appliedFilters)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold bg-white dark:bg-white/5 text-slate-600 dark:text-gray-400 border border-slate-200 dark:border-white/10 hover:bg-slate-50 dark:hover:bg-white/10 transition-all"
          >
            <Download className="w-4 h-4" /> CSV
          </button>
          <button
            onClick={() => downloadMetricsExcel(activeTab, appliedFilters)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20 transition-all"
          >
            <FileSpreadsheet className="w-4 h-4" /> Excel
          </button>
        </div>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="glass-card p-6 animate-fade-in">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-gray-400 mb-1.5">Desde</label>
              <input
                type="date"
                value={filters.date_from}
                onChange={(e) => setFilters({ ...filters, date_from: e.target.value })}
                className="input-field text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-gray-400 mb-1.5">Hasta</label>
              <input
                type="date"
                value={filters.date_to}
                onChange={(e) => setFilters({ ...filters, date_to: e.target.value })}
                className="input-field text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-gray-400 mb-1.5">Jugador</label>
              <select
                value={filters.player_id}
                onChange={(e) => setFilters({ ...filters, player_id: e.target.value })}
                className="input-field text-sm"
              >
                <option value="">Todos</option>
                {players.map((p) => (
                  <option key={p.id} value={p.id}>{p.display_name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-gray-400 mb-1.5">Tipología</label>
              <select
                value={filters.typology}
                onChange={(e) => setFilters({ ...filters, typology: e.target.value })}
                className="input-field text-sm"
              >
                <option value="">Todas</option>
                {TYPOLOGY_ORDER.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            <div className="flex items-end gap-2">
              <button
                onClick={applyFilters}
                className="flex-1 px-4 py-2.5 rounded-xl text-sm font-bold bg-primary-500 text-white hover:bg-primary-600 transition-all shadow-md shadow-primary-500/20"
              >
                Aplicar
              </button>
              <button
                onClick={clearFilters}
                className="p-2.5 rounded-xl text-slate-400 hover:text-slate-600 dark:hover:text-gray-200 hover:bg-slate-100 dark:hover:bg-white/5 transition-all"
                title="Limpiar filtros"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 p-1 bg-white dark:bg-white/5 rounded-2xl border border-slate-200 dark:border-white/5 overflow-x-auto">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold whitespace-nowrap transition-all ${
              activeTab === id
                ? 'bg-primary-500 text-white shadow-md shadow-primary-500/20'
                : 'text-slate-500 dark:text-gray-400 hover:text-slate-700 dark:hover:text-gray-200 hover:bg-slate-50 dark:hover:bg-white/5'
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex flex-col items-center justify-center h-64 gap-3">
          <div className="w-8 h-8 border-3 border-primary-500/30 border-t-primary-500 rounded-full animate-spin" />
          <p className="text-sm text-slate-400 dark:text-gray-500">Cargando métricas...</p>
        </div>
      ) : error ? (
        <div className="glass-card p-12 text-center animate-fade-in">
          <AlertTriangle className="w-12 h-12 text-amber-500 mx-auto mb-4" />
          <h3 className="text-lg font-bold text-slate-700 dark:text-gray-200 mb-2">Error al cargar métricas</h3>
          <p className="text-sm text-slate-500 dark:text-gray-400 mb-6 max-w-md mx-auto">{error}</p>
          <button
            onClick={loadData}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold bg-primary-500 text-white hover:bg-primary-600 transition-all shadow-md shadow-primary-500/20"
          >
            <RefreshCcw className="w-4 h-4" />
            Reintentar
          </button>
        </div>
      ) : data ? (
        <div className="space-y-6">
          {activeTab === 'reading-time' && <ReadingTimePanel data={data} tooltipStyle={tooltipStyle} />}
          {activeTab === 'answers' && <AnswersPanel data={data} tooltipStyle={tooltipStyle} />}
          {activeTab === 'question-attempts' && <QuestionAttemptsPanel data={data} />}
          {activeTab === 'npc-interactions' && <NpcInteractionsPanel data={data} tooltipStyle={tooltipStyle} />}
          {activeTab === 'tool-usage' && <ToolUsagePanel data={data} tooltipStyle={tooltipStyle} />}
        </div>
      ) : (
        <div className="glass-card p-12 text-center">
          <BarChart3 className="w-12 h-12 text-slate-300 dark:text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-bold text-slate-600 dark:text-gray-300 mb-2">Sin datos disponibles</h3>
          <p className="text-sm text-slate-400 dark:text-gray-500">
            No se encontraron datos para los filtros seleccionados. Intenta ajustar los filtros o verifica que haya sesiones registradas.
          </p>
        </div>
      )}
    </div>
  );
}


// ── Panel: Tiempos de Lectura ───────────────────────────────────────────────

function ReadingTimePanel({ data, tooltipStyle }) {
  const byTypology = data.by_typology || [];
  const byPlayer = data.by_player || [];

  const typologyData = byTypology.map((t) => ({
    name: (t.typology || '').substring(0, 5) + '.',
    fullName: t.typology || '',
    lectura: Math.round(t.avg_reading_time || 0),
    total: Math.round(t.avg_total_time || 0),
  }));

  return (
    <>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <KpiCard icon={<Clock className="w-5 h-5" />} label="Tiempo Lectura Prom." value={`${Math.round(data.avg_reading_time || 0)}s`} color="from-sky-500 to-cyan-500" />
        <KpiCard icon={<TrendingUp className="w-5 h-5" />} label="Tiempo Total Prom." value={`${Math.round(data.avg_total_time || 0)}s`} color="from-violet-500 to-purple-500" />
        <KpiCard icon={<BarChart3 className="w-5 h-5" />} label="Total Sesiones" value={data.total_sessions || 0} color="from-primary-500 to-indigo-500" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-slate-700 dark:text-gray-300 mb-4">Tiempos por Tipología</h3>
          {typologyData.length > 0 ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={typologyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
                  <XAxis dataKey="name" stroke="var(--chart-axis)" fontSize={12} />
                  <YAxis stroke="var(--chart-axis)" fontSize={12} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Legend />
                  <Bar dataKey="lectura" name="Lectura (s)" fill="#6366f1" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="total" name="Total (s)" fill="#a855f7" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <EmptyState message="No hay datos de tipologías aún" />
          )}
        </div>

        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-slate-700 dark:text-gray-300 mb-4">Tiempos por Jugador</h3>
          {byPlayer.length > 0 ? (
            <div className="overflow-x-auto max-h-64 overflow-y-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200/50 dark:border-white/5">
                    <th className="text-left px-3 py-2 text-xs font-semibold text-slate-500 dark:text-gray-400">Jugador</th>
                    <th className="text-right px-3 py-2 text-xs font-semibold text-slate-500 dark:text-gray-400">Lectura</th>
                    <th className="text-right px-3 py-2 text-xs font-semibold text-slate-500 dark:text-gray-400">Total</th>
                    <th className="text-right px-3 py-2 text-xs font-semibold text-slate-500 dark:text-gray-400">Sesiones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-white/5">
                  {byPlayer.map((p) => (
                    <tr key={p.player_id} className="hover:bg-slate-50 dark:hover:bg-white/[0.02]">
                      <td className="px-3 py-2 font-medium text-slate-700 dark:text-gray-200">{p.display_name}</td>
                      <td className="px-3 py-2 text-right text-slate-500 dark:text-gray-400">{Math.round(p.avg_reading_time || 0)}s</td>
                      <td className="px-3 py-2 text-right text-slate-500 dark:text-gray-400">{Math.round(p.avg_total_time || 0)}s</td>
                      <td className="px-3 py-2 text-right font-bold text-slate-700 dark:text-gray-200">{p.total_sessions || 0}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState message="No hay datos de jugadores aún" />
          )}
        </div>
      </div>
    </>
  );
}


// ── Panel: Respuestas ───────────────────────────────────────────────────────

function AnswersPanel({ data, tooltipStyle }) {
  const byLevel = data.by_level || [];
  const byPlayer = data.by_player || [];

  const levelData = byLevel.map((l) => ({
    name: l.level || '',
    correctas: l.total_correct || 0,
    incorrectas: l.total_incorrect || 0,
  }));

  const totalCorrect = data.total_correct || 0;
  const totalIncorrect = data.total_incorrect || 0;
  const pieData = [
    { name: 'Correctas', value: totalCorrect, color: '#22c55e' },
    { name: 'Incorrectas', value: totalIncorrect, color: '#ef4444' },
  ].filter((d) => d.value > 0);

  return (
    <>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <KpiCard icon={<CheckCircle className="w-5 h-5" />} label="Correctas" value={totalCorrect} color="from-emerald-500 to-green-500" />
        <KpiCard icon={<XCircle className="w-5 h-5" />} label="Incorrectas" value={totalIncorrect} color="from-red-500 to-rose-500" />
        <KpiCard icon={<TrendingUp className="w-5 h-5" />} label="Precisión Global" value={`${data.overall_accuracy || 0}%`} color="from-primary-500 to-indigo-500" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-slate-700 dark:text-gray-300 mb-4">Respuestas por Nivel</h3>
          {levelData.length > 0 ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={levelData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
                  <XAxis dataKey="name" stroke="var(--chart-axis)" fontSize={12} />
                  <YAxis stroke="var(--chart-axis)" fontSize={12} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Legend />
                  <Bar dataKey="correctas" name="Correctas" fill="#22c55e" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="incorrectas" name="Incorrectas" fill="#ef4444" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <EmptyState message="No hay datos de respuestas por nivel" />
          )}
        </div>

        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-slate-700 dark:text-gray-300 mb-4">Distribución Global</h3>
          {pieData.length > 0 ? (
            <div className="h-64 flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} innerRadius={45} strokeWidth={0}>
                    {pieData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                  </Pie>
                  <Tooltip contentStyle={tooltipStyle} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <EmptyState message="No hay respuestas registradas aún" />
          )}
        </div>
      </div>

      {byPlayer.length > 0 && (
        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-slate-700 dark:text-gray-300 mb-4">Precisión por Jugador</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200/50 dark:border-white/5">
                  <th className="text-left px-3 py-2 text-xs font-semibold text-slate-500 dark:text-gray-400">Jugador</th>
                  <th className="text-right px-3 py-2 text-xs font-semibold text-slate-500 dark:text-gray-400">Correctas</th>
                  <th className="text-right px-3 py-2 text-xs font-semibold text-slate-500 dark:text-gray-400">Incorrectas</th>
                  <th className="text-right px-3 py-2 text-xs font-semibold text-slate-500 dark:text-gray-400">Precisión</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-white/5">
                {byPlayer.map((p) => (
                  <tr key={p.player_id} className="hover:bg-slate-50 dark:hover:bg-white/[0.02]">
                    <td className="px-3 py-2 font-medium text-slate-700 dark:text-gray-200">{p.display_name}</td>
                    <td className="px-3 py-2 text-right text-emerald-600 dark:text-emerald-400 font-bold">{p.total_correct || 0}</td>
                    <td className="px-3 py-2 text-right text-red-500 dark:text-red-400">{p.total_incorrect || 0}</td>
                    <td className="px-3 py-2 text-right">
                      <span className={`px-2 py-0.5 rounded-lg text-xs font-bold ${
                        (p.accuracy || 0) >= 70 ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400' :
                        (p.accuracy || 0) >= 50 ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400' :
                        'bg-red-500/10 text-red-600 dark:text-red-400'
                      }`}>
                        {p.accuracy || 0}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}


// ── Panel: Intentos por Pregunta ─────────────────────────────────────────────

function QuestionAttemptsPanel({ data }) {
  const questions = data.questions || [];

  return (
    <div className="glass-card overflow-hidden">
      <div className="p-6 border-b border-slate-200/50 dark:border-white/5">
        <h3 className="text-sm font-semibold text-slate-700 dark:text-gray-300 flex items-center gap-2">
          <HelpCircle className="w-4 h-4 text-primary-500" />
          Intentos por Pregunta ({data.total_questions || 0} preguntas)
        </h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200/50 dark:border-white/5">
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 dark:text-gray-400">Pregunta</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 dark:text-gray-400">Lectura</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 dark:text-gray-400">Tipología</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 dark:text-gray-400">Nivel</th>
              <th className="text-right px-4 py-3 text-xs font-semibold text-slate-500 dark:text-gray-400">Intentos</th>
              <th className="text-right px-4 py-3 text-xs font-semibold text-slate-500 dark:text-gray-400">Tasa Acierto</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-white/5">
            {questions.map((q) => (
              <tr key={q.question_id} className="hover:bg-slate-50 dark:hover:bg-white/[0.02]">
                <td className="px-4 py-3 text-slate-700 dark:text-gray-200 max-w-xs truncate">{q.question_text}</td>
                <td className="px-4 py-3 text-slate-500 dark:text-gray-400 text-xs max-w-[120px] truncate">{q.reading_title}</td>
                <td className="px-4 py-3">
                  <span className="px-2 py-0.5 rounded-lg text-xs font-bold" style={{ backgroundColor: `${TYPOLOGY_COLORS[q.typology] || '#6366f1'}20`, color: TYPOLOGY_COLORS[q.typology] || '#6366f1' }}>
                    {q.typology}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className="px-2 py-0.5 rounded-lg text-xs font-bold" style={{ backgroundColor: `${LEVEL_COLORS[q.comprehension_level] || '#6366f1'}20`, color: LEVEL_COLORS[q.comprehension_level] || '#6366f1' }}>
                    {q.comprehension_level}
                  </span>
                </td>
                <td className="px-4 py-3 text-right font-bold text-slate-700 dark:text-gray-200">{q.total_attempts || 0}</td>
                <td className="px-4 py-3 text-right">
                  <span className={`px-2 py-0.5 rounded-lg text-xs font-bold ${
                    (q.correct_rate || 0) >= 70 ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400' :
                    (q.correct_rate || 0) >= 50 ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400' :
                    'bg-red-500/10 text-red-600 dark:text-red-400'
                  }`}>
                    {q.correct_rate || 0}%
                  </span>
                </td>
              </tr>
            ))}
            {questions.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-12 text-center text-slate-400 dark:text-gray-500">
                  No hay datos de intentos disponibles
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}


// ── Panel: Interacciones NPC ────────────────────────────────────────────────

function NpcInteractionsPanel({ data, tooltipStyle }) {
  const totalRobot = data.total_robot || 0;
  const totalSabio = data.total_sabio || 0;
  const totalAll = data.total_all || 0;
  const byPlayer = data.by_player || [];

  const npcData = [
    { name: '🤖 Robot', value: totalRobot, color: '#6366f1' },
    { name: '🧙 Sabio', value: totalSabio, color: '#f59e0b' },
  ].filter((d) => d.value > 0);

  const playerData = byPlayer.slice(0, 10).map((p) => ({
    name: (p.display_name || '').length > 10 ? p.display_name.substring(0, 10) + '.' : (p.display_name || ''),
    robot: p.robot_interactions || 0,
    sabio: p.sabio_interactions || 0,
  }));

  return (
    <>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <KpiCard icon={<span className="text-lg">🤖</span>} label="Robot Asistente" value={totalRobot} color="from-primary-500 to-indigo-500" />
        <KpiCard icon={<span className="text-lg">🧙</span>} label="Sabio" value={totalSabio} color="from-amber-500 to-orange-500" />
        <KpiCard icon={<MessageCircle className="w-5 h-5" />} label="Total Interacciones" value={totalAll} color="from-emerald-500 to-teal-500" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-slate-700 dark:text-gray-300 mb-4">Distribución por NPC</h3>
          {npcData.length > 0 ? (
            <div className="h-64 flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={npcData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} innerRadius={45} strokeWidth={0}>
                    {npcData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                  </Pie>
                  <Tooltip contentStyle={tooltipStyle} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <EmptyState message="No hay interacciones NPC registradas aún" />
          )}
        </div>

        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-slate-700 dark:text-gray-300 mb-4">Top Jugadores por Interacciones</h3>
          {playerData.length > 0 ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={playerData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
                  <XAxis type="number" stroke="var(--chart-axis)" fontSize={12} />
                  <YAxis dataKey="name" type="category" stroke="var(--chart-axis)" fontSize={11} width={80} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Legend />
                  <Bar dataKey="robot" name="🤖 Robot" fill="#6366f1" stackId="a" radius={[0, 0, 0, 0]} />
                  <Bar dataKey="sabio" name="🧙 Sabio" fill="#f59e0b" stackId="a" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <EmptyState message="No hay datos de jugadores aún" />
          )}
        </div>
      </div>
    </>
  );
}


// ── Panel: Uso de Herramientas ───────────────────────────────────────────────

function ToolUsagePanel({ data, tooltipStyle }) {
  const tools = data.tools || [];

  const radarData = tools.map((t) => ({
    tool: t.tool_name === 'highlight' ? 'Resaltado' : t.tool_name === 'underline' ? 'Subrayado' : t.tool_name === 'notes' ? 'Notas' : t.tool_name,
    uso: t.usage_rate || 0,
    full: 100,
  }));

  return (
    <>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard icon={<Wrench className="w-5 h-5" />} label="Total Sesiones" value={data.total_sessions || 0} color="from-primary-500 to-indigo-500" />
        {tools.map((t, i) => (
          <KpiCard
            key={t.tool_name}
            icon={<span className="text-lg">{t.tool_name === 'highlight' ? '🖍️' : t.tool_name === 'underline' ? '📏' : '📝'}</span>}
            label={t.tool_name === 'highlight' ? 'Resaltado' : t.tool_name === 'underline' ? 'Subrayado' : 'Notas'}
            value={`${t.usage_rate || 0}%`}
            color={i === 0 ? 'from-violet-500 to-purple-500' : i === 1 ? 'from-pink-500 to-rose-500' : 'from-amber-500 to-orange-500'}
          />
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-slate-700 dark:text-gray-300 mb-4">Tasa de Uso por Herramienta</h3>
          {radarData.length > 0 ? (
            <div className="h-64 flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData}>
                  <PolarGrid stroke="var(--chart-grid)" />
                  <PolarAngleAxis dataKey="tool" stroke="var(--chart-axis)" fontSize={12} />
                  <PolarRadiusAxis angle={90} domain={[0, 100]} stroke="var(--chart-axis)" fontSize={10} />
                  <Radar name="Uso (%)" dataKey="uso" stroke="#6366f1" fill="#6366f1" fillOpacity={0.3} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <EmptyState message="No hay datos de herramientas aún" />
          )}
        </div>

        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-slate-700 dark:text-gray-300 mb-4">Detalle de Herramientas</h3>
          {tools.length > 0 ? (
            <div className="space-y-4">
              {tools.map((t, i) => (
                <div key={t.tool_name} className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center text-lg" style={{ backgroundColor: `${TOOL_COLORS[i] || '#6366f1'}15` }}>
                    {t.tool_name === 'highlight' ? '🖍️' : t.tool_name === 'underline' ? '📏' : '📝'}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-semibold text-slate-700 dark:text-gray-200">
                        {t.tool_name === 'highlight' ? 'Resaltado' : t.tool_name === 'underline' ? 'Subrayado' : 'Notas'}
                      </span>
                      <span className="text-sm font-bold text-primary-600 dark:text-primary-400">{t.usage_rate || 0}%</span>
                    </div>
                    <div className="w-full h-2 bg-slate-100 dark:bg-white/5 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{ width: `${t.usage_rate || 0}%`, backgroundColor: TOOL_COLORS[i] || '#6366f1' }}
                      />
                    </div>
                    <p className="text-xs text-slate-400 dark:text-gray-500 mt-1">{t.times_used || 0} usos en {t.total_sessions || 0} sesiones</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState message="No hay datos de herramientas aún" />
          )}
        </div>
      </div>
    </>
  );
}


// ── Componentes Compartidos ─────────────────────────────────────────────────

function KpiCard({ icon, label, value, color }) {
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

function EmptyState({ message }) {
  return (
    <div className="flex flex-col items-center justify-center h-48 text-center">
      <BarChart3 className="w-8 h-8 text-slate-200 dark:text-gray-700 mb-3" />
      <p className="text-sm text-slate-400 dark:text-gray-500">{message}</p>
    </div>
  );
}
