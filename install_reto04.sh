#!/usr/bin/env bash
set -euo pipefail

# Codefest CTF - Reto 04
# Ejecutar desde la raiz del proyecto:
#   chmod +x install_reto04.sh
#   ./install_reto04.sh

ROOT="$(pwd)"

if [[ ! -f "$ROOT/platform/app/main.py" ]]; then
    echo "ERROR: ejecuta este script desde la raiz del proyecto codefest."
    exit 1
fi

MAIN="$ROOT/platform/app/main.py"
RETOS="$ROOT/platform/app/retos.json"
RETO_DIR="$ROOT/challenges/sitio/reto-04"
FLAG_TEMPLATE="$ROOT/platform/app/templates/flag.html"

echo "[1/5] Creando pagina del Reto 04..."
mkdir -p "$RETO_DIR"

cat > "$RETO_DIR/index.html" <<'HTML'
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Reto 4</title>
  <link rel="stylesheet" href="/comun/estilo.css">
</head>
<body>
  <main>
    <h1>Reto 4</h1>

    <p class="grande">¿y si la respuesta estuviera en la dirección?</p>

    <p class="apunte">
      <b>Pista.</b> Mira la dirección de la página en la que estás.
      Ahora estás en <b>/jugar</b>. Prueba a cambiarla por <b>/flag</b>.
    </p>
  </main>
</body>
</html>
HTML

echo "[2/5] Actualizando retos.json..."

python3 - "$RETOS" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
flag = "flag{c4mb14_l4_url}"

data = json.loads(path.read_text(encoding="utf-8"))

# Elimina cualquier Reto 04 anterior creado por este script.
data = [reto for reto in data if reto.get("reto") != "Una dirección diferente"]

data.append({
    "codigo": flag,
    "reto": "Una dirección diferente",
    "dificultad": "Fácil",
    "coef": 1,
    "url": "http://localhost:9000/reto-04/"
})

path.write_text(
    json.dumps(data, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
PY

echo "[3/5] Actualizando main.py con /flag..."

python3 - "$MAIN" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

marker = '@app.get("/flag", response_class=HTMLResponse)'

# Quita una version anterior de esta ruta si existe.
start = text.find(marker)
if start != -1:
    next_marker = text.find('\n@app.', start + len(marker))
    if next_marker == -1:
        text = text[:start].rstrip() + "\n"
    else:
        text = text[:start] + text[next_marker + 1:]

needle = '@app.post("/enviar")\n'

route = '''@app.get("/flag", response_class=HTMLResponse)
async def flag(request: Request):
    jugador = jugador_actual(request)
    if not jugador:
        return RedirectResponse("/", status_code=303)
    if not en_curso(jugador):
        return RedirectResponse("/fin", status_code=303)
    return plantillas.TemplateResponse(
        request,
        "flag.html",
        {
            "lluvia": lluvia(),
        },
    )


@app.post("/enviar")
'''

if needle not in text:
    raise SystemExit(
        'ERROR: no se encontro @app.post("/enviar") como punto de insercion.'
    )

text = text.replace(needle, route, 1)
path.write_text(text, encoding="utf-8")
PY

echo "[4/5] Creando platform/app/templates/flag.html..."

cat > "$FLAG_TEMPLATE" <<'HTML'
{% extends "base.html" %}

{% block titulo %}Flag · Codefest CTF{% endblock %}
{% block clase %}pantalla-juego{% endblock %}

{% block contenido %}

<div class="estado">
  <span>codefest ctf</span>
  <span class="rellena"></span>
  <span>destino encontrado</span>
</div>

<main>
  <h1>Reto 4</h1>

  <p class="grande">has encontrado la dirección correcta</p>

  <p class="bandera">flag{c4mb14_l4_url}</p>

  <p class="apunte">
    Copia la bandera y vuelve a la partida para enviarla.
  </p>
</main>

{% endblock %}
HTML

echo "[5/5] Validando..."

python3 - "$RETOS" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8"))

matches = [x for x in data if x.get("codigo") == "flag{c4mb14_l4_url}"]

if len(matches) != 1:
    raise SystemExit("ERROR: la flag del Reto 04 no esta registrada exactamente una vez.")

reto = matches[0]
assert reto["reto"] == "Una dirección diferente"
assert reto["dificultad"] == "Fácil"
assert reto["coef"] == 1
assert reto["url"] == "http://localhost:9000/reto-04/"

print("OK: retos.json")
PY

python3 -m py_compile "$MAIN"

echo
echo "============================================"
echo " Reto 04 instalado correctamente"
echo "============================================"
echo
echo "Reto:"
echo "  http://localhost:9000/reto-04/"
echo
echo "Solucion:"
echo "  http://localhost:8000/flag"
echo
echo "Flag:"
echo "  flag{c4mb14_l4_url}"
echo
echo "No se han tocado docker-compose.yml, nginx ni scoring.py."
echo "Con el override de desarrollo, al guardar se recargan los cambios."
echo "============================================"
