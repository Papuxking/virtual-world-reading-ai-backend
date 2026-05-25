import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getPlayerDetail, resetTypology, resetAllProgress } from '../services/api';
import {
  ArrowLeft, Star, Trophy, BookOpen, Target, CheckCircle2,
  XCircle, Lock, Unlock, RotateCcw, AlertTriangle, StickyNote,
  Highlighter, Underline, PenTool, ChevronDown, ChevronUp, Award,
} from 'lucide-react';

const DIFFICULTY_ORDER = ['Narrativo', 'Descriptivo', 'Argumentativo', 'Instructivo', 'Expositivo'];
const DIFFICULTY_COLORS = {
  Narrativo: { bg: 'bg-indigo-50 dark:bg-indigo-500/10', text: 'text-indigo-600 dark:text-indigo-400', border: 'border-indigo-100 dark:border-indigo-500/20', bar: 'bg-indigo-500' },
  Descriptivo: { bg: 'bg-violet-50 dark:bg-violet-500/10', text: 'text-violet-600 dark:text-violet-400', border: 'border-violet-100 dark:border-violet-500/20', bar: 'bg-violet-500' },
  Argumentativo: { bg: 'bg-purple-50 dark:bg-purple-500/10', text: 'text-purple-600 dark:text-purple-400', border: 'border-purple-100 dark:border-purple-500/20', bar: 'bg-purple-500' },
  Instructivo: { bg: 'bg-fuchsia-50 dark:bg-fuchsia-500/10', text: 'text-fuchsia-600 dark:text-fuchsia-400', border: 'border-fuchsia-100 dark:border-fuchsia-500/20', bar: 'bg-fuchsia-500' },
  Expositivo: { bg: 'bg-pink-50 dark:bg-pink-500/10', text: 'text-pink-600 dark:text-pink-400', border: 'border-pink-100 dark:border-pink-500/20', bar: 'bg-pink-500' },
};

const TOOL_ICONS = { highlight: Highlighter, underline: Underline, notes: PenTool };
const TOOL_LABELS = { highlight: 'Resaltar', underline: 'Subrayar', notes: 'Notas' };

const ALL_ACHIEVEMENTS = {
  first_reading: '📖 Primera lectura',
  explorer: '🏅 Explorador',
  perfectionist: '🎯 Perfeccionista',
  avid_reader: '📚 Lector ávido',
  star_literal: '⭐ Estrella literal',
  star_inferencial: '⭐⭐ Estrella inferencial',
  star_critico: '⭐⭐⭐ Estrella crítica',
  improvement: '📈 En mejora',
  centurion: '💯 Centurión',
  half_millennium: '🏆 Medio milenio',
};

