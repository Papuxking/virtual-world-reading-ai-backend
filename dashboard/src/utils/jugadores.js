/**
 * Utilidades para procesar, copiar y exportar listas de jugadores.
 */

/**
 * Parsea el texto ingresado por el usuario: un correo por línea con nombre opcional tras la primera coma.
 * @param {string} texto
 * @returns {Array<{ email: string, display_name: string | null }>}
 */
export function parsearLineas(texto) {
  if (!texto) return [];
  const lineas = texto.split(/\r?\n/);
  const resultado = [];
  for (const linea of lineas) {
    const recortada = linea.trim();
    if (!recortada) continue;
    const comaIdx = recortada.indexOf(',');
    if (comaIdx === -1) {
      resultado.push({
        email: recortada,
        display_name: null,
      });
    } else {
      const email = recortada.substring(0, comaIdx).trim();
      const nombre = recortada.substring(comaIdx + 1).trim();
      resultado.push({
        email,
        display_name: nombre ? nombre : null,
      });
    }
  }
  return resultado;
}

/**
 * Convierte una lista de jugadores a texto tabulado para el portapapeles.
 * @param {Array<{ email: string, display_name: string, temp_password: string }>} filas
 * @returns {string}
 */
export function aTexto(filas) {
  return filas
    .map((f) => `${f.email || ''}\t${f.display_name || ''}\t${f.temp_password || ''}`)
    .join('\n');
}

function escaparCsv(valor) {
  const str = valor !== null && valor !== undefined ? String(valor) : '';
  if (str.includes(',') || str.includes('"') || str.includes('\n') || str.includes('\r')) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

/**
 * Convierte una lista de jugadores a formato CSV con BOM UTF-8 para Excel.
 * @param {Array<{ email: string, display_name: string, temp_password: string }>} filas
 * @returns {string}
 */
export function aCsv(filas) {
  const cabecera = 'correo,nombre,contraseña temporal';
  const lineas = [cabecera];
  for (const f of filas) {
    const c = escaparCsv(f.email);
    const n = escaparCsv(f.display_name);
    const p = escaparCsv(f.temp_password);
    lineas.push(`${c},${n},${p}`);
  }
  return '\uFEFF' + lineas.join('\r\n');
}
