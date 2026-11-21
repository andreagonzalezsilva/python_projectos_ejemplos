import json
import unittest
from unittest import mock

import ayuda

import herramientas
import memoria
import textos


class PruebaTareas(ayuda.PruebaConDatos):
    def test_agregar_y_listar(self):
        resultado = herramientas.ejecutar("agregar_tarea", {"texto": "  comprar pan  "})
        self.assertEqual(resultado, {"id": 1, "texto": "comprar pan", "hecha": False})
        listado = herramientas.ejecutar("listar_tareas", {})
        self.assertEqual([t["texto"] for t in listado["tareas"]], ["comprar pan"])

    def test_listar_por_defecto_solo_pendientes(self):
        herramientas.ejecutar("agregar_tarea", {"texto": "a"})
        herramientas.ejecutar("agregar_tarea", {"texto": "b"})
        herramientas.ejecutar("completar_tarea", {"id": 1})
        pendientes = herramientas.ejecutar("listar_tareas", {})["tareas"]
        self.assertEqual([t["id"] for t in pendientes], [2])
        todas = herramientas.ejecutar("listar_tareas", {"solo_pendientes": False})["tareas"]
        self.assertEqual([t["id"] for t in todas], [1, 2])

    def test_completar(self):
        herramientas.ejecutar("agregar_tarea", {"texto": "a"})
        self.assertEqual(herramientas.ejecutar("completar_tarea", {"id": 1}), {"id": 1, "hecha": True})
        self.assertTrue(herramientas.todas_las_tareas()[0]["hecha"])

    def test_completar_acepta_entero_como_decimal(self):
        herramientas.ejecutar("agregar_tarea", {"texto": "a"})
        self.assertEqual(herramientas.ejecutar("completar_tarea", {"id": 1.0}), {"id": 1, "hecha": True})

    def test_tarea_inexistente(self):
        self.assertEqual(herramientas.ejecutar("completar_tarea", {"id": 3}),
                         {"error": "No existe la tarea 3"})

    def test_los_ids_nunca_se_reutilizan(self):
        herramientas.ejecutar("agregar_tarea", {"texto": "a"})
        herramientas.ejecutar("agregar_tarea", {"texto": "b"})
        # Aunque se borre la ultima a mano, el siguiente id sigue creciendo
        datos = herramientas.almacen.leer_json("tareas.json", None)
        datos["tareas"].pop()
        herramientas.almacen.escribir_json("tareas.json", datos)
        self.assertEqual(herramientas.ejecutar("agregar_tarea", {"texto": "c"})["id"], 3)

    def test_limite_de_100_tareas(self):
        for numero in range(herramientas.MAXIMO_TAREAS):
            self.assertNotIn("error", herramientas.ejecutar("agregar_tarea", {"texto": f"t{numero}"}))
        resultado = herramientas.ejecutar("agregar_tarea", {"texto": "una mas"})
        self.assertIn("error", resultado)
        self.assertEqual(len(herramientas.todas_las_tareas()), 100)

    def test_limite_de_texto(self):
        self.assertNotIn("error", herramientas.ejecutar("agregar_tarea", {"texto": "x" * 500}))
        self.assertIn("error", herramientas.ejecutar("agregar_tarea", {"texto": "x" * 501}))

    def test_texto_vacio(self):
        self.assertEqual(herramientas.ejecutar("agregar_tarea", {"texto": "   "}),
                         {"error": textos.HERRAMIENTA_TEXTO_VACIO})


class PruebaNotas(ayuda.PruebaConDatos):
    def test_agregar_y_listar(self):
        self.assertEqual(herramientas.ejecutar("agregar_nota", {"texto": "idea"}),
                         {"id": 1, "texto": "idea"})
        self.assertEqual(herramientas.ejecutar("agregar_nota", {"texto": "otra"})["id"], 2)
        notas = herramientas.ejecutar("listar_notas", {})["notas"]
        self.assertEqual([n["texto"] for n in notas], ["idea", "otra"])

    def test_limites(self):
        self.assertNotIn("error", herramientas.ejecutar("agregar_nota", {"texto": "x" * 1000}))
        self.assertIn("error", herramientas.ejecutar("agregar_nota", {"texto": "x" * 1001}))
        for _ in range(herramientas.MAXIMO_NOTAS - 1):
            herramientas.ejecutar("agregar_nota", {"texto": "n"})
        self.assertIn("error", herramientas.ejecutar("agregar_nota", {"texto": "n"}))
        self.assertEqual(len(herramientas.todas_las_notas()), 100)


class PruebaPreferencias(ayuda.PruebaConDatos):
    def test_guardar(self):
        resultado = herramientas.ejecutar("guardar_preferencia", {"clave": "nombre", "valor": "Ana"})
        self.assertEqual(resultado, {"clave": "nombre", "valor": "Ana"})
        self.assertEqual(memoria.cargar_preferencias(), {"nombre": "Ana"})

    def test_limites(self):
        self.assertIn("error", herramientas.ejecutar(
            "guardar_preferencia", {"clave": "k" * 41, "valor": "v"}))
        self.assertIn("error", herramientas.ejecutar(
            "guardar_preferencia", {"clave": "k", "valor": "v" * 201}))
        self.assertNotIn("error", herramientas.ejecutar(
            "guardar_preferencia", {"clave": "k" * 40, "valor": "v" * 200}))

    def test_maximo_20_preferencias(self):
        for numero in range(19):
            herramientas.ejecutar("guardar_preferencia", {"clave": f"k{numero}", "valor": "v"})
        self.assertNotIn("error", herramientas.ejecutar(
            "guardar_preferencia", {"clave": "ultima", "valor": "v"}))
        self.assertIn("error", herramientas.ejecutar(
            "guardar_preferencia", {"clave": "sobra", "valor": "v"}))
        self.assertNotIn("error", herramientas.ejecutar(
            "guardar_preferencia", {"clave": "ultima", "valor": "otro"}))
        self.assertEqual(len(memoria.cargar_preferencias()), 20)


