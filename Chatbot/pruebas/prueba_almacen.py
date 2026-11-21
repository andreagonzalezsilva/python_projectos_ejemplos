import os
import subprocess
import sys
import unittest

import ayuda  # noqa: F401  (prepara el path y los datos temporales)

import almacen
import configuracion


class PruebaAlmacen(ayuda.PruebaConDatos):
    def test_archivo_inexistente_devuelve_por_defecto(self):
        self.assertEqual(almacen.leer_json("nada.json", {"a": 1}), {"a": 1})

    def test_por_defecto_no_se_comparte(self):
        por_defecto = {"lista": []}
        resultado = almacen.leer_json("nada.json", por_defecto)
        resultado["lista"].append(1)
        self.assertEqual(por_defecto, {"lista": []})

    def test_escribir_y_leer_con_tildes(self):
        datos = {"texto": "Añadir canción", "n": 3}
        almacen.escribir_json("a.json", datos)
        self.assertEqual(almacen.leer_json("a.json", None), datos)
        with open(os.path.join(self.carpeta, "a.json"), encoding="utf-8") as archivo:
            self.assertIn("Añadir canción", archivo.read())

    def test_escritura_atomica_no_deja_temporales(self):
        almacen.escribir_json("a.json", {"x": 1})
        almacen.escribir_json("a.json", {"x": 2})
        self.assertEqual(os.listdir(self.carpeta), ["a.json"])

    def test_fallo_al_escribir_conserva_el_original(self):
        almacen.escribir_json("a.json", {"x": 1})
        with self.assertRaises(TypeError):
            almacen.escribir_json("a.json", {"x": object()})
        self.assertEqual(almacen.leer_json("a.json", None), {"x": 1})
        self.assertEqual(os.listdir(self.carpeta), ["a.json"])

    def test_archivo_corrupto_se_renombra(self):
        ruta = os.path.join(self.carpeta, "a.json")
        with open(ruta, "w", encoding="utf-8") as archivo:
            archivo.write("{esto no es json")
        self.assertEqual(almacen.leer_json("a.json", {"ok": True}), {"ok": True})
        self.assertFalse(os.path.exists(ruta))
        self.assertTrue(os.path.exists(ruta + ".corrupto"))

    def test_ruta_datos_usa_la_variable_de_entorno(self):
        self.assertEqual(configuracion.ruta_datos(), self.carpeta)


class PruebaConfiguracion(ayuda.PruebaConDatos):
    def test_faltantes_vacio_con_valores_reales(self):
        self.assertEqual(configuracion.faltantes(), [])

    def test_faltantes_detecta_valores_de_ejemplo_y_vacios(self):
        from unittest import mock

        with mock.patch.object(configuracion, "GEMINI_API_KEY", "pega_aqui_tu_clave"), \
                mock.patch.object(configuracion, "APP_PASSWORD", ""):
            self.assertEqual(configuracion.faltantes(), ["GEMINI_API_KEY", "APP_PASSWORD"])

    def test_importar_sin_env_funciona(self):
        # Proceso nuevo, sin variables de entorno del proyecto ni .env en una carpeta vacia
        entorno = {k: v for k, v in os.environ.items()
                   if k not in ("GEMINI_API_KEY", "APP_PASSWORD", "SECRET_KEY")}
        resultado = subprocess.run(
            [sys.executable, "-c",
             "import configuracion; print(configuracion.BOT_NAME)"],
            cwd=ayuda.CARPETA_PROYECTO, env=entorno,
            capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(resultado.returncode, 0, resultado.stderr)


if __name__ == "__main__":
    unittest.main()
