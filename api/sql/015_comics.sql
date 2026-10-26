-- ============================================================================
-- 015: Progreso de la zona de comics
-- Al aprobar las cuatro tipologias de lectura se abre una sala de comics. El
-- profesor necesita ver desde el dashboard si esa recompensa funciona, asi que
-- el progreso se guarda en el servidor y no solo en el equipo del alumno:
--   * comic_progress: por jugador, slot y episodio, la ultima pagina vista y
--     si lo termino (reanudar la lectura y contar episodios completados).
--   * comic_zone_visits: por jugador y slot, cuantas veces entro a la sala y
--     cuando fue la primera y la ultima vez.
-- Ambas se borran con el usuario o con el slot (ON DELETE CASCADE).
-- Idempotente: solo crea lo que falta. La API lo aplica al arrancar
-- (esquema.aplicar_migraciones).
-- ============================================================================

CREATE TABLE IF NOT EXISTS comic_progress (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    slot_id     INTEGER NOT NULL REFERENCES player_slots(id) ON DELETE CASCADE,
    episode_id  VARCHAR(20) NOT NULL,
    last_page   INTEGER NOT NULL DEFAULT 0,
    finished    BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT now(),
    updated_at  TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT uq_user_slot_comic_episode UNIQUE (user_id, slot_id, episode_id)
);
CREATE INDEX IF NOT EXISTS ix_comic_progress_user_id ON comic_progress (user_id);
CREATE INDEX IF NOT EXISTS ix_comic_progress_slot_id ON comic_progress (slot_id);

CREATE TABLE IF NOT EXISTS comic_zone_visits (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    slot_id         INTEGER NOT NULL REFERENCES player_slots(id) ON DELETE CASCADE,
    visits          INTEGER NOT NULL DEFAULT 1,
    first_visit_at  TIMESTAMPTZ DEFAULT now(),
    last_visit_at   TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT uq_user_slot_comic_zone_visit UNIQUE (user_id, slot_id)
);
CREATE INDEX IF NOT EXISTS ix_comic_zone_visits_user_id ON comic_zone_visits (user_id);
CREATE INDEX IF NOT EXISTS ix_comic_zone_visits_slot_id ON comic_zone_visits (slot_id);
