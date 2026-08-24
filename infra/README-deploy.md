# Despliegue — entorno virtual de lectura

Servidor: Hetzner vServer aarch64, 2 vCPU / 3.4 GB RAM / 38 GB disco.
Rocky Linux 10.2. Dominio `entornovirtual.duckdns.org`.

## Regla número uno

**LecturaIA no se toca.** Vive en `/opt/lecturaia`, la mantiene otro autor y usa
los puertos `8002` (API), `3001` (Next.js) y `5433` (su Postgres). Ningún script
de este repositorio escribe ahí.

La única pieza compartida es **nginx**. Su config incluye las rutas de LecturaIA
(`/npc/`, `/lecturaia/`, `/api/v1/`) y las nuestras. Por eso `nginx-vw.conf` de
este repo es una copia fiel de la config viva, y tanto `deploy.sh nginx` como el
wrapper de root **abortan** si el fichero entrante no contiene esas tres rutas.
Esa comprobación existe porque la versión anterior del repo no las tenía:
aplicarla habría dejado a tu compañero sin servicio.

## Quién es quién

| Puerto | Servicio | Dueño |
|---|---|---|
| 8001 | API Virtual World (contenedor `vw-api-1`) | nosotros |
| 5432 | Postgres `godot_readings` (`vw-db-1`) | nosotros |
| 8002 | API LecturaIA | **compañero** |
| 3001 | Frontend Next.js LecturaIA | **compañero** |
| 5433 | Postgres LecturaIA | **compañero** |

Estáticos del juego: `/var/www/vw` → symlink a `/var/www/vw-releases/<ts>/`.
Dashboard: `/var/www/vw-dashboard`.

## Puesta en marcha (una sola vez)

Como **root** en el servidor:

```bash
bash /opt/vw/infra/bootstrap-root.sh
```

Añade `deploy` al grupo docker, instala un sudoers acotado, convierte
`/var/www/vw` en symlink de releases, crea `/var/backups/vw` y programa el
backup diario. Es idempotente.

Después, en la **consola de Hetzner**: `Server → Backups → Enable`. Cuesta un 20 %
del precio del servidor y es la única copia que sobrevive a perder el disco.

## Ciclo de trabajo normal

```
rama feature/*  →  develop  →  main  →  despliegue  →  tag prod-*
```

`main` es, por definición, lo que corre en producción. Nada se despliega desde
una rama `feature/*`: hoy producción corría desde `feature/testmultiplayer`, que
es justo lo que hace imposible saber qué hay desplegado.

### Cambio solo de juego (Godot)

1. Trabaja en `feature/*` en el repo del entorno, mergea a `main`, pushea.
2. Exporta el preset **Web** a `PROYECTO/web_build/`.
   Comprueba que `exclude_filter="*server_config.json"` sigue en
   `export_presets.cfg`: sin él, el juego apunta a `localhost:8001` en producción.
3. `bash Docker/infra/push.sh web`

`push.sh web` aborta si el repo de Godot tiene cambios sin commitear o sin
pushear: el build sale de ahí, así que es ese repo el que determina qué versión
corre. Junto a cada release se guarda un `.info` con la rama y el commit del
juego y del backend, fuera del directorio servido, y `deploy.sh status` lo
muestra.

> El repo del juego (`Steeven24/virtual-world-reading-ai`) está en la cuenta de
> un compañero, aunque trabajemos en él. Se empuja a `feature/presentación`; no
> se mueve `main` ahí sin hablarlo antes.

### Cambio de API (Python)

1. Commit y push en el repo del backend (`main`).
2. `bash Docker/infra/push.sh code`

El código viaja por SSH (`git archive` del commit ya pusheado), **no** con un
`git pull` en el servidor: el repo es privado y la máquina no tiene credenciales
de GitHub. `/opt/vw/.deployed-commit` registra qué commit está desplegado y
`deploy.sh status` lo muestra. `infra/.env` se excluye siempre del rsync porque
es la única copia de `JWT_SECRET_KEY`.


Si tocas dependencias, edita `api/requirements.txt` **y regenera el lock**:

```bash
docker run --rm -v "$PWD/api:/api" -w /api python:3.12-slim sh -c \
  "pip install --only-binary=:all: -q -r requirements.txt && pip freeze" \
  > api/requirements.lock.txt
```

