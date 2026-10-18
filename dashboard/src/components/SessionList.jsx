import { useState } from 'react';
import { CheckCircle2, XCircle, ChevronDown, ChevronUp } from 'lucide-react';

// Lista de sesiones desplegables con sus respuestas. La usan el historial de
// progresión y la tarjeta de práctica del detalle del jugador.
export default function SessionList({ sessions, emptyText }) {
  const [expanded, setExpanded] = useState(null);

  if (sessions.length === 0) {
    return <p className="text-sm text-slate-400 dark:text-gray-400 py-4 text-center">{emptyText}</p>;
  }

  return (
    <>
      {sessions.map((session) => (
        <div key={session.id} className="border border-slate-200/60 dark:border-white/5 rounded-xl overflow-hidden bg-white dark:bg-transparent">
          <button
            onClick={() => setExpanded(expanded === session.id ? null : session.id)}
            className="w-full p-3 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-white/5 transition-colors"
          >
            <div className="flex items-center gap-3 text-left">
              <div className={`w-2 h-2 rounded-full ${session.is_perfect ? 'bg-emerald-400' : 'bg-amber-400'}`} />
              <div>
                <p className="text-sm font-semibold text-slate-700 dark:text-gray-200 truncate max-w-[180px]">
                  {session.reading_title}
                </p>
                <p className="text-xs text-slate-400 dark:text-gray-400 font-medium">
                  {session.typology} · {session.completed_at
                    ? new Date(session.completed_at).toLocaleDateString('es-EC', { day: '2-digit', month: 'short' })
                    : '—'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm font-bold text-amber-600 dark:text-amber-400">{session.session_score} pts</span>
              <span className="text-xs text-slate-500 dark:text-gray-400 font-semibold">{session.correct_count}/{session.correct_count + session.incorrect_count}</span>
              {expanded === session.id ? (
                <ChevronUp className="w-4 h-4 text-slate-400 dark:text-gray-400" />
              ) : (
                <ChevronDown className="w-4 h-4 text-slate-400 dark:text-gray-400" />
              )}
            </div>
          </button>
          {expanded === session.id && (
            <div className="px-3 pb-3 border-t border-slate-200/50 dark:border-white/5 mt-0 pt-3 animate-slide-up bg-slate-50/30 dark:bg-transparent">
              <div className="grid grid-cols-3 gap-2 text-xs mb-3">
                <div className="text-center">
                  <p className="text-slate-400 dark:text-gray-400 font-semibold">Lectura</p>
                  <p className="text-slate-700 dark:text-gray-300 font-bold">
                    {session.reading_time_seconds ? `${Math.floor(session.reading_time_seconds / 60)}m ${session.reading_time_seconds % 60}s` : '—'}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-slate-400 dark:text-gray-400 font-semibold">Total</p>
                  <p className="text-slate-700 dark:text-gray-300 font-bold">
                    {session.total_time_seconds ? `${Math.floor(session.total_time_seconds / 60)}m ${session.total_time_seconds % 60}s` : '—'}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-slate-400 dark:text-gray-400 font-semibold">Bonus</p>
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
                      <span className="text-slate-400 dark:text-gray-400 font-semibold">{a.comprehension_level}</span>
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
      ))}
    </>
  );
}
