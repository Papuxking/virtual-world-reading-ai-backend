-- ============================================================================
-- 006_slots_passwords_catalog.sql — Slots, contraseñas y catálogo de logros
-- ============================================================================

-- ── 1. Tabla de Catálogo de Logros y Medallas ────────────────────────────────
CREATE TABLE IF NOT EXISTS achievement_catalog (
    id                VARCHAR(50) PRIMARY KEY,
    name              VARCHAR(100) NOT NULL,
    description       TEXT NOT NULL,
    how_to_unlock     TEXT NOT NULL,
    category          VARCHAR(30) NOT NULL,
    icon              VARCHAR(10) DEFAULT '🏆',
    medal_name        VARCHAR(100) NOT NULL,
    medal_tier        VARCHAR(20) NOT NULL DEFAULT 'bronce' CHECK (medal_tier IN ('bronce', 'plata', 'oro', 'platino')),
    medal_description TEXT,
    medal_image_path  VARCHAR(255) DEFAULT NULL,
    display_order     SMALLINT DEFAULT 0,
    is_active         BOOLEAN DEFAULT TRUE,
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    updated_at        TIMESTAMPTZ DEFAULT NOW()
);

-- ── 2. Tabla de Slots de Sesiones de Jugadores ──────────────────────────────
CREATE TABLE IF NOT EXISTS player_slots (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    slot_number     SMALLINT NOT NULL CHECK (slot_number BETWEEN 1 AND 4),
    label           VARCHAR(50) DEFAULT 'Sesión 1',
    is_active       BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    created_by      INTEGER REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE(user_id, slot_number)
);

CREATE INDEX IF NOT EXISTS idx_player_slots_user ON player_slots(user_id);
CREATE INDEX IF NOT EXISTS idx_player_slots_active ON player_slots(user_id, is_active);

-- ── 3. Modificaciones a la Tabla de Usuarios ─────────────────────────────────
ALTER TABLE users ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN DEFAULT FALSE;

-- ── 4. Agregar slot_id a las tablas de progreso ──────────────────────────────
ALTER TABLE player_sessions ADD COLUMN IF NOT EXISTS slot_id INTEGER REFERENCES player_slots(id) ON DELETE CASCADE;
ALTER TABLE player_notes ADD COLUMN IF NOT EXISTS slot_id INTEGER REFERENCES player_slots(id) ON DELETE CASCADE;
ALTER TABLE player_typology_progress ADD COLUMN IF NOT EXISTS slot_id INTEGER REFERENCES player_slots(id) ON DELETE CASCADE;
ALTER TABLE player_achievements ADD COLUMN IF NOT EXISTS slot_id INTEGER REFERENCES player_slots(id) ON DELETE CASCADE;

-- ── 5. Migración de Datos Existentes ──────────────────────────────────────────
-- Crear slot 1 activo para todos los usuarios que no sean administradores
INSERT INTO player_slots (user_id, slot_number, label, is_active, created_at)
SELECT id, 1, 'Sesión 1', TRUE, COALESCE(created_at, NOW())
FROM users
WHERE is_admin = FALSE
ON CONFLICT (user_id, slot_number) DO NOTHING;

-- Vincular player_sessions existentes al slot 1
UPDATE player_sessions ps
SET slot_id = s.id
FROM player_slots s
WHERE ps.user_id = s.user_id AND s.slot_number = 1 AND ps.slot_id IS NULL;

-- Vincular player_notes existentes al slot 1
UPDATE player_notes pn
SET slot_id = s.id
FROM player_slots s
WHERE pn.user_id = s.user_id AND s.slot_number = 1 AND pn.slot_id IS NULL;

-- Vincular player_typology_progress existentes al slot 1
UPDATE player_typology_progress pt
SET slot_id = s.id
FROM player_slots s
WHERE pt.user_id = s.user_id AND s.slot_number = 1 AND pt.slot_id IS NULL;

-- Vincular player_achievements existentes al slot 1
UPDATE player_achievements pa
SET slot_id = s.id
FROM player_slots s
WHERE pa.user_id = s.user_id AND s.slot_number = 1 AND pa.slot_id IS NULL;

-- ── 6. Restricción NOT NULL y Actualización de Restricciones Unique ──────────

-- Cambiar columnas slot_id a NOT NULL para registros futuros
ALTER TABLE player_sessions ALTER COLUMN slot_id SET NOT NULL;
ALTER TABLE player_notes ALTER COLUMN slot_id SET NOT NULL;
ALTER TABLE player_typology_progress ALTER COLUMN slot_id SET NOT NULL;
ALTER TABLE player_achievements ALTER COLUMN slot_id SET NOT NULL;

-- Actualizar restricciones Unique en player_typology_progress
ALTER TABLE player_typology_progress DROP CONSTRAINT IF EXISTS player_typology_progress_user_id_typology_key;
ALTER TABLE player_typology_progress ADD CONSTRAINT player_typology_progress_user_slot_typology_key UNIQUE (user_id, slot_id, typology);

-- Actualizar restricciones Unique en player_achievements
ALTER TABLE player_achievements DROP CONSTRAINT IF EXISTS player_achievements_user_id_achievement_id_key;
ALTER TABLE player_achievements ADD CONSTRAINT player_achievements_user_slot_achievement_key UNIQUE (user_id, slot_id, achievement_id);

-- Índices compuestos para optimizar consultas filtradas por slot
CREATE INDEX IF NOT EXISTS idx_player_sessions_slot ON player_sessions(slot_id);
CREATE INDEX IF NOT EXISTS idx_player_notes_slot ON player_notes(slot_id);
CREATE INDEX IF NOT EXISTS idx_player_typology_slot ON player_typology_progress(slot_id);
CREATE INDEX IF NOT EXISTS idx_player_achievements_slot ON player_achievements(slot_id);
