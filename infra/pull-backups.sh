#!/usr/bin/env bash
# ============================================================================
#  Descarga las copias del servidor a tu equipo — SE EJECUTA EN LOCAL
#      Docker/infra/pull-backups.sh
#
#  Una copia que vive en el mismo disco que el servidor no es una copia: si el
#  disco se pierde, se pierden las dos. Esto se trae los ultimos dumps a
#  PROYECTO/BACKUP_SERVIDOR/, que esta FUERA de todo repositorio git.
#
#  Ojo: el .env descargado contiene JWT_SECRET_KEY y la contrasena de Postgres
#  en claro. Su sitio definitivo es un gestor de contrasenas, no el escritorio.
# ============================================================================
set -euo pipefail

SSH_KEY="${SSH_KEY:-$HOME/.ssh/vw_deploy}"
HOST="${VW_HOST:-deploy@entornovirtual.duckdns.org}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="$(cd "$HERE/../.." && pwd)/BACKUP_SERVIDOR"
KEEP=3

log() { printf '[pull] %s\n' "$*"; }

mkdir -p "$DEST/db" "$DEST/medals" "$DEST/config"

log "ultimos $KEEP dumps de base de datos"
for f in $(ssh -i "$SSH_KEY" "$HOST" "ls -1t /var/backups/vw/db-*.sql.gz 2>/dev/null | head -$KEEP"); do
    n="$(basename "$f")"
    [ -f "$DEST/db/$n" ] && { log "  ya tengo $n"; continue; }
    log "  bajando $n"
    scp -q -i "$SSH_KEY" "$HOST:$f" "$DEST/db/$n"
done

log "ultimo volcado de medallas"
for f in $(ssh -i "$SSH_KEY" "$HOST" "ls -1t /var/backups/vw/medals-*.tar.gz 2>/dev/null | head -1"); do
    n="$(basename "$f")"
    [ -f "$DEST/medals/$n" ] || scp -q -i "$SSH_KEY" "$HOST:$f" "$DEST/medals/$n"
done

log "config viva (.env y nginx)"
scp -q -i "$SSH_KEY" "$HOST:/opt/vw/infra/.env"        "$DEST/config/vw-infra.env"
scp -q -i "$SSH_KEY" "$HOST:/etc/nginx/conf.d/vw.conf" "$DEST/config/nginx-vw.conf.live"

log "verificando integridad de lo descargado"
find "$DEST/db" "$DEST/medals" -name '*.gz' -print0 | while IFS= read -r -d '' g; do
    gzip -t "$g" && echo "  OK $(basename "$g")" || echo "  CORRUPTO $(basename "$g")"
done

log "en $DEST:"
du -sh "$DEST"/* 2>/dev/null | sed 's/^/  /'
