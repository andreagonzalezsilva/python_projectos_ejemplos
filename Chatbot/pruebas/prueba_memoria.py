import json
import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import ayuda

import almacen
import asistente
import gemini
import memoria
import textos


def hay_base_de_zonas():
    try:
        ZoneInfo("America/Guayaquil")
        return True
    except ZoneInfoNotFoundError:
        return False


class PruebaHistorial(ayuda.PruebaConDatos):
    def test_historial_vacio(self):
        self.assertEqual(memoria.cargar_historial(), [])

    def test_agregar_mensaje_guarda_rol_texto_y_fecha(self):
        memoria.agregar_mensaje("usuario", "hola")
        mensaje = memoria.cargar_historial()[0]
        self.assertEqual((mensaje["rol"], mensaje["texto"]), ("usuario", "hola"))
        datetime.fromisoformat(mensaje["fecha"])

    def test_recorte_a_20_y_empieza_con_usuario(self):
        for numero in range(30):
            memoria.agregar_mensaje("usuario", f"u{numero}")
            memoria.agregar_mensaje("asistente", f"a{numero}")
            historial = memoria.cargar_historial()
            self.assertLessEqual(len(historial), 20)
            self.assertEqual(historial[0]["rol"], "usuario")
        self.assertEqual(memoria.cargar_historial()[-1]["texto"], "a29")

    def test_si_el_recorte_deja_al_asistente_primero_se_quita(self):
        for numero in range(10):
            memoria.agregar_mensaje("usuario", f"u{numero}")
            memoria.agregar_mensaje("asistente", f"a{numero}")
        self.assertEqual(len(memoria.cargar_historial()), 20)
        memoria.agregar_mensaje("usuario", "nuevo")
        historial = memoria.cargar_historial()
        self.assertEqual(len(historial), 19)
        self.assertEqual((historial[0]["rol"], historial[0]["texto"]), ("usuario", "u1"))

    def test_borrar_historial_no_toca_preferencias(self):
        memoria.agregar_mensaje("usuario", "hola")
        memoria.guardar_preferencia("nombre", "Ana")
        memoria.borrar_historial()
        self.assertEqual(memoria.cargar_historial(), [])
        self.assertEqual(memoria.cargar_preferencias(), {"nombre": "Ana"})

    def test_sobrevive_a_reiniciar(self):
        memoria.agregar_mensaje("usuario", "recuérdame esto")
        memoria.guardar_preferencia("nombre", "Ana")
        # "Reiniciar" = leer de nuevo el archivo con lo que hay en disco
        with open(os.path.join(self.carpeta, "conversaciones.json"), encoding="utf-8") as archivo:
            self.assertEqual(json.load(archivo)["conversaciones"][0]["mensajes"][0]["texto"], "recuérdame esto")
        with open(os.path.join(self.carpeta, "preferencias.json"), encoding="utf-8") as archivo:
            self.assertEqual(json.load(archivo), {"nombre": "Ana"})


