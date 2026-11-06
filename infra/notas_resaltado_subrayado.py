"""Muestra en el dashboard lo resaltado y lo subrayado por el alumno.

El juego guarda cada fragmento resaltado como nota de tipo 'annotation' y cada
fragmento subrayado como 'margin_note'. Este script cambia, en
PlayerDetailPage.jsx, la etiqueta en crudo por «Resaltado» / «Subrayado» / «Nota»
y pinta el texto resaltado (fondo amarillo) o subrayado.

Uso: python3 notas_resaltado_subrayado.py /ruta/a/dashboard/src/pages/PlayerDetailPage.jsx
"""
import sys

ruta = sys.argv[1]
s = open(ruta, encoding="utf-8").read()

VIEJO_CHIP = """                                  <span className="px-1.5 py-0.5 rounded text-[8px] font-extrabold bg-primary-50 dark:bg-primary-500/10 text-primary-600 dark:text-primary-400 border border-primary-100 dark:border-primary-500/20">
                                    {note.note_type}
                                  </span>"""
NUEVO_CHIP = """                                  <span className={`px-1.5 py-0.5 rounded text-[8px] font-extrabold border ${
                                    note.note_type === 'annotation'
                                      ? 'bg-yellow-100 dark:bg-yellow-500/20 text-yellow-800 dark:text-yellow-300 border-yellow-200 dark:border-yellow-500/30'
                                      : note.note_type === 'margin_note'
                                        ? 'bg-sky-100 dark:bg-sky-500/20 text-sky-800 dark:text-sky-300 border-sky-200 dark:border-sky-500/30'
                                        : 'bg-primary-50 dark:bg-primary-500/10 text-primary-600 dark:text-primary-400 border-primary-100 dark:border-primary-500/20'
                                  }`}>
                                    {note.note_type === 'annotation' ? 'Resaltado' : note.note_type === 'margin_note' ? 'Subrayado' : 'Nota'}
                                  </span>"""
VIEJO_TXT = """                                <p className="text-xs text-slate-600 dark:text-gray-300 leading-relaxed font-semibold whitespace-pre-wrap">
                                  {note.note_content}
                                </p>"""
NUEVO_TXT = """                                <p className="text-xs text-slate-600 dark:text-gray-300 leading-relaxed font-semibold whitespace-pre-wrap">
                                  {note.note_type === 'annotation' ? (
                                    <mark className="bg-yellow-200 dark:bg-yellow-500/40 text-slate-800 dark:text-yellow-50 rounded px-0.5">{note.note_content}</mark>
                                  ) : note.note_type === 'margin_note' ? (
                                    <span className="underline decoration-sky-500 decoration-2 underline-offset-2">{note.note_content}</span>
                                  ) : note.note_content}
                                </p>"""

if NUEVO_CHIP in s:
    print("Ya estaba aplicado.")
    sys.exit(0)
crlf = "\r\n" in s
s = s.replace("\r\n", "\n")
assert s.count(VIEJO_CHIP) == 1, "No encontré la etiqueta de la nota"
assert s.count(VIEJO_TXT) == 1, "No encontré el texto de la nota"
s = s.replace(VIEJO_CHIP, NUEVO_CHIP).replace(VIEJO_TXT, NUEVO_TXT)
if crlf:
    s = s.replace("\n", "\r\n")
open(ruta, "w", encoding="utf-8", newline="").write(s)
print("Aplicado.")
