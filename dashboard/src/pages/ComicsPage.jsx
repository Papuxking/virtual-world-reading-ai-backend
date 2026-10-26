import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getComicsResumen, getComicsJugadores } from '../services/api';
import { BookImage, Unlock, DoorOpen, BookOpen } from 'lucide-react';

const TH = 'px-6 py-3 text-xs font-semibold text-slate-500 dark:text-gray-400 uppercase tracking-wider';

function fecha(valor) {
  return valor ? new Date(valor).toLocaleDateString('es-EC') : '—';
}

export default function ComicsPage() {
  const navigate = useNavigate();
  const [resumen, setResumen] = useState(null);
  const [jugadores, setJugadores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let vivo = true;
    Promise.all([getComicsResumen(), getComicsJugadores()])
      .then(([r, j]) => {
        if (!vivo) return;
        setResumen(r);
        setJugadores(Array.isArray(j) ? j : []);
      })
      .catch((err) => { if (vivo) setError(err.message || 'No se pudo cargar la zona de cómics'); })
      .finally(() => { if (vivo) setLoading(false); });
    return () => { vivo = false; };
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-3 border-primary-500/30 border-t-primary-500 rounded-full animate-spin" />
      </div>
    );
  }

  const desbloquearon = resumen?.desbloquearon ?? 0;
  const entraron = resumen?.entraron ?? 0;
  const lectores = resumen?.lectores ?? 0;
  const top = resumen?.episodios_top ?? [];
  const vacio = !error && entraron === 0 && lectores === 0 && jugadores.length === 0;

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-slate-800 dark:text-white flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-rose-500 to-pink-500 flex items-center justify-center shadow-lg shadow-rose-500/20">
            <BookImage className="w-5 h-5 text-white" />
          </div>
          Zona de cómics
        </h1>
        <p className="text-slate-500 dark:text-gray-400 mt-1">
          ¿Funciona la recompensa? Cuántos alumnos podían entrar, cuántos entraron y cuántos leyeron
        </p>
      </div>

      {error && (
        <div className="glass-card p-4 text-sm text-red-500 dark:text-red-400">{error}</div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard icon={<Unlock className="w-5 h-5" />} label="Desbloquearon la zona" value={desbloquearon} color="from-amber-500 to-orange-500" />
        <StatCard icon={<DoorOpen className="w-5 h-5" />} label="Entraron" value={entraron} color="from-sky-500 to-cyan-500" />
        <StatCard icon={<BookOpen className="w-5 h-5" />} label="Leyeron algún episodio" value={lectores} color="from-rose-500 to-pink-500" />
      </div>

      {vacio ? (
        <div className="glass-card p-10 text-center text-slate-500 dark:text-gray-400">
          Todavía nadie ha entrado en la zona.
        </div>
      ) : (
        <>
          <div className="glass-card p-6">
            <h3 className="text-sm font-semibold text-slate-700 dark:text-gray-300 mb-4">Episodios más leídos</h3>
            {top.length === 0 ? (
              <p className="text-sm text-slate-400 dark:text-gray-400">Nadie ha abierto un episodio todavía.</p>
            ) : (
              <ul className="space-y-2">
                {top.map((e) => (
                  <li key={e.episode_id} className="flex items-center justify-between text-sm">
                    <span className="text-slate-700 dark:text-gray-300">{e.episode_id}</span>
                    <span className="font-bold text-slate-800 dark:text-white">
                      {e.lecturas} {e.lecturas === 1 ? 'alumno' : 'alumnos'}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="glass-card overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200/50 dark:border-white/5">
              <h3 className="text-sm font-semibold text-slate-700 dark:text-gray-300">Alumnos que han entrado</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-200/50 dark:border-white/5">
                    <th className={`text-left ${TH}`}>Alumno</th>
                    <th className={`text-right ${TH}`}>Episodios terminados</th>
                    <th className={`text-right ${TH}`}>Páginas leídas</th>
                    <th className={`text-right ${TH}`}>Última visita</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-white/5">
                  {jugadores.map((j) => (
                    <tr key={j.player_id} onClick={() => navigate(`/players/${j.player_id}`)} className="table-row-hover cursor-pointer">
                      <td className="px-6 py-3">
                        <p className="text-sm font-semibold text-slate-800 dark:text-white">{j.display_name}</p>
                        <p className="text-xs text-slate-400 dark:text-gray-400">{j.email}</p>
                      </td>
                      <td className="px-6 py-3 text-right text-sm text-slate-700 dark:text-gray-300">{j.episodios_terminados ?? 0}</td>
                      <td className="px-6 py-3 text-right text-sm text-slate-700 dark:text-gray-300">{j.paginas_leidas ?? 0}</td>
                      <td className="px-6 py-3 text-right text-sm text-slate-700 dark:text-gray-300">{fecha(j.ultima_visita)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
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
