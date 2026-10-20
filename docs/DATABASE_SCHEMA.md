# Esquema de Base de Datos — Virtual World Reading API

## Diagrama relacional

```
readings                          questions                    answers
┌─────────────────────────┐       ┌─────────────────────────┐  ┌────────────────────────┐
│ id          PK SERIAL   │──1:N─▶│ id          PK SERIAL   │─▶│ id       PK SERIAL     │
│ title       VARCHAR(255)│       │ reading_id  FK NOT NULL  │  │ question_id FK NOT NULL│
│ typology    VARCHAR(50) │       │ question_number SMALLINT │  │ letter   CHAR(1)       │
│ type        VARCHAR(100)│       │ comprehension_level      │  │ answer_text TEXT       │
│ content     TEXT        │       │   VARCHAR(20)            │  │ UNIQUE(question_id,    │
│ created_at  TIMESTAMPTZ │       │ question_text TEXT       │  │         letter)        │
│ updated_at  TIMESTAMPTZ │       │ correct_answer CHAR(1)   │  └────────────────────────┘
└─────────────────────────┘       │ justification TEXT       │
        │                         └─────────────────────────┘
        │ 1:N
        ▼
user_readings (futura)
┌─────────────────────────┐
│ id         PK SERIAL    │
│ user_id    VARCHAR(100)  │
│ reading_id FK NOT NULL   │
│ read_at    TIMESTAMPTZ   │
│ UNIQUE(user_id,          │
│        reading_id)       │
└─────────────────────────┘
```

## Tabla `readings`

| Columna      | Tipo          | Restricciones                                     |
|-------------|---------------|---------------------------------------------------|
| `id`        | `SERIAL`      | PRIMARY KEY                                       |
| `title`     | `VARCHAR(255)` | NOT NULL                                          |
| `typology`  | `VARCHAR(50)` | NOT NULL, CHECK IN (Descriptivo, Narrativo, Argumentativo, Expositivo, Instructivo) |
| `type`      | `VARCHAR(100)` | NULL (subtipo textual opcional)                   |
| `content`   | `TEXT`        | NOT NULL                                          |
| `created_at`| `TIMESTAMPTZ` | DEFAULT NOW()                                     |
| `updated_at`| `TIMESTAMPTZ` | DEFAULT NOW()                                     |

El CHECK de `typology` conserva Instructivo por compatibilidad con la sincronización
de LecturaIA; el juego ya no la usa (ver `game_rules.DIFFICULTY_ORDER`).
La zona de práctica se retiró en la Beta 2.1: al arrancar, la API borra sus
lecturas y sesiones y las columnas `is_practice` de `readings` y `player_sessions`
(`esquema.quitar_practica`).

**Índices:**
- `idx_readings_typology` — B-tree sobre `typology`
- `idx_readings_title_fts` — GIN full-text español sobre `title`
- `idx_readings_content_fts` — GIN full-text español sobre `content`

## Tabla `questions`

| Columna              | Tipo         | Restricciones                                     |
|---------------------|--------------|---------------------------------------------------|
| `id`                | `SERIAL`     | PRIMARY KEY                                       |
| `reading_id`        | `INTEGER`    | FK → readings(id) ON DELETE CASCADE               |
| `question_number`   | `SMALLINT`   | NOT NULL (orden dentro de la lectura)             |
| `comprehension_level` | `VARCHAR(20)` | NOT NULL, CHECK IN (Literal, Inferencial, Critico) |
| `question_text`     | `TEXT`       | NOT NULL                                          |
| `correct_answer`    | `CHAR(1)`    | NOT NULL, CHECK IN (A, B, C, D)                   |
| `justification`     | `TEXT`       | Explicación de la respuesta correcta              |

**Índices:**
- `idx_questions_reading` — B-tree sobre `reading_id`
- `idx_questions_level` — B-tree sobre `comprehension_level`

## Tabla `answers`

| Columna        | Tipo      | Restricciones                           |
|---------------|-----------|------------------------------------------|
| `id`          | `SERIAL`  | PRIMARY KEY                              |
| `question_id` | `INTEGER` | FK → questions(id) ON DELETE CASCADE     |
| `letter`      | `CHAR(1)` | NOT NULL, CHECK IN (A, B, C, D)          |
| `answer_text` | `TEXT`    | NOT NULL                                 |

**Restricciones:**
- `UNIQUE(question_id, letter)` — cada pregunta tiene exactamente una A, B, C, D

## Tabla `user_readings` (futura activación)

| Columna      | Tipo          | Restricciones                           |
|-------------|---------------|-----------------------------------------|
| `id`        | `SERIAL`      | PRIMARY KEY                             |
| `user_id`   | `VARCHAR(100)` | NOT NULL                               |
| `reading_id`| `INTEGER`     | FK → readings(id) ON DELETE CASCADE     |
| `read_at`   | `TIMESTAMPTZ` | DEFAULT NOW()                           |

**Restricción:** `UNIQUE(user_id, reading_id)`

## Tabla `workspaces` (entornos de trabajo)

| Columna      | Tipo          | Restricciones                                     |
|-------------|---------------|---------------------------------------------------|
| `id`        | `SERIAL`      | PRIMARY KEY                                       |
| `name`      | `VARCHAR(40)` | NOT NULL, único sin distinguir mayúsculas (`ux_workspaces_nombre`) |
| `color`     | `VARCHAR(7)`  | NOT NULL (uno de la paleta del dashboard)         |
| `is_active` | `BOOLEAN`     | NOT NULL DEFAULT false; como mucho uno activo (`ux_workspaces_un_activo`) |
| `created_at`| `TIMESTAMPTZ` | DEFAULT NOW()                                     |

Cada cuenta de jugador es de un entorno: `users.workspace_id` → `workspaces(id)`
`ON DELETE CASCADE` (borrar un entorno borra sus cuentas y, en cascada, todo lo
suyo). Los administradores no tienen entorno, y tampoco las cuentas de antes de
los entornos (no se migraron: no entran al juego ni salen en el dashboard).

El correo es único dentro de cada entorno y entre las cuentas sin entorno:
`ux_users_workspace_email` sobre `(workspace_id, email) NULLS NOT DISTINCT`. Lo
crea la migración `011_entornos.sql`, que quita la unicidad vieja
(`ix_users_email` o `users_email_key`).

Al arrancar, cada proceso de la API prepara la base (`esquema.preparar_base`:
`create_all` y las migraciones) con un candado de Postgres
(`pg_advisory_xact_lock`), un proceso detrás de otro.

## Niveles de comprensión lectora

| Nivel          | Descripción                                    |
|---------------|------------------------------------------------|
| `Literal`     | Datos explícitos en el texto                   |
| `Inferencial` | Deducciones a partir del texto                 |
| `Critico`     | Análisis, evaluación y juicio del lector       |

## Archivos SQL

| Archivo | Descripción |
|---------|-------------|
| `001_schema.sql` | DDL base: readings, user_readings, índices FTS |
| `002_questions_schema.sql` | DDL: questions, answers, ALTER readings ADD type |
| `002_seed.sql` | Seed: lectura Baños de Agua Santa + 12 preguntas |
| `011_entornos.sql` | Tabla `workspaces`, `users.workspace_id` y correo único por entorno |
| `012_conversaciones_asistente.sql` | `npc_interactions.user_message` y `assistant_reply`: lo que el jugador habla con el asistente IA |

## Resetear la base de datos

```bash
docker-compose down -v
docker-compose up -d
```

## Importar lecturas desde JSON

```bash
docker-compose exec api python import_json_readings.py
```
