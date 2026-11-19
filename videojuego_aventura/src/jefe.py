"""Jefe final: el volcan Cotopaxi, su ciclo de erupcion, ceniza y rocas."""
import math
import random

import pygame

import ajustes
import interfaz
import sprites
import textos
from ajustes import BALDOSA, color


class Proyectil:
    """Bola de ceniza o roca que cae desde arriba."""

    def __init__(self, x, tipo, suelo_y, vx=0.0):
        self.x = x
        self.vx = vx            # distinto de 0: bola de lava que rueda por el suelo
        self.y = (suelo_y - 6) if vx else -16.0
        self.vy = 0.0 if vx else 120.0
        self.tipo = tipo
        self.suelo_y = suelo_y
        self.vivo = True

    @property
    def rect(self):
        if self.vx:
            return pygame.Rect(int(self.x) - 7, int(self.y) - 5, 14, 11)
        lado = 16 if self.tipo == "roca" else 13
        return pygame.Rect(int(self.x) - lado // 2, int(self.y) - lado // 2, lado, lado)

    def actualizar(self, dt, ancho_nivel=0):
        if self.vx:
            self.x += self.vx * dt
            if self.x < -40 or self.x > ancho_nivel + 40:
                self.vivo = False
            return
        self.vy = min(self.vy + 700 * dt, 340)
        self.y += self.vy * dt
        if self.y + 6 >= self.suelo_y:
            self.vivo = False


class Jefe:
    CALMA, AVISO, ERUPCION = "calma", "aviso", "erupcion"

    def __init__(self, nivel):
        self.nivel = nivel
        self.azar = random.Random(5)
        self.sellos_activos = 0
        self.total_sellos = max(1, len(nivel.sellos))
        self.derrotado = False
        self.suelo_y = BALDOSA * 9
        self.volcan = self._crear_volcan()
        self.reiniciar_ciclo()

    # ------------------------------------------------------------ propiedades
    @property
    def vida(self):
        return self.total_sellos - self.sellos_activos

    @property
    def duracion_erupcion(self):
        """Cada sello activado enfurece al volcan: la erupcion dura mas."""
        return ajustes.JEFE_ERUPCION + 1.5 * self.sellos_activos

    @property
    def duracion_calma(self):
        return max(0.8, ajustes.JEFE_CALMA - 0.35 * self.sellos_activos)

    @property
    def intervalo_disparo(self):
        return max(0.07, ajustes.JEFE_INTERVALO - 0.025 * self.sellos_activos)

    # ------------------------------------------------------------ ciclo
    def reiniciar_ciclo(self):
        self.fase = self.CALMA
        self.t_fase = 0.0
        self.proyectiles = []
        self.avisos = []
        self.t_disparo = 0.0
        self.t_lava = 0.0
        self.lado_lava = self.azar.random() < 0.5
        self.indice_aviso = 0
        self.nivel.camara.temblor = 0

    def sello_activado(self):
        self.sellos_activos += 1
        self.nivel.sumar_puntos(500, *self._pos_jugador())
        if self.sellos_activos >= self.total_sellos:
            self.derrotar()

    def _pos_jugador(self):
        j = self.nivel.jugador
        return j.x + j.w / 2, j.y - 6

    def derrotar(self):
        self.derrotado = True
        self.proyectiles = []
        self.avisos = []
        self.nivel.camara.temblor = 0
        self.nivel.bandera.visible = True
        self.nivel.sonido.efecto("victoria_nivel")
        self.nivel.particulas.texto(self.nivel.bandera.col * BALDOSA + 8, 60, "!")

    def _elegir_avisos(self):
        j = self.nivel.jugador
        cantidad = 10
        xs = []
        for i in range(cantidad):
            base = j.x + (i - cantidad / 2) * 26 + self.azar.uniform(-8, 8)
            xs.append(max(12, min(self.nivel.ancho_px - 12, base)))
        self.azar.shuffle(xs)
        # siempre cae una justo sobre el jugador
        xs[0] = j.x + j.w / 2
        return xs

    def actualizar(self, dt):
        if self.derrotado:
            return
        self.t_fase += dt
        camara = self.nivel.camara
        if self.fase == self.CALMA:
            camara.temblor = 0
            if self.t_fase >= self.duracion_calma:
                self.fase = self.AVISO
                self.t_fase = 0.0
                self.avisos = self._elegir_avisos()
                self.nivel.sonido.efecto("temblor")
        elif self.fase == self.AVISO:
            camara.temblor = 1
            if self.t_fase >= ajustes.JEFE_AVISO:
                self.fase = self.ERUPCION
                self.t_fase = 0.0
                self.t_disparo = 0.0
                self.t_lava = 0.4
                self.indice_aviso = 0
        else:
            camara.temblor = 2
            self.t_disparo -= dt
            self.t_lava -= dt
            j = self.nivel.jugador
            if self.t_disparo <= 0 and self.avisos:
                # la mitad de los disparos apunta (sin aviso) a donde estara el jugador
                if self.indice_aviso % 2 == 1:
                    x = j.x + j.w / 2 + j.vx * 0.5 + self.azar.uniform(-8, 8)
                    x = max(8, min(self.nivel.ancho_px - 8, x))
                else:
                    x = self.avisos[(self.indice_aviso // 2) % len(self.avisos)]
                tipo = "roca" if self.indice_aviso % 3 == 2 else "ceniza"
                self.proyectiles.append(Proyectil(x, tipo, self.suelo_y))
                self.indice_aviso += 1
                self.t_disparo = self.intervalo_disparo
            if self.t_lava <= 0:
                # bola de lava que rueda desde un borde: hay que saltarla o subir a una plataforma
                desde_izquierda = self.lado_lava
                borde = self.nivel.camara.x
                x0 = borde - 8 if desde_izquierda else borde + ajustes.ANCHO + 8
                vel = ajustes.JEFE_VEL_LAVA * (1 if desde_izquierda else -1)
                self.proyectiles.append(Proyectil(x0, "roca", self.suelo_y, vx=vel))
                self.lado_lava = not self.lado_lava
                self.t_lava = 1.5
            if self.t_fase >= self.duracion_erupcion:
                self.fase = self.CALMA
                self.t_fase = 0.0
                self.avisos = []
                camara.temblor = 0
        j = self.nivel.jugador
        for p in self.proyectiles:
            p.actualizar(dt, self.nivel.ancho_px)
            if p.vivo and not j.muriendo and p.rect.colliderect(j.rect):
                p.vivo = False
                self.nivel.danar_jugador()
            if not p.vivo:
                self.nivel.particulas.chispas(p.x, min(p.y, self.suelo_y), "#FF8A1F")
        self.proyectiles = [p for p in self.proyectiles if p.vivo]

    # ------------------------------------------------------------ dibujo
    def _crear_volcan(self):
        ancho, alto = 300, 150
        s = pygame.Surface((ancho, alto), pygame.SRCALPHA)
        roca = color("#3A2E40")
        sombra = color("#2A2030")
        cima_y = 18
        pygame.draw.polygon(s, roca, [(0, alto), (ancho // 2 - 34, cima_y), (ancho // 2 + 34, cima_y), (ancho, alto)])
        pygame.draw.polygon(s, sombra, [(ancho // 2 + 10, cima_y), (ancho // 2 + 34, cima_y), (ancho, alto),
                                        (ancho // 2 + 70, alto)])
        # nieve irregular en la cima
        nieve = color("#E8EEF5")
        puntos = [(ancho // 2 - 34, cima_y), (ancho // 2 + 34, cima_y), (ancho // 2 + 56, cima_y + 36)]
        for i in range(8):
            x = ancho // 2 + 56 - i * 14
            puntos.append((x, cima_y + 36 + (8 if i % 2 else -2)))
        pygame.draw.polygon(s, nieve, puntos)
        # crater
        pygame.draw.ellipse(s, color("#1A1220"), (ancho // 2 - 34, cima_y - 6, 68, 14))
        return pygame.transform.scale(s, (255, 128)).convert_alpha()

    def dibujar_fondo(self, lienzo, cx, oy):
        x = int(ajustes.ANCHO / 2 - 128 - cx * 0.12)
        y = oy + 150 - 128
        brillo = 0.0
        if self.fase == self.AVISO:
            brillo = 0.5 + 0.5 * math.sin(self.t_fase * 12)
        elif self.fase == self.ERUPCION:
            brillo = 1.0
        if brillo > 0 and not self.derrotado:
            resplandor = pygame.Surface((150, 90), pygame.SRCALPHA)
            for r, a in ((60, 40), (42, 70), (26, 100)):
                pygame.draw.circle(resplandor, (255, 138, 31, int(a * brillo)), (75, 60), r)
            lienzo.blit(resplandor, (x + 53, y - 40))
        lienzo.blit(self.volcan, (x, y))
        # lava y humo
        crater_x = x + 128
        if not self.derrotado:
            if brillo > 0:
                pygame.draw.ellipse(lienzo, color("#FF8A1F"), (crater_x - 22, y + 12, 44, 8))
                for i in range(4):
                    ay = y + 6 - ((self.nivel.reloj * 40 + i * 14) % 56)
                    ax = crater_x + math.sin(self.nivel.reloj * 3 + i) * 8
                    pygame.draw.circle(lienzo, color("#5A4A5A"), (int(ax), int(ay)), 5 + i)
                if self.fase == self.ERUPCION:
                    for i in range(6):
                        ang = i * 1.0 + self.nivel.reloj * 3
                        px = crater_x + math.cos(ang) * (10 + (self.nivel.reloj * 60 + i * 9) % 40)
                        py = y + 10 - abs(math.sin(ang * 1.3)) * 40
                        pygame.draw.rect(lienzo, color("#FFD24A"), (int(px), int(py), 2, 2))
            else:
                ay = y + 8 - (self.nivel.reloj * 6) % 18
                pygame.draw.circle(lienzo, color("#6A5A6A"), (crater_x, int(ay)), 3)
        else:
            pygame.draw.ellipse(lienzo, color("#9FE3FF"), (crater_x - 22, y + 12, 44, 8))

    def dibujar_frente(self, lienzo, cx, oy):
        # sombras de aviso en el suelo
        if self.fase == self.AVISO or (self.fase == self.ERUPCION and self.avisos):
            parpadeo = int(self.nivel.reloj * 8) % 2 == 0
            if self.fase == self.ERUPCION or parpadeo:
                for x in self.avisos:
                    pygame.draw.ellipse(lienzo, color("#14121C"), (int(x) - 9 - cx, self.suelo_y + oy - 2, 18, 5))
                    pygame.draw.ellipse(lienzo, color("#FF8A1F"), (int(x) - 9 - cx, self.suelo_y + oy - 2, 18, 5), 1)
        for p in self.proyectiles:
            imagen = sprites.enemigo(p.tipo, "caer", 0, True)
            lienzo.blit(imagen, (int(p.x) - 8 - cx, int(p.y) - 8 + oy))
        self._dibujar_barra(lienzo)

    def _dibujar_barra(self, lienzo):
        ancho_seg, alto = 22, 7
        total = ancho_seg * self.total_sellos + 3 * (self.total_sellos - 1)
        x0 = ajustes.ANCHO // 2 - total // 2
        y0 = 17
        interfaz.texto(lienzo, textos.t("nivel_cotopaxi"), (x0 - 4, y0 - 1), derecha=True, tam=8,
                       color_texto="#FF8A1F")
        for i in range(self.total_sellos):
            rect = pygame.Rect(x0 + i * (ancho_seg + 3), y0, ancho_seg, alto)
            pygame.draw.rect(lienzo, color("#14121C"), rect.inflate(2, 2))
            llena = i < self.vida
            pygame.draw.rect(lienzo, color("#D8332B" if llena else "#3A3040"), rect)
            if llena:
                pygame.draw.rect(lienzo, color("#FF8A60"), (rect.x, rect.y, rect.w, 2))
        texto = "%d/%d" % (self.sellos_activos, self.total_sellos)
        icono = sprites.coleccionable("sello_hielo")
        lienzo.blit(icono, (x0 + total + 4, y0 - 3))
        interfaz.texto(lienzo, texto, (x0 + total + 18, y0 - 1), tam=8, color_texto="#9FE3FF")
        if self.derrotado:
            interfaz.texto(lienzo, textos.t("mensaje_volcan_calmado"), (ajustes.ANCHO // 2, 30),
                           centrado=True, tam=8, color_texto="#FFFFFF")
