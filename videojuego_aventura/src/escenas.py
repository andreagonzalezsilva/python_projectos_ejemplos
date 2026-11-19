"""Escenas: Titulo -> Seleccion -> Juego -> (Pausa) -> FinNivel -> ... -> Victoria, y GameOver."""
import math
import random

import pygame

import ajustes
import fondos
import interfaz
import sprites
import textos
from ajustes import color
from interfaz import Desplegable, Menu
from motor import Escena
from nivel import cargar_nivel
from niveles import LISTA_NIVELES


def _tecla(evento, *teclas):
    return evento.type == pygame.KEYDOWN and evento.key in teclas


def _enter(evento):
    return _tecla(evento, pygame.K_RETURN, pygame.K_KP_ENTER)


# ======================================================================
#  Titulo
# ======================================================================
class Titulo(Escena):
    def __init__(self, motor):
        super().__init__(motor)
        self.menu = Menu(motor, ["jugar", "salir"], y=80)
        self.desplegable = Desplegable(motor)
        self.fondo = fondos.obtener("sierra")
        self.terreno = sprites.terreno("sierra")
        self.tiempo = 0.0
        motor.sonido.musica("titulo")

    def eventos(self, lista):
        if self.desplegable.eventos(lista):
            return
        if self.desplegable.abierto:
            return
        elegido = self.menu.eventos(lista)
        if elegido == "jugar":
            self.motor.cambiar_escena(Seleccion(self.motor))
        elif elegido == "salir":
            self.motor.corriendo = False

    def actualizar(self, dt):
        self.tiempo += dt

    def dibujar(self, lienzo):
        self.fondo.dibujar(lienzo, 0, deriva=self.tiempo * 25)
        for col in range(ajustes.ANCHO // 16 + 1):
            lienzo.blit(self.terreno["tope"], (col * 16, 144))
            lienzo.blit(self.terreno["relleno"], (col * 16, 160))
        # el personaje elegido camina por el paisaje
        datos = self.motor.datos
        x = int(self.tiempo * 38) % (ajustes.ANCHO + 40) - 20
        imagen = sprites.personaje(datos["personaje"], datos["accesorio"], False, "caminar",
                                   int(self.tiempo * 8), True)
        lienzo.blit(imagen, (x, 128))

        zona = interfaz.titulo_inca(lienzo, textos.t("titulo"), ajustes.ANCHO // 2, 31, alto=16, ancho_max=262)
        interfaz.tricolor(lienzo, ajustes.ANCHO // 2 - 90, int(zona.bottom) + 1, 180, 6)
        self.menu.dibujar(lienzo)
        mejor = "%s: %06d" % (textos.t("mejor_puntaje"), self.motor.datos.get("mejor_puntaje", 0))
        interfaz.panel(lienzo, pygame.Rect(ajustes.ANCHO // 2 - 85, 117, 170, 13))
        interfaz.texto(lienzo, mejor, (ajustes.ANCHO // 2, 118), centrado=True)
        interfaz.panel(lienzo, pygame.Rect(0, 164, ajustes.ANCHO, 14), 140)
        if not self.desplegable.abierto:
            interfaz.texto(lienzo, textos.t("idioma_tecla"), (ajustes.ANCHO - 4, 19), derecha=True, tam=8,
                           color_texto="#DDE6FF")
        interfaz.texto(lienzo, textos.t("controles"), (ajustes.ANCHO // 2, 166), centrado=True, tam=8)
        self.desplegable.dibujar(lienzo)


# ======================================================================
#  Seleccion de personaje y accesorio
# ======================================================================
class Seleccion(Escena):
    ORIGEN = (8, 18)
    CELDA = (52, 44)

    def __init__(self, motor):
        super().__init__(motor)
        datos = motor.datos
        self.ip = ajustes.ORDEN_PERSONAJES.index(datos["personaje"]) if datos["personaje"] in ajustes.PERSONAJES else 0
        self.ia = ajustes.ORDEN_ACCESORIOS.index(datos["accesorio"]) if datos["accesorio"] in ajustes.ACCESORIOS else 0
        self.zona = "personajes"
        self.tiempo = 0.0
        self.boton = pygame.Rect(ajustes.ANCHO // 2 - 40, 164, 80, 13)

    @property
    def personaje(self):
        return ajustes.ORDEN_PERSONAJES[self.ip]

    @property
    def accesorio(self):
        return ajustes.ORDEN_ACCESORIOS[self.ia]

    def rect_personaje(self, i):
        col, fila = i % 4, i // 4
        return pygame.Rect(self.ORIGEN[0] + col * self.CELDA[0], self.ORIGEN[1] + fila * self.CELDA[1],
                           self.CELDA[0] - 2, self.CELDA[1] - 2)

    def rect_accesorio(self, i):
        return pygame.Rect(8 + i * 76, 118, 74, 42)

    def confirmar(self):
        self.motor.guardar_preferencias(personaje=self.personaje, accesorio=self.accesorio)
        self.motor.nueva_partida()
        self.motor.sonido.efecto("elegir")
        self.motor.cambiar_escena(Juego(self.motor, 0))

    def eventos(self, lista):
        for ev in lista:
            if self._idioma(ev):
                continue
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self.motor.cambiar_escena(Titulo(self.motor))
                    return
                if _enter(ev):
                    self.confirmar()
                    return
                self._mover(ev.key)
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                pos = self.motor.pos_mouse(ev.pos)
                for i in range(8):
                    if self.rect_personaje(i).collidepoint(pos):
                        self.ip, self.zona = i, "personajes"
                        self.motor.sonido.efecto("menu")
                for i in range(4):
                    if self.rect_accesorio(i).collidepoint(pos):
                        self.ia, self.zona = i, "accesorios"
                        self.motor.sonido.efecto("menu")
                if self.boton.collidepoint(pos):
                    self.confirmar()
                    return

    def _idioma(self, ev):
        if _tecla(ev, pygame.K_l):
            self.motor.cambiar_idioma()
            return True
        return False

    def _mover(self, tecla):
        izq = tecla in (pygame.K_LEFT, pygame.K_a)
        der = tecla in (pygame.K_RIGHT, pygame.K_d)
        arriba = tecla in (pygame.K_UP, pygame.K_w)
        abajo = tecla in (pygame.K_DOWN, pygame.K_s)
        if not (izq or der or arriba or abajo):
            return
        self.motor.sonido.efecto("menu")
        if self.zona == "personajes":
            col, fila = self.ip % 4, self.ip // 4
            if izq:
                col = (col - 1) % 4
            elif der:
                col = (col + 1) % 4
            elif arriba:
                fila = max(0, fila - 1)
            elif abajo:
                if fila == 1:
                    self.zona = "accesorios"
                fila = min(1, fila + 1)
            self.ip = fila * 4 + col
        else:
            if izq:
                self.ia = (self.ia - 1) % 4
            elif der:
                self.ia = (self.ia + 1) % 4
            elif arriba:
                self.zona = "personajes"

    def actualizar(self, dt):
        self.tiempo += dt

    def dibujar(self, lienzo):
        lienzo.fill(color(ajustes.COLORES["fondo_menu"]))
        interfaz.tricolor(lienzo, 0, 0, ajustes.ANCHO, 3)
        interfaz.texto(lienzo, textos.t("elige_personaje"), (8, 6), color_texto=ajustes.COLORES["amarillo"])
        negro = color(ajustes.COLORES["negro"])
        for i, clave in enumerate(ajustes.ORDEN_PERSONAJES):
            rect = self.rect_personaje(i)
            elegido = i == self.ip
            pygame.draw.rect(lienzo, negro, rect.inflate(2, 2))
            pygame.draw.rect(lienzo, color("#2C4090" if elegido else "#26346E"), rect)
            if elegido:
                borde = ajustes.COLORES["amarillo"] if self.zona == "personajes" else "#FFFFFF"
                pygame.draw.rect(lienzo, color(borde), rect, 1)
            if elegido:
                cuadro = int(self.tiempo * 8)
                imagen = sprites.personaje(clave, self.accesorio, False, "caminar", cuadro, True)
            else:
                imagen = sprites.personaje(clave, self.accesorio, False, "quieto", 0, True)
            imagen = pygame.transform.scale(imagen, (32, 32))
            lienzo.blit(imagen, (rect.centerx - 16, rect.y + 1))
            interfaz.texto(lienzo, ajustes.PERSONAJES[clave]["nombre"], (rect.centerx, rect.bottom - 11),
                           centrado=True, tam=8)

        # vista previa grande y animada
        caja = pygame.Rect(228, 18, 84, 86)
        pygame.draw.rect(lienzo, negro, caja.inflate(2, 2))
        pygame.draw.rect(lienzo, color("#1B2350"), caja)
        pygame.draw.rect(lienzo, color(ajustes.COLORES["amarillo"]), caja, 1)
        grande = sprites.personaje(self.personaje, self.accesorio, False, "caminar", int(self.tiempo * 8), True)
        grande = pygame.transform.scale(grande, (64, 64))
        lienzo.blit(grande, (caja.centerx - 32, caja.y - 1))
        pygame.draw.rect(lienzo, color("#5A7A3A"), (caja.x + 6, caja.y + 60, caja.w - 12, 3))
        interfaz.texto(lienzo, ajustes.PERSONAJES[self.personaje]["nombre"], (caja.centerx, caja.y + 64),
                       centrado=True, color_texto=ajustes.COLORES["amarillo"])
        interfaz.texto_ajustado(lienzo, textos.t(self.accesorio), caja.centerx, caja.y + 73, caja.w - 6)

        interfaz.texto(lienzo, textos.t("elige_accesorio"), (8, 107), color_texto=ajustes.COLORES["amarillo"])
        for i, clave in enumerate(ajustes.ORDEN_ACCESORIOS):
            rect = self.rect_accesorio(i)
            elegido = i == self.ia
            pygame.draw.rect(lienzo, negro, rect.inflate(2, 2))
            pygame.draw.rect(lienzo, color("#2C4090" if elegido else "#26346E"), rect)
            if elegido:
                borde = ajustes.COLORES["amarillo"] if self.zona == "accesorios" else "#FFFFFF"
                pygame.draw.rect(lienzo, color(borde), rect, 1)
            cabeza = pygame.transform.scale(sprites.cabeza(self.personaje, clave), (32, 20))
            lienzo.blit(cabeza, (rect.centerx - 16, rect.y + 2))
            interfaz.texto_ajustado(lienzo, textos.t(clave), rect.centerx, rect.y + 23, rect.w - 4)

        pygame.draw.rect(lienzo, negro, self.boton.inflate(2, 2))
        pygame.draw.rect(lienzo, color(ajustes.COLORES["rojo"]), self.boton)
        interfaz.texto(lienzo, "Enter - " + textos.t("jugar"), (self.boton.centerx, self.boton.y + 1), centrado=True)
        interfaz.texto(lienzo, textos.t("idioma_tecla"), (ajustes.ANCHO - 4, 6), derecha=True, tam=8,
                       color_texto="#DDE6FF")

    @staticmethod
    def _corto(cadena, maximo=17):
        return cadena if len(cadena) <= maximo else cadena[:maximo - 1] + "."


# ======================================================================
#  Juego
# ======================================================================
class Juego(Escena):
    def __init__(self, motor, indice):
        super().__init__(motor)
        self.indice = indice
        motor.sesion.nivel = indice
        datos = LISTA_NIVELES[indice]
        self.nivel = cargar_nivel(datos, motor.sesion, motor.sonido, motor.datos["personaje"],
                                  motor.datos["accesorio"])
        self.t_cartel = 2.6
        motor.sonido.musica(datos.get("musica", datos["clave"]))

    def eventos(self, lista):
        for ev in lista:
            if _tecla(ev, pygame.K_ESCAPE) and self.nivel.estado == "jugando":
                self.motor.cambiar_escena(Pausa(self.motor, self))
                return

    def actualizar(self, dt):
        self.t_cartel = max(0.0, self.t_cartel - dt)
        self.nivel.actualizar(dt, self.motor.entrada)
        for evento in list(self.nivel.eventos):
            if evento == "nivel_completo":
                self.motor.cambiar_escena(FinNivel(self.motor, self))
            elif evento == "game_over":
                self.motor.cambiar_escena(GameOver(self.motor))
            elif evento == "reaparecer":
                self.motor.sonido.musica(self.nivel.datos.get("musica", self.nivel.datos["clave"]))
        self.nivel.eventos.clear()

    def dibujar(self, lienzo, con_hud=True):
        self.nivel.dibujar(lienzo)
        if not con_hud:
            return
        interfaz.hud(lienzo, self.nivel, self.motor.datos["personaje"], self.motor.datos["accesorio"],
                     self.motor.sonido)
        if self.t_cartel > 0:
            visible = min(1.0, self.t_cartel / 0.5)
            nombre = textos.t(self.nivel.datos["nombre"])
            if visible >= 0.2:
                interfaz.texto_grande(lienzo, nombre, (ajustes.ANCHO // 2, 52), "#FFFFFF", escala=2)
                interfaz.texto(lienzo, "%d / %d" % (self.indice + 1, len(LISTA_NIVELES)),
                               (ajustes.ANCHO // 2, 78), centrado=True)
                if self.nivel.jefe:
                    interfaz.texto(lienzo, textos.t("mensaje_sellos"), (ajustes.ANCHO // 2, 92), centrado=True,
                                   color_texto="#9FE3FF")


# ======================================================================
#  Pausa
# ======================================================================
class Pausa(Escena):
    def __init__(self, motor, juego):
        super().__init__(motor)
        self.juego = juego
        self.menu = Menu(motor, ["continuar", "salir_menu"], y=88, ancho=110)
        self.congelado = None

    def eventos(self, lista):
        for ev in lista:
            if _tecla(ev, pygame.K_ESCAPE):
                self.motor.cambiar_escena(self.juego)
                return
        elegido = self.menu.eventos(lista)
        if elegido == "continuar":
            self.motor.cambiar_escena(self.juego)
        elif elegido == "salir_menu":
            self.motor.sonido.parar_musica()
            self.motor.registrar_puntaje()
            self.motor.cambiar_escena(Titulo(self.motor))

    def dibujar(self, lienzo):
        self.juego.dibujar(lienzo, con_hud=False)
        interfaz.oscurecer(lienzo, 150)
        interfaz.texto_grande(lienzo, textos.t("pausa"), (ajustes.ANCHO // 2, 56), "#FFFFFF", escala=2)
        self.menu.dibujar(lienzo)
        sonido = self.motor.sonido
        musica = "OFF" if sonido.musica_silenciada else "ON"
        efectos = "OFF" if sonido.efectos_silenciados else "ON"
        interfaz.texto(lienzo, "M: %s %s    N: %s %s" % (textos.t("musica"), musica, textos.t("efectos"), efectos),
                       (ajustes.ANCHO // 2, 150), centrado=True, tam=8, color_texto="#DDE6FF")


# ======================================================================
#  Fin de nivel: cuenta animada del bono por tiempo
# ======================================================================
class FinNivel(Escena):
    def __init__(self, motor, juego):
        super().__init__(motor)
        self.juego = juego
        self.nivel = juego.nivel
        self.restante = int(self.nivel.tiempo)
        self.bono = 0
        self.t_cuenta = 0.0
        self.t_final = 0.0
        self.terminado = False
        motor.sonido.efecto("victoria_nivel")

    def _cerrar_cuenta(self):
        self.bono += self.restante * ajustes.PUNTOS_POR_SEGUNDO
        self.motor.sesion.puntaje += self.restante * ajustes.PUNTOS_POR_SEGUNDO
        self.restante = 0
        self.terminado = True

    def _siguiente(self):
        indice = self.juego.indice + 1
        if indice >= len(LISTA_NIVELES):
            self.motor.cambiar_escena(Victoria(self.motor))
        else:
            self.motor.cambiar_escena(Juego(self.motor, indice))

    def eventos(self, lista):
        for ev in lista:
            if _enter(ev) or _tecla(ev, pygame.K_SPACE):
                if not self.terminado:
                    self._cerrar_cuenta()
                    self.t_final = 0.6
                else:
                    self._siguiente()
                    return

    def actualizar(self, dt):
        self.nivel.reloj += dt
        if self.nivel.bandera:
            self.nivel.bandera.actualizar(dt)
        if not self.terminado:
            self.t_cuenta += dt
            while self.t_cuenta >= 0.012 and self.restante > 0:
                self.t_cuenta -= 0.012
                paso = min(self.restante, 2)
                self.restante -= paso
                self.bono += paso * ajustes.PUNTOS_POR_SEGUNDO
                self.motor.sesion.puntaje += paso * ajustes.PUNTOS_POR_SEGUNDO
                if int(self.restante) % 6 == 0:
                    self.motor.sonido.efecto("cuenta")
            if self.restante <= 0:
                self.terminado = True
        else:
            self.t_final += dt
            if self.t_final > 1.4:
                self._siguiente()

    def dibujar(self, lienzo):
        self.nivel.dibujar(lienzo)
        interfaz.oscurecer(lienzo, 150)
        interfaz.texto_grande(lienzo, textos.t("nivel_completo"), (ajustes.ANCHO // 2, 40), "#F6C915", escala=2)
        interfaz.texto(lienzo, "%s: %03d x %d" % (textos.t("tiempo"), self.restante, ajustes.PUNTOS_POR_SEGUNDO),
                       (ajustes.ANCHO // 2, 80), centrado=True)
        interfaz.texto(lienzo, "%s: +%d" % (textos.t("bono_tiempo"), self.bono), (ajustes.ANCHO // 2, 94),
                       centrado=True, color_texto="#9FE3FF")
        interfaz.texto(lienzo, "%s: %06d" % (textos.t("puntaje"), self.motor.sesion.puntaje),
                       (ajustes.ANCHO // 2, 110), centrado=True)
        if int(self.nivel.reloj * 2) % 2 == 0:
            interfaz.texto(lienzo, textos.t("enter_continuar"), (ajustes.ANCHO // 2, 150), centrado=True, tam=8)


# ======================================================================
#  Game Over y Victoria
# ======================================================================
class _Final(Escena):
    TITULO = "game_over"
    COLOR = "#FF6B5A"

    def __init__(self, motor):
        super().__init__(motor)
        self.tiempo = 0.0
        self.record = motor.registrar_puntaje()
        self.menu = Menu(motor, ["salir_menu"], y=140, ancho=110)
        self.confeti = []
        self.azar = random.Random(3)

    def eventos(self, lista):
        for ev in lista:
            if _enter(ev) or _tecla(ev, pygame.K_ESCAPE):
                self.motor.cambiar_escena(Titulo(self.motor))
                return
        if self.menu.eventos(lista):
            self.motor.cambiar_escena(Titulo(self.motor))

    def actualizar(self, dt):
        self.tiempo += dt

    def dibujar_encabezado(self, lienzo):
        interfaz.texto_grande(lienzo, textos.t(self.TITULO), (ajustes.ANCHO // 2, 34), self.COLOR, escala=2)
        interfaz.tricolor(lienzo, ajustes.ANCHO // 2 - 70, 62, 140, 6)
        interfaz.texto(lienzo, "%s: %06d" % (textos.t("puntaje_total"), self.motor.sesion.puntaje),
                       (ajustes.ANCHO // 2, 84), centrado=True)
        interfaz.texto(lienzo, "%s: %06d" % (textos.t("mejor_puntaje"), self.motor.datos.get("mejor_puntaje", 0)),
                       (ajustes.ANCHO // 2, 98), centrado=True, color_texto=ajustes.COLORES["amarillo"])
        if self.record and int(self.tiempo * 3) % 2 == 0:
            interfaz.texto(lienzo, textos.t("nuevo_record"), (ajustes.ANCHO // 2, 114), centrado=True,
                           color_texto="#9FE3FF")


class GameOver(_Final):
    TITULO = "game_over"
    COLOR = "#FF6B5A"

    def dibujar(self, lienzo):
        lienzo.fill(color("#1A1020"))
        fondos.obtener("cotopaxi").dibujar(lienzo, 0, deriva=self.tiempo * 6)
        interfaz.oscurecer(lienzo, 170)
        self.dibujar_encabezado(lienzo)
        self.menu.dibujar(lienzo)


class Victoria(_Final):
    TITULO = "victoria"
    COLOR = "#F6C915"

    def __init__(self, motor):
        super().__init__(motor)
        motor.sonido.musica("victoria")

    def actualizar(self, dt):
        super().actualizar(dt)
        if self.azar.random() < 0.6:
            self.confeti.append([self.azar.uniform(0, ajustes.ANCHO), -4, self.azar.uniform(-10, 10),
                                 self.azar.uniform(25, 55), self.azar.choice(["#F6C915", "#1F3E8C", "#C8242B", "#FFFFFF"])])
        for c in self.confeti:
            c[0] += c[2] * dt
            c[1] += c[3] * dt
        self.confeti = [c for c in self.confeti if c[1] < ajustes.ALTO + 4]

    def dibujar(self, lienzo):
        fondos.obtener("sierra").dibujar(lienzo, 0, deriva=self.tiempo * 15)
        interfaz.oscurecer(lienzo, 110)
        for x, y, vx, vy, c in self.confeti:
            lienzo.fill(color(c), (int(x), int(y), 2, 2))
        lienzo.blit(sprites.bandera_ecuador(36, 24, int(self.tiempo * 5)), (ajustes.ANCHO // 2 - 18, 118))
        self.dibujar_encabezado(lienzo)
        datos = self.motor.datos
        imagen = sprites.personaje(datos["personaje"], datos["accesorio"], False, "saltar" if int(self.tiempo * 3) % 2 == 0 else "quieto", int(self.tiempo * 6), True)
        lienzo.blit(pygame.transform.scale(imagen, (32, 32)), (ajustes.ANCHO // 2 - 70, 122))
        lienzo.blit(pygame.transform.scale(imagen, (32, 32)), (ajustes.ANCHO // 2 + 38, 122))
        self.menu.y = 150
        self.menu.dibujar(lienzo)
