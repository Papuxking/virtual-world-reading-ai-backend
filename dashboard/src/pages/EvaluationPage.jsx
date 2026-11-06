import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ClipboardList, Download, Gauge, GraduationCap, Users } from 'lucide-react';
import {
  downloadEvaluationCSV,
  getEvaluationResponses,
  getEvaluationSummary,
} from '../services/api';

const SUS_ITEMS = [
  'Me gustaría usar este mundo virtual frecuentemente.',
  'El mundo virtual fue innecesariamente complejo.',
  'El mundo virtual fue fácil de usar.',
  'Necesitaría ayuda técnica para usarlo.',
  'Sus funciones estuvieron bien integradas.',
  'El mundo virtual fue demasiado inconsistente.',
  'La mayoría aprendería a usarlo rápidamente.',
  'El mundo virtual fue engorroso de usar.',
  'Me sentí con confianza al usarlo.',
  'Tuve que aprender muchas cosas antes de usarlo.',
];

const TAM_PU_ITEMS = [
  'Permitió completar más rápidamente las actividades.',
  'Mejoró el desempeño en comprensión lectora.',
  'Aumentó la productividad en actividades de lectura.',
  'Aumentó la eficacia en comprensión lectora.',
  'Hizo más fáciles las actividades de comprensión lectora.',
  'Fue útil para aprender y practicar comprensión lectora.',
];

const TAM_EASE_ITEMS = [
  'Aprender a utilizarlo fue fácil.',
  'Fue fácil hacer que respondiera como quería.',
  'La interacción fue clara y comprensible.',
  'Fue flexible al interactuar.',
  'Fue fácil adquirir habilidad para usarlo.',
  'El mundo virtual fue fácil de usar.',
];

const TH = 'px-5 py-3 text-xs font-semibold text-slate-500 dark:text-gray-400 uppercase tracking-wider';

function formatNumber(value, digits = 1) {
  return value === null || value === undefined ? '—' : Number(value).toFixed(digits);
}

function itemAverage(counts) {
  const total = counts.reduce((sum, count) => sum + count, 0);
  if (!total) return null;
  return counts.reduce((sum, count, index) => sum + count * (index + 1), 0) / total;
}

function dateTime(value) {
  return value ? new Date(value).toLocaleString('es-EC') : '—';
}

