"""La aplicacion web con Flask.

Flask recibe peticiones HTTP (el navegador pide una pagina o envia datos) y
responde con HTML o con JSON. Cada funcion con @app.route(...) atiende una ruta.

Rutas:
  /              pagina del chat
  /login         formulario de contrasena
  /salir         cierra la sesion
  /chat          recibe un mensaje y devuelve la respuesta (JSON)
  /estado        devuelve tareas, notas, preferencias, conversaciones e historial (JSON)
  /borrar        borra el historial de una conversacion
  /chats/nuevo   abre una conversacion nueva (una pestana mas)
  /chats/cerrar  cierra una conversacion y borra su historial

Cada conversacion (pestana) tiene su propio historial; las tareas, las notas
y las preferencias son comunes a todas. Las rutas reciben el id con "chat".
"""

import hmac
import logging
import secrets
import threading
import time
from functools import wraps

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

import asistente
import configuracion
import gemini
import herramientas
import memoria
import textos

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
registro = logging.getLogger(__name__)

MAXIMO_CARACTERES = 1000

# PythonAnywhere importa esta variable "app" (ver el archivo WSGI en el README)
app = Flask(__name__)
app.secret_key = configuracion.SECRET_KEY or secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_SECURE=True,      # solo por HTTPS (en local se desactiva al final del archivo)
    SESSION_COOKIE_HTTPONLY=True,    # JavaScript no puede leer la cookie
    SESSION_COOKIE_SAMESITE="Lax",   # no se envia en peticiones POST de otros sitios
    MAX_CONTENT_LENGTH=32 * 1024,    # el mensaje mas largo ocupa muy poco
)

# Un solo mensaje a la vez: evita mezclar el historial si llegan dos peticiones juntas
_candado_chat = threading.Lock()


def _decorador_de_sesion(funcion, al_fallar):
    @wraps(funcion)
    def envoltura(*argumentos, **opciones):
        if not session.get("autenticado"):
            return al_fallar()
        return funcion(*argumentos, **opciones)

    return envoltura


def requiere_sesion(funcion):
    """Para paginas: sin sesion, redirige a /login."""
    return _decorador_de_sesion(funcion, lambda: redirect(url_for("login")))


def requiere_sesion_json(funcion):
    """Para rutas JSON: sin sesion, responde 401 (y no entrega ningun dato)."""
    return _decorador_de_sesion(
        funcion, lambda: (jsonify({"error": textos.ERROR_NO_AUTORIZADO}), 401))


def estado_actual():
    """Los datos que pinta el panel lateral y las pestanas."""
    return {
        "tareas": herramientas.todas_las_tareas(),
        "notas": herramientas.todas_las_notas(),
        "preferencias": memoria.cargar_preferencias(),
        "conversaciones": memoria.listar_conversaciones(),
    }


def _id_valido(valor):
    """Un id de conversacion bien formado (entero, no booleano) o None."""
    return valor if isinstance(valor, int) and not isinstance(valor, bool) else None


def _cuerpo_json():
    cuerpo = request.get_json(silent=True)
    return cuerpo if isinstance(cuerpo, dict) else {}


def _conversacion_pedida(cuerpo):
    """El id de la conversacion que pide la peticion, o None si no existe.

    Si la peticion no manda "chat" se usa la primera conversacion.
    """
    pedido = cuerpo.get("chat")
    if pedido is None:
        return memoria.id_por_defecto()
    pedido = _id_valido(pedido)
    if pedido is not None and memoria.existe_conversacion(pedido):
        return pedido
    return None


def _no_existe():
    cuerpo = {"error": textos.ERROR_CHAT_NO_EXISTE, "conversaciones": memoria.listar_conversaciones()}
    return jsonify(cuerpo), 404


def respuesta_de_error(mensaje, codigo_http):
    cuerpo = {"error": mensaje}
    cuerpo.update(estado_actual())  # una herramienta pudo ejecutarse antes del fallo
    return jsonify(cuerpo), codigo_http


@app.after_request
def agregar_cabeceras(respuesta):
    respuesta.headers["X-Content-Type-Options"] = "nosniff"
    respuesta.headers["X-Frame-Options"] = "DENY"
    respuesta.headers["Referrer-Policy"] = "same-origin"
    if respuesta.mimetype == "application/json":
        respuesta.headers["Cache-Control"] = "no-store"
    return respuesta


@app.get("/")
@requiere_sesion
def inicio():
    return render_template(
        "chat.html",
        nombre_bot=configuracion.BOT_NAME,
        bienvenida=textos.BIENVENIDA.format(nombre_bot=configuracion.BOT_NAME),
    )


