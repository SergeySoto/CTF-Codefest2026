# Sistema visual — Codefest CTF

Escrito desde el código construido, no desde la intención. Si el CSS y este
documento se contradicen, manda el CSS y hay que corregir este fichero.

Todo vive en `platform/app/static/css/estilo.css`. Los retos heredan un
subconjunto en `challenges/sitio/comun/estilo.css`.

## La idea

La interfaz **es** una sesión de terminal en un tubo de fósforo verde: una
rejilla de celdas de carácter dibujada con reglas y glifos. Rechaza
explícitamente la cuadrícula de tarjetas redondeadas que sirve cualquier
plataforma de CTF.

## Color

El fósforo P1 es verde amarillento. El `#00ff00` de las películas no aparece
en ninguna parte.

| Token | Valor | Uso |
|---|---|---|
| `--vidrio` | `#030a06` | el cristal apagado, fondo de página |
| `--vidrio-2` | `#061309` | fondo de panel |
| `--p-max` | `#eaffe4` | el trazo quemado: cifras grandes, aciertos |
| `--p-alto` | `#b6ff8f` | titulares, botones, énfasis |
| `--p-med` | `#63e85c` | texto corriente |
| `--p-bajo` | `#52bd58` | rótulos y secundario |
| `--p-linea` | `#1d5228` | marcos y reglas |
| `--p-muerto` | `#0e2a16` | celda apagada (barra gastada, separadores) |

`--p-bajo` está calibrado contra la viñeta: los rótulos caen en las esquinas,
donde la pantalla se oscurece un ~28%, y `#52bd58` sigue por encima de 4.5:1
ahí. Bajarlo rompe la capa entera de rótulos.

`--p-muerto` **nunca lleva texto que haya que leer**. Solo separadores y
celdas apagadas.

No hay segundo tono. La urgencia no se resuelve con un rojo: el fósforo se
sobrecarga e invierte. Un terminal monocromo no tiene otro color y el diseño
no se lo inventa.

## Tipografía

Dos familias, ambas dentro del repositorio (OFL, ver
`platform/app/static/fonts/LEEME.md`). Sin CDN: el día del evento no hay red.

- `--pantalla` — **VT323**. Solo cifras y rótulos de pantalla: el reloj, el
  tanteo, el marcador, la marca, el prompt `>`, la barra de bloques.
  Es una tipografía de pantalla, **no de lectura**.
- `--texto` — **Inconsolata**. Todo el texto corriente. Monoespaciada, así
  que la rejilla de caracteres no se rompe al cambiar de familia.

Usar VT323 para párrafos fue el primer intento y falló en pruebas con el
usuario: no se lee a tamaño de lectura. No revertir.

Base `18px`. Cuerpo `1.1rem`. Reglas `1.15rem`. Rótulos `1rem` con
interletraje `.14em` — más apretado que eso y se emborronan bajo el barrido.

## El halo

El brillo va **por capas**, como el de un haz real: las celdas tenues no
brillan.

- `--halo-max` — capa de pantalla: `.marca`, `.cifras`, `.puntos`, `.total`,
  títulos de panel, retos resueltos.
- `--halo` — texto corriente: `p`, `li`, avisos de acierto.
- `text-shadow: none` — capa de rótulos: `.estado`, `.rotulo`, `.dif`,
  `.pie`, `.visor-fuera`, `.salida button`, marcadores de posición.

Un halo global sobre `body` fue el error inicial: hacía brillar más
precisamente lo más pequeño y tenue, que es lo que peor se leía.

## Composición

- Rejilla de celdas: anchos en `ch`, ritmo vertical único `--paso: .75rem`.
- `border-radius: 0` en todas partes. No hay una sola esquina redondeada.
- Marcos de 1px con el título sentado sobre el trazo (`.panel > .titulo`),
  vocabulario de terminal, no de tarjeta.
- Ni una tarjeta. El índice de retos es salida de `ls`, no una cuadrícula.
- Nada de marcos anidados: el visor no lleva borde propio porque el panel ya
  lo enmarca.

Tres capas fijas por encima del fondo, ninguna intercepta el ratón: la lluvia
de código (`z-index: 0`, `opacity: .1`), el barrido y la viñeta
(`z-index: 90`).

El alfabeto de la lluvia (`main.py`, `ALFABETO`) son glifos que VT323 tiene de
verdad. Katakana caería en otra fuente y rompería la rejilla — y además es lo
que sirve todo el mundo.

## Movimiento

**Solo se animan `transform`, `opacity` y `clip-path`.** Nunca `width`,
`height`, `top` ni `left`: son las únicas propiedades que el navegador anima
sin recalcular la maquetación, y el ordenador del stand tiene que aguantar
ocho horas.

Todas las animaciones usan `steps()`. El movimiento es cuantizado, como la
rejilla; nada de suavizados prestados de otro mundo.

| Momento | Qué hace |
|---|---|
| Entrada | las líneas se imprimen escalonadas (`--t`), todo en 700 ms |
| Acierto | el aviso se teclea con `clip-path` y los puntos suben desde la caja |
| Fallo | la caja se sacude. **No** se invierte la pantalla |
| Últimos 20 s | las cifras del reloj invierten y parpadean a ~1.1 Hz |

Fallar es deliberadamente **más discreto** que acertar. El público son
personas que se asoman a esto por primera vez y el juego tiene que premiar
más fuerte de lo que castiga.

`prefers-reduced-motion` corta toda animación y esconde la lluvia. La
inversión del reloj sobrevive como estado estático: se pierde el parpadeo,
no la señal.

## Accesibilidad

- Todo el texto legible por encima de 4.5:1 sobre `--vidrio`, medido con la
  viñeta puesta.
- `:focus-visible` autorizado en la caja, los botones, las filas de reto y el
  enlace del visor: el recorrido con teclado no sale del mundo.
- Los marcadores de posición no son decorativos: llevan la única instrucción
  en contexto de la pantalla y van en `--p-bajo`, no en `--p-muerto`.

## Lo que no se hace

- Ningún CDN, ninguna fuente remota, ninguna librería de animación.
- Ningún `confirm()` ni diálogo del navegador: en modo kiosco bloquean el
  puesto hasta que alguien los cierre a mano.
- Ninguna esquina redondeada, ninguna sombra proyectada que no sea el halo
  del fósforo.
- Ningún color fuera de la rampa verde.
