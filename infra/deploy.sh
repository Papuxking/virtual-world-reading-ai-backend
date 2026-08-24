#!/usr/bin/env bash
# ============================================================================
#  Despliegue del entorno virtual de lectura — SE EJECUTA EN EL SERVIDOR
#      /opt/vw/infra/deploy.sh <subcomando>
#
#  LIMITE DURO: este script NO toca nada de LecturaIA. Ni /opt/lecturaia, ni
#  los contenedores de los puertos 8002 / 3001 / 5433, ni su base de datos.
#  La unica pieza compartida es nginx: aqui solo se VALIDA y se RECARGA, y
#  siempre con copia de seguridad previa.
#
#  Subcomandos:
#    web <release>    activa una release ya subida a /var/www/vw-releases/
#    api              reconstruye y promociona la API, revierte si no responde
#    nginx            instala infra/nginx-vw.conf validandola antes
#    rollback-web     vuelve a la release anterior
#    rollback-api     vuelve a la imagen anterior
#    status           que hay desplegado ahora mismo
# ============================================================================
set -euo pipefail

VW_ROOT=/opt/vw
INFRA="$VW_ROOT/infra"
RELEASES=/var/www/vw-releases
LIVE=/var/www/vw
STATE="$VW_ROOT/.deploy-state"
KEEP=5
HEALTH=http://127.0.0.1:8001/health
PUBLIC=https://entornovirtual.duckdns.org
TS="$(date +%Y%m%d-%H%M%S)"
COMPOSE=(docker compose -f "$INFRA/compose.prod.yaml" --env-file "$INFRA/.env")

log()  { printf '[deploy] %s\n' "$*"; }
warn() { printf '[aviso ] %s\n' "$*"; }
die()  { printf '[error ] %s\n' "$*" >&2; exit 1; }

mkdir -p "$STATE"

# Un solo despliegue a la vez: dos subidas simultaneas sobre la misma release
# dejarian el .pck y el .wasm de versiones distintas.
exec 9>"$STATE/lock"
flock -n 9 || die "ya hay un despliegue en curso (lock en $STATE/lock)"

need_docker() {
    docker info >/dev/null 2>&1 || die "este usuario no puede hablar con Docker. Ejecuta bootstrap-root.sh como root (anade deploy al grupo docker) y vuelve a entrar por SSH."
}

