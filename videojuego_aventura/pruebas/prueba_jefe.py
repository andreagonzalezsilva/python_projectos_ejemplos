"""Fase 7: jefe Cotopaxi (ciclo de erupcion, 3 sellos de hielo, barra de vida, bandera y victoria)."""
import sys

import ayuda
import pygame
from ayuda import DT, Verificador, crear_nivel, guardar_lienzo, simular
from motor import Sesion
from niveles import NIVEL_COTOPAXI

BALDOSA = 16


def nuevo():
    sesion = Sesion()
    sesion.vidas = 5
    nivel = crear_nivel(NIVEL_COTOPAXI, sesion=sesion)
    simular(nivel, [(0.3, "")])
    return nivel


def poner_sobre_suelo(nivel, col):
    j = nivel.jugador
    j.x = col * BALDOSA + 2
    j.y = 9 * BALDOSA - j.h
    j.vx = j.vy = 0


def alcanza(sello, desde_col, plataforma_y=None, intentos=None):
    """Busca un salto (con o sin correr) que desde una superficie toque el sello."""
    variantes = []
    for pre in (0.0, 0.1, 0.2, 0.3, 0.4, 0.6):
        for dir_ in ("derecha", "izquierda", ""):
            for correr in ("", " correr"):
                variantes.append((pre, dir_ + correr))
    for desfase in range(-30, 31, 6):
        for pre, accion in variantes:
            nivel = nuevo()
            j = nivel.jugador
            j.x = desde_col * BALDOSA + desfase
            j.y = (9 if plataforma_y is None else plataforma_y) * BALDOSA - j.h
            j.vx = j.vy = 0
            simular(nivel, [(0.1, "")])
            simular(nivel, [(pre, accion), (0.7, accion + " salto"), (0.9, accion)])
            if any(s.activo and s.x == sello.x for s in nivel.sellos):
                return True
    return False


