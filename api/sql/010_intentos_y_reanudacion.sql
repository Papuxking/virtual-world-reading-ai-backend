-- ============================================================================
-- 010: Intentos por tipología y lectura en curso reanudable
-- attempts_used cuenta las lecturas de progresión terminadas en cada tipología
-- (5 como máximo para aprobarla). Empieza en 0 para todos: los intentos se
-- cuentan desde que se aplica esta migración.
-- reading_seconds / total_seconds acumulan el tiempo de una lectura a medias
-- entre interrupciones. La lectura en curso deja de caducar.
-- Idempotente. La API lo aplica al arrancar (esquema.aplicar_migraciones); en
-- instalaciones nuevas, si initdb lo ejecuta antes de que existan las tablas,
-- los IF EXISTS lo dejan sin efecto y las columnas llegan con create_all.
-- ============================================================================

ALTER TABLE IF EXISTS player_typology_progress
    ADD COLUMN IF NOT EXISTS attempts_used INTEGER NOT NULL DEFAULT 0;
ALTER TABLE IF EXISTS active_readings
    ADD COLUMN IF NOT EXISTS reading_seconds INTEGER NOT NULL DEFAULT 0;
ALTER TABLE IF EXISTS active_readings
    ADD COLUMN IF NOT EXISTS total_seconds INTEGER NOT NULL DEFAULT 0;
UPDATE active_readings SET expires_at = NULL WHERE expires_at IS NOT NULL;
