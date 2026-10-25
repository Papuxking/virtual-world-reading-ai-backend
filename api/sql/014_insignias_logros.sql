-- ============================================================================
-- 014: Insignias dibujadas para los logros, y nombres sin emoji
-- Los logros se representaban con emojis del sistema, que desentonan con el
-- pixel art del juego. Ahora cada uno tiene su insignia de 32x32 en
-- /static/medals/. El emoji se queda en medal_placeholder_emoji como respaldo
-- por si la imagen no carga.
-- De paso se quita el emoji incrustado en el nombre: ya lo cuenta la insignia,
-- y repetirlo al lado quedaba redundante.
-- Idempotente: solo escribe donde el valor aun no es el esperado. La API lo
-- aplica al arrancar (esquema.aplicar_migraciones).
-- ============================================================================

UPDATE achievement_catalog SET medal_image_path = '/static/medals/' || id || '.png?v=2'
 WHERE id IN ('first_reading', 'improvement', 'explorer', 'avid_reader', 'star_literal',
              'perfectionist', 'star_inferencial', 'centurion', 'star_critico', 'half_millennium')
   AND medal_image_path IS DISTINCT FROM '/static/medals/' || id || '.png?v=2';

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
