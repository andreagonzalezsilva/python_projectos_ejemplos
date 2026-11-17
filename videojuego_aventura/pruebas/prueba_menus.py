"""Fase 6: menus, desplegable ES/EN, seleccion de personaje, HUD, pausa, Game Over y Victoria."""
import json
import os
import sys

import ayuda
from ayuda import CAPTURAS, Verificador

import guardado
import pygame
import textos
from motor import Motor
from escenas import Titulo, Seleccion, Juego, Pausa, GameOver, Victoria, FinNivel

RUTA_PRUEBA = os.path.join(CAPTURAS, "_puntaje_prueba.json")


def tecla(motor, tecla_pygame, repetir=1):
    for _ in range(repetir):
        motor.paso(1 / 60, [pygame.event.Event(pygame.KEYDOWN, key=tecla_pygame, mod=0, unicode="")])


def clic(motor, x_lienzo, y_lienzo):
    pos = (x_lienzo * 4 + 2, y_lienzo * 4 + 2)
    motor.paso(1 / 60, [pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1)])


def cuadros(motor, n):
    for _ in range(n):
        motor.paso(1 / 60, [])


def foto(motor, nombre):
    motor.guardar_captura(os.path.join(CAPTURAS, nombre))


def main():
    guardado.RUTA = RUTA_PRUEBA
    if os.path.exists(RUTA_PRUEBA):
        os.remove(RUTA_PRUEBA)
    v = Verificador("Fase 6 - menus, idioma e interfaz")

    # ---- traducciones completas
    es, en = set(textos.TEXTOS["es"]), set(textos.TEXTOS["en"])
    v.comprobar(es == en, "ES y EN tienen exactamente las mismas claves", str(es ^ en))

    motor = Motor()
    ayuda.iniciar_pygame()
    motor.cambiar_escena(Titulo(motor))
    cuadros(motor, 20)
    v.comprobar(textos.IDIOMA_ACTUAL == "es" and textos.t("jugar") == "Jugar", "arranca en espanol")
    foto(motor, "menu_es.png")

    # ---- desplegable con clic
    clic(motor, 300, 9)
    cuadros(motor, 2)
    v.comprobar(motor.escena.desplegable.abierto, "clic en el desplegable lo abre")
    foto(motor, "menu_desplegable.png")
    clic(motor, 280, 35)       # opcion EN
    cuadros(motor, 2)
    v.comprobar(textos.IDIOMA_ACTUAL == "en" and textos.t("jugar") == "Play", "clic en 'EN' cambia a ingles")
    v.comprobar(not motor.escena.desplegable.abierto, "el desplegable se cierra al elegir")
    foto(motor, "menu_en.png")
    v.comprobar(guardado.leer()["idioma"] == "en", "el idioma se guarda en puntaje.json")

    # ---- tecla L
    tecla(motor, pygame.K_l)
    v.comprobar(textos.IDIOMA_ACTUAL == "es", "la tecla L alterna el idioma")
    tecla(motor, pygame.K_l)
    v.comprobar(textos.IDIOMA_ACTUAL == "en", "la tecla L vuelve a alternar")

    # ---- seleccion: ingles, con L tambien cambia
    tecla(motor, pygame.K_RETURN)
    v.comprobar(isinstance(motor.escena, Seleccion), "Enter en 'Jugar' abre la seleccion")
    cuadros(motor, 10)
    foto(motor, "seleccion_en.png")
    tecla(motor, pygame.K_l)
    v.comprobar(textos.IDIOMA_ACTUAL == "es", "L funciona tambien en la seleccion")
    tecla(motor, pygame.K_RIGHT, 2)       # killari
    tecla(motor, pygame.K_DOWN, 2)        # baja a yaku y pasa a la zona de accesorios
    tecla(motor, pygame.K_RIGHT, 3)       # chullo
    cuadros(motor, 12)
    foto(motor, "seleccion.png")
    sel = motor.escena
    v.comprobar(sel.personaje == "yaku" and sel.accesorio == "chullo" and sel.zona == "accesorios", "flechas eligen personaje y accesorio",
                "(%s, %s)" % (sel.personaje, sel.accesorio))

    # ---- empezar el juego y guardar eleccion
    tecla(motor, pygame.K_RETURN)
    v.comprobar(isinstance(motor.escena, Juego), "Enter en la seleccion empieza el juego")
    datos = guardado.leer()
    v.comprobar(datos["personaje"] == "yaku" and datos["accesorio"] == "chullo",
                "se guardan personaje y accesorio", str(datos))
    cuadros(motor, 60)
    foto(motor, "cartel_nivel.png")
    motor.sesion.puntaje = 4520
    motor.sesion.coleccionables = 37
    cuadros(motor, 200)
    foto(motor, "hud.png")

    # ---- pausa
    tecla(motor, pygame.K_ESCAPE)
    v.comprobar(isinstance(motor.escena, Pausa), "Esc abre la pausa")
    cuadros(motor, 3)
    foto(motor, "pausa.png")
    tecla(motor, pygame.K_ESCAPE)
    v.comprobar(isinstance(motor.escena, Juego), "Esc otra vez continua")
    tecla(motor, pygame.K_ESCAPE)
    tecla(motor, pygame.K_DOWN)
    tecla(motor, pygame.K_RETURN)
    v.comprobar(isinstance(motor.escena, Titulo), "'Salir al menu' vuelve al titulo")

    # ---- game over y victoria
    motor.sesion.puntaje = 12340
    motor.cambiar_escena(GameOver(motor))
    cuadros(motor, 30)
    foto(motor, "game_over.png")
    v.comprobar(motor.datos["mejor_puntaje"] == 12340, "el mejor puntaje se guarda")
    motor.sesion.puntaje = 15000
    motor.cambiar_escena(Victoria(motor))
    cuadros(motor, 90)
    foto(motor, "victoria.png")
    v.comprobar(guardado.leer()["mejor_puntaje"] == 15000, "la victoria actualiza el mejor puntaje")
    tecla(motor, pygame.K_RETURN)
    v.comprobar(isinstance(motor.escena, Titulo), "Enter en Victoria vuelve al menu")
    textos.fijar_idioma("en")
    motor.cambiar_escena(Victoria(motor))
    cuadros(motor, 30)
    foto(motor, "victoria_en.png")
    pygame.quit()

    # ---- reinicio del programa: recuerda idioma y personaje
    textos.fijar_idioma("en")      # el ultimo idioma guardado fue "es"
    motor2 = Motor()
    v.comprobar(textos.IDIOMA_ACTUAL == "es", "al reiniciar recuerda el idioma", textos.IDIOMA_ACTUAL)
    motor2.cambiar_escena(Titulo(motor2))
    cuadros(motor2, 5)
    v.comprobar(motor2.datos["personaje"] == "yaku" and motor2.datos["accesorio"] == "chullo",
                "al reiniciar recuerda personaje y accesorio")
    foto(motor2, "menu_recordado.png")
    pygame.quit()

    if os.path.exists(RUTA_PRUEBA):
        os.remove(RUTA_PRUEBA)
    return 0 if v.terminar() else 1


if __name__ == "__main__":
    sys.exit(main())
