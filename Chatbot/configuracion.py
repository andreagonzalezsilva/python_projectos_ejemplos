"""Lee la configuracion desde el archivo .env y las variables de entorno.

Importante: el .env se busca junto a este archivo (ruta absoluta), no en la
carpeta actual. En PythonAnywhere la carpeta actual NO es la del proyecto.
"""

import os

from dotenv import load_dotenv

CARPETA_PROYECTO = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(CARPETA_PROYECTO, ".env"))

# Valores de ejemplo que trae .env.example: si siguen asi, falta configurar
VALORES_DE_EJEMPLO = {
    "GEMINI_API_KEY": "pega_aqui_tu_clave",
    "APP_PASSWORD": "cambia_esta_contrasena",
    "SECRET_KEY": "cambia_esto_por_una_cadena_larga",
}

OBLIGATORIAS = ["GEMINI_API_KEY", "APP_PASSWORD", "SECRET_KEY"]

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "").strip() or "gemini-3.5-flash-lite"
BOT_NAME = os.environ.get("BOT_NAME", "").strip() or "Asistente"
APP_PASSWORD = os.environ.get("APP_PASSWORD", "").strip()
SECRET_KEY = os.environ.get("SECRET_KEY", "").strip()
ZONA_HORARIA = os.environ.get("ZONA_HORARIA", "").strip() or "America/Guayaquil"
# Opcional: con clave de Tavily el asistente puede buscar en toda la web (plan gratuito: 1000 busquedas al mes)
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "").strip()
# Busqueda en internet con Google Search. Requiere facturacion activada en Gemini (no hay plan gratuito)
BUSQUEDA_WEB = os.environ.get("BUSQUEDA_WEB", "").strip().lower() in ("1", "true", "si", "sí")


def ruta_datos():
    """Devuelve la carpeta donde se guardan los JSON (la crea si no existe).

    Si existe la variable DIRECTORIO_DATOS se usa esa carpeta: asi las pruebas
    trabajan en una carpeta temporal y nunca tocan datos/.
    """
    carpeta = os.environ.get("DIRECTORIO_DATOS", "").strip()
    if not carpeta:
        carpeta = os.path.join(CARPETA_PROYECTO, "datos")
    os.makedirs(carpeta, exist_ok=True)
    return carpeta


def ruta_archivo(nombre):
    """Ruta absoluta de un archivo que vive junto al codigo (ej. personalidad.txt)."""
    return os.path.join(CARPETA_PROYECTO, nombre)


def faltantes():
    """Lista de variables obligatorias vacias o que aun tienen el valor de ejemplo."""
    valores = {
        "GEMINI_API_KEY": GEMINI_API_KEY,
        "APP_PASSWORD": APP_PASSWORD,
        "SECRET_KEY": SECRET_KEY,
    }
    lista = []
    for nombre in OBLIGATORIAS:
        valor = valores[nombre]
        if not valor or valor == VALORES_DE_EJEMPLO[nombre]:
            lista.append(nombre)
    return lista