@app.get("/estado")
@requiere_sesion_json
def estado():
    # Una conversacion que ya no existe (por ejemplo, guardada en el navegador) cae en la primera
    pedido = request.args.get("chat", type=int)
    chat_id = pedido if pedido is not None and memoria.existe_conversacion(pedido) else memoria.id_por_defecto()
    datos = estado_actual()
    datos["chat"] = chat_id
    datos["mensajes"] = memoria.cargar_historial(chat_id)
    return jsonify(datos)


@app.post("/chat")
@requiere_sesion_json
def chat():
    datos = request.get_json(silent=True)
    mensaje = datos.get("mensaje") if isinstance(datos, dict) else None
    if not isinstance(mensaje, str) or not mensaje.strip():
        return jsonify({"error": textos.ERROR_MENSAJE_VACIO}), 400
    mensaje = mensaje.strip()
    if len(mensaje) > MAXIMO_CARACTERES:
        return jsonify({"error": textos.ERROR_MENSAJE_LARGO.format(maximo=MAXIMO_CARACTERES)}), 400
    chat_id = _conversacion_pedida(datos)
    if chat_id is None:
        return _no_existe()

    try:
        with _candado_chat:
            respuesta = asistente.responder(mensaje, chat_id)
    except gemini.ErrorGemini as error:
        return respuesta_de_error(error.mensaje, 429 if error.codigo == "limite" else 502)
    except asistente.ErrorAsistente as error:
        return respuesta_de_error(error.mensaje, 502)
    except memoria.ConversacionNoExiste:
        return _no_existe()  # la cerraron mientras se esperaba la respuesta
    except Exception:
        registro.exception("Error inesperado en /chat")
        return respuesta_de_error(textos.ERROR_INTERNO, 500)

    cuerpo = {"respuesta": respuesta, "chat": chat_id}
    cuerpo.update(estado_actual())
    return jsonify(cuerpo)


@app.post("/borrar")
@requiere_sesion_json
def borrar():
    chat_id = _conversacion_pedida(_cuerpo_json())
    if chat_id is None:
        return _no_existe()
    memoria.borrar_historial(chat_id)
    return jsonify({"ok": True, "conversaciones": memoria.listar_conversaciones()})


@app.post("/chats/nuevo")
@requiere_sesion_json
def chat_nuevo():
    try:
        nueva = memoria.crear_conversacion()
    except memoria.LimiteExcedido:
        cuerpo = {
            "error": textos.ERROR_LIMITE_CHATS.format(maximo=memoria.MAXIMO_CONVERSACIONES),
            "conversaciones": memoria.listar_conversaciones(),
        }
        return jsonify(cuerpo), 409
    return jsonify({"chat": nueva["id"], "conversaciones": memoria.listar_conversaciones()})


@app.post("/chats/cerrar")
@requiere_sesion_json
def chat_cerrar():
    # Aqui el id es obligatorio: sin el, no se cerraria "la primera" por accidente
    chat_id = _id_valido(_cuerpo_json().get("chat"))
    if chat_id is None:
        return _no_existe()
    try:
        memoria.eliminar_conversacion(chat_id)
    except memoria.ConversacionNoExiste:
        return _no_existe()
    return jsonify({"ok": True, "conversaciones": memoria.listar_conversaciones()})


@app.route("/login", methods=["GET", "POST"])
def login():
    faltan = configuracion.faltantes()
    contexto = {"nombre_bot": configuracion.BOT_NAME, "aviso": None, "ayuda": None, "error": None}

    if faltan:
        # La web no se cae: avisa que falta configurar y no deja entrar
        contexto["aviso"] = textos.AVISO_FALTA_CONFIGURAR.format(lista=", ".join(faltan))
        contexto["ayuda"] = textos.AVISO_FALTA_CONFIGURAR_AYUDA
        return render_template("login.html", **contexto)

    if request.method == "POST":
        intento = request.form.get("contrasena", "")
        # compare_digest tarda lo mismo acierte o no (evita ataques por tiempo)
        if hmac.compare_digest(intento.encode("utf-8"), configuracion.APP_PASSWORD.encode("utf-8")):
            session.clear()
            session["autenticado"] = True
            return redirect(url_for("inicio"))
        time.sleep(1)  # frena los intentos repetidos
        contexto["error"] = textos.ERROR_CONTRASENA
        return render_template("login.html", **contexto), 401

    if session.get("autenticado"):
        return redirect(url_for("inicio"))
    return render_template("login.html", **contexto)


@app.post("/salir")
def salir():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    # En local se usa http://127.0.0.1, sin HTTPS: la cookie no puede ser "Secure"
    app.config["SESSION_COOKIE_SECURE"] = False
    app.config["TEMPLATES_AUTO_RELOAD"] = True  # en local, un cambio en templates/ se ve sin reiniciar
    app.run(host="127.0.0.1", port=5000, debug=False)
