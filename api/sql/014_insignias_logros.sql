-- ============================================================================
-- 014: Nombres de logro sin emoji, e insignias servidas por el juego
-- Los logros se representaban con emojis del sistema, que desentonan con el
-- pixel art. Ahora cada uno tiene su insignia de 32x32, pero vive en el propio
-- juego (res://assets/Medals/): es arte fijo de 1 KB igual para todos, y
-- pedirlo por red solo anadia dependencia de conexion y un parpadeo al abrir el
-- panel.
-- Por eso medal_image_path vuelve a quedar vacio: ahora significa «un
-- administrador subio una insignia propia para este logro», y solo entonces el
-- juego la usa en lugar de la suya.
-- De paso se quita el emoji incrustado en el nombre: ya lo cuenta la insignia.
-- Idempotente: solo escribe donde el valor aun no es el esperado. La API lo
-- aplica al arrancar (esquema.aplicar_migraciones).
-- ============================================================================

-- Solo las rutas por defecto que llego a poner una version anterior de esta
-- migracion (?v=1 y ?v=2). Una subida real del dashboard lleva una marca de
-- tiempo, asi que no la toca.
UPDATE achievement_catalog SET medal_image_path = NULL
 WHERE medal_image_path IN ('/static/medals/' || id || '.png?v=1',
                            '/static/medals/' || id || '.png?v=2');

-- Reparacion: una version anterior de esta migracion piso la ruta de los diez
-- logros sin mirar si alguno tenia ya una insignia subida. El historial si lo
-- sabe, asi que se devuelve la que esta marcada como vigente.
UPDATE achievement_catalog SET medal_image_path = h.image_path
  FROM medal_image_history h
 WHERE h.achievement_id = achievement_catalog.id
   AND h.is_current
   AND achievement_catalog.medal_image_path IS DISTINCT FROM h.image_path;

UPDATE achievement_catalog SET name = 'Primera lectura'       WHERE id = 'first_reading'    AND name <> 'Primera lectura';
UPDATE achievement_catalog SET name = 'En mejora'             WHERE id = 'improvement'      AND name <> 'En mejora';
UPDATE achievement_catalog SET name = 'Explorador'            WHERE id = 'explorer'         AND name <> 'Explorador';
UPDATE achievement_catalog SET name = 'Lector ávido'          WHERE id = 'avid_reader'      AND name <> 'Lector ávido';
UPDATE achievement_catalog SET name = 'Estrella literal'      WHERE id = 'star_literal'     AND name <> 'Estrella literal';
UPDATE achievement_catalog SET name = 'Perfeccionista'        WHERE id = 'perfectionist'    AND name <> 'Perfeccionista';
UPDATE achievement_catalog SET name = 'Estrella inferencial'  WHERE id = 'star_inferencial' AND name <> 'Estrella inferencial';
UPDATE achievement_catalog SET name = 'Centurión'             WHERE id = 'centurion'        AND name <> 'Centurión';
UPDATE achievement_catalog SET name = 'Estrella crítica'      WHERE id = 'star_critico'     AND name <> 'Estrella crítica';
UPDATE achievement_catalog SET name = 'Medio milenio'         WHERE id = 'half_millennium'  AND name <> 'Medio milenio';

-- Los logros ya desbloqueados guardaron el nombre con emoji en su momento; el
-- historial del dashboard los lee de aquí, así que se limpian también.
UPDATE player_achievements SET achievement_name = c.name
  FROM achievement_catalog c
 WHERE player_achievements.achievement_id = c.id
   AND player_achievements.achievement_name <> c.name;
