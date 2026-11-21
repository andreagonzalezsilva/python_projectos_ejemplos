import os
import re
import unittest
from unittest import mock

import ayuda

import app as modulo_app
import asistente
import gemini
import herramientas
import memoria
import textos

URL = "https://localhost"  # HTTPS: asi la cookie "Secure" viaja en las pruebas


def llamada(id_llamada, nombre, argumentos):
    return {"type": "function_call", "id": id_llamada, "name": nombre, "arguments": argumentos}


class PruebaWeb(ayuda.PruebaConDatos):
    def setUp(self):
        super().setUp()
        modulo_app.app.config["TESTING"] = True
        self.cliente = modulo_app.app.test_client()
        self.respuestas = []
        parche_gemini = mock.patch(
            "asistente.gemini.llamar_api", side_effect=self.lanzar_o_devolver)
        self.falso_gemini = parche_gemini.start()
        self.addCleanup(parche_gemini.stop)
        parche_espera = mock.patch("app.time.sleep")
        self.falsa_espera = parche_espera.start()
        self.addCleanup(parche_espera.stop)

    def lanzar_o_devolver(self, *argumentos, **opciones):
        elemento = self.respuestas.pop(0)
        if isinstance(elemento, Exception):
            raise elemento
        return elemento

    def entrar(self):
        respuesta = self.cliente.post(
            "/login", data={"contrasena": ayuda.CONTRASENA_FALSA}, base_url=URL)
        self.assertEqual(respuesta.status_code, 302)

    def post_json(self, ruta, cuerpo):
        return self.cliente.post(ruta, json=cuerpo, base_url=URL)


class PruebaSinSesion(PruebaWeb):
    def setUp(self):
        super().setUp()
        memoria.agregar_mensaje("usuario", "mensaje secreto")
        herramientas.ejecutar("agregar_tarea", {"texto": "tarea secreta"})

    def test_la_pagina_redirige_al_login(self):
        respuesta = self.cliente.get("/", base_url=URL)
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(respuesta.headers["Location"].endswith("/login"))

    def test_las_rutas_json_devuelven_401_sin_datos(self):
        peticiones = [
            self.cliente.get("/estado", base_url=URL),
            self.post_json("/chat", {"mensaje": "hola"}),
            self.cliente.post("/borrar", base_url=URL),
            self.post_json("/chats/nuevo", {}),
            self.post_json("/chats/cerrar", {"chat": 1}),
            self.post_json("/tareas/marcar", {"id": 1, "hecha": True}),
        ]
        for respuesta in peticiones:
            self.assertEqual(respuesta.status_code, 401)
            cuerpo = respuesta.get_data(as_text=True)
            self.assertNotIn("secret", cuerpo)
            self.assertEqual(respuesta.get_json(), {"error": textos.ERROR_NO_AUTORIZADO})

    def test_sin_sesion_no_se_gasta_cuota_ni_se_borra_nada(self):
        self.post_json("/chat", {"mensaje": "hola"})
        self.cliente.post("/borrar", base_url=URL)
        self.falso_gemini.assert_not_called()
        self.assertEqual(len(memoria.cargar_historial()), 1)


