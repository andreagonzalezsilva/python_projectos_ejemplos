import unittest
from unittest import mock

import requests

import ayuda

import gemini
import textos


class RespuestaFalsa:
    """Imita lo minimo de requests.Response."""

    def __init__(self, estado=200, datos=None, error_json=False):
        self.status_code = estado
        self._datos = datos
        self._error_json = error_json

    def json(self):
        if self._error_json:
            raise ValueError("no es json")
        return self._datos


def respuesta_con_texto(texto):
    return RespuestaFalsa(200, {
        "status": "completed",
        "steps": [{"type": "model_output", "content": [{"type": "text", "text": texto}]}],
    })


class PruebaLlamada(ayuda.PruebaConDatos):
    def llamar(self, respuesta, **argumentos):
        with mock.patch("gemini.requests.post", return_value=respuesta) as falso:
            resultado = gemini.llamar_api([gemini.paso_usuario("hola")], **argumentos)
        return resultado, falso

    def test_url_cabeceras_y_cuerpo(self):
        _, falso = self.llamar(respuesta_con_texto("Hola"), instruccion_sistema="Eres un bot")
        argumentos, opciones = falso.call_args
        self.assertEqual(argumentos[0], "https://generativelanguage.googleapis.com/v1beta/interactions")
        cabeceras = opciones["headers"]
        self.assertEqual(cabeceras["x-goog-api-key"], ayuda.CLAVE_FALSA)
        self.assertEqual(cabeceras["Api-Revision"], "2026-05-20")
        self.assertEqual(cabeceras["Content-Type"], "application/json")
        cuerpo = opciones["json"]
        self.assertEqual(cuerpo["model"], "modelo-falso")
        self.assertIs(cuerpo["store"], False)
        self.assertEqual(cuerpo["system_instruction"], "Eres un bot")
        self.assertEqual(cuerpo["input"], [
            {"type": "user_input", "content": [{"type": "text", "text": "hola"}]}])
        self.assertNotIn("tools", cuerpo)
        for prohibido in ("temperature", "top_p", "top_k", "generation_config"):
            self.assertNotIn(prohibido, cuerpo)
        self.assertEqual(opciones["timeout"], 30)

    def test_clave_solo_va_en_la_cabecera(self):
        _, falso = self.llamar(respuesta_con_texto("Hola"))
        self.assertNotIn(ayuda.CLAVE_FALSA, str(falso.call_args[0]))
        self.assertNotIn(ayuda.CLAVE_FALSA, str(falso.call_args[1]["json"]))

    def test_herramientas_se_envian(self):
        herramientas = [{"type": "function", "name": "f", "description": "d", "parameters": {}}]
        _, falso = self.llamar(respuesta_con_texto("Hola"), herramientas=herramientas)
        self.assertEqual(falso.call_args[1]["json"]["tools"], herramientas)

    def test_extraccion_de_texto(self):
        pasos, _ = self.llamar(respuesta_con_texto("¡Hola, Ana!"))
        self.assertEqual(gemini.extraer_texto(pasos), "¡Hola, Ana!")

    def test_extraer_texto_ignora_lo_anterior_al_ultimo_usuario(self):
        pasos = [
            gemini.paso_usuario("a"), gemini.paso_modelo("vieja"),
            gemini.paso_usuario("b"),
            {"type": "thought", "signature": "xyz"},
            gemini.paso_modelo("nueva"),
        ]
        self.assertEqual(gemini.extraer_texto(pasos), "nueva")

    def test_extraer_llamadas(self):
        pasos = [{"type": "thought"},
                 {"type": "function_call", "id": "1", "name": "f", "arguments": {}}]
        self.assertEqual(len(gemini.extraer_llamadas(pasos)), 1)

    def test_paso_resultado(self):
        self.assertEqual(gemini.paso_resultado("f", "9", '{"a": 1}'), {
            "type": "function_result", "name": "f", "call_id": "9",
            "result": [{"type": "text", "text": '{"a": 1}'}]})


