import { AlertTriangle } from 'lucide-react';
import { useWorkspace } from '../context/workspace';

export default function WorkspaceBanner() {
  const { viewed } = useWorkspace();

  if (!viewed || viewed.is_active) {
    return null;
  }

  return (
    <div
      role="alert"
      className="mb-6 flex items-center gap-3 rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900 shadow-sm dark:border-amber-700/60 dark:bg-amber-950/40 dark:text-amber-200"
    >
      <AlertTriangle className="h-5 w-5 flex-shrink-0 text-amber-600 dark:text-amber-400" />
      <span>
        Estás viendo «{viewed.name}», que no está activo: sus jugadores no pueden entrar al juego ahora.
      </span>
    </div>
  );
}
