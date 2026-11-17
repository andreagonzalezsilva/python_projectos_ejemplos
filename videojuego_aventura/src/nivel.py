"""Nivel: carga el diccionario, valida el mapa, resuelve colisiones y aplica las reglas del juego."""
import math
import random

import pygame

import ajustes
import fondos
import sprites
from ajustes import BALDOSA
from camara import Camara
from jugador import Jugador
from objetos import (Bandera, Bloque, Checkpoint, Coleccionable, Comida,
                     Particulas, Sello)

OFFSET_Y = ajustes.ALTO - ajustes.FILAS_NIVEL * BALDOSA   # el nivel se pega abajo; el HUD va encima
SOLIDOS = set("#=B?")
SIMBOLOS_VALIDOS = set(" #=B?CEKPFWS")
SIMBOLOS_OBJETO = set("CEKPFS")     # se convierten en objetos y dejan la celda vacia


class ErrorNivel(ValueError):
    """Error claro cuando el diccionario de un nivel esta mal escrito."""


# ======================================================================
#  Validacion y carga
# ======================================================================
def validar_mapa(datos):
    """Revisa el mapa de texto. Lanza ErrorNivel indicando el numero de fila (desde 1)."""
    clave = datos.get("clave", "?")
    mapa = datos.get("mapa")
    if not mapa:
        raise ErrorNivel("Nivel '%s': falta el mapa." % clave)
    ancho = len(mapa[0])
    if len(mapa) != ajustes.FILAS_NIVEL:
        raise ErrorNivel("Nivel '%s': el mapa tiene %d filas y debe tener %d."
                         % (clave, len(mapa), ajustes.FILAS_NIVEL))
    for numero, fila in enumerate(mapa, start=1):
        if len(fila) != ancho:
            raise ErrorNivel("Nivel '%s': la fila %d mide %d caracteres y debe medir %d (como la fila 1)."
                             % (clave, numero, len(fila), ancho))
        for columna, simbolo in enumerate(fila, start=1):
            if simbolo not in SIMBOLOS_VALIDOS:
                raise ErrorNivel("Nivel '%s': simbolo desconocido %r en la fila %d, columna %d."
                                 % (clave, simbolo, numero, columna))
    texto = "".join(mapa)
    if texto.count("P") != 1:
        raise ErrorNivel("Nivel '%s': debe haber exactamente una P (hay %d)." % (clave, texto.count("P")))
    if texto.count("F") < 1:
        raise ErrorNivel("Nivel '%s': falta la bandera F." % clave)
    return ancho


def cargar_nivel(datos, sesion, sonido, personaje, accesorio):
    """Valida el diccionario y devuelve un Nivel listo para jugar."""
    validar_mapa(datos)
    return Nivel(datos, sesion, sonido, personaje, accesorio)