class PruebaEjecutar(ayuda.PruebaConDatos):
    def test_funcion_desconocida(self):
        self.assertEqual(herramientas.ejecutar("borrar_todo", {}), {"error": "Función desconocida"})

    def test_tipos_incorrectos(self):
        for nombre, argumentos in [
            ("agregar_tarea", {"texto": 5}),
            ("agregar_tarea", {"texto": None}),
            ("completar_tarea", {"id": "uno"}),
            ("completar_tarea", {"id": 1.5}),
            ("completar_tarea", {"id": True}),
            ("listar_tareas", {"solo_pendientes": "si"}),
            ("guardar_preferencia", {"clave": "a", "valor": ["x"]}),
        ]:
            with self.subTest(nombre=nombre, argumentos=argumentos):
                self.assertIn("error", herramientas.ejecutar(nombre, argumentos))
        self.assertEqual(herramientas.todas_las_tareas(), [])

    def test_falta_un_argumento_obligatorio(self):
        self.assertIn("error", herramientas.ejecutar("agregar_tarea", {}))
        self.assertIn("error", herramientas.ejecutar("guardar_preferencia", {"clave": "a"}))

    def test_argumentos_que_no_son_diccionario(self):
        self.assertIn("error", herramientas.ejecutar("listar_notas", None))
        self.assertIn("error", herramientas.ejecutar("listar_notas", "x"))

    def test_nunca_lanza_excepcion(self):
        original = herramientas.FUNCIONES["listar_notas"]
        herramientas.FUNCIONES["listar_notas"] = lambda: 1 / 0
        try:
            resultado = herramientas.ejecutar("listar_notas", {})
        finally:
            herramientas.FUNCIONES["listar_notas"] = original
        self.assertEqual(resultado, {"error": textos.HERRAMIENTA_FALLO})


class PruebaDeclaraciones(unittest.TestCase):
    def test_hay_diez_y_coinciden_con_las_funciones(self):
        nombres = [d["name"] for d in herramientas.DECLARACIONES]
        self.assertEqual(sorted(nombres), sorted(herramientas.FUNCIONES))
        self.assertEqual(len(nombres), 10)

    def nombres_activos(self, google, clave):
        with mock.patch("herramientas.configuracion.BUSQUEDA_WEB", google), \
                mock.patch("herramientas.configuracion.TAVILY_API_KEY", clave):
            return [d["name"] for d in herramientas.declaraciones_activas()]

    def test_una_sola_busqueda_general_segun_la_configuracion(self):
        nombres = self.nombres_activos(google=False, clave="")
        self.assertIn("buscar_wikipedia", nombres)
        self.assertNotIn("buscar_web", nombres)
        nombres = self.nombres_activos(google=False, clave="tvly-falsa")
        self.assertIn("buscar_web", nombres)
        self.assertNotIn("buscar_wikipedia", nombres)
        for google_clave in ("", "tvly-falsa"):
            nombres = self.nombres_activos(google=True, clave=google_clave)
            self.assertNotIn("buscar_web", nombres)
            self.assertNotIn("buscar_wikipedia", nombres)
        for fija in ("buscar_noticias", "consultar_clima", "agregar_tarea"):
            self.assertIn(fija, nombres)

    def test_formato_de_la_api(self):
        for declaracion in herramientas.DECLARACIONES:
            self.assertEqual(declaracion["type"], "function")
            self.assertTrue(declaracion["description"])
            parametros = declaracion["parameters"]
            self.assertEqual(parametros["type"], "object")
            for propiedad in parametros["properties"].values():
                self.assertIn(propiedad["type"], ("string", "boolean", "integer"))
                self.assertTrue(propiedad["description"])
            for obligatorio in parametros["required"]:
                self.assertIn(obligatorio, parametros["properties"])

    def test_se_pueden_convertir_a_json(self):
        json.dumps(herramientas.DECLARACIONES)

    def test_parametros_obligatorios(self):
        por_nombre = {d["name"]: d["parameters"] for d in herramientas.DECLARACIONES}
        self.assertEqual(por_nombre["listar_tareas"]["required"], [])
        self.assertEqual(por_nombre["completar_tarea"]["required"], ["id"])
        self.assertEqual(por_nombre["guardar_preferencia"]["required"], ["clave", "valor"])
        self.assertEqual(por_nombre["buscar_noticias"]["required"], [])
        self.assertEqual(por_nombre["buscar_wikipedia"]["required"], ["consulta"])
        self.assertEqual(por_nombre["consultar_clima"]["required"], ["ciudad"])
        self.assertEqual(por_nombre["buscar_web"]["required"], ["consulta"])


if __name__ == "__main__":
    unittest.main()
