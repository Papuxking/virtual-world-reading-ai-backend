-- Migración: Crear tabla active_readings
-- Almacena el estado de lectura activa por jugador/slot
-- Solo puede haber una lectura activa por jugador por slot (UNIQUE constraint)

CREATE TABLE IF NOT EXISTS active_readings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    slot_id INTEGER NOT NULL REFERENCES player_slots(id) ON DELETE CASCADE,
    reading_id INTEGER NOT NULL REFERENCES readings(id) ON DELETE CASCADE,
    typology VARCHAR(50) NOT NULL,
    current_level_index INTEGER NOT NULL DEFAULT 0,
    current_question_index INTEGER NOT NULL DEFAULT 0,
    reading_completed BOOLEAN NOT NULL DEFAULT FALSE,
    session_score INTEGER NOT NULL DEFAULT 0,
    results_json TEXT DEFAULT '[]',
    tools_used_json TEXT DEFAULT '{"highlight":false,"underline":false,"notes":false}',
    reading_start_time VARCHAR(50) DEFAULT '0',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '24 hours'),
    UNIQUE(user_id, slot_id)
);

-- Índice para consultas rápidas por usuario
CREATE INDEX IF NOT EXISTS idx_active_readings_user_slot ON active_readings(user_id, slot_id);
