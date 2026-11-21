"""Permite ejecutar todas las pruebas con el comando corto:

    python -m unittest discover -s pruebas -v

unittest solo descubre por defecto archivos que empiezan con "test". Este
archivo carga las pruebas prueba_*.py de esta misma carpeta.
"""

import os
import unittest


def load_tests(cargador, pruebas, patron):
    carpeta = os.path.dirname(os.path.abspath(__file__))
    return cargador.discover(carpeta, pattern="prueba_*.py", top_level_dir=carpeta)
