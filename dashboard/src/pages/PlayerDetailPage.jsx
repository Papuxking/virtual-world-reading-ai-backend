import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  getPlayerDetail, resetTypology, resetAllProgress,
  getPlayerSlots, createPlayerSlot, activatePlayerSlot,
  resetPlayerPassword, getAchievementsCatalog,
  uploadMedalImage, deleteMedalImage
} from '../services/api';
import SessionList from '../components/SessionList';
import { TYPOLOGY_ORDER } from '../constants/typologies';
import {
  ArrowLeft, Star, Trophy, BookOpen, Target, CheckCircle2,
  Lock, Unlock, RotateCcw, AlertTriangle, StickyNote,
  Highlighter, Underline, PenTool, ChevronDown, ChevronUp, Award,
  Key, Plus, Copy, Check, Trash2, ShieldAlert, Sparkles, Upload, X,
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE ?? '';

// Grupo de las lecturas de la zona de práctica en el panel de notas.
const PRACTICE_GROUP = 'Práctica';
const NOTES_GROUPS = [...TYPOLOGY_ORDER, PRACTICE_GROUP];

const DIFFICULTY_COLORS = {
  Narrativo: { bg: 'bg-indigo-50 dark:bg-indigo-500/10', text: 'text-indigo-600 dark:text-indigo-400', border: 'border-indigo-100 dark:border-indigo-500/20', bar: 'bg-indigo-500' },
  Descriptivo: { bg: 'bg-violet-50 dark:bg-violet-500/10', text: 'text-violet-600 dark:text-violet-400', border: 'border-violet-100 dark:border-violet-500/20', bar: 'bg-violet-500' },
  Argumentativo: { bg: 'bg-purple-50 dark:bg-purple-500/10', text: 'text-purple-600 dark:text-purple-400', border: 'border-purple-100 dark:border-purple-500/20', bar: 'bg-purple-500' },
  Expositivo: { bg: 'bg-pink-50 dark:bg-pink-500/10', text: 'text-pink-600 dark:text-pink-400', border: 'border-pink-100 dark:border-pink-500/20', bar: 'bg-pink-500' },
  [PRACTICE_GROUP]: { bg: 'bg-emerald-50 dark:bg-emerald-500/10', text: 'text-emerald-600 dark:text-emerald-400', border: 'border-emerald-100 dark:border-emerald-500/20', bar: 'bg-emerald-500' },
};

const TIER_COLORS = {
  bronce: {
    ring: 'ring-amber-500/30',
    border: 'border-amber-200 dark:border-amber-500/20',
    bg: 'bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-950/20 dark:to-orange-950/20',
    text: 'text-amber-700 dark:text-amber-400',
    badge: 'bg-amber-100 dark:bg-amber-500/20 text-amber-800 dark:text-amber-400',
    medalBg: 'bg-[#CD7F32]'
  },
  plata: {
    ring: 'ring-slate-400/30',
    border: 'border-slate-200 dark:border-white/5',
    bg: 'bg-gradient-to-br from-slate-50 to-blue-50/20 dark:from-slate-900/10 dark:to-blue-900/5',
    text: 'text-slate-600 dark:text-slate-400',
    badge: 'bg-slate-100 dark:bg-white/10 text-slate-800 dark:text-slate-400',
    medalBg: 'bg-[#C0C0C0]'
  },
  oro: {
    ring: 'ring-yellow-500/30',
    border: 'border-yellow-200 dark:border-yellow-500/20',
    bg: 'bg-gradient-to-br from-yellow-50 to-amber-50/30 dark:from-yellow-950/10 dark:to-amber-950/5',
    text: 'text-yellow-700 dark:text-yellow-500',
    badge: 'bg-yellow-100 dark:bg-yellow-500/20 text-yellow-800 dark:text-yellow-400',
    medalBg: 'bg-[#FFD700]'
  },
  platino: {
    ring: 'ring-cyan-400/40',
    border: 'border-cyan-200 dark:border-cyan-500/20',
    bg: 'bg-gradient-to-br from-cyan-50 to-teal-50/20 dark:from-cyan-950/10 dark:to-teal-950/5',
    text: 'text-cyan-600 dark:text-cyan-400',
    badge: 'bg-cyan-100 dark:bg-cyan-500/20 text-cyan-800 dark:text-cyan-400',
    medalBg: 'bg-[#E5E4E2]'
  }
};

const TOOL_ICONS = { highlight: Highlighter, underline: Underline, notes: PenTool };
const TOOL_LABELS = { highlight: 'Resaltar', underline: 'Subrayar', notes: 'Notas' };

export default function PlayerDetailPage() {
  const { playerId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Slots
  const [slots, setSlots] = useState([]);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [showCreateSlot, setShowCreateSlot] = useState(false);
  const [newSlotLabel, setNewSlotLabel] = useState('');
  const [confirmSlotModal, setConfirmSlotModal] = useState(null); // { slotNumber, slotLabel }

  // Password reset
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [tempPassword, setTempPassword] = useState('');
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  // Catálogo de logros
  const [catalog, setCatalog] = useState([]);
  const [catalogLoading, setCatalogLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('all');

  // Danger zone resets
  const [resetModal, setResetModal] = useState(null); // { type: 'typology' | 'all', typology?: string }
  const [confirmEmail, setConfirmEmail] = useState('');
  const [resetLoading, setResetLoading] = useState(false);
  const [resetError, setResetError] = useState('');
  const [agreed, setAgreed] = useState(false);
  const [countdown, setCountdown] = useState(10);
  const [canDelete, setCanDelete] = useState(false);

  // Notes view filtering
  const [selectedNotesTypology, setSelectedNotesTypology] = useState('Narrativo');
  const [selectedReadingId, setSelectedReadingId] = useState(null);

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playerId]);

  useEffect(() => {
    let timer;
    if (resetModal && agreed) {
      setCountdown(10);
      setCanDelete(false);
      timer = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(timer);
            setCanDelete(true);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } else {
      setCountdown(10);
      setCanDelete(false);
    }
    return () => clearInterval(timer);
  }, [resetModal, agreed]);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const detail = await getPlayerDetail(playerId);
      setData(detail);

      const playerSlots = await getPlayerSlots(playerId);
      setSlots(playerSlots);

      const achCatalog = await getAchievementsCatalog();
      setCatalog(achCatalog);
    } catch (err) {
      console.error(err);
      setError(err.message || 'Error al cargar datos del jugador');
    } finally {
      setLoading(false);
      setCatalogLoading(false);
    }
  }

  async function handleCreateSlot(e) {
    e.preventDefault();
    if (!newSlotLabel.trim()) return;
    setSlotsLoading(true);
    try {
      await createPlayerSlot(playerId, newSlotLabel);
      setNewSlotLabel('');
      setShowCreateSlot(false);
      await loadData();
    } catch (err) {
      alert(err.message || 'Error al crear slot');
    } finally {
      setSlotsLoading(false);
    }
  }

  function handleActivateSlot(slotNumber) {
    const slot = slots.find((s) => s.slot_number === slotNumber);
    setConfirmSlotModal({ slotNumber, slotLabel: slot?.label || `Slot ${slotNumber}` });
  }

  async function confirmActivateSlot() {
    if (!confirmSlotModal) return;
    setSlotsLoading(true);
    try {
      await activatePlayerSlot(playerId, confirmSlotModal.slotNumber);
      setConfirmSlotModal(null);
      await loadData();
    } catch (err) {
      alert(err.message || 'Error al activar slot');
    } finally {
      setSlotsLoading(false);
    }
  }

  async function handleResetPassword() {
    if (!window.confirm('¿Deseas restablecer la contraseña de este jugador? Se generará una clave temporal.')) return;
    setPasswordLoading(true);
    try {
      const resp = await resetPlayerPassword(playerId);
      setTempPassword(resp.temp_password);
      setShowPasswordModal(true);
      await loadData();
    } catch (err) {
      alert(err.message || 'Error al restablecer contraseña');
    } finally {
      setPasswordLoading(false);
    }
  }

  function handleCopyPassword() {
    navigator.clipboard.writeText(tempPassword);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  async function handleUploadMedal(achievementId, file) {
    if (!file) return;
    try {
      await uploadMedalImage(achievementId, file);
      alert('Medalla de logro actualizada con éxito');
      await loadData();
    } catch (err) {
      alert(err.message || 'Error al subir la imagen de la medalla');
    }
  }

  async function handleDeleteMedal(achievementId) {
    if (!window.confirm('¿Deseas eliminar la medalla personalizada y volver al placeholder?')) return;
    try {
      await deleteMedalImage(achievementId);
      alert('Medalla restablecida al placeholder');
      await loadData();
    } catch (err) {
      alert(err.message || 'Error al restablecer medalla');
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
      setAgreed(false);
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

  const { user, total_score, active_slot_number, active_slot_label, typology_progress, achievements, sessions, practice_sessions, notes, tool_stats, level_stats, score_rules, game_over } = data;
  const unlockedAchievementIds = achievements.map((a) => a.achievement_id);

  // Filtrar catálogo de logros
  const filteredCatalog = catalog.filter((achievement) => {
    if (selectedCategory === 'all') return true;
    return achievement.category === selectedCategory;
  });

  // Lecturas que ha abierto el estudiante, agrupadas por tipología. Las de la
  // zona de práctica van en su propio grupo.
  const presentedReadingsByTypology = NOTES_GROUPS.reduce((acc, group) => {
    const isPractice = group === PRACTICE_GROUP;
    const fromSessions = (isPractice ? practice_sessions : sessions.filter((s) => s.typology === group))
      .map((s) => ({ id: s.reading_id, title: s.reading_title }));

    const fromNotes = notes
      .filter((n) => (isPractice ? n.reading_is_practice : !n.reading_is_practice && n.reading_typology === group))
      .map((n) => ({ id: n.reading_id, title: n.reading_title }));

    const merged = [...fromSessions, ...fromNotes];
    const uniqueMap = new Map();
    merged.forEach((item) => {
      if (item.id) {
        uniqueMap.set(item.id, item.title);
      } else if (item.title) {
        uniqueMap.set(item.title, item.title);
      }
    });

    acc[group] = Array.from(uniqueMap.entries()).map(([id, title]) => ({
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
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-2xl font-bold text-slate-800 dark:text-white">{user.display_name}</h1>
                {user.must_change_password && (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-amber-100 dark:bg-amber-500/20 text-amber-800 dark:text-amber-400 border border-amber-200 dark:border-amber-500/35 animate-pulse">
                    <Key className="w-3 h-3" />
                    Pendiente de cambio
                  </span>
                )}
                {game_over && (
                  <span className="badge-danger" title="Agotó los intentos de una tipología sin aprobarla">
                    Juego terminado
                  </span>
                )}
              </div>
              <div className="flex items-center gap-3 mt-1 flex-wrap">
                <p className="text-sm text-slate-500 dark:text-gray-400">{user.email}</p>
                <button
                  onClick={handleResetPassword}
                  disabled={passwordLoading}
                  className="inline-flex items-center gap-1 text-xs font-bold text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 transition-colors bg-primary-50 dark:bg-primary-500/10 px-2 py-0.5 rounded border border-primary-200 dark:border-primary-500/20"
                >
                  <Key className="w-3.5 h-3.5" />
                  {passwordLoading ? 'Procesando...' : 'Restablecer contraseña'}
                </button>
              </div>
            </div>
          </div>
        </div>
        <div className="text-left sm:text-right px-2 sm:px-0">
          <p className="text-xs text-slate-400 dark:text-gray-400 uppercase font-semibold">Registrado</p>
          <p className="text-sm font-semibold text-slate-700 dark:text-gray-300">{new Date(user.created_at).toLocaleDateString('es-EC')}</p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="stat-card">
          <Star className="w-5 h-5 text-amber-500 mb-2" />
          <p className="text-2xl font-extrabold text-slate-800 dark:text-white">{total_score.toLocaleString()}</p>
          <p className="text-xs font-semibold text-slate-400 dark:text-gray-400">Puntos totales ({active_slot_label})</p>
        </div>
        <div className="stat-card">
          <BookOpen className="w-5 h-5 text-violet-500 mb-2" />
          <p className="text-2xl font-extrabold text-slate-800 dark:text-white">{sessions.length}</p>
          <p className="text-xs font-semibold text-slate-400 dark:text-gray-400">Sesiones ({active_slot_label})</p>
        </div>
        <div className="stat-card">
          <Award className="w-5 h-5 text-emerald-500 mb-2" />
          <p className="text-2xl font-extrabold text-slate-800 dark:text-white">{achievements.length}/10</p>
          <p className="text-xs font-semibold text-slate-400 dark:text-gray-400">Logros ({active_slot_label})</p>
        </div>
        <div className="stat-card">
          <Target className="w-5 h-5 text-sky-500 mb-2" />
          <p className="text-2xl font-extrabold text-slate-800 dark:text-white">
            {level_stats.length > 0
              ? `${Math.round(level_stats.reduce((s, l) => s + l.correct, 0) / Math.max(1, level_stats.reduce((s, l) => s + l.total, 0)) * 100)}%`
              : '—'}
          </p>
          <p className="text-xs font-semibold text-slate-400 dark:text-gray-400">Precisión ({active_slot_label})</p>
        </div>
      </div>

      {/* Slots Section */}
      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-slate-800 dark:text-white flex items-center gap-2">
            <RotateCcw className="w-5 h-5 text-primary-500 dark:text-primary-400 animate-spin-slow" />
            Sesiones del Jugador (Slots de Progreso)
          </h3>
          {slots.length < 4 && (
            <button
              onClick={() => setShowCreateSlot(true)}
              className="btn-primary text-xs flex items-center gap-1 py-1.5 px-3"
            >
              <Plus className="w-3.5 h-3.5" />
              Nuevo Slot
            </button>
          )}
        </div>

        {slotsLoading ? (
          <div className="py-8 text-center text-xs text-slate-400">Cargando slots de juego...</div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
            {slots.map((slot) => {
              const isActive = slot.is_active;
              return (
                <div
                  key={slot.id}
                  onClick={() => !isActive && handleActivateSlot(slot.slot_number)}
                  className={`p-4 rounded-xl border transition-all duration-200 flex flex-col justify-between ${
                    isActive
                      ? 'bg-emerald-500/[0.03] dark:bg-emerald-500/[0.02] border-emerald-500 dark:border-emerald-500/35 ring-2 ring-emerald-500/10 shadow-md cursor-default'
                      : 'bg-white dark:bg-transparent border-slate-200/60 dark:border-white/5 hover:border-slate-300 dark:hover:border-white/10 shadow-sm cursor-pointer hover:shadow'
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold text-slate-400 dark:text-gray-400">Slot {slot.slot_number}</span>
                      {isActive ? (
                        <span className="px-2 py-0.5 rounded-full text-[9px] font-extrabold bg-emerald-100 dark:bg-emerald-500/20 text-emerald-800 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/30">
                          ✅ Activo
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-slate-100 dark:bg-white/5 text-slate-500 dark:text-gray-400">
                          Inactivo
                        </span>
                      )}
                    </div>
                    <h4 className="font-bold text-slate-800 dark:text-white truncate mb-2">{slot.label}</h4>
                    <div className="space-y-1 text-xs text-slate-500 dark:text-gray-400 font-semibold">
                      <p>🏆 Puntos: <span className="font-extrabold text-slate-700 dark:text-gray-300">{slot.total_score}</span></p>
                      <p>📖 Sesiones: <span className="font-extrabold text-slate-700 dark:text-gray-300">{slot.total_sessions}</span></p>
                      <p>🏅 Logros: <span className="font-extrabold text-slate-700 dark:text-gray-300">{slot.total_achievements}</span></p>
                    </div>
                  </div>
                  <div className="mt-3 pt-3 border-t border-slate-100 dark:border-white/5 flex items-center justify-between">
                    <span className="text-[10px] text-slate-400 dark:text-gray-400 font-semibold">
                      {slot.created_at ? new Date(slot.created_at).toLocaleDateString('es-EC') : '—'}
                    </span>
                    {!isActive && (
                      <span className="text-[10px] font-bold text-primary-500 dark:text-primary-400 hover:underline">
                        Activar →
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Typology Progress */}
      <div className="glass-card p-6">
        <h3 className="text-lg font-semibold text-slate-800 dark:text-white mb-4 flex items-center gap-2">
          <Trophy className="w-5 h-5 text-primary-500 dark:text-primary-400" />
          Progreso por Tipología ({active_slot_label})
        </h3>
        <div className="space-y-4">
          {TYPOLOGY_ORDER.map((typology, index) => {
            const progress = typology_progress.find((tp) => tp.typology === typology);
            const colors = DIFFICULTY_COLORS[typology];
            const score = progress?.best_score || 0;
            // El máximo y los umbrales vienen de la API (game_rules.py). Antes el
            // máximo estaba fijado aquí a 350, por encima de los 300 posibles.
            const maxScore = score_rules.max_session_score;
            const next = TYPOLOGY_ORDER[index + 1];
            const threshold = next ? score_rules.unlock_thresholds[next] : null;
            const pct = Math.min(100, (score / maxScore) * 100);
            // Se aprueba con el umbral que abre la siguiente; la última, con el
            // suyo (game_rules.pass_threshold). Sin aprobar y sin intentos, agotada.
            const passThreshold = next ? score_rules.unlock_thresholds[next] : score_rules.unlock_thresholds[typology];
            const maxAttempts = score_rules.max_attempts;
            const attempts = progress?.attempts_used || 0;
            const agotada = score < passThreshold && attempts >= maxAttempts;

            return (
              <div key={typology} className={`p-4 rounded-xl border ${colors.border} ${colors.bg}`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {progress?.is_unlocked ? (
                      <Unlock className={`w-4 h-4 ${colors.text}`} />
                    ) : (
                      <Lock className="w-4 h-4 text-slate-400 dark:text-gray-400" />
                    )}
                    <span className={`font-semibold ${progress?.is_unlocked ? colors.text : 'text-slate-400 dark:text-gray-400'}`}>
                      {typology}
                    </span>
                    {progress?.is_unlocked && (
                      <span className="badge-success text-[10px]">Desbloqueado</span>
                    )}
                    {agotada && (
                      <span className="badge-danger text-[10px]">Sin intentos</span>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-bold text-slate-800 dark:text-white">{score} pts</span>
                    <span className="text-xs text-slate-500 dark:text-gray-400">{progress?.total_sessions || 0} sesiones</span>
                    <span className={`text-xs font-semibold ${agotada ? 'text-red-600 dark:text-red-300' : 'text-slate-500 dark:text-gray-400'}`}>
                      Intentos: {attempts}/{maxAttempts}
                    </span>
                    {progress?.is_unlocked && progress?.total_sessions > 0 && (
                      <button
                        onClick={() => setResetModal({ type: 'typology', typology })}
                        className="text-xs text-slate-400 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400 transition-colors flex items-center gap-1 font-semibold"
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
                  <span className="text-[10px] text-slate-400 dark:text-gray-400 font-semibold">0</span>
                  {threshold !== null && (
                    <span className="text-[10px] text-slate-400 dark:text-gray-400 font-semibold">Umbral: {threshold}</span>
                  )}
                  <span className="text-[10px] text-slate-400 dark:text-gray-400 font-semibold">{maxScore}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Sessions, Achievements, Tools, Notes */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left column */}
        <div className="space-y-6">
          {/* Sessions History */}
          <div className="glass-card p-6">
            <h3 className="text-lg font-semibold text-slate-800 dark:text-white mb-4 flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-primary-500 dark:text-primary-400" />
              Historial de Sesiones ({active_slot_label})
            </h3>
            <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
              <SessionList sessions={sessions} emptyText="Sin sesiones registradas" />
            </div>
          </div>

          {/* Practice */}
          <div className="glass-card p-6">
            <h3 className="text-lg font-semibold text-slate-800 dark:text-white mb-1 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-emerald-500 dark:text-emerald-400" />
              Práctica ({active_slot_label})
            </h3>
            <p className="text-xs text-slate-400 dark:text-gray-400 mb-4">
              Lecturas de la zona de práctica. No cuentan para el puntaje, los desbloqueos, los logros ni las métricas.
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-4">
              {TYPOLOGY_ORDER.map((typology) => {
                const colors = DIFFICULTY_COLORS[typology];
                const count = practice_sessions.filter((s) => s.typology === typology).length;
                return (
                  <div key={typology} className={`p-2 rounded-lg border text-center ${colors.border} ${colors.bg}`}>
                    <p className={`text-lg font-extrabold ${colors.text}`}>{count}</p>
                    <p className="text-[10px] font-semibold text-slate-500 dark:text-gray-400">{typology}</p>
                  </div>
                );
              })}
            </div>
            <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
              <SessionList sessions={practice_sessions} emptyText="Todavía no ha usado la zona de práctica" />
            </div>
          </div>
        </div>

        {/* Right column */}
        <div className="space-y-6">
          {/* Achievements (Logros del Jugador) */}
          <div className="glass-card p-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
              <div>
                <h3 className="text-lg font-bold text-slate-800 dark:text-white flex items-center gap-2">
                  <Trophy className="w-5 h-5 text-amber-500 dark:text-amber-400" />
                  Logros del Jugador ({active_slot_label})
                </h3>
                <p className="text-xs text-slate-500 dark:text-gray-400 mt-0.5">
                  Completado: <span className="font-extrabold text-amber-500">{achievements.length}/10</span> logros
                </p>
              </div>
            </div>

            {/* Category Toggles */}
            <div className="flex flex-wrap gap-1 mb-4">
              {['all', 'progreso', 'exploración', 'maestría', 'superación'].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`px-2.5 py-1 rounded-lg text-[10px] font-extrabold uppercase tracking-wide border transition-all ${
                    selectedCategory === cat
                      ? 'bg-amber-50 dark:bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-200 dark:border-amber-500/25 ring-1 ring-amber-500/10'
                      : 'bg-transparent border-slate-200/60 dark:border-white/5 text-slate-500 dark:text-gray-400 hover:bg-slate-50 dark:hover:bg-white/5'
                  }`}
                >
                  {cat === 'all' ? 'Todos' : cat}
                </button>
              ))}
            </div>

            {catalogLoading ? (
              <div className="py-8 text-center text-xs text-slate-400 animate-pulse">Cargando logros...</div>
            ) : (
              <div className="space-y-3 max-h-[300px] overflow-y-auto pr-1">
                {filteredCatalog.map((achievement) => {
                  const unlocked = unlockedAchievementIds.includes(achievement.id);
                  const unlockRecord = achievements.find((a) => a.achievement_id === achievement.id);
                  const tierStyles = TIER_COLORS[achievement.medal_tier] || TIER_COLORS.bronce;

                  return (
                    <div
                      key={achievement.id}
                      className={`p-3 rounded-xl border transition-all flex items-center justify-between gap-4 ${
                        unlocked
                          ? 'bg-slate-50 dark:bg-white/[0.02] border-emerald-100 dark:border-emerald-500/20'
                          : 'bg-slate-100/[0.2] dark:bg-white/[0.005] border-slate-200/60 dark:border-white/5 opacity-60'
                      }`}
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <span className="text-xl flex-shrink-0">{achievement.icon}</span>
                        <div className="min-w-0">
                          <h4 className={`text-xs font-bold truncate ${unlocked ? 'text-slate-800 dark:text-white' : 'text-slate-500 dark:text-gray-400'}`}>
                            {achievement.name}
                          </h4>
                          <p className="text-[10px] text-slate-400 dark:text-gray-400 font-semibold line-clamp-1">
                            {achievement.description}
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex-shrink-0 text-right">
                        {unlocked ? (
                          <div className="flex flex-col items-end">
                            <span className="text-[9px] font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                              <CheckCircle2 className="w-3 h-3" /> Desbloqueado
                            </span>
                            <span className="text-[8px] text-slate-400 dark:text-gray-400">
                              {unlockRecord?.unlocked_at ? new Date(unlockRecord.unlocked_at).toLocaleDateString('es-EC') : '—'}
                            </span>
                          </div>
                        ) : (
                          <span className="text-[9px] font-bold text-amber-600/80 dark:text-amber-400/80" title={achievement.how_to_unlock}>
                            Requisito: {achievement.how_to_unlock}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Medals (Medallas Coleccionadas) */}
          <div className="glass-card p-6">
            <div className="mb-4">
              <h3 className="text-lg font-bold text-slate-800 dark:text-white flex items-center gap-2">
                <Award className="w-5 h-5 text-primary-500 dark:text-primary-400" />
                Medallas Coleccionadas ({active_slot_label})
              </h3>
              <p className="text-xs text-slate-500 dark:text-gray-400 mt-0.5">
                Coleccionadas: <span className="font-extrabold text-primary-500 dark:text-primary-400">{achievements.length}/10</span> cromos/medallas
              </p>
            </div>

            {catalogLoading ? (
              <div className="py-8 text-center text-xs text-slate-400 animate-pulse">Cargando medallas...</div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 max-h-[350px] overflow-y-auto pr-1">
                {catalog.map((achievement) => {
                  const unlocked = unlockedAchievementIds.includes(achievement.id);
                  const tierStyles = TIER_COLORS[achievement.medal_tier] || TIER_COLORS.bronce;

                  return (
                    <div
                      key={achievement.id}
                      className={`p-3 rounded-xl border transition-all flex flex-col items-center justify-between text-center relative group ${
                        unlocked
                          ? `${tierStyles.bg} ${tierStyles.border} shadow-sm shadow-emerald-500/5`
                          : 'bg-slate-100/[0.4] dark:bg-white/[0.01] border-slate-200/60 dark:border-white/5 opacity-40 grayscale'
                      }`}
                      title={unlocked ? `${achievement.medal_name} (${achievement.medal_tier})` : 'Medalla Bloqueada'}
                    >
                      {/* Medalla Image or Fallback */}
                      <div className="relative w-16 h-16 mb-2 flex items-center justify-center">
                        {achievement.medal_image_path ? (
                          <div className="w-16 h-16 rounded-xl overflow-hidden border border-slate-200 dark:border-white/10 shadow-sm relative bg-white dark:bg-slate-900 flex items-center justify-center">
                            <img
                              src={`${API_BASE}${achievement.medal_image_path}`}
                              alt={achievement.medal_name}
                              className="w-full h-full object-contain"
                            />
                            {/* Delete custom image */}
                            <button
                              onClick={() => handleDeleteMedal(achievement.id)}
                              className="absolute -top-1 -right-1 p-0.5 bg-red-100 hover:bg-red-200 dark:bg-red-950/80 dark:hover:bg-red-900 rounded-full border border-red-300 dark:border-red-500/40 text-red-600 dark:text-red-400 shadow-sm transition-opacity opacity-0 group-hover:opacity-100"
                              title="Borrar imagen personalizada"
                            >
                              <X className="w-2.5 h-2.5" />
                            </button>
                          </div>
                        ) : (
                          <div className={`w-16 h-16 rounded-xl flex flex-col items-center justify-center border border-dashed shadow-sm relative overflow-hidden ${
                            unlocked ? 'border-white/60' : 'border-slate-300 dark:border-gray-700 bg-slate-100 dark:bg-white/5'
                          }`} style={unlocked ? { backgroundColor: tierStyles.medalBg.replace('bg-[', '').replace(']', '') } : undefined}>
                            <span className="text-2xl filter drop-shadow-sm">{unlocked ? achievement.icon : '?'}</span>
                            <span className={`text-[6px] font-extrabold uppercase tracking-wider absolute bottom-0.5 ${unlocked ? 'text-slate-800' : 'text-slate-400 dark:text-gray-400'}`}>
                              {achievement.medal_tier}
                            </span>
                            {/* Admin Upload file input */}
                            <label className="absolute -bottom-1 -right-1 p-0.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-white/10 rounded-full shadow-sm cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 opacity-0 group-hover:opacity-100" title="Subir medalla manual (PNG 256x256)">
                              <Upload className="w-2.5 h-2.5" />
                              <input
                                type="file"
                                accept=".png"
                                className="hidden"
                                onChange={(e) => handleUploadMedal(achievement.id, e.target.files[0])}
                              />
                            </label>
                          </div>
                        )}
                      </div>

                      {/* Medal Text */}
                      <div className="leading-tight">
                        <h4 className="text-[10px] font-extrabold text-slate-700 dark:text-gray-200 truncate max-w-[90px]">
                          {unlocked ? achievement.medal_name : '???'}
                        </h4>
                        <span className={`px-1.5 py-0.2 rounded text-[6px] font-extrabold uppercase tracking-wider block mt-1 ${tierStyles.badge}`}>
                          {achievement.medal_tier}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Tools Usage */}
          <div className="glass-card p-6">
            <h3 className="text-sm font-semibold text-slate-700 dark:text-gray-300 mb-3 flex items-center gap-2">
              <Highlighter className="w-4 h-4 text-primary-500 dark:text-primary-400" />
              Uso de Herramientas ({active_slot_label})
            </h3>
            {tool_stats.length === 0 ? (
              <p className="text-sm text-slate-400 dark:text-gray-400">Sin datos de herramientas</p>
            ) : (
              <div className="space-y-3">
                {tool_stats.map((tool) => {
                  const Icon = TOOL_ICONS[tool.tool_name] || PenTool;
                  return (
                    <div key={tool.tool_name} className="flex items-center gap-3">
                      <Icon className="w-4 h-4 text-slate-400 dark:text-gray-400" />
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
              Apuntes & Notas ({notes.length} en {active_slot_label})
            </h3>

            {/* Selector de Tipologías */}
            <div className="flex flex-wrap gap-1.5 mb-4">
              {NOTES_GROUPS.map((typology) => {
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
                        ? 'bg-white/60 dark:bg-white/10 dark:text-white'
                        : 'bg-slate-100 dark:bg-white/5 text-slate-400 dark:text-gray-400'
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
                <p className="text-[10px] text-slate-400 dark:text-gray-400 max-w-[200px] mt-1 leading-normal">
                  El estudiante aún no ha abierto ninguna lectura{' '}
                  {selectedNotesTypology === PRACTICE_GROUP ? (
                    'de práctica'
                  ) : (
                    <>de la tipología <span className="font-semibold text-slate-500 dark:text-gray-400">{selectedNotesTypology}</span></>
                  )}{' '}
                  en este slot.
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
                          <BookOpen className={`w-4 h-4 flex-shrink-0 ${isExpanded ? 'text-primary-500' : 'text-slate-400 dark:text-gray-400'}`} />
                          <span className="text-xs font-semibold text-slate-700 dark:text-gray-200 truncate max-w-[150px] sm:max-w-[180px]">
                            {reading.title}
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5 ml-2 flex-shrink-0">
                          <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold ${
                            readingNotes.length > 0
                              ? 'bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-100 dark:border-emerald-500/20'
                              : 'bg-slate-100 dark:bg-white/5 text-slate-400 dark:text-gray-400'
                          }`}>
                            {readingNotes.length === 0 ? 'Sin notas' : `${readingNotes.length} ${readingNotes.length === 1 ? 'nota' : 'notas'}`}
                          </span>
                          {isExpanded ? (
                            <ChevronUp className="w-3.5 h-3.5 text-slate-400 dark:text-gray-400" />
                          ) : (
                            <ChevronDown className="w-3.5 h-3.5 text-slate-400 dark:text-gray-400" />
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
                                  <span className="text-[9px] text-slate-400 dark:text-gray-400 font-semibold">
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

      {/* Danger Zone Section */}
      <div className="glass-card p-6 border-red-200/60 dark:border-red-500/10 bg-red-500/[0.01] dark:bg-transparent">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-sm font-bold text-red-500 dark:text-red-400 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 animate-bounce" />
              Zona de Peligro (Borrado Real de Datos)
            </h3>
            <p className="text-xs text-slate-500 dark:text-gray-400 mt-1">
              Las opciones de borrado definitivo se mantienen disponibles para el administrador. Se aplicarán exclusivamente al slot activo ({active_slot_label}).
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setResetModal({ type: 'all' })}
              className="btn-danger text-xs py-2 px-4 inline-flex items-center gap-1"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Reiniciar Todo el Progreso
            </button>
          </div>
        </div>
      </div>

      {/* New Slot Modal */}
      {showCreateSlot && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in">
          <form onSubmit={handleCreateSlot} className="glass-card p-6 max-w-sm w-full mx-4 bg-white dark:bg-surface-800 border border-slate-200 dark:border-white/10 shadow-2xl animate-slide-up">
            <h3 className="font-bold text-slate-800 dark:text-white text-lg mb-3">Crear Nuevo Slot de Sesión</h3>
            <p className="text-xs text-slate-500 dark:text-gray-400 mb-4 leading-relaxed">
              Crea una nueva sesión limpia para este jugador (máx. 4 slots). Su historial anterior se conservará intacto y podrá cambiarse en cualquier momento.
            </p>
            <input
              type="text"
              value={newSlotLabel}
              onChange={(e) => setNewSlotLabel(e.target.value)}
              placeholder="Ej: Intento 2, Práctica Final"
              className="input-field mb-4 text-sm"
              maxLength={30}
              required
              autoFocus
            />
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => { setShowCreateSlot(false); setNewSlotLabel(''); }}
                className="btn-ghost flex-1 text-xs"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={slotsLoading}
                className="btn-primary flex-1 text-xs"
              >
                {slotsLoading ? 'Creando...' : 'Crear Slot'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Password Reset Temp Pass Modal */}
      {showPasswordModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in">
          <div className="glass-card p-6 max-w-sm w-full mx-4 bg-white dark:bg-surface-800 border border-slate-200 dark:border-white/10 shadow-2xl animate-slide-up">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-primary-500/20 flex items-center justify-center">
                <Key className="w-5 h-5 text-primary-500 dark:text-primary-400 animate-pulse" />
              </div>
              <div>
                <h3 className="font-bold text-slate-800 dark:text-white">Contraseña Temporal Generada</h3>
                <p className="text-xs text-slate-500 dark:text-gray-400">Comunícala verbalmente al estudiante</p>
              </div>
            </div>
            <p className="text-xs text-slate-500 dark:text-gray-400 mb-4 leading-normal font-semibold">
              El estudiante iniciará sesión con esta clave y el juego le solicitará crear una nueva contraseña de inmediato.
            </p>
            <div className="flex items-center justify-between p-3 bg-slate-100 dark:bg-white/5 rounded-xl border border-slate-200 dark:border-white/10 mb-4 font-mono font-extrabold text-sm text-slate-700 dark:text-gray-300">
              <span>{tempPassword}</span>
              <button
                onClick={handleCopyPassword}
                className="p-1.5 hover:bg-slate-200 dark:hover:bg-white/10 rounded transition-colors text-slate-500 dark:text-gray-400"
                title="Copiar contraseña"
              >
                {copied ? <Check className="w-4 h-4 text-emerald-500" /> : <Copy className="w-4 h-4" />}
              </button>
            </div>
            <button
              onClick={() => setShowPasswordModal(false)}
              className="btn-primary w-full text-xs py-2"
            >
              Cerrar y Entendido
            </button>
          </div>
        </div>
      )}

      {/* Safety Danger Zone Reset Modal */}
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
                    ? `⚠️ Reiniciar desde ${resetModal.typology}`
                    : '⚠️ Reiniciar todo el progreso'}
                </h3>
                <p className="text-xs text-red-500 font-extrabold">Esta acción eliminará datos reales en la BD</p>
              </div>
            </div>

            <div className="bg-red-50 dark:bg-red-500/5 border border-red-200/50 dark:border-red-500/20 rounded-xl p-3.5 mb-4 text-xs text-red-700 dark:text-red-400 space-y-2 leading-relaxed">
              <p><strong>¿Qué datos se borrarán permanentemente del slot activo ({active_slot_label})?</strong></p>
              <ul className="list-disc list-inside space-y-1 font-semibold ml-1">
                {resetModal.type === 'typology' ? (
                  <>
                    <li>Sesiones y respuestas de {resetModal.typology} y superiores.</li>
                    <li>Notas y apuntes tomados en estas tipologías.</li>
                    <li>Progreso de tipologías afectadas volverá a 0 / se bloquearán.</li>
                  </>
                ) : (
                  <>
                    <li>TODAS las sesiones de juego y respuestas.</li>
                    <li>TODAS las notas y apuntes de todas las lecturas.</li>
                    <li>TODOS los logros desbloqueados en este slot.</li>
                    <li>Progreso completo vuelve a 0 (solo Narrativo desbloqueado).</li>
                  </>
                )}
              </ul>
              <div className="p-2 bg-white/70 dark:bg-slate-900/50 rounded border border-red-300/40 font-semibold text-center text-slate-600 dark:text-gray-300">
                💡 Considera usar <strong>"Nuevo Slot"</strong> como alternativa para no perder este historial.
              </div>
            </div>

            {resetModal.type === 'typology' && (
              <div className="bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/20 rounded-xl p-3 mb-4 text-xs text-amber-700 dark:text-amber-400">
                <strong>Cascada:</strong> Se reiniciarán {resetModal.typology} y todas las tipologías superiores:
                <span className="font-bold ml-1">
                  {TYPOLOGY_ORDER.slice(TYPOLOGY_ORDER.indexOf(resetModal.typology)).join(' → ')}
                </span>
              </div>
            )}

            {/* Paso 1: Checkbox */}
            <label className="flex items-start gap-2.5 p-3 bg-slate-50 dark:bg-white/[0.02] border border-slate-200/60 dark:border-white/5 rounded-xl cursor-pointer mb-4">
              <input
                type="checkbox"
                checked={agreed}
                onChange={(e) => setAgreed(e.target.checked)}
                className="mt-1 rounded text-red-600 focus:ring-red-500 border-slate-300"
              />
              <span className="text-xs font-bold text-slate-700 dark:text-gray-300 leading-normal">
                Estoy de acuerdo en que los datos se borren permanentemente y entiendo que no hay marcha atrás.
              </span>
            </label>

            {/* Paso 2: Email */}
            <p className="text-xs font-bold text-slate-500 dark:text-gray-400 mb-2 uppercase tracking-wide">
              Escribe el email del jugador para confirmar:
            </p>
            <input
              type="email"
              value={confirmEmail}
              onChange={(e) => setConfirmEmail(e.target.value)}
              placeholder={user.email}
              className="input-field mb-4 text-sm"
            />

            {resetError && (
              <p className="text-sm text-red-400 mb-3">{resetError}</p>
            )}

            {/* Paso 3: Botones */}
            <div className="flex gap-3">
              <button
                onClick={() => { setResetModal(null); setConfirmEmail(''); setResetError(''); setAgreed(false); }}
                className="btn-ghost flex-1 text-xs"
              >
                Cancelar
              </button>
              <button
                onClick={handleReset}
                disabled={resetLoading || !agreed || !canDelete || confirmEmail !== user.email}
                className={`btn-danger flex-1 disabled:opacity-40 flex items-center justify-center gap-1.5 transition-all text-xs font-semibold py-2.5 ${
                  (!agreed || !canDelete || confirmEmail !== user.email) ? 'bg-slate-300 dark:bg-slate-700 border-transparent text-slate-500 dark:text-slate-400 cursor-not-allowed' : ''
                }`}
              >
                <Trash2 className="w-4 h-4" />
                {resetLoading
                  ? 'Procesando...'
                  : !agreed
                  ? 'Acepte los términos'
                  : !canDelete
                  ? `Borrar (espere ${countdown}s...)`
                  : 'Borrar Datos'}
              </button>
            </div>
          </div>
        </div>
      )}
      {/* Confirm Slot Change Modal */}
      {confirmSlotModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-white dark:bg-surface-800 rounded-2xl shadow-2xl border border-slate-200 dark:border-white/10 p-8 max-w-md w-full mx-4 animate-slide-up">
            <div className="flex items-center justify-center mb-5">
              <div className="w-14 h-14 rounded-2xl bg-amber-500/10 border border-amber-200 dark:border-amber-500/20 flex items-center justify-center">
                <ShieldAlert className="w-7 h-7 text-amber-500" />
              </div>
            </div>
            <h3 className="text-lg font-bold text-slate-800 dark:text-white text-center mb-2">
              Confirmación de Cambio de Slot
            </h3>
            <p className="text-sm text-slate-500 dark:text-gray-400 text-center mb-6 leading-relaxed">
              ¿Está seguro que desea cambiar de slot a este jugador?
              <br />
              <span className="font-semibold text-slate-700 dark:text-gray-200">
                Se activará: {confirmSlotModal.slotLabel} (Slot {confirmSlotModal.slotNumber})
              </span>
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setConfirmSlotModal(null)}
                className="flex-1 px-4 py-2.5 rounded-xl text-sm font-bold bg-slate-100 dark:bg-white/5 text-slate-600 dark:text-gray-400 border border-slate-200 dark:border-white/10 hover:bg-slate-200 dark:hover:bg-white/10 transition-all"
              >
                No
              </button>
              <button
                onClick={confirmActivateSlot}
                disabled={slotsLoading}
                className="flex-1 px-4 py-2.5 rounded-xl text-sm font-bold bg-primary-500 text-white hover:bg-primary-600 transition-all shadow-md shadow-primary-500/20 disabled:opacity-50"
              >
                {slotsLoading ? 'Procesando...' : 'Sí'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
