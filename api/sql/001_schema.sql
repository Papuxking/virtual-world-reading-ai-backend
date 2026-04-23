-- ============================================================================
-- 001_schema.sql — DDL para el sistema de lecturas
-- Base de datos: godot_readings
-- Ejecutado automáticamente por PostgreSQL al inicializar el contenedor
-- ============================================================================

-- Tabla principal de lecturas
CREATE TABLE IF NOT EXISTS readings (
    id          SERIAL       PRIMARY KEY,
    title       VARCHAR(255) NOT NULL,
    typology    VARCHAR(50)  NOT NULL
                CHECK (typology IN (
                    'Descriptivo',
                    'Narrativo',
                    'Argumentativo',
                    'Expositivo',
                    'Instructivo'
                )),
    content     TEXT         NOT NULL,
    created_at  TIMESTAMPTZ  DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  DEFAULT NOW()
);

-- Índice para filtrado rápido por tipología
CREATE INDEX IF NOT EXISTS idx_readings_typology
    ON readings (typology);

-- Índices GIN para búsqueda full-text en español
CREATE INDEX IF NOT EXISTS idx_readings_title_fts
    ON readings USING gin (to_tsvector('spanish', title));

CREATE INDEX IF NOT EXISTS idx_readings_content_fts
    ON readings USING gin (to_tsvector('spanish', content));

-- ============================================================================
-- Tabla para no-repetición por usuario (futura activación)
-- Registra qué lecturas ha visto cada usuario para evitar repeticiones.
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_readings (
    id         SERIAL       PRIMARY KEY,
    user_id    VARCHAR(100) NOT NULL,   -- UUID del dispositivo, login futuro, etc.
    reading_id INTEGER      NOT NULL REFERENCES readings(id) ON DELETE CASCADE,
    read_at    TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE(user_id, reading_id)
);

CREATE INDEX IF NOT EXISTS idx_user_readings_user
    ON user_readings (user_id);
