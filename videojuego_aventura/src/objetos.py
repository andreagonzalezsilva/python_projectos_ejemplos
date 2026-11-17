"""Objetos del nivel: Comida, Coleccionable, Bloque, Checkpoint, Bandera, Sello y particulas."""
import math
import random

import pygame

import ajustes
import interfaz
import sprites
from ajustes import BALDOSA, color


# ======================================================================
#  Particulas (polvo, chispas, fragmentos, textos de puntos)
# ======================================================================
class Particulas:
    def __init__(self):
        self.lista = []     # [x, y, vx, vy, vida, vida_max, color, tam, gravedad]
        self.textos = []    # [x, y, texto, vida]
        self.iconos = []    # [x, y, superficie, vida]
        self.fragmentos_ladrillo = []   # [x, y, vx, vy, vida]
        self.azar = random.Random(7)

    def polvo(self, x, y):
        for lado in (-1, 1):
            for _ in range(2):
                self.lista.append([x + lado * 3, y - 1, lado * self.azar.uniform(15, 40),
                                   self.azar.uniform(-25, -8), 0.3, 0.3, color("#E8E0D0"), 2, 0])

    def chispas(self, x, y, c="#FFF080"):
        for _ in range(7):
            ang = self.azar.uniform(0, math.tau)
            vel = self.azar.uniform(30, 70)
            self.lista.append([x, y, math.cos(ang) * vel, math.sin(ang) * vel, 0.35, 0.35,
                               color(c), 1, 0])

    def fragmentos(self, x, y):
        for dx, dy in ((-4, -4), (4, -4), (-4, 4), (4, 4)):
            self.fragmentos_ladrillo.append([x + dx, y + dy, dx * 14, -140 + dy * 8, 1.2])

    def texto(self, x, y, cadena):
        self.textos.append([x, y, str(cadena), 0.8])

    def icono(self, x, y, superficie):
        self.iconos.append([x, y, superficie, 0.45])

    def actualizar(self, dt):
        for p in self.lista:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += p[8] * dt
            p[4] -= dt
        self.lista = [p for p in self.lista if p[4] > 0]
        for t in self.textos:
            t[1] -= 24 * dt
            t[3] -= dt
        self.textos = [t for t in self.textos if t[3] > 0]
        for i in self.iconos:
            i[1] -= 70 * dt
            i[3] -= dt
        self.iconos = [i for i in self.iconos if i[3] > 0]
        for fr in self.fragmentos_ladrillo:
            fr[0] += fr[2] * dt
            fr[1] += fr[3] * dt
            fr[3] += ajustes.GRAVEDAD * dt
            fr[4] -= dt
        self.fragmentos_ladrillo = [fr for fr in self.fragmentos_ladrillo if fr[4] > 0]

    def dibujar(self, lienzo, cam_x, oy=0):
        for x, y, vx, vy, vida, vmax, c, tam, g in self.lista:
            lienzo.fill(c, (int(x) - cam_x, int(y) + oy, tam, tam))
        for x, y, superficie, vida in self.iconos:
            lienzo.blit(superficie, (int(x) - 6 - cam_x, int(y) - 6 + oy))
        for x, y, vx, vy, vida in self.fragmentos_ladrillo:
            lienzo.blit(sprites.CACHE["fragmento"], (int(x) - 2 - cam_x, int(y) - 2 + oy))
        for x, y, cadena, vida in self.textos:
            interfaz.texto(lienzo, cadena, (int(x) - cam_x, int(y) + oy), "#FFFFFF", tam=8, centrado=True)


# ======================================================================
#  Bloques
# ======================================================================
class Bloque:
    """Ladrillo (B) o bloque de pregunta (?). contenido: 'comida', 'coleccionable' o None."""

    TIEMPO_REBOTE = 0.18

    def __init__(self, col, fila, tipo, contenido=None):
        self.col = col
        self.fila = fila
        self.tipo = tipo
        self.contenido = contenido
        self.usado = False
        self.roto = False
        self.rebote = 0.0

    def golpear(self):
        self.rebote = self.TIEMPO_REBOTE

    def actualizar(self, dt):
        if self.rebote > 0:
            self.rebote = max(0.0, self.rebote - dt)

    def dibujar(self, lienzo, cam_x, oy, tiempo):
        if self.roto:
            return
        desplazo = 0
        if self.rebote > 0:
            desplazo = -int(round(5 * math.sin(math.pi * (1 - self.rebote / self.TIEMPO_REBOTE))))
        x = self.col * BALDOSA - cam_x
        y = self.fila * BALDOSA + oy + desplazo
        if self.tipo == "B":
            imagen = sprites.bloque("ladrillo")
        elif self.usado:
            imagen = sprites.bloque("usado")
        else:
            cuadros = sprites.CACHE["bloques"]["signo"]
            imagen = cuadros[int(tiempo * 5) % 4 if int(tiempo * 5) % 8 < 4 else 0]
        lienzo.blit(imagen, (x, y))


