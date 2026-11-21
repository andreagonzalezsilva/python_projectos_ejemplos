"""UNA prueba con Gemini de verdad. Gasta 2 peticiones de la cuota gratuita.

Se omite si no hay una GEMINI_API_KEY real en .env, y tambien si no pides
explicitamente la prueba real. Para ejecutarla:

    .venv\\Scripts\\python pruebas\\prueba_real.py

(Al correr este archivo directamente se activa solo; dentro de
"unittest discover" se omite para no gastar cuota.)
Usa una carpeta de datos temporal: no toca datos/.
"""

import os
import shutil
import tempfile
import unittest
from unittest import mock

import ayuda  # noqa: F401  (prepara el path)

import asistente
import configuracion
import herramientas

def mostrar(*partes):
    """print que no falla con emojis en la consola de Windows (cp1252)."""
    texto = " ".join(str(parte) for parte in partes)
    print(texto.encode("ascii", "replace").decode("ascii"))


CLAVE_REAL = configuracion.GEMINI_API_KEY
TIENE_CLAVE_REAL = bool(CLAVE_REAL) and CLAVE_REAL != configuracion.VALORES_DE_EJEMPLO["GEMINI_API_KEY"]


class PruebaReal(unittest.TestCase):
    def setUp(self):
        if not TIENE_CLAVE_REAL:
            self.skipTest("No hay GEMINI_API_KEY real en .env")
        if os.environ.get("PRUEBA_REAL") != "1":
            self.skipTest("Prueba real no solicitada (ejecuta pruebas/prueba_real.py)")
        self.carpeta = tempfile.mkdtemp(prefix="chatbot_real_")
        parche = mock.patch.dict(os.environ, {"DIRECTORIO_DATOS": self.carpeta})
        parche.start()
        self.addCleanup(parche.stop)
        self.addCleanup(shutil.rmtree, self.carpeta, ignore_errors=True)

    def test_apuntar_una_tarea(self):
        respuesta = asistente.responder("Apúntame comprar pan")
        mostrar("\nRespuesta real:", respuesta)
        self.assertTrue(respuesta.strip())
        textos_de_tareas = [t["texto"].lower() for t in herramientas.todas_las_tareas()]
        self.assertTrue(any("pan" in texto for texto in textos_de_tareas), textos_de_tareas)

    def test_wikipedia_y_noticias(self):
        # Sin clave de Tavily la busqueda general es Wikipedia
        with mock.patch.object(configuracion, "BUSQUEDA_WEB", False), \
                mock.patch.object(configuracion, "TAVILY_API_KEY", ""):
            llamadas = []
            original = herramientas.ejecutar

            def espiar(nombre, argumentos):
                llamadas.append(nombre)
                return original(nombre, argumentos)

            with mock.patch("asistente.herramientas.ejecutar", espiar):
                datos = asistente.responder("Busca en Wikipedia quién ganó la Eurocopa 2024 y dime el marcador de la final.")
                mostrar("\nRespuesta Wikipedia:", datos, llamadas)
                self.assertEqual(llamadas, ["buscar_wikipedia"])
                self.assertIn("españa", datos.lower())
                noticias = asistente.responder("¿Cuáles son las últimas noticias de Ecuador?")
                mostrar("\nRespuesta noticias:", noticias, llamadas)
                self.assertIn("buscar_noticias", llamadas)

    def test_clima(self):
        with mock.patch.object(configuracion, "BUSQUEDA_WEB", False):
            resultado = herramientas.ejecutar("consultar_clima", {"ciudad": "Quito"})
            mostrar("\nClima Open-Meteo:", resultado)
            self.assertEqual(resultado["lugar"].split(",")[0], "Quito")
            self.assertEqual(len(resultado["proximos_dias"]), 3)
            respuesta = asistente.responder("¿Va a llover mañana en Cuenca, Ecuador?")
            mostrar("Respuesta clima:", respuesta)
            self.assertTrue(respuesta.strip())

    def test_tavily(self):
        if not configuracion.TAVILY_API_KEY:
            self.skipTest("No hay TAVILY_API_KEY en .env")
        with mock.patch.object(configuracion, "BUSQUEDA_WEB", False):
            resultado = herramientas.ejecutar("buscar_web", {"consulta": "Ecuador capital población"})
            mostrar("\nTavily:", resultado)
            self.assertNotIn("error", resultado)
            self.assertTrue(resultado["resultados"])
            llamadas = []
            original = herramientas.ejecutar

            def espiar(nombre, argumentos):
                llamadas.append(nombre)
                return original(nombre, argumentos)

            with mock.patch("asistente.herramientas.ejecutar", espiar):
                respuesta = asistente.responder(
                    "Busca en la web las mejores universidades de Ecuador y dame las fuentes con su dirección.")
            mostrar("Respuesta Tavily:", respuesta, llamadas)
            # Una sola busqueda general: ni Wikipedia ni buscar_web repetido
            self.assertEqual(llamadas, ["buscar_web"])

    def test_busqueda_web(self):
        if not configuracion.BUSQUEDA_WEB:
            self.skipTest("BUSQUEDA_WEB no esta activa en .env (requiere facturacion en Gemini)")
        respuesta = asistente.responder(
            "Busca en internet quién ganó la Eurocopa 2024 y dime el resultado de la final.")
        mostrar("\nRespuesta con busqueda web:", respuesta)
        self.assertIn("españa", respuesta.lower().replace("spain", "españa"))
        self.assertNotIn("no tengo acceso", respuesta.lower())


if __name__ == "__main__":
    os.environ["PRUEBA_REAL"] = "1"
    unittest.main(verbosity=2)
