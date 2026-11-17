"""Fase 7: los 5 niveles cargan, cumplen las reglas de diseno y se pueden completar."""
import sys

import ayuda
import pygame
from ayuda import (DT, Verificador, correr_piloto, crear_nivel, guardar_lienzo, simular)
from niveles import LISTA_NIVELES
from motor import Sesion
from nivel import validar_mapa
import interfaz

BALDOSA = 16


def huecos(mapa):
    """Largo de cada hueco: columnas seguidas sin ningun suelo ni plataforma."""
    columnas = len(mapa[0])
    libres = [not any(fila[c] in "#=" for fila in mapa) for c in range(columnas)]
    mayores, actual = [], 0
    for libre in libres + [False]:
        if libre:
            actual += 1
        elif actual:
            mayores.append(actual)
            actual = 0
    return mayores


def captura_nivel(nivel, nombre):
    """Foto del nivel con HUD, con la camara en un punto interesante."""
    def hud(lienzo):
        interfaz.hud(lienzo, nivel, nivel.jugador.personaje, nivel.jugador.accesorio)
    return guardar_lienzo(nivel, nombre, hud)


def main():
    v = Verificador("Fase 7 - los 5 niveles")
    ayuda.iniciar_pygame()

    v.comprobar(len(LISTA_NIVELES) == 5, "hay 5 niveles en LISTA_NIVELES")
    claves = [n["clave"] for n in LISTA_NIVELES]
    v.comprobar(claves == ["costa", "sierra", "amazonia", "galapagos", "cotopaxi"], "orden de niveles", str(claves))

    for datos in LISTA_NIVELES:
        clave = datos["clave"]
        mapa = datos["mapa"]
        texto = "".join(mapa)
        ancho = validar_mapa(datos)
        es_jefe = bool(datos.get("jefe"))
        v.comprobar(texto.count("P") == 1 and texto.count("F") == 1 and texto.count("K") >= 2,
                    "%s: tiene 1 P, 1 F y al menos 2 K" % clave, "(K=%d)" % texto.count("K"))
        v.comprobar(max(huecos(mapa) or [0]) <= 4, "%s: ningun hueco supera 4 baldosas" % clave,
                    "(max %d)" % max(huecos(mapa) or [0]))
        if es_jefe:
            v.comprobar(texto.count("S") == 3 and 36 <= ancho <= 44, "%s: arena de ~40 baldosas con 3 sellos" % clave,
                        "(%d columnas)" % ancho)
        else:
            v.comprobar(140 <= ancho <= 160, "%s: ~150 baldosas de largo" % clave, "(%d)" % ancho)
            v.comprobar(8 <= texto.count("E") <= 12, "%s: entre 8 y 12 enemigos" % clave, "(%d)" % texto.count("E"))
            v.comprobar(60 <= texto.count("C") <= 100, "%s: entre 60 y 100 coleccionables" % clave,
                        "(%d)" % texto.count("C"))
        comidas = sum(1 for v_ in datos["bloques_especiales"].values() if v_ == "comida")
        v.comprobar(2 <= comidas <= 3 or (es_jefe and comidas == 1), "%s: bloques ? con comida" % clave, "(%d)" % comidas)
        # los bloques especiales coinciden con un ? o B del mapa
        ok = all(mapa[f][c] in "?B" for (c, f) in datos["bloques_especiales"])
        v.comprobar(ok, "%s: bloques_especiales apuntan a un ? o B" % clave)

    # ---- completar los 4 primeros con el piloto automatico
    for indice, datos in enumerate(LISTA_NIVELES[:4]):
        sesion = Sesion()
        sesion.vidas = 99
        nivel = crear_nivel(datos, sesion=sesion)
        completo, segundos = correr_piloto(nivel, 235.0)
        muertes = 99 - sesion.vidas
        detalle = "(%.0f s, muertes=%d, x=%.0f/%d, puntos=%d)" % (segundos, muertes, nivel.jugador.x,
                                                                nivel.ancho_px, sesion.puntaje)
        v.comprobar(completo, "%s: el piloto automatico llega a la bandera" % datos["clave"], detalle)
        if not completo:
            print("      atascado cerca de la columna", int(nivel.jugador.x // BALDOSA))

    # ---- capturas de cada nivel (jugador en un punto con paisaje y objetos)
    for indice, datos in enumerate(LISTA_NIVELES):
        sesion = Sesion()
        sesion.vidas = 99
        sesion.puntaje = 1250
        sesion.coleccionables = 23
        nivel = crear_nivel(datos, sesion=sesion)
        objetivo = {"costa": 12, "sierra": 14, "amazonia": 12, "galapagos": 10, "cotopaxi": 6}[datos["clave"]]
        simular(nivel, [(0.3, "")])
        if datos["clave"] != "cotopaxi":
            simular(nivel, [(10.0, "derecha")], lambda n, c: n.jugador.x > objetivo * BALDOSA)
        nivel.camara.centrar(nivel.jugador)
        ruta = captura_nivel(nivel, "nivel_%s.png" % datos["clave"])

    return 0 if v.terminar() else 1


if __name__ == "__main__":
    sys.exit(main())
