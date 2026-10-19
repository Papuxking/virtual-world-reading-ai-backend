import React, { useState } from 'react';
import { X, Copy, Download, Check, AlertCircle } from 'lucide-react';
import { parsearLineas, aTexto, aCsv } from '../utils/jugadores';
import { addPlayers } from '../services/api';

export default function AddPlayersDialog({ isOpen, workspace, onClose, onSuccess }) {
  const [step, setStep] = useState(1); // 1 = entrada, 2 = resultado
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState({ created: [], skipped: [] });
  const [copied, setCopied] = useState(false);

  React.useEffect(() => {
    if (isOpen) {
      setStep(1);
      setText('');
      setError('');
      setResult({ created: [], skipped: [] });
      setCopied(false);
    }
  }, [isOpen]);

  if (!isOpen || !workspace) return null;

  const parsed = parsearLineas(text);
  const count = parsed.length;

  async function handleAdd() {
    if (count === 0) return;
    if (count > 200) {
      setError('No se pueden agregar más de 200 jugadores a la vez.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const data = await addPlayers(workspace.id, parsed);
      setResult(data);
      setStep(2);
    } catch (err) {
      setError(err.message || 'Error al agregar jugadores');
    } finally {
      setLoading(false);
    }
  }

  async function handleCopy() {
    if (!result.created.length) return;
    const tabText = aTexto(result.created);
    await navigator.clipboard.writeText(tabText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleDownloadCsv() {
    if (!result.created.length) return;
    const csvContent = aCsv(result.created);
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const hoy = new Date().toISOString().slice(0, 10);
    const safeName = workspace.name.replace(/[^\w\d-]/g, '_');
    const filename = `jugadores_${safeName}_${hoy}.csv`;

    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(a.href);
  }

  function handleFinish() {
    onClose();
    if (onSuccess) onSuccess();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm">
      <div className="glass-card w-full max-w-2xl p-6">
        {/* Cabecera */}
        <div className="flex items-center justify-between pb-3">
          <h3 className="text-lg font-bold text-slate-800 dark:text-gray-100">
            {step === 1
              ? `Agregar jugadores a «${workspace.name}»`
              : `${result.created.length} ${
                  result.created.length === 1 ? 'jugador agregado' : 'jugadores agregados'
                }`}
          </h3>
          <button
            onClick={step === 2 ? handleFinish : onClose}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-gray-200"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Paso 1: Entrada */}
        {step === 1 && (
          <div>
            <p className="text-xs text-slate-500 dark:text-gray-400">
              Un correo por línea. Si quieres, pon el nombre después de una coma; si no, se usa lo que va antes de la @.
            </p>
            <p className="mb-3 text-xs text-slate-500 dark:text-gray-400">
              Cada uno recibe una contraseña temporal y el juego le pedirá cambiarla al entrar.
            </p>

            {error && (
              <div className="mb-3 rounded-xl border border-red-300 bg-red-50 p-3 text-xs text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-300">
                {error}
              </div>
            )}

            <textarea
              rows={8}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder={'alumno1@colegio.edu, Ana Torres\nalumno2@colegio.edu\nalumno3@colegio.edu, Pedro Ruiz'}
              className="input-field font-mono text-xs leading-relaxed mb-4"
              autoFocus
            />

            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-500 dark:text-gray-400">
                {count > 0 ? `${count} ${count === 1 ? 'jugador detectado' : 'jugadores detectados'}` : ''}
              </span>
              <div className="flex gap-2">
                <button type="button" onClick={onClose} className="btn-ghost text-sm" disabled={loading}>
                  Cancelar
                </button>
                <button
                  type="button"
                  onClick={handleAdd}
                  disabled={loading || count === 0}
                  className="btn-primary text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading
                    ? 'Agregando...'
                    : count === 0
                    ? 'Agregar jugadores'
                    : `Agregar ${count} ${count === 1 ? 'jugador' : 'jugadores'}`}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Paso 2: Resultado */}
        {step === 2 && (
          <div>
            <p className="mb-4 text-xs text-slate-500 dark:text-gray-400">
              Las contraseñas temporales solo se ven ahora: cópialas o descárgalas antes de cerrar.
            </p>

            <div className="max-h-72 space-y-2 overflow-y-auto pr-1 mb-4">
              {/* Tabla de agregados */}
              {result.created.length > 0 && (
                <div className="overflow-hidden rounded-xl border border-slate-200 dark:border-white/5">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-100/80 dark:bg-white/5 text-slate-600 dark:text-gray-300">
                      <tr>
                        <th className="px-3 py-2 font-semibold">Correo</th>
                        <th className="px-3 py-2 font-semibold">Nombre</th>
                        <th className="px-3 py-2 font-semibold">Contraseña temporal</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-white/5 text-slate-700 dark:text-gray-300">
                      {result.created.map((c) => (
                        <tr key={c.id}>
                          <td className="px-3 py-2 font-mono text-[11px]">{c.email}</td>
                          <td className="px-3 py-2">{c.display_name}</td>
                          <td className="px-3 py-2 font-mono text-[11px] font-bold text-amber-600 dark:text-amber-400">
                            {c.temp_password}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Renglones de los saltados */}
              {result.skipped.length > 0 && (
                <div className="space-y-1 pt-2">
                  <p className="text-xs font-semibold text-slate-500 dark:text-gray-400">No agregados:</p>
                  {result.skipped.map((s, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50/60 px-3 py-1.5 text-xs text-amber-800 dark:border-amber-900/40 dark:bg-amber-950/20 dark:text-amber-300"
                    >
                      <AlertCircle className="h-4 w-4 flex-shrink-0 text-amber-600 dark:text-amber-400" />
                      <span className="font-mono text-[11px]">{s.email || '(línea vacía)'}</span>
                      <span>—</span>
                      <span>No se agregó: {s.reason}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex items-center justify-between border-t border-slate-200/80 pt-4 dark:border-white/5">
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={handleCopy}
                  disabled={result.created.length === 0}
                  className="btn-ghost flex items-center gap-1.5 text-xs"
                >
                  {copied ? <Check className="h-4 w-4 text-emerald-500" /> : <Copy className="h-4 w-4" />}
                  {copied ? '¡Copiado!' : 'Copiar todo'}
                </button>
                <button
                  type="button"
                  onClick={handleDownloadCsv}
                  disabled={result.created.length === 0}
                  className="btn-ghost flex items-center gap-1.5 text-xs"
                >
                  <Download className="h-4 w-4" />
                  Descargar CSV
                </button>
              </div>

              <button type="button" onClick={handleFinish} className="btn-primary text-sm">
                Listo
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
