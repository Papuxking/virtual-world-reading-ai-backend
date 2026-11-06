-- ============================================================================
-- 016: Encuesta obligatoria SUS + TAM antes de desbloquear los comics
-- Una respuesta inmutable por jugador y slot. Se conservan los 22 valores
-- crudos y las puntuaciones derivadas para auditoria y consulta del dashboard.
-- Idempotente: la API la aplica al arrancar desde esquema.py.
-- ============================================================================

CREATE TABLE IF NOT EXISTS technology_survey_responses (
    id                      SERIAL PRIMARY KEY,
    user_id                 INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    slot_id                 INTEGER NOT NULL REFERENCES player_slots(id) ON DELETE CASCADE,
    instrument_version      VARCHAR(40) NOT NULL DEFAULT 'sus10_tam12_v1',
    sus_1 SMALLINT NOT NULL CHECK (sus_1 BETWEEN 1 AND 5),
    sus_2 SMALLINT NOT NULL CHECK (sus_2 BETWEEN 1 AND 5),
    sus_3 SMALLINT NOT NULL CHECK (sus_3 BETWEEN 1 AND 5),
    sus_4 SMALLINT NOT NULL CHECK (sus_4 BETWEEN 1 AND 5),
    sus_5 SMALLINT NOT NULL CHECK (sus_5 BETWEEN 1 AND 5),
    sus_6 SMALLINT NOT NULL CHECK (sus_6 BETWEEN 1 AND 5),
    sus_7 SMALLINT NOT NULL CHECK (sus_7 BETWEEN 1 AND 5),
    sus_8 SMALLINT NOT NULL CHECK (sus_8 BETWEEN 1 AND 5),
    sus_9 SMALLINT NOT NULL CHECK (sus_9 BETWEEN 1 AND 5),
    sus_10 SMALLINT NOT NULL CHECK (sus_10 BETWEEN 1 AND 5),
    tam_pu_1 SMALLINT NOT NULL CHECK (tam_pu_1 BETWEEN 1 AND 7),
    tam_pu_2 SMALLINT NOT NULL CHECK (tam_pu_2 BETWEEN 1 AND 7),
    tam_pu_3 SMALLINT NOT NULL CHECK (tam_pu_3 BETWEEN 1 AND 7),
    tam_pu_4 SMALLINT NOT NULL CHECK (tam_pu_4 BETWEEN 1 AND 7),
    tam_pu_5 SMALLINT NOT NULL CHECK (tam_pu_5 BETWEEN 1 AND 7),
    tam_pu_6 SMALLINT NOT NULL CHECK (tam_pu_6 BETWEEN 1 AND 7),
    tam_peou_1 SMALLINT NOT NULL CHECK (tam_peou_1 BETWEEN 1 AND 7),
    tam_peou_2 SMALLINT NOT NULL CHECK (tam_peou_2 BETWEEN 1 AND 7),
    tam_peou_3 SMALLINT NOT NULL CHECK (tam_peou_3 BETWEEN 1 AND 7),
    tam_peou_4 SMALLINT NOT NULL CHECK (tam_peou_4 BETWEEN 1 AND 7),
    tam_peou_5 SMALLINT NOT NULL CHECK (tam_peou_5 BETWEEN 1 AND 7),
    tam_peou_6 SMALLINT NOT NULL CHECK (tam_peou_6 BETWEEN 1 AND 7),
    sus_score               DOUBLE PRECISION NOT NULL,
    tam_usefulness_score    DOUBLE PRECISION NOT NULL,
    tam_ease_score          DOUBLE PRECISION NOT NULL,
    submitted_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_user_slot_technology_survey UNIQUE (user_id, slot_id)
);
CREATE INDEX IF NOT EXISTS ix_technology_survey_user_id ON technology_survey_responses (user_id);
CREATE INDEX IF NOT EXISTS ix_technology_survey_slot_id ON technology_survey_responses (slot_id);
