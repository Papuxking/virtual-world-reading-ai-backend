# API Reference — Virtual World Reading API v1.1

**Base URL:** `http://localhost:8000`  
**Docs interactivos:** `http://localhost:8000/docs` (Swagger UI)

---

## Sistema

### `GET /health`
Verifica el estado de la API y la conexión a la BD.

```bash
curl http://localhost:8000/health
```

```json
{"status": "ok", "database": "connected"}
```

---

## Tipologías

### `GET /typologies`
Lista tipologías con conteo de lecturas.

```bash
curl http://localhost:8000/typologies
```

```json
{
  "typologies": [
    {"name": "Descriptivo", "count": 2},
    {"name": "Narrativo", "count": 1},
    {"name": "Argumentativo", "count": 7},
    {"name": "Expositivo", "count": 5}
  ]
}
```

---

## Lecturas (retrocompatibles v1.0)

### `GET /readings`
Lista con paginación, búsqueda full-text y filtrado.

| Parámetro  | Tipo   | Default      | Descripción                    |
|-----------|--------|-------------|--------------------------------|
| `q`       | string | `""`        | Búsqueda full-text (español)   |
| `typology`| string | `null`      | Filtrar por tipología          |
| `page`    | int    | `1`         | Página                         |
| `per_page`| int    | `10`        | Elementos por página (máx 50)  |
| `sort`    | string | `created_at`| Campo: title, typology, created_at |
| `order`   | string | `desc`      | asc o desc                     |

```bash
curl "http://localhost:8000/readings?typology=Narrativo&page=1&per_page=5"
```

### `GET /readings/{id}`
Lectura por ID (**sin preguntas**).

```bash
curl http://localhost:8000/readings/1
```

### `GET /readings/random`
Lectura aleatoria (**sin preguntas**).

| Parámetro  | Tipo   | Default | Descripción |
|-----------|--------|---------|-------------|
| `typology`| string | `null`  | Filtrar por tipología |

```bash
curl "http://localhost:8000/readings/random?typology=Descriptivo"
```

### `POST /readings`
Crear lectura.

```bash
curl -X POST http://localhost:8000/readings \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Mi lectura",
    "typology": "Narrativo",
    "type": "Narrativa literaria",
    "content": "Contenido de al menos 100 caracteres para ser aceptado por la validación del sistema..."
  }'
```

### `PUT /readings/{id}`
Actualizar lectura.

```bash
curl -X PUT http://localhost:8000/readings/1 \
  -H "Content-Type: application/json" \
  -d '{"title": "Nuevo título"}'
```

### `DELETE /readings/{id}`
Eliminar lectura (CASCADE elimina preguntas y respuestas).

```bash
curl -X DELETE http://localhost:8000/readings/1
```

---

## Lecturas con Preguntas (v1.1 — para caché local)

### `GET /readings/{id}/full`
Lectura completa **con todas sus preguntas y respuestas**.
Incluye `correct_answer` y `justification` para validación offline.

```bash
curl http://localhost:8000/readings/1/full
```

```json
{
  "id": 1,
  "title": "Baños de Agua Santa: Naturaleza...",
  "typology": "Descriptivo",
  "type": "Texto descriptivo geográfico-cultural",
  "content": "Ubicada en la provincia de Tungurahua...",
  "created_at": "2026-04-26T...",
  "updated_at": "2026-04-26T...",
  "questions": [
    {
      "id": 1,
      "question_number": 1,
      "comprehension_level": "Literal",
      "question_text": "¿En qué provincia se encuentra Baños?",
      "correct_answer": "B",
      "justification": "El primer párrafo indica...",
      "answers": [
        {"letter": "A", "answer_text": "Cotopaxi"},
        {"letter": "B", "answer_text": "Tungurahua"},
        {"letter": "C", "answer_text": "Chimborazo"},
        {"letter": "D", "answer_text": "Pastaza"}
      ]
    }
  ]
}
```

### `GET /readings/{id}/questions`
Solo las preguntas de una lectura, con filtro opcional por nivel.

| Parámetro | Tipo   | Default | Descripción                        |
|----------|--------|---------|-------------------------------------|
| `level`  | string | `null`  | Literal, Inferencial, o Critico     |