def main():
    v = Verificador("Fase 7 - jefe Cotopaxi")
    ayuda.iniciar_pygame()

    nivel = nuevo()
    jefe = nivel.jefe
    v.comprobar(jefe is not None and len(nivel.sellos) == 3, "el nivel tiene jefe y 3 sellos de hielo")
    v.comprobar(not nivel.bandera.visible, "la bandera esta oculta al empezar")
    v.comprobar(jefe.vida == 3, "la barra de vida tiene 3 segmentos")

    # ---- ciclo: calma 1,6 s -> aviso 0,7 s -> erupcion 6 s
    nivel = nuevo()
    j = nivel.jugador
    j.invulnerable = 999
    fases = []

    def espiar(n, c):
        if not fases or fases[-1][0] != n.jefe.fase:
            fases.append((n.jefe.fase, nivel.reloj))
    simular(nivel, [(12.0, "")], espiar)
    nombres = [f[0] for f in fases]
    v.comprobar(nombres[:4] == ["calma", "aviso", "erupcion", "calma"], "ciclo calma -> aviso -> erupcion -> calma",
                str(nombres[:4]))
    t_calma = fases[1][1] if len(fases) > 1 else 0        # la calma empezo en t=0
    t_aviso = fases[2][1] - fases[1][1] if len(fases) > 2 else 0
    t_erup = fases[3][1] - fases[2][1] if len(fases) > 3 else 0
    v.comprobar(abs(t_calma - 1.6) < 0.3 and abs(t_aviso - 0.7) < 0.3 and abs(t_erup - 6.0) < 0.3,
                "duraciones 1,6 s / 0,7 s / 6 s", "(%.1f, %.1f, %.1f)" % (t_calma, t_aviso, t_erup))

    # ---- aviso: sombras y temblor; erupcion: cae ceniza que daña
    nivel = nuevo()
    simular(nivel, [(5.0, "")], lambda n, c: n.jefe.fase == "aviso")
    simular(nivel, [(0.4, "")])
    v.comprobar(nivel.jefe.fase == "aviso" and len(nivel.jefe.avisos) >= 4 and nivel.camara.temblor > 0,
                "el aviso muestra sombras en el suelo y hace temblar la pantalla")
    guardar_lienzo(nivel, "fase7_jefe_aviso.png")
    nivel.jugador.invulnerable = 0
    vidas = nivel.sesion.vidas
    simular(nivel, [(4.0, "")], lambda n, c: n.estado == "muerto")
    v.comprobar(nivel.estado == "muerto" and nivel.sesion.vidas == vidas - 1, "la ceniza daña como un enemigo",
                "(vidas %d -> %d)" % (vidas, nivel.sesion.vidas))

    # ---- los sellos se alcanzan saltando
    nivel = nuevo()
    s1, s2, s3 = sorted(nivel.sellos, key=lambda s: s.x)
    v.comprobar(alcanza(s1, 7), "el sello 1 se alcanza desde el suelo")
    v.comprobar(alcanza(s3, 25), "el sello 3 se alcanza desde el suelo")
    v.comprobar(alcanza(s2, 15, plataforma_y=7), "el sello 2 se alcanza desde la plataforma escalon")

    # ---- activar los 3 sellos
    nivel = nuevo()
    nivel.jugador.invulnerable = 999
    sellos = sorted(nivel.sellos, key=lambda s: s.x)
    duraciones = []
    for i, sello in enumerate(sellos):
        j = nivel.jugador
        j.x, j.y = sello.x, sello.y
        j.vx = j.vy = 0
        simular(nivel, [(0.05, "")])
        duraciones.append(round(nivel.jefe.duracion_erupcion, 2))
        if i < 2:
            v.comprobar(nivel.jefe.vida == 3 - (i + 1) and not nivel.jefe.derrotado,
                        "sello %d activado: la barra baja a %d" % (i + 1, 3 - (i + 1)))
    v.comprobar(duraciones[0] > 6.0 and duraciones[1] > duraciones[0], "cada sello enfurece al volcan: erupcion mas larga",
                str([6.0] + duraciones))
    jefe = nivel.jefe
    v.comprobar(jefe.derrotado and jefe.vida == 0, "con los 3 sellos el volcan se calma")
    simular(nivel, [(12.0, "")])
    v.comprobar(len(jefe.proyectiles) == 0 and nivel.camara.temblor == 0 and jefe.fase == "calma"
                or jefe.derrotado and not jefe.proyectiles, "se acaba la ceniza y el temblor")
    v.comprobar(nivel.bandera.visible, "aparece la bandera de Ecuador")
    guardar_lienzo(nivel, "fase7_jefe_derrotado.png")

    # ---- llegar a la bandera
    nivel.sesion.puntaje = 1000
    simular(nivel, [(1.0, "")])
    j = nivel.jugador
    j.x, j.y = 33 * BALDOSA, 9 * BALDOSA - j.h
    simular(nivel, [(12.0, "derecha")], lambda n, c: n.estado == "completo")
    v.comprobar(nivel.estado == "completo" and "nivel_completo" in nivel.eventos, "llegar a la bandera termina el jefe")

    # ---- colada morada: vida extra
    nivel = nuevo()
    nivel.jugador.invulnerable = 999
    vidas = nivel.sesion.vidas
    poner_sobre_suelo(nivel, 24)
    simular(nivel, [(0.5, "salto"), (0.6, "")])
    v.comprobar(len(nivel.comidas) == 1 and nivel.comidas[0].clave == "colada_morada", "el bloque ? suelta la colada morada")
    for _ in range(600):
        if not nivel.comidas:
            break
        c = nivel.comidas[0]
        simular(nivel, [(1 / 60, "derecha" if c.x > nivel.jugador.x else "izquierda")])
    v.comprobar(nivel.sesion.vidas == vidas + 1, "la colada morada da una vida extra",
                "(vidas %d -> %d)" % (vidas, nivel.sesion.vidas))

    # ---- reaparecer no reinicia los sellos
    nivel = nuevo()
    nivel.jugador.invulnerable = 999
    j = nivel.jugador
    j.x, j.y = sellos[0].x, sellos[0].y
    simular(nivel, [(0.1, "")])
    nivel.jugador.invulnerable = 0
    nivel.matar_jugador()
    simular(nivel, [(2.3, "")])
    v.comprobar(nivel.estado == "jugando" and nivel.jefe.sellos_activos == 1, "al reaparecer se conservan los sellos")

    return 0 if v.terminar() else 1


if __name__ == "__main__":
    sys.exit(main())
