"""Chat por terminal (paso previo a la web). Escribe "salir" para terminar."""

import sys

import asistente
import configuracion
import gemini
import textos


def principal():
    faltan = configuracion.faltantes()
    if faltan:
        print(textos.AVISO_FALTA_CONFIGURAR.format(lista=", ".join(faltan)))
        print(textos.AVISO_FALTA_CONFIGURAR_AYUDA)
        return 1

    print(textos.CONSOLA_BIENVENIDA.format(nombre_bot=configuracion.BOT_NAME))
    while True:
        try:
            mensaje = input(textos.CONSOLA_PROMPT).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if mensaje.lower() == "salir":
            break
        if not mensaje:
            continue
        try:
            print(f"{configuracion.BOT_NAME}: {asistente.responder(mensaje)}")
        except (gemini.ErrorGemini, asistente.ErrorAsistente) as error:
            print(f"[Error] {error.mensaje}")
    print(textos.CONSOLA_DESPEDIDA)
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(principal())
