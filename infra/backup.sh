#!/usr/bin/env bash
# ============================================================================
#  Copia de seguridad del entorno virtual — SE EJECUTA EN EL SERVIDOR
#      /opt/vw/infra/backup.sh
#
#  Respalda SOLO lo del entorno virtual:
#    - base de datos godot_readings (contenedor vw-db-1, puerto 5432)
#    - volumen vw_medals (medallas subidas por el admin: no estan en git)
#    - /opt/vw/infra/.env (JWT_SECRET_KEY y password de Postgres: sin esto,
#      restaurar la BD no sirve de nada porque los tokens no validan)
#    - /etc/nginx/conf.d/vw.conf (la config viva, que evoluciona a mano)
#
#  NO respalda LecturaIA (puerto 5433, /opt/lecturaia): esa pila es de otro
#  autor y sus copias son cosa suya.
#
#  Pensado para cron diario. La retencion son 14 dias.
# ============================================================================
set -euo pipefail

DEST=/var/backups/vw
KEEP_DAYS=14
TS="$(date +%Y%m%d-%H%M%S)"
ENV_FILE=/opt/vw/infra/.env

log() { printf '[backup] %s\n' "$*"; }
die() { printf '[error ] %s\n' "$*" >&2; exit 1; }

mkdir -p "$DEST"
chmod 700 "$DEST"

docker info >/dev/null 2>&1 || die "sin acceso a Docker (falta bootstrap-root.sh)"
[ -r "$ENV_FILE" ] || die "no puedo leer $ENV_FILE"

# shellcheck disable=SC1090
set -a; . "$ENV_FILE"; set +a

# --- base de datos ---------------------------------------------------------
log "volcando $POSTGRES_DB"
docker exec vw-db-1 pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists \
    | gzip -9 > "$DEST/db-$TS.sql.gz"
# Un dump de 0 bytes es peor que ningun dump: da falsa sensacion de seguridad.
[ -s "$DEST/db-$TS.sql.gz" ] || die "el dump salio vacio"
if ! gzip -t "$DEST/db-$TS.sql.gz"; then
    die "el dump esta corrupto"
fi
log "  -> db-$TS.sql.gz ($(du -h "$DEST/db-$TS.sql.gz" | cut -f1))"

# --- volumen de medallas ---------------------------------------------------
log "volcando volumen vw_medals"
docker run --rm -v vw_medals:/data:ro -v "$DEST":/bk alpine \
    tar czf "/bk/medals-$TS.tar.gz" -C /data . 2>/dev/null
log "  -> medals-$TS.tar.gz ($(du -h "$DEST/medals-$TS.tar.gz" | cut -f1))"

# --- secretos y config viva ------------------------------------------------
cp "$ENV_FILE" "$DEST/env-$TS"
chmod 600 "$DEST/env-$TS"
cp /etc/nginx/conf.d/vw.conf "$DEST/nginx-vw-$TS.conf" 2>/dev/null || true

# --- retencion -------------------------------------------------------------
find "$DEST" -maxdepth 1 -type f -mtime "+$KEEP_DAYS" -print -delete | sed 's/^/[backup] purgado /'

log "hecho. Contenido de $DEST:"
ls -1t "$DEST" | head -8 | sed 's/^/  /'
log "RECUERDA: esto vive en el MISMO disco que el servidor. La copia que"
log "de verdad te salva es la de fuera: pull-backups.sh en local + los"
log "Backups automaticos de Hetzner."
