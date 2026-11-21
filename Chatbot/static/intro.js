// Bienvenida tras el login: "Iniciando sistemas…" -> "Acceso concedido" -> "Bienvenido"
// y el circulo se encoge hasta el orbe del encabezado. Un clic o una tecla la saltan.
// Solo se activa si el login dejo la marca (la pagina agrega la clase "con-intro").
(() => {
  const raiz = document.documentElement;
  const intro = document.getElementById("intro");
  if (!intro || !raiz.classList.contains("con-intro")) return;

  const orbeGrande = document.getElementById("intro-orbe");
  const orbeCabecera = document.getElementById("orbe-cabecera");
  const estado = document.getElementById("intro-estado");
  const sinMovimiento = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const temporizadores = [];
  let escritura = null;
  let terminada = false;

  function programar(ms, funcion) {
    temporizadores.push(window.setTimeout(funcion, ms));
  }

  function escribir(texto, ritmo) {
    window.clearInterval(escritura);
    if (sinMovimiento) {
      estado.textContent = texto;
      return;
    }
    let letras = 0;
    estado.textContent = "";
    escritura = window.setInterval(() => {
      letras += 1;
      estado.textContent = texto.slice(0, letras);
      if (letras >= texto.length) window.clearInterval(escritura);
    }, ritmo);
  }

  function etapa(nombre) {
    intro.dataset.etapa = nombre;
  }

  // El circulo grande viaja y se encoge hasta quedar encima del orbe pequeno
  function encoger() {
    if (sinMovimiento) return;
    const grande = orbeGrande.getBoundingClientRect();
    const pequeno = orbeCabecera.getBoundingClientRect();
    const escala = pequeno.width / grande.width;
    const dx = pequeno.left + pequeno.width / 2 - (grande.left + grande.width / 2);
    const dy = pequeno.top + pequeno.height / 2 - (grande.top + grande.height / 2);
    orbeGrande.style.animation = "none";
    orbeGrande.style.transform = "translate(" + dx + "px, " + dy + "px) scale(" + escala + ")";
  }

  function terminar() {
    if (terminada) return;
    terminada = true;
    temporizadores.forEach(window.clearTimeout);
    window.clearInterval(escritura);
    document.removeEventListener("pointerdown", terminar);
    document.removeEventListener("keydown", terminar);
    etapa("salida");
    encoger();
    window.setTimeout(() => raiz.classList.add("intro-fin"), sinMovimiento ? 250 : 800);
    window.setTimeout(() => raiz.classList.remove("con-intro", "intro-fin"), sinMovimiento ? 500 : 1100);
  }

  document.addEventListener("pointerdown", terminar);
  document.addEventListener("keydown", terminar);

  etapa("inicio");
  escribir(intro.dataset.iniciando, 35);
  programar(900, () => {
    etapa("acceso");
    escribir(intro.dataset.acceso, 30);
  });
  programar(1600, () => etapa("bienvenida"));
  programar(sinMovimiento ? 2200 : 2800, terminar);
})();
