import React, { useState } from 'react';
import { X, AlertTriangle } from 'lucide-react';
import { useWorkspace, PALETA_ENTORNOS } from '../context/WorkspaceContext';
import {
  createWorkspace,
  updateWorkspace,
  activateWorkspace,
  deactivateWorkspace,
  deleteWorkspace,
} from '../services/api';

export function ColorPicker({ value, onChange }) {
  return (
    <div className="flex items-center gap-2">
      {PALETA_ENTORNOS.map((c) => (
        <button
          key={c}
          type="button"
          onClick={() => onChange(c)}
          className={`h-7 w-7 rounded-full transition-transform ${
            value === c
              ? 'scale-110 ring-2 ring-primary-500 ring-offset-2 dark:ring-offset-surface-900'
              : 'hover:scale-105 opacity-80 hover:opacity-100'
          }`}
          style={{ backgroundColor: c }}
          aria-label={c}
        />
      ))}
    </div>
  );
}

export function NewWorkspaceModal({ isOpen, onClose }) {
  const { refresh } = useWorkspace();
  const [name, setName] = useState('');
  const [color, setColor] = useState(PALETA_ENTORNOS[0]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  async function handleSubmit(e) {
    e.preventDefault();
    const cleanName = name.trim();
    if (!cleanName || cleanName.length > 40) {
      setError('El nombre debe tener entre 1 y 40 caracteres.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const created = await createWorkspace(cleanName, color);
      await refresh(created.id);
      setName('');
      setColor(PALETA_ENTORNOS[0]);
      onClose();
    } catch (err) {
      setError(err.message || 'Error al crear el entorno');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm">
      <div className="glass-card w-full max-w-md p-6">
        <div className="flex items-center justify-between pb-3">
          <h3 className="text-lg font-bold text-slate-800 dark:text-gray-100">Nuevo entorno</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 dark:hover:text-gray-200">
            <X className="h-5 w-5" />
          </button>
        </div>

        <p className="mb-4 text-xs text-slate-500 dark:text-gray-400">
          Se crea inactivo: nadie pierde el acceso al juego hasta que lo actives.
        </p>

        {error && (
          <div className="mb-4 rounded-xl border border-red-300 bg-red-50 p-3 text-xs text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-300">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-700 dark:text-gray-300">Nombre</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ej. Primaria 2026"
              maxLength={40}
              className="input-field text-sm"
              autoFocus
              required
            />
          </div>

          <div>
            <label className="mb-2 block text-xs font-semibold text-slate-700 dark:text-gray-300">Color</label>
            <ColorPicker value={color} onChange={setColor} />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="btn-ghost text-sm" disabled={loading}>
              Cancelar
            </button>
            <button type="submit" className="btn-primary text-sm" disabled={loading || !name.trim()}>
              {loading ? 'Creando...' : 'Crear entorno'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export function EditWorkspaceModal({ isOpen, workspace, onClose }) {
  const { refresh } = useWorkspace();
  const [name, setName] = useState(workspace?.name || '');
  const [color, setColor] = useState(workspace?.color || PALETA_ENTORNOS[0]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  React.useEffect(() => {
    if (workspace) {
      setName(workspace.name);
      setColor(workspace.color);
      setError('');
    }
  }, [workspace]);

  if (!isOpen || !workspace) return null;

  async function handleSubmit(e) {
    e.preventDefault();
    const cleanName = name.trim();
    if (!cleanName || cleanName.length > 40) {
      setError('El nombre debe tener entre 1 y 40 caracteres.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      await updateWorkspace(workspace.id, { name: cleanName, color });
      await refresh(workspace.id);
      onClose();
    } catch (err) {
      setError(err.message || 'Error al actualizar el entorno');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm">
      <div className="glass-card w-full max-w-md p-6">
        <div className="flex items-center justify-between pb-3">
          <h3 className="text-lg font-bold text-slate-800 dark:text-gray-100">Editar entorno</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 dark:hover:text-gray-200">
            <X className="h-5 w-5" />
          </button>
        </div>

        {error && (
          <div className="mb-4 rounded-xl border border-red-300 bg-red-50 p-3 text-xs text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-300">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-700 dark:text-gray-300">Nombre</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={40}
              className="input-field text-sm"
              autoFocus
              required
            />
          </div>

          <div>
            <label className="mb-2 block text-xs font-semibold text-slate-700 dark:text-gray-300">Color</label>
            <ColorPicker value={color} onChange={setColor} />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="btn-ghost text-sm" disabled={loading}>
              Cancelar
            </button>
            <button type="submit" className="btn-primary text-sm" disabled={loading || !name.trim()}>
              {loading ? 'Guardando...' : 'Guardar cambios'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export function DeleteWorkspaceModal({ isOpen, workspace, onClose }) {
  const { refresh } = useWorkspace();
  const [confirmName, setConfirmName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  React.useEffect(() => {
    setConfirmName('');
    setError('');
  }, [isOpen, workspace]);

  if (!isOpen || !workspace) return null;

  const matches = confirmName.trim() === workspace.name;

  async function handleDelete() {
    if (!matches) return;
    setLoading(true);
    setError('');
    try {
      await deleteWorkspace(workspace.id, confirmName.trim());
      await refresh();
      onClose();
    } catch (err) {
      setError(err.message || 'Error al eliminar el entorno');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm">
      <div className="glass-card w-full max-w-md p-6">
        <div className="flex items-center justify-between pb-3">
          <h3 className="text-lg font-bold text-slate-800 dark:text-gray-100">
            ¿Eliminar «{workspace.name}»?
          </h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 dark:hover:text-gray-200">
            <X className="h-5 w-5" />
          </button>
        </div>

        <p className="mb-3 text-sm text-slate-600 dark:text-gray-300">
          Se borrarán sus {workspace.player_count} {workspace.player_count === 1 ? 'cuenta' : 'cuentas'} con todo su progreso, sesiones, logros y notas. No se puede deshacer.
        </p>

        <p className="mb-2 text-xs font-semibold text-slate-700 dark:text-gray-300">
          Escribe el nombre del entorno para confirmar:
        </p>

        <input
          type="text"
          value={confirmName}
          onChange={(e) => setConfirmName(e.target.value)}
          placeholder={workspace.name}
          className="input-field mb-4 text-sm"
          autoFocus
        />

        {error && (
          <div className="mb-4 rounded-xl border border-red-300 bg-red-50 p-3 text-xs text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-300">
            {error}
          </div>
        )}

        <div className="flex justify-end gap-2">
          <button type="button" onClick={onClose} className="btn-ghost text-sm" disabled={loading}>
            Cancelar
          </button>
          <button
            type="button"
            onClick={handleDelete}
            disabled={!matches || loading}
            className="btn-danger text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Eliminando...' : 'Eliminar entorno'}
          </button>
        </div>
      </div>
    </div>
  );
}

export function ManageWorkspacesModal({ isOpen, onClose }) {
  const { workspaces } = useWorkspace();
  const [editingWorkspace, setEditingWorkspace] = useState(null);
  const [deletingWorkspace, setDeletingWorkspace] = useState(null);

  if (!isOpen) return null;

  return (
    <>
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm">
        <div className="glass-card w-full max-w-lg p-6">
          <div className="flex items-center justify-between pb-3">
            <h3 className="text-lg font-bold text-slate-800 dark:text-gray-100">Administrar entornos</h3>
            <button onClick={onClose} className="text-slate-400 hover:text-slate-600 dark:hover:text-gray-200">
              <X className="h-5 w-5" />
            </button>
          </div>

          <p className="mb-4 text-xs text-slate-500 dark:text-gray-400">
            Renombrar o cambiar el color está siempre permitido. Solo se puede eliminar un entorno inactivo.
          </p>

          <div className="max-h-80 space-y-2 overflow-y-auto pr-1">
            {workspaces.map((w) => {
              const canDelete = !w.is_active && workspaces.length > 1;
              return (
                <div
                  key={w.id}
                  className="flex items-center justify-between rounded-xl border border-slate-200/60 bg-slate-50/50 p-3 dark:border-white/5 dark:bg-white/[0.02]"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className="flex h-8 w-8 items-center justify-center rounded-lg text-sm font-bold text-white shadow-sm"
                      style={{ backgroundColor: w.color }}
                    >
                      {w.name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-800 dark:text-gray-200">{w.name}</span>
                        {w.is_active ? (
                          <span className="badge-success text-[10px]">● Activo</span>
                        ) : (
                          <span className="badge-locked text-[10px]">Inactivo</span>
                        )}
                      </div>
                      <span className="text-xs text-slate-500 dark:text-gray-400">
                        {w.player_count} {w.player_count === 1 ? 'jugador' : 'jugadores'}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setEditingWorkspace(w)}
                      className="btn-ghost px-2.5 py-1 text-xs"
                    >
                      Editar
                    </button>
                    <button
                      type="button"
                      onClick={() => setDeletingWorkspace(w)}
                      disabled={!canDelete}
                      className="btn-danger px-2.5 py-1 text-xs disabled:opacity-40 disabled:cursor-not-allowed"
                      title={!canDelete ? (w.is_active ? 'No se puede eliminar el entorno activo' : 'No se puede eliminar el último entorno') : 'Eliminar entorno'}
                    >
                      Eliminar
                    </button>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="flex justify-end pt-4">
            <button type="button" onClick={onClose} className="btn-ghost text-sm">
              Cerrar
            </button>
          </div>
        </div>
      </div>

      <EditWorkspaceModal
        isOpen={Boolean(editingWorkspace)}
        workspace={editingWorkspace}
        onClose={() => setEditingWorkspace(null)}
      />

      <DeleteWorkspaceModal
        isOpen={Boolean(deletingWorkspace)}
        workspace={deletingWorkspace}
        onClose={() => setDeletingWorkspace(null)}
      />
    </>
  );
}

export function ConfirmActivateModal({ isOpen, workspace, onClose }) {
  const { workspaces, refresh } = useWorkspace();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen || !workspace) return null;

  const currentActive = workspaces.find((w) => w.is_active && w.id !== workspace.id);

  async function handleActivate() {
    setLoading(true);
    setError('');
    try {
      await activateWorkspace(workspace.id);
      await refresh(workspace.id);
      onClose();
    } catch (err) {
      setError(err.message || 'Error al activar el entorno');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm">
      <div className="glass-card w-full max-w-md p-6">
        <div className="flex items-center justify-between pb-3">
          <h3 className="text-lg font-bold text-slate-800 dark:text-gray-100">
            ¿Activar «{workspace.name}»?
          </h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 dark:hover:text-gray-200">
            <X className="h-5 w-5" />
          </button>
        </div>

        <p className="mb-2 text-sm text-slate-600 dark:text-gray-300">
          Solo los jugadores de «{workspace.name}» podrán entrar al juego.
        </p>

        {currentActive && (
          <p className="mb-4 text-xs text-amber-700 dark:text-amber-300">
            Los de «{currentActive.name}» quedarán fuera. Quien esté jugando ahora saldrá en menos de medio minuto, con lo que ya tenía guardado intacto.
          </p>
        )}

        {error && (
          <div className="mb-4 rounded-xl border border-red-300 bg-red-50 p-3 text-xs text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-300">
            {error}
          </div>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={onClose} className="btn-ghost text-sm" disabled={loading}>
            Cancelar
          </button>
          <button type="button" onClick={handleActivate} className="btn-primary text-sm" disabled={loading}>
            {loading ? 'Activando...' : `Activar «${workspace.name}»`}
          </button>
        </div>
      </div>
    </div>
  );
}

export function ConfirmDeactivateModal({ isOpen, workspace, onClose }) {
  const { refresh } = useWorkspace();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen || !workspace) return null;

  async function handleDeactivate() {
    setLoading(true);
    setError('');
    try {
      await deactivateWorkspace(workspace.id);
      await refresh(workspace.id);
      onClose();
    } catch (err) {
      setError(err.message || 'Error al desactivar el entorno');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm">
      <div className="glass-card w-full max-w-md p-6">
        <div className="flex items-center justify-between pb-3">
          <h3 className="text-lg font-bold text-slate-800 dark:text-gray-100">
            ¿Desactivar «{workspace.name}»?
          </h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 dark:hover:text-gray-200">
            <X className="h-5 w-5" />
          </button>
        </div>

        <p className="mb-2 text-sm text-slate-600 dark:text-gray-300">
          No quedará ningún entorno activo: el juego se cerrará para todos los estudiantes hasta que actives uno.
        </p>

        <p className="mb-4 text-xs text-slate-500 dark:text-gray-400">
          Los datos no se borran.
        </p>

        {error && (
          <div className="mb-4 rounded-xl border border-red-300 bg-red-50 p-3 text-xs text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-300">
            {error}
          </div>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={onClose} className="btn-ghost text-sm" disabled={loading}>
            Cancelar
          </button>
          <button type="button" onClick={handleDeactivate} className="btn-danger text-sm" disabled={loading}>
            {loading ? 'Desactivando...' : 'Desactivar'}
          </button>
        </div>
      </div>
    </div>
  );
}
