# Database Schema — Virtual World Reading API

## Diagrama de tablas

```
┌──────────────────────────────────┐
│            readings              │
├──────────────────────────────────┤
│ id          SERIAL       PK     │
│ title       VARCHAR(255) NOT NULL│
│ typology    VARCHAR(50)  NOT NULL│  CHECK (Descriptivo, Narrativo,
│ content     TEXT         NOT NULL│         Argumentativo, Expositivo,
│ created_at  TIMESTAMPTZ         │         Instructivo)
│ updated_at  TIMESTAMPTZ         │
└──────────────┬───────────────────┘
               │ 1:N (FK)
┌──────────────┴───────────────────┐
│         user_readings            │ ← Futura activación
├──────────────────────────────────┤
│ id          SERIAL       PK     │
│ user_id     VARCHAR(100) NOT NULL│
│ reading_id  INTEGER      FK → readings(id) ON DELETE CASCADE
│ read_at     TIMESTAMPTZ         │
│                                  │
│ UNIQUE(user_id, reading_id)     │
└──────────────────────────────────┘
```

## DDL completo

Ver [`api/sql/001_schema.sql`](../api/sql/001_schema.sql)

## Índices

| Índice | Tabla | Tipo | Propósito |
|--------|-------|------|-----------|
| `idx_readings_typology` | readings | B-tree | Filtrado rápido por tipología |
| `idx_readings_title_fts` | readings | GIN | Búsqueda full-text en título (español) |
| `idx_readings_content_fts` | readings | GIN | Búsqueda full-text en contenido (español) |
| `idx_user_readings_user` | user_readings | B-tree | Búsqueda por user_id |

## Tipologías (CHECK constraint)

Las tipologías están restringidas a nivel de base de datos:

1. **Descriptivo** — Textos que describen personas, lugares, objetos o situaciones
2. **Narrativo** — Relatos con secuencia de eventos, personajes y trama
3. **Argumentativo** — Textos con tesis, argumentos y conclusión persuasiva
4. **Expositivo** — Textos informativos que explican conceptos o procesos
5. **Instructivo** — Guías paso a paso, instrucciones o procedimientos

## Seed data

Ver [`api/sql/002_seed.sql`](../api/sql/002_seed.sql)

| Tipología | Cantidad | Origen |
|-----------|----------|--------|
| Descriptivo | 2 | Textos reales del proyecto (bannos.txt, temporal reading 1.txt) |
| Narrativo | 3 | Generados (relatos breves ficción) |
| Argumentativo | 3 | Generados (textos opinativos con evidencia) |
| Expositivo | 3 | Generados (textos informativos educativos) |
| Instructivo | 3 | Generados (guías paso a paso) |

## Propuesta de no-repetición por usuario

### Estado actual
- La tabla `user_readings` ya está creada en el DDL
- Los endpoints aún NO están implementados en la API
- Actualmente las lecturas pueden repetirse

### Activación futura

Cuando se implemente autenticación de usuarios:

1. **Marcar lectura como vista:**
   ```
   POST /users/{user_id}/readings/{reading_id}/mark-read
   ```
   Inserta un registro en `user_readings`.

2. **Obtener siguiente lectura no vista:**
   ```
   GET /users/{user_id}/readings/next?typology=Narrativo
   ```
   SQL subyacente:
   ```sql
   SELECT r.* FROM readings r
   WHERE r.id NOT IN (
       SELECT ur.reading_id FROM user_readings ur
       WHERE ur.user_id = :user_id
   )
   AND (:typology IS NULL OR r.typology = :typology)
   ORDER BY RANDOM()
   LIMIT 1;
   ```

3. **Historial de lecturas del usuario:**
   ```
   GET /users/{user_id}/readings/history?page=1&per_page=10
   ```

### Consideraciones para `user_id`

El campo `user_id` es `VARCHAR(100)` para admitir:
- UUID generado por Godot (`OS.get_unique_id()`)
- ID de sesión temporal
- ID de usuario autenticado (futuro)

No hay FK a una tabla `users` porque el sistema de autenticación aún no existe.

## Inicialización

Los scripts SQL se ejecutan automáticamente al crear el contenedor PostgreSQL por primera vez:

```bash
# Primera vez: crea BD, tablas y seed
docker-compose up -d

# Re-seed (destruye datos existentes):
docker-compose down -v
docker-compose up -d
```

Los archivos en `api/sql/` se montan en `/docker-entrypoint-initdb.d/` y PostgreSQL los ejecuta en orden alfabético (`001_schema.sql` → `002_seed.sql`).
