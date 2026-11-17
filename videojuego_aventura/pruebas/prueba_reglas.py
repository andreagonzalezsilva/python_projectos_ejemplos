"""Fase 5: enemigos, pisotones, dano, vidas, puntaje, checkpoint y vida extra."""
import sys

import ayuda
from ayuda import Verificador, crear_nivel, datos_prueba, mapa_vacio, poner, simular

BALDOSA = 16


def mapa_base(columnas=60):
    mapa = mapa_vacio(columnas)
    poner(mapa, 9, 0, "#" * columnas)
    poner(mapa, 10, 0, "#" * columnas)
    poner(mapa, 8, 3, "P")
    poner(mapa, 8, columnas - 3, "F")
    return mapa


def nivel_con(region, col_enemigo=15, **extra):
    mapa = mapa_base()
    poner(mapa, 8, col_enemigo, "E")
    return crear_nivel(datos_prueba(mapa, region, **extra))


def caer_sobre(nivel, enemigo):
    j = nivel.jugador
    j.x = enemigo.x + (enemigo.w - j.w) / 2
    j.y = enemigo.y - j.h - 6
    j.vy = 120
    j.en_suelo = False


def tocar_de_lado(nivel, enemigo):
    j = nivel.jugador
    j.x = enemigo.x - j.w + 3
    j.y = enemigo.y + enemigo.h - j.h
    j.vy = 0
    j.vx = 0


