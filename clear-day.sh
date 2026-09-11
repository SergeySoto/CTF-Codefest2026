#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

docker compose -f docker-compose.yml exec -T plataforma \
  python -c "
import sqlite3
con = sqlite3.connect('/data/ctf.db')
con.execute('PRAGMA foreign_keys = ON')
jugadores = con.execute('SELECT COUNT(*) FROM jugadores').fetchone()[0]
envios = con.execute('SELECT COUNT(*) FROM envios').fetchone()[0]
con.execute('DELETE FROM envios')
con.execute('DELETE FROM jugadores')
con.commit()
print(f'Jugadores eliminados: {jugadores}')
print(f'Envios eliminados: {envios}')
con.close()
"

echo "Jugadores, puntuaciones y envíos eliminados."