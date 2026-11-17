"""Prueba de humo: arranca sin ventana y recorre menu -> seleccion -> 5 niveles -> victoria.

Uso (PowerShell, desde videojuego_aventura/):
    $env:SDL_VIDEODRIVER = "dummy"; $env:SDL_AUDIODRIVER = "dummy"
    .\\.venv\\Scripts\\python pruebas\\prueba_humo.py
    .\\.venv\\Scripts\\python pruebas\\prueba_humo.py --sin-audio     (simula un PC sin sonido)

Termina con codigo 0 si todo pasa. Guarda capturas en capturas/.
Los niveles 1 a 4 los completa un piloto automatico; el jefe, una ruta de prueba (toca los 3 sellos).
"""
import os
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "src"))
sys.path.insert(0, RAIZ)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
if "--sin-audio" in sys.argv:
    os.environ["SDL_AUDIODRIVER"] = "controlador_que_no_existe"
else:
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

import ajustes  # noqa: E402
import fondos  # noqa: E402
import guardado  # noqa: E402
import sprites  # noqa: E402
import textos  # noqa: E402
from ayuda import CAPTURAS, DT, Piloto, Verificador  # noqa: E402

RUTA_PRUEBA = os.path.join(CAPTURAS, "_puntaje_humo.json")
claves_perdidas = set()


def vigilar_textos():
    """Cada vez que se pide una clave inexistente la anota (deben ser cero)."""
    original = textos.t

    def espia(clave):
        if clave not in textos.TEXTOS[textos.IDIOMA_ACTUAL]:
            claves_perdidas.add(clave)
        return original(clave)
    textos.t = espia


