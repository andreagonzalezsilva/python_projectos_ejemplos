"""Memoria del asistente: conversaciones (las pestanas del chat) y preferencias del usuario.

Este modulo es dueno de estos archivos en datos/:
  - conversaciones.json  {"siguiente_id": 3, "conversaciones": [
                            {"id": 1, "titulo": "...", "mensajes": [{"rol", "texto", "fecha"}]}]}
                         Cada conversacion guarda sus ultimos 20 mensajes.
  - preferencias.json    {"nombre": "Ana", ...}  Se comparten entre todas las conversaciones.
  - historial.json       Formato anterior (una sola conversacion). Solo se lee, una vez, para migrarlo.

Las tareas y las notas (herramientas.py) tambien son comunes a todas las conversaciones.
Todas las funciones de mensajes reciben "chat_id"; si es None usan la primera conversacion.
No llama a la API de Gemini: se puede probar sin red.
"""

import threading
from datetime import datetime

import almacen
import textos

MAXIMO_MENSAJES = 20
MAXIMO_CONVERSACIONES = 8
LARGO_TITULO = 28

ARCHIVO_CONVERSACIONES = "conversaciones.json"
ARCHIVO_HISTORIAL = "historial.json"
ARCHIVO_PREFERENCIAS = "preferencias.json"

_candado = threading.Lock()


class LimiteExcedido(Exception):
    """Se intento guardar mas preferencias o abrir mas conversaciones de las permitidas."""


class ConversacionNoExiste(Exception):
    """No hay ninguna conversacion con ese id."""


def _ahora():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _titulo_corto(texto):
    linea = " ".join(texto.split())
    if len(linea) <= LARGO_TITULO:
        return linea
    return linea[: LARGO_TITULO - 1].rstrip() + "…"


def _nueva(id_conversacion, mensajes=None):
    mensajes = mensajes or []
    titulo = textos.TITULO_CHAT_NUEVO
    for mensaje in mensajes:
        if mensaje.get("rol") == "usuario":
            titulo = _titulo_corto(mensaje["texto"])
            break
    return {"id": id_conversacion, "titulo": titulo, "mensajes": mensajes}


def _leer():
    """Todos los datos de conversaciones (hay que llamarla con el candado puesto).

    Si todavia no existe conversaciones.json, crea la primera conversacion a partir
    del historial.json anterior (si lo hay), asi no se pierde lo que ya se conversaba.
    """
    datos = almacen.leer_json(ARCHIVO_CONVERSACIONES, None)
    if isinstance(datos, dict) and isinstance(datos.get("conversaciones"), list) and datos["conversaciones"]:
        return datos
    anterior = almacen.leer_json(ARCHIVO_HISTORIAL, {"mensajes": []})
    mensajes = anterior.get("mensajes", []) if isinstance(anterior, dict) else []
    datos = {"siguiente_id": 2, "conversaciones": [_nueva(1, mensajes)]}
    almacen.escribir_json(ARCHIVO_CONVERSACIONES, datos)
    return datos


def _buscar(datos, chat_id):
    if chat_id is None:
        return datos["conversaciones"][0]
    for conversacion in datos["conversaciones"]:
        if conversacion["id"] == chat_id:
            return conversacion
    raise ConversacionNoExiste(chat_id)


# --- Conversaciones (pestanas) ---

def listar_conversaciones():
    """[{"id", "titulo", "cantidad"}] en el orden en que se crearon."""
    with _candado:
        return [
            {"id": c["id"], "titulo": c["titulo"], "cantidad": len(c["mensajes"])}
            for c in _leer()["conversaciones"]
        ]


def id_por_defecto():
    """El id de la primera conversacion (la que se usa si no se indica otra)."""
    with _candado:
        return _leer()["conversaciones"][0]["id"]


def existe_conversacion(chat_id):
    with _candado:
        try:
            _buscar(_leer(), chat_id)
        except ConversacionNoExiste:
            return False
        return True


def crear_conversacion(maximo=MAXIMO_CONVERSACIONES):
    """Abre una conversacion vacia. Si ya hay "maximo", lanza LimiteExcedido."""
    with _candado:
        datos = _leer()
        if len(datos["conversaciones"]) >= maximo:
            raise LimiteExcedido(maximo)
        nueva = _nueva(datos["siguiente_id"])
        datos["siguiente_id"] += 1  # los ids nunca se reutilizan
        datos["conversaciones"].append(nueva)
        almacen.escribir_json(ARCHIVO_CONVERSACIONES, datos)
        return {"id": nueva["id"], "titulo": nueva["titulo"], "cantidad": 0}


def eliminar_conversacion(chat_id):
    """Cierra una conversacion y su historial. Si era la unica, queda una vacia."""
    with _candado:
        datos = _leer()
        conversacion = _buscar(datos, chat_id)
        datos["conversaciones"].remove(conversacion)
        if not datos["conversaciones"]:
            datos["conversaciones"].append(_nueva(datos["siguiente_id"]))
            datos["siguiente_id"] += 1
        almacen.escribir_json(ARCHIVO_CONVERSACIONES, datos)


# --- Mensajes de una conversacion ---

def cargar_historial(chat_id=None):
    """Lista de mensajes guardados: [{"rol": "usuario"|"asistente", "texto", "fecha"}]."""
    with _candado:
        return _buscar(_leer(), chat_id)["mensajes"]


def agregar_mensaje(rol, texto, chat_id=None):
    """Agrega un mensaje y deja solo los ultimos 20. El historial siempre empieza con el usuario.

    El primer mensaje del usuario le pone titulo a la conversacion.
    """
    with _candado:
        datos = _leer()
        conversacion = _buscar(datos, chat_id)
        mensajes = conversacion["mensajes"]
        mensajes.append({"rol": rol, "texto": texto, "fecha": _ahora()})
        mensajes = mensajes[-MAXIMO_MENSAJES:]
        while mensajes and mensajes[0]["rol"] != "usuario":
            mensajes.pop(0)
        conversacion["mensajes"] = mensajes
        if rol == "usuario" and conversacion["titulo"] == textos.TITULO_CHAT_NUEVO:
            conversacion["titulo"] = _titulo_corto(texto)
        almacen.escribir_json(ARCHIVO_CONVERSACIONES, datos)


def borrar_historial(chat_id=None):
    """Vacia una conversacion. No toca las preferencias (ni tareas ni notas)."""
    with _candado:
        datos = _leer()
        conversacion = _buscar(datos, chat_id)
        conversacion["mensajes"] = []
        conversacion["titulo"] = textos.TITULO_CHAT_NUEVO
        almacen.escribir_json(ARCHIVO_CONVERSACIONES, datos)


# --- Preferencias (comunes a todas las conversaciones) ---

def cargar_preferencias():
    """Diccionario de preferencias, por ejemplo {"nombre": "Ana"}."""
    with _candado:
        return almacen.leer_json(ARCHIVO_PREFERENCIAS, {})


def guardar_preferencia(clave, valor, maximo=None):
    """Guarda o reemplaza una preferencia. Si es nueva y ya hay "maximo", lanza LimiteExcedido."""
    with _candado:
        preferencias = almacen.leer_json(ARCHIVO_PREFERENCIAS, {})
        if maximo is not None and clave not in preferencias and len(preferencias) >= maximo:
            raise LimiteExcedido(clave)
        preferencias[clave] = valor
        almacen.escribir_json(ARCHIVO_PREFERENCIAS, preferencias)
        return preferencias
