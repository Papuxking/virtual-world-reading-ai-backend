-- ============================================================================
-- 012: Conversaciones con el asistente IA
-- Cada interacción con el robot o el sabio guarda lo que preguntó el jugador y
-- lo que le respondió el tutor, para que el dashboard pueda mostrarlo. Las
-- interacciones anteriores se quedan sin texto (NULL): solo se contaban.
-- Idempotente. La API lo aplica al arrancar (esquema.aplicar_migraciones); en
-- instalaciones nuevas initdb no encuentra la tabla (la crea la API) y no hace
-- nada.
-- ============================================================================

ALTER TABLE IF EXISTS npc_interactions ADD COLUMN IF NOT EXISTS user_message TEXT;
ALTER TABLE IF EXISTS npc_interactions ADD COLUMN IF NOT EXISTS assistant_reply TEXT;