def main():
    guardado.RUTA = RUTA_PRUEBA
    if os.path.exists(RUTA_PRUEBA):
        os.remove(RUTA_PRUEBA)
    v = Verificador("Prueba de humo (%s)" % ("sin audio" if "--sin-audio" in sys.argv else "con audio"))
    vigilar_textos()

    # ---- arte: debe generarse en menos de 2 segundos
    pygame.init()
    pygame.display.set_mode((1280, 720))
    inicio = time.perf_counter()
    sprites.iniciar()
    fondos.generar_todos()
    t_arte = time.perf_counter() - inicio
    v.comprobar(t_arte < 2.0, "sprites y fondos se generan en menos de 2 s", "(%.2f s)" % t_arte)
    pygame.quit()

    from escenas import FinNivel, GameOver, Juego, Seleccion, Titulo, Victoria
    from motor import Motor
    from niveles import LISTA_NIVELES

    motor = Motor()
    v.comprobar(motor.escena is None and motor.corriendo, "el motor arranca")
    v.comprobar(("SonidoNulo" in type(motor.sonido).__name__) == ("--sin-audio" in sys.argv),
                "sonido: %s" % type(motor.sonido).__name__)
    motor.cambiar_escena(Titulo(motor))
    tiempos = []

    def avanzar(n=1, eventos=None):
        for i in range(n):
            t0 = time.perf_counter()
            motor.paso(DT, eventos if (eventos and i == 0) else [])
            motor.presentar()
            tiempos.append(time.perf_counter() - t0)

    def tecla(codigo):
        avanzar(1, [pygame.event.Event(pygame.KEYDOWN, key=codigo, mod=0, unicode="")])

    # ---- menu y seleccion
    avanzar(30)
    tecla(pygame.K_RETURN)
    v.comprobar(isinstance(motor.escena, Seleccion), "Titulo -> Seleccion")
    avanzar(10)
    tecla(pygame.K_RETURN)
    v.comprobar(isinstance(motor.escena, Juego), "Seleccion -> Juego")
    motor.sesion.vidas = 99

    # ---- niveles 1 a 4 con el piloto automatico
    piloto = Piloto(motor.escena.nivel)
    motor.entrada = piloto
    for indice in range(4):
        escena = motor.escena
        v.comprobar(isinstance(escena, Juego) and escena.indice == indice, "empieza el nivel %d (%s)" % (
            indice + 1, LISTA_NIVELES[indice]["clave"]))
        region = LISTA_NIVELES[indice]["clave"]
        foto_hecha = False
        cuadros = 0
        while isinstance(motor.escena, Juego) and cuadros < 60 * 300:
            piloto.nivel = motor.escena.nivel
            avanzar(1)
            cuadros += 1
            n = motor.escena.nivel if isinstance(motor.escena, Juego) else None
            if n and not foto_hecha and n.jugador.x > 0.3 * n.ancho_px and n.estado == "jugando":
                motor.guardar_captura(os.path.join(CAPTURAS, "nivel_%s.png" % region))
                foto_hecha = True
        v.comprobar(isinstance(motor.escena, FinNivel), "nivel %d completado en %.0f s" % (indice + 1, cuadros * DT))
        avanzar(40)
        if indice == 0:
            motor.guardar_captura(os.path.join(CAPTURAS, "fin_nivel.png"))
        avanzar(60 * 6)

    # ---- nivel 5: jefe Cotopaxi (ruta de prueba)
    escena = motor.escena
    v.comprobar(isinstance(escena, Juego) and escena.nivel.jefe is not None, "empieza el jefe Cotopaxi")
    nivel = escena.nivel
    motor.entrada.limpiar()
    avanzar(60 * 3)
    # esperar la erupcion para fotografiarla
    for _ in range(60 * 12):
        avanzar(1)
        if nivel.jefe.fase == "erupcion" and nivel.jefe.t_fase > 1.0:
            break
    nivel.jugador.invulnerable = 9999
    avanzar(5)
    motor.guardar_captura(os.path.join(CAPTURAS, "nivel_cotopaxi.png"))
    for sello in sorted(nivel.sellos, key=lambda s: s.x):
        nivel.jugador.x, nivel.jugador.y = sello.x, sello.y
        nivel.jugador.vx = nivel.jugador.vy = 0
        avanzar(10)
    v.comprobar(nivel.jefe.derrotado and nivel.bandera.visible, "los 3 sellos calman al volcan y aparece la bandera")
    avanzar(120)
    nivel.jugador.x, nivel.jugador.y = 33 * 16, 9 * 16 - nivel.jugador.h
    piloto.nivel = nivel
    motor.entrada = piloto
    cuadros = 0
    while isinstance(motor.escena, Juego) and cuadros < 60 * 30:
        avanzar(1)
        cuadros += 1
    v.comprobar(isinstance(motor.escena, FinNivel), "jefe superado: llega a la bandera")
    avanzar(60 * 6)
    v.comprobar(isinstance(motor.escena, Victoria), "Fin del ultimo nivel -> Victoria")
    avanzar(60)
    motor.guardar_captura(os.path.join(CAPTURAS, "victoria.png"))
    puntaje = motor.sesion.puntaje
    v.comprobar(puntaje > 0 and guardado.leer()["mejor_puntaje"] == puntaje, "el mejor puntaje queda guardado",
                "(%d)" % puntaje)

    # ---- Game Over aparte
    motor.nueva_partida()
    motor.sesion.puntaje = 100
    motor.cambiar_escena(GameOver(motor))
    avanzar(30)
    motor.guardar_captura(os.path.join(CAPTURAS, "game_over.png"))
    tecla(pygame.K_RETURN)
    v.comprobar(isinstance(motor.escena, Titulo), "Game Over -> Titulo")

    # ---- silenciar con M
    tecla(pygame.K_m)
    tecla(pygame.K_m)
    v.comprobar(True, "la tecla M no rompe nada", "(sonido %s)" % ("sin dispositivo" if "--sin-audio" in sys.argv else "ok"))

    # ---- rendimiento y textos
    media = sum(tiempos) / len(tiempos) * 1000
    peor = sorted(tiempos)[int(len(tiempos) * 0.99)] * 1000
    v.comprobar(media < 8.0, "rendimiento: cuadro medio bajo 8 ms (60 FPS con margen)",
                "(media %.2f ms, p99 %.2f ms, %d cuadros)" % (media, peor, len(tiempos)))
    v.comprobar(not claves_perdidas, "no quedan claves de texto sin traducir", str(sorted(claves_perdidas)))

    pygame.quit()
    if os.path.exists(RUTA_PRUEBA):
        os.remove(RUTA_PRUEBA)
    return 0 if v.terminar() else 1


if __name__ == "__main__":
    sys.exit(main())
