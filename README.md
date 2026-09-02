# CTF Codefest 2026

Mini-CTF de stand: **5 minutos por persona**, en **un solo ordenador**, en **español**.
Público general, sin conocimientos técnicos.

---

## Cómo funciona

Cada jugador dispone de 5 minutos para encontrar y validar el máximo de banderas.
Los puntos bajan según pasa el tiempo, y **una bandera ya encontrada por otra persona sigue siendo válida**:
quien escucha al jugador anterior la valida en 10 segundos y se lleva casi todos los puntos.

El boca a boca es la mecánica principal del juego.

## Reglas

1. 5 minutos por jugador. El cronómetro arranca al pulsar `EMPEZAR`, no antes.
2. **Una sola caja** para todas las banderas: el sistema reconoce cuál es.
3. Formato de bandera: `flag{...}`. Se acepta con espacios de más y en cualquier caja.
4. Fallar no resta puntos, solo tiempo.
5. Los retos se abren **dentro de la pantalla**, sin perder de vista el reloj.
6. Se puede salir a propósito con un botón; si se sale sin querer, la partida
   se recupera desde la pantalla de inicio con el tiempo que quedaba.
7. Al acabar el tiempo se ve el tanteo **y el marcador**, con la fila del
   jugador señalada. Si ha quedado fuera del top, su fila se añade igualmente.
8. El marcador también se consulta desde la pantalla de inicio.
9. Las reglas se muestran en pantalla y se explican en voz alta antes de empezar.
10. Al final del día, quien más puntos tenga se lleva el premio.

### Los retos

| # | Dificultad | Dónde está la bandera | Habilidad |
|---|---|---|---|
| 0 | `Fácil` | en la sugerencia de la propia caja de texto | fijarse |
| 1 | `Fácil` | en un comentario del código fuente de `/reto-01/` | ver código fuente |
| 2 | `Media` | cayendo en la lluvia del fondo, en la pantalla de juego | observar |
| 3 | `Difícil` | **pendiente de escribir** | — |

El Reto 0 existe para que **nadie se vaya con cero puntos**: se descubre
pulsando en la caja o mirando el código de la página.

El Reto 2 solo cae en la pantalla de juego, nunca en el marcador: en la
segunda pantalla, a la vista de la cola, la bandera se leería desde el otro
lado de la sala. Su columna baja más despacio y casi no se desvanece, para
que se pueda leer entera; es la única escrita en minúsculas.

Las banderas viven en `platform/app/retos.json` y en la página de cada reto.
Al cambiar una hay que tocar los dos sitios.

## Puntuación

```
puntos = coeficiente(dificultad) × segundos restantes
```

| Dificultad | Coef. | Máximo |
|---|---|---|
| `Fácil`   | ×1 | 300 |
| `Media`   | ×2 | 600 |
| `Difícil` | ×3 | 900 |

Ejemplo: una bandera `Media` validada a 60 s del final da 120 puntos; la misma validada a
290 s del final da 580. La diferencia es intencionada: ayudar tiene que salir más rentable que callarse.

---

## Arquitectura

Todo local en el ordenador del stand. Sin dependencia de la red el día del evento.

```
docker compose
├── plataforma  :8000   reglas, juego, marcador (FastAPI + SQLite)
└── retos       :9000   todos los retos, servidos por un solo nginx
                        /reto-01/  /reto-02/  /reto-03/  ...

data/ctf.db             SQLite, persistente (sobrevive a los reinicios)
Chrome --kiosk          perfil temporal, se borra entre jugadores
```

Los retos son estáticos: no tienen estado que un jugador pueda romper, así que no
necesitan un contenedor cada uno. Añadir un reto es crear una carpeta en
`challenges/sitio/`, sin tocar el `docker-compose.yml`. Si algún día un reto necesita
backend propio, se le añade su contenedor solo a él.

**Stack:** Python 3.12 + FastAPI + SQLite. Front en HTML/CSS/JS sin build y sin
framework: cuatro pantallas y tres estados no justifican React, y un paso de
compilación es una pieza más que puede romperse la mañana del evento.