def main():
    v = Verificador("Fase 5 - enemigos, vidas y puntaje")

    # ---- pisar suma 100 y rebota
    nivel = nivel_con("costa")
    simular(nivel, [(0.2, "")])
    e = nivel.enemigos[0]
    antes = nivel.sesion.puntaje
    caer_sobre(nivel, e)
    simular(nivel, [(0.06, "")])
    v.comprobar(nivel.sesion.puntaje - antes == 100, "pisar un enemigo suma 100", "(+%d)" % (nivel.sesion.puntaje - antes))
    v.comprobar(nivel.jugador.vy < 0, "el jugador rebota al pisar")
    simular(nivel, [(0.8, "")])
    v.comprobar(len(nivel.enemigos) == 0 and nivel.estado == "jugando", "el enemigo pisado desaparece")

    # ---- de lado siendo pequeno: pierde una vida
    nivel = nivel_con("costa")
    simular(nivel, [(0.2, "")])
    tocar_de_lado(nivel, nivel.enemigos[0])
    vidas = nivel.sesion.vidas
    simular(nivel, [(0.05, "")])
    v.comprobar(nivel.sesion.vidas == vidas - 1 and nivel.jugador.muriendo, "tocar de lado siendo pequeno quita una vida")

    # ---- siendo grande: vuelve a pequeno e invulnerable 2 s
    nivel = nivel_con("costa")
    simular(nivel, [(0.2, "")])
    nivel.jugador.crecer()
    nivel.jugador.t_crecer = 0
    nivel.jugador.y += 0
    simular(nivel, [(0.2, "")])
    tocar_de_lado(nivel, nivel.enemigos[0])
    simular(nivel, [(0.05, "")])
    j = nivel.jugador
    v.comprobar(not j.grande and not j.muriendo and nivel.sesion.vidas == 3, "siendo grande vuelve a pequeno sin morir")
    v.comprobar(1.8 < j.invulnerable <= 2.0, "invulnerable 2 s tras el golpe", "(%.2f s)" % j.invulnerable)
    vidas = nivel.sesion.vidas
    simular(nivel, [(0.5, "")])
    tocar_de_lado(nivel, nivel.enemigos[0]) if nivel.enemigos else None
    simular(nivel, [(0.05, "")])
    v.comprobar(nivel.sesion.vidas == vidas, "durante la invulnerabilidad no recibe dano")

    # ---- iguana: dos pisotones
    nivel = nivel_con("galapagos")
    simular(nivel, [(0.2, "")])
    iguana = nivel.enemigos[0]
    caer_sobre(nivel, iguana)
    simular(nivel, [(0.06, "")])
    v.comprobar(iguana.aturdida > 2.5 and iguana.vivo and not iguana.muriendo, "1er pisoton: la iguana queda aturdida (3 s)")
    # aturdida no daña
    simular(nivel, [(0.6, "")])
    tocar_de_lado(nivel, iguana)
    vidas = nivel.sesion.vidas
    simular(nivel, [(0.05, "")])
    v.comprobar(nivel.sesion.vidas == vidas, "una iguana aturdida no daña")
    simular(nivel, [(0.6, "")])
    caer_sobre(nivel, iguana)
    simular(nivel, [(0.06, "")])
    v.comprobar(iguana.muriendo, "2do pisoton: la iguana se elimina")
    nivel = nivel_con("galapagos")
    simular(nivel, [(0.2, "")])
    iguana = nivel.enemigos[0]
    caer_sobre(nivel, iguana)
    simular(nivel, [(0.06, "")])
    nivel.jugador.x = 60
    simular(nivel, [(3.4, "")])
    v.comprobar(iguana.aturdida == 0 and abs(iguana.vx) > 0, "la iguana se recupera despues de 3 s")

    # ---- comportamientos
    mapa = mapa_base()
    poner(mapa, 9, 20, "   ")           # borde: plataforma corta
    poner(mapa, 10, 20, "   ")
    poner(mapa, 7, 25, "###")
    poner(mapa, 8, 25, "   ")
    nivel = crear_nivel(datos_prueba(mapa_base()))
    # cangrejo en plataforma de 3 baldosas
    mapa = mapa_vacio(60)
    poner(mapa, 9, 0, "#" * 60)
    poner(mapa, 10, 0, "#" * 60)
    poner(mapa, 7, 20, "===")
    poner(mapa, 6, 21, "E")
    poner(mapa, 8, 3, "P")
    poner(mapa, 8, 57, "F")
    nivel = crear_nivel(datos_prueba(mapa))
    cangrejo = nivel.enemigos[0]
    y0 = cangrejo.y
    xs = []
    for _ in range(60 * 8):
        simular(nivel, [(1 / 60, "")])
        xs.append(cangrejo.x)
    en_plataforma = all(20 * BALDOSA - 1 <= x <= 23 * BALDOSA for x in xs)
    v.comprobar(en_plataforma and abs(cangrejo.y - y0) < 0.5, "el cangrejo da la vuelta en los bordes del suelo",
                "(x entre %.0f y %.0f)" % (min(xs), max(xs)))
    mapa = mapa_base()
    poner(mapa, 8, 20, "#")
    poner(mapa, 8, 17, "E")
    nivel = crear_nivel(datos_prueba(mapa))
    cangrejo = nivel.enemigos[0]
    cangrejo.vx = 30
    simular(nivel, [(2.0, "")])
    v.comprobar(cangrejo.vx < 0 and cangrejo.x < 20 * BALDOSA, "el cangrejo da la vuelta en las paredes")
    v.comprobar(abs(abs(cangrejo.vx) - 30) < 0.1, "velocidad del cangrejo 30 px/s")

    nivel = nivel_con("sierra", 18)
    condor = nivel.enemigos[0]
    ys, xs = [], []
    for _ in range(60 * 8):
        simular(nivel, [(1 / 60, "")])
        ys.append(condor.y)
        xs.append(condor.x)
    amplitud = (max(ys) - min(ys)) / 2
    v.comprobar(17 <= amplitud <= 21, "el condor vuela en onda de ~20 px", "(amplitud %.1f)" % amplitud)
    v.comprobar(max(xs) - min(xs) > 60, "el condor va a la izquierda y vuelve", "(recorre %.0f px)" % (max(xs) - min(xs)))

    nivel = nivel_con("amazonia", 12)
    mono = nivel.enemigos[0]
    saltos = 0
    previo = True
    for _ in range(60 * 5):
        simular(nivel, [(1 / 60, "")])
        nivel.jugador.invulnerable = 5
        if mono.vy < -200 and previo:
            saltos += 1
        previo = mono.vy >= -200
    v.comprobar(saltos >= 2, "el mono salta cerca del jugador", "(%d saltos en 5 s)" % saltos)
    nivel = nivel_con("amazonia", 40)
    mono = nivel.enemigos[0]
    nivel.camara.x = 100
    simular(nivel, [(0.1, "")])
    nivel.enemigos[0].activo = True
    vy_min = 0
    for _ in range(60 * 3):
        simular(nivel, [(1 / 60, "")])
        vy_min = min(vy_min, mono.vy)
    v.comprobar(vy_min > -50, "el mono no salta si el jugador esta lejos")

    # ---- reaparecer en el ultimo checkpoint
    mapa = mapa_base(80)
    poner(mapa, 8, 15, "K")
    poner(mapa, 8, 30, "K")
    nivel = crear_nivel(datos_prueba(mapa))
    simular(nivel, [(0.3, ""), (4.0, "derecha correr")], lambda n, c: n.jugador.x > 33 * BALDOSA)
    v.comprobar(sum(cp.activo for cp in nivel.checkpoints) == 2, "se activaron los 2 checkpoints")
    nivel.matar_jugador()
    simular(nivel, [(2.3, "")])
    j = nivel.jugador
    v.comprobar(not j.muriendo and nivel.estado == "jugando" and abs(j.x - (30 * BALDOSA + 2)) < 1,
                "reaparece en el ultimo checkpoint", "(x=%.0f, esperado %d)" % (j.x, 30 * BALDOSA + 2))
    v.comprobar(nivel.sesion.vidas == 2, "la muerte resta una vida", "(vidas=%d)" % nivel.sesion.vidas)

    # reaparece pequeno si estaba pequeno en el checkpoint
    v.comprobar(not j.grande, "reaparece pequeno si pasó el checkpoint pequeño")

    # ---- sin vidas: game over
    nivel = crear_nivel(datos_prueba(mapa_base()))
    nivel.sesion.vidas = 1
    nivel.matar_jugador()
    simular(nivel, [(2.3, "")])
    v.comprobar(nivel.estado == "game_over" and "game_over" in nivel.eventos, "sin vidas llega el Game Over")

    # ---- caer al vacio y agua
    mapa = mapa_base()
    poner(mapa, 9, 10, "WWWW")
    poner(mapa, 10, 10, "WWWW")
    nivel = crear_nivel(datos_prueba(mapa))
    simular(nivel, [(3.0, "derecha")], lambda n, c: n.estado == "muerto")
    v.comprobar(nivel.estado == "muerto" and nivel.sesion.vidas == 2, "tocar el agua W quita una vida")

    # ---- tiempo agotado
    nivel = crear_nivel(datos_prueba(mapa_base()))
    nivel.tiempo = 0.5
    simular(nivel, [(1.0, "")])
    v.comprobar(nivel.estado == "muerto", "al acabarse el tiempo se pierde una vida")

    # ---- coleccionables: 10 puntos y vida extra a los 100
    mapa = mapa_base(70)
    poner(mapa, 8, 6, "C" * 20)
    nivel = crear_nivel(datos_prueba(mapa))
    simular(nivel, [(0.3, ""), (6.0, "derecha")], lambda n, c: n.jugador.x > 28 * BALDOSA)
    v.comprobar(nivel.sesion.puntaje == 200 and nivel.sesion.coleccionables == 20,
                "cada coleccionable suma 10 puntos", "(%d puntos)" % nivel.sesion.puntaje)
    nivel = crear_nivel(datos_prueba(mapa_base()))
    for _ in range(99):
        nivel.sumar_coleccionable()
    v.comprobar(nivel.sesion.vidas == 3 and nivel.sesion.coleccionables == 99, "99 coleccionables: aun sin vida extra")
    nivel.sumar_coleccionable()
    v.comprobar(nivel.sesion.vidas == 4 and nivel.sesion.coleccionables == 0,
                "100 coleccionables dan una vida extra y el contador se reinicia")

    return 0 if v.terminar() else 1


if __name__ == "__main__":
    sys.exit(main())
