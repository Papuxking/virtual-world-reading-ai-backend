#!/usr/bin/env bash
# ============================================================================
#  Subida desde LOCAL (Git Bash en Windows) al servidor.
#      Docker/infra/push.sh web     sube web_build/ y activa la release
#      Docker/infra/push.sh code    sincroniza /opt/vw con el commit pusheado
#      Docker/infra/push.sh all     las dos cosas, en orden
#
#  No usa rsync: Git Bash no lo trae. Va con tar sobre ssh, que ademas
#  comprime en transito (los 90 MB del build bajan a ~20 MB reales).
#
#  Requisito previo: haber hecho commit y push de lo que se despliega. El
#  script lo verifica y aborta si el arbol esta sucio, para que lo que corre
#  en produccion sea siempre un commit identificable.
# ============================================================================
set -euo pipefail

SSH_KEY="${SSH_KEY:-$HOME/.ssh/vw_deploy}"
HOST="${VW_HOST:-deploy@entornovirtual.duckdns.org}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"          # PROYECTO/Docker  (repo del backend)
WEB_BUILD="$(cd "$HERE/../.." && pwd)/web_build"
RELEASES=/var/www/vw-releases
TS="$(date +%Y%m%d-%H%M%S)"

SSH=(ssh -i "$SSH_KEY" -o StrictHostKeyChecking=accept-new "$HOST")

log()  { printf '[push] %s\n' "$*"; }
die()  { printf '[error] %s\n' "$*" >&2; exit 1; }

check_clean() {
    git -C "$REPO" diff --quiet && git -C "$REPO" diff --cached --quiet \
        || die "el repo $REPO tiene cambios sin commitear. Commitea y pushea antes de desplegar."
    local branch upstream
    branch="$(git -C "$REPO" rev-parse --abbrev-ref HEAD)"
    upstream="origin/$branch"
    git -C "$REPO" fetch origin --quiet
    if [ -n "$(git -C "$REPO" log "$upstream..HEAD" --oneline 2>/dev/null)" ]; then
        die "hay commits sin pushear en $branch. Ejecuta: git push origin $branch"
    fi
}

push_web() {
    [ -s "$WEB_BUILD/index.html" ] || die "no encuentro $WEB_BUILD/index.html - exporta desde Godot primero"
    [ -s "$WEB_BUILD/index.pck" ]  || die "falta index.pck en $WEB_BUILD"
    [ -s "$WEB_BUILD/index.wasm" ] || die "falta index.wasm en $WEB_BUILD"

    # Comprobacion en local, antes de gastar la subida: si el .pck lleva dentro
    # server_config.json, el juego apuntara a localhost:8001 en produccion.
    if grep -qa 'server_config\.json' "$WEB_BUILD/index.pck"; then
        die "el .pck contiene server_config.json. Revisa exclude_filter en export_presets.cfg y reexporta."
    fi

    # Los .gz NO se suben: los regenera deploy.sh en el servidor a partir de los
    # ficheros recien subidos. Asi es imposible que quede un .gz viejo servido
    # por gzip_static junto a un .wasm nuevo.
    log "creando release $TS en el servidor"
    "${SSH[@]}" "mkdir -p $RELEASES/$TS"

    log "subiendo $(du -sh "$WEB_BUILD" | cut -f1) desde $WEB_BUILD"
    tar -czf - -C "$WEB_BUILD" --exclude='*.gz' . \
        | "${SSH[@]}" "tar -xzf - -C $RELEASES/$TS"

    log "activando"
    "${SSH[@]}" "/opt/vw/infra/deploy.sh web $TS"
}

push_code() {
    check_clean
    local commit
    commit="$(git -C "$REPO" rev-parse HEAD)"
    local branch
    branch="$(git -C "$REPO" rev-parse --abbrev-ref HEAD)"
    log "sincronizando /opt/vw con $branch @ ${commit:0:8}"
    # --hard es seguro AQUI porque el arranque dejo /opt/vw limpio y desde
    # entonces el servidor no es sitio donde editar: se edita en local.
    "${SSH[@]}" "cd /opt/vw && git fetch origin && git checkout $branch && git reset --hard $commit"
    log "reconstruyendo API"
    "${SSH[@]}" "/opt/vw/infra/deploy.sh api"
}

case "${1:-}" in
    web)  push_web ;;
    code) push_code ;;
    all)  push_code; push_web ;;
    *)    sed -n '2,14p' "$0"; exit 1 ;;
esac

log "listo. Estado:"
"${SSH[@]}" "/opt/vw/infra/deploy.sh status"
