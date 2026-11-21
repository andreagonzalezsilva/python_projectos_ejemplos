"""Consultas a internet: noticias (Google News), Wikipedia y clima (Open-Meteo) sin clave,
y busqueda en toda la web con Tavily (necesita TAVILY_API_KEY).

Este archivo SOLO sabe pedir datos y devolverlos ordenados. No sabe nada de
Gemini ni de memoria. Usa solo sitios de la lista de permitidos de la cuenta
gratuita de PythonAnywhere (news.google.com, es.wikipedia.org, Open-Meteo y api.tavily.com).
Si algo falla lanza ErrorInternet; herramientas.py lo convierte en {"error": ...}.
"""

import logging
import xml.etree.ElementTree as ET
from urllib.parse import quote

import requests

import textos

registro = logging.getLogger(__name__)

URL_NOTICIAS = "https://news.google.com/rss"
URL_NOTICIAS_BUSCAR = "https://news.google.com/rss/search"
# Idioma y pais de las noticias: espanol de Latinoamerica, Ecuador
PARAMETROS_REGION = {"hl": "es-419", "gl": "EC", "ceid": "EC:es-419"}

URL_WIKIPEDIA = "https://es.wikipedia.org/w/api.php"
URL_ARTICULO = "https://es.wikipedia.org/wiki/"

URL_TAVILY = "https://api.tavily.com/search"
RESULTADOS_TAVILY = 5

URL_GEOCODIFICACION = "https://geocoding-api.open-meteo.com/v1/search"
URL_PRONOSTICO = "https://api.open-meteo.com/v1/forecast"
DIAS_PRONOSTICO = 3

TIEMPO_MAXIMO = 10  # segundos
LARGO_RESUMEN = 700  # caracteres por articulo: cada uno cuesta tokens
# Wikipedia pide identificarse con un User-Agent propio
CABECERAS = {"User-Agent": "AsistenteEscolar/1.0 (proyecto de clase; Python requests)"}


class ErrorInternet(Exception):
    """No se pudo obtener o leer la respuesta de internet.

    "codigo" indica el motivo cuando se conoce: "clave" o "limite" (ver textos.ERRORES_INTERNET).
    """

    def __init__(self, codigo=None):
        self.codigo = codigo
        super().__init__(codigo or "internet")


def _pedir(url, parametros):
    try:
        respuesta = requests.get(url, params=parametros, headers=CABECERAS, timeout=TIEMPO_MAXIMO)
        respuesta.raise_for_status()
    except requests.RequestException as error:
        registro.warning("Fallo la consulta a %s: %s", url, type(error).__name__)
        raise ErrorInternet() from error
    return respuesta


def noticias(tema="", maximo=5):
    """Titulares recientes. Sin tema devuelve las noticias principales.

    Devuelve una lista de {"titulo", "fuente", "fecha"}.
    """
    if tema:
        url, parametros = URL_NOTICIAS_BUSCAR, dict(PARAMETROS_REGION, q=tema)
    else:
        url, parametros = URL_NOTICIAS, dict(PARAMETROS_REGION)
    respuesta = _pedir(url, parametros)
    try:
        raiz = ET.fromstring(respuesta.content)
        resultado = []
        for item in raiz.iter("item"):
            fuente = (item.findtext("source") or "").strip()
            titulo = (item.findtext("title") or "").strip()
            # Google agrega " - Fuente" al final del titulo: ya va en su propio campo
            if fuente and titulo.endswith(" - " + fuente):
                titulo = titulo[: -len(" - " + fuente)]
            if titulo:
                resultado.append({
                    "titulo": titulo,
                    "fuente": fuente,
                    "fecha": (item.findtext("pubDate") or "").strip(),
                })
            if len(resultado) >= maximo:
                break
    except ET.ParseError as error:
        registro.warning("Respuesta de noticias con formato inesperado")
        raise ErrorInternet() from error
    return resultado


def wikipedia(consulta, maximo=3):
    """Resumen de los articulos de Wikipedia mas parecidos a la consulta.

    Devuelve una lista de {"titulo", "resumen", "url"}.
    """
    parametros = {
        "action": "query", "format": "json", "formatversion": 2,
        "generator": "search", "gsrsearch": consulta, "gsrlimit": maximo,
        "prop": "extracts", "exintro": 1, "explaintext": 1, "exlimit": maximo,
    }
    respuesta = _pedir(URL_WIKIPEDIA, parametros)
    try:
        paginas = respuesta.json().get("query", {}).get("pages", [])
        paginas = sorted(paginas, key=lambda pagina: pagina.get("index", 0))
        resultado = []
        for pagina in paginas:
            titulo = pagina["title"]
            resumen = " ".join((pagina.get("extract") or "").split())
            resultado.append({
                "titulo": titulo,
                "resumen": resumen[:LARGO_RESUMEN],
                "url": URL_ARTICULO + quote(titulo.replace(" ", "_")),
            })
    except (ValueError, KeyError, TypeError, AttributeError) as error:
        registro.warning("Respuesta de Wikipedia con formato inesperado")
        raise ErrorInternet() from error
    return resultado


