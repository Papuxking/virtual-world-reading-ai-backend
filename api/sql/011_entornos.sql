-- ============================================================================
-- 011: Entornos de trabajo
-- Cada cuenta de jugador pertenece a un entorno; como mucho uno está activo y
-- solo sus jugadores entran al juego. Los administradores no tienen entorno.
-- No crea ningún entorno ni toca las cuentas que ya existen: se quedan sin
-- entorno (no entran al juego ni salen en el dashboard) hasta que el admin
-- cree uno y agregue a los jugadores.
-- El correo deja de ser único en toda la tabla: lo es dentro de cada entorno,
-- y entre las cuentas sin entorno. Según cómo se creó la base, la unicidad
-- vieja es el índice ix_users_email (la API) o la restricción users_email_key
-- (initdb con 004_users_schema.sql): se quitan las dos.
-- Idempotente. La API lo aplica al arrancar (esquema.aplicar_migraciones); en
-- instalaciones nuevas también lo ejecuta initdb, ya con la tabla users creada.
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspaces (
    id          SERIAL      PRIMARY KEY,
    name        VARCHAR(40) NOT NULL,
    color       VARCHAR(7)  NOT NULL,
    is_active   BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_workspaces_nombre ON workspaces (lower(name));
CREATE UNIQUE INDEX IF NOT EXISTS ux_workspaces_un_activo ON workspaces (is_active) WHERE is_active;

ALTER TABLE IF EXISTS users
    ADD COLUMN IF NOT EXISTS workspace_id INTEGER REFERENCES workspaces(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS ix_users_workspace_id ON users (workspace_id);

ALTER TABLE IF EXISTS users DROP CONSTRAINT IF EXISTS users_email_key;
DROP INDEX IF EXISTS ix_users_email;
CREATE INDEX IF NOT EXISTS ix_users_email_login ON users (email);
CREATE UNIQUE INDEX IF NOT EXISTS ux_users_workspace_email
    ON users (workspace_id, email) NULLS NOT DISTINCT;
