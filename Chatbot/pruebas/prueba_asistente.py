import copy
import json
import unittest
from unittest import mock

import ayuda

import asistente
import gemini
import herramientas
import memoria
import textos


def llamada(id_llamada, nombre, argumentos):
    return {"type": "function_call", "id": id_llamada, "name": nombre, "arguments": argumentos}


class GeminiSimulado:
    """Reemplaza gemini.llamar_api: devuelve respuestas en orden y guarda copias de lo que recibe."""

    def __init__(self, *respuestas):
        self.respuestas = list(respuestas)
        self.recibidos = []

    def __call__(self, pasos, instruccion_sistema="", herramientas=None):
        self.recibidos.append({
            "pasos": copy.deepcopy(pasos),
            "instruccion": instruccion_sistema,
            "herramientas": herramientas,
        })
        respuesta = self.respuestas.pop(0)
        if isinstance(respuesta, Exception):
            raise respuesta
        return respuesta


class PruebaBucle(ayuda.PruebaConDatos):
    def responder(self, simulado, mensaje="hola"):
        with mock.patch("asistente.gemini.llamar_api", simulado):
            return asistente.responder(mensaje)

    def test_respuesta_sin_herramientas(self):
        simulado = GeminiSimulado([gemini.paso_modelo("¡Hola!")])
        self.assertEqual(self.responder(simulado), "¡Hola!")
        self.assertEqual(len(simulado.recibidos), 1)
        self.assertEqual(simulado.recibidos[0]["herramientas"], herramientas.declaraciones_activas())
        nombres = [d["name"] for d in simulado.recibidos[0]["herramientas"]]
        self.assertNotIn("buscar_web", nombres)

        self.assertIn("buscar_wikipedia", nombres)

    def test_con_clave_de_tavily_solo_buscar_web_y_su_instruccion(self):
        simulado = GeminiSimulado([gemini.paso_modelo("hola")])
        with mock.patch("asistente.configuracion.TAVILY_API_KEY", "tvly-falsa"), \
                mock.patch("herramientas.configuracion.TAVILY_API_KEY", "tvly-falsa"):
            self.responder(simulado)
        nombres = [d["name"] for d in simulado.recibidos[0]["herramientas"]]
        self.assertIn("buscar_web", nombres)
        self.assertNotIn("buscar_wikipedia", nombres)
        instruccion = simulado.recibidos[0]["instruccion"]
        self.assertIn(textos.INSTRUCCION_BUSQUEDA_TAVILY, instruccion)
        self.assertNotIn(textos.INSTRUCCION_BUSQUEDA_WIKIPEDIA, instruccion)

    def test_sin_clave_de_tavily_solo_wikipedia_y_su_instruccion(self):
        simulado = GeminiSimulado([gemini.paso_modelo("hola")])
        self.responder(simulado)
        instruccion = simulado.recibidos[0]["instruccion"]
        self.assertIn(textos.INSTRUCCION_BUSQUEDA_WIKIPEDIA, instruccion)
        self.assertNotIn(textos.INSTRUCCION_BUSQUEDA_TAVILY, instruccion)

    def test_sin_busqueda_web_no_se_envia_google_search(self):
        simulado = GeminiSimulado([gemini.paso_modelo("hola")])
        with mock.patch("asistente.configuracion.BUSQUEDA_WEB", False):
            self.responder(simulado)
        self.assertNotIn({"type": "google_search"}, simulado.recibidos[0]["herramientas"])
        self.assertNotIn(textos.INSTRUCCION_BUSQUEDA_WEB, simulado.recibidos[0]["instruccion"])

    def test_con_busqueda_web_se_envia_google_search_y_la_instruccion(self):
        simulado = GeminiSimulado([gemini.paso_modelo("hola")])
        with mock.patch("asistente.configuracion.BUSQUEDA_WEB", True):
            self.responder(simulado)
            funciones = herramientas.declaraciones_activas()
        enviadas = simulado.recibidos[0]["herramientas"]
        self.assertIn({"type": "google_search"}, enviadas)
        self.assertEqual(enviadas[:-1], funciones)
        self.assertIn(textos.INSTRUCCION_BUSQUEDA_WEB, simulado.recibidos[0]["instruccion"])
        nombres = [d.get("name") for d in enviadas]
        self.assertNotIn("buscar_wikipedia", nombres)
        self.assertNotIn("buscar_web", nombres)

    def test_google_search_y_tavily_se_excluyen_aunque_haya_clave(self):
        simulado = GeminiSimulado([gemini.paso_modelo("hola")])
        with mock.patch("asistente.configuracion.BUSQUEDA_WEB", True), \
                mock.patch("asistente.configuracion.TAVILY_API_KEY", "tvly-falsa"):
            self.responder(simulado)
        enviadas = simulado.recibidos[0]["herramientas"]
        nombres = [d.get("name") for d in enviadas]
        self.assertIn({"type": "google_search"}, enviadas)
        self.assertNotIn("buscar_web", nombres)
        self.assertNotIn("buscar_wikipedia", nombres)
        for fija in ("buscar_noticias", "consultar_clima", "agregar_tarea"):
            self.assertIn(fija, nombres)
        instruccion = simulado.recibidos[0]["instruccion"]
        self.assertIn(textos.INSTRUCCION_BUSQUEDA_WEB, instruccion)
        self.assertNotIn(textos.INSTRUCCION_BUSQUEDA_TAVILY, instruccion)
        self.assertNotIn(textos.INSTRUCCION_BUSQUEDA_WIKIPEDIA, instruccion)

    def test_hay_exactamente_una_busqueda_general_en_cada_combinacion(self):
        general = {"buscar_web", "buscar_wikipedia", "google_search"}
        for google in (False, True):
            for clave in ("", "tvly-falsa"):
                simulado = GeminiSimulado([gemini.paso_modelo("hola")])
                with mock.patch("asistente.configuracion.BUSQUEDA_WEB", google), \
                        mock.patch("asistente.configuracion.TAVILY_API_KEY", clave):
                    self.responder(simulado)
                ofrecidas = {d.get("name") or d["type"] for d in simulado.recibidos[0]["herramientas"]}
                esperada = "google_search" if google else ("buscar_web" if clave else "buscar_wikipedia")
                self.assertEqual(ofrecidas & general, {esperada}, (google, clave))

    def test_cada_conversacion_usa_su_propio_historial(self):
        segunda = memoria.crear_conversacion()["id"]
        memoria.agregar_mensaje("usuario", "tema de la primera")
        memoria.agregar_mensaje("asistente", "ok primera")
        simulado = GeminiSimulado([gemini.paso_modelo("respuesta segunda")])
        with mock.patch("asistente.gemini.llamar_api", simulado):
            asistente.responder("hola desde la segunda", segunda)
        enviados = [paso["content"][0]["text"] for paso in simulado.recibidos[0]["pasos"]]
        self.assertEqual(enviados, ["hola desde la segunda"])  # no se mezcla con la primera
        self.assertEqual([m["texto"] for m in memoria.cargar_historial(segunda)],
                         ["hola desde la segunda", "respuesta segunda"])
        self.assertEqual([m["texto"] for m in memoria.cargar_historial(1)],
                         ["tema de la primera", "ok primera"])

    def test_las_preferencias_viajan_a_todas_las_conversaciones(self):
        segunda = memoria.crear_conversacion()["id"]
        memoria.guardar_preferencia("nombre", "Ana")
        simulado = GeminiSimulado([gemini.paso_modelo("hola")])
        with mock.patch("asistente.gemini.llamar_api", simulado):
            asistente.responder("hola", segunda)
        self.assertIn("- nombre: Ana", simulado.recibidos[0]["instruccion"])

    def test_ejecuta_la_funcion_y_termina_con_el_texto_final(self):
        simulado = GeminiSimulado(
            [llamada("c1", "agregar_tarea", {"texto": "comprar pan"})],
            [gemini.paso_modelo("Listo, apunté comprar pan.")],
        )
        texto = self.responder(simulado, "apúntame comprar pan")
        self.assertEqual(texto, "Listo, apunté comprar pan.")
        self.assertEqual(len(simulado.recibidos), 2)
        self.assertEqual([t["texto"] for t in herramientas.todas_las_tareas()], ["comprar pan"])

    def test_reenvia_los_pasos_intactos_con_el_function_result(self):
        paso_pensamiento = {"type": "thought", "signature": "FIRMA-ABC", "extra": {"x": 1}}
        paso_llamada = llamada("c1", "agregar_tarea", {"texto": "comprar pan"})
        paso_llamada["signature"] = "FIRMA-DEF"
        simulado = GeminiSimulado(
            [paso_pensamiento, paso_llamada],
            [gemini.paso_modelo("Hecho")],
        )
        self.responder(simulado, "apúntame comprar pan")

        segunda = simulado.recibidos[1]["pasos"]
        self.assertEqual([p["type"] for p in segunda],
                         ["user_input", "thought", "function_call", "function_result"])
        self.assertEqual(segunda[1], {"type": "thought", "signature": "FIRMA-ABC", "extra": {"x": 1}})
        self.assertEqual(segunda[2]["signature"], "FIRMA-DEF")
        resultado = segunda[3]
        self.assertEqual(resultado["name"], "agregar_tarea")
        self.assertEqual(resultado["call_id"], "c1")
        self.assertEqual(resultado["result"][0]["type"], "text")
        self.assertEqual(json.loads(resultado["result"][0]["text"]),
                         {"id": 1, "texto": "comprar pan", "hecha": False})

    def test_varias_llamadas_en_un_mismo_paso(self):
        simulado = GeminiSimulado(
            [llamada("a", "agregar_tarea", {"texto": "uno"}),
             llamada("b", "agregar_nota", {"texto": "idea"})],
            [gemini.paso_modelo("Hecho")],
        )
        self.responder(simulado)
        resultados = [p for p in simulado.recibidos[1]["pasos"] if p["type"] == "function_result"]
        self.assertEqual([r["call_id"] for r in resultados], ["a", "b"])
        self.assertEqual(len(herramientas.todas_las_notas()), 1)

    def test_error_de_herramienta_se_le_devuelve_a_gemini(self):
        simulado = GeminiSimulado(
            [llamada("c1", "completar_tarea", {"id": 99})],
            [gemini.paso_modelo("No existe esa tarea.")],
        )
        self.assertEqual(self.responder(simulado), "No existe esa tarea.")
        resultado = simulado.recibidos[1]["pasos"][-1]
        self.assertEqual(json.loads(resultado["result"][0]["text"]), {"error": "No existe la tarea 99"})

    def test_funcion_desconocida_no_rompe_el_bucle(self):
        simulado = GeminiSimulado(
            [llamada("c1", "hackear", {})],
            [gemini.paso_modelo("No puedo.")],
        )
        self.assertEqual(self.responder(simulado), "No puedo.")

    def test_corta_a_las_5_vueltas(self):
        simulado = GeminiSimulado(*[[llamada(f"c{n}", "listar_tareas", {})] for n in range(10)])
        with self.assertRaises(asistente.ErrorAsistente) as contexto:
            self.responder(simulado)
        self.assertEqual(contexto.exception.mensaje, textos.ERROR_DEMASIADAS_VUELTAS)
        self.assertEqual(len(simulado.recibidos), 5)
        self.assertEqual(memoria.cargar_historial(), [])

    def test_en_el_historial_solo_quedan_el_mensaje_y_el_texto_final(self):
        simulado = GeminiSimulado(
            [{"type": "thought", "signature": "x"}, llamada("c1", "agregar_nota", {"texto": "n"})],
            [gemini.paso_modelo("Guardada.")],
        )
        self.responder(simulado, "guarda una nota")
        historial = memoria.cargar_historial()
        self.assertEqual([(m["rol"], m["texto"]) for m in historial],
                         [("usuario", "guarda una nota"), ("asistente", "Guardada.")])

    def test_el_historial_previo_va_en_los_pasos_y_las_preferencias_en_la_instruccion(self):
        memoria.agregar_mensaje("usuario", "hola")
        memoria.agregar_mensaje("asistente", "¡Hola!")
        memoria.guardar_preferencia("nombre", "Ana")
        simulado = GeminiSimulado([gemini.paso_modelo("Claro")])
        self.responder(simulado, "¿me oyes?")
        recibido = simulado.recibidos[0]
        self.assertEqual([p["type"] for p in recibido["pasos"]],
                         ["user_input", "model_output", "user_input"])
        self.assertIn("- nombre: Ana", recibido["instruccion"])

    def test_texto_antes_y_despues_de_la_llamada(self):
        simulado = GeminiSimulado(
            [gemini.paso_modelo("Voy a apuntarla."), llamada("c1", "agregar_tarea", {"texto": "x"})],
            [gemini.paso_modelo("Listo.")],
        )
        self.assertEqual(self.responder(simulado), "Voy a apuntarla.\n\nListo.")

    def test_si_gemini_falla_no_se_guarda_el_historial(self):
        simulado = GeminiSimulado(gemini.ErrorGemini("limite"))
        with self.assertRaises(gemini.ErrorGemini):
            self.responder(simulado)
        self.assertEqual(memoria.cargar_historial(), [])

    def test_fallo_en_la_segunda_vuelta(self):
        simulado = GeminiSimulado(
            [llamada("c1", "agregar_tarea", {"texto": "x"})],
            gemini.ErrorGemini("red"),
        )
        with self.assertRaises(gemini.ErrorGemini):
            self.responder(simulado)
        self.assertEqual(memoria.cargar_historial(), [])

    def test_sin_texto_ni_llamadas_es_error_de_formato(self):
        simulado = GeminiSimulado([{"type": "thought"}])
        with self.assertRaises(gemini.ErrorGemini) as contexto:
            self.responder(simulado)
        self.assertEqual(contexto.exception.codigo, "formato")


if __name__ == "__main__":
    unittest.main()