# ======================================================================
#  Comida que hace crecer
# ======================================================================
class Comida:
    TAM = 12

    def __init__(self, clave, col, fila):
        self.clave = clave
        self.w = self.TAM
        self.h = self.TAM
        self.x = col * BALDOSA + (BALDOSA - self.w) / 2
        self.y = fila * BALDOSA + BALDOSA - self.h
        self.destino_y = fila * BALDOSA - self.h
        self.vx = ajustes.VEL_COMIDA
        self.vy = 0.0
        self.saliendo = True
        self.viva = True

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def actualizar(self, dt, nivel):
        if self.saliendo:
            self.y -= 36 * dt
            if self.y <= self.destino_y:
                self.y = self.destino_y
                self.saliendo = False
            return
        self.vy = min(self.vy + ajustes.GRAVEDAD * dt, ajustes.VEL_CAIDA_MAX)
        col = nivel.mover(self, self.vx * dt, 0)
        if col["izq"] or col["der"]:
            self.vx = -self.vx
        col = nivel.mover(self, 0, self.vy * dt)
        if col["abajo"]:
            self.vy = 0.0
        if self.y > ajustes.ALTO + 40:
            self.viva = False

    def dibujar(self, lienzo, cam_x, oy=0):
        imagen = sprites.comida(self.clave)
        lienzo.blit(imagen, (int(self.x) - 2 - cam_x, int(self.y) - 3 + oy))


# ======================================================================
#  Coleccionables, checkpoints, bandera, sellos
# ======================================================================
class Coleccionable:
    def __init__(self, col, fila, clave):
        self.clave = clave
        self.x = col * BALDOSA + BALDOSA / 2
        self.y = fila * BALDOSA + BALDOSA / 2
        self.fase = (col * 0.7) % math.tau
        self.recogido = False

    @property
    def rect(self):
        return pygame.Rect(int(self.x) - 5, int(self.y) - 5, 10, 10)

    def dibujar(self, lienzo, cam_x, oy, tiempo):
        flotar = math.sin(tiempo * 4 + self.fase) * 1.5
        imagen = sprites.coleccionable(self.clave)
        lienzo.blit(imagen, (int(self.x) - 6 - cam_x, int(self.y + flotar) - 6 + oy))


class Checkpoint:
    def __init__(self, col, fila):
        self.col = col
        self.fila = fila
        self.activo = False

    @property
    def rect(self):
        return pygame.Rect(self.col * BALDOSA, self.fila * BALDOSA - 8, BALDOSA, BALDOSA + 8)

    @property
    def punto_reaparicion(self):
        """(x del centro de la baldosa, y del suelo)."""
        return (self.col * BALDOSA, (self.fila + 1) * BALDOSA)

    def dibujar(self, lienzo, cam_x, oy, tiempo):
        x = self.col * BALDOSA - cam_x
        y = self.fila * BALDOSA + oy
        if self.activo:
            imagen = sprites.CACHE["checkpoint"]["activo"][int(tiempo * 6) % 4]
        else:
            imagen = sprites.CACHE["checkpoint"]["apagado"]
        lienzo.blit(imagen, (x, y))


class Bandera:
    """Bandera de Ecuador: la meta. El mastil mide 6 baldosas de alto."""
    ALTO = 96
    EXTRA = 32          # zona invisible sobre el mastil: no se puede saltar por encima

    def __init__(self, col, fila):
        self.col = col
        self.fila = fila
        self.tocada = False
        self.visible = True

    @property
    def rect(self):
        return pygame.Rect(self.col * BALDOSA + 3, (self.fila + 1) * BALDOSA - self.ALTO - self.EXTRA, 5,
                           self.ALTO + self.EXTRA)

    @property
    def x_mastil(self):
        return self.col * BALDOSA + 5

    def dibujar(self, lienzo, cam_x, oy, tiempo):
        if not self.visible:
            return
        imagen = sprites.CACHE["bandera_meta"][int(tiempo * 5) % 4]
        lienzo.blit(imagen, (self.col * BALDOSA - cam_x, (self.fila + 1) * BALDOSA - self.ALTO + oy))


class Sello:
    """Sello de hielo del jefe: se activa al tocarlo."""

    def __init__(self, col, fila):
        self.x = col * BALDOSA
        self.y = fila * BALDOSA
        self.activo = False

    @property
    def rect(self):
        return pygame.Rect(self.x + 1, self.y + 1, 14, 14)

    def dibujar(self, lienzo, cam_x, oy, tiempo):
        clave = "activo" if self.activo else "apagado"
        imagen = sprites.CACHE["sello_jefe"][clave]
        flotar = 0 if self.activo else int(round(math.sin(tiempo * 3 + self.x) * 1.5))
        lienzo.blit(imagen, (self.x - cam_x, self.y + oy + flotar))
        if not self.activo:
            brillo = (int(tiempo * 4) % 2) * 40
            if brillo:
                pygame.draw.rect(lienzo, color("#9FE3FF"), (self.x - cam_x + 7, self.y + oy + 7 + flotar, 2, 2))
