// Chat del asistente. Sin librerias. El texto siempre se inserta con textContent
// (nunca innerHTML), asi ni el modelo ni las notas pueden inyectar HTML.
const zonaMensajes = document.getElementById("mensajes");
const formulario = document.getElementById("formulario");
const campo = document.getElementById("campo");
const botonEnviar = document.getElementById("boton-enviar");
const zonaPestanas = document.getElementById("pestanas");
const botonNuevo = document.getElementById("boton-nuevo");
const zonaChat = document.getElementById("chat");
const botonColapsar = document.getElementById("boton-colapsar");

// Conversaciones (pestanas): cada una tiene su historial; tareas, notas y preferencias son comunes
let chatActivo = null;
let conversaciones = [];
let ocupado = false;
const CLAVE_CHAT = "chatActivo";
const CLAVE_COLAPSADO = "listaColapsada";

function crear(etiqueta, clase, texto) {
  const elemento = document.createElement(etiqueta);
  if (clase) elemento.className = clase;
  if (texto !== undefined) elemento.textContent = texto;
  return elemento;
}

function agregarBurbuja(clase, texto) {
  const burbuja = crear("div", "burbuja " + clase, texto);
  zonaMensajes.appendChild(burbuja);
  zonaMensajes.scrollTop = zonaMensajes.scrollHeight;
  return burbuja;
}

// Llena un contenedor con elementos, o con el texto "vacio" si no hay datos
function llenar(id, elementos) {
  const contenedor = document.getElementById(id);
  contenedor.replaceChildren(...elementos);
  if (elementos.length === 0) contenedor.appendChild(crear("p", "vacio", contenedor.dataset.vacio));
}

function pintarPanel(datos) {
  if (datos.tareas) {
    llenar("lista-tareas", datos.tareas.map((tarea) => {
      const casilla = crear("input");
      casilla.type = "checkbox";
      casilla.checked = tarea.hecha;
      casilla.disabled = true;
      casilla.setAttribute("aria-label", tarea.hecha ? "hecha" : "pendiente");
      const fila = crear("li", tarea.hecha ? "hecha" : "");
      fila.append(casilla, crear("span", "", tarea.texto));
      return fila;
    }));
  }
  if (datos.notas) llenar("lista-notas", datos.notas.map((nota) => crear("div", "nota", nota.texto)));
  if (datos.preferencias) {
    const filas = Object.entries(datos.preferencias).map(([clave, valor]) => clave + ": " + valor);
    const parrafo = document.getElementById("preferencias");
    parrafo.textContent = filas.length ? filas.join(", ") : parrafo.dataset.vacio;
  }
}

async function pedir(url, cuerpo) {
  const opciones = cuerpo === undefined ? {} : {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cuerpo),
  };
  const respuesta = await fetch(url, opciones);
  if (respuesta.status === 401) window.location.href = "/login";
  return { ok: respuesta.ok, estado: respuesta.status, datos: await respuesta.json() };
}

// --- Pestanas ---

function bloquear(si) {
  ocupado = si;
  campo.disabled = botonEnviar.disabled = botonNuevo.disabled = si;
  zonaPestanas.querySelectorAll("button").forEach((boton) => { boton.disabled = si; });
}

function pintarPestanas() {
  zonaPestanas.replaceChildren(...conversaciones.map((conversacion) => {
    const activa = conversacion.id === chatActivo;
    const pestana = crear("div", "pestana" + (activa ? " activa" : ""));
    const titulo = crear("button", "titulo-pestana", conversacion.titulo);
    titulo.type = "button";
    titulo.setAttribute("role", "tab");
    titulo.setAttribute("aria-selected", activa ? "true" : "false");
    titulo.title = conversacion.titulo;
    titulo.addEventListener("click", () => { if (!activa) cambiarDeChat(conversacion.id); });
    const cerrar = crear("button", "cerrar-pestana", "×");
    cerrar.type = "button";
    cerrar.setAttribute("aria-label", zonaPestanas.dataset.cerrar + ": " + conversacion.titulo);
    cerrar.addEventListener("click", () => cerrarChat(conversacion));
    pestana.append(titulo, cerrar);
    return pestana;
  }));
  zonaPestanas.querySelectorAll("button").forEach((boton) => { boton.disabled = ocupado; });
}

// Muestra u oculta la lista vertical de conversaciones (queda una franja angosta)
function aplicarColapso(colapsado) {
  zonaChat.classList.toggle("colapsado", colapsado);
  botonColapsar.textContent = colapsado ? "»" : "«";
  botonColapsar.setAttribute("aria-expanded", colapsado ? "false" : "true");
  const texto = colapsado ? botonColapsar.dataset.mostrar : botonColapsar.dataset.ocultar;
  botonColapsar.title = texto;
  botonColapsar.setAttribute("aria-label", texto);
  botonNuevo.textContent = colapsado ? botonNuevo.dataset.corto : botonNuevo.dataset.largo;
}

