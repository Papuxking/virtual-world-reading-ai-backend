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

## Resetear la base de datos

```bash
docker-compose down -v
docker-compose up -d
```

## Importar lecturas desde JSON

```bash
docker-compose exec api python import_json_readings.py
```
