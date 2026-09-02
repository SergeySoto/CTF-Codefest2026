"""Plataforma del CTF: reglas, juego, marcador."""
import json
import os
import pathlib
import random
import secrets
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Form, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import db
from .scoring import normalizar, puntos

BASE = pathlib.Path(__file__).parent
DURACION = int(os.environ.get("CTF_DURACION", 300))
COOKIE = "ctf_jugador"

plantillas = Jinja2Templates(directory=BASE / "templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.inicializar()
    db.cargar_banderas(json.loads((BASE / "retos.json").read_text(encoding="utf-8")))
    yield


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


# ---------------------------------------------------------------- utilidades

def jugador_actual(request: Request):
    token = request.cookies.get(COOKIE)
    if not token:
        return None
    with db.conexion() as con:
        return con.execute(
            "SELECT * FROM jugadores WHERE token = ?", (token,)
        ).fetchone()


def restantes(jugador) -> float:
    return max(0.0, jugador["termina_en"] - time.time())


def en_curso(jugador) -> bool:
    """Sesión viva: queda tiempo y nadie la ha cerrado."""
    return jugador is not None and jugador["cerrado_en"] is None and restantes(jugador) > 0


# Alfabeto de la lluvia. Glifos que la VT323 tiene de verdad: si metiéramos
# katakana caería en otra fuente y se rompería la rejilla de caracteres.
ALFABETO = "0123456789ABCDEF{}[]<>/\\|=+*·:."

# Reto 1: una de las columnas de la lluvia lleva la bandera. Va en minúsculas,
# así que destaca entre el ruido en mayúsculas para quien se fije.
BANDERA_LLUVIA = "flag{lluvia_de_d4t0s}"

# Reto 2: la bandera es el NOMBRE de una cookie. Se reparte desde la pantalla
# de juego y no desde la página del reto, que se carga dentro de un marco:
# una navegación de primer nivel no depende ni de la caché del navegador ni
# de cómo trate Chrome las cookies dentro de un iframe.
BANDERA_COOKIE = "flag{c00k13_d3_4dm1n}"
RELLENO_COOKIES = [("idioma", "es"), ("tema", "oscuro"), ("consentimiento", "1")]


def repartir_cookies(respuesta):
    """No se puede usar respuesta.set_cookie(): el módulo cookies de Python
    rechaza las llaves en el nombre (RFC 6265), aunque el navegador las
    acepte. Se escribe la cabecera a mano."""
    galletas = RELLENO_COOKIES + [(BANDERA_COOKIE, secrets.token_hex(16))]
    for nombre, valor in galletas:
        respuesta.headers.append(
            "set-cookie",
            f"{nombre}={valor}; Path=/; Max-Age=7200; SameSite=Lax",
        )
    return respuesta


def lluvia(columnas: int = 26, con_bandera: bool = False):
    """Columnas de código cayendo, generadas en el servidor: cero JS.

    La columna portadora solo cae en la pantalla de juego. En el marcador
    (segunda pantalla, a la vista de toda la cola) la bandera se leería desde
    el otro lado de la sala y el reto dejaría de serlo.
    """
    rnd = random.Random()
    # En la mitad derecha: a la izquierda el reloj y su halo se comen el fondo,
    # y en las columnas del borde la pantalla recorta los caracteres.
    portadora = rnd.randrange(columnas // 2 + 1, columnas - 3) if con_bandera else -1
    gotas = []
    for i in range(columnas):
        if i == portadora:
            texto = BANDERA_LLUVIA
            # más lenta y con su propio desvanecido: si cayera como las demás,
            # el degradado se comería medio código y no habría reto, solo suerte
            dur, clave = round(rnd.uniform(19.0, 24.0), 1), True
        else:
            texto = "".join(rnd.choice(ALFABETO) for _ in range(34))
            dur, clave = round(rnd.uniform(7.5, 17.0), 1), False
        gotas.append({
            "texto": texto,
            "izq": round(i * (100 / columnas) + rnd.uniform(-1.2, 1.2), 2),
            "dur": dur,
            "esp": round(rnd.uniform(-14.0, 0.0), 1),
            "clave": clave,
        })
    return gotas


def retos_con_estado(jugador_id: int):
    """Lista de retos; marca los que este jugador ya ha validado."""
    with db.conexion() as con:
        return con.execute(
            """SELECT b.id, b.reto, b.dificultad, b.coef, b.url,
                      (e.id IS NOT NULL) AS encontrada
               FROM banderas b
               LEFT JOIN envios e
                    ON e.bandera_id = b.id AND e.jugador_id = ?
               WHERE b.activa = 1
               ORDER BY b.orden, b.id""",
            (jugador_id,),
        ).fetchall()


def clasificacion(limite: int = 15):
    with db.conexion() as con:
        return con.execute(
            "SELECT id, apodo, puntos FROM jugadores "
            "ORDER BY puntos DESC, empezado_en LIMIT ?",
            (limite,),
        ).fetchall()


# ------------------------------------------------------------------- páginas

@app.get("/", response_class=HTMLResponse)
async def inicio(request: Request):
    # Si alguien ha salido sin querer, aquí puede volver a lo suyo.
    jugador = jugador_actual(request)
    activa = jugador if en_curso(jugador) else None
    return plantillas.TemplateResponse(
        request,
        "inicio.html",
        {
            "duracion": DURACION // 60,
            "activa": activa,
            "quedan": int(restantes(activa)) if activa else 0,
            "lluvia": lluvia(),
        },
    )


@app.post("/empezar")
async def empezar(apodo: str = Form(...)):
    apodo = apodo.strip()[:24] or "Anónimo"
    token = secrets.token_urlsafe(16)
    ahora = time.time()
    with db.conexion() as con:
        con.execute(
            """INSERT INTO jugadores (apodo, token, empezado_en, termina_en)
               VALUES (?, ?, ?, ?)""",
            (apodo, token, ahora, ahora + DURACION),
        )
    respuesta = RedirectResponse("/jugar", status_code=303)
    respuesta.set_cookie(COOKIE, token, httponly=True, samesite="lax")
    return respuesta


@app.get("/jugar", response_class=HTMLResponse)
async def jugar(request: Request):
    jugador = jugador_actual(request)
    if not jugador:
        return RedirectResponse("/", status_code=303)
    if not en_curso(jugador):
        return RedirectResponse("/fin", status_code=303)
    return repartir_cookies(plantillas.TemplateResponse(
        request,
        "jugar.html",
        {
            "jugador": jugador,
            "retos": retos_con_estado(jugador["id"]),
            "restantes": int(restantes(jugador)),
            "duracion": DURACION,
            "lluvia": lluvia(con_bandera=True),
        },
    ))


@app.post("/enviar")
async def enviar(request: Request, bandera: str = Form(...)):
    jugador = jugador_actual(request)
    if not jugador:
        return JSONResponse({"estado": "sin_sesion"}, status_code=401)

    queda = restantes(jugador)
    if queda <= 0:
        return JSONResponse({"estado": "tiempo_agotado"})

    ahora = time.time()
    with db.conexion() as con:
        # anti-bruteforce: un envío por segundo
        ultimo = con.execute(
            "SELECT MAX(en) AS en FROM envios WHERE jugador_id = ?",
            (jugador["id"],),
        ).fetchone()["en"]
        if ultimo and ahora - ultimo < 1.0:
            return JSONResponse({"estado": "demasiado_rapido"})

        fila = con.execute(
            "SELECT * FROM banderas WHERE activa = 1"
        ).fetchall()
        objetivo = normalizar(bandera)
        acierto = next((b for b in fila if normalizar(b["codigo"]) == objetivo), None)

        if acierto is None:
            con.execute(
                "INSERT INTO envios (jugador_id, entrada, bandera_id, en, puntos) "
                "VALUES (?, ?, NULL, ?, 0)",
                (jugador["id"], bandera[:120], ahora),
            )
            return JSONResponse({"estado": "incorrecta"})

        ya = con.execute(
            "SELECT 1 FROM envios WHERE jugador_id = ? AND bandera_id = ?",
            (jugador["id"], acierto["id"]),
        ).fetchone()
        if ya:
            return JSONResponse({"estado": "repetida", "reto": acierto["reto"]})

        ganados = puntos(acierto["coef"], queda)
        con.execute(
            "INSERT INTO envios (jugador_id, entrada, bandera_id, en, puntos) "
            "VALUES (?, ?, ?, ?, ?)",
            (jugador["id"], bandera[:120], acierto["id"], ahora, ganados),
        )
        con.execute(
            "UPDATE jugadores SET puntos = puntos + ? WHERE id = ?",
            (ganados, jugador["id"]),
        )
        total = con.execute(
            "SELECT puntos FROM jugadores WHERE id = ?", (jugador["id"],)
        ).fetchone()["puntos"]

    return JSONResponse(
        {
            "estado": "correcta",
            "bandera_id": acierto["id"],
            "reto": acierto["reto"],
            "puntos": ganados,
            "total": total,
        }
    )


@app.post("/salir")
async def salir(request: Request):
    """Salida voluntaria. Cierra la sesión: no se puede volver a ella."""
    jugador = jugador_actual(request)
    if jugador:
        with db.conexion() as con:
            con.execute(
                "UPDATE jugadores SET cerrado_en = ? WHERE id = ? AND cerrado_en IS NULL",
                (time.time(), jugador["id"]),
            )
    return RedirectResponse("/fin", status_code=303)


@app.get("/api/estado")
async def estado(request: Request):
    """El JS del cronómetro se sincroniza con el servidor, no con el reloj del PC."""
    jugador = jugador_actual(request)
    if not jugador:
        return JSONResponse({"estado": "sin_sesion"}, status_code=401)
    return JSONResponse(
        {
            "restantes": int(restantes(jugador)),
            "duracion": DURACION,
            "puntos": jugador["puntos"],
        }
    )


@app.get("/fin", response_class=HTMLResponse)
async def fin(request: Request):
    jugador = jugador_actual(request)
    if not jugador:
        return RedirectResponse("/", status_code=303)
    # Llegar aquí con tiempo por delante y sin haber pulsado SALIR es un
    # accidente: se devuelve al jugador a su partida en vez de terminarla.
    if en_curso(jugador):
        return RedirectResponse("/jugar", status_code=303)
    with db.conexion() as con:
        con.execute(
            "UPDATE jugadores SET cerrado_en = ? WHERE id = ? AND cerrado_en IS NULL",
            (time.time(), jugador["id"]),
        )
        posicion = con.execute(
            "SELECT COUNT(*) + 1 AS p FROM jugadores WHERE puntos > ?",
            (jugador["puntos"],),
        ).fetchone()["p"]
        encontradas = con.execute(
            """SELECT b.reto, e.puntos FROM envios e
               JOIN banderas b ON b.id = e.bandera_id
               WHERE e.jugador_id = ? ORDER BY e.en""",
            (jugador["id"],),
        ).fetchall()
    top = clasificacion(10)
    # si el jugador se ha quedado fuera del top, su fila se añade igualmente:
    # nadie debe terminar sin verse en la lista.
    fuera = not any(f["id"] == jugador["id"] for f in top)
    respuesta = plantillas.TemplateResponse(
        request,
        "fin.html",
        {
            "jugador": jugador,
            "posicion": posicion,
            "encontradas": encontradas,
            "top": top,
            "fuera": fuera,
            "lluvia": lluvia(),
        },
    )
    respuesta.delete_cookie(COOKIE)
    return respuesta


@app.get("/marcador", response_class=HTMLResponse)
async def marcador(request: Request, volver: int = 0):
    # `volver` solo lo pone el enlace de la pantalla de inicio. La pantalla
    # pública del stand abre /marcador a secas y no enseña ningún botón.
    top = clasificacion(15)
    with db.conexion() as con:
        total = con.execute("SELECT COUNT(*) AS n FROM jugadores").fetchone()["n"]
    return plantillas.TemplateResponse(
        request,
        "marcador.html",
        {"top": top, "total": total, "volver": bool(volver), "lluvia": lluvia()},
    )


@app.get("/api/marcador")
async def api_marcador():
    return JSONResponse([
        {"apodo": f["apodo"], "puntos": f["puntos"]} for f in clasificacion(15)
    ])
