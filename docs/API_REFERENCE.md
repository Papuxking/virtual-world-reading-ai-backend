# API Reference — Virtual World Reading API

## Base URL

```
http://localhost:8000
```

---

## Endpoints

### `GET /health`

Verifica el estado de la API y la conexión a la base de datos.

```bash
curl http://localhost:8000/health
```

**Respuesta:**
```json
{
  "status": "ok",
  "database": "connected"
}
```

---

### `GET /typologies`

Lista las tipologías disponibles con el conteo de lecturas.

```bash
curl http://localhost:8000/typologies
```

**Respuesta:**
```json
{
  "typologies": [
    {"name": "Descriptivo", "count": 2},
    {"name": "Narrativo", "count": 3},
    {"name": "Argumentativo", "count": 3},
    {"name": "Expositivo", "count": 3},
    {"name": "Instructivo", "count": 3}
  ]
}
```

---

### `GET /readings`

Lista lecturas con paginación, búsqueda full-text y filtrado.

| Parámetro  | Tipo   | Default      | Descripción |
|------------|--------|--------------|-------------|
| `q`        | string | `""`         | Búsqueda full-text en título y contenido (español) |
| `typology` | string | `null`       | Filtro por tipología: Descriptivo, Narrativo, Argumentativo, Expositivo, Instructivo |
| `page`     | int    | `1`          | Número de página (1-indexed) |
| `per_page` | int    | `10`         | Elementos por página (máx: 50) |
| `sort`     | string | `created_at` | Campo: `title`, `typology`, `created_at` |
| `order`    | string | `desc`       | Dirección: `asc`, `desc` |

```bash
# Todas las lecturas, página 1
curl "http://localhost:8000/readings?page=1&per_page=5"

# Filtrar por tipología
curl "http://localhost:8000/readings?typology=Descriptivo"

# Búsqueda full-text en español
curl "http://localhost:8000/readings?q=cascada"

# Ordenar por título ascendente
curl "http://localhost:8000/readings?sort=title&order=asc"
```

**Respuesta:**
```json
{
  "items": [
    {
      "id": 1,
      "title": "Baños de Agua Santa...",
      "typology": "Descriptivo",
      "content": "Ubicada en la provincia...",
      "created_at": "2026-04-23T14:00:00Z",
      "updated_at": "2026-04-23T14:00:00Z"
    }
  ],
  "total": 14,
  "page": 1,
  "per_page": 5,
  "pages": 3
}
```

---

### `GET /readings/random`

Retorna una lectura aleatoria, opcionalmente filtrada por tipología.

```bash
# Aleatoria de cualquier tipología
curl http://localhost:8000/readings/random

# Aleatoria de tipo Narrativo
curl "http://localhost:8000/readings/random?typology=Narrativo"
```

---

### `GET /readings/{id}`

Obtiene una lectura por su ID.

```bash
curl http://localhost:8000/readings/1
```

**Respuesta:** Un objeto `ReadingResponse`.

**Error 404:**
```json
{"detail": "Lectura no encontrada"}
```

---

### `POST /readings`

Crea una nueva lectura.

```bash
curl -X POST http://localhost:8000/readings \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Mi nueva lectura",
    "typology": "Expositivo",
    "content": "Contenido del texto expositivo que debe tener al menos cien caracteres para superar la validación mínima del campo content en el schema Pydantic."
  }'
```

**Body (JSON):**
```json
{
  "title": "string (1-255 chars, requerido)",
  "typology": "string (Descriptivo|Narrativo|Argumentativo|Expositivo|Instructivo, requerido)",
  "content": "string (100-50000 chars, requerido)"
}
```

**Respuesta:** `201 Created` con el objeto `ReadingResponse`.

---

### `PUT /readings/{id}`

Actualiza una lectura existente (campos opcionales).

```bash
curl -X PUT http://localhost:8000/readings/1 \
  -H "Content-Type: application/json" \
  -d '{"title": "Nuevo título actualizado"}'
```

**Body (JSON):** Cualquier combinación de `title`, `typology`, `content`.

---

### `DELETE /readings/{id}`

Elimina una lectura.

```bash
curl -X DELETE http://localhost:8000/readings/5
```

**Respuesta:**
```json
{"detail": "Lectura eliminada", "id": 5}
```

---

## Tipologías válidas

| Tipología      | Descripción |
|----------------|-------------|
| Descriptivo    | Textos que describen personas, lugares, objetos o situaciones |
| Narrativo      | Relatos con secuencia de eventos, personajes y trama |
| Argumentativo  | Textos con tesis, argumentos y conclusión persuasiva |
| Expositivo     | Textos informativos que explican conceptos o procesos |
| Instructivo    | Guías paso a paso, instrucciones o procedimientos |

---

## Límites de contenido

- **Mínimo:** 100 caracteres
- **Máximo:** 50,000 caracteres (~62 páginas del libro Godot a 800 chars/pág)
- **Paginación visual:** la fragmentación en páginas de 800 caracteres se realiza en el cliente Godot, no en la API

---

## Integración con Godot

Ejemplo de request HTTP desde GDScript:

```gdscript
var http_request = HTTPRequest.new()
add_child(http_request)
http_request.request_completed.connect(_on_request_completed)

# Obtener lectura aleatoria de tipo Descriptivo
http_request.request("http://localhost:8000/readings/random?typology=Descriptivo")

func _on_request_completed(result, response_code, headers, body):
    var json = JSON.parse_string(body.get_string_from_utf8())
    if json and response_code == 200:
        var titulo = json["title"]
        var contenido = json["content"]
        # Usar contenido en el libro...
```
