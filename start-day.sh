#!/usr/bin/env bash
# Arranque de la mañana. Levanta todo y abre las dos pantallas.
set -euo pipefail
cd "$(dirname "$0")"
docker compose -f docker-compose.yml up -d --build

echo -n "Esperando a la plataforma"
until curl -sf localhost:8000/ >/dev/null; do echo -n "."; sleep 1; done
echo " lista."

# Pantalla pública del marcador. Esta sí va en kiosco: nadie la toca y
# conviene que esté bien cerrada. Perfil aparte, para que reset.sh no la cierre.
google-chrome --kiosk --user-data-dir=/tmp/ctf-marcador \
  --no-first-run http://localhost:8000/marcador >/dev/null 2>&1 &

./reset.sh
