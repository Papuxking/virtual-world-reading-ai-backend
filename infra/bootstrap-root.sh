#!/usr/bin/env bash
# ============================================================================
#  ARRANQUE — SE EJECUTA UNA SOLA VEZ, COMO ROOT, EN EL SERVIDOR
#      bash bootstrap-root.sh
#
#  Deja el servidor preparado para que TODO despliegue posterior se pueda
#  hacer con la clave SSH de 'deploy', sin volver a entrar como root.
#
#  Que hace, y por que:
#   1. deploy -> grupo docker         : hoy deploy no puede ni listar contenedores.
#   2. sudoers acotado                : deploy podra recargar nginx y NADA MAS.
#                                       No se le da 'sudo cp' (equivale a root):
#                                       se le da un unico wrapper de root con
#                                       origen y destino fijos.
#   3. /var/www/vw pasa a symlink     : despliegue atomico y rollback instantaneo.
#                                       Hoy es un directorio que se sobreescribe
#                                       encima, que es como se mezclan versiones.
#   4. /var/backups/vw                : destino de backup.sh.
#   5. cron diario de backup          : ahora mismo NO hay ninguna copia.
#
#  Que NO hace: no toca /opt/lecturaia, ni sus contenedores (8002/3001/5433),
#  ni su base de datos, ni el usuario que los ejecuta. Solo lee la config de
#  nginx, que es compartida, y la conserva intacta.
#
#  Idempotente: se puede volver a ejecutar sin romper nada.
# ============================================================================
set -euo pipefail

[ "$(id -u)" = 0 ] || { echo "Esto hay que ejecutarlo como root." >&2; exit 1; }

TS="$(date +%Y%m%d-%H%M%S)"
DEPLOY_USER=deploy
RELEASES=/var/www/vw-releases
LIVE=/var/www/vw

log() { printf '\n[bootstrap] %s\n' "$*"; }

# --- 1. acceso a Docker ----------------------------------------------------
log "1/5  anadiendo $DEPLOY_USER al grupo docker"
if id -nG "$DEPLOY_USER" | tr ' ' '\n' | grep -qx docker; then
    echo "     ya estaba"
else
    usermod -aG docker "$DEPLOY_USER"
    echo "     hecho (surte efecto en la proxima sesion SSH)"
fi

# --- 2. sudoers acotado + wrapper de nginx ---------------------------------
log "2/5  wrapper de nginx y sudoers acotado"
cat > /usr/local/sbin/vw-nginx-apply <<'WRAPPER'
#!/usr/bin/env bash
# Instala /opt/vw/infra/nginx-vw.conf como /etc/nginx/conf.d/vw.conf.
# Origen y destino son FIJOS a proposito: este script se ejecuta via sudo sin
# contrasena, asi que no debe aceptar rutas por argumento.
set -euo pipefail
SRC=/opt/vw/infra/nginx-vw.conf
DST=/etc/nginx/conf.d/vw.conf
TS="$(date +%Y%m%d-%H%M%S)"

[ -f "$SRC" ] || { echo "falta $SRC" >&2; exit 1; }

# Salvaguarda: LecturaIA es de otro autor. Si el fichero entrante no trae sus
# rutas, esta desactualizado y aplicarlo la dejaria sin servicio.
for needed in '/npc/' '/lecturaia/' '/api/v1/'; do
    grep -q "$needed" "$SRC" || {
        echo "ABORTADO: $SRC no contiene el bloque $needed." >&2
        echo "Aplicarlo dejaria LecturaIA sin rutas. Rescata la config viva:" >&2
        echo "  cp $DST $SRC" >&2
        exit 1
    }
done

cp -a "$DST" "$DST.bak-$TS"
cp "$SRC" "$DST"
if ! nginx -t; then
    echo "nginx -t fallo: restaurando $DST.bak-$TS" >&2
    cp -a "$DST.bak-$TS" "$DST"
    nginx -t
    exit 1
fi
systemctl reload nginx
echo "nginx recargado (copia previa en $DST.bak-$TS)"

# Conservar solo los 10 backups mas recientes de la config.
ls -1t "$DST".bak-* 2>/dev/null | tail -n +11 | xargs -r rm -f
WRAPPER
chmod 0755 /usr/local/sbin/vw-nginx-apply
chown root:root /usr/local/sbin/vw-nginx-apply

