"""Pruebas de internet.py y de las herramientas de busqueda. No usan red: requests.get esta simulado."""

import unittest
from unittest import mock

import ayuda  # noqa: F401  (prepara el path)

import herramientas
import internet
import requests
import textos

RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Google News</title>
<item><title>Ecuador sube su meta - Diario Uno</title><pubDate>Fri, 20 Nov 2026 10:00:00 GMT</pubDate>
<source url="https://uno.example">Diario Uno</source></item>
<item><title>Segunda noticia</title><pubDate>Fri, 20 Nov 2026 09:00:00 GMT</pubDate>
<source url="https://dos.example">Diario Dos</source></item>
<item><title></title></item>
<item><title>Tercera - Diario Tres</title><source>Diario Tres</source></item>
</channel></rss>""".encode("utf-8")

WIKIPEDIA = {
    "query": {"pages": [
        {"pageid": 2, "title": "Eurocopa 1996", "index": 2, "extract": "Segunda.\n\nTexto   con espacios."},
        {"pageid": 1, "title": "Eurocopa 2024", "index": 1, "extract": "A" * 2000},
    ]}
}


def respuesta(contenido=b"", json=None, estado=200):
    falsa = mock.Mock()
    falsa.content = contenido
    falsa.status_code = estado
    falsa.json.return_value = json
    if estado >= 400:
        falsa.raise_for_status.side_effect = requests.HTTPError(str(estado))
    return falsa


class PruebaNoticias(unittest.TestCase):
    def test_titulares_con_fuente_y_sin_el_sufijo(self):
        with mock.patch("internet.requests.get", return_value=respuesta(RSS)) as pedir:
            lista = internet.noticias("Ecuador")
        self.assertEqual(lista[0], {
            "titulo": "Ecuador sube su meta", "fuente": "Diario Uno",
            "fecha": "Fri, 20 Nov 2026 10:00:00 GMT"})
        self.assertEqual([n["titulo"] for n in lista], ["Ecuador sube su meta", "Segunda noticia", "Tercera"])
        argumentos = pedir.call_args
        self.assertTrue(argumentos.args[0].endswith("/rss/search"))
        self.assertEqual(argumentos.kwargs["params"]["q"], "Ecuador")
        self.assertEqual(argumentos.kwargs["params"]["gl"], "EC")
        self.assertIn("User-Agent", argumentos.kwargs["headers"])

    def test_sin_tema_pide_las_noticias_principales(self):
        with mock.patch("internet.requests.get", return_value=respuesta(RSS)) as pedir:
            internet.noticias("")
        self.assertTrue(pedir.call_args.args[0].endswith("/rss"))
        self.assertNotIn("q", pedir.call_args.kwargs["params"])

    def test_respeta_el_maximo(self):
        with mock.patch("internet.requests.get", return_value=respuesta(RSS)):
            self.assertEqual(len(internet.noticias("x", maximo=1)), 1)

    def test_error_de_red_y_http(self):
        with mock.patch("internet.requests.get", side_effect=requests.ConnectionError()):
            with self.assertRaises(internet.ErrorInternet):
                internet.noticias("x")
        with mock.patch("internet.requests.get", return_value=respuesta(estado=503)):
            with self.assertRaises(internet.ErrorInternet):
                internet.noticias("x")

    def test_xml_invalido(self):
        with mock.patch("internet.requests.get", return_value=respuesta(b"<html>no es rss")):
            with self.assertRaises(internet.ErrorInternet):
                internet.noticias("x")


class PruebaWikipedia(unittest.TestCase):
    def test_ordena_limpia_y_recorta(self):
        with mock.patch("internet.requests.get", return_value=respuesta(json=WIKIPEDIA)):
            lista = internet.wikipedia("Eurocopa")
        self.assertEqual([a["titulo"] for a in lista], ["Eurocopa 2024", "Eurocopa 1996"])
        self.assertEqual(len(lista[0]["resumen"]), internet.LARGO_RESUMEN)
        self.assertEqual(lista[1]["resumen"], "Segunda. Texto con espacios.")
        self.assertEqual(lista[0]["url"], "https://es.wikipedia.org/wiki/Eurocopa_2024")

    def test_sin_resultados(self):
        with mock.patch("internet.requests.get", return_value=respuesta(json={"batchcomplete": True})):
            self.assertEqual(internet.wikipedia("zzzz"), [])

    def test_error_de_red_y_json_raro(self):
        with mock.patch("internet.requests.get", side_effect=requests.Timeout()):
            with self.assertRaises(internet.ErrorInternet):
                internet.wikipedia("x")
        with mock.patch("internet.requests.get", return_value=respuesta(json=["raro"])):
            with self.assertRaises(internet.ErrorInternet):
                internet.wikipedia("x")


GEOCODIFICACION = {"results": [{
    "name": "Quito", "admin1": "Pichincha", "country": "Ecuador",
    "latitude": -0.22985, "longitude": -78.52495}]}

PRONOSTICO = {
    "current": {"weather_code": 3, "temperature_2m": 14.5, "apparent_temperature": 13.0,
                "relative_humidity_2m": 80, "wind_speed_10m": 9.0, "precipitation": 0.0},
    "daily": {"time": ["2026-11-20", "2026-11-21"], "weather_code": [61, 999],
              "temperature_2m_max": [19.0, 20.0], "temperature_2m_min": [9.0, 10.0],
              "precipitation_sum": [2.5, 0.0], "precipitation_probability_max": [70, 10]},
}


class PruebaClima(unittest.TestCase):
    def test_geocodifica_y_ordena_el_pronostico(self):
        with mock.patch("internet.requests.get", side_effect=[
                respuesta(json=GEOCODIFICACION), respuesta(json=PRONOSTICO)]) as pedir:
            datos = internet.clima("Quito")
        geocodificacion, pronostico = pedir.call_args_list
        self.assertEqual(geocodificacion.kwargs["params"]["name"], "Quito")
        self.assertEqual(pronostico.kwargs["params"]["latitude"], -0.22985)
        self.assertEqual(datos["lugar"], "Quito, Pichincha, Ecuador")
        self.assertEqual(datos["ahora"]["estado"], "nublado")
        self.assertEqual(datos["ahora"]["temperatura_c"], 14.5)
        self.assertEqual(datos["proximos_dias"][0], {
            "fecha": "2026-11-20", "estado": "lluvia ligera", "min_c": 9.0, "max_c": 19.0,
            "lluvia_mm": 2.5, "prob_lluvia_pct": 70})
        self.assertEqual(datos["proximos_dias"][1]["estado"], "desconocido")
        self.assertEqual(datos["fuente"], "Open-Meteo.com")

    def test_ciudad_inexistente_devuelve_none_sin_pedir_pronostico(self):
        with mock.patch("internet.requests.get", return_value=respuesta(json={"generationtime_ms": 1})) as pedir:
            self.assertIsNone(internet.clima("zzzzzz"))
        self.assertEqual(pedir.call_count, 1)

    def test_errores(self):
        with mock.patch("internet.requests.get", side_effect=requests.Timeout()):
            with self.assertRaises(internet.ErrorInternet):
                internet.clima("Quito")
        with mock.patch("internet.requests.get", side_effect=[
                respuesta(json=GEOCODIFICACION), respuesta(json={"current": {}})]):
            with self.assertRaises(internet.ErrorInternet):
                internet.clima("Quito")


TAVILY = {"results": [
    {"title": " Precio de la gasolina ", "url": "https://uno.example/gasolina", "content": "Extra  cuesta\n3 dólares. " + "x" * 2000},
    {"title": "", "url": "https://dos.example", "content": None},
]}


class PruebaBuscarWeb(unittest.TestCase):
    def test_envia_la_clave_en_la_cabecera_y_ordena_los_resultados(self):
        with mock.patch("internet.requests.post", return_value=respuesta(json=TAVILY)) as enviar:
            lista = internet.buscar_web("gasolina Ecuador", "tvly-secreta")
        argumentos = enviar.call_args
        self.assertEqual(argumentos.args[0], "https://api.tavily.com/search")
        self.assertEqual(argumentos.kwargs["headers"]["Authorization"], "Bearer tvly-secreta")
        self.assertEqual(argumentos.kwargs["json"]["query"], "gasolina Ecuador")
        self.assertEqual(argumentos.kwargs["json"]["search_depth"], "basic")
        self.assertNotIn("tvly-secreta", str(argumentos.kwargs["json"]))
        self.assertEqual(lista[0]["titulo"], "Precio de la gasolina")
        self.assertEqual(lista[0]["url"], "https://uno.example/gasolina")
        self.assertTrue(lista[0]["resumen"].startswith("Extra cuesta 3 dólares."))
        self.assertEqual(len(lista[0]["resumen"]), internet.LARGO_RESUMEN)
        self.assertEqual(lista[1], {"titulo": "", "url": "https://dos.example", "resumen": ""})

    def test_codigos_de_error(self):
        casos = {401: "clave", 429: "limite", 432: "limite", 433: "limite", 500: None}
        for estado, codigo in casos.items():
            with mock.patch("internet.requests.post", return_value=respuesta(estado=estado)):
                with self.assertRaises(internet.ErrorInternet) as contexto:
                    internet.buscar_web("x", "tvly-secreta")
            self.assertEqual(contexto.exception.codigo, codigo, estado)

    def test_red_y_formato(self):
        with mock.patch("internet.requests.post", side_effect=requests.Timeout()):
            with self.assertRaises(internet.ErrorInternet):
                internet.buscar_web("x", "tvly-secreta")
        with mock.patch("internet.requests.post", return_value=respuesta(json={"results": [{"title": "sin url"}]})):
            with self.assertRaises(internet.ErrorInternet):
                internet.buscar_web("x", "tvly-secreta")

    def test_la_clave_no_aparece_en_el_registro(self):
        with mock.patch("internet.requests.post", return_value=respuesta(estado=401)):
            with self.assertLogs("internet", level="WARNING") as registro:
                with self.assertRaises(internet.ErrorInternet):
                    internet.buscar_web("x", "tvly-secreta")
        self.assertNotIn("tvly-secreta", "\n".join(registro.output))


class PruebaHerramientaBuscarWeb(unittest.TestCase):
    def test_sin_clave_devuelve_error_y_no_llama(self):
        with mock.patch("herramientas.configuracion.TAVILY_API_KEY", ""), \
                mock.patch("herramientas.internet.buscar_web") as buscar:
            self.assertEqual(herramientas.ejecutar("buscar_web", {"consulta": "x"}),
                             {"error": textos.HERRAMIENTA_BUSQUEDA_SIN_CLAVE})
        buscar.assert_not_called()

    def test_con_clave(self):
        with mock.patch("herramientas.configuracion.TAVILY_API_KEY", "tvly-falsa"), \
                mock.patch("herramientas.internet.buscar_web", return_value=[{"titulo": "t"}]) as buscar:
            resultado = herramientas.ejecutar("buscar_web", {"consulta": "  gasolina  "})
        self.assertEqual(resultado, {"resultados": [{"titulo": "t"}]})
        buscar.assert_called_once_with("gasolina", "tvly-falsa")

    def test_mensajes_de_error(self):
        esperados = {
            "clave": textos.ERRORES_INTERNET["clave"],
            "limite": textos.ERRORES_INTERNET["limite"],
            None: textos.HERRAMIENTA_SIN_INTERNET,
        }
        for codigo, mensaje in esperados.items():
            with mock.patch("herramientas.configuracion.TAVILY_API_KEY", "tvly-falsa"), \
                    mock.patch("herramientas.internet.buscar_web", side_effect=internet.ErrorInternet(codigo)):
                self.assertEqual(herramientas.ejecutar("buscar_web", {"consulta": "x"}), {"error": mensaje})

    def test_validaciones(self):
        with mock.patch("herramientas.configuracion.TAVILY_API_KEY", "tvly-falsa"):
            self.assertEqual(herramientas.ejecutar("buscar_web", {"consulta": "  "}),
                             {"error": textos.HERRAMIENTA_TEXTO_VACIO})
            largo = "a" * (herramientas.LARGO_BUSQUEDA + 1)
            self.assertIn("error", herramientas.ejecutar("buscar_web", {"consulta": largo}))


class PruebaHerramientasDeInternet(unittest.TestCase):
    def test_clima(self):
        with mock.patch("herramientas.internet.clima", return_value={"lugar": "Quito"}) as consultar:
            self.assertEqual(herramientas.ejecutar("consultar_clima", {"ciudad": " Quito "}), {"lugar": "Quito"})
        consultar.assert_called_once_with("Quito")
        with mock.patch("herramientas.internet.clima", return_value=None):
            self.assertEqual(herramientas.ejecutar("consultar_clima", {"ciudad": "x"}),
                             {"error": textos.HERRAMIENTA_CIUDAD_NO_ENCONTRADA})
        with mock.patch("herramientas.internet.clima", side_effect=internet.ErrorInternet()):
            self.assertEqual(herramientas.ejecutar("consultar_clima", {"ciudad": "x"}),
                             {"error": textos.HERRAMIENTA_SIN_INTERNET})
        self.assertEqual(herramientas.ejecutar("consultar_clima", {"ciudad": "  "}),
                         {"error": textos.HERRAMIENTA_TEXTO_VACIO})
        self.assertIn("error", herramientas.ejecutar("consultar_clima", {}))

    def test_noticias_ok_y_tema_opcional(self):
        with mock.patch("herramientas.internet.noticias", return_value=[{"titulo": "t"}]) as buscar:
            self.assertEqual(herramientas.ejecutar("buscar_noticias", {}), {"noticias": [{"titulo": "t"}]})
            buscar.assert_called_once_with("")
            herramientas.ejecutar("buscar_noticias", {"tema": "  Ecuador  "})
            buscar.assert_called_with("Ecuador")

    def test_wikipedia_ok(self):
        with mock.patch("herramientas.internet.wikipedia", return_value=[{"titulo": "t"}]) as buscar:
            resultado = herramientas.ejecutar("buscar_wikipedia", {"consulta": " Quito "})
        self.assertEqual(resultado, {"articulos": [{"titulo": "t"}]})
        buscar.assert_called_once_with("Quito")

    def test_errores_amigables(self):
        fallo = internet.ErrorInternet()
        with mock.patch("herramientas.internet.noticias", side_effect=fallo):
            self.assertEqual(herramientas.ejecutar("buscar_noticias", {"tema": "x"}),
                             {"error": textos.HERRAMIENTA_SIN_INTERNET})
        with mock.patch("herramientas.internet.wikipedia", side_effect=fallo):
            self.assertEqual(herramientas.ejecutar("buscar_wikipedia", {"consulta": "x"}),
                             {"error": textos.HERRAMIENTA_SIN_INTERNET})

    def test_validaciones(self):
        largo = "a" * (herramientas.LARGO_BUSQUEDA + 1)
        self.assertIn("error", herramientas.ejecutar("buscar_noticias", {"tema": largo}))
        self.assertIn("error", herramientas.ejecutar("buscar_wikipedia", {"consulta": largo}))
        self.assertEqual(herramientas.ejecutar("buscar_wikipedia", {"consulta": "   "}),
                         {"error": textos.HERRAMIENTA_TEXTO_VACIO})
        self.assertIn("error", herramientas.ejecutar("buscar_wikipedia", {}))


if __name__ == "__main__":
    unittest.main()
