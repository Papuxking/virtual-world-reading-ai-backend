-- ============================================================================
-- 009: Zona de práctica
-- Marca las lecturas exclusivas de práctica y las sesiones jugadas en ella.
-- Idempotente. En instalaciones nuevas lo ejecuta initdb; en bases existentes
-- lo aplica migrate_practice_mode.py (o psql, antes de desplegar la API nueva).
-- ============================================================================

ALTER TABLE readings        ADD COLUMN IF NOT EXISTS is_practice BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE player_sessions ADD COLUMN IF NOT EXISTS is_practice BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_readings_typology_practice
    ON readings (typology, is_practice);
CREATE INDEX IF NOT EXISTS idx_player_sessions_practice
    ON player_sessions (user_id, slot_id, is_practice);
