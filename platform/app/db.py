"""Acceso a SQLite. Un solo fichero, sin ORM."""
import os
import sqlite3
from contextlib import contextmanager

RUTA_DB = os.environ.get("CTF_DB", "/data/ctf.db")

ESQUEMA = """
CREATE TABLE IF NOT EXISTS jugadores (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    apodo        TEXT    NOT NULL,
    token        TEXT    NOT NULL UNIQUE,
    empezado_en  REAL    NOT NULL,
    termina_en   REAL    NOT NULL,
    cerrado_en   REAL,
    puntos       INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS banderas (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo     TEXT    NOT NULL UNIQUE,
    reto       TEXT    NOT NULL,
    dificultad TEXT    NOT NULL,
    coef       INTEGER NOT NULL,
    url        TEXT,
    orden      INTEGER NOT NULL DEFAULT 0,
    activa     INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS envios (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    jugador_id INTEGER NOT NULL REFERENCES jugadores(id),
    entrada    TEXT    NOT NULL,
    bandera_id INTEGER REFERENCES banderas(id),
    en         REAL    NOT NULL,
    puntos     INTEGER NOT NULL DEFAULT 0
);

-- una bandera solo puntúa una vez por jugador
CREATE UNIQUE INDEX IF NOT EXISTS idx_envio_unico
    ON envios(jugador_id, bandera_id) WHERE bandera_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_bandera_codigo ON banderas(codigo);
"""


@contextmanager
def conexion():
    con = sqlite3.connect(RUTA_DB, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    try:
        yield con
        con.commit()
    finally:
        con.close()


def inicializar():
    os.makedirs(os.path.dirname(RUTA_DB), exist_ok=True)
    with conexion() as con:
        con.executescript(ESQUEMA)
        # bases creadas antes de que existiera la columna de orden
        columnas = {f["name"] for f in con.execute("PRAGMA table_info(banderas)")}
        if "orden" not in columnas:
            con.execute("ALTER TABLE banderas ADD COLUMN orden INTEGER NOT NULL DEFAULT 0")


def cargar_banderas(retos):
    """retos.json manda: lo que no esté ahí deja de estar activo.

    Las banderas retiradas no se borran (los envíos antiguos las referencian),
    solo se desactivan. Sin esto, cambiar un código deja el viejo en juego.
    """
    with conexion() as con:
        for i, r in enumerate(retos):
            con.execute(
                """INSERT INTO banderas (codigo, reto, dificultad, coef, url, orden, activa)
                   VALUES (?, ?, ?, ?, ?, ?, 1)
                   ON CONFLICT(codigo) DO UPDATE SET
                       reto=excluded.reto,
                       dificultad=excluded.dificultad,
                       coef=excluded.coef,
                       url=excluded.url,
                       orden=excluded.orden,
                       activa=1""",
                (r["codigo"], r["reto"], r["dificultad"], r["coef"], r.get("url"), i),
            )
        vigentes = [r["codigo"] for r in retos]
        con.execute(
            "UPDATE banderas SET activa = 0 WHERE codigo NOT IN (%s)"
            % ",".join("?" * len(vigentes)),
            vigentes,
        )