class PruebaConversaciones(ayuda.PruebaConDatos):
    def test_siempre_hay_una_conversacion_vacia(self):
        self.assertEqual(memoria.listar_conversaciones(),
                         [{"id": 1, "titulo": textos.TITULO_CHAT_NUEVO, "cantidad": 0}])

    def test_cada_conversacion_tiene_su_historial(self):
        segunda = memoria.crear_conversacion()["id"]
        memoria.agregar_mensaje("usuario", "en la primera")
        memoria.agregar_mensaje("usuario", "en la segunda", segunda)
        self.assertEqual([m["texto"] for m in memoria.cargar_historial()], ["en la primera"])
        self.assertEqual([m["texto"] for m in memoria.cargar_historial(segunda)], ["en la segunda"])

    def test_sin_id_se_usa_la_primera(self):
        memoria.crear_conversacion()
        memoria.agregar_mensaje("usuario", "hola")
        self.assertEqual(memoria.cargar_historial(1), memoria.cargar_historial())
        self.assertEqual(memoria.id_por_defecto(), 1)

    def test_el_titulo_sale_del_primer_mensaje_y_se_recorta(self):
        memoria.agregar_mensaje("usuario", "  Háblame\nde la   fotosíntesis de las plantas verdes  ")
        titulo = memoria.listar_conversaciones()[0]["titulo"]
        self.assertTrue(titulo.startswith("Háblame de la fotosíntesis"))
        self.assertLessEqual(len(titulo), memoria.LARGO_TITULO)
        self.assertTrue(titulo.endswith("…"))
        memoria.agregar_mensaje("usuario", "otra cosa")
        self.assertEqual(memoria.listar_conversaciones()[0]["titulo"], titulo)  # no cambia

    def test_los_ids_no_se_reutilizan(self):
        segunda = memoria.crear_conversacion()["id"]
        memoria.eliminar_conversacion(segunda)
        self.assertEqual(memoria.crear_conversacion()["id"], segunda + 1)

    def test_limite_de_conversaciones(self):
        for _ in range(memoria.MAXIMO_CONVERSACIONES - 1):
            memoria.crear_conversacion()
        with self.assertRaises(memoria.LimiteExcedido):
            memoria.crear_conversacion()
        self.assertEqual(len(memoria.listar_conversaciones()), memoria.MAXIMO_CONVERSACIONES)

    def test_eliminar_borra_solo_esa_conversacion(self):
        segunda = memoria.crear_conversacion()["id"]
        memoria.agregar_mensaje("usuario", "uno")
        memoria.agregar_mensaje("usuario", "dos", segunda)
        memoria.eliminar_conversacion(1)
        self.assertEqual([c["id"] for c in memoria.listar_conversaciones()], [segunda])
        self.assertEqual(memoria.cargar_historial()[0]["texto"], "dos")

    def test_si_se_elimina_la_ultima_queda_una_vacia(self):
        memoria.agregar_mensaje("usuario", "hola")
        memoria.eliminar_conversacion(1)
        lista = memoria.listar_conversaciones()
        self.assertEqual(len(lista), 1)
        self.assertEqual((lista[0]["titulo"], lista[0]["cantidad"]), (textos.TITULO_CHAT_NUEVO, 0))
        self.assertNotEqual(lista[0]["id"], 1)

    def test_id_inexistente(self):
        self.assertFalse(memoria.existe_conversacion(99))
        self.assertTrue(memoria.existe_conversacion(1))
        for accion in (lambda: memoria.cargar_historial(99),
                       lambda: memoria.agregar_mensaje("usuario", "x", 99),
                       lambda: memoria.borrar_historial(99),
                       lambda: memoria.eliminar_conversacion(99)):
            with self.assertRaises(memoria.ConversacionNoExiste):
                accion()

    def test_borrar_historial_vacia_una_sola_y_reinicia_su_titulo(self):
        segunda = memoria.crear_conversacion()["id"]
        memoria.agregar_mensaje("usuario", "uno")
        memoria.agregar_mensaje("usuario", "dos", segunda)
        memoria.borrar_historial(segunda)
        self.assertEqual(memoria.cargar_historial(segunda), [])
        self.assertEqual(memoria.listar_conversaciones()[1]["titulo"], textos.TITULO_CHAT_NUEVO)
        self.assertEqual(len(memoria.cargar_historial(1)), 1)

    def test_el_recorte_a_20_es_por_conversacion(self):
        segunda = memoria.crear_conversacion()["id"]
        for numero in range(15):
            memoria.agregar_mensaje("usuario", f"u{numero}")
            memoria.agregar_mensaje("asistente", f"a{numero}")
        memoria.agregar_mensaje("usuario", "solo uno", segunda)
        self.assertLessEqual(len(memoria.cargar_historial(1)), 20)
        self.assertEqual(len(memoria.cargar_historial(segunda)), 1)

    def test_las_preferencias_son_comunes(self):
        memoria.crear_conversacion()
        memoria.guardar_preferencia("nombre", "Ana")
        self.assertEqual(memoria.cargar_preferencias(), {"nombre": "Ana"})

    def test_migra_el_historial_anterior_a_la_primera_conversacion(self):
        almacen.escribir_json("historial.json", {"mensajes": [
            {"rol": "usuario", "texto": "hola de antes", "fecha": "2026-11-01T10:00:00-05:00"},
            {"rol": "asistente", "texto": "¡Hola!", "fecha": "2026-11-01T10:00:01-05:00"},
        ]})
        self.assertEqual([m["texto"] for m in memoria.cargar_historial()], ["hola de antes", "¡Hola!"])
        self.assertEqual(memoria.listar_conversaciones()[0]["titulo"], "hola de antes")
        # una vez migrado, el archivo anterior ya no se vuelve a leer
        almacen.escribir_json("historial.json", {"mensajes": []})
        self.assertEqual(len(memoria.cargar_historial()), 2)

    def test_archivo_danado_no_rompe(self):
        with open(os.path.join(self.carpeta, "conversaciones.json"), "w", encoding="utf-8") as archivo:
            archivo.write("{esto no es json")
        self.assertEqual(len(memoria.listar_conversaciones()), 1)


class PruebaPreferencias(ayuda.PruebaConDatos):
    def test_guardar_y_reemplazar(self):
        memoria.guardar_preferencia("nombre", "Ana")
        memoria.guardar_preferencia("nombre", "Luisa")
        self.assertEqual(memoria.cargar_preferencias(), {"nombre": "Luisa"})

    def test_limite_de_preferencias(self):
        for numero in range(3):
            memoria.guardar_preferencia(f"k{numero}", "v", maximo=3)
        with self.assertRaises(memoria.LimiteExcedido):
            memoria.guardar_preferencia("otra", "v", maximo=3)
        memoria.guardar_preferencia("k0", "nuevo", maximo=3)  # reemplazar si se puede
        self.assertEqual(memoria.cargar_preferencias()["k0"], "nuevo")


