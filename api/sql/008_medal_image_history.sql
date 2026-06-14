-- ============================================================================
-- 008: Historial de imágenes de medallas
-- Almacena versiones anteriores de imágenes de medallas para el dashboard admin.
-- ============================================================================

CREATE TABLE IF NOT EXISTS medal_image_history (
    id SERIAL PRIMARY KEY,
    achievement_id VARCHAR(50) NOT NULL REFERENCES achievement_catalog(id) ON DELETE CASCADE,
    image_path VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    file_size_bytes INTEGER,
    uploaded_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_current BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_medal_history_achievement ON medal_image_history(achievement_id);
CREATE INDEX IF NOT EXISTS idx_medal_history_current ON medal_image_history(achievement_id, is_current);
