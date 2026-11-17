"""Enemigos: Cangrejo, Condor, Mono, Iguana (y la Ceniza que camina en el Cotopaxi)."""
import math

import pygame

import ajustes
import sprites
from ajustes import BALDOSA


class Enemigo:
    """Base comun. Se vence pisandolo; tocarlo de lado o desde abajo daña al jugador."""

    TIPO = "cangrejo"
    ANCHO = 12
    ALTO = 10
    ANIM = "caminar"

    def __init__(self, col, fila):
        self.w = self.ANCHO
        self.h = self.ALTO
        self.x = col * BALDOSA + (BALDOSA - self.w) / 2
        self.y = (fila + 1) * BALDOSA - self.h
        self.vx = 0.0
        self.vy = 0.0
        self.derecha = False
        self.activo = False
        self.vivo = True
        self.muriendo = False        # "" / "aplastado" / "golpe"
        self.t_muerte = 0.0
        self.t_anim = 0.0
        self.inmune = 0.0
        self.pisable = True

    # ------------------------------------------------------------ propiedades
    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    @property
    def letal(self):
        return self.vivo and not self.muriendo

    # ------------------------------------------------------------ vencer
    def pisar(self):
        """Pisoton. Devuelve los puntos ganados."""
        self.muriendo = "aplastado"
        self.t_muerte = 0.0
        self.vx = 0.0
        return ajustes.PUNTOS_ENEMIGO

    def matar_por_golpe(self):
        """Muere al golpear el bloque que tiene debajo: sale volando."""
        self.muriendo = "golpe"
        self.t_muerte = 0.0
        self.vy = -150.0
        self.vx = 0.0

    # ------------------------------------------------------------ actualizacion
    def actualizar(self, dt, nivel, jugador):
        self.t_anim += dt
        if self.inmune > 0:
            self.inmune = max(0.0, self.inmune - dt)
        if self.muriendo:
            self.t_muerte += dt
            if self.muriendo == "golpe":
                self.vy += ajustes.GRAVEDAD * dt
                self.y += self.vy * dt
                self.x += (40 if jugador.x < self.x else -40) * dt
                if self.y > ajustes.ALTO + 40:
                    self.vivo = False
            elif self.t_muerte > 0.45:
                self.vivo = False
            return
        self.mover(dt, nivel, jugador)
        if self.y > nivel.alto_px + 40:
            self.vivo = False

    def mover(self, dt, nivel, jugador):
        pass

    def _caminar_con_gravedad(self, dt, nivel, girar_en_bordes=True):
        """Camina a la izquierda o derecha, gira en paredes y (si se pide) en bordes."""
        self.vy = min(self.vy + ajustes.GRAVEDAD * dt, ajustes.VEL_CAIDA_MAX)
        col = nivel.mover(self, self.vx * dt, 0)
        if col["izq"] or col["der"]:
            self.vx = -self.vx
        col = nivel.mover(self, 0, self.vy * dt)
        if col["abajo"]:
            self.vy = 0.0
            if girar_en_bordes and self.vx != 0:
                delante = self.x + self.w + 1 if self.vx > 0 else self.x - 1
                columna = int(math.floor(delante / BALDOSA))
                fila_abajo = int(math.floor((self.y + self.h + 1) / BALDOSA))
                if not nivel.es_solido(columna, fila_abajo):
                    self.vx = -self.vx
        if self.vx != 0:
            self.derecha = self.vx > 0

    # ------------------------------------------------------------ dibujo
    def imagen(self):
        if self.muriendo == "aplastado":
            return sprites.enemigo(self.TIPO, "aplastado", 0, self.derecha)
        cuadro = int(self.t_anim / 0.25)
        return sprites.enemigo(self.TIPO, self.ANIM, cuadro, self.derecha)

    def dibujar(self, lienzo, cam_x, oy=0):
        imagen = self.imagen()
        if self.muriendo == "golpe":
            imagen = pygame.transform.flip(imagen, False, True)
        sx = int(self.x + self.w / 2) - 8 - cam_x
        sy = int(self.y) + self.h - 15 + oy
        lienzo.blit(imagen, (sx, sy))


class Cangrejo(Enemigo):
    """Camina de lado. Da la vuelta en paredes y en bordes del suelo."""
    TIPO = "cangrejo"
    ANCHO = 12
    ALTO = 10

    def __init__(self, col, fila):
        super().__init__(col, fila)
        self.vx = -ajustes.VEL_CANGREJO

    def mover(self, dt, nivel, jugador):
        self._caminar_con_gravedad(dt, nivel, True)