class PruebaLogin(PruebaWeb):
    def test_formulario_de_login(self):
        respuesta = self.cliente.get("/login", base_url=URL)
        self.assertEqual(respuesta.status_code, 200)
        html = respuesta.get_data(as_text=True)
        self.assertIn('type="password"', html)
        self.assertIn("Entrar", html)

    def test_contrasena_incorrecta_no_entra(self):
        respuesta = self.cliente.post("/login", data={"contrasena": "mala"}, base_url=URL)
        self.assertEqual(respuesta.status_code, 401)
        self.assertIn("Contraseña incorrecta", respuesta.get_data(as_text=True))
        self.falsa_espera.assert_called_once_with(1)
        self.assertEqual(self.cliente.get("/", base_url=URL).status_code, 302)

    def test_contrasena_vacia_no_entra(self):
        respuesta = self.cliente.post("/login", data={}, base_url=URL)
        self.assertEqual(respuesta.status_code, 401)

    def test_contrasena_correcta_entra(self):
        self.entrar()
        respuesta = self.cliente.get("/", base_url=URL)
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Asistente", respuesta.get_data(as_text=True))
        self.falsa_espera.assert_not_called()

    def test_contrasena_con_tildes(self):
        with mock.patch.object(modulo_app.configuracion, "APP_PASSWORD", "contraseña-ñandú"):
            respuesta = self.cliente.post(
                "/login", data={"contrasena": "contraseña-ñandú"}, base_url=URL)
        self.assertEqual(respuesta.status_code, 302)

    def test_salir_cierra_la_sesion(self):
        self.entrar()
        respuesta = self.cliente.post("/salir", base_url=URL)
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(self.cliente.get("/", base_url=URL).status_code, 302)
        self.assertEqual(self.cliente.get("/estado", base_url=URL).status_code, 401)

    def test_salir_solo_acepta_post(self):
        self.assertEqual(self.cliente.get("/salir", base_url=URL).status_code, 405)

    def test_aviso_de_configuracion_incompleta(self):
        with mock.patch.object(modulo_app.configuracion, "GEMINI_API_KEY", "pega_aqui_tu_clave"):
            respuesta = self.cliente.get("/login", base_url=URL)
            html = respuesta.get_data(as_text=True)
            self.assertEqual(respuesta.status_code, 200)
            self.assertIn("Falta configurar: GEMINI_API_KEY", html)
            self.assertNotIn('type="password"', html)
            # y aunque se mande la contrasena correcta, no deja entrar
            self.cliente.post("/login", data={"contrasena": ayuda.CONTRASENA_FALSA}, base_url=URL)
            self.assertEqual(self.cliente.get("/", base_url=URL).status_code, 302)

    def test_cookie_segura(self):
        respuesta = self.cliente.post(
            "/login", data={"contrasena": ayuda.CONTRASENA_FALSA}, base_url=URL)
        cookie = respuesta.headers["Set-Cookie"]
        self.assertIn("HttpOnly", cookie)
        self.assertIn("Secure", cookie)
        self.assertIn("SameSite=Lax", cookie)

    def test_cabeceras_de_seguridad(self):
        respuesta = self.cliente.get("/login", base_url=URL)
        self.assertEqual(respuesta.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(respuesta.headers["X-Frame-Options"], "DENY")
        self.assertEqual(respuesta.headers["Referrer-Policy"], "same-origin")
        self.entrar()
        self.assertEqual(self.cliente.get("/estado", base_url=URL).headers["Cache-Control"], "no-store")

    def test_nunca_aparecen_la_clave_ni_la_contrasena(self):
        self.respuestas.append([gemini.paso_modelo("hola")])
        respuestas = [
            self.cliente.get("/login", base_url=URL),
            self.cliente.post("/login", data={"contrasena": "mala"}, base_url=URL),
        ]
        self.entrar()
        respuestas += [
            self.cliente.get("/", base_url=URL),
            self.cliente.get("/estado", base_url=URL),
            self.post_json("/chat", {"mensaje": "hola"}),
            self.cliente.get("/static/chat.js", base_url=URL),
        ]
        for respuesta in respuestas:
            cuerpo = respuesta.get_data(as_text=True)
            self.assertNotIn(ayuda.CLAVE_FALSA, cuerpo)
            self.assertNotIn(ayuda.CONTRASENA_FALSA, cuerpo)
            self.assertNotIn(ayuda.SECRETO_FALSO, cuerpo)
            self.assertNotIn(ayuda.CLAVE_FALSA, str(respuesta.headers))
            respuesta.close()


class PruebaChat(PruebaWeb):
    def setUp(self):
        super().setUp()
        self.entrar()

    def test_pagina_con_bienvenida_y_nombre(self):
        html = self.cliente.get("/", base_url=URL).get_data(as_text=True)
        self.assertIn("Soy Asistente", html)
        self.assertIn("Borrar conversación", html)
        self.assertIn("Salir", html)
        self.assertIn("Tareas", html)
        self.assertIn("Notas", html)
        self.assertIn("Lo que recuerdo de ti", html)

    def test_casilla_marca_y_desmarca_una_tarea(self):
        tarea = herramientas.agregar_tarea("comprar pan")["id"]
        datos = self.post_json("/tareas/marcar", {"id": tarea, "hecha": True}).get_json()
        self.assertTrue(datos["tareas"][0]["hecha"])
        self.assertTrue(herramientas.todas_las_tareas()[0]["hecha"])  # quedo guardado
        datos = self.post_json("/tareas/marcar", {"id": tarea, "hecha": False}).get_json()
        self.assertFalse(datos["tareas"][0]["hecha"])

    def test_casilla_con_datos_invalidos_o_tarea_inexistente(self):
        herramientas.agregar_tarea("comprar pan")
        invalidos = [{}, {"id": 1}, {"hecha": True}, {"id": "1", "hecha": True},
                     {"id": True, "hecha": True}, {"id": 1, "hecha": "si"}, [], None]
        for cuerpo in invalidos:
            with self.subTest(cuerpo=cuerpo):
                respuesta = self.post_json("/tareas/marcar", cuerpo)
                self.assertEqual(respuesta.status_code, 400)
                self.assertEqual(respuesta.get_json()["error"], textos.ERROR_PETICION_INVALIDA)
        respuesta = self.post_json("/tareas/marcar", {"id": 99, "hecha": True})
        self.assertEqual(respuesta.status_code, 404)
        self.assertIn("99", respuesta.get_json()["error"])
        self.assertFalse(herramientas.todas_las_tareas()[0]["hecha"])

    def test_bienvenida_muestra_el_nombre_del_usuario(self):
        sin_nombre = self.cliente.get("/", base_url=URL).get_data(as_text=True)
        self.assertIn("Bienvenido/a", sin_nombre)
        self.assertNotIn('class="intro-nombre"', sin_nombre)
        memoria.guardar_preferencia("nombre", "Ana")
        con_nombre = self.cliente.get("/", base_url=URL).get_data(as_text=True)
        self.assertIn('<p class="intro-nombre">Ana</p>', con_nombre)

    def test_nombre_del_usuario_no_inyecta_html(self):
        memoria.guardar_preferencia("nombre", "<script>alert(1)</script>")
        html = self.cliente.get("/", base_url=URL).get_data(as_text=True)
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_chat_responde_y_devuelve_el_estado(self):
        self.respuestas += [
            [llamada("c1", "agregar_tarea", {"texto": "comprar pan"}),
             llamada("c2", "guardar_preferencia", {"clave": "nombre", "valor": "Ana"}),
             llamada("c3", "agregar_nota", {"texto": "una idea"})],
            [gemini.paso_modelo("Listo, Ana.")],
        ]
        respuesta = self.post_json("/chat", {"mensaje": "apúntame comprar pan"})
        self.assertEqual(respuesta.status_code, 200)
        datos = respuesta.get_json()
        self.assertEqual(datos["respuesta"], "Listo, Ana.")
        self.assertEqual([t["texto"] for t in datos["tareas"]], ["comprar pan"])
        self.assertEqual([n["texto"] for n in datos["notas"]], ["una idea"])
        self.assertEqual(datos["preferencias"], {"nombre": "Ana"})
        self.assertEqual(respuesta.headers["Cache-Control"], "no-store")

    def test_estado(self):
        memoria.agregar_mensaje("usuario", "hola")
        memoria.agregar_mensaje("asistente", "¡Hola!")
        herramientas.ejecutar("agregar_tarea", {"texto": "a"})
        datos = self.cliente.get("/estado", base_url=URL).get_json()
        self.assertEqual(sorted(datos),
                         ["chat", "conversaciones", "mensajes", "notas", "preferencias", "tareas"])
        self.assertEqual([m["texto"] for m in datos["mensajes"]], ["hola", "¡Hola!"])
        self.assertEqual(len(datos["tareas"]), 1)
        self.assertEqual(datos["chat"], 1)
        self.assertEqual(datos["conversaciones"], [{"id": 1, "titulo": "hola", "cantidad": 2}])

    def test_borrar_no_toca_tareas_notas_ni_preferencias(self):
        memoria.agregar_mensaje("usuario", "hola")
        herramientas.ejecutar("agregar_tarea", {"texto": "a"})
        herramientas.ejecutar("agregar_nota", {"texto": "n"})
        memoria.guardar_preferencia("nombre", "Ana")
        respuesta = self.cliente.post("/borrar", base_url=URL)
        self.assertTrue(respuesta.get_json()["ok"])
        datos = self.cliente.get("/estado", base_url=URL).get_json()
        self.assertEqual(datos["mensajes"], [])
        self.assertEqual(len(datos["tareas"]), 1)
        self.assertEqual(len(datos["notas"]), 1)
        self.assertEqual(datos["preferencias"], {"nombre": "Ana"})

    def test_la_pagina_trae_las_pestanas(self):
        html = self.cliente.get("/", base_url=URL).get_data(as_text=True)
        self.assertIn('role="tablist"', html)
        self.assertIn('aria-orientation="vertical"', html)
        self.assertIn('id="boton-nuevo"', html)
        self.assertIn('id="boton-colapsar"', html)
        self.assertIn('aria-expanded="true"', html)

    def test_nuevo_chat_y_chats_independientes(self):
        nuevo = self.post_json("/chats/nuevo", {}).get_json()
        self.assertEqual(nuevo["chat"], 2)
        self.assertEqual([c["id"] for c in nuevo["conversaciones"]], [1, 2])
        self.respuestas += [[gemini.paso_modelo("A")], [gemini.paso_modelo("B")]]
        primera = self.post_json("/chat", {"mensaje": "mensaje uno", "chat": 1}).get_json()
        segunda = self.post_json("/chat", {"mensaje": "mensaje dos", "chat": 2}).get_json()
        self.assertEqual((primera["chat"], segunda["chat"]), (1, 2))
        self.assertEqual([c["titulo"] for c in segunda["conversaciones"]], ["mensaje uno", "mensaje dos"])
        uno = self.cliente.get("/estado?chat=1", base_url=URL).get_json()
        dos = self.cliente.get("/estado?chat=2", base_url=URL).get_json()
        self.assertEqual([m["texto"] for m in uno["mensajes"]], ["mensaje uno", "A"])
        self.assertEqual([m["texto"] for m in dos["mensajes"]], ["mensaje dos", "B"])
        # lo comun a todas las pestanas
        self.assertEqual(uno["tareas"], dos["tareas"])
        self.assertEqual(uno["preferencias"], dos["preferencias"])

    def test_el_chat_sin_id_va_a_la_primera_conversacion(self):
        self.respuestas.append([gemini.paso_modelo("A")])
        self.post_json("/chat", {"mensaje": "hola"})
        self.assertEqual(len(memoria.cargar_historial(1)), 2)

    def test_estado_con_chat_inexistente_cae_en_la_primera(self):
        for pedido in ("/estado?chat=99", "/estado?chat=abc", "/estado?chat=-1"):
            datos = self.cliente.get(pedido, base_url=URL).get_json()
            self.assertEqual(datos["chat"], 1, pedido)

    def test_chat_en_una_conversacion_inexistente_da_404_y_no_gasta_cuota(self):
        for chat in (99, "abc", True, 1.5, [1]):
            with self.subTest(chat=chat):
                respuesta = self.post_json("/chat", {"mensaje": "hola", "chat": chat})
                self.assertEqual(respuesta.status_code, 404)
                self.assertEqual(respuesta.get_json()["error"], textos.ERROR_CHAT_NO_EXISTE)
        self.falso_gemini.assert_not_called()
        self.assertEqual(memoria.cargar_historial(), [])

    def test_borrar_solo_la_conversacion_pedida(self):
        memoria.crear_conversacion()
        memoria.agregar_mensaje("usuario", "uno", 1)
        memoria.agregar_mensaje("usuario", "dos", 2)
        respuesta = self.post_json("/borrar", {"chat": 2})
        self.assertTrue(respuesta.get_json()["ok"])
        self.assertEqual(memoria.cargar_historial(2), [])
        self.assertEqual(len(memoria.cargar_historial(1)), 1)
        self.assertEqual(self.post_json("/borrar", {"chat": 99}).status_code, 404)

    def test_limite_de_pestanas(self):
        for _ in range(memoria.MAXIMO_CONVERSACIONES - 1):
            self.assertEqual(self.post_json("/chats/nuevo", {}).status_code, 200)
        respuesta = self.post_json("/chats/nuevo", {})
        self.assertEqual(respuesta.status_code, 409)
        datos = respuesta.get_json()
        self.assertIn(str(memoria.MAXIMO_CONVERSACIONES), datos["error"])
        self.assertEqual(len(datos["conversaciones"]), memoria.MAXIMO_CONVERSACIONES)

    def test_cerrar_una_conversacion(self):
        memoria.crear_conversacion()
        memoria.agregar_mensaje("usuario", "uno", 1)
        datos = self.post_json("/chats/cerrar", {"chat": 1}).get_json()
        self.assertEqual([c["id"] for c in datos["conversaciones"]], [2])
        self.assertEqual(self.post_json("/chats/cerrar", {"chat": 1}).status_code, 404)

    def test_cerrar_exige_un_id_valido_y_no_cierra_la_primera_por_accidente(self):
        for cuerpo in ({}, {"chat": None}, {"chat": "1"}, {"chat": True}, []):
            with self.subTest(cuerpo=cuerpo):
                self.assertEqual(self.post_json("/chats/cerrar", cuerpo).status_code, 404)
        self.assertEqual(len(memoria.listar_conversaciones()), 1)

    def test_si_cierran_la_conversacion_mientras_se_espera_la_respuesta(self):
        def cierra_y_responde(*argumentos, **opciones):
            memoria.eliminar_conversacion(2)
            return [gemini.paso_modelo("tarde")]

        memoria.crear_conversacion()
        self.falso_gemini.side_effect = cierra_y_responde
        respuesta = self.post_json("/chat", {"mensaje": "hola", "chat": 2})
        self.assertEqual(respuesta.status_code, 404)
        self.assertEqual(respuesta.get_json()["error"], textos.ERROR_CHAT_NO_EXISTE)

    def test_mensaje_con_script_se_devuelve_como_texto(self):
        malo = "<script>alert(1)</script>"
        self.respuestas.append([gemini.paso_modelo(malo)])
        datos = self.post_json("/chat", {"mensaje": malo}).get_json()
        self.assertEqual(datos["respuesta"], malo)  # JSON puro: el navegador lo muestra con textContent

    def test_chat_js_no_usa_innerhtml(self):
        ruta = os.path.join(ayuda.CARPETA_PROYECTO, "static", "chat.js")
        with open(ruta, encoding="utf-8") as archivo:
            codigo = "\n".join(
                linea for linea in archivo.read().splitlines() if not linea.strip().startswith("//"))
        for prohibido in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval("):
            self.assertNotIn(prohibido, codigo)
        self.assertIn("textContent", codigo)

    def test_mensajes_invalidos(self):
        casos = [{"mensaje": ""}, {"mensaje": "   "}, {"mensaje": 5}, {}, {"otro": "x"}, [], None]
        for cuerpo in casos:
            with self.subTest(cuerpo=cuerpo):
                respuesta = self.post_json("/chat", cuerpo)
                self.assertEqual(respuesta.status_code, 400)
                self.assertEqual(respuesta.get_json()["error"], textos.ERROR_MENSAJE_VACIO)
        sin_json = self.cliente.post("/chat", data="hola", base_url=URL)
        self.assertEqual(sin_json.status_code, 400)
        self.falso_gemini.assert_not_called()

    def test_mensaje_demasiado_largo(self):
        respuesta = self.post_json("/chat", {"mensaje": "x" * 1001})
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("demasiado largo", respuesta.get_json()["error"])
        self.falso_gemini.assert_not_called()
        self.respuestas.append([gemini.paso_modelo("ok")])
        self.assertEqual(self.post_json("/chat", {"mensaje": "x" * 1000}).status_code, 200)

    def test_errores_de_gemini_son_amigables(self):
        esperados = {"limite": 429, "clave": 502, "modelo": 502, "red": 502, "formato": 502, "servidor": 502}
        for codigo, estado in esperados.items():
            with self.subTest(codigo=codigo):
                self.respuestas.append(gemini.ErrorGemini(codigo))
                respuesta = self.post_json("/chat", {"mensaje": "hola"})
                self.assertEqual(respuesta.status_code, estado)
                self.assertEqual(respuesta.get_json()["error"], textos.ERRORES_GEMINI[codigo])
        self.assertEqual(memoria.cargar_historial(), [])

    def test_el_error_conserva_el_panel_actualizado(self):
        self.respuestas += [[llamada("c1", "agregar_tarea", {"texto": "x"})], gemini.ErrorGemini("red")]
        datos = self.post_json("/chat", {"mensaje": "hola"}).get_json()
        self.assertIn("error", datos)
        self.assertEqual(len(datos["tareas"]), 1)

    def test_demasiadas_vueltas(self):
        self.falso_gemini.side_effect = lambda *a, **k: [llamada("c", "listar_notas", {})]
        respuesta = self.post_json("/chat", {"mensaje": "hola"})
        self.assertEqual(respuesta.status_code, 502)
        self.assertEqual(respuesta.get_json()["error"], textos.ERROR_DEMASIADAS_VUELTAS)

    def test_error_inesperado_no_muestra_detalles(self):
        self.falso_gemini.side_effect = RuntimeError("detalle interno secreto")
        with self.assertLogs("app", level="ERROR"):
            respuesta = self.post_json("/chat", {"mensaje": "hola"})
        self.assertEqual(respuesta.status_code, 500)
        self.assertNotIn("secreto", respuesta.get_data(as_text=True))
        self.assertEqual(respuesta.get_json()["error"], textos.ERROR_INTERNO)


class PruebaArchivosEstaticos(unittest.TestCase):
    def test_sin_llamadas_a_sitios_externos(self):
        encontrados = []
        for carpeta in ("templates", "static"):
            for raiz, _, archivos in os.walk(os.path.join(ayuda.CARPETA_PROYECTO, carpeta)):
                for nombre in archivos:
                    with open(os.path.join(raiz, nombre), encoding="utf-8") as archivo:
                        texto = archivo.read()
                    for url in re.findall(r"https?://[^\s\"')]+", texto):
                        if "w3.org/2000/svg" not in url:
                            encontrados.append((nombre, url))
        self.assertEqual(encontrados, [])


if __name__ == "__main__":
    unittest.main()