class PruebaErrores(ayuda.PruebaConDatos):
    def codigo(self, respuesta=None, excepcion=None):
        with mock.patch("gemini.requests.post", return_value=respuesta, side_effect=excepcion):
            with self.assertRaises(gemini.ErrorGemini) as contexto:
                gemini.llamar_api([gemini.paso_usuario("hola")])
        return contexto.exception

    def prueba_http(self, estado, codigo, datos=None):
        error = self.codigo(RespuestaFalsa(estado, datos or {"error": {"message": "x"}}))
        self.assertEqual(error.codigo, codigo)
        self.assertEqual(error.mensaje, textos.ERRORES_GEMINI[codigo])

    def test_429_limite(self):
        self.prueba_http(429, "limite")

    def test_401_y_403_clave(self):
        self.prueba_http(401, "clave")
        self.prueba_http(403, "clave")

    def test_400_con_clave_invalida(self):
        self.prueba_http(400, "clave", {"error": {"message": "API key not valid. Please pass a valid API key."}})

    def test_400_clave_invalida_con_el_formato_real_de_google(self):
        # Respuesta real (recortada) de Google: el error viene dentro de una LISTA
        real = [{"error": {
            "code": 400,
            "message": "API key not valid. Please pass a valid API key.",
            "status": "INVALID_ARGUMENT",
            "details": [{"@type": "type.googleapis.com/google.rpc.ErrorInfo",
                         "reason": "API_KEY_INVALID", "domain": "googleapis.com"}]}}]
        self.prueba_http(400, "clave", real)

    def test_400_solo_con_el_motivo_api_key_invalid(self):
        self.prueba_http(400, "clave", [{"error": {"message": "x", "details": [{"reason": "API_KEY_INVALID"}]}}])

    def test_400_otro_motivo_es_formato(self):
        self.prueba_http(400, "formato", {"error": {"message": "campo desconocido"}})

    def test_404_modelo(self):
        self.prueba_http(404, "modelo")

    def test_5xx_servidor(self):
        self.prueba_http(500, "servidor")
        self.prueba_http(503, "servidor")

    def test_timeout_red(self):
        self.assertEqual(self.codigo(excepcion=requests.Timeout()).codigo, "red")

    def test_error_de_conexion_red(self):
        self.assertEqual(self.codigo(excepcion=requests.ConnectionError()).codigo, "red")

    def test_error_de_proxy_pythonanywhere_red(self):
        error = requests.exceptions.ProxyError("Tunnel connection failed: 403 Forbidden")
        self.assertEqual(self.codigo(excepcion=error).codigo, "red")

    def test_respuesta_que_no_es_json(self):
        self.assertEqual(self.codigo(RespuestaFalsa(200, error_json=True)).codigo, "formato")

    def test_respuesta_sin_steps(self):
        self.assertEqual(self.codigo(RespuestaFalsa(200, {"status": "completed"})).codigo, "formato")

    def test_estado_failed(self):
        self.assertEqual(
            self.codigo(RespuestaFalsa(200, {"status": "failed", "steps": []})).codigo, "formato")

    def test_el_mensaje_nunca_trae_la_clave_ni_el_cuerpo(self):
        cuerpo = {"error": {"message": "secreto " + ayuda.CLAVE_FALSA}}
        error = self.codigo(RespuestaFalsa(500, cuerpo))
        self.assertNotIn(ayuda.CLAVE_FALSA, error.mensaje)
        self.assertNotIn("secreto", error.mensaje)

    def test_el_registro_no_guarda_la_clave(self):
        cuerpo = {"error": {"message": "mala " + ayuda.CLAVE_FALSA}}
        with self.assertLogs("gemini", level="WARNING") as registro:
            self.codigo(RespuestaFalsa(500, cuerpo))
        self.assertNotIn(ayuda.CLAVE_FALSA, "\n".join(registro.output))


if __name__ == "__main__":
    unittest.main()