export default function EvaluationPage() {
  const navigate = useNavigate();
  const [summary, setSummary] = useState(null);
  const [responses, setResponses] = useState([]);
  const [section, setSection] = useState('sus');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [downloadError, setDownloadError] = useState('');

  useEffect(() => {
    let alive = true;
    Promise.all([getEvaluationSummary(), getEvaluationResponses()])
      .then(([s, r]) => {
        if (!alive) return;
        setSummary(s);
        setResponses(Array.isArray(r) ? r : []);
      })
      .catch((err) => { if (alive) setError(err.message || 'No se pudo cargar la encuesta'); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, []);

  const currentItems = useMemo(() => {
    if (section === 'sus') return { prefix: 'sus', labels: SUS_ITEMS, scale: 5 };
    if (section === 'tam_pu') return { prefix: 'tam_pu', labels: TAM_PU_ITEMS, scale: 7 };
    return { prefix: 'tam_peou', labels: TAM_EASE_ITEMS, scale: 7 };
  }, [section]);

  async function exportCsv() {
    setDownloadError('');
    try {
      await downloadEvaluationCSV();
    } catch (err) {
      setDownloadError(err.message || 'No se pudo descargar el CSV');
    }
  }

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-3 border-violet-500/30 border-t-violet-500 rounded-full animate-spin" /></div>;
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-800 dark:text-white flex items-center gap-3">
            <span className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-indigo-500 flex items-center justify-center shadow-lg shadow-violet-500/20">
              <ClipboardList className="w-5 h-5 text-white" />
            </span>
            Encuesta SUS/TAM
          </h1>
          <p className="text-slate-500 dark:text-gray-400 mt-1">
            Usabilidad, utilidad percibida y facilidad de uso del mundo virtual
          </p>
        </div>
        <button type="button" onClick={exportCsv} className="btn-primary flex items-center justify-center gap-2 text-sm">
          <Download className="w-4 h-4" /> Exportar respuestas CSV
        </button>
      </div>

      {(error || downloadError) && (
        <div className="glass-card p-4 text-sm text-red-500 dark:text-red-400">{error || downloadError}</div>
      )}

      {!error && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-4">
            <Stat icon={<Users />} label="Respondieron / habilitados" value={`${summary?.responses ?? 0} / ${summary?.eligible_slots ?? 0}`} />
            <Stat icon={<Gauge />} label="Tasa de respuesta" value={`${formatNumber(summary?.response_rate)} %`} />
            <Stat icon={<ClipboardList />} label="SUS medio (0–100)" value={formatNumber(summary?.sus_average)} />
            <Stat icon={<GraduationCap />} label="TAM utilidad (1–7)" value={formatNumber(summary?.tam_usefulness_average, 2)} />
            <Stat icon={<GraduationCap />} label="TAM facilidad (1–7)" value={formatNumber(summary?.tam_ease_average, 2)} />
          </div>

          <div className="glass-card p-6">
            <div className="flex flex-wrap gap-2 mb-5">
              <Tab active={section === 'sus'} onClick={() => setSection('sus')}>SUS · Usabilidad</Tab>
              <Tab active={section === 'tam_pu'} onClick={() => setSection('tam_pu')}>TAM · Utilidad</Tab>
              <Tab active={section === 'tam_peou'} onClick={() => setSection('tam_peou')}>TAM · Facilidad</Tab>
            </div>
            <h2 className="text-lg font-bold text-slate-800 dark:text-white mb-1">Distribución por afirmación</h2>
            <p className="text-xs text-slate-400 dark:text-gray-400 mb-5">
              Las barras muestran cuántas respuestas recibió cada valor de la escala. La puntuación SUS es una escala 0–100, no un porcentaje.
            </p>
            <div className="space-y-5">
              {currentItems.labels.map((label, index) => {
                const counts = summary?.item_distributions?.[`${currentItems.prefix}_${index + 1}`] ?? Array(currentItems.scale).fill(0);
                const total = counts.reduce((sum, n) => sum + n, 0);
                return (
                  <div key={`${currentItems.prefix}_${index + 1}`}>
                    <div className="flex items-start justify-between gap-4 mb-2">
                      <p className="text-sm text-slate-700 dark:text-gray-300"><span className="font-bold">{index + 1}.</span> {label}</p>
                      <span className="shrink-0 text-xs font-bold text-violet-600 dark:text-violet-400">Media {formatNumber(itemAverage(counts), 2)}</span>
                    </div>
                    <div className="grid gap-2" style={{ gridTemplateColumns: `repeat(${currentItems.scale}, minmax(0, 1fr))` }}>
                      {counts.map((count, value) => (
                        <div key={value} className="text-center">
                          <div className="h-7 rounded-md bg-slate-100 dark:bg-white/5 overflow-hidden flex items-end">
                            <div className="w-full bg-violet-500/70" style={{ height: total && count ? `${Math.max(8, count / total * 100)}%` : '0%' }} />
                          </div>
                          <span className="text-[11px] text-slate-400">{value + 1}: {count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="glass-card overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200/50 dark:border-white/5">
              <h2 className="text-sm font-semibold text-slate-700 dark:text-gray-300">Respuestas por alumno y slot</h2>
            </div>
            {responses.length === 0 ? (
              <p className="p-10 text-center text-slate-500 dark:text-gray-400">Todavía no hay respuestas en este entorno.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead><tr className="border-b border-slate-200/50 dark:border-white/5">
                    <th className={`text-left ${TH}`}>Alumno</th><th className={`text-left ${TH}`}>Slot</th>
                    <th className={`text-right ${TH}`}>SUS</th><th className={`text-right ${TH}`}>TAM utilidad</th>
                    <th className={`text-right ${TH}`}>TAM facilidad</th><th className={`text-right ${TH}`}>Enviada</th>
                  </tr></thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-white/5">
                    {responses.map((row) => (
                      <tr key={`${row.player_id}-${row.slot_number}`} onClick={() => navigate(`/players/${row.player_id}`)} className="table-row-hover cursor-pointer">
                        <td className="px-5 py-3"><p className="text-sm font-semibold text-slate-800 dark:text-white">{row.display_name}</p><p className="text-xs text-slate-400">{row.email}</p></td>
                        <td className="px-5 py-3 text-sm text-slate-600 dark:text-gray-300">{row.slot_label || `Slot ${row.slot_number}`}</td>
                        <td className="px-5 py-3 text-right font-bold text-slate-800 dark:text-white">{formatNumber(row.sus_score)}</td>
                        <td className="px-5 py-3 text-right text-sm text-slate-700 dark:text-gray-300">{formatNumber(row.tam_usefulness_score, 2)}</td>
                        <td className="px-5 py-3 text-right text-sm text-slate-700 dark:text-gray-300">{formatNumber(row.tam_ease_score, 2)}</td>
                        <td className="px-5 py-3 text-right text-xs text-slate-500 dark:text-gray-400">{dateTime(row.submitted_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

function Stat({ icon, label, value }) {
  return <div className="stat-card"><div className="w-9 h-9 rounded-lg bg-violet-500/10 text-violet-600 dark:text-violet-400 flex items-center justify-center mb-3 [&>svg]:w-4 [&>svg]:h-4">{icon}</div><p className="text-2xl font-extrabold text-slate-800 dark:text-white">{value}</p><p className="text-xs font-semibold text-slate-400 dark:text-gray-400 mt-1">{label}</p></div>;
}

function Tab({ active, onClick, children }) {
  return <button type="button" onClick={onClick} className={`px-3 py-2 rounded-lg text-xs font-semibold border transition-colors ${active ? 'bg-violet-500/10 text-violet-600 dark:text-violet-400 border-violet-500/25' : 'text-slate-500 dark:text-gray-400 border-slate-200 dark:border-white/10 hover:bg-slate-100 dark:hover:bg-white/5'}`}>{children}</button>;
}
