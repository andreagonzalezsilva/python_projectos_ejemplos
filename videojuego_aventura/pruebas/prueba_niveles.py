"""Fase 4: cargador de niveles, validacion, bloques, comida que hace crecer, checkpoint y bandera."""
import sys

import ayuda
from ayuda import Verificador, crear_nivel, datos_prueba, mapa_vacio, poner, simular
from nivel import ErrorNivel, cargar_nivel
from objetos import Comida

BALDOSA = 16


def mapa_base(columnas=80):
    mapa = mapa_vacio(columnas)
    poner(mapa, 9, 0, "#" * columnas)
    poner(mapa, 10, 0, "#" * columnas)
    poner(mapa, 8, 4, "P")
    poner(mapa, 8, columnas - 4, "F")
    return mapa


def ir_a(nivel, x_centro, tolerancia=3, maximo=6.0):
    """Camina hacia x_centro (px) y se detiene. Usa un guion corto repetido."""
    tiempo = 0.0
    while tiempo < maximo:
        j = nivel.jugador
        centro = j.x + j.w / 2
        if abs(centro - x_centro) <= tolerancia and abs(j.vx) < 20:
            return
        if abs(centro - x_centro) <= tolerancia:
            accion = ""
        else:
            accion = "derecha" if centro < x_centro else "izquierda"
        simular(nivel, [(1 / 60, accion)])
        tiempo += 1 / 60


def main():
    v = Verificador("Fase 4 - niveles, bloques, comida, meta")

    # ---- validacion de filas
    mapa = mapa_base()
    mapa[4] = mapa[4][:-3]
    try:
        cargar_nivel(datos_prueba(mapa), None, None, "lorena", "poncho")
        v.comprobar(False, "una fila con largo incorrecto lanza error")
    except ErrorNivel as error:
        mensaje = str(error)
        v.comprobar("fila 5" in mensaje, "el error indica el numero de fila", "-> " + mensaje)
    mapa = mapa_base()
    poner(mapa, 3, 10, "x")
    try:
        cargar_nivel(datos_prueba(mapa), None, None, "lorena", "poncho")
        v.comprobar(False, "un simbolo desconocido lanza error")
    except ErrorNivel as error:
        v.comprobar("fila 4" in str(error), "simbolo desconocido: error con fila", "-> " + str(error))

    # ---- bloque ? con comida, crecer y romper ladrillo
    mapa = mapa_base()
    poner(mapa, 5, 10, "?B")
    poner(mapa, 5, 20, "B")
    poner(mapa, 5, 30, "B")
    datos = datos_prueba(mapa, bloques_especiales={(10, 5): "comida"})
    nivel = crear_nivel(datos)
    simular(nivel, [(0.3, "")])
    j = nivel.jugador
    v.comprobar(not j.grande and (j.w, j.h) == (12, 16), "empieza pequeno (hitbox 12x16)")

    ir_a(nivel, 10 * BALDOSA + 8)
    simular(nivel, [(0.5, "salto"), (0.8, "")])
    bloque = nivel.bloques[(10, 5)]
    v.comprobar(bloque.usado and len(nivel.comidas) == 1, "golpear ? desde abajo suelta la comida")

    # el jugador persigue la comida
    for _ in range(600):
        if not nivel.comidas:
            break
        comida = nivel.comidas[0]
        accion = "derecha" if comida.x > j.x else "izquierda"
        simular(nivel, [(1 / 60, accion)])
        if j.t_crecer > 0:
            break
    v.comprobar(j.grande and (j.w, j.h) == (12, 30), "comer la comida lo hace grande (hitbox 12x30)")
    imagen = ayuda.sprites.personaje("lorena", "poncho", True, "quieto", 0, True)
    v.comprobar(imagen.get_size() == (16, 32), "el sprite grande mide 16x32", str(imagen.get_size()))
    nivel.jugador.t_crecer = 0
    puntos_antes = nivel.sesion.puntaje

    ir_a(nivel, 20 * BALDOSA + 8)
    simular(nivel, [(0.5, "salto"), (0.8, "")])
    v.comprobar(nivel.bloques[(20, 5)].roto and nivel.rejilla[5][20] == " ",
                "estando grande rompe un ladrillo B")

    # pequeno no rompe
    nivel2 = crear_nivel(datos_prueba(mapa))
    simular(nivel2, [(0.3, "")])
    ir_a(nivel2, 20 * BALDOSA + 8)
    simular(nivel2, [(0.5, "salto"), (0.8, "")])
    v.comprobar(not nivel2.bloques[(20, 5)].roto, "estando pequeno el ladrillo solo rebota")

    # comida cuando ya eres grande: 1000 puntos
    nivel.comidas.append(Comida("bolon", 22, 8))
    puntos_antes = nivel.sesion.puntaje
    nivel.comidas[0].saliendo = False
    nivel.comidas[0].x, nivel.comidas[0].y = nivel.jugador.x, nivel.jugador.y + 10
    simular(nivel, [(0.1, "")])
    v.comprobar(nivel.sesion.puntaje - puntos_antes == 1000, "comida estando grande da 1000 puntos",
                "(+%d)" % (nivel.sesion.puntaje - puntos_antes))

    # ---- checkpoint y bandera con bono
    mapa = mapa_base(60)
    poner(mapa, 8, 20, "K")
    poner(mapa, 8, 40, "K")
    nivel = crear_nivel(datos_prueba(mapa))
    simular(nivel, [(0.3, ""), (3.0, "derecha correr")])
    activos = sum(1 for cp in nivel.checkpoints if cp.activo)
    v.comprobar(activos >= 1, "al pasar un checkpoint se activa", "(%d activos)" % activos)

    nivel = crear_nivel(datos_prueba(mapa_base(60)))
    simular(nivel, [(0.3, "")])
    nivel.tiempo = 100.0
    simular(nivel, [(10.0, "derecha correr")], lambda n, c: n.estado == "completo")
    v.comprobar(nivel.estado == "completo" and "nivel_completo" in nivel.eventos,
                "tocar la bandera termina el nivel")
    v.comprobar(nivel.bono() == int(nivel.tiempo) * 10 and 0 < nivel.bono() < 1000, "el bono por tiempo es segundos x 10", "(%d con %.1f s)" % (nivel.bono(), nivel.tiempo))
    ayuda.guardar_lienzo(nivel, "fase4_meta.png")

    return 0 if v.terminar() else 1


if __name__ == "__main__":
    sys.exit(main())