class Condor(Enemigo):
    """Vuela en onda senoidal hacia la izquierda y vuelve. Se activa al entrar en pantalla."""
    TIPO = "condor"
    ANIM = "volar"
    ANCHO = 12
    ALTO = 10
    ALCANCE = 120

    def __init__(self, col, fila):
        super().__init__(col, fila)
        self.x0 = self.x
        self.y0 = self.y
        self.sentido = -1
        self.fase = 0.0
        self.recorrido = 0.0

    def mover(self, dt, nivel, jugador):
        paso = ajustes.VEL_CONDOR * dt
        self.x += self.sentido * paso
        self.recorrido += paso
        if self.recorrido >= self.ALCANCE:
            self.recorrido = 0.0
            self.sentido = -self.sentido
        self.fase += dt * 3.2
        self.y = self.y0 + math.sin(self.fase) * ajustes.AMPLITUD_CONDOR
        self.derecha = self.sentido > 0

    def imagen(self):
        if self.muriendo == "aplastado":
            return sprites.enemigo("condor", "aplastado", 0, self.derecha)
        return sprites.enemigo("condor", "volar", int(self.t_anim / 0.18), self.derecha)


class Mono(Enemigo):
    """Camina y salta cada ~1,2 s hacia el jugador si esta a menos de 8 baldosas."""
    TIPO = "mono"
    ANCHO = 10
    ALTO = 12

    def __init__(self, col, fila):
        super().__init__(col, fila)
        self.vx = -ajustes.VEL_MONO
        self.t_salto = ajustes.INTERVALO_SALTO_MONO
        self.en_suelo = False

    def mover(self, dt, nivel, jugador):
        cerca = abs((jugador.x + jugador.w / 2) - (self.x + self.w / 2)) < 8 * BALDOSA
        if cerca and not jugador.muriendo:
            hacia = 1 if jugador.x > self.x else -1
            self.vx = hacia * ajustes.VEL_MONO
        self.t_salto -= dt
        if self.t_salto <= 0 and cerca and self.en_suelo:
            self.vy = ajustes.SALTO_MONO
            self.t_salto = ajustes.INTERVALO_SALTO_MONO
            self.en_suelo = False
        elif self.t_salto <= 0 and not cerca:
            self.t_salto = 0.3
        self.vy = min(self.vy + ajustes.GRAVEDAD * dt, ajustes.VEL_CAIDA_MAX)
        col = nivel.mover(self, self.vx * dt, 0)
        if col["izq"] or col["der"]:
            self.vx = -self.vx
        col = nivel.mover(self, 0, self.vy * dt)
        if col["abajo"]:
            self.vy = 0.0
            self.en_suelo = True
        else:
            self.en_suelo = False
        self.derecha = self.vx > 0

    def imagen(self):
        if self.muriendo == "aplastado":
            return sprites.enemigo("mono", "aplastado", 0, self.derecha)
        cuadro = 1 if not self.en_suelo else int(self.t_anim / 0.25)
        return sprites.enemigo("mono", "caminar", cuadro, self.derecha)


class Iguana(Enemigo):
    """Lenta y resistente: el primer pisoton la deja aturdida 3 s, el segundo la elimina."""
    TIPO = "iguana"
    ANCHO = 14
    ALTO = 9

    def __init__(self, col, fila):
        super().__init__(col, fila)
        self.vx = -ajustes.VEL_IGUANA
        self.aturdida = 0.0
        self.sentido = -1

    @property
    def letal(self):
        return self.vivo and not self.muriendo and self.aturdida <= 0

    def pisar(self):
        if self.aturdida > 0:
            return super().pisar()
        self.aturdida = ajustes.TIEMPO_ATURDIDA
        self.vx = 0.0
        return ajustes.PUNTOS_ENEMIGO

    def mover(self, dt, nivel, jugador):
        if self.aturdida > 0:
            self.aturdida = max(0.0, self.aturdida - dt)
            self.vx = 0.0
            if self.aturdida == 0:
                self.vx = self.sentido * ajustes.VEL_IGUANA
        elif self.vx != 0:
            self.sentido = 1 if self.vx > 0 else -1
        self._caminar_con_gravedad(dt, nivel, True)
        if self.vx != 0:
            self.sentido = 1 if self.vx > 0 else -1
    def imagen(self):
        if self.muriendo == "aplastado":
            return sprites.enemigo("iguana", "aturdida", 0, self.derecha)
        if self.aturdida > 0:
            return sprites.enemigo("iguana", "aturdida", 0, self.derecha)
        return sprites.enemigo("iguana", "caminar", int(self.t_anim / 0.35), self.derecha)


class Ceniza(Enemigo):
    """Bola de ceniza que rueda por la arena del Cotopaxi."""
    TIPO = "ceniza"
    ANIM = "caer"
    ANCHO = 12
    ALTO = 11

    def __init__(self, col, fila):
        super().__init__(col, fila)
        self.vx = -ajustes.VEL_CANGREJO

    def mover(self, dt, nivel, jugador):
        self._caminar_con_gravedad(dt, nivel, True)

    def imagen(self):
        return sprites.enemigo("ceniza", "caer", 0, self.derecha)


CLASES = {
    "cangrejo": Cangrejo,
    "condor": Condor,
    "mono": Mono,
    "iguana": Iguana,
    "ceniza": Ceniza,
}


def crear(tipo, col, fila):
    """Crea el enemigo de la region en la baldosa (col, fila)."""
    return CLASES[tipo](col, fila)
