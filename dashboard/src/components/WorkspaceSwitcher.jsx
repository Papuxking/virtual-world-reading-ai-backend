import React, { useState, useRef, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ChevronDown, Check, Plus, Settings } from 'lucide-react';
import { useWorkspace } from '../context/WorkspaceContext';
import {
  NewWorkspaceModal,
  ManageWorkspacesModal,
  ConfirmActivateModal,
  ConfirmDeactivateModal,
} from './WorkspaceDialogs';

export default function WorkspaceSwitcher() {
  const { workspaces, viewed, selectWorkspace, loading } = useWorkspace();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [newModalOpen, setNewModalOpen] = useState(false);
  const [manageModalOpen, setManageModalOpen] = useState(false);
  const [activateTarget, setActivateTarget] = useState(null);
  const [deactivateTarget, setDeactivateTarget] = useState(null);

  const dropdownRef = useRef(null);
  const location = useLocation();
  const navigate = useNavigate();

  // Cerrar al hacer clic fuera
  useEffect(() => {
    function handleClickOutside(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setDropdownOpen(false);
      }
    }
    if (dropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [dropdownOpen]);

  function handleSelect(w) {
    selectWorkspace(w.id);
    setDropdownOpen(false);
    if (location.pathname.startsWith('/players/')) {
      navigate('/');
    }
  }

  function handleToggleActive(e) {
    e.stopPropagation();
    if (!viewed) return;
    if (viewed.is_active) {
      setDeactivateTarget(viewed);
    } else {
      setActivateTarget(viewed);
    }
  }

  // Estado sin entornos
  if (!loading && workspaces.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-slate-300 p-3 text-center dark:border-white/10">
        <p className="mb-2 text-xs font-semibold text-slate-600 dark:text-gray-300">Sin entornos</p>
        <button
          type="button"
          onClick={() => setNewModalOpen(true)}
          className="btn-primary w-full py-1.5 text-xs font-semibold"
        >
          Crear entorno
        </button>
        <NewWorkspaceModal isOpen={newModalOpen} onClose={() => setNewModalOpen(false)} />
      </div>
    );
  }

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Tarjeta del selector (Opción A) */}
      <div
        onClick={() => setDropdownOpen((prev) => !prev)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') setDropdownOpen((prev) => !prev);
        }}
        className="flex cursor-pointer items-center justify-between gap-2.5 rounded-xl border border-slate-200/80 bg-slate-50/80 p-2.5 transition-all duration-200 hover:border-slate-300 dark:border-white/10 dark:bg-white/[0.04] dark:hover:border-white/20"
      >
        <div className="flex min-w-0 flex-1 items-center gap-2.5">
          {/* Avatar cuadrado con inicial sobre su color */}
          <div
            className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg text-sm font-bold text-white shadow-sm"
            style={{ backgroundColor: viewed?.color || '#059669' }}
          >
            {viewed?.name ? viewed.name.charAt(0).toUpperCase() : '?'}
          </div>

          <div className="min-w-0 flex-1">
            <h2 className="truncate text-xs font-bold text-slate-800 dark:text-gray-100">
              {viewed?.name || 'Seleccionar entorno'}
            </h2>
            <p className="text-[11px] text-slate-500 dark:text-gray-400">
              {viewed ? `${viewed.player_count} ${viewed.player_count === 1 ? 'jugador' : 'jugadores'}` : ''}
            </p>
          </div>
        </div>

        {/* Interruptor ACTIVO / INACTIVO */}
        {viewed && (
          <button
            type="button"
            onClick={handleToggleActive}
            title={viewed.is_active ? 'Desactivar entorno' : 'Activar entorno'}
            className={`flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider transition-colors ${
              viewed.is_active
                ? 'bg-emerald-500/20 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300 hover:bg-emerald-500/30'
                : 'bg-slate-200 text-slate-600 dark:bg-white/10 dark:text-gray-400 hover:bg-slate-300 dark:hover:bg-white/15'
            }`}
          >
            <span
              className={`h-1.5 w-1.5 rounded-full ${
                viewed.is_active ? 'bg-emerald-500' : 'bg-slate-400 dark:bg-gray-500'
              }`}
            />
            {viewed.is_active ? 'ACTIVO' : 'INACTIVO'}
          </button>
        )}

        <ChevronDown
          className={`h-4 w-4 flex-shrink-0 text-slate-400 transition-transform duration-200 ${
            dropdownOpen ? 'rotate-180' : ''
          }`}
        />
      </div>

      {/* Menú desplegable */}
      {dropdownOpen && (
        <div className="absolute left-0 right-0 top-full z-40 mt-1.5 overflow-hidden rounded-xl border border-slate-200 bg-white p-1.5 shadow-xl dark:border-white/10 dark:bg-surface-800 animate-fade-in">
          <div className="px-2.5 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-gray-400">
            Entornos
          </div>

          <div className="max-h-56 space-y-0.5 overflow-y-auto">
            {workspaces.map((w) => {
              const isSelected = viewed && viewed.id === w.id;
              return (
                <button
                  key={w.id}
                  type="button"
                  onClick={() => handleSelect(w)}
                  className={`flex w-full items-center justify-between gap-2 rounded-lg px-2.5 py-2 text-left text-xs transition-colors ${
                    isSelected
                      ? 'bg-primary-500/10 font-semibold text-primary-700 dark:bg-primary-500/20 dark:text-primary-300'
                      : 'text-slate-700 hover:bg-slate-100 dark:text-gray-300 dark:hover:bg-white/5'
                  }`}
                >
                  <div className="flex min-w-0 items-center gap-2">
                    <div
                      className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded text-[11px] font-bold text-white shadow-sm"
                      style={{ backgroundColor: w.color }}
                    >
                      {w.name.charAt(0).toUpperCase()}
                    </div>
                    <span className="truncate">{w.name}</span>
                  </div>

                  <div className="flex items-center gap-1.5 flex-shrink-0">
                    <span
                      className={`text-[10px] font-medium ${
                        w.is_active
                          ? 'text-emerald-600 dark:text-emerald-400'
                          : 'text-slate-400 dark:text-gray-500'
                      }`}
                    >
                      {w.is_active ? '● Activo' : 'Inactivo'}
                    </span>
                    {isSelected && <Check className="h-3.5 w-3.5 text-primary-600 dark:text-primary-400" />}
                  </div>
                </button>
              );
            })}
          </div>

          <div className="my-1 border-t border-slate-200/80 dark:border-white/5" />

          <button
            type="button"
            onClick={() => {
              setDropdownOpen(false);
              setNewModalOpen(true);
            }}
            className="flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100 dark:text-gray-300 dark:hover:bg-white/5"
          >
            <Plus className="h-3.5 w-3.5 text-primary-500" />
            Nuevo entorno
          </button>

          <button
            type="button"
            onClick={() => {
              setDropdownOpen(false);
              setManageModalOpen(true);
            }}
            className="flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100 dark:text-gray-300 dark:hover:bg-white/5"
          >
            <Settings className="h-3.5 w-3.5 text-slate-400" />
            Administrar entornos
          </button>
        </div>
      )}

      {/* Modales */}
      <NewWorkspaceModal isOpen={newModalOpen} onClose={() => setNewModalOpen(false)} />
      <ManageWorkspacesModal isOpen={manageModalOpen} onClose={() => setManageModalOpen(false)} />
      <ConfirmActivateModal
        isOpen={Boolean(activateTarget)}
        workspace={activateTarget}
        onClose={() => setActivateTarget(null)}
      />
      <ConfirmDeactivateModal
        isOpen={Boolean(deactivateTarget)}
        workspace={deactivateTarget}
        onClose={() => setDeactivateTarget(null)}
      />
    </div>
  );
}
