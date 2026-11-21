"""Las herramientas del asistente: tareas, notas, preferencias y busqueda en internet.

Cada herramienta es una funcion de Python que DEVUELVE UN DICCIONARIO y nunca
lanza una excepcion hacia Gemini: si algo falla devuelve {"error": "mensaje"}.

Este modulo es dueno de datos/tareas.json y datos/notas.json. No llama a la API
de Gemini; las consultas a internet las hace internet.py.
"""

import logging
import threading
from datetime import datetime

import almacen
import configuracion
import internet
import memoria
import textos

registro = logging.getLogger(__name__)

MAXIMO_TAREAS = 100
MAXIMO_NOTAS = 100
MAXIMO_PREFERENCIAS = 20
LARGO_TAREA = 500
LARGO_NOTA = 1000
LARGO_CLAVE = 40
LARGO_VALOR = 200
LARGO_BUSQUEDA = 200

ARCHIVO_TAREAS = "tareas.json"
ARCHIVO_NOTAS = "notas.json"

_candado = threading.Lock()


def _ahora():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _error(mensaje):
    return {"error": mensaje}


def _texto_valido(texto, maximo, mensaje_largo):
    """Devuelve (texto_limpio, None) o (None, diccionario_de_error)."""
    texto = texto.strip()
    if not texto:
        return None, _error(textos.HERRAMIENTA_TEXTO_VACIO)
    if len(texto) > maximo:
        return None, _error(mensaje_largo.format(maximo=maximo))
    return texto, None


# --- Lectura para la web (no son herramientas de Gemini) ---

def todas_las_tareas():
    with _candado:
        return almacen.leer_json(ARCHIVO_TAREAS, {"siguiente_id": 1, "tareas": []})["tareas"]


def todas_las_notas():
    with _candado:
        return almacen.leer_json(ARCHIVO_NOTAS, {"siguiente_id": 1, "notas": []})["notas"]


# --- Herramientas ---

def agregar_tarea(texto):
    texto, error = _texto_valido(texto, LARGO_TAREA, textos.HERRAMIENTA_TEXTO_LARGO)
    if error:
        return error
    with _candado:
        datos = almacen.leer_json(ARCHIVO_TAREAS, {"siguiente_id": 1, "tareas": []})
        if len(datos["tareas"]) >= MAXIMO_TAREAS:
            return _error(textos.HERRAMIENTA_LIMITE_TAREAS.format(maximo=MAXIMO_TAREAS))
        tarea = {"id": datos["siguiente_id"], "texto": texto, "hecha": False, "fecha": _ahora()}
        datos["siguiente_id"] += 1  # los ids nunca se reutilizan
        datos["tareas"].append(tarea)
        almacen.escribir_json(ARCHIVO_TAREAS, datos)
    return {"id": tarea["id"], "texto": tarea["texto"], "hecha": False}


def listar_tareas(solo_pendientes=True):
    tareas = todas_las_tareas()
    if solo_pendientes:
        tareas = [tarea for tarea in tareas if not tarea["hecha"]]
    return {"tareas": tareas}


def completar_tarea(id):
    with _candado:
        datos = almacen.leer_json(ARCHIVO_TAREAS, {"siguiente_id": 1, "tareas": []})
        for tarea in datos["tareas"]:
            if tarea["id"] == id:
                tarea["hecha"] = True
                almacen.escribir_json(ARCHIVO_TAREAS, datos)
                return {"id": id, "hecha": True}
    return _error(textos.HERRAMIENTA_NO_EXISTE_TAREA.format(id=id))


def agregar_nota(texto):
    texto, error = _texto_valido(texto, LARGO_NOTA, textos.HERRAMIENTA_TEXTO_LARGO)
    if error:
        return error
    with _candado:
        datos = almacen.leer_json(ARCHIVO_NOTAS, {"siguiente_id": 1, "notas": []})
        if len(datos["notas"]) >= MAXIMO_NOTAS:
            return _error(textos.HERRAMIENTA_LIMITE_NOTAS.format(maximo=MAXIMO_NOTAS))
        nota = {"id": datos["siguiente_id"], "texto": texto, "fecha": _ahora()}
        datos["siguiente_id"] += 1
        datos["notas"].append(nota)
        almacen.escribir_json(ARCHIVO_NOTAS, datos)
    return {"id": nota["id"], "texto": nota["texto"]}


def listar_notas():
    return {"notas": todas_las_notas()}


def guardar_preferencia(clave, valor):
    clave, error = _texto_valido(clave, LARGO_CLAVE, textos.HERRAMIENTA_CLAVE_LARGA)
    if error:
        return error
    valor, error = _texto_valido(valor, LARGO_VALOR, textos.HERRAMIENTA_VALOR_LARGO)
    if error:
        return error
    try:
        memoria.guardar_preferencia(clave, valor, maximo=MAXIMO_PREFERENCIAS)
    except memoria.LimiteExcedido:
        return _error(textos.HERRAMIENTA_LIMITE_PREFERENCIAS.format(maximo=MAXIMO_PREFERENCIAS))
    return {"clave": clave, "valor": valor}


def _error_de_internet(error):
    return _error(textos.ERRORES_INTERNET.get(error.codigo, textos.HERRAMIENTA_SIN_INTERNET))


def buscar_noticias(tema=""):
    tema = tema.strip()
    if len(tema) > LARGO_BUSQUEDA:
        return _error(textos.HERRAMIENTA_BUSQUEDA_LARGA.format(maximo=LARGO_BUSQUEDA))
    try:
        return {"noticias": internet.noticias(tema)}
    except internet.ErrorInternet as error:
        return _error_de_internet(error)


