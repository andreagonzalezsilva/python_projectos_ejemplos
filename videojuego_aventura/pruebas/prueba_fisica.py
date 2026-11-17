"""Fase 3: fisica del jugador (saltos, huecos, colisiones, camara) con EntradaGuion."""
import sys

import ayuda
from ayuda import DT, Verificador, crear_nivel, datos_prueba, mapa_vacio, poner, simular

BALDOSA = 16


def nivel_plano(hueco=0, columnas=70):
    mapa = mapa_vacio(columnas)
    poner(mapa, 9, 0, "#" * columnas)
    poner(mapa, 10, 0, "#" * columnas)
    if hueco:
        poner(mapa, 9, 20, "W" * hueco)
        poner(mapa, 10, 20, "W" * hueco)
    poner(mapa, 8, 3, "P")
    poner(mapa, 8, columnas - 3, "F")
    # pared alta para probar colisiones laterales
    for fila in range(5, 9):
        poner(mapa, fila, 50, "#")
    return crear_nivel(datos_prueba(mapa))


def altura_salto(sostener):
    nivel = nivel_plano()
    simular(nivel, [(0.4, "")])
    y0 = nivel.jugador.y
    minimo = [y0]

    def registrar(n, c):
        minimo[0] = min(minimo[0], n.jugador.y)
    simular(nivel, [(sostener, "salto"), (1.0, "")], registrar)
    return (y0 - minimo[0]) / BALDOSA


def cruza_hueco(hueco, correr):
    """Prueba muchos instantes de salto antes del borde. True si en alguno cruza el hueco."""
    accion = "derecha correr" if correr else "derecha"
    borde = 20 * BALDOSA
    for tick in range(0, 120):
        nivel = nivel_plano(hueco)
        objetivo = borde - 0.5 * tick

        def cuando(n, c):
            return n.jugador.x >= objetivo
        simular(nivel, [(6.0, accion)], cuando)
        if nivel.jugador.x >= borde or nivel.estado != "jugando":
            continue
        simular(nivel, [(0.7, accion + " salto"), (1.2, accion)])
        j = nivel.jugador
        if nivel.estado == "jugando" and j.en_suelo and j.x > (20 + hueco) * BALDOSA:
            return True
    return False

def main():
    v = Verificador("Fase 3 - fisica del jugador")

    corto = altura_salto(0.05)
    largo = altura_salto(0.7)
    v.comprobar(1.0 <= corto <= 2.0, "salto corto llega a ~1,5 baldosas", "(%.2f)" % corto)
    v.comprobar(2.8 <= largo <= 3.3, "salto largo llega a ~3 baldosas", "(%.2f)" % largo)
    v.comprobar(largo > corto + 1, "el salto largo es mas alto que el corto")

    v.comprobar(cruza_hueco(4, True), "correr cruza un hueco de 4 baldosas")
    v.comprobar(cruza_hueco(5, True), "correr cruza un hueco de 5 baldosas")
    v.comprobar(not cruza_hueco(5, False), "caminar NO cruza un hueco de 5 baldosas")
    v.comprobar(not cruza_hueco(8, True), "ni corriendo se cruza un hueco de 8 baldosas")
    print("  (dato) caminando, hueco de 4 baldosas:", "se cruza" if cruza_hueco(4, False) else "no se cruza")

    # no atraviesa el suelo ni las paredes
    nivel = nivel_plano()
    simular(nivel, [(0.5, ""), (6.0, "derecha correr")])
    j = nivel.jugador
    v.comprobar(abs(j.pies - 9 * BALDOSA) < 0.01, "los pies descansan sobre el suelo", "(y=%.2f)" % j.pies)
    v.comprobar(j.x + j.w <= 50 * BALDOSA + 0.01, "no atraviesa la pared", "(x=%.1f)" % j.x)

    # velocidades
    nivel = nivel_plano()
    simular(nivel, [(1.0, "derecha")])
    v1 = nivel.jugador.vx
    nivel = nivel_plano()
    simular(nivel, [(1.0, "derecha correr")])
    v2 = nivel.jugador.vx
    v.comprobar(abs(v1 - 90) < 1 and abs(v2 - 140) < 1, "velocidades 90 y 140 px/s", "(%.0f, %.0f)" % (v1, v2))

    # coyote: saltar poco despues de salir del borde sigue funcionando
    nivel = nivel_plano(8)
    simular(nivel, [(2.0, "derecha")], lambda n, c: n.jugador.en_suelo is False and c > 5)
    alto_antes = nivel.jugador.vy
    simular(nivel, [(0.03, "derecha salto")])
    v.comprobar(nivel.jugador.vy < alto_antes, "coyote: salta justo despues de salir del borde")

    # buffer: pulsar salto un poco antes de aterrizar
    nivel = nivel_plano()
    simular(nivel, [(0.4, "")])
    vy_min = [0]

    def seguir(n, c):
        vy_min[0] = min(vy_min[0], n.jugador.vy)
    simular(nivel, [(0.05, "salto"), (0.5, ""), (0.0, "")], seguir)
    # en la caida pulsa salto 0.06 s antes de tocar suelo
    ciclos = 0
    while not nivel.jugador.en_suelo and ciclos < 400:
        simular(nivel, [(DT, "")])
        ciclos += 1
        if nivel.jugador.vy > 0 and nivel.jugador.pies > 9 * BALDOSA - 8:
            break
    simular(nivel, [(DT, "salto")])
    simular(nivel, [(0.15, "salto")])
    v.comprobar(nivel.jugador.vy < 0 or not nivel.jugador.en_suelo, "buffer: salto adelantado se ejecuta al aterrizar")

    # camara
    nivel = nivel_plano()
    simular(nivel, [(0.3, ""), (3.0, "derecha correr")])
    cam = nivel.camara.x
    v.comprobar(0 < cam <= nivel.ancho_px - 320, "la camara sigue al jugador y no sale del mapa", "(%.1f)" % cam)

    nivel = nivel_plano()
    simular(nivel, [(0.5, ""), (1.5, "derecha correr")])
    ayuda.guardar_lienzo(nivel, "fase3_fisica.png")
    print("  captura: capturas/fase3_fisica.png")
    return 0 if v.terminar() else 1


if __name__ == "__main__":
    sys.exit(main())
