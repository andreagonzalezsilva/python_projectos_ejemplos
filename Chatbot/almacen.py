"""Leer y escribir archivos JSON de forma segura.

La escritura es atomica: primero se escribe en un archivo temporal de la misma
carpeta y luego se reemplaza el original con os.replace. Si el programa se corta
a mitad de escritura, el JSON original no queda roto.
"""

import copy
import json
import os
import tempfile

import configuracion


def _ruta(nombre):
    return os.path.join(configuracion.ruta_datos(), nombre)


def leer_json(nombre, por_defecto):
    """Lee datos/<nombre>. Si no existe o esta danado, devuelve por_defecto.

    Un archivo danado se renombra agregandole la terminacion .corrupto.
    """
    ruta = _ruta(nombre)
    if not os.path.exists(ruta):
        return copy.deepcopy(por_defecto)
    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            return json.load(archivo)
    except (ValueError, OSError):
        try:
            os.replace(ruta, ruta + ".corrupto")
        except OSError:
            pass
        return copy.deepcopy(por_defecto)


def escribir_json(nombre, datos):
    """Guarda datos en datos/<nombre> con escritura atomica."""
    ruta = _ruta(nombre)
    carpeta = os.path.dirname(ruta)
    descriptor, ruta_temporal = tempfile.mkstemp(dir=carpeta, suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, ensure_ascii=False, indent=2)
        os.replace(ruta_temporal, ruta)
    except BaseException:
        if os.path.exists(ruta_temporal):
            os.remove(ruta_temporal)
        raise
