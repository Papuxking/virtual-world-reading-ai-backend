-- Migración 003: agrega external_id para sincronización con LecturaIA
-- Ejecutar manualmente si la base de datos ya existe:
--   docker exec -i <db_container> psql -U DB-virtual-world-reading-ai -d godot_readings < 003_add_external_id.sql

ALTER TABLE readings ADD COLUMN IF NOT EXISTS external_id INTEGER;
CREATE INDEX IF NOT EXISTS ix_readings_external_id ON readings(external_id);