class PruebaInstruccion(ayuda.PruebaConDatos):
    MOMENTO = datetime(2026, 11, 19, 20, 30, tzinfo=timezone.utc)

    def test_incluye_personalidad_con_el_nombre_del_bot(self):
        with mock.patch.object(asistente.configuracion, "BOT_NAME", "Pepe"):
            instruccion = asistente.armar_instruccion(self.MOMENTO)
        self.assertIn("Eres Pepe", instruccion)
        self.assertNotIn("{nombre_bot}", instruccion)

    def test_fecha_en_la_zona_configurada(self):
        menos_cinco = timezone(timedelta(hours=-5))
        with mock.patch("asistente.ZoneInfo", return_value=menos_cinco) as zona:
            linea = asistente.linea_de_fecha(self.MOMENTO)
        zona.assert_called_once_with("America/Guayaquil")
        self.assertEqual(
            linea,
            "Fecha y hora actuales: jueves 19 de noviembre de 2026, 15:30 (America/Guayaquil).")

    @unittest.skipUnless(hay_base_de_zonas(), "este Python no trae base de zonas horarias")
    def test_fecha_con_la_base_de_zonas_real(self):
        self.assertIn("15:30 (America/Guayaquil)", asistente.linea_de_fecha(self.MOMENTO))

    def test_si_no_hay_zona_usa_la_hora_del_sistema(self):
        with mock.patch("asistente.ZoneInfo", side_effect=ZoneInfoNotFoundError("x")):
            linea = asistente.linea_de_fecha(self.MOMENTO)
        self.assertTrue(linea.startswith("Fecha y hora actuales:"))
        self.assertIn("(hora del sistema)", linea)

    def test_incluye_las_preferencias(self):
        memoria.guardar_preferencia("nombre", "Ana")
        memoria.guardar_preferencia("tono", "formal")
        instruccion = asistente.armar_instruccion(self.MOMENTO)
        self.assertIn("- nombre: Ana", instruccion)
        self.assertIn("- tono: formal", instruccion)

    def test_sin_preferencias_no_agrega_el_bloque(self):
        self.assertNotIn("preferencias guardadas", asistente.armar_instruccion(self.MOMENTO))

    def test_orden_personalidad_fecha_preferencias(self):
        memoria.guardar_preferencia("nombre", "Ana")
        instruccion = asistente.armar_instruccion(self.MOMENTO)
        self.assertLess(instruccion.index("Eres Asistente"), instruccion.index("Fecha y hora"))
        self.assertLess(instruccion.index("Fecha y hora"), instruccion.index("- nombre: Ana"))


class PruebaResponderConMemoria(ayuda.PruebaConDatos):
    def test_envia_el_historial_como_pasos_y_guarda_el_intercambio(self):
        memoria.agregar_mensaje("usuario", "hola")
        memoria.agregar_mensaje("asistente", "¡Hola!")
        enviados = []

        def falso(pasos, instruccion_sistema="", herramientas=None):
            enviados.append(list(pasos))  # copia: el asistente sigue agregando pasos a la lista
            return [gemini.paso_modelo("Claro")]

        with mock.patch("asistente.gemini.llamar_api", falso):
            texto = asistente.responder("¿me oyes?")
        self.assertEqual(texto, "Claro")
        pasos = enviados[0]
        self.assertEqual([paso["type"] for paso in pasos], ["user_input", "model_output", "user_input"])
        self.assertEqual(pasos[2]["content"][0]["text"], "¿me oyes?")
        textos_guardados = [m["texto"] for m in memoria.cargar_historial()]
        self.assertEqual(textos_guardados, ["hola", "¡Hola!", "¿me oyes?", "Claro"])

    def test_si_falla_no_se_guarda_nada(self):
        with mock.patch("asistente.gemini.llamar_api", side_effect=gemini.ErrorGemini("red")):
            with self.assertRaises(gemini.ErrorGemini):
                asistente.responder("hola")
        self.assertEqual(memoria.cargar_historial(), [])

    def test_respuesta_sin_texto_es_error_de_formato(self):
        with mock.patch("asistente.gemini.llamar_api", return_value=[{"type": "thought"}]):
            with self.assertRaises(gemini.ErrorGemini) as contexto:
                asistente.responder("hola")
        self.assertEqual(contexto.exception.codigo, "formato")
        self.assertEqual(memoria.cargar_historial(), [])


if __name__ == "__main__":
    unittest.main()
