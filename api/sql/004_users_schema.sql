-- ============================================================================
-- 004_users_schema.sql — Tabla de usuarios para autenticación
-- Sistema de login con correo + contraseña (bcrypt + JWT)
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id              SERIAL        PRIMARY KEY,
    email           VARCHAR(255)  NOT NULL UNIQUE,
    hashed_password VARCHAR(255)  NOT NULL,
    display_name    VARCHAR(100)  NOT NULL,
    character       VARCHAR(10)   DEFAULT 'male'
                    CHECK (character IN ('male', 'women')),
    is_active       BOOLEAN       DEFAULT TRUE,
    is_admin        BOOLEAN       DEFAULT FALSE,
    created_at      TIMESTAMPTZ   DEFAULT NOW(),
    last_login_at   TIMESTAMPTZ   DEFAULT NULL
);

CREATE INDEX IF NOT EXISTS idx_users_email
    ON users (email);

-- Migrar user_readings para usar FK a users
-- (No se altera la tabla existente para no romper datos,
--  la relación se hace por user_id numérico en las nuevas tablas)