cat > /etc/sudoers.d/deploy-vw <<SUDOERS
# Despliegue del entorno virtual. Acotado a proposito: 'deploy' NO tiene sudo
# general. Solo puede aplicar la config de nginx a traves de un wrapper de root
# con rutas fijas, y consultar el estado del servicio.
$DEPLOY_USER ALL=(root) NOPASSWD: /usr/local/sbin/vw-nginx-apply
$DEPLOY_USER ALL=(root) NOPASSWD: /usr/bin/systemctl status nginx
SUDOERS
chmod 0440 /etc/sudoers.d/deploy-vw
visudo -cf /etc/sudoers.d/deploy-vw
echo "     sudoers validado"

# --- 3. /var/www/vw -> symlink a releases ----------------------------------
log "3/5  convirtiendo $LIVE en symlink de release"
mkdir -p "$RELEASES"
if [ -L "$LIVE" ]; then
    echo "     ya era un symlink -> $(readlink -f "$LIVE")"
else
    REL="$RELEASES/$TS-inicial"
    echo "     copiando el contenido actual a $REL"
    cp -a "$LIVE" "$REL"
    mv "$LIVE" "$LIVE.old-$TS"
    ln -sfn "$REL" "$LIVE"
    rm -rf "$LIVE.old-$TS"
    echo "     hecho: $LIVE -> $REL"
fi

# El backup manual del 18-ago se conserva como release, asi sirve de destino
# de rollback en vez de quedarse como carpeta suelta.
if [ -d /var/www/vw.bak-20260818-174212 ] && [ ! -d "$RELEASES/20260818-174212-manual" ]; then
    mv /var/www/vw.bak-20260818-174212 "$RELEASES/20260818-174212-manual"
    echo "     backup manual del 18-ago archivado como release"
fi

chown -R "$DEPLOY_USER":nginx "$RELEASES"
chmod -R a+rX "$RELEASES"
chown -h "$DEPLOY_USER":nginx "$LIVE"

# Ser dueno del symlink NO basta para reemplazarlo: el intercambio atomico de
# deploy.sh crea $LIVE.tmp.$$ dentro de /var/www y lo mueve encima, y eso exige
# escritura en el DIRECTORIO PADRE. Sin esta linea 'deploy.sh web' muere con
# "ln: failed to create symbolic link: Permission denied" y la release se queda
# subida pero sin activar, sirviendo la version anterior sin dar error.
chown root:"$DEPLOY_USER" /var/www
chmod 775 /var/www
# vw-dashboard sigue siendo directorio normal, pero deploy debe poder escribirlo.
chown -R "$DEPLOY_USER":nginx /var/www/vw-dashboard
chmod -R a+rX /var/www/vw-dashboard

# --- 4. destino de backups -------------------------------------------------
log "4/5  /var/backups/vw"
mkdir -p /var/backups/vw
chown "$DEPLOY_USER":"$DEPLOY_USER" /var/backups/vw
chmod 700 /var/backups/vw
echo "     listo"

# --- 5. cron diario de backup ---------------------------------------------
log "5/5  cron diario de backup (03:30)"
cat > /etc/cron.d/vw-backup <<CRON
# Copia diaria del entorno virtual. NO toca LecturaIA.
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
30 3 * * * $DEPLOY_USER /opt/vw/infra/backup.sh >> /var/log/vw-backup.log 2>&1
CRON
chmod 0644 /etc/cron.d/vw-backup
touch /var/log/vw-backup.log
chown "$DEPLOY_USER":"$DEPLOY_USER" /var/log/vw-backup.log
echo "     instalado en /etc/cron.d/vw-backup"

log "ARRANQUE COMPLETADO"
cat <<FIN

  Comprobacion rapida (desde tu equipo, con la clave de deploy):
    ssh vw 'docker ps --format "{{.Names}}"'      # ya no deberia dar permission denied
    ssh vw '/opt/vw/infra/deploy.sh status'

  Pendiente y NO automatizable desde aqui:
    - Activar Backups en la consola de Hetzner (Server > Backups). Es la unica
      copia que sobrevive a que este disco se pierda entero.
    - Endurecer SSH (deshabilitar login de root por contrasena). No lo hace este
      script a proposito: si algo va mal con la clave de deploy te quedas fuera.
      Hazlo solo despues de verificar que la clave funciona, y con la consola
      de rescate de Hetzner a mano.

FIN
