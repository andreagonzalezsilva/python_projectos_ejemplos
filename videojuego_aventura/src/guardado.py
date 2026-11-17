"""Lectura y escritura de puntaje.json (mejor puntaje, idioma, personaje y accesorio)."""
import json
import os

CARPETA_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA = os.path.join(CARPETA_RAIZ, "puntaje.json")

DATOS_INICIALES = {
    "mejor_puntaje": 0,
    "idioma": "es",
    "personaje": "lorena",
    "accesorio": "poncho",
}


def leer():
    """Lee el archivo. Si no existe o esta danado, devuelve los valores iniciales."""
    datos = dict(DATOS_INICIALES)
    try:
        with open(RUTA, "r", encoding="utf-8") as archivo:
            leidos = json.load(archivo)
        if isinstance(leidos, dict):
            for clave in DATOS_INICIALES:
                if clave in leidos:
                    datos[clave] = leidos[clave]
    except (OSError, ValueError):
        pass
    return datos


def escribir(datos):
    """Guarda el diccionario completo en puntaje.json."""
    completos = dict(DATOS_INICIALES)
    completos.update({k: v for k, v in datos.items() if k in DATOS_INICIALES})
    try:
        with open(RUTA, "w", encoding="utf-8") as archivo:
            json.dump(completos, archivo, indent=2, ensure_ascii=False)
    except OSError:
        pass


def actualizar(**cambios):
    """Lee, aplica los cambios y vuelve a guardar. Devuelve los datos nuevos."""
    datos = leer()
    datos.update(cambios)
    escribir(datos)
    return datos


def asegurar_archivo():
    """Crea puntaje.json si todavia no existe."""
    if not os.path.exists(RUTA):
        escribir(DATOS_INICIALES)
