import { useState, useEffect, useCallback } from 'react';
import { getWorkspaces, setViewedWorkspace, getViewedWorkspace } from '../services/api';
import { WorkspaceContext } from './workspace';

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

  const aplicar = useCallback((lista, preferId = null) => {
    setWorkspaces(lista);
    const sel = _elegirPorDefecto(lista, preferId);
    setViewed(sel);
    setViewedWorkspace(sel ? sel.id : null);
  }, []);

  const refresh = useCallback(async (preferId = null) => {
    try {
      aplicar(await getWorkspaces(), preferId);
    } catch (err) {
      console.error('Error al cargar entornos:', err);
    } finally {
      setLoading(false);
    }
  }, [aplicar]);

  const selectWorkspace = useCallback((id) => {
    const sel = workspaces.find(w => w.id === Number(id)) || null;
    setViewed(sel);
    setViewedWorkspace(sel ? sel.id : null);
  }, [workspaces]);

  useEffect(() => {
    // Primera carga: el estado se actualiza cuando llega la respuesta.
    let vivo = true;
    getWorkspaces()
      .then((lista) => { if (vivo) aplicar(lista); })
      .catch((err) => console.error('Error al cargar entornos:', err))
      .finally(() => { if (vivo) setLoading(false); });

    const handleMissing = () => {
      refresh();
    };

    window.addEventListener('vw:workspace-missing', handleMissing);
    return () => {
      vivo = false;
      window.removeEventListener('vw:workspace-missing', handleMissing);
    };
  }, [aplicar, refresh]);

  return (
    <WorkspaceContext.Provider value={{ workspaces, viewed, loading, selectWorkspace, refresh }}>
      {children}
    </WorkspaceContext.Provider>
  );
}