```bash
# Todas las preguntas
curl http://localhost:8000/readings/1/questions

# Solo preguntas inferenciales
curl "http://localhost:8000/readings/1/questions?level=Inferencial"
```

### `GET /readings/random/full`
Lectura aleatoria **con preguntas**, con filtro opcional por tipología.

| Parámetro  | Tipo   | Default | Descripción |
|-----------|--------|---------|-------------|
| `typology`| string | `null`  | Filtrar por tipología |

```bash
curl "http://localhost:8000/readings/random/full?typology=Argumentativo"
```

La zona de práctica se retiró en la Beta 2.1: ya no hay lecturas ni sesiones de
práctica. `POST /progress/sessions` responde 404 `Lectura no encontrada` si la
lectura no existe (por ejemplo, una de práctica enviada por un juego viejo).

---

## Importar lecturas desde JSON

```bash
# Desde el contenedor (JSONs montados en /data)
docker-compose exec api python import_json_readings.py

# Archivos personalizados
docker-compose exec api python import_json_readings.py /data/mi_archivo.json

```

---

## Entornos de trabajo (Beta 2.1)

Cada cuenta de jugador es de un entorno y, como mucho, uno está activo: solo sus
jugadores entran al juego. Los administradores no tienen entorno y entran siempre.
El mismo correo puede tener una cuenta en cada entorno.

**Acceso de los jugadores:**
- `POST /auth/login` usa la cuenta del administrador con ese correo o, si no, la
  del entorno activo. Con la contraseña de una cuenta de otro entorno (o de antes
  de los entornos): 403 `Tu cuenta no pertenece al entorno activo del juego.`; sin
  entorno activo: 403 `El juego no está disponible en este momento.`; si no, 401.
- `POST /auth/register` crea la cuenta en el entorno activo (403 si no hay).
- Cualquier petición de un jugador cuyo entorno no está activo responde
  409 `WORKSPACE_INACTIVE`; el juego lo trata como una sesión invalidada.
- `GET /leaderboard/top` solo trae jugadores del entorno activo.

**Administración** (solo administradores):

| Método y ruta | Qué hace |
|---|---|
| `GET /admin/workspaces` | Lista: `id`, `name`, `color`, `is_active`, `player_count`, `created_at` |
| `POST /admin/workspaces` | Crea (`name` de 1-40 caracteres, `color` de la paleta); nace inactivo. 409 si el nombre existe (sin distinguir mayúsculas) |
| `PATCH /admin/workspaces/{id}` | Cambia `name` y/o `color` |
| `POST /admin/workspaces/{id}/activate` | Lo activa y apaga los demás; devuelve la lista |
| `POST /admin/workspaces/{id}/deactivate` | Lo apaga (puede no quedar ninguno activo); devuelve la lista |
| `DELETE /admin/workspaces/{id}?confirm_name=…` | Solo inactivo, no el último y con el nombre exacto: borra sus cuentas con todo lo suyo (204) |
| `POST /admin/workspaces/{id}/players` | Alta de jugadores (abajo) |

Paleta: `#059669`, `#d97706`, `#2563eb`, `#7c3aed`, `#db2777`, `#0891b2`.

**Alta de jugadores:** `{"players": [{"email": "...", "display_name": "..."}]}` (1-200).
Cada uno se crea con una contraseña temporal y `must_change_password`, o se salta
con su motivo: `el correo no es válido`, `está repetido en la lista`,
`ya tiene cuenta en este entorno` o `es el correo de un administrador`. Sin nombre,
se usa lo que va antes de la @. Respuesta: `{"created": [{"id", "email",
"display_name", "temp_password"}], "skipped": [{"email", "reason"}]}`; las
contraseñas temporales solo viajan aquí.

```bash
curl -X POST http://localhost:8001/admin/workspaces/2/players   -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json"   -d '{"players": [{"email": "ana@correo.com", "display_name": "Ana Torres"}]}'
```

---

## Códigos de error

| Código | Significado                        |
|--------|------------------------------------|
| 400    | Tipología o nivel inválido         |
| 404    | Lectura no encontrada              |
| 422    | Validación de datos fallida        |
| 500    | Error interno del servidor         |
