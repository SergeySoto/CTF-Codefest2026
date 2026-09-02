#!/usr/bin/env bash
# Reinicio entre dos jugadores. No toca data/ctf.db: el marcador es acumulativo.
set -euo pipefail
cd "$(dirname "$0")"
[ -f .env ] && set -a && . ./.env && set +a

PERFIL=/tmp/ctf-perfil

pkill -f "user-data-dir=$PERFIL" 2>/dev/null || true   # cerrar Chrome del jugador
rm -rf "$PERFIL"                                       # perfil desechable
rm -rf "$HOME/Descargas"/* "$HOME/Escritorio"/* 2>/dev/null || true
command -v xsel >/dev/null && xsel -bc 2>/dev/null || true   # portapapeles

curl -sf -X POST localhost:8000/admin/reset \
     -H "X-Token: ${CTF_ADMIN_TOKEN}" >/dev/null || echo "aviso: no se pudo cerrar la sesión"

docker compose -f docker-compose.yml restart retos >/dev/null                # retos a su estado inicial

google-chrome --kiosk --incognito \
  --user-data-dir="$PERFIL" \
  --disable-session-crashed-bubble \
  --no-first-run \
  http://localhost:8000 >/dev/null 2>&1 &

echo "Listo para el siguiente jugador."