# ======================================================================
#  Nivel
# ======================================================================
class Nivel:
    def __init__(self, datos, sesion, sonido, personaje, accesorio):
        self.datos = datos
        self.region = datos["clave"]
        self.sesion = sesion
        self.sonido = sonido
        self.columnas = len(datos["mapa"][0])
        self.filas = ajustes.FILAS_NIVEL
        self.ancho_px = self.columnas * BALDOSA
        self.alto_px = self.filas * BALDOSA
        self.rejilla = [list(fila) for fila in datos["mapa"]]
        self.fondo = fondos.obtener(self.region)
        self.terreno = sprites.terreno(self.region)
        self.particulas = Particulas()
        self.azar = random.Random(1)

        self.bloques = {}
        self.coleccionables = []
        self.enemigos = []
        self.checkpoints = []
        self.sellos = []
        self.comidas = []
        self.bandera = None
        inicio = (1, 1)

        especiales = datos.get("bloques_especiales", {})
        claves_coleccionable = datos.get("coleccionable", "banano")
        if isinstance(claves_coleccionable, str):
            claves_coleccionable = [claves_coleccionable]
        indice_coleccionable = 0
        for fila, texto in enumerate(datos["mapa"]):
            for col, simbolo in enumerate(texto):
                if simbolo in "B?":
                    contenido = especiales.get((col, fila))
                    if simbolo == "?" and contenido is None:
                        contenido = "coleccionable"
                    self.bloques[(col, fila)] = Bloque(col, fila, simbolo, contenido)
                elif simbolo == "C":
                    clave = claves_coleccionable[indice_coleccionable % len(claves_coleccionable)]
                    indice_coleccionable += 1
                    self.coleccionables.append(Coleccionable(col, fila, clave))
                elif simbolo == "E":
                    import enemigos
                    self.enemigos.append(enemigos.crear(datos["enemigo"], col, fila))
                elif simbolo == "K":
                    self.checkpoints.append(Checkpoint(col, fila))
                elif simbolo == "P":
                    inicio = (col, fila)
                elif simbolo == "F":
                    self.bandera = Bandera(col, fila)
                elif simbolo == "S":
                    self.sellos.append(Sello(col, fila))
                if simbolo in SIMBOLOS_OBJETO:
                    self.rejilla[fila][col] = " "

        self.punto_inicio = (inicio[0] * BALDOSA, (inicio[1] + 1) * BALDOSA)
        self.punto_reaparicion = self.punto_inicio
        self.grande_en_checkpoint = sesion.grande
        self.jugador = Jugador(self.punto_inicio[0], self.punto_inicio[1], personaje, accesorio, sesion.grande)
        self.camara = Camara(self.ancho_px)
        self.camara.centrar(self.jugador)

        self.tiempo_total = datos.get("tiempo", ajustes.TIEMPO_NIVEL)
        self.tiempo = float(self.tiempo_total)
        self.reloj = 0.0               # reloj de animaciones
        self.estado = "jugando"        # jugando | muerto | meta | completo | game_over
        self.t_estado = 0.0
        self.eventos = []              # mensajes para la escena: "muerte", "nivel_completo", "game_over"...
        self.jefe = None
        if datos.get("jefe"):
            import jefe
            self.jefe = jefe.Jefe(self)
            self.bandera.visible = False

    # ------------------------------------------------------------ mapa
    def es_solido(self, col, fila):
        if col < 0 or col >= self.columnas:
            return True
        if fila < 0 or fila >= self.filas:
            return False
        return self.rejilla[fila][col] in SOLIDOS

    def simbolo(self, col, fila):
        if 0 <= col < self.columnas and 0 <= fila < self.filas:
            return self.rejilla[fila][col]
        return " "

    def _rango(self, ent):
        eps = 1e-4
        c0 = int(math.floor(ent.x / BALDOSA))
        c1 = int(math.floor((ent.x + ent.w - eps) / BALDOSA))
        f0 = int(math.floor(ent.y / BALDOSA))
        f1 = int(math.floor((ent.y + ent.h - eps) / BALDOSA))
        return c0, c1, f0, f1

    def mover(self, ent, dx, dy):
        """Mueve una entidad (x, y, w, h) por ejes separados: primero X, luego Y."""
        col = {"izq": False, "der": False, "arriba": False, "abajo": False, "bloque_golpeado": None}
        if dx:
            ent.x += dx
            c0, c1, f0, f1 = self._rango(ent)
            for fila in range(f0, f1 + 1):
                for c in range(c0, c1 + 1):
                    if self.es_solido(c, fila):
                        if dx > 0:
                            ent.x = min(ent.x, c * BALDOSA - ent.w)
                            col["der"] = True
                        else:
                            ent.x = max(ent.x, (c + 1) * BALDOSA)
                            col["izq"] = True
        if dy:
            ent.y += dy
            c0, c1, f0, f1 = self._rango(ent)
            candidatos = []
            for fila in range(f0, f1 + 1):
                for c in range(c0, c1 + 1):
                    if self.es_solido(c, fila):
                        if dy > 0:
                            ent.y = min(ent.y, fila * BALDOSA - ent.h)
                            col["abajo"] = True
                        else:
                            ent.y = max(ent.y, (fila + 1) * BALDOSA)
                            col["arriba"] = True
                            candidatos.append((c, fila))
            if candidatos:
                centro = ent.x + ent.w / 2
                col["bloque_golpeado"] = min(candidatos, key=lambda cf: abs(cf[0] * BALDOSA + 8 - centro))
        return col

    def agua_en(self, rect):
        """True si el rectangulo se hunde en una baldosa de agua (o lava) W."""
        c0 = max(0, rect.left // BALDOSA)
        c1 = min(self.columnas - 1, (rect.right - 1) // BALDOSA)
        for fila in range(max(0, rect.top // BALDOSA), min(self.filas - 1, (rect.bottom - 1) // BALDOSA) + 1):
            for c in range(c0, c1 + 1):
                if self.rejilla[fila][c] == "W" and rect.bottom > fila * BALDOSA + 6:
                    return True
        return False

    # ------------------------------------------------------------ reglas
    def sumar_puntos(self, cantidad, x=None, y=None):
        self.sesion.puntaje += cantidad
        if x is not None:
            self.particulas.texto(x, y, cantidad)

    def sumar_coleccionable(self, x=None, y=None):
        self.sesion.puntaje += ajustes.PUNTOS_COLECCIONABLE
        self.sesion.coleccionables += 1
        if self.sesion.coleccionables >= ajustes.COLECCIONABLES_VIDA:
            self.sesion.coleccionables = 0
            self.sesion.vidas += 1
            self.sonido.efecto("vida_extra")
            if x is not None:
                self.particulas.texto(x, y - 8, "1UP")
        else:
            self.sonido.efecto("coleccionable")

    def danar_jugador(self):
        """Golpe de enemigo o ceniza: grande -> pequeno; pequeno -> pierde una vida."""
        j = self.jugador
        if j.muriendo or j.invulnerable > 0 or self.estado != "jugando":
            return
        if j.grande:
            j.encoger()
            self.sonido.efecto("golpe")
        else:
            self.matar_jugador()

    def matar_jugador(self):
        j = self.jugador
        if j.muriendo or self.estado not in ("jugando",):
            return
        j.morir()
        self.sesion.vidas -= 1
        self.estado = "muerto"
        self.t_estado = 0.0
        self.sonido.parar_musica()
        self.sonido.efecto("morir")
        self.eventos.append("muerte")

    def _reaparecer(self):
        x, y = self.punto_reaparicion
        self.jugador = Jugador(x, y, self.jugador.personaje, self.jugador.accesorio, self.grande_en_checkpoint)
        self.jugador.invulnerable = 1.5
        self.camara.centrar(self.jugador)
        self.tiempo = float(self.tiempo_total)
        self.estado = "jugando"
        self.comidas = []
        if self.jefe:
            self.jefe.reiniciar_ciclo()
        self.eventos.append("reaparecer")

    def _golpear_bloque(self, col, fila):
        bloque = self.bloques.get((col, fila))
        if bloque is None or bloque.roto:
            return
        j = self.jugador
        if bloque.tipo == "B":
            if j.grande:
                bloque.roto = True
                self.rejilla[fila][col] = " "
                self.particulas.fragmentos(col * BALDOSA + 8, fila * BALDOSA + 8)
                self.sonido.efecto("romper")
            else:
                bloque.golpear()
                self.sonido.efecto("golpe")
        else:
            bloque.golpear()
            if bloque.usado:
                return
            bloque.usado = True
            if bloque.contenido == "comida":
                self.comidas.append(Comida(self.datos["comida"], col, fila))
                self.sonido.efecto("comida_sale")
            elif bloque.contenido == "coleccionable":
                clave = self.datos.get("coleccionable", "banano")
                if not isinstance(clave, str):
                    clave = clave[0]
                self.particulas.icono(col * BALDOSA + 8, fila * BALDOSA - 4, sprites.coleccionable(clave))
                self.sumar_coleccionable(col * BALDOSA + 8, fila * BALDOSA - 8)
        # lo que estuviera encima del bloque sale volando
        arriba = pygame.Rect(col * BALDOSA - 2, fila * BALDOSA - 6, BALDOSA + 4, 8)
        for enemigo in self.enemigos:
            if enemigo.vivo and not enemigo.muriendo and enemigo.rect.colliderect(arriba):
                enemigo.matar_por_golpe()
                self.sumar_puntos(ajustes.PUNTOS_ENEMIGO, enemigo.x + enemigo.w / 2, enemigo.y)

    def _comer(self, comida):
        j = self.jugador
        comida.viva = False
        self.sonido.efecto("comida")
        self.particulas.chispas(comida.x + 6, comida.y + 6, "#FFFFFF")
        if comida.clave == "colada_morada":
            self.sesion.vidas += 1
            self.sonido.efecto("vida_extra")
            self.particulas.texto(j.x + j.w / 2, j.y - 6, "1UP")
            if not j.grande:
                j.crecer()
            return
        if j.grande:
            self.sumar_puntos(ajustes.PUNTOS_COMIDA_GRANDE, j.x + j.w / 2, j.y - 6)
        else:
            j.crecer()
            self.sumar_puntos(0)

    def bono(self):
        """Puntos por los segundos que sobran al llegar a la bandera."""
        return int(self.tiempo) * ajustes.PUNTOS_POR_SEGUNDO

    # ------------------------------------------------------------ actualizacion
    def actualizar(self, dt, entrada):
        self.reloj += dt
        self.particulas.actualizar(dt)
        for bloque in self.bloques.values():
            bloque.actualizar(dt)
        j = self.jugador

        if self.estado == "muerto":
            self.t_estado += dt
            j.actualizar(dt, entrada, self)
            if self.t_estado > 2.0:
                if self.sesion.vidas > 0:
                    self._reaparecer()
                else:
                    self.estado = "game_over"
                    self.eventos.append("game_over")
            return
        if self.estado == "completo":
            return

        if j.t_crecer > 0:           # pausa breve mientras crece
            j.t_crecer = max(0.0, j.t_crecer - dt)
            return

        if self.estado == "jugando":
            self.tiempo -= dt
            if self.tiempo <= 0:
                self.tiempo = 0
                self.matar_jugador()
                return

        j.actualizar(dt, entrada, self)
        if j.golpe_bloque is not None and self.estado == "jugando":
            self._golpear_bloque(*j.golpe_bloque)

        if self.estado == "meta":
            self.t_estado += dt
            self.camara.seguir(j, dt)
            if j.modo == "meta_caminar" and j.t_modo > 1.2:
                self.estado = "completo"
                self.sesion.grande = j.grande
                self.eventos.append("nivel_completo")
        elif self.estado == "jugando":
            self._reglas(dt)
            self.camara.seguir(j, dt)

    def _reglas(self, dt):
        j = self.jugador
        rect = j.rect
        # vacio y agua
        if j.y > self.alto_px + 24 or self.agua_en(rect):
            self.matar_jugador()
            return
        # comida
        for comida in self.comidas:
            comida.actualizar(dt, self)
            if comida.viva and not comida.saliendo and rect.colliderect(comida.rect):
                self._comer(comida)
        self.comidas = [c for c in self.comidas if c.viva]
        # coleccionables
        for c in self.coleccionables:
            if not c.recogido and rect.colliderect(c.rect):
                c.recogido = True
                self.particulas.chispas(c.x, c.y)
                self.sumar_coleccionable(c.x, c.y - 6)
        # checkpoints
        for cp in self.checkpoints:
            if not cp.activo and rect.colliderect(cp.rect):
                cp.activo = True
                self.punto_reaparicion = cp.punto_reaparicion
                self.grande_en_checkpoint = j.grande
                self.sonido.efecto("checkpoint")
                self.particulas.chispas(cp.col * BALDOSA + 10, cp.fila * BALDOSA + 4, "#FFFFFF")
        # sellos de hielo
        for sello in self.sellos:
            if not sello.activo and rect.colliderect(sello.rect):
                sello.activo = True
                self.sonido.efecto("sello")
                self.particulas.chispas(sello.x + 8, sello.y + 8, "#9FE3FF")
                if self.jefe:
                    self.jefe.sello_activado()
        # enemigos
        self._enemigos(dt)
        if self.jefe:
            self.jefe.actualizar(dt)
        # meta
        b = self.bandera
        if b and b.visible and not b.tocada and rect.colliderect(b.rect):
            b.tocada = True
            self.estado = "meta"
            self.t_estado = 0.0
            j.iniciar_meta(b.x_mastil)
            self.sonido.parar_musica()
            self.sonido.efecto("meta")
            self.eventos.append("meta")

    def _enemigos(self, dt):
        j = self.jugador
        borde_derecho = self.camara.x + ajustes.ANCHO + 24
        for e in self.enemigos:
            if not e.activo and e.x < borde_derecho and e.x > self.camara.x - 160:
                e.activo = True
            if e.activo:
                e.actualizar(dt, self, j)
        self.enemigos = [e for e in self.enemigos if e.vivo]
        for e in self.enemigos:
            if not e.activo or e.muriendo:
                continue
            rect = j.rect
            if not rect.colliderect(e.rect):
                continue
            desde_arriba = j.vy > 0 and rect.bottom - e.rect.top <= 10 + max(0, j.vy * dt)
            if desde_arriba and e.pisable:
                puntos = e.pisar()
                j.rebotar()
                j.y = min(j.y, e.rect.top - j.h)
                self.sumar_puntos(puntos, e.x + e.w / 2, e.y - 4)
                self.sonido.efecto("pisar")
                self.particulas.chispas(e.x + e.w / 2, e.y, "#FFFFFF")
            elif e.letal:
                self.danar_jugador()

    # ------------------------------------------------------------ dibujo
    def _dibujar_terreno(self, lienzo, cx, oy):
        col0 = max(0, cx // BALDOSA)
        col1 = min(self.columnas - 1, (cx + ajustes.ANCHO) // BALDOSA)
        sprites_terreno = self.terreno
        cuadro_agua = int(self.reloj * 4) % 4
        color_agua = sprites_terreno["agua"][0].get_at((8, 12))[:3]
        for fila in range(self.filas):
            y = fila * BALDOSA + oy
            for col in range(col0, col1 + 1):
                simbolo = self.rejilla[fila][col]
                if simbolo == " ":
                    continue
                x = col * BALDOSA - cx
                if simbolo == "#":
                    arriba_solido = fila > 0 and self.rejilla[fila - 1][col] == "#"
                    lienzo.blit(sprites_terreno["relleno" if arriba_solido else "tope"], (x, y))
                elif simbolo == "=":
                    lienzo.blit(sprites_terreno["plataforma"], (x, y))
                elif simbolo == "W":
                    if fila > 0 and self.rejilla[fila - 1][col] == "W":
                        lienzo.fill(color_agua, (x, y, BALDOSA, BALDOSA))
                    else:
                        lienzo.blit(sprites_terreno["agua"][cuadro_agua], (x, y))

    def dibujar(self, lienzo):
        temblor = self.camara.temblor
        sx = sy = 0
        if temblor > 0:
            sx = self.azar.randint(-int(temblor), int(temblor))
            sy = self.azar.randint(-int(temblor), int(temblor))
        cx = self.camara.entero + sx
        oy = OFFSET_Y + sy
        self.fondo.dibujar(lienzo, cx)
        if self.jefe:
            self.jefe.dibujar_fondo(lienzo, cx, oy)
        self._dibujar_terreno(lienzo, cx, oy)
        for cp in self.checkpoints:
            cp.dibujar(lienzo, cx, oy, self.reloj)
        if self.bandera:
            self.bandera.dibujar(lienzo, cx, oy, self.reloj)
        for sello in self.sellos:
            sello.dibujar(lienzo, cx, oy, self.reloj)
        for c in self.coleccionables:
            if not c.recogido and cx - 16 < c.x < cx + ajustes.ANCHO + 16:
                c.dibujar(lienzo, cx, oy, self.reloj)
        for comida in self.comidas:
            comida.dibujar(lienzo, cx, oy)
        for (col, fila), bloque in self.bloques.items():
            if cx - 16 < col * BALDOSA < cx + ajustes.ANCHO:
                bloque.dibujar(lienzo, cx, oy, self.reloj)
        for e in self.enemigos:
            if cx - 32 < e.x < cx + ajustes.ANCHO + 32:
                e.dibujar(lienzo, cx, oy)
        self.jugador.dibujar(lienzo, cx, oy)
        if self.jefe:
            self.jefe.dibujar_frente(lienzo, cx, oy)
        self.particulas.dibujar(lienzo, cx, oy)
