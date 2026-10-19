import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { getWorkspaces, setViewedWorkspace, getViewedWorkspace } from '../services/api';

const WorkspaceContext = createContext(null);

export const PALETA_ENTORNOS = [
  '#059669',
  '#d97706',
  '#2563eb',
  '#7c3aed',
  '#db2777',
  '#0891b2',
];

export function WorkspaceProvider({ children }) {
  const [workspaces, setWorkspaces] = useState([]);
  const [viewed, setViewed] = useState(null);
  const [loading, setLoading] = useState(true);

  const _elegirPorDefecto = (lista, preferId = null) => {
    if (!lista || lista.length === 0) return null;
    const buscado = preferId !== null ? lista.find(w => w.id === preferId) : null;
    if (buscado) return buscado;
    const recordadoId = getViewedWorkspace();
    const recordado = recordadoId !== null ? lista.find(w => w.id === recordadoId) : null;
    if (recordado) return recordado;
    const activo = lista.find(w => w.is_active);
    if (activo) return activo;
    return lista[0];
  };

  const refresh = useCallback(async (preferId = null) => {
    try {
      setLoading(true);
      const lista = await getWorkspaces();
      setWorkspaces(lista);
      const sel = _elegirPorDefecto(lista, preferId);
      setViewed(sel);
      setViewedWorkspace(sel ? sel.id : null);
    } catch (err) {
      console.error('Error al cargar entornos:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const selectWorkspace = useCallback((id) => {
    const sel = workspaces.find(w => w.id === Number(id)) || null;
    setViewed(sel);
    setViewedWorkspace(sel ? sel.id : null);
  }, [workspaces]);

  useEffect(() => {
    refresh();

    const handleMissing = () => {
      refresh();
    };

    window.addEventListener('vw:workspace-missing', handleMissing);
    return () => {
      window.removeEventListener('vw:workspace-missing', handleMissing);
    };
  }, [refresh]);

  return (
    <WorkspaceContext.Provider value={{ workspaces, viewed, loading, selectWorkspace, refresh }}>
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error('useWorkspace debe usarse dentro de un WorkspaceProvider');
  }
  return context;
}
