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
GODOT_REPO="$(cd "$HERE/../.." && pwd)/virtual-world-reading-ai"
WEB_BUILD="$(cd "$HERE/../.." && pwd)/web_build"
RELEASES=/var/www/vw-releases
TS="$(date +%Y%m%d-%H%M%S)"

SSH=(ssh -i "$SSH_KEY" -o StrictHostKeyChecking=accept-new "$HOST")

log()  { printf '[push] %s\n' "$*"; }
die()  { printf '[error] %s\n' "$*" >&2; exit 1; }

# Exige que un repo este limpio y pusheado. Si no, lo que corra en produccion
# no seria un commit identificable y no se podria reproducir ni revertir.
check_clean() {
    local repo="$1" nombre="$2"
    [ -d "$repo/.git" ] || die "no encuentro el repo de $nombre en $repo"
    git -C "$repo" diff --quiet && git -C "$repo" diff --cached --quiet \
        || die "el repo de $nombre ($repo) tiene cambios sin commitear. Commitea antes de desplegar."
    local branch
    branch="$(git -C "$repo" rev-parse --abbrev-ref HEAD)"
    git -C "$repo" fetch origin --quiet
    if [ -n "$(git -C "$repo" log "origin/$branch..HEAD" --oneline 2>/dev/null)" ]; then
        die "hay commits sin pushear en $nombre ($branch). Ejecuta: git -C '$repo' push origin '$branch'"
    fi
}

push_web() {
    # El build sale del repo de Godot, asi que es ESE el que tiene que estar
    # limpio y pusheado para poder decir que commit corre en produccion.
    check_clean "$GODOT_REPO" "el juego Godot"

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

    # Trazabilidad: de que commit salio este build. Se guarda FUERA del
    # directorio servido (fichero hermano) para no publicarlo por HTTP.
    printf 'release=%s\njuego=%s @ %s\nbackend=%s @ %s\nexportado=%s\ndesplegado_por=%s\n' \
        "$TS" \
        "$(git -C "$GODOT_REPO" rev-parse --abbrev-ref HEAD)" \
        "$(git -C "$GODOT_REPO" rev-parse --short HEAD)" \
        "$(git -C "$REPO" rev-parse --abbrev-ref HEAD)" \
        "$(git -C "$REPO" rev-parse --short HEAD)" \
        "$(date -r "$WEB_BUILD/index.pck" '+%Y-%m-%d %H:%M' 2>/dev/null || echo '?')" \
        "${USERNAME:-$USER}" \
        | "${SSH[@]}" "cat > $RELEASES/$TS.info"

    log "activando"
    "${SSH[@]}" "/opt/vw/infra/deploy.sh web $TS"
}

push_code() {
    check_clean "$REPO" "el backend"
    local commit branch
    commit="$(git -C "$REPO" rev-parse HEAD)"
    branch="$(git -C "$REPO" rev-parse --abbrev-ref HEAD)"

    # El codigo viaja por SSH, NO con un git pull en el servidor. El repo es
    # privado y el servidor no tiene credenciales de GitHub: alli 'git fetch'
    # falla con "could not read Username for https://github.com". Enviar un
    # git archive del commit ya pusheado conserva la propiedad que importa
    # -- lo desplegado es un commit identificable -- sin tener que gestionar
    # una credencial mas en la maquina.
    log "enviando $branch @ ${commit:0:8} a /opt/vw"
    git -C "$REPO" archive --format=tar "$commit" \
        | "${SSH[@]}" "rm -rf /opt/vw/.incoming && mkdir -p /opt/vw/.incoming && tar -xf - -C /opt/vw/.incoming"

    # rsync --delete deja /opt/vw exactamente como el commit, pero infra/.env
    # es la unica copia de JWT_SECRET_KEY y no esta en git: se excluye siempre.
    "${SSH[@]}" "rsync -a --delete --exclude 'infra/.env' --exclude '.git' --exclude '.incoming' --exclude '.deploy-state' /opt/vw/.incoming/ /opt/vw/ \
        && rm -rf /opt/vw/.incoming \
        && printf '%s\n' '$branch $commit' > /opt/vw/.deployed-commit \
        && chmod +x /opt/vw/infra/*.sh"

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
