"""Servidor local con un Gemini SIMULADO, para ver la pagina sin gastar cuota.

Uso (desde Chatbot/):
    .venv\\Scripts\\python pruebas\\servir_simulado.py [--puerto 5000]

Usa una carpeta temporal para los datos y una clave y contrasena FALSAS.
Frases para probar:
    "Me llamo Ana"          guarda una preferencia
    "Apuntame comprar pan"  agrega una tarea
    "Anota una idea"        agrega una nota
    "Que tareas tengo?"     lista las tareas
    "Termine la tarea 1"    completa una tarea
    "limite"                simula el error 429 de Gemini
    "clave" / "modelo" / "red" / "formato" / "servidor" / "vueltas"   otros errores
    cualquier otra cosa     respuesta de texto
"""

import argparse
import json
import os
import re
import sys
import tempfile
import unicodedata

CARPETA_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CARPETA_PROYECTO)

CONTRASENA_SIMULADA = "simulado"


def sin_tildes(texto):
    descompuesto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn").lower()


def preparar_entorno(carpeta_datos):
    os.environ["DIRECTORIO_DATOS"] = carpeta_datos
    import configuracion

    configuracion.GEMINI_API_KEY = "clave-falsa-simulada"
    configuracion.APP_PASSWORD = CONTRASENA_SIMULADA
    configuracion.SECRET_KEY = "secreto-falso-simulado-0123456789abcdef"
    configuracion.GEMINI_MODEL = "modelo-simulado"


def crear_gemini_simulado():
    import gemini

    def llamada(nombre, argumentos):
        return {"type": "function_call", "id": "sim-" + nombre, "name": nombre, "arguments": argumentos}

    def decir_resultado(nombre, resultado):
        if "error" in resultado:
            return "No pude hacerlo: " + resultado["error"]
        if nombre == "listar_tareas":
            tareas = resultado["tareas"]
            if not tareas:
                return "No tienes tareas pendientes."
            return "Tus tareas pendientes:\n" + "\n".join("- " + t["texto"] for t in tareas)
        if nombre == "agregar_tarea":
            return "Listo, apunté: " + resultado["texto"]
        if nombre == "agregar_nota":
            return "Nota guardada."
        if nombre == "completar_tarea":
            return "Marqué la tarea %s como hecha." % resultado["id"]
        if nombre == "guardar_preferencia":
            return "¡Encantado, %s! Lo recordaré." % resultado["valor"]
        return "Hecho."

    def simulado(pasos, instruccion_sistema="", herramientas=None):
        ultimo = pasos[-1]
        if ultimo["type"] == "function_result":
            resultado = json.loads(ultimo["result"][0]["text"])
            return [gemini.paso_modelo(decir_resultado(ultimo["name"], resultado))]

        original = ultimo["content"][0]["text"]
        texto = sin_tildes(original)
        errores = {"limite": "limite", "clave": "clave", "modelo": "modelo", "red": "red",
                   "formato": "formato", "servidor": "servidor"}
        if texto.strip() in errores:
            raise gemini.ErrorGemini(errores[texto.strip()])
        if texto.strip() == "vueltas":
            return [llamada("listar_tareas", {})]  # nunca termina: prueba el corte a 5 vueltas
        buscado = re.search(r"me llamo (\w+)", texto)
        if buscado:
            nombre = re.search(r"me llamo (\w+)", original, re.IGNORECASE).group(1)
            return [{"type": "thought", "signature": "simulada"},
                    llamada("guardar_preferencia", {"clave": "nombre", "valor": nombre})]
        if "apunt" in texto or "agrega" in texto:
            tarea = re.sub(r"^\W*(apuntame|apunta|agrega|agregame)\s*", "", texto).strip() or "algo"
            return [llamada("agregar_tarea", {"texto": tarea})]
        if "nota" in texto or "anota" in texto:
            return [llamada("agregar_nota", {"texto": original})]
        if "tareas" in texto:
            return [llamada("listar_tareas", {})]
        numero = re.search(r"tarea (\d+)", texto)
        if numero:
            return [llamada("completar_tarea", {"id": int(numero.group(1))})]
        return [gemini.paso_modelo("Soy un Gemini simulado.\nTu mensaje fue: " + original)]

    gemini.llamar_api = simulado


def principal():
    analizador = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analizador.add_argument("--puerto", type=int, default=5000)
    argumentos = analizador.parse_args()

    carpeta_datos = tempfile.mkdtemp(prefix="chatbot_simulado_")
    preparar_entorno(carpeta_datos)
    crear_gemini_simulado()

    import app as modulo_app

    modulo_app.app.secret_key = "secreto-falso-simulado-0123456789abcdef"
    modulo_app.app.config["SESSION_COOKIE_SECURE"] = False
    print("Servidor SIMULADO en http://127.0.0.1:%d  (contraseña: %s)" % (argumentos.puerto, CONTRASENA_SIMULADA))
    print("Datos temporales en", carpeta_datos)
    modulo_app.app.run(host="127.0.0.1", port=argumentos.puerto, debug=False)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    principal()