export default function PlayerDetailPage() {
  const { playerId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedSession, setExpandedSession] = useState(null);
  const [resetModal, setResetModal] = useState(null); // { type: 'typology' | 'all', typology?: string }
  const [confirmEmail, setConfirmEmail] = useState('');
  const [resetLoading, setResetLoading] = useState(false);
  const [resetError, setResetError] = useState('');
  const [selectedNotesTypology, setSelectedNotesTypology] = useState('Narrativo');
  const [selectedReadingId, setSelectedReadingId] = useState(null);

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playerId]);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const detail = await getPlayerDetail(playerId);
      setData(detail);
    } catch (err) {
      console.error(err);
      setError(err.message || 'Error al cargar datos del jugador');
    } finally {
      setLoading(false);
    }
  }

  async function handleReset() {
    setResetError('');
    setResetLoading(true);
    try {
      if (resetModal.type === 'typology') {
        await resetTypology(playerId, resetModal.typology, confirmEmail);
      } else {
        await resetAllProgress(playerId, confirmEmail);
      }
      setResetModal(null);
      setConfirmEmail('');
      await loadData();
    } catch (err) {
      setResetError(err.message);
    } finally {
      setResetLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-3 border-primary-500/30 border-t-primary-500 rounded-full animate-spin" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center py-20 animate-fade-in">
        <p className="text-slate-500 dark:text-gray-400 mb-4">{error || 'Jugador no encontrado'}</p>
        <div className="flex items-center justify-center gap-3">
          <button onClick={() => navigate('/')} className="btn-ghost text-sm">
            ← Volver
          </button>
          {error && (
            <button onClick={loadData} className="btn-primary text-sm">
              Reintentar
            </button>
          )}
        </div>
      </div>
    );
  }

  const { user, total_score, typology_progress, achievements, sessions, notes, tool_stats, level_stats } = data;
  const unlockedAchievementIds = achievements.map((a) => a.achievement_id);

  // Agrupar y deduplicar lecturas presentadas al estudiante por tipología
  const presentedReadingsByTypology = DIFFICULTY_ORDER.reduce((acc, typo) => {
    // Lecturas de sesiones de esta tipología
    const fromSessions = sessions
      .filter((s) => s.typology === typo)
      .map((s) => ({ id: s.reading_id, title: s.reading_title }));

    // Lecturas con notas de esta tipología
    const fromNotes = notes
      .filter((n) => n.reading_typology === typo)
      .map((n) => ({ id: n.reading_id, title: n.reading_title }));

    // Combinar y deduplicar por ID de lectura (o título si ID es nulo)
    const merged = [...fromSessions, ...fromNotes];
    const uniqueMap = new Map();
    merged.forEach((item) => {
      if (item.id) {
        uniqueMap.set(item.id, item.title);
      } else if (item.title) {
        uniqueMap.set(item.title, item.title);
      }
    });

    acc[typo] = Array.from(uniqueMap.entries()).map(([id, title]) => ({
      id,
      title,
    }));
    return acc;
  }, {});


  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate('/')} className="btn-ghost p-2">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-lg ${
              user.character === 'women' ? 'bg-pink-500/20 text-pink-500' : 'bg-sky-500/20 text-sky-500'
            }`}>
              {user.character === 'women' ? '👩' : '👨'}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-800 dark:text-white">{user.display_name}</h1>
              <p className="text-sm text-slate-500 dark:text-gray-400">{user.email}</p>
            </div>
          </div>
        </div>
        <div className="text-left sm:text-right px-2 sm:px-0">
          <p className="text-xs text-slate-400 dark:text-gray-500 uppercase font-semibold">Registrado</p>
          <p className="text-sm font-semibold text-slate-700 dark:text-gray-300">{new Date(user.created_at).toLocaleDateString('es-EC')}</p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="stat-card">
          <Star className="w-5 h-5 text-amber-500 mb-2" />
          <p className="text-2xl font-extrabold text-slate-800 dark:text-white">{total_score.toLocaleString()}</p>
          <p className="text-xs font-semibold text-slate-400 dark:text-gray-400">Puntos totales</p>
        </div>
        <div className="stat-card">
          <BookOpen className="w-5 h-5 text-violet-500 mb-2" />
          <p className="text-2xl font-extrabold text-slate-800 dark:text-white">{sessions.length}</p>
          <p className="text-xs font-semibold text-slate-400 dark:text-gray-400">Sesiones</p>
        </div>
        <div className="stat-card">
          <Award className="w-5 h-5 text-emerald-500 mb-2" />
          <p className="text-2xl font-extrabold text-slate-800 dark:text-white">{achievements.length}/10</p>
          <p className="text-xs font-semibold text-slate-400 dark:text-gray-400">Logros</p>
        </div>
        <div className="stat-card">
          <Target className="w-5 h-5 text-sky-500 mb-2" />
          <p className="text-2xl font-extrabold text-slate-800 dark:text-white">
            {level_stats.length > 0
              ? `${Math.round(level_stats.reduce((s, l) => s + l.correct, 0) / Math.max(1, level_stats.reduce((s, l) => s + l.total, 0)) * 100)}%`
              : '—'}
          </p>
          <p className="text-xs font-semibold text-slate-400 dark:text-gray-400">Precisión</p>
        </div>
      </div>

      {/* Typology Progress */}
      <div className="glass-card p-6">
        <h3 className="text-lg font-semibold text-slate-800 dark:text-white mb-4 flex items-center gap-2">
          <Trophy className="w-5 h-5 text-primary-500 dark:text-primary-400" />
          Progreso por Tipología
        </h3>
        <div className="space-y-4">
          {DIFFICULTY_ORDER.map((typology) => {
            const progress = typology_progress.find((tp) => tp.typology === typology);
            const colors = DIFFICULTY_COLORS[typology];
            const score = progress?.best_score || 0;
            const maxScore = 350;
            const pct = Math.min(100, (score / maxScore) * 100);

            return (
              <div key={typology} className={`p-4 rounded-xl border ${colors.border} ${colors.bg}`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {progress?.is_unlocked ? (
                      <Unlock className={`w-4 h-4 ${colors.text}`} />
                    ) : (
                      <Lock className="w-4 h-4 text-slate-400 dark:text-gray-500" />
                    )}
                    <span className={`font-semibold ${progress?.is_unlocked ? colors.text : 'text-slate-400 dark:text-gray-500'}`}>
                      {typology}
                    </span>
                    {progress?.is_unlocked && (
                      <span className="badge-success text-[10px]">Desbloqueado</span>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-bold text-slate-800 dark:text-white">{score} pts</span>
                    <span className="text-xs text-slate-500 dark:text-gray-400">{progress?.total_sessions || 0} sesiones</span>
                    {progress?.is_unlocked && progress?.total_sessions > 0 && (
                      <button
                        onClick={() => setResetModal({ type: 'typology', typology })}
                        className="text-xs text-slate-400 hover:text-red-600 dark:text-gray-500 dark:hover:text-red-400 transition-colors flex items-center gap-1 font-semibold"
                        title="Reiniciar esta tipología y las superiores"
                      >
                        <RotateCcw className="w-3 h-3" />
                        Reiniciar
                      </button>
                    )}
                  </div>
                </div>
                <div className="w-full bg-slate-200/50 dark:bg-white/5 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${colors.bar} transition-all duration-500`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
                <div className="flex justify-between mt-1">
                  <span className="text-[10px] text-slate-400 dark:text-gray-500 font-semibold">0</span>
                  <span className="text-[10px] text-slate-400 dark:text-gray-500 font-semibold">Umbral: 250</span>
                  <span className="text-[10px] text-slate-400 dark:text-gray-500 font-semibold">{maxScore}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Sessions, Achievements, Tools, Notes */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sessions History */}
        <div className="glass-card p-6">
          <h3 className="text-lg font-semibold text-slate-800 dark:text-white mb-4 flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-primary-500 dark:text-primary-400" />
            Historial de Sesiones
          </h3>
          <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
            {sessions.length === 0 ? (
              <p className="text-sm text-slate-400 dark:text-gray-500 py-4 text-center">Sin sesiones registradas</p>
            ) : (
              sessions.map((session) => (
                <div key={session.id} className="border border-slate-200/60 dark:border-white/5 rounded-xl overflow-hidden bg-white dark:bg-transparent">
                  <button
                    onClick={() => setExpandedSession(expandedSession === session.id ? null : session.id)}
                    className="w-full p-3 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-white/5 transition-colors"
                  >
                    <div className="flex items-center gap-3 text-left">
                      <div className={`w-2 h-2 rounded-full ${session.is_perfect ? 'bg-emerald-400' : 'bg-amber-400'}`} />
                      <div>
                        <p className="text-sm font-semibold text-slate-700 dark:text-gray-200 truncate max-w-[180px]">
                          {session.reading_title}
                        </p>
                        <p className="text-xs text-slate-400 dark:text-gray-500 font-medium">
                          {session.typology} · {session.completed_at
                            ? new Date(session.completed_at).toLocaleDateString('es-EC', { day: '2-digit', month: 'short' })
                            : '—'}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-bold text-amber-600 dark:text-amber-400">{session.session_score} pts</span>
                      <span className="text-xs text-slate-500 dark:text-gray-400 font-semibold">{session.correct_count}/{session.correct_count + session.incorrect_count}</span>
                      {expandedSession === session.id ? (
                        <ChevronUp className="w-4 h-4 text-slate-400 dark:text-gray-500" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-slate-400 dark:text-gray-500" />
                      )}
                    </div>
                  </button>
                  {expandedSession === session.id && (
                    <div className="px-3 pb-3 border-t border-slate-200/50 dark:border-white/5 mt-0 pt-3 animate-slide-up bg-slate-50/30 dark:bg-transparent">
                      <div className="grid grid-cols-3 gap-2 text-xs mb-3">
                        <div className="text-center">
                          <p className="text-slate-400 dark:text-gray-500 font-semibold">Lectura</p>
                          <p className="text-slate-700 dark:text-gray-300 font-bold">
                            {session.reading_time_seconds ? `${Math.floor(session.reading_time_seconds / 60)}m ${session.reading_time_seconds % 60}s` : '—'}
                          </p>
                        </div>
                        <div className="text-center">
                          <p className="text-slate-400 dark:text-gray-500 font-semibold">Total</p>
                          <p className="text-slate-700 dark:text-gray-300 font-bold">
                            {session.total_time_seconds ? `${Math.floor(session.total_time_seconds / 60)}m ${session.total_time_seconds % 60}s` : '—'}
                          </p>
                        </div>
                        <div className="text-center">
                          <p className="text-slate-400 dark:text-gray-500 font-semibold">Bonus</p>
                          <p className="text-emerald-600 dark:text-emerald-400 font-bold">+{session.tool_bonus}</p>
                        </div>
                      </div>
                      {session.answers.length > 0 && (
                        <div className="space-y-1">
                          {session.answers.map((a, i) => (
                            <div key={i} className="flex items-center gap-2 text-xs py-1 border-b border-dashed border-slate-100 dark:border-white/5 last:border-b-0">
                              {a.is_correct ? (
                                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 dark:text-emerald-400 flex-shrink-0" />
                              ) : (
                                <XCircle className="w-3.5 h-3.5 text-red-500 dark:text-red-400 flex-shrink-0" />
                              )}
                              <span className="text-slate-400 dark:text-gray-500 font-semibold">{a.comprehension_level}</span>
                              <span className="text-slate-700 dark:text-gray-300 font-medium">
                                {a.selected_answer}{a.is_correct ? '' : ` (→${a.correct_answer})`}
                              </span>
                              <span className={`ml-auto font-bold ${a.is_correct ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-500 dark:text-red-400'}`}>
                                {a.is_correct ? `+${a.points_earned}` : `-${a.penalty_applied}`}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right column */}
        <div className="space-y-6">
          {/* Achievements */}
          <div className="glass-card p-6">
            <h3 className="text-sm font-semibold text-slate-700 dark:text-gray-300 mb-3 flex items-center gap-2">
              <Award className="w-4 h-4 text-primary-500 dark:text-primary-400" />
              Logros ({achievements.length}/10)
            </h3>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(ALL_ACHIEVEMENTS).map(([id, name]) => {
                const unlocked = unlockedAchievementIds.includes(id);
                return (
                  <div
                    key={id}
                    className={`px-3 py-2 rounded-lg text-xs font-semibold border ${
                      unlocked
                        ? 'bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-100 dark:border-emerald-500/20 shadow-sm shadow-emerald-500/5'
                        : 'bg-slate-100 dark:bg-white/5 text-slate-400 dark:text-gray-500 border-slate-200/60 dark:border-white/5'
                    }`}
                  >
                    {unlocked ? '✅' : '🔒'} {name}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Tools Usage */}
          <div className="glass-card p-6">
            <h3 className="text-sm font-semibold text-slate-700 dark:text-gray-300 mb-3 flex items-center gap-2">
              <Highlighter className="w-4 h-4 text-primary-500 dark:text-primary-400" />
              Uso de Herramientas
            </h3>
            {tool_stats.length === 0 ? (
              <p className="text-sm text-slate-400 dark:text-gray-500">Sin datos de herramientas</p>
            ) : (
              <div className="space-y-3">
                {tool_stats.map((tool) => {
                  const Icon = TOOL_ICONS[tool.tool_name] || PenTool;
                  return (
                    <div key={tool.tool_name} className="flex items-center gap-3">
                      <Icon className="w-4 h-4 text-slate-400 dark:text-gray-500" />
                      <span className="text-sm font-semibold text-slate-700 dark:text-gray-300 w-20">{TOOL_LABELS[tool.tool_name] || tool.tool_name}</span>
                      <div className="flex-1 bg-slate-100 dark:bg-white/5 rounded-full h-2">
                        <div
                          className="h-2 rounded-full bg-primary-600 dark:bg-primary-500 transition-all duration-500"
                          style={{ width: `${tool.usage_rate}%` }}
                        />
                      </div>
                      <span className="text-xs font-semibold text-slate-500 dark:text-gray-400 w-12 text-right">{tool.usage_rate}%</span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Notes */}
          <div className="glass-card p-6">
            <h3 className="text-sm font-semibold text-slate-700 dark:text-gray-300 mb-3 flex items-center gap-2">
              <StickyNote className="w-4 h-4 text-primary-500 dark:text-primary-400" />
              Apuntes & Notas ({notes.length})
            </h3>

            {/* Selector de Tipologías */}
            <div className="flex flex-wrap gap-1.5 mb-4">
              {DIFFICULTY_ORDER.map((typology) => {
                const colors = DIFFICULTY_COLORS[typology];
                const isSelected = selectedNotesTypology === typology;
                const readingsForTypo = presentedReadingsByTypology[typology] || [];

                return (
                  <button
                    key={typology}
                    onClick={() => {
                      setSelectedNotesTypology(typology);
                      setSelectedReadingId(null);
                    }}
                    className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-bold border transition-all duration-200 ${
                      isSelected
                        ? `${colors.bg} ${colors.text} ${colors.border} ring-1 ring-primary-500/10`
                        : 'bg-transparent border-slate-200/60 dark:border-white/5 text-slate-500 dark:text-gray-400 hover:bg-slate-50 dark:hover:bg-white/5'
                    }`}
                  >
                    <span>{typology}</span>
                    <span className={`px-1.5 py-0.5 rounded-full text-[9px] font-extrabold ${
                      isSelected
                        ? 'bg-white/60 dark:bg-white/10'
                        : 'bg-slate-100 dark:bg-white/5 text-slate-400 dark:text-gray-500'
                    }`}>
                      {readingsForTypo.length}
                    </span>
                  </button>
                );
              })}
            </div>

            {/* Listado de Lecturas Presentadas */}
            {presentedReadingsByTypology[selectedNotesTypology]?.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-center bg-slate-50/50 dark:bg-white/[0.01] border border-dashed border-slate-200 dark:border-white/5 rounded-xl">
                <BookOpen className="w-8 h-8 text-slate-300 dark:text-gray-600 mb-2" />
                <p className="text-xs font-bold text-slate-500 dark:text-gray-400">Sin lecturas presentadas</p>
                <p className="text-[10px] text-slate-400 dark:text-gray-500 max-w-[200px] mt-1 leading-normal">
                  El estudiante aún no ha abierto ninguna lectura de la tipología <span className="font-semibold text-slate-500 dark:text-gray-400">{selectedNotesTypology}</span>.
                </p>
              </div>
            ) : (
              <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
                {presentedReadingsByTypology[selectedNotesTypology].map((reading) => {
                  const isExpanded = selectedReadingId === reading.id;
                  const readingNotes = notes.filter((n) => n.reading_id === reading.id || n.reading_title === reading.title);

                  return (
                    <div
                      key={reading.id}
                      className={`border rounded-xl overflow-hidden transition-all duration-200 ${
                        isExpanded
                          ? 'bg-slate-50/40 dark:bg-white/[0.01] border-slate-300 dark:border-white/10 shadow-sm'
                          : 'bg-white dark:bg-transparent border-slate-200/60 dark:border-white/5 hover:border-slate-300 dark:hover:border-white/10'
                      }`}
                    >
                      <button
                        onClick={() => setSelectedReadingId(isExpanded ? null : reading.id)}
                        className="w-full p-2.5 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-white/5 transition-colors"
                      >
                        <div className="flex items-center gap-2 text-left min-w-0">
                          <BookOpen className={`w-4 h-4 flex-shrink-0 ${isExpanded ? 'text-primary-500' : 'text-slate-400 dark:text-gray-500'}`} />
                          <span className="text-xs font-semibold text-slate-700 dark:text-gray-200 truncate max-w-[150px] sm:max-w-[180px]">
                            {reading.title}
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5 ml-2 flex-shrink-0">
                          <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold ${
                            readingNotes.length > 0
                              ? 'bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-100 dark:border-emerald-500/20'
                              : 'bg-slate-100 dark:bg-white/5 text-slate-400 dark:text-gray-500'
                          }`}>
                            {readingNotes.length === 0 ? 'Sin notas' : `${readingNotes.length} ${readingNotes.length === 1 ? 'nota' : 'notas'}`}
                          </span>
                          {isExpanded ? (
                            <ChevronUp className="w-3.5 h-3.5 text-slate-400 dark:text-gray-500" />
                          ) : (
                            <ChevronDown className="w-3.5 h-3.5 text-slate-400 dark:text-gray-500" />
                          )}
                        </div>
                      </button>

                      {isExpanded && (
                        <div className="px-2.5 pb-2.5 pt-1 border-t border-slate-200/50 dark:border-white/5 bg-slate-50/20 dark:bg-transparent space-y-2 animate-slide-up">
                          {readingNotes.length === 0 ? (
                            <div className="p-2.5 bg-amber-500/[0.01] rounded-lg border border-dashed border-amber-200/30 dark:border-amber-500/10 text-center py-3">
                              <p className="text-[10px] font-bold text-amber-600/80 dark:text-amber-400/80">
                                No hay apuntes o notas tomadas para esta lectura.
                              </p>
                            </div>
                          ) : (
                            readingNotes.map((note) => (
                              <div key={note.id} className="p-2.5 bg-white dark:bg-white/5 rounded-lg border border-slate-100 dark:border-white/5 shadow-sm">
                                <div className="flex items-center justify-between gap-2 mb-1.5">
                                  <span className="px-1.5 py-0.5 rounded text-[8px] font-extrabold bg-primary-50 dark:bg-primary-500/10 text-primary-600 dark:text-primary-400 border border-primary-100 dark:border-primary-500/20">
                                    {note.note_type}
                                  </span>
                                  <span className="text-[9px] text-slate-400 dark:text-gray-500 font-semibold">
                                    {note.created_at ? new Date(note.created_at).toLocaleDateString('es-EC', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : ''}
                                  </span>
                                </div>
                                <p className="text-xs text-slate-600 dark:text-gray-300 leading-relaxed font-semibold whitespace-pre-wrap">
                                  {note.note_content}
                                </p>
                              </div>
                            ))
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Reset All Button */}
      <div className="glass-card p-6 border-red-200/60 dark:border-red-500/10 bg-red-500/[0.01] dark:bg-transparent">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-sm font-bold text-red-500 dark:text-red-400 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" />
              Zona de Peligro
            </h3>
            <p className="text-xs text-slate-500 dark:text-gray-500 mt-1">
              Reiniciar todo borra sesiones, logros, notas y progreso del jugador
            </p>
          </div>
          <button
            onClick={() => setResetModal({ type: 'all' })}
            className="btn-danger text-sm"
          >
            <RotateCcw className="w-4 h-4 mr-1 inline animate-reverse-spin" />
            Reiniciar Todo
          </button>
        </div>
      </div>

      {/* Reset Modal */}
      {resetModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in">
          <div className="glass-card p-6 max-w-md w-full mx-4 bg-white dark:bg-surface-800 border border-slate-200 dark:border-white/10 shadow-2xl animate-slide-up">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-red-500/20 flex items-center justify-center">
                <AlertTriangle className="w-5 h-5 text-red-500 dark:text-red-400" />
              </div>
              <div>
                <h3 className="font-bold text-slate-800 dark:text-white">
                  {resetModal.type === 'typology'
                    ? `Reiniciar desde ${resetModal.typology}`
                    : 'Reiniciar todo el progreso'}
                </h3>
                <p className="text-xs text-slate-500 dark:text-gray-400">Esta acción no se puede deshacer</p>
              </div>
            </div>

            {resetModal.type === 'typology' && (
              <div className="bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/20 rounded-xl p-3 mb-4 text-xs text-amber-700 dark:text-amber-400">
                <strong>Cascada:</strong> Se reiniciarán {resetModal.typology} y todas las tipologías superiores:
                <span className="font-bold ml-1">
                  {DIFFICULTY_ORDER.slice(DIFFICULTY_ORDER.indexOf(resetModal.typology)).join(' → ')}
                </span>
              </div>
            )}

            <p className="text-sm font-semibold text-slate-600 dark:text-gray-300 mb-3">
              Escribe el email del jugador para confirmar:
            </p>
            <input
              type="email"
              value={confirmEmail}
              onChange={(e) => setConfirmEmail(e.target.value)}
              placeholder={user.email}
              className="input-field mb-3"
            />

            {resetError && (
              <p className="text-sm text-red-400 mb-3">{resetError}</p>
            )}

            <div className="flex gap-3">
              <button
                onClick={() => { setResetModal(null); setConfirmEmail(''); setResetError(''); }}
                className="btn-ghost flex-1"
              >
                Cancelar
              </button>
              <button
                onClick={handleReset}
                disabled={resetLoading || confirmEmail !== user.email}
                className="btn-danger flex-1 disabled:opacity-40"
              >
                {resetLoading ? 'Procesando...' : 'Confirmar Reinicio'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
