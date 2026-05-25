-- 007_session_version_medals.sql
-- Añade la columna session_version para el control de slots en tiempo real
-- y medal_placeholder_emoji para las medallas.

ALTER TABLE users ADD COLUMN IF NOT EXISTS session_version INTEGER NOT NULL DEFAULT 1;

ALTER TABLE achievement_catalog ADD COLUMN IF NOT EXISTS medal_placeholder_emoji VARCHAR(10) NOT NULL DEFAULT '🏅';