botonColapsar.addEventListener("click", () => {
  const colapsado = !zonaChat.classList.contains("colapsado");
  aplicarColapso(colapsado);
  localStorage.setItem(CLAVE_COLAPSADO, colapsado ? "1" : "0");
});

function guardarConversaciones(datos) {
  if (datos.conversaciones) conversaciones = datos.conversaciones;
}

function limpiarMensajes() {
  zonaMensajes.querySelectorAll(".burbuja:not(#bienvenida)").forEach((burbuja) => burbuja.remove());
}

// Carga una conversacion (o la primera si el id ya no existe) y la muestra
async function cargarChat(id) {
  const url = id === null ? "/estado" : "/estado?chat=" + encodeURIComponent(id);
  const { datos } = await pedir(url);
  chatActivo = datos.chat;
  localStorage.setItem(CLAVE_CHAT, String(chatActivo));
  guardarConversaciones(datos);
  limpiarMensajes();
  datos.mensajes.forEach((m) => agregarBurbuja(m.rol === "usuario" ? "usuario" : "bot", m.texto));
  pintarPanel(datos);
  pintarPestanas();
  campo.focus();
}

async function cambiarDeChat(id) {
  if (ocupado) return;
  bloquear(true);
  try {
    await cargarChat(id);
  } catch (error) {
    agregarBurbuja("error", zonaMensajes.dataset.errorRed);
  }
  bloquear(false);
}

async function nuevoChat() {
  if (ocupado) return;
  bloquear(true);
  try {
    const { ok, datos } = await pedir("/chats/nuevo", {});
    guardarConversaciones(datos);
    if (ok) await cargarChat(datos.chat);
    else {
      pintarPestanas();
      agregarBurbuja("error", datos.error);
    }
  } catch (error) {
    agregarBurbuja("error", zonaMensajes.dataset.errorRed);
  }
  bloquear(false);
}

async function cerrarChat(conversacion) {
  if (ocupado) return;
  if (conversacion.cantidad > 0 && !window.confirm(zonaPestanas.dataset.confirmar)) return;
  bloquear(true);
  try {
    const indice = conversaciones.findIndex((c) => c.id === conversacion.id);
    const { datos } = await pedir("/chats/cerrar", { chat: conversacion.id });
    guardarConversaciones(datos);
    if (conversacion.id === chatActivo) {
      // Pasa a la pestana de la izquierda (o a la primera)
      const vecina = datos.conversaciones[Math.max(0, indice - 1)];
      await cargarChat(vecina ? vecina.id : null);
    } else {
      pintarPestanas();
    }
  } catch (error) {
    agregarBurbuja("error", zonaMensajes.dataset.errorRed);
  }
  bloquear(false);
}

// --- Mensajes ---

async function enviar(texto) {
  agregarBurbuja("usuario", texto);
  const escribiendo = agregarBurbuja("bot escribiendo", zonaMensajes.dataset.escribiendo);
  bloquear(true);
  try {
    const { ok, estado, datos } = await pedir("/chat", { mensaje: texto, chat: chatActivo });
    if (estado === 404) {
      // La conversacion ya no existe: se vuelve a una que si existe
      guardarConversaciones(datos);
      await cargarChat(null);
      agregarBurbuja("error", datos.error);
    } else {
      agregarBurbuja(ok ? "bot" : "error", ok ? datos.respuesta : datos.error);
      guardarConversaciones(datos);
      pintarPanel(datos);
      pintarPestanas();
    }
  } catch (error) {
    agregarBurbuja("error", zonaMensajes.dataset.errorRed);
  }
  escribiendo.remove();
  bloquear(false);
  campo.focus();
}

formulario.addEventListener("submit", (evento) => {
  evento.preventDefault();
  const texto = campo.value.trim();
  if (!texto) return;
  campo.value = "";
  enviar(texto);
});

// Enter envia; Shift+Enter hace salto de linea
campo.addEventListener("keydown", (evento) => {
  if (evento.key === "Enter" && !evento.shiftKey) {
    evento.preventDefault();
    formulario.requestSubmit();
  }
});

botonNuevo.addEventListener("click", nuevoChat);

// Borra solo la conversacion que se esta viendo
document.getElementById("boton-borrar").addEventListener("click", async () => {
  if (ocupado) return;
  const { datos } = await pedir("/borrar", { chat: chatActivo });
  guardarConversaciones(datos);
  limpiarMensajes();
  pintarPestanas();
});

// Al cargar la pagina: recordar si la lista estaba oculta (en el telefono empieza oculta),
// y pintar la ultima conversacion que se miro, el panel y las pestanas
(async () => {
  const preferencia = localStorage.getItem(CLAVE_COLAPSADO);
  aplicarColapso(preferencia === null ? window.matchMedia("(max-width: 800px)").matches : preferencia === "1");
  const guardado = Number.parseInt(localStorage.getItem(CLAVE_CHAT), 10);
  await cargarChat(Number.isNaN(guardado) ? null : guardado);
})();
