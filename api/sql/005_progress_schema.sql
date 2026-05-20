-- ============================================================================
-- 005_progress_schema.sql — Tablas de progreso del jugador
-- Almacena sesiones, respuestas, herramientas, notas, progresión y logros
-- ============================================================================

-- ── Sesiones de juego completadas ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS player_sessions (
    id                    SERIAL        PRIMARY KEY,
    user_id               INTEGER       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reading_id            INTEGER       NOT NULL REFERENCES readings(id) ON DELETE CASCADE,
    typology              VARCHAR(50)   NOT NULL,
    session_score         INTEGER       NOT NULL DEFAULT 0,
    reading_time_seconds  INTEGER       DEFAULT NULL,
    total_time_seconds    INTEGER       DEFAULT NULL,
    is_perfect            BOOLEAN       DEFAULT FALSE,
    correct_count         INTEGER       NOT NULL DEFAULT 0,
    incorrect_count       INTEGER       NOT NULL DEFAULT 0,
    tool_bonus            INTEGER       NOT NULL DEFAULT 0,
    started_at            TIMESTAMPTZ   DEFAULT NOW(),
    completed_at          TIMESTAMPTZ   DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_player_sessions_user
    ON player_sessions (user_id);

CREATE INDEX IF NOT EXISTS idx_player_sessions_typology
    ON player_sessions (typology);

CREATE INDEX IF NOT EXISTS idx_player_sessions_user_typology
    ON player_sessions (user_id, typology);


-- ── Respuestas individuales por sesión ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS player_answers (
    id                    SERIAL        PRIMARY KEY,
    session_id            INTEGER       NOT NULL REFERENCES player_sessions(id) ON DELETE CASCADE,
    question_id           INTEGER       NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    comprehension_level   VARCHAR(20)   NOT NULL,
    selected_answer       CHAR(1)       NOT NULL,
    correct_answer        CHAR(1)       NOT NULL,
    is_correct            BOOLEAN       NOT NULL,
    points_earned         INTEGER       NOT NULL DEFAULT 0,
    penalty_applied       INTEGER       NOT NULL DEFAULT 0,
    response_time_ms      INTEGER       DEFAULT NULL,
    answered_at           TIMESTAMPTZ   DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_player_answers_session
    ON player_answers (session_id);


-- ── Herramientas usadas por sesión ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS session_tools (
    id                SERIAL        PRIMARY KEY,
    session_id        INTEGER       NOT NULL REFERENCES player_sessions(id) ON DELETE CASCADE,
    tool_name         VARCHAR(30)   NOT NULL
                      CHECK (tool_name IN ('highlight', 'underline', 'notes')),
    was_used          BOOLEAN       NOT NULL DEFAULT FALSE,
    usage_count       INTEGER       NOT NULL DEFAULT 0,
    duration_seconds  INTEGER       DEFAULT NULL,
    UNIQUE(session_id, tool_name)
);

CREATE INDEX IF NOT EXISTS idx_session_tools_session
    ON session_tools (session_id);


-- ── Notas/apuntes del jugador (texto completo) ──────────────────────────────
CREATE TABLE IF NOT EXISTS player_notes (
    id              SERIAL        PRIMARY KEY,
    user_id         INTEGER       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reading_id      INTEGER       NOT NULL REFERENCES readings(id) ON DELETE CASCADE,
    session_id      INTEGER       REFERENCES player_sessions(id) ON DELETE SET NULL,
    note_content    TEXT          NOT NULL,
    note_type       VARCHAR(30)  NOT NULL DEFAULT 'free_text'
                    CHECK (note_type IN ('free_text', 'annotation', 'margin_note')),
    created_at      TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_player_notes_user
    ON player_notes (user_id);

CREATE INDEX IF NOT EXISTS idx_player_notes_reading
    ON player_notes (user_id, reading_id);


-- ── Progreso acumulado por tipología ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS player_typology_progress (
    id                  SERIAL        PRIMARY KEY,
    user_id             INTEGER       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    typology            VARCHAR(50)   NOT NULL,
    best_score          INTEGER       NOT NULL DEFAULT 0,
    total_sessions      INTEGER       NOT NULL DEFAULT 0,
    perfect_sessions    INTEGER       NOT NULL DEFAULT 0,
    is_unlocked         BOOLEAN       NOT NULL DEFAULT FALSE,
    first_completed_at  TIMESTAMPTZ   DEFAULT NULL,
    last_played_at      TIMESTAMPTZ   DEFAULT NULL,
    UNIQUE(user_id, typology)
);

CREATE INDEX IF NOT EXISTS idx_player_typology_progress_user
    ON player_typology_progress (user_id);


-- ── Logros desbloqueados ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS player_achievements (
    id                SERIAL        PRIMARY KEY,
    user_id           INTEGER       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    achievement_id    VARCHAR(50)   NOT NULL,
    achievement_name  VARCHAR(100)  NOT NULL,
    unlocked_at       TIMESTAMPTZ   DEFAULT NOW(),
    UNIQUE(user_id, achievement_id)
);

CREATE INDEX IF NOT EXISTS idx_player_achievements_user
    ON player_achievements (user_id);
