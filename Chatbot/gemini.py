"""Llamada REST a la Interactions API de Gemini, con requests.

Este archivo SOLO sabe hablar con la API: envia "pasos" y devuelve "pasos".
No sabe nada de tareas ni de memoria. Si Google cambia el formato, solo se
cambia este archivo.

Un "paso" (step) es un diccionario con un "type":
  - user_input     lo que escribe el usuario
  - model_output   lo que responde el modelo (texto)
  - function_call  el modelo pide ejecutar una funcion de Python
  - function_result el resultado de esa funcion, que le devolvemos al modelo
  - thought        pensamiento interno del modelo (se reenvia intacto)
"""

import logging

import requests

import configuracion
import textos

URL_INTERACCIONES = "https://generativelanguage.googleapis.com/v1beta/interactions"
REVISION_API = "2026-05-20"
TIEMPO_MAXIMO = 30  # segundos

registro = logging.getLogger(__name__)


class ErrorGemini(Exception):
    """Error al hablar con Gemini. "codigo" indica que paso (ver textos.ERRORES_GEMINI)."""

    def __init__(self, codigo, estado_http=None):
        self.codigo = codigo
        self.estado_http = estado_http
        self.mensaje = textos.ERRORES_GEMINI[codigo]
        super().__init__(self.mensaje)


def paso_usuario(texto):
    return {"type": "user_input", "content": [{"type": "text", "text": texto}]}


def paso_modelo(texto):
    return {"type": "model_output", "content": [{"type": "text", "text": texto}]}


def paso_resultado(nombre, id_llamada, texto_json):
    return {
        "type": "function_result",
        "name": nombre,
        "call_id": id_llamada,
        "result": [{"type": "text", "text": texto_json}],
    }


def extraer_llamadas(pasos):
    """Pasos function_call de una lista de pasos."""
    return [paso for paso in pasos if paso.get("type") == "function_call"]


def extraer_texto(pasos):
    """Texto de los pasos model_output posteriores a la ultima entrada del usuario."""
    inicio = 0
    for posicion, paso in enumerate(pasos):
        if paso.get("type") == "user_input":
            inicio = posicion + 1
    trozos = []
    for paso in pasos[inicio:]:
        if paso.get("type") != "model_output":
            continue
        for bloque in paso.get("content") or []:
            if bloque.get("type") == "text" and (bloque.get("text") or "").strip():
                trozos.append(bloque["text"].strip())
    return "\n\n".join(trozos)


def _mensaje_corto(respuesta):
    """Mensaje breve del error de Google, para el registro (sin la clave).

    Ojo: Google a veces envuelve el error en una lista: [{"error": {...}}].
    """
    try:
        cuerpo = respuesta.json()
        if isinstance(cuerpo, list):
            cuerpo = cuerpo[0]
        error = cuerpo["error"]
        texto = str(error.get("message", ""))
        for detalle in error.get("details", []):
            if detalle.get("reason"):
                texto += " [" + str(detalle["reason"]) + "]"
    except Exception:
        texto = ""
    clave = configuracion.GEMINI_API_KEY
    if clave:
        texto = texto.replace(clave, "***")
    return texto[:200]


def _codigo_de_error(estado, mensaje):
    if estado == 429:
        return "limite"
    if estado in (401, 403):
        return "clave"
    if estado == 400 and "api key" in mensaje.lower().replace("_", " "):
        return "clave"
    if estado == 404:
        return "modelo"
    if estado >= 500:
        return "servidor"
    return "formato"


def llamar_api(pasos, instruccion_sistema="", herramientas=None):
    """Envia los pasos a Gemini y devuelve la lista de pasos de la respuesta."""
    cabeceras = {
        "x-goog-api-key": configuracion.GEMINI_API_KEY,
        "Content-Type": "application/json",
        "Api-Revision": REVISION_API,
    }
    cuerpo = {
        "model": configuracion.GEMINI_MODEL,
        "store": False,  # sin estado en el servidor: la memoria la guardamos nosotros
        "input": pasos,
    }
    if instruccion_sistema:
        cuerpo["system_instruction"] = instruccion_sistema
    if herramientas:
        cuerpo["tools"] = herramientas

    try:
        respuesta = requests.post(
            URL_INTERACCIONES, headers=cabeceras, json=cuerpo, timeout=TIEMPO_MAXIMO)
    except requests.RequestException as error:
        # Incluye Timeout, ConnectionError y ProxyError (sitio no permitido en PythonAnywhere)
        registro.warning("No hubo conexion con Gemini: %s", type(error).__name__)
        raise ErrorGemini("red") from error

    if respuesta.status_code != 200:
        mensaje = _mensaje_corto(respuesta)
        registro.warning("Gemini respondio HTTP %s: %s", respuesta.status_code, mensaje)
        raise ErrorGemini(_codigo_de_error(respuesta.status_code, mensaje), respuesta.status_code)

    try:
        datos = respuesta.json()
        pasos_respuesta = datos["steps"]
        if not isinstance(pasos_respuesta, list) or datos.get("status") == "failed":
            raise ValueError("respuesta inesperada")
    except (ValueError, KeyError, TypeError) as error:
        registro.warning("Respuesta de Gemini con formato inesperado")
        raise ErrorGemini("formato") from error
    return pasos_respuesta
