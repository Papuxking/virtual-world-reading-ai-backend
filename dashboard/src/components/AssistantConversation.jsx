import { useEffect, useMemo, useState } from 'react';
import { Bot, ChevronDown, ChevronUp, MessageCircle, User } from 'lucide-react';
import { getNpcConversations } from '../services/api';

const NPC_LABELS = { robot: 'Robot asistente', sabio: 'Sabio' };

function formatearFecha(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleString('es-EC', {
    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
  });
}

/**
 * Conversación del jugador con el asistente IA, agrupada por lectura. Solo
 * trae las interacciones con texto: las anteriores a que se guardara solo se
 * contaban.
 */
export default function AssistantConversation({ playerId }) {
  const [mensajes, setMensajes] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);
  const [abierta, setAbierta] = useState(null);

  useEffect(() => {
    // Al cambiar de jugador el padre lo vuelve a montar (key), así que el
    // estado ya empieza «cargando».
    let vigente = true;
    getNpcConversations(playerId)
      .then((datos) => { if (vigente) setMensajes(datos); })
      .catch((err) => { if (vigente) setError(err.message || 'No se pudo cargar la conversación'); })
      .finally(() => { if (vigente) setCargando(false); });
    return () => { vigente = false; };
  }, [playerId]);

  // Una entrada por lectura, la conversada más recientemente primero.
  const porLectura = useMemo(() => {
    const grupos = new Map();
    for (const m of mensajes) {
      const clave = m.reading_id ?? 'sin-lectura';
      if (!grupos.has(clave)) {
        grupos.set(clave, {
          clave,
          titulo: m.reading_title || 'Lectura eliminada',
          tipologia: m.typology,
          mensajes: [],
        });
      }
      grupos.get(clave).mensajes.push(m);
    }
    return [...grupos.values()].sort((a, b) =>
      new Date(b.mensajes.at(-1).created_at) - new Date(a.mensajes.at(-1).created_at));
  }, [mensajes]);

  return (
    <div className="glass-card p-6">
      <h3 className="text-lg font-semibold text-slate-800 dark:text-white mb-1 flex items-center gap-2">
        <MessageCircle className="w-5 h-5 text-primary-500 dark:text-primary-400" />
        Conversación con el asistente IA
      </h3>
      <p className="text-xs text-slate-500 dark:text-gray-400 mb-4">
        {mensajes.length} {mensajes.length === 1 ? 'pregunta' : 'preguntas'} en {porLectura.length}{' '}
        {porLectura.length === 1 ? 'lectura' : 'lecturas'}
      </p>

      {cargando ? (
        <div className="py-8 text-center text-xs text-slate-400 animate-pulse">Cargando conversación...</div>
      ) : error ? (
        <p className="text-sm text-red-500 dark:text-red-400">{error}</p>
      ) : porLectura.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-8 text-center bg-slate-50/50 dark:bg-white/[0.01] border border-dashed border-slate-200 dark:border-white/5 rounded-xl">
          <Bot className="w-8 h-8 text-slate-300 dark:text-gray-600 mb-2" />
          <p className="text-xs font-bold text-slate-500 dark:text-gray-400">Sin conversaciones guardadas</p>
          <p className="text-[10px] text-slate-400 dark:text-gray-400 max-w-[240px] mt-1 leading-normal">
            Aquí aparecerá lo que el estudiante le pregunte al asistente durante las lecturas.
          </p>
        </div>
      ) : (
        <div className="space-y-2 max-h-[520px] overflow-y-auto pr-1">
          {porLectura.map((grupo) => {
            const expandida = abierta === grupo.clave;
            return (
              <div
                key={grupo.clave}
                className={`border rounded-xl overflow-hidden transition-all duration-200 ${
                  expandida
                    ? 'bg-slate-50/40 dark:bg-white/[0.01] border-slate-300 dark:border-white/10 shadow-sm'
                    : 'bg-white dark:bg-transparent border-slate-200/60 dark:border-white/5 hover:border-slate-300 dark:hover:border-white/10'
                }`}
              >
                <button
                  onClick={() => setAbierta(expandida ? null : grupo.clave)}
                  className="w-full p-2.5 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-white/5 transition-colors"
                >
                  <div className="text-left min-w-0">
                    <p className="text-xs font-semibold text-slate-700 dark:text-gray-200 truncate">{grupo.titulo}</p>
                    {grupo.tipologia && (
                      <p className="text-[10px] text-slate-400 dark:text-gray-400">{grupo.tipologia}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-1.5 ml-2 flex-shrink-0">
                    <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-primary-50 dark:bg-primary-500/10 text-primary-600 dark:text-primary-400 border border-primary-100 dark:border-primary-500/20">
                      {grupo.mensajes.length} {grupo.mensajes.length === 1 ? 'pregunta' : 'preguntas'}
                    </span>
                    {expandida
                      ? <ChevronUp className="w-3.5 h-3.5 text-slate-400 dark:text-gray-400" />
                      : <ChevronDown className="w-3.5 h-3.5 text-slate-400 dark:text-gray-400" />}
                  </div>
                </button>

                {expandida && (
                  <div className="px-3 pb-3 pt-2 border-t border-slate-200/50 dark:border-white/5 space-y-3">
                    {grupo.mensajes.map((m) => (
                      <div key={m.id} className="space-y-1.5">
                        <div className="flex items-start gap-2 justify-end">
                          <div className="max-w-[85%] rounded-xl rounded-tr-sm px-3 py-2 bg-primary-600 text-white">
                            <p className="text-xs leading-relaxed whitespace-pre-wrap">{m.user_message}</p>
                          </div>
                          <User className="w-4 h-4 mt-1 text-slate-400 dark:text-gray-400 flex-shrink-0" />
                        </div>
                        {m.assistant_reply && (
                          <div className="flex items-start gap-2">
                            <Bot className="w-4 h-4 mt-1 text-primary-500 dark:text-primary-400 flex-shrink-0" />
                            <div className="max-w-[85%] rounded-xl rounded-tl-sm px-3 py-2 bg-white dark:bg-white/5 border border-slate-100 dark:border-white/5">
                              <p className="text-xs text-slate-700 dark:text-gray-200 leading-relaxed whitespace-pre-wrap">{m.assistant_reply}</p>
                            </div>
                          </div>
                        )}
                        <p className="text-[9px] text-slate-400 dark:text-gray-400 text-center">
                          {NPC_LABELS[m.npc_type] || m.npc_type} · {formatearFecha(m.created_at)}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
