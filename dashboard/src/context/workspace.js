import { createContext, useContext } from 'react';

// Contexto del entorno que se ve en el dashboard. El proveedor está en
// WorkspaceContext.jsx; aquí solo lo que no es un componente, para que la
// recarga en caliente de Vite siga funcionando.
export const WorkspaceContext = createContext(null);

// Colores que se pueden elegir para un entorno (mismo orden que la API).
export const PALETA_ENTORNOS = [
  '#059669',
  '#d97706',
  '#2563eb',
  '#7c3aed',
  '#db2777',
  '#0891b2',
];

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error('useWorkspace debe usarse dentro de un WorkspaceProvider');
  }
  return context;
}
