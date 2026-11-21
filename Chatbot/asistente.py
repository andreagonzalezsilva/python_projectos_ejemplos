"""Une todo: arma el prompt, llama a Gemini y guarda la memoria.

responder(mensaje) -> str  la usan por igual app.py (web) y consola.py (terminal).
"""

import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import configuracion
import gemini
import herramientas
import memoria
import textos

registro = logging.getLogger(__name__)

MAXIMO_VUELTAS = 5
ERRORES_DE_ZONA = (ZoneInfoNotFoundError, ValueError, OSError)

# Herramienta integrada de Gemini: la busqueda la hace Google, no nuestro servidor.
# Google no la ofrece en el plan gratuito (da 429), por eso solo se activa con BUSQUEDA_WEB=1.
BUSQUEDA_WEB = {"type": "google_search"}


def herramientas_activas():
    declaraciones = list(herramientas.declaraciones_activas())
    if configuracion.BUSQUEDA_WEB:
        declaraciones.append(BUSQUEDA_WEB)
    return declaraciones


class ErrorAsistente(Exception):
    """Error propio del asistente (no de Gemini). "mensaje" es amigable para el usuario."""

    def __init__(self, mensaje):
        self.mensaje = mensaje
        super().__init__(mensaje)


def cargar_personalidad():
    """Lee personalidad.txt y pone el nombre del bot."""
    with open(configuracion.ruta_archivo("personalidad.txt"), "r", encoding="utf-8") as archivo:
        texto = archivo.read().strip()
    return texto.replace("{nombre_bot}", configuracion.BOT_NAME)


def linea_de_fecha(ahora=None):
    """Ejemplo: Fecha y hora actuales: jueves 19 de noviembre de 2026, 15:30 (America/Guayaquil).

    Windows no trae base de zonas horarias. Si no se encuentra la zona,
    se usa la hora del sistema y se avisa en el texto.
    """
    zona = configuracion.ZONA_HORARIA
    try:
        momento = (ahora or datetime.now().astimezone()).astimezone(ZoneInfo(zona))
        etiqueta = zona
    except ERRORES_DE_ZONA:
        registro.warning("No se encontro la zona horaria %s; se usa la hora del sistema", zona)
        momento = ahora or datetime.now().astimezone()
        etiqueta = textos.ETIQUETA_HORA_DEL_SISTEMA
    return textos.LINEA_FECHA.format(
        dia=textos.DIAS_SEMANA[momento.weekday()], numero=momento.day,
        mes=textos.MESES[momento.month - 1], anio=momento.year,
        hora=momento.hour, minuto=momento.minute, zona=etiqueta)


def lineas_de_preferencias():
    preferencias = memoria.cargar_preferencias()
    if not preferencias:
        return ""
    lineas = [textos.ENCABEZADO_PREFERENCIAS]
    lineas += [f"- {clave}: {valor}" for clave, valor in preferencias.items()]
    return "\n".join(lineas)


def armar_instruccion(ahora=None):
    """Prompt de sistema: personalidad + fecha y hora + preferencias."""
    partes = [cargar_personalidad(), linea_de_fecha(ahora), lineas_de_preferencias()]
    # Una sola busqueda general (misma prioridad que herramientas.declaraciones_activas)
    if configuracion.BUSQUEDA_WEB:
        partes.insert(1, textos.INSTRUCCION_BUSQUEDA_WEB)
    elif configuracion.TAVILY_API_KEY:
        partes.insert(1, textos.INSTRUCCION_BUSQUEDA_TAVILY)
    else:
        partes.insert(1, textos.INSTRUCCION_BUSQUEDA_WIKIPEDIA)
    return "\n\n".join(parte for parte in partes if parte)


def historial_a_pasos(chat_id=None):
    """Convierte el historial guardado de una conversacion en pasos de la API (solo texto)."""
    pasos = []
    for mensaje in memoria.cargar_historial(chat_id):
        if mensaje["rol"] == "usuario":
            pasos.append(gemini.paso_usuario(mensaje["texto"]))
        else:
            pasos.append(gemini.paso_modelo(mensaje["texto"]))
    return pasos


def ejecutar_llamada(llamada):
    """Ejecuta un paso function_call y devuelve el paso function_result para Gemini."""
    nombre = llamada.get("name")
    resultado = herramientas.ejecutar(nombre, llamada.get("arguments") or {})
    texto_json = json.dumps(resultado, ensure_ascii=False)
    return gemini.paso_resultado(nombre, llamada.get("id"), texto_json)


def responder(mensaje, chat_id=None):
    """Responde un mensaje del usuario en una conversacion (la primera si no se indica). Devuelve el texto final.

    Bucle de funciones (maximo 5 vueltas, cada una es una peticion a Gemini):
      1. Llamar a Gemini con el historial + el mensaje nuevo.
      2. Guardar TODOS los pasos devueltos tal como llegaron (llevan firmas).
      3. Si pide funciones: ejecutarlas, agregar los resultados y volver al 1.
      4. Si no, el texto de la respuesta es el final.
    """
    pasos = historial_a_pasos(chat_id) + [gemini.paso_usuario(mensaje)]
    instruccion = armar_instruccion()

    for vuelta in range(MAXIMO_VUELTAS):
        devueltos = gemini.llamar_api(pasos, instruccion, herramientas_activas())
        pasos.extend(devueltos)

        llamadas = gemini.extraer_llamadas(devueltos)
        if not llamadas:
            texto = gemini.extraer_texto(pasos)
            if not texto:
                raise gemini.ErrorGemini("formato")
            # Solo al terminar bien: se guarda el mensaje y el texto final (no los pasos internos)
            memoria.agregar_mensaje("usuario", mensaje, chat_id)
            memoria.agregar_mensaje("asistente", texto, chat_id)
            return texto

        if vuelta == MAXIMO_VUELTAS - 1:
            break
        for llamada in llamadas:
            pasos.append(ejecutar_llamada(llamada))

    raise ErrorAsistente(textos.ERROR_DEMASIADAS_VUELTAS)