La imagen se construye desde el lock, no desde `requirements.txt`. Sin eso, cada
rebuild resolvía versiones frescas de PyPI y la imagen no era reproducible.

### Reemplazar el corpus de lecturas

```bash
# 1. copia previa (obligatoria)
ssh vw '/opt/vw/infra/backup.sh'
# 2. simulacro: muestra el arrastre en cascada sin tocar nada
ssh vw 'docker exec vw-api-1 python replace_readings.py --json /data/LECTURAS_TIPOLOGIAS_TEXTUALES.json'
# 3. aplicar
ssh vw 'docker exec vw-api-1 python replace_readings.py --json /data/LECTURAS_TIPOLOGIAS_TEXTUALES.json --apply'
# 4. dejar a los jugadores en estado inicial
ssh vw 'docker exec vw-api-1 python reset_players.py --students 50 --demo --apply'
```

Borrar una lectura arrastra en cascada sus preguntas, respuestas, sesiones de
alumno y notas. Los logros y el `best_score` por tipología **no** cuelgan de
`readings` y sobreviven, así que sin el paso 4 queda puntuación sin sesiones
detrás. El simulacro del paso 2 cuantifica todo eso antes de escribir.

### Router nuevo en la API

nginx enruta por **lista blanca**:

```nginx
location ~ ^/(auth|progress|readings|typologies|leaderboard|achievements|admin|static|health|docs|openapi\.json)
```

Un router nuevo que no esté en ese regex da **404 en producción y 200 en local**.
Añádelo a `infra/nginx-vw.conf`, pushea, y luego:

```bash
ssh vw '/opt/vw/infra/deploy.sh nginx'
```

### Ambos a la vez

```bash
bash Docker/infra/push.sh all      # code primero, luego web
```

## Rollback

| Qué falló | Orden | Tiempo |
|---|---|---|
| El juego web | `ssh vw '/opt/vw/infra/deploy.sh rollback-web'` | instantáneo (symlink) |
| La API | `ssh vw '/opt/vw/infra/deploy.sh rollback-api'` | ~10 s (imagen anterior) |
| nginx | `sudo cp /etc/nginx/conf.d/vw.conf.bak-<ts> /etc/nginx/conf.d/vw.conf && sudo nginx -t && sudo systemctl reload nginx` | manual |
| Base de datos | `gunzip -c /var/backups/vw/db-<ts>.sql.gz \| docker exec -i vw-db-1 psql -U <user> -d godot_readings` | minutos |
| Todo | Restaurar snapshot de Hetzner | minutos |

`deploy.sh api` ya revierte **solo** si `/health` no responde 200 en 60 s, y
`deploy.sh web` revierte solo si la portada no responde 200. El rollback manual
es para cuando el fallo es funcional, no de arranque.

Se conservan las **5 últimas releases** y las **5 últimas imágenes**.

## Backups

`backup.sh` corre a diario a las 03:30 vía `/etc/cron.d/vw-backup` y guarda en
`/var/backups/vw` (retención 14 días): dump de la BD, volumen `vw_medals`,
`.env` y la config viva de nginx.

Eso vive en el mismo disco. Tráete copia a local con regularidad:

```bash
bash Docker/infra/pull-backups.sh
```

Restaurar la BD sin el `.env` no sirve de nada: los tokens JWT no validarían.
Por eso el `.env` va en la copia.

## Secretos

- `infra/.env` está en `.gitignore` y **debe seguir estándolo**. Es la única
  copia de `JWT_SECRET_KEY` y de la contraseña de Postgres.
- `.env.example` lista todas las claves que el código lee, sin valores.
- Los `.txt` con credenciales del escritorio (`AccesoServidor.txt`,
  `CLAVES_SSH_SERVIDOR.txt`, `CREDENCIALES_DESPLIEGUE.txt`) son material sensible
  en claro. Su sitio es un gestor de contraseñas.

## Comprobar estado

```bash
ssh vw '/opt/vw/infra/deploy.sh status'
```

Muestra release activa, imagen de la API, commit desplegado y salud de los tres
servicios (los de LecturaIA, solo como información).