Sin CDN y sin red: las tipografías van dentro del repositorio
(`platform/app/static/fonts/`). VT323 para las cifras grandes, Inconsolata para
el texto corriente. Animaciones en CSS puro, limitadas a `transform`, `opacity`
y `clip-path`; el JS solo lleva el estado.

**Aspecto:** terminal de fósforo verde. Rejilla de caracteres, marcos de un
píxel, líneas de barrido, viñeta y lluvia de código de fondo. Se respeta
`prefers-reduced-motion`. Ver `DESIGN.md`.

**La página nunca se desplaza.** Es un kiosco: cada pantalla cabe entera en
el monitor. Lo que puede desbordar (el índice de retos, el visor, el
marcador) se desplaza dentro de su propio panel. Los tamaños están atados a
la altura del viewport, así que la interfaz encoge en vez de recortarse;
comprobado sin scroll de 1080 a 700 px de alto.

## Puesta en marcha

El día del evento:

```bash
./start-day.sh            # levanta todo y abre las dos pantallas
```

No hay nada que configurar: ni fichero de entorno, ni token, ni secreto.
`start-day.sh` arranca con `-f docker-compose.yml` a propósito, para que la
configuración de desarrollo nunca llegue al stand.

La duración se cambia con `CTF_DURACION` (segundos, 300 por defecto) si
alguna vez hace falta, por ejemplo para probar:

```bash
CTF_DURACION=30 docker compose up --build
```

La plataforma no expone ninguna ruta de administración. Si algún día se añade
una (corregir un tanteo, vaciar el marcador), **entonces** habrá que ponerle
autenticación; hoy no hay nada que proteger.

## Desarrollo

```bash
docker compose up --build   # aplica docker-compose.override.yml solo
```

El `override` monta el código en vivo y arranca uvicorn con `--reload`: se
recargan las rutas, las plantillas, el CSS, el JS y `retos.json` sin
reconstruir la imagen. Los retos se sirven desde disco, así que editar un
HTML en `challenges/sitio/` se ve al recargar la página.

Si se toca `challenges/nginx.conf`:

```bash
docker compose exec retos nginx -s reload
```

## Añadir un reto

1. Crear `challenges/sitio/reto-04/index.html`.
2. Añadir su entrada en `platform/app/retos.json` (código, nombre, dificultad,
   coeficiente y URL). El orden del fichero es el orden en pantalla.

`retos.json` manda: una bandera que se quita del fichero deja de estar activa
al arrancar, sin borrar los envíos que ya la referenciaban. No hay que tocar
el `docker-compose.yml`.

## Entre dos jugadores

```bash
./reset.sh
```

Cierra Chrome, borra el perfil temporal, la carpeta de descargas y el portapapeles,
reinicia los contenedores de retos y vuelve a abrir el kiosco en la pantalla de reglas.
**No toca `data/ctf.db`**: el marcador es acumulativo durante toda la jornada.

## Estructura

```
platform/
  app/main.py         rutas
  app/db.py           esquema SQLite
  app/scoring.py      baremo
  app/retos.json      banderas, dificultad y URL de cada reto
  app/templates/      inicio, jugar, fin, marcador
  app/static/css      el mundo visual entero
  app/static/js       estado: cronómetro, envío, visor, salir
  app/static/fonts    VT323 e Inconsolata, dentro del repositorio
challenges/
  nginx.conf
  sitio/comun/        hoja de estilo y tipografías de los retos
  sitio/reto-01/      un directorio por reto
data/                 ctf.db (ignorado por git)
reset.sh              reinicio entre jugadores
start-day.sh          arranque de la mañana
docker-compose.override.yml   solo desarrollo: recarga en caliente
```

## Pendiente

- Definir los retos (contenido, dificultad, banderas)
- Dirección visual de la interfaz
- Número total de retos
- Premio y criterio de desempate
