"""El jugador: fisica, animacion y estados pequeno/grande."""
import pygame

import ajustes
import sprites


def aproximar(valor, objetivo, paso):
    """Acerca 'valor' a 'objetivo' sin pasarse."""
    if valor < objetivo:
        return min(valor + paso, objetivo)
    return max(valor - paso, objetivo)


class Jugador:
    TIEMPO_CRECER = 0.8

    def __init__(self, x_baldosa, y_suelo, personaje, accesorio, grande=False):
        """x_baldosa: columna en pixeles (izquierda de la baldosa). y_suelo: y donde pisan los pies."""
        self.personaje = personaje
        self.accesorio = accesorio
        self.grande = grande
        self.w = ajustes.HITBOX_PEQUENO[0]
        self.h = ajustes.HITBOX_GRANDE[1] if grande else ajustes.HITBOX_PEQUENO[1]
        self.x = x_baldosa + (ajustes.BALDOSA - self.w) / 2
        self.y = y_suelo - self.h
        self.vx = 0.0
        self.vy = 0.0
        self.derecha = True
        self.en_suelo = False
        self.coyote = 0.0
        self.buffer = 0.0
        self.salto_cortado = False
        self.invulnerable = 0.0
        self.vivo = True
        self.muriendo = False
        self.t_muerte = 0.0
        self.t_crecer = 0.0
        self.t_anim = 0.0
        self.t_total = 0.0
        self.modo = "normal"            # normal | meta_bajar | meta_caminar
        self.t_modo = 0.0
        self.golpe_bloque = None        # (col, fila) golpeado desde abajo en este cuadro
        self.salto_ahora = False        # True en el cuadro en que salto (para sonido)

    # ------------------------------------------------------------ propiedades
    @property
    def rect(self):
        return pygame.Rect(int(round(self.x)), int(round(self.y)), self.w, self.h)

    @property
    def pies(self):
        return self.y + self.h

    # ------------------------------------------------------------ cambios de tamano
    def crecer(self):
        if self.grande:
            return
        self.grande = True
        self.y -= ajustes.HITBOX_GRANDE[1] - self.h
        self.h = ajustes.HITBOX_GRANDE[1]
        self.t_crecer = self.TIEMPO_CRECER

    def encoger(self):
        if not self.grande:
            return
        self.grande = False
        self.y += self.h - ajustes.HITBOX_PEQUENO[1]
        self.h = ajustes.HITBOX_PEQUENO[1]
        self.invulnerable = ajustes.TIEMPO_INVULNERABLE

    def morir(self):
        if self.muriendo:
            return
        self.muriendo = True
        self.vx = 0
        self.vy = -250
        self.t_muerte = 0.0

    def rebotar(self):
        """Rebote despues de pisar a un enemigo."""
        self.vy = ajustes.REBOTE_PISOTON
        self.en_suelo = False
        self.salto_cortado = True

    def iniciar_meta(self, x_mastil):
        self.modo = "meta_bajar"
        self.x = x_mastil - self.w / 2
        self.vx = 0
        self.vy = 0
        self.t_modo = 0.0
        self.derecha = True

    # ------------------------------------------------------------ actualizacion
    def actualizar(self, dt, entrada, nivel):
        self.golpe_bloque = None
        self.salto_ahora = False
        self.t_total += dt
        if self.invulnerable > 0:
            self.invulnerable = max(0.0, self.invulnerable - dt)

        if self.muriendo:
            self.t_muerte += dt
            if self.t_muerte > 0.35:
                self.vy = min(self.vy + ajustes.GRAVEDAD * dt, ajustes.VEL_CAIDA_MAX)
                self.y += self.vy * dt
            else:
                self.vy = 0
            return

        if self.modo == "meta_bajar":
            self.t_modo += dt
            self.vy = 70
            col = nivel.mover(self, 0, self.vy * dt)
            if col["abajo"]:
                self.modo = "meta_caminar"
                self.t_modo = 0.0
                self.x += 10
                self.derecha = True
            return
        if self.modo == "meta_caminar":
            self.t_modo += dt
            self.vx = 50
            self.vy = min(self.vy + ajustes.GRAVEDAD * dt, ajustes.VEL_CAIDA_MAX)
            nivel.mover(self, self.vx * dt, 0)
            col = nivel.mover(self, 0, self.vy * dt)
            if col["abajo"]:
                self.vy = 0
            self.t_anim += abs(self.vx) * dt
            return

        # ---- horizontal
        direccion = int(entrada.derecha) - int(entrada.izquierda)
        vel_max = ajustes.VEL_CORRER if entrada.correr else ajustes.VEL_CAMINAR
        if direccion != 0:
            self.derecha = direccion > 0
            objetivo = direccion * vel_max
            if self.en_suelo:
                aceleracion = ajustes.FRENO_SUELO if self.vx * direccion < 0 else ajustes.ACEL_SUELO
            else:
                aceleracion = ajustes.ACEL_SUELO * ajustes.CONTROL_AIRE
            self.vx = aproximar(self.vx, objetivo, aceleracion * dt)
        elif self.en_suelo:
            self.vx = aproximar(self.vx, 0.0, ajustes.FRENO_SUELO * dt)

        # ---- salto (coyote + buffer + salto variable)
        if entrada.salto:
            self.buffer = ajustes.TIEMPO_BUFFER
        else:
            self.buffer = max(0.0, self.buffer - dt)
        if self.en_suelo:
            self.coyote = ajustes.TIEMPO_COYOTE
        else:
            self.coyote = max(0.0, self.coyote - dt)
        if self.buffer > 0 and self.coyote > 0:
            self.vy = ajustes.VEL_SALTO
            self.buffer = 0.0
            self.coyote = 0.0
            self.en_suelo = False
            self.salto_cortado = False
            self.salto_ahora = True
            nivel.sonido.efecto("saltar")
        if self.vy < 0 and not entrada.salto_presionado and not self.salto_cortado:
            self.vy *= ajustes.CORTE_SALTO
            self.salto_cortado = True

        # ---- gravedad y movimiento por ejes
        self.vy = min(self.vy + ajustes.GRAVEDAD * dt, ajustes.VEL_CAIDA_MAX)
        col = nivel.mover(self, self.vx * dt, 0)
        if col["izq"] or col["der"]:
            self.vx = 0.0
        velocidad_antes = self.vy
        col = nivel.mover(self, 0, self.vy * dt)
        if col["abajo"]:
            if not self.en_suelo and velocidad_antes > 160:
                nivel.particulas.polvo(self.x + self.w / 2, self.pies)
            self.vy = 0.0
            self.en_suelo = True
        else:
            self.en_suelo = False
        if col["arriba"]:
            self.vy = max(self.vy, 0.0)
            self.golpe_bloque = col["bloque_golpeado"]

        # ---- animacion
        self.t_anim += abs(self.vx) * dt

    # ------------------------------------------------------------ dibujo
    def _animacion(self):
        if self.muriendo:
            return "caer", 0
        if self.modo == "meta_bajar":
            return "quieto", 0
        if not self.en_suelo and self.modo != "meta_caminar":
            return ("saltar", 0) if self.vy < 0 else ("caer", 0)
        if abs(self.vx) > 8:
            return "caminar", int(self.t_anim / 9)
        return "quieto", 0

    def dibujar(self, lienzo, cam_x, oy=0):
        if self.invulnerable > 0 and int(self.t_total / 0.06) % 2 == 0:
            return
        anim, cuadro = self._animacion()
        grande = self.grande
        if self.t_crecer > 0:
            grande = int(self.t_crecer / 0.1) % 2 == 0
        imagen = sprites.personaje(self.personaje, self.accesorio, grande, anim, cuadro, self.derecha)
        sx = int(round(self.x + self.w / 2)) - 8 - cam_x
        sy = int(round(self.y + self.h)) - imagen.get_height() + oy
        lienzo.blit(imagen, (sx, sy))
