# Alias y vitrina: servidor local

Implementados la migración 013 (registrada en el arranque), las columnas del modelo, el catálogo espejo de alias, GET y PUT `/progress/profile` y los campos aditivos de `/leaderboard/top`. La caché sigue siendo de 60 segundos por entorno. Sin cambios en el juego ni despliegues.

## Contrato para el cliente

GET y PUT `/progress/profile` requieren Bearer y trabajan con el slot activo. Ambos comprueban `X-Slot-Id` y `X-Session-Version` cuando se envían, siguiendo el patrón existente (409 si la partida o versión no coincide).

El PUT sustituye la selección completa. Acepta `alias` como id del catálogo o null y `vitrina` como lista ordenada de cero a tres objetos `{tipo, id}`. No admite duplicados del mismo par `(tipo, id)`. Si se omiten campos, sus valores son null y lista vacía. No hay escrituras parciales si falla la validación.

GET y PUT devuelven exclusivamente la selección guardada, con el id del alias. Un slot nuevo devuelve `{"alias":null,"vitrina":[]}`. En la clasificación, null se representa con el alias por defecto «Intuición».

Los alias se desbloquean sumando `PlayerTypologyProgress.total_sessions` del usuario y slot activo. Los logros se validan contra `PlayerAchievement` del mismo usuario y slot; las medallas contra `medallas_del_jugador`. Alias inexistentes o bloqueados e insignias no desbloqueadas producen 422.

La clasificación conserva sus campos anteriores y añade `alias` (nombre resuelto) y `vitrina` (lista ordenada). Cada elemento incluye `tipo`, `id`, `nombre`, `emoji`, `tier` e `imagen`. Los dos últimos pueden ser null. `imagen` procede de `AchievementCatalog.medal_image_path` cuando existe; no se inventa una ruta para las medallas calculadas. Para logros, el nombre y emoji proceden del catálogo (con el nombre registrado y 🏆 como respaldo); para medallas, del cálculo existente. El tier de las medallas es el ganado en esa partida. Las insignias que dejen de estar desbloqueadas se omiten de la vista pública.

## Verificación local

Se consultaron `seed_entorno_prueba.py` y `alta_alumnos.py` antes de usar las cuentas existentes del entorno activo «Pruebas». No se ejecutaron esos scripts ni se regeneró progreso. La cuenta `alumno45@test.com` tiene cuatro lecturas completadas; se dejó seleccionada Curiosidad y una vitrina con `medalla_narrativo` y `first_reading`. Para el rechazo de medalla se utilizó `alumno41@test.com`, que tiene una lectura y Narrativo sin aprobar.

Se reinició únicamente `docker-api-1`; las consultas SQL fueron contra `docker-db-1`, base `godot_readings`. Los tests usan la base separada `godot_readings_test`, según `tests/conftest.py`.

Durante la implementación se corrigió un error de esquema introducido en la edición. La primera ejecución general quedó interrumpida por el reinicio. Dos ejecuciones específicas se solaparon por error sobre la base de tests y causaron errores de tablas y claves duplicadas; se descartaron esas ejecuciones y se ejecutó después la suite completa sin concurrencia. No se atribuyen esos fallos a problemas previos del proyecto.

### Tests: salida real

Comando: `docker exec docker-api-1 python -m pytest -q`.

```text
. [100%]
144 passed in 151.40s (0:02:31)
```

La ejecución final terminó con código 0. Incluye diez casos nuevos de perfil: valores iniciales, alias nulo, catálogo y umbrales, vitrina bloqueada o inválida, duplicados, límite de tres, lectura y escritura, resolución pública de medalla y logro, aislamiento entre slots y cabecera de slot desactualizada. No quedaron tests en rojo ni fue necesario modificar tests existentes.

### Migración y columnas: salida real

Comandos: `docker restart docker-api-1`, `docker logs` y consulta a `information_schema.columns` con `docker exec docker-db-1 psql`.

```text
INFO:     Migración aplicada: 013_alias_y_vitrina.sql
INFO:     Application startup complete.
INFO:     Migración aplicada: 013_alias_y_vitrina.sql
INFO:     Application startup complete.
INFO:     Migración aplicada: 013_alias_y_vitrina.sql
INFO:     Application startup complete.
INFO:     Migración aplicada: 013_alias_y_vitrina.sql
INFO:     Application startup complete.
 column_name |     data_type     | character_maximum_length | is_nullable | column_default 
-------------+-------------------+--------------------------+-------------+----------------
 vitrina     | jsonb             |                          | NO          | '[]'::jsonb
 alias       | character varying |                       40 | YES         | 
(2 rows)

```

### Curl autenticado: salida real

Se obtuvo un Bearer con POST /auth/login. Las llamadas usaron curl.exe, cabecera Authorization: Bearer y, para PUT, Content-Type: application/json con --data-binary. No se guarda el token.

En la primera comprobación, Gran lector sí estaba desbloqueada para Alumno 45 y devolvió 200. Se restauró la selección final y se comprobó el rechazo con Alumno 41; ambas salidas se conservan abajo.

```text
GET /progress/profile (antes)
{"alias":null,"vitrina":[]}
HTTP 200
PUT /progress/profile
{"alias":"curiosidad","vitrina":[{"tipo":"medalla","id":"medalla_narrativo"},{"tipo":"logro","id":"first_reading"}]}
HTTP 200
GET /progress/profile (despues)
{"alias":"curiosidad","vitrina":[{"tipo":"medalla","id":"medalla_narrativo"},{"tipo":"logro","id":"first_reading"}]}
HTTP 200
PUT alias sin lecturas suficientes
{"detail":"El alias Conocimiento requiere 20 lecturas completadas"}
HTTP 422
PUT medalla sin desbloquear
{"alias":"curiosidad","vitrina":[{"tipo":"medalla","id":"gran_lector"}]}
HTTP 200
GET /leaderboard/top?limit=1
{"players":[{"rank":1,"display_name":"Alumno 45","character":"male","total_score":748,"total_achievements":5,"alias":"Curiosidad","vitrina":[{"tipo":"medalla","id":"gran_lector","nombre":"Gran lector","emoji":"👑","tier":"platino","imagen":null}]}],"updated_at":"2026-10-25T00:31:07.341587Z"}
HTTP 200
PUT /progress/profile (Alumno 45, seleccion final)
{"alias":"curiosidad","vitrina":[{"tipo":"medalla","id":"medalla_narrativo"},{"tipo":"logro","id":"first_reading"}]}
HTTP 200
PUT /progress/profile (Alumno 41, medalla sin desbloquear)
{"detail":"No has desbloqueado medalla: medalla_narrativo en esta partida"}
HTTP 422
```

### JSON literal de GET /leaderboard/top?limit=1 (HTTP 200)

Respuesta final obtenida con curl autenticado, después de guardar la selección definitiva. limit solo cambia cuántos jugadores se incluyen; el contrato es el mismo que sin ese parámetro.

```json
{"players":[{"rank":1,"display_name":"Alumno 45","character":"male","total_score":748,"total_achievements":5,"alias":"Curiosidad","vitrina":[{"tipo":"medalla","id":"medalla_narrativo","nombre":"Medalla del Narrador","emoji":"📜","tier":"oro","imagen":null},{"tipo":"logro","id":"first_reading","nombre":"📖 Primera lectura","emoji":"📖","tier":"bronce","imagen":null}]}],"updated_at":"2026-10-25T00:31:36.192629Z"}
```
