#!/usr/bin/env bash
# Arranque de la mañana. Levanta todo y abre las dos pantallas.
set -euo pipefail
cd "$(dirname "$0")"
[ -f .env ] || { echo "Falta .env — copia .env.example y cambia el token."; exit 1; }

docker compose -f docker-compose.yml up -d --build

echo -n "Esperando a la plataforma"
until curl -sf localhost:8000/ >/dev/null; do echo -n "."; sleep 1; done
echo " lista."

# Pantalla pública del marcador (perfil aparte: reset.sh no la cierra)
google-chrome --kiosk --user-data-dir=/tmp/ctf-marcador \
  --no-first-run http://localhost:8000/marcador >/dev/null 2>&1 &

./reset.sh
