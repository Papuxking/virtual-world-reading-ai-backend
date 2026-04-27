-- ============================================================================
-- 002_questions_schema.sql — Tablas de preguntas y respuestas
-- Ejecutado después de 001_schema.sql (orden alfabético)
-- ============================================================================

-- Agregar campo 'type' (subtipo textual) a readings — opcional
ALTER TABLE readings ADD COLUMN IF NOT EXISTS type VARCHAR(100) DEFAULT NULL;

-- Tabla de preguntas (1:N con readings)
CREATE TABLE IF NOT EXISTS questions (
    id                   SERIAL      PRIMARY KEY,
    reading_id           INTEGER     NOT NULL REFERENCES readings(id) ON DELETE CASCADE,
    question_number      SMALLINT    NOT NULL,
    comprehension_level  VARCHAR(20) NOT NULL
                         CHECK (comprehension_level IN ('Literal', 'Inferencial', 'Critico')),
    question_text        TEXT        NOT NULL,
    correct_answer       CHAR(1)     NOT NULL CHECK (correct_answer IN ('A','B','C','D')),
    justification        TEXT
);

CREATE INDEX IF NOT EXISTS idx_questions_reading
    ON questions (reading_id);

CREATE INDEX IF NOT EXISTS idx_questions_level
    ON questions (comprehension_level);

-- Tabla de opciones de respuesta (1:N con questions)
CREATE TABLE IF NOT EXISTS answers (
    id           SERIAL  PRIMARY KEY,
    question_id  INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    letter       CHAR(1) NOT NULL CHECK (letter IN ('A','B','C','D')),
    answer_text  TEXT    NOT NULL,
    UNIQUE(question_id, letter)
);

CREATE INDEX IF NOT EXISTS idx_answers_question
    ON answers (question_id);