def buscar_wikipedia(consulta):
    consulta, error = _texto_valido(consulta, LARGO_BUSQUEDA, textos.HERRAMIENTA_BUSQUEDA_LARGA)
    if error:
        return error
    try:
        return {"articulos": internet.wikipedia(consulta)}
    except internet.ErrorInternet as error:
        return _error_de_internet(error)


def buscar_web(consulta):
    if not configuracion.TAVILY_API_KEY:
        return _error(textos.HERRAMIENTA_BUSQUEDA_SIN_CLAVE)
    consulta, error = _texto_valido(consulta, LARGO_BUSQUEDA, textos.HERRAMIENTA_BUSQUEDA_LARGA)
    if error:
        return error
    try:
        return {"resultados": internet.buscar_web(consulta, configuracion.TAVILY_API_KEY)}
    except internet.ErrorInternet as error:
        return _error_de_internet(error)


def consultar_clima(ciudad):
    ciudad, error = _texto_valido(ciudad, LARGO_BUSQUEDA, textos.HERRAMIENTA_BUSQUEDA_LARGA)
    if error:
        return error
    try:
        datos = internet.clima(ciudad)
    except internet.ErrorInternet as error:
        return _error_de_internet(error)
    if datos is None:
        return _error(textos.HERRAMIENTA_CIUDAD_NO_ENCONTRADA)
    return datos


# --- Lo que ve Gemini ---

FUNCIONES = {
    "agregar_tarea": agregar_tarea,
    "listar_tareas": listar_tareas,
    "completar_tarea": completar_tarea,
    "agregar_nota": agregar_nota,
    "listar_notas": listar_notas,
    "guardar_preferencia": guardar_preferencia,
    "buscar_noticias": buscar_noticias,
    "buscar_wikipedia": buscar_wikipedia,
    "buscar_web": buscar_web,
    "consultar_clima": consultar_clima,
}

# Para cada funcion: parametro -> (tipo de JSON Schema, es obligatorio)
PARAMETROS = {
    "agregar_tarea": {"texto": ("string", True)},
    "listar_tareas": {"solo_pendientes": ("boolean", False)},
    "completar_tarea": {"id": ("integer", True)},
    "agregar_nota": {"texto": ("string", True)},
    "listar_notas": {},
    "guardar_preferencia": {"clave": ("string", True), "valor": ("string", True)},
    "buscar_noticias": {"tema": ("string", False)},
    "buscar_wikipedia": {"consulta": ("string", True)},
    "buscar_web": {"consulta": ("string", True)},
    "consultar_clima": {"ciudad": ("string", True)},
}


def _construir_declaraciones():
    """Arma la lista de declaraciones en el formato de la API (type, name, description, parameters)."""
    declaraciones = []
    for nombre, parametros in PARAMETROS.items():
        propiedades = {
            parametro: {
                "type": tipo,
                "description": textos.DESCRIPCIONES_HERRAMIENTAS[f"{nombre}.{parametro}"],
            }
            for parametro, (tipo, _) in parametros.items()
        }
        declaraciones.append({
            "type": "function",
            "name": nombre,
            "description": textos.DESCRIPCIONES_HERRAMIENTAS[nombre],
            "parameters": {
                "type": "object",
                "properties": propiedades,
                "required": [p for p, (_, obligatorio) in parametros.items() if obligatorio],
            },
        })
    return declaraciones


DECLARACIONES = _construir_declaraciones()


def declaraciones_activas():
    """Las declaraciones de funciones que se le ofrecen a Gemini.

    Una sola busqueda general, para no duplicar llamadas. Prioridad:
    Google Search (BUSQUEDA_WEB, lo agrega asistente.py) > buscar_web (Tavily) > buscar_wikipedia.
    """
    if configuracion.BUSQUEDA_WEB:
        sobran = {"buscar_web", "buscar_wikipedia"}
    elif configuracion.TAVILY_API_KEY:
        sobran = {"buscar_wikipedia"}
    else:
        sobran = {"buscar_web"}
    return [d for d in DECLARACIONES if d["name"] not in sobran]


def _validar_tipo(valor, tipo):
    """Devuelve (valor_convertido, es_valido). Gemini a veces manda 3.0 en vez de 3."""
    if tipo == "string":
        return valor, isinstance(valor, str)
    if tipo == "boolean":
        return valor, isinstance(valor, bool)
    if tipo == "integer":
        if isinstance(valor, bool):
            return valor, False
        if isinstance(valor, float) and valor.is_integer():
            return int(valor), True
        return valor, isinstance(valor, int)
    return valor, False


def ejecutar(nombre, argumentos):
    """Ejecuta la herramienta "nombre" con un diccionario de argumentos. Siempre devuelve un diccionario."""
    funcion = FUNCIONES.get(nombre)
    if funcion is None:
        return _error(textos.HERRAMIENTA_DESCONOCIDA)
    if not isinstance(argumentos, dict):
        return _error(textos.HERRAMIENTA_ARGUMENTOS_INVALIDOS.format(detalle="argumentos"))

    validos = {}
    for parametro, (tipo, obligatorio) in PARAMETROS[nombre].items():
        if parametro not in argumentos:
            if obligatorio:
                return _error(textos.HERRAMIENTA_ARGUMENTOS_INVALIDOS.format(detalle=parametro))
            continue
        valor, es_valido = _validar_tipo(argumentos[parametro], tipo)
        if not es_valido:
            return _error(textos.HERRAMIENTA_ARGUMENTOS_INVALIDOS.format(detalle=parametro))
        validos[parametro] = valor

    try:
        return funcion(**validos)
    except Exception:
        registro.exception("Fallo la herramienta %s", nombre)
        return _error(textos.HERRAMIENTA_FALLO)
