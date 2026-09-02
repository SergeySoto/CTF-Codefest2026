#!/usr/bin/env bash
# Reinicio entre dos jugadores. No toca data/ctf.db: el marcador es acumulativo.
set -euo pipefail
cd "$(dirname "$0")"
PERFIL=/tmp/ctf-perfil

pkill -f "user-data-dir=$PERFIL" 2>/dev/null || true   # cerrar Chrome del jugador
rm -rf "$PERFIL"                                       # perfil desechable
rm -rf "$HOME/Descargas"/* "$HOME/Escritorio"/* 2>/dev/null || true
command -v xsel >/dev/null && xsel -bc 2>/dev/null || true   # portapapeles

# No hace falta avisar al servidor: sin perfil no hay cookie, así que el
# siguiente jugador no puede caer en la partida del anterior, y una sesión
# abandonada caduca sola a los cinco minutos.
docker compose -f docker-compose.yml restart retos >/dev/null                # retos a su estado inicial

# --app y no --kiosk: el modo kiosco de Chrome desactiva las herramientas de
# desarrollo, y el Reto 2 se resuelve justamente ahí. --app da la misma
# ventana sin barra de direcciones ni pestañas, pero con F12 disponible.
google-chrome --app=http://localhost:8000 \
  --start-fullscreen \
  --user-data-dir="$PERFIL" \
  --disable-session-crashed-bubble \
  --no-first-run \
  --no-default-browser-check >/dev/null 2>&1 &

echo "Listo para el siguiente jugador."
