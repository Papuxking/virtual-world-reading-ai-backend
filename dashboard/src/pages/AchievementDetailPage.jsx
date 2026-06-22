import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  getAchievementDetail, uploadMedalImageAdmin, restoreMedalImage,
  deleteHistoryImage, downloadAchievementPlayersCSV, downloadAchievementPlayersExcel,
} from '../services/api';
import {
  ArrowLeft, Trophy, Upload, RotateCcw, Trash2, Search,
  Download, FileText, FileSpreadsheet, ChevronDown, Clock,
  Users, Medal, Info, ImageIcon, AlertTriangle, CheckCircle2, X,
} from 'lucide-react';

const API_BASE = 'http://localhost:8001';

const TIER_LABELS = { bronce: 'Bronce', plata: 'Plata', oro: 'Oro', platino: 'Platino' };
const TIER_BADGE_CLASS = { bronce: 'badge-bronze', plata: 'badge-silver', oro: 'badge-gold', platino: 'badge-platinum' };
const CATEGORY_BADGE_CLASS = { progreso: 'badge-progreso', maestría: 'badge-maestria', exploración: 'badge-exploracion', superación: 'badge-superacion' };

export default function AchievementDetailPage() {
  const { achievementId } = useParams();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [achievement, setAchievement] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [searchPlayers, setSearchPlayers] = useState('');
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [toast, setToast] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);

  const loadDetail = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getAchievementDetail(achievementId);
      setAchievement(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [achievementId]);

  useEffect(() => { loadDetail(); }, [loadDetail]);

  function showToast(message, type = 'success') {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  }

  async function handleUpload(file) {
    if (!file) return;
    if (!file.name.match(/\.(png|jpe?g|webp|bmp|gif)$/i)) {
      showToast('Formatos aceptados: PNG, JPG, WebP, BMP, GIF', 'error');
      return;
    }
    try {
      setUploading(true);
      await uploadMedalImageAdmin(achievementId, file);
      showToast('Imagen actualizada exitosamente');
      await loadDetail();
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setUploading(false);
    }
  }

  async function handleRestore(historyId) {
    try {
      await restoreMedalImage(achievementId, historyId);
      showToast('Imagen restaurada exitosamente');
      await loadDetail();
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  async function handleDeleteHistory(historyId) {
    try {
      await deleteHistoryImage(achievementId, historyId);
      showToast('Imagen del historial eliminada');
      setConfirmDelete(null);
      await loadDetail();
    } catch (err) {
      showToast(err.message, 'error');
      setConfirmDelete(null);
    }
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    handleUpload(file);
  }

  const filteredPlayers = achievement?.players?.filter(p =>
    !searchPlayers ||
    p.display_name.toLowerCase().includes(searchPlayers.toLowerCase()) ||
    p.email.toLowerCase().includes(searchPlayers.toLowerCase())
  ) || [];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-3 border-primary-500/30 border-t-primary-500 rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !achievement) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <AlertTriangle className="w-12 h-12 text-red-400" />
        <p className="text-slate-500 dark:text-gray-400">{error || 'Logro no encontrado'}</p>
        <button onClick={() => navigate('/achievements')} className="btn-ghost">Volver</button>
      </div>
    );
  }

  const ach = achievement;

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Toast */}
      {toast && (
        <div className={`fixed top-6 right-6 z-50 animate-slide-up flex items-center gap-2 px-4 py-3 rounded-xl shadow-xl border text-sm font-medium ${
          toast.type === 'error'
            ? 'bg-red-50 dark:bg-red-500/10 text-red-700 dark:text-red-400 border-red-200 dark:border-red-500/20'
            : 'bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-500/20'
        }`}>
          {toast.type === 'error' ? <AlertTriangle className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
          {toast.message}
          <button onClick={() => setToast(null)} className="ml-2 opacity-50 hover:opacity-100"><X className="w-3.5 h-3.5" /></button>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {confirmDelete !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-white dark:bg-surface-800 rounded-2xl shadow-2xl p-6 max-w-sm mx-4 border border-slate-200 dark:border-white/10 animate-slide-up">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-red-500/10 flex items-center justify-center">
                <Trash2 className="w-5 h-5 text-red-500" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-800 dark:text-white">¿Eliminar imagen?</h3>
                <p className="text-xs text-slate-500 dark:text-gray-400">Esta acción no se puede deshacer.</p>
              </div>
            </div>
            <div className="flex gap-2">
              <button onClick={() => setConfirmDelete(null)} className="btn-ghost flex-1 text-sm">Cancelar</button>
              <button onClick={() => handleDeleteHistory(confirmDelete)} className="btn-danger flex-1 text-sm">Eliminar</button>
            </div>
          </div>
        </div>
      )}

      {/* Breadcrumb & Back */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => navigate('/achievements')}
          className="flex items-center gap-1.5 text-sm text-slate-500 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Logros y Medallas
        </button>
        <span className="text-slate-300 dark:text-gray-600">/</span>
        <span className="text-sm font-medium text-slate-700 dark:text-gray-200 truncate">{ach.name}</span>
      </div>

      {/* Main Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Medal Image & Upload */}
        <div className="space-y-6">
          {/* Medal Card */}
          <div className="glass-card p-6 text-center">
            <div className="w-40 h-40 mx-auto rounded-2xl bg-slate-100 dark:bg-white/5 border-2 border-slate-200/50 dark:border-white/10 flex items-center justify-center overflow-hidden mb-4 shadow-inner">
              {ach.medal_image_path ? (
                <img
                  src={`${API_BASE}${ach.medal_image_path}`}
                  alt={ach.medal_name}
                  className="w-full h-full object-cover"
                  onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex'; }}
                />
              ) : null}
              <span
                className="text-7xl"
                style={ach.medal_image_path ? { display: 'none' } : { display: 'flex' }}
              >
                {ach.medal_placeholder_emoji || ach.icon}
              </span>
            </div>
            <h2 className="text-lg font-bold text-slate-800 dark:text-white">{ach.medal_name}</h2>
            <span className={`${TIER_BADGE_CLASS[ach.medal_tier] || 'badge-info'} mt-2`}>
              {TIER_LABELS[ach.medal_tier] || ach.medal_tier}
            </span>
          </div>

          {/* Upload Zone */}
          <div
            className={`image-upload-zone ${dragOver ? 'drag-over' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".png,.jpg,.jpeg,.webp,.bmp,.gif"
              className="hidden"
              onChange={(e) => handleUpload(e.target.files[0])}
            />
            {uploading ? (
              <div className="w-8 h-8 border-3 border-primary-500/30 border-t-primary-500 rounded-full animate-spin" />
            ) : (
              <>
                <Upload className="w-8 h-8 text-slate-400 dark:text-gray-500" />
                <p className="text-sm font-medium text-slate-600 dark:text-gray-300">Subir nueva imagen</p>
                <p className="text-xs text-slate-400 dark:text-gray-500">PNG, JPG, WebP… se redimensiona a 256×256 auto</p>
              </>
            )}
          </div>

          {/* Image History */}
          {ach.image_history && ach.image_history.length > 0 && (
            <div className="glass-card p-6">
              <h3 className="text-sm font-semibold text-slate-700 dark:text-gray-300 mb-4 flex items-center gap-2">
                <Clock className="w-4 h-4 text-primary-500 dark:text-primary-400" />
                Historial de Imágenes ({ach.image_history.length})
              </h3>
              <div className="space-y-3">
                {ach.image_history.map(hist => (
                  <div
                    key={hist.id}
                    className={`flex items-center gap-3 p-2.5 rounded-xl border transition-all ${
                      hist.is_current
                        ? 'bg-primary-50/50 dark:bg-primary-500/5 border-primary-200 dark:border-primary-500/20'
                        : 'bg-slate-50/50 dark:bg-white/[0.02] border-slate-200/50 dark:border-white/5 hover:bg-slate-100/50 dark:hover:bg-white/5'
                    }`}
                  >
                    <div className="gallery-thumb shrink-0">
                      <img
                        src={`${API_BASE}${hist.image_path}`}
                        alt="Medal version"
                        className="w-full h-full object-cover"
                        onError={(e) => { e.target.src = ''; e.target.alt = '❌'; }}
                      />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-slate-600 dark:text-gray-300 truncate">
                        {hist.original_filename || 'imagen.png'}
                      </p>
                      <p className="text-[10px] text-slate-400 dark:text-gray-500">
                        {new Date(hist.uploaded_at).toLocaleDateString('es-EC', {
                          day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
                        })}
                      </p>
                      {hist.uploader_name && (
                        <p className="text-[10px] text-slate-400 dark:text-gray-500">
                          por {hist.uploader_name}
                        </p>
                      )}
                      {hist.is_current && (
                        <span className="badge-success text-[10px] mt-1">Actual</span>
                      )}
                    </div>
                    <div className="flex flex-col gap-1 shrink-0">
                      {!hist.is_current && (
                        <>
                          <button
                            onClick={() => handleRestore(hist.id)}
                            className="p-1.5 rounded-lg bg-primary-50 hover:bg-primary-100 text-primary-600 dark:bg-primary-500/10 dark:hover:bg-primary-500/20 dark:text-primary-400 transition-colors"
                            title="Restaurar"
                          >
                            <RotateCcw className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => setConfirmDelete(hist.id)}
                            className="p-1.5 rounded-lg bg-red-50 hover:bg-red-100 text-red-600 dark:bg-red-500/10 dark:hover:bg-red-500/20 dark:text-red-400 transition-colors"
                            title="Eliminar"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Details & Players */}
        <div className="lg:col-span-2 space-y-6">
          {/* Achievement Info */}
          <div className="glass-card p-6">
            <div className="flex items-start gap-4 mb-6">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center text-3xl shadow-lg shadow-amber-500/20 shrink-0">
                {ach.icon}
              </div>
              <div className="flex-1 min-w-0">
                <h1 className="text-xl font-bold text-slate-800 dark:text-white">{ach.name}</h1>
                <div className="flex flex-wrap items-center gap-2 mt-2">
                  <span className={CATEGORY_BADGE_CLASS[ach.category] || 'badge-info'}>
                    {ach.category.charAt(0).toUpperCase() + ach.category.slice(1)}
                  </span>
                  <span className={TIER_BADGE_CLASS[ach.medal_tier] || 'badge-info'}>
                    {TIER_LABELS[ach.medal_tier]}
                  </span>
                  <span className="badge-info">
                    #{ach.display_order}
                  </span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <InfoRow icon={<Info className="w-4 h-4" />} label="Descripción" value={ach.description} />
              <InfoRow icon={<Trophy className="w-4 h-4" />} label="Cómo desbloquear" value={ach.how_to_unlock} />
              <InfoRow icon={<Medal className="w-4 h-4" />} label="Descripción medalla" value={ach.medal_description || '—'} />
              <InfoRow icon={<ImageIcon className="w-4 h-4" />} label="Emoji placeholder" value={ach.medal_placeholder_emoji || '🏅'} />
            </div>

            {/* Unlock Progress */}
            <div className="mt-6 p-4 rounded-xl bg-slate-50/80 dark:bg-white/[0.03] border border-slate-200/50 dark:border-white/5">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-semibold text-slate-700 dark:text-gray-300 flex items-center gap-2">
                  <Users className="w-4 h-4 text-primary-500" />
                  Progreso de Desbloqueo
                </span>
                <span className="text-lg font-extrabold text-primary-600 dark:text-primary-400">
                  {ach.unlock_percentage}%
                </span>
              </div>
              <div className="progress-bar h-3">
                <div
                  className="progress-bar-fill bg-gradient-to-r from-primary-500 to-violet-500"
                  style={{ width: `${Math.min(ach.unlock_percentage, 100)}%` }}
                />
              </div>
              <p className="text-xs text-slate-500 dark:text-gray-400 mt-2">
                {ach.unlock_count} de {ach.total_players} jugadores lo han desbloqueado
              </p>
            </div>
          </div>

          {/* Players Table */}
          <div className="glass-card overflow-hidden">
            <div className="p-6 border-b border-slate-200/50 dark:border-white/5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <h3 className="text-lg font-semibold text-slate-800 dark:text-white flex items-center gap-2">
                <Users className="w-5 h-5 text-primary-500 dark:text-primary-400" />
                Jugadores ({filteredPlayers.length})
              </h3>

              <div className="flex items-center gap-2 w-full sm:w-auto">
                <div className="relative flex-1 sm:w-64">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 dark:text-gray-500" />
                  <input
                    type="text"
                    value={searchPlayers}
                    onChange={(e) => setSearchPlayers(e.target.value)}
                    placeholder="Buscar jugador..."
                    className="input-field pl-10 text-sm"
                    id="detail-player-search"
                  />
                </div>

                {/* Export Menu */}
                <div className="relative">
                  <button
                    onClick={() => setShowExportMenu(!showExportMenu)}
                    className="btn-ghost flex items-center gap-1.5 text-sm py-2"
                  >
                    <Download className="w-4 h-4" />
                    <ChevronDown className="w-3 h-3" />
                  </button>
                  {showExportMenu && (
                    <>
                      <div className="fixed inset-0 z-10" onClick={() => setShowExportMenu(false)} />
                      <div className="absolute right-0 top-full mt-2 w-48 bg-white dark:bg-surface-800 border border-slate-200 dark:border-white/10 rounded-xl shadow-xl z-20 py-1 animate-slide-up">
                        <button
                          onClick={() => { downloadAchievementPlayersCSV(achievementId); setShowExportMenu(false); }}
                          className="flex items-center gap-2 w-full px-4 py-2.5 text-sm text-slate-700 dark:text-gray-300 hover:bg-slate-50 dark:hover:bg-white/5"
                        >
                          <FileText className="w-4 h-4 text-emerald-500" /> CSV
                        </button>
                        <button
                          onClick={() => { downloadAchievementPlayersExcel(achievementId); setShowExportMenu(false); }}
                          className="flex items-center gap-2 w-full px-4 py-2.5 text-sm text-slate-700 dark:text-gray-300 hover:bg-slate-50 dark:hover:bg-white/5"
                        >
                          <FileSpreadsheet className="w-4 h-4 text-primary-500" /> Excel
                        </button>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full" id="players-table">
                <thead>
                  <tr className="border-b border-slate-200/50 dark:border-white/5">
                    <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 dark:text-gray-400 uppercase tracking-wider">Jugador</th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 dark:text-gray-400 uppercase tracking-wider">Email</th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 dark:text-gray-400 uppercase tracking-wider">Slot</th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 dark:text-gray-400 uppercase tracking-wider">Fecha Desbloqueo</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-white/5">
                  {filteredPlayers.map((player, i) => (
                    <tr
                      key={`${player.user_id}-${i}`}
                      onClick={() => navigate(`/players/${player.user_id}`)}
                      className="table-row-hover cursor-pointer animate-card-in"
                      style={{ animationDelay: `${i * 30}ms` }}
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
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-500 dark:text-gray-400">{player.email}</td>
                      <td className="px-6 py-4">
                        <span className="badge-info text-xs">
                          {player.slot_label} #{player.slot_number}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-500 dark:text-gray-400">
                        {player.unlocked_at
                          ? new Date(player.unlocked_at).toLocaleDateString('es-EC', {
                              day: '2-digit', month: 'short', year: 'numeric',
                            })
                          : '—'}
                      </td>
                    </tr>
                  ))}
                  {filteredPlayers.length === 0 && (
                    <tr>
                      <td colSpan={4} className="px-6 py-12 text-center text-slate-400 dark:text-gray-500">
                        <Users className="w-8 h-8 mx-auto mb-2 opacity-30" />
                        Ningún jugador ha desbloqueado este logro
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function InfoRow({ icon, label, value }) {
  return (
    <div className="p-3 rounded-xl bg-slate-50/80 dark:bg-white/[0.02] border border-slate-100 dark:border-white/5">
      <div className="flex items-center gap-1.5 mb-1">
        <span className="text-primary-500 dark:text-primary-400">{icon}</span>
        <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 dark:text-gray-500">{label}</span>
      </div>
      <p className="text-sm text-slate-700 dark:text-gray-300">{value}</p>
    </div>
  );
}