def clima(ciudad):
    """Clima actual y pronostico de los proximos dias de una ciudad (Open-Meteo, sin clave).

    Devuelve None si no se encuentra la ciudad; si no, un diccionario con
    "lugar", "ahora", "proximos_dias" y "fuente".
    """
    busqueda = _pedir(URL_GEOCODIFICACION, {
        "name": ciudad, "count": 1, "language": "es", "format": "json"})
    try:
        lugares = busqueda.json().get("results") or []
        if not lugares:
            return None
        lugar = lugares[0]
        latitud, longitud = lugar["latitude"], lugar["longitude"]
        nombre = ", ".join(str(lugar[campo]) for campo in ("name", "admin1", "country") if lugar.get(campo))
    except (ValueError, KeyError, TypeError, AttributeError) as error:
        registro.warning("Respuesta de geocodificacion con formato inesperado")
        raise ErrorInternet() from error

    pronostico = _pedir(URL_PRONOSTICO, {
        "latitude": latitud, "longitude": longitud, "timezone": "auto",
        "forecast_days": DIAS_PRONOSTICO,
        "current": "temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,weather_code,wind_speed_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max",
    })
    try:
        datos = pronostico.json()
        actual, diario = datos["current"], datos["daily"]
        resultado = {
            "lugar": nombre,
            "ahora": {
                "estado": textos.CODIGOS_CLIMA.get(actual["weather_code"], "desconocido"),
                "temperatura_c": actual["temperature_2m"],
                "sensacion_c": actual["apparent_temperature"],
                "humedad_pct": actual["relative_humidity_2m"],
                "viento_kmh": actual["wind_speed_10m"],
                "lluvia_mm": actual["precipitation"],
            },
            "proximos_dias": [
                {
                    "fecha": fecha,
                    "estado": textos.CODIGOS_CLIMA.get(diario["weather_code"][i], "desconocido"),
                    "min_c": diario["temperature_2m_min"][i],
                    "max_c": diario["temperature_2m_max"][i],
                    "lluvia_mm": diario["precipitation_sum"][i],
                    "prob_lluvia_pct": diario["precipitation_probability_max"][i],
                }
                for i, fecha in enumerate(diario["time"])
            ],
            "fuente": "Open-Meteo.com",
        }
    except (ValueError, KeyError, TypeError, IndexError) as error:
        registro.warning("Respuesta de pronostico con formato inesperado")
        raise ErrorInternet() from error
    return resultado


def buscar_web(consulta, clave, maximo=RESULTADOS_TAVILY):
    """Busca en toda la web con Tavily. Devuelve una lista de {"titulo", "url", "resumen"}.

    La clave solo viaja en la cabecera Authorization y nunca se escribe en el registro.
    """
    try:
        respuesta = requests.post(
            URL_TAVILY,
            headers=dict(CABECERAS, Authorization="Bearer " + clave),
            json={"query": consulta, "search_depth": "basic", "max_results": maximo},
            timeout=TIEMPO_MAXIMO,
        )
    except requests.RequestException as error:
        registro.warning("Fallo la consulta a Tavily: %s", type(error).__name__)
        raise ErrorInternet() from error

    if respuesta.status_code != 200:
        registro.warning("Tavily respondio HTTP %s", respuesta.status_code)
        if respuesta.status_code == 401:
            raise ErrorInternet("clave")
        if respuesta.status_code in (429, 432, 433):
            raise ErrorInternet("limite")
        raise ErrorInternet()

    try:
        return [
            {
                "titulo": (item.get("title") or "").strip(),
                "url": item["url"],
                "resumen": " ".join((item.get("content") or "").split())[:LARGO_RESUMEN],
            }
            for item in respuesta.json().get("results", [])[:maximo]
        ]
    except (ValueError, KeyError, TypeError, AttributeError) as error:
        registro.warning("Respuesta de Tavily con formato inesperado")
        raise ErrorInternet() from error
