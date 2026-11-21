"""Ayudas comunes para las pruebas.

- Agrega la carpeta del proyecto al path para poder importar los modulos.
- PruebaConDatos: cada prueba trabaja en una carpeta temporal (DIRECTORIO_DATOS),
  asi nunca se toca datos/ y nunca se usa una clave real.
"""

import logging
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

CARPETA_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if CARPETA_PROYECTO not in sys.path:
    sys.path.insert(0, CARPETA_PROYECTO)

import configuracion  # noqa: E402

# Evita que los avisos del registro ensucien la salida de las pruebas
logging.getLogger().addHandler(logging.NullHandler())

CLAVE_FALSA = "clave-falsa-para-pruebas"
CONTRASENA_FALSA = "contrasena-falsa-123"
SECRETO_FALSO = "secreto-falso-para-pruebas-0123456789"


class PruebaConDatos(unittest.TestCase):
    """Base: carpeta de datos temporal y configuracion falsa."""

    def setUp(self):
        self.carpeta = tempfile.mkdtemp(prefix="chatbot_prueba_")
        parches = [
            mock.patch.dict(os.environ, {"DIRECTORIO_DATOS": self.carpeta}),
            mock.patch.object(configuracion, "GEMINI_API_KEY", CLAVE_FALSA),
            mock.patch.object(configuracion, "APP_PASSWORD", CONTRASENA_FALSA),
            mock.patch.object(configuracion, "SECRET_KEY", SECRETO_FALSO),
            mock.patch.object(configuracion, "GEMINI_MODEL", "modelo-falso"),
            mock.patch.object(configuracion, "BOT_NAME", "Asistente"),
            mock.patch.object(configuracion, "ZONA_HORARIA", "America/Guayaquil"),
            mock.patch.object(configuracion, "BUSQUEDA_WEB", False),
            mock.patch.object(configuracion, "TAVILY_API_KEY", ""),
        ]
        for parche in parches:
            parche.start()
            self.addCleanup(parche.stop)
        self.addCleanup(shutil.rmtree, self.carpeta, ignore_errors=True)
