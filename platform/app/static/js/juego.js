// Estado de la partida. Las animaciones viven en el CSS; aquí solo se
// cambian textos y clases.
(() => {
  const crono = document.getElementById("crono");
  const reloj = document.getElementById("reloj");
  const barra = document.getElementById("barra");
  const total = document.getElementById("total");
  const formulario = document.getElementById("formulario");
  const caja = document.getElementById("bandera");
  const aviso = document.getElementById("aviso");

  const CELDAS = 24;
  let restantes = Number(crono.dataset.restantes);
  let duracion = Number(crono.dataset.duracion) || restantes || 1;

  const dos = (n) => String(n).padStart(2, "0");

  function pintar() {
    reloj.textContent = `${dos(Math.floor(restantes / 60))}:${dos(restantes % 60)}`;
    const llenas = Math.round((restantes / duracion) * CELDAS);
    barra.replaceChildren(
      Object.assign(document.createElement("span"), { textContent: "█".repeat(llenas) }),
      Object.assign(document.createElement("span"), {
        className: "vacio", textContent: "░".repeat(CELDAS - llenas),
      }),
    );
    crono.classList.toggle("critico", restantes <= 20);
  }

  function decir(texto, clase = "") {
    aviso.className = "aviso";
    void aviso.offsetWidth;          // reinicia la animación y el aria-live
    aviso.textContent = texto;
    aviso.className = `aviso ${clase}`;
  }

  // El cronómetro corre en local pero se resincroniza: el reloj del
  // navegador no decide cuándo se acaba el tiempo, lo decide el servidor.
  async function sincronizar() {
    try {
      const r = await fetch("/api/estado");
      if (!r.ok) return;
      const d = await r.json();
      restantes = d.restantes;
      duracion = d.duracion;
      total.textContent = d.puntos;
      pintar();
    } catch { /* sin respuesta: seguimos con el contador local */ }
  }

  setInterval(() => {
    restantes = Math.max(0, restantes - 1);
    pintar();
    if (restantes === 0) location.assign("/fin");
  }, 1000);
  setInterval(sincronizar, 10000);
  pintar();
  sincronizar();

  // ------------------------------------------------------------- envíos

  function ascender(puntos) {
    const g = document.createElement("div");
    g.className = "ganancia";
    g.textContent = `+${puntos}`;
    const r = caja.getBoundingClientRect();
    g.style.left = `${r.left + 8}px`;
    g.style.top = `${r.top}px`;
    document.body.appendChild(g);
    g.addEventListener("animationend", () => g.remove());
  }

  function sacudir() {
    formulario.classList.remove("error");
    void formulario.offsetWidth;         // reinicia la animación
    formulario.classList.add("error");
  }

  formulario.addEventListener("submit", async (e) => {
    e.preventDefault();
    const valor = caja.value.trim();
    if (!valor) return;

    const cuerpo = new FormData();
    cuerpo.append("bandera", valor);

    let d;
    try {
      d = await (await fetch("/enviar", { method: "POST", body: cuerpo })).json();
    } catch {
      decir("Sin conexión con el servidor. Avisa al organizador.", "ko");
      return;
    }

    switch (d.estado) {
      case "correcta":
        caja.value = "";
        total.textContent = d.total;
        ascender(d.puntos);
        marcarHecha(d.bandera_id);
        retirarSugerencia(valor);
        decir(`CORRECTA · ${d.reto} · +${d.puntos} puntos`, "ok");
        break;
      case "repetida":
        decir(`Esa ya la tienes (${d.reto}). Busca otra.`, "");
        break;
      case "demasiado_rapido":
        decir("Espera un segundo antes de volver a probar.", "");
        break;
      case "tiempo_agotado":
        location.assign("/fin");
        break;
      case "sin_sesion":
        location.assign("/");
        break;
      default:
        sacudir();
        decir("Esa no es. Sigue buscando.", "ko");
    }
    caja.focus();
  });

  function marcarHecha(id) {
    const fila = document.getElementById(`reto-${id}`);
    if (!fila) return;
    fila.classList.add("hecha");
    fila.querySelector(".marca-ok").textContent = "[✓]";
  }

  // Una vez acertada la bandera que sugiere el navegador, la sugerencia
  // estorba: taparía el aviso cada vez que el jugador escriba "flag{".
  function retirarSugerencia(valor) {
    const lista = caja.list;
    if (!lista) return;
    const v = valor.trim().toLowerCase();
    if ([...lista.options].some((o) => o.value.trim().toLowerCase() === v)) {
      caja.removeAttribute("list");
    }
  }

  // -------------------------------------------------------------- visor
  // El reto se abre dentro de la pantalla: el reloj y la caja no se pierden
  // de vista en ningún momento.

  const visor = document.getElementById("visor");
  const visorVacio = document.getElementById("visor-vacio");
  const visorTitulo = document.getElementById("visor-titulo");

  document.querySelectorAll(".reto").forEach((fila) => {
    fila.addEventListener("click", (e) => {
      const url = fila.dataset.visor;
      if (!url) return;
      e.preventDefault();

      visor.src = url;
      visor.hidden = false;
      visorVacio.hidden = true;
      visorTitulo.textContent = `[ ${fila.querySelector(".nombre").textContent} ]`;

      document.querySelectorAll(".reto.mirando").forEach((o) => o.classList.remove("mirando"));
      fila.classList.add("mirando");
    });
  });

  // -------------------------------------------------------------- salir
  // Confirmación en la propia página: un confirm() del navegador bloquea
  // el kiosco si nadie lo cierra.

  const pedirSalir = document.getElementById("pedir-salir");
  const confirmar = document.getElementById("confirmar");
  const seguir = document.getElementById("seguir");

  pedirSalir.addEventListener("click", () => {
    pedirSalir.hidden = true;
    confirmar.hidden = false;
  });
  seguir.addEventListener("click", () => {
    confirmar.hidden = true;
    pedirSalir.hidden = false;
    caja.focus();
  });
})();
