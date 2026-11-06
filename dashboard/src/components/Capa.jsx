import { createPortal } from 'react-dom';

// Fondo oscuro de un diálogo, dibujado directamente en <body>. Los diálogos de
// entornos se abren desde la barra lateral, que es sticky (y por tanto crea
// su propio contexto de apilamiento): dentro de ella, su z-50 quedaba por
// debajo de las tarjetas de la página.
export default function Capa({ children }) {
  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm">
      {children}
    </div>,
    document.body,
  );
}