# --- web -------------------------------------------------------------------
cmd_web() {
    local rel="${1:-}"
    [ -n "$rel" ] || die "uso: deploy.sh web <release>   (mira $RELEASES)"
    local dir="$RELEASES/$rel"
    [ -d "$dir" ]            || die "no existe la release $dir"
    [ -s "$dir/index.html" ] || die "$dir no tiene index.html: subida incompleta"
    [ -s "$dir/index.pck" ]  || die "$dir no tiene index.pck: subida incompleta"
    [ -s "$dir/index.wasm" ] || die "$dir no tiene index.wasm: subida incompleta"

    # El build de Godot NO debe llevar server_config.json dentro: apuntaria a
    # localhost:8001 y romperia el login en produccion. El .pck es un blob, asi
    # que se comprueba por firma de cadena.
    if grep -qa 'server_config\.json' "$dir/index.pck"; then
        warn "el .pck menciona server_config.json - revisa exclude_filter en"
        warn "export_presets.cfg antes de continuar."
        die  "release rechazada por precaucion"
    fi

    # Los .gz se regeneran SIEMPRE aqui dentro. Este es el fallo silencioso mas
    # probable del despliegue manual: nginx tiene gzip_static on y sirve el .gz
    # con preferencia, asi que un .gz viejo junto a un .wasm nuevo mezcla
    # versiones sin dar ningun error.
    log "regenerando .gz de la release"
    find "$dir" -type f \( -name '*.html' -o -name '*.js' -o -name '*.json' -o -name '*.wasm' -o -name '*.svg' \) -print0 | xargs -0 -r gzip -9 -k -f
    chmod -R a+rX "$dir"

    local prev
    prev="$(readlink -f "$LIVE" 2>/dev/null || echo none)"
    echo "$prev" > "$STATE/web.prev"

    # Cambio atomico: mv -T sobre el symlink. No hay ni un instante en que
    # nginx vea un directorio a medias.
    log "activando release $rel"
    ln -sfn "$dir" "$LIVE.tmp.$$"
    mv -Tf "$LIVE.tmp.$$" "$LIVE"

    local code
    code="$(curl -sk -o /dev/null -w '%{http_code}' "$PUBLIC/" || echo 000)"
    if [ "$code" != "200" ]; then
        warn "la portada respondio $code - revirtiendo"
        if [ "$prev" != none ]; then
            ln -sfn "$prev" "$LIVE.tmp.$$"
            mv -Tf "$LIVE.tmp.$$" "$LIVE"
        fi
        die "release $rel revertida"
    fi
    log "portada OK ($code). Release activa: $rel"

    # Retencion: conservar las KEEP mas recientes.
    local n
    n=$(ls -1d "$RELEASES"/*/ 2>/dev/null | wc -l)
    if [ "$n" -gt "$KEEP" ]; then
        ls -1dt "$RELEASES"/*/ | tail -n +$((KEEP+1)) | while read -r old; do
            if [ "$(readlink -f "$old")" != "$(readlink -f "$LIVE")" ]; then
                log "purgando release antigua $(basename "$old")"
                rm -rf "$old"
            fi
        done
    fi
}

cmd_rollback_web() {
    local prev
    prev="$(cat "$STATE/web.prev" 2>/dev/null || echo none)"
    [ "$prev" != none ] && [ -d "$prev" ] || die "no hay release anterior registrada"
    log "volviendo a $prev"
    ln -sfn "$prev" "$LIVE.tmp.$$"
    mv -Tf "$LIVE.tmp.$$" "$LIVE"
    log "hecho: $(readlink -f "$LIVE")"
}

# --- api -------------------------------------------------------------------
cmd_api() {
    need_docker
    local tag="prod-$TS"
    local prev
    prev="$(docker inspect --format '{{.Config.Image}}' vw-api-1 2>/dev/null || echo none)"

    log "construyendo vw-api:$tag"
    API_TAG="$tag" "${COMPOSE[@]}" build api

    log "promocionando"
    API_TAG="$tag" "${COMPOSE[@]}" up -d api

    log "esperando healthcheck"
    local ok=0
    for _ in $(seq 1 30); do
        if [ "$(curl -s -o /dev/null -w '%{http_code}' "$HEALTH" || echo 000)" = "200" ]; then
            ok=1
            break
        fi
        sleep 2
    done

    if [ "$ok" != 1 ]; then
        warn "la API no respondio 200 en /health tras 60 s"
        if [ "$prev" != none ]; then
            warn "revirtiendo a $prev"
            API_TAG="${prev#vw-api:}" "${COMPOSE[@]}" up -d api
        fi
        die "despliegue de API revertido. Log:  docker logs --tail 50 vw-api-1"
    fi

    echo "$prev" > "$STATE/api.prev"
    echo "$tag"  > "$STATE/api.current"
    log "API viva en vw-api:$tag (anterior: $prev)"

    # Conservar solo las ultimas imagenes para no llenar el disco.
    docker images vw-api --format '{{.Tag}}' | grep '^prod-' | sort -r | tail -n +$((KEEP+1)) | while read -r t; do
        log "purgando imagen vw-api:$t"
        docker rmi "vw-api:$t" >/dev/null 2>&1 || true
    done
}

cmd_rollback_api() {
    need_docker
    local prev
    prev="$(cat "$STATE/api.prev" 2>/dev/null || echo none)"
    [ "$prev" != none ] || die "no hay imagen anterior registrada"
    log "volviendo a $prev"
    API_TAG="${prev#vw-api:}" "${COMPOSE[@]}" up -d api
    log "hecho"
}

# --- nginx -----------------------------------------------------------------
cmd_nginx() {
    local src="$INFRA/nginx-vw.conf"
    local dst=/etc/nginx/conf.d/vw.conf
    [ -f "$src" ] || die "falta $src"

    # Salvaguarda: si el fichero del repo no lleva las rutas de LecturaIA es que
    # esta desactualizado, e instalarlo tumbaria la pila del companero.
    local needed
    for needed in '/npc/' '/lecturaia/' '/api/v1/'; do
        grep -q "$needed" "$src" || die "$src no contiene el bloque $needed. Instalarlo dejaria LecturaIA sin rutas. Rescata la config viva primero:  cp $dst $src"
    done

    # Se delega en un wrapper de root con rutas fijas. Deliberadamente NO se le
    # da a deploy un 'sudo cp' generico: eso equivaldria a darle root entero.
    # El wrapper hace backup, valida con nginx -t y revierte solo si falla.
    log "aplicando via /usr/local/sbin/vw-nginx-apply"
    sudo -n /usr/local/sbin/vw-nginx-apply || die "no se aplico la config (ejecuta bootstrap-root.sh como root si aun no lo hiciste)"
}

# --- status ----------------------------------------------------------------
cmd_status() {
    echo "release web activa : $(readlink -f "$LIVE" 2>/dev/null || echo '(no es symlink)')"
    echo "imagen de la API   : $(docker inspect --format '{{.Config.Image}}' vw-api-1 2>/dev/null || echo '(sin acceso a docker)')"
    echo "commit de /opt/vw  : $(git -C "$VW_ROOT" describe --tags --always --dirty 2>/dev/null || echo '?')"
    echo "salud API (8001)   : $(curl -s -o /dev/null -w '%{http_code}' "$HEALTH" || echo 000)"
    echo "portada publica    : $(curl -sk -o /dev/null -w '%{http_code}' "$PUBLIC/" || echo 000)"
    echo "--- ajeno, solo informativo (LecturaIA, no se toca) ---"
    echo "  /npc  (8002)     : $(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8002/health || echo 000)"
    echo "  next  (3001)     : $(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3001/ || echo 000)"
    echo
    echo "releases disponibles:"
    ls -1t "$RELEASES" 2>/dev/null | head -"$KEEP" | sed 's/^/  /'
}

case "${1:-}" in
    web)          shift; cmd_web "${1:-}" ;;
    api)          cmd_api ;;
    nginx)        cmd_nginx ;;
    rollback-web) cmd_rollback_web ;;
    rollback-api) cmd_rollback_api ;;
    status)       cmd_status ;;
    *) sed -n '2,17p' "$0"; exit 1 ;;
esac
