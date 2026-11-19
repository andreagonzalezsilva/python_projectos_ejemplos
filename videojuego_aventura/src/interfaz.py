"""Interfaz: texto nitido, menus, desplegable de idioma y HUD.

El arte vive en el lienzo de 320x180 (pixel art). El TEXTO no: se dibuja en una "capa de texto"
transparente con la resolucion real de la ventana (1280x720, o la de la pantalla completa) y con
suavizado, y se pone encima del arte. Asi las letras se leen con nitidez.
Si no hay capa configurada (por ejemplo una prueba que dibuja en otra superficie), el texto se
dibuja pixelado directamente en el lienzo que se le pase.
"""
import pygame

import ajustes
import letras_inca
import sprites
import textos
from ajustes import color

_FUENTES = {}       # fuentes pequenas, sin suavizado (solo para el modo sin capa)
_FUENTES_HR = {}    # fuentes de alta resolucion
_GRANDES = {}
_TEXTOS = {}        # textos ya dibujados: (cadena, tam, color...) -> (superficie, tamano, sombra)
_PREFERIDAS = ["trebuchetms", "consolas", "dejavusansmono", "lucidaconsole", "arial"]
_CAPA = {"lienzo": None, "capa": None, "rects": []}


# ======================================================================
#  Capa de texto de alta resolucion
# ======================================================================
def configurar_capa(lienzo, capa):
    """Indica que el texto dibujado en 'lienzo' debe ir a 'capa' (Surface con alfa mas grande)."""
    _CAPA["lienzo"] = lienzo
    _CAPA["capa"] = capa
    _CAPA["rects"] = []


def limpiar_capa():
    """Borra solo las zonas donde hubo texto en el cuadro anterior (rapido)."""
    capa = _CAPA["capa"]
    if capa is None:
        return
    for rect in _CAPA["rects"]:
        capa.fill((0, 0, 0, 0), rect)
    _CAPA["rects"] = []


def zonas_de_texto():
    """Rectangulos (en pixeles de la capa) donde hay texto este cuadro."""
    return list(_CAPA["rects"])


def _escala(lienzo):
    """Cuantos pixeles de la capa mide un pixel del lienzo (None si no hay capa para este lienzo)."""
    capa = _CAPA["capa"]
    if capa is not None and lienzo is _CAPA["lienzo"]:
        return capa.get_width() / ajustes.ANCHO
    return None


def reiniciar_fuentes():
    """Vacia las caches (hace falta si pygame se reinicia)."""
    _FUENTES.clear()
    _FUENTES_HR.clear()
    _GRANDES.clear()
    _TEXTOS.clear()


def _buscar_fuente(tam, negrita=False, preferidas=None):
    for nombre in (preferidas or _PREFERIDAS):
        ruta = pygame.font.match_font(nombre, bold=negrita)
        if ruta:
            return pygame.font.Font(ruta, tam)
    return pygame.font.Font(None, tam + 6)


def fuente(tam=9, negrita=False):
    """Fuente pequena del sistema, sin suavizado (modo sin capa)."""
    clave = (tam, negrita)
    if clave not in _FUENTES:
        _FUENTES[clave] = _buscar_fuente(tam, negrita)
    return _FUENTES[clave]


def fuente_hr(tam, escala, negrita=False, titulo=False):
    """Fuente del tamano 'tam' (en pixeles del lienzo) pero dibujada a la resolucion de la capa."""
    px = max(6, int(round(tam * escala)))
    clave = (px, negrita, titulo)
    if clave not in _FUENTES_HR:
        preferidas = ["verdana"] + _PREFERIDAS if titulo else None
        _FUENTES_HR[clave] = _buscar_fuente(px, negrita or titulo, preferidas)
    return _FUENTES_HR[clave]


def ancho_texto(lienzo, cadena, tam=9, negrita=False):
    """Ancho que ocupara un texto, medido en pixeles del lienzo."""
    k = _escala(lienzo)
    if k is None:
        return fuente(tam, negrita).size(str(cadena))[0]
    return fuente_hr(tam, k, negrita).size(str(cadena))[0] / k


def _texto_dibujado(cadena, tam, negrita, color_texto, sombra, k):
    """Dibuja (una sola vez) el texto con su sombra y lo guarda: renderizar fuentes cada cuadro es lo mas caro."""
    clave = (cadena, tam, negrita, color_texto, sombra, int(round(k * 100)))
    hecho = _TEXTOS.get(clave)
    if hecho is None:
        if len(_TEXTOS) > 500:
            _TEXTOS.clear()
        f = fuente_hr(tam, k, negrita)
        base = f.render(cadena, True, color_texto)
        desplazo = max(1, int(round(k * 0.5)))
        if sombra:
            imagen = pygame.Surface((base.get_width() + desplazo, base.get_height() + desplazo), pygame.SRCALPHA)
            imagen.blit(f.render(cadena, True, color(ajustes.COLORES["sombra"])), (desplazo, desplazo))
            imagen.blit(base, (0, 0))
        else:
            imagen = base
        hecho = (imagen, base.get_size(), desplazo)
        _TEXTOS[clave] = hecho
    return hecho


def precalentar(k):
    """Carga las fuentes y sus letras al arrancar, para que el primer texto de cada tamano no frene el juego."""
    letras = "".join(chr(c) for c in range(32, 127)) + "\u00e1\u00e9\u00ed\u00f3\u00fa\u00f1\u00c1\u00c9\u00cd\u00d3\u00da\u00d1\u00a1\u00bf\u00fc\u2013"
    for tam in (8, 9, 12):
        for negrita in (False, True):
            fuente_hr(tam, k, negrita).render(letras, True, (255, 255, 255))
    for escala in (1, 2, 3):
        fuente_hr(8 * escala, k, titulo=True).render(letras, True, (255, 255, 255))


def texto(lienzo, cadena, pos, color_texto="#FFFFFF", tam=9, centrado=False, derecha=False,
          sombra=True, negrita=False):
    """Dibuja texto. pos (en pixeles del lienzo) es la esquina superior izquierda (o el centro/derecha)."""
    if isinstance(color_texto, str):
        color_texto = color(color_texto)
    cadena = str(cadena)
    k = _escala(lienzo)
    if k is None:
        return _texto_pixelado(lienzo, cadena, pos, color_texto, tam, centrado, derecha, sombra, negrita)
    imagen, (ancho_px, alto_px), desplazo = _texto_dibujado(cadena, tam, negrita, color_texto, sombra, k)
    ancho, alto = ancho_px / k, alto_px / k
    x, y = pos
    if centrado:
        x -= ancho / 2
    elif derecha:
        x -= ancho
    px, py = int(round(x * k)), int(round(y * k))
    _CAPA["capa"].blit(imagen, (px, py))
    _CAPA["rects"].append(pygame.Rect(px, py, ancho_px + desplazo, alto_px + desplazo))
    return pygame.Rect(x, y, ancho, alto)


def _texto_pixelado(lienzo, cadena, pos, color_texto, tam, centrado, derecha, sombra, negrita):
    f = fuente(tam, negrita)
    base = f.render(cadena, False, color_texto)
    x, y = pos
    if centrado:
        x -= base.get_width() // 2
    elif derecha:
        x -= base.get_width()
    if sombra:
        lienzo.blit(f.render(cadena, False, color(ajustes.COLORES["sombra"])), (x + 1, y + 1))
    lienzo.blit(base, (x, y))
    return pygame.Rect(x, y, base.get_width(), base.get_height())


def panel(lienzo, rect, alfa=110):
    """Rectangulo oscuro translucido para que el texto se lea sobre cualquier fondo."""
    velo = pygame.Surface(rect.size, pygame.SRCALPHA)
    velo.fill((10, 8, 20, alfa))
    lienzo.blit(velo, rect.topleft)


def texto_grande(lienzo, cadena, pos, color_texto="#F6C915", escala=2, centrado=True):
    """Titulo grande con contorno oscuro. En alta resolucion si hay capa; si no, pixelado. Con cache."""
    k = _escala(lienzo)
    if k is None:
        return _texto_grande_pixelado(lienzo, cadena, pos, color_texto, escala, centrado)
    clave = (cadena, color_texto, escala, int(round(k * 100)))
    if clave not in _GRANDES:
        base = fuente_hr(8 * escala, k, titulo=True).render(str(cadena), True, color(color_texto))
        radio = max(2, int(round(k * 0.6)))
        borde = pygame.mask.from_surface(base, 20).to_surface(setcolor=color(ajustes.COLORES["negro"]),
                                                              unsetcolor=(0, 0, 0, 0))
        final = pygame.Surface((base.get_width() + 2 * radio, base.get_height() + 2 * radio), pygame.SRCALPHA)
        for dx in range(-radio, radio + 1):
            for dy in range(-radio, radio + 1):
                if dx * dx + dy * dy <= radio * radio:
                    final.blit(borde, (radio + dx, radio + dy))
        final.blit(base, (radio, radio))
        _GRANDES[clave] = final
    imagen = _GRANDES[clave]
    x, y = pos
    px, py = int(round(x * k)), int(round(y * k))
    if centrado:
        px -= imagen.get_width() // 2
    _CAPA["capa"].blit(imagen, (px, py))
    _CAPA["rects"].append(pygame.Rect(px, py, imagen.get_width(), imagen.get_height()))
    return pygame.Rect(px / k, py / k, imagen.get_width() / k, imagen.get_height() / k)


def titulo_inca(lienzo, cadena, centro_x, y, alto=18.0, ancho_max=304):
    """Titulo del juego con la tipografia Inca (letras escalonadas doradas y chakanas).

    alto = alto de las letras en pixeles del lienzo. Devuelve el Rect que ocupa (en pixeles del lienzo).
    Si no hay capa de alta resolucion, o la cadena trae letras que la tipografia no tiene,
    se usa el titulo normal.
    """
    k = _escala(lienzo)
    if k is not None:
        clave = ("inca", cadena, alto, ancho_max, int(round(k * 100)))
        if clave not in _GRANDES:
            _GRANDES[clave] = letras_inca.crear_titulo(cadena, alto * k, ancho_max_px=ancho_max * k)
        imagen = _GRANDES[clave]
        if imagen is not None:
            px = int(round(centro_x * k)) - imagen.get_width() // 2
            py = int(round(y * k))
            _CAPA["capa"].blit(imagen, (px, py))
            _CAPA["rects"].append(pygame.Rect(px, py, imagen.get_width(), imagen.get_height()))
            return pygame.Rect(px / k, py / k, imagen.get_width() / k, imagen.get_height() / k)
    return texto_grande(lienzo, cadena, (centro_x, y), "#F6C915", 2)


def _fuente_titulo():
    if "titulo" not in _FUENTES:
        ruta = pygame.font.match_font("verdana", bold=True)
        _FUENTES["titulo"] = pygame.font.Font(ruta, 8) if ruta else fuente(9, True)
    return _FUENTES["titulo"]


def _texto_grande_pixelado(lienzo, cadena, pos, color_texto, escala, centrado):
    clave = (cadena, color_texto, escala)
    if clave not in _GRANDES:
        base = _fuente_titulo().render(str(cadena), False, color(color_texto))
        base = pygame.transform.scale(base, (base.get_width() * escala, base.get_height() * escala))
        borde = pygame.mask.from_surface(base).to_surface(setcolor=color(ajustes.COLORES["negro"]),
                                                          unsetcolor=(0, 0, 0, 0))
        ancho, alto = base.get_size()
        final = pygame.Surface((ancho + 4, alto + 4), pygame.SRCALPHA)
        for dx in (0, 1, 2, 3, 4):
            for dy in (0, 1, 2, 3, 4):
                if (dx, dy) != (2, 2):
                    final.blit(borde, (dx, dy))
        final.blit(base, (2, 2))
        _GRANDES[clave] = final
    imagen = _GRANDES[clave]
    x, y = pos
    if centrado:
        x -= imagen.get_width() // 2
    lienzo.blit(imagen, (x, y))
    return pygame.Rect(x, y, imagen.get_width(), imagen.get_height())


def texto_ajustado(lienzo, cadena, centro_x, y, ancho_max, tam=8, color_texto="#FFFFFF", interlineado=9):
    """Texto centrado que se parte en dos lineas si no cabe. Devuelve cuantas lineas uso."""
    if ancho_texto(lienzo, cadena, tam) <= ancho_max or " " not in cadena:
        texto(lienzo, cadena, (centro_x, y), color_texto, tam=tam, centrado=True)
        return 1
    palabras = cadena.split(" ")
    mejor = None
    for i in range(1, len(palabras)):
        a, b = " ".join(palabras[:i]), " ".join(palabras[i:])
        ancho = max(ancho_texto(lienzo, a, tam), ancho_texto(lienzo, b, tam))
        if mejor is None or ancho < mejor[0]:
            mejor = (ancho, a, b)
    texto(lienzo, mejor[1], (centro_x, y), color_texto, tam=tam, centrado=True)
    texto(lienzo, mejor[2], (centro_x, y + interlineado), color_texto, tam=tam, centrado=True)
    return 2


def triangulo(lienzo, x, y, direccion="derecha", c="#F6C915", tam=4):
    """Pequena flecha dibujada con poligonos (no depende de la fuente)."""
    c = color(c) if isinstance(c, str) else c
    if direccion == "derecha":
        puntos = [(x, y), (x, y + tam * 2), (x + tam, y + tam)]
    elif direccion == "abajo":
        puntos = [(x, y), (x + tam * 2, y), (x + tam, y + tam)]
    else:
        puntos = [(x + tam, y), (x + tam, y + tam * 2), (x, y + tam)]
    pygame.draw.polygon(lienzo, c, puntos)


def tricolor(lienzo, x, y, ancho, alto=6):
    """Franja con los colores de la bandera de Ecuador."""
    mitad = alto // 2
    pygame.draw.rect(lienzo, color(ajustes.COLORES["amarillo"]), (x, y, ancho, mitad))
    pygame.draw.rect(lienzo, color(ajustes.COLORES["azul"]), (x, y + mitad, ancho, (alto - mitad + 1) // 2))
    pygame.draw.rect(lienzo, color(ajustes.COLORES["rojo"]),
                     (x, y + mitad + (alto - mitad + 1) // 2, ancho, alto - mitad - (alto - mitad + 1) // 2))


def oscurecer(lienzo, alfa=140):
    velo = pygame.Surface(lienzo.get_size(), pygame.SRCALPHA)
    velo.fill((10, 8, 20, alfa))
    lienzo.blit(velo, (0, 0))


# ======================================================================
#  Menu vertical de opciones
# ======================================================================
class Menu:
    """Lista de opciones. Se maneja con flechas + Enter o con el mouse."""

    def __init__(self, motor, claves, centro_x=ajustes.ANCHO // 2, y=100, separacion=16, ancho=84):
        self.motor = motor
        self.claves = claves          # claves de textos.py
        self.indice = 0
        self.centro_x = centro_x
        self.y = y
        self.separacion = separacion
        self.ancho = ancho

    def rect_opcion(self, i):
        return pygame.Rect(self.centro_x - self.ancho // 2, self.y + i * self.separacion, self.ancho, 13)

    def eventos(self, lista):
        """Devuelve la clave elegida o None."""
        for ev in lista:
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_UP, pygame.K_w):
                    self.indice = (self.indice - 1) % len(self.claves)
                    self.motor.sonido.efecto("menu")
                elif ev.key in (pygame.K_DOWN, pygame.K_s):
                    self.indice = (self.indice + 1) % len(self.claves)
                    self.motor.sonido.efecto("menu")
                elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    self.motor.sonido.efecto("elegir")
                    return self.claves[self.indice]
            elif ev.type == pygame.MOUSEMOTION:
                pos = self.motor.pos_mouse(ev.pos)
                for i in range(len(self.claves)):
                    if self.rect_opcion(i).collidepoint(pos):
                        self.indice = i
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                pos = self.motor.pos_mouse(ev.pos)
                for i in range(len(self.claves)):
                    if self.rect_opcion(i).collidepoint(pos):
                        self.indice = i
                        self.motor.sonido.efecto("elegir")
                        return self.claves[i]
        return None

    def dibujar(self, lienzo):
        for i, clave in enumerate(self.claves):
            rect = self.rect_opcion(i)
            elegido = i == self.indice
            fondo = ajustes.COLORES["azul"] if elegido else ajustes.COLORES["fondo_menu"]
            pygame.draw.rect(lienzo, color(ajustes.COLORES["negro"]), rect.inflate(2, 2))
            pygame.draw.rect(lienzo, color(fondo), rect)
            if elegido:
                pygame.draw.rect(lienzo, color(ajustes.COLORES["amarillo"]), rect, 1)
                triangulo(lienzo, rect.x + 4, rect.y + 3, "derecha")
            texto(lienzo, textos.t(clave), (rect.centerx, rect.y + 1), centrado=True,
                  color_texto=ajustes.COLORES["amarillo"] if elegido else "#FFFFFF")


# ======================================================================
#  Desplegable de idioma ES / EN (arriba a la derecha)
# ======================================================================
class Desplegable:
    def __init__(self, motor):
        self.motor = motor
        self.abierto = False
        self.cerrado_rect = pygame.Rect(ajustes.ANCHO - 37, 3, 34, 13)
        self.ancho_abierto = 74

    def rects_opciones(self):
        x = ajustes.ANCHO - 3 - self.ancho_abierto
        return [pygame.Rect(x, 3 + 13 * (i + 1), self.ancho_abierto, 13) for i in range(len(textos.IDIOMAS))]

    def eventos(self, lista):
        """Devuelve True si el idioma cambio."""
        for ev in lista:
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                pos = self.motor.pos_mouse(ev.pos)
                if self.cerrado_rect.collidepoint(pos):
                    self.abierto = not self.abierto
                elif self.abierto:
                    for idioma, rect in zip(textos.IDIOMAS, self.rects_opciones()):
                        if rect.collidepoint(pos):
                            self.abierto = False
                            if idioma != textos.IDIOMA_ACTUAL:
                                self.motor.cambiar_idioma(idioma)
                                self.motor.sonido.efecto("elegir")
                                return True
                            return False
                    self.abierto = False
            elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_l:
                self.abierto = False
                self.motor.cambiar_idioma()
                self.motor.sonido.efecto("elegir")
                return True
        return False

    def dibujar(self, lienzo):
        negro = color(ajustes.COLORES["negro"])
        caja = self.cerrado_rect
        if self.abierto:
            caja = pygame.Rect(ajustes.ANCHO - 3 - self.ancho_abierto, 3, self.ancho_abierto, 13)
        pygame.draw.rect(lienzo, negro, caja.inflate(2, 2))
        pygame.draw.rect(lienzo, color(ajustes.COLORES["fondo_menu"]), caja)
        pygame.draw.rect(lienzo, color(ajustes.COLORES["amarillo"]), caja, 1)
        if self.abierto:
            texto(lienzo, textos.NOMBRES_IDIOMA[textos.IDIOMA_ACTUAL], (caja.x + 4, caja.y + 1), sombra=False)
        else:
            texto(lienzo, textos.IDIOMA_ACTUAL.upper(), (caja.x + 5, caja.y + 1), sombra=False)
        triangulo(lienzo, caja.right - 11, caja.y + 4, "abajo", tam=3)
        if self.abierto:
            for idioma, rect in zip(textos.IDIOMAS, self.rects_opciones()):
                activo = idioma == textos.IDIOMA_ACTUAL
                pygame.draw.rect(lienzo, negro, rect.inflate(2, 2))
                pygame.draw.rect(lienzo, color(ajustes.COLORES["azul"] if activo else ajustes.COLORES["fondo_menu"]), rect)
                texto(lienzo, textos.NOMBRES_IDIOMA[idioma], (rect.x + 4, rect.y + 1), sombra=False,
                      color_texto=ajustes.COLORES["amarillo"] if activo else "#FFFFFF")


# ======================================================================
#  HUD
# ======================================================================
_FRANJA = {}


def _franja():
    if "hud" not in _FRANJA:
        s = pygame.Surface((ajustes.ANCHO, 14), pygame.SRCALPHA)
        s.fill((10, 8, 20, 120))
        _FRANJA["hud"] = s
    return _FRANJA["hud"]


def hud(lienzo, nivel, personaje, accesorio, sonido=None):
    """Vidas, puntaje, coleccionables, tiempo y nombre del nivel."""
    sesion = nivel.sesion
    if sonido is not None and sonido.hay_audio and sonido.musica_silenciada:
        texto(lienzo, "M: %s OFF" % textos.t("musica"), (ajustes.ANCHO - 4, 16), derecha=True, tam=8,
              color_texto="#DDE6FF")
    lienzo.blit(_franja(), (0, 0))
    lienzo.blit(sprites.cabeza(personaje, accesorio), (2, 1))
    if nivel.t_vida > 0:
        # vida extra: el contador parpadea en verde y el HUD se ilumina
        brillo = int(nivel.t_vida * 8) % 2 == 0
        velo = pygame.Surface((42, 14), pygame.SRCALPHA)
        velo.fill((60, 200, 60, 150) if brillo else (246, 201, 21, 150))
        lienzo.blit(velo, (0, 0))
        texto(lienzo, "x%d +1" % max(0, sesion.vidas), (20, 2), tam=8, color_texto="#5BE35B" if brillo else "#F6C915")
    else:
        texto(lienzo, "x%d" % max(0, sesion.vidas), (20, 2), tam=8)
    texto(lienzo, "%s %06d" % (textos.t("puntaje"), sesion.puntaje), (44, 2), tam=8)
    clave = nivel.datos.get("coleccionable", "banano")
    if not isinstance(clave, str):
        clave = clave[0]
    lienzo.blit(sprites.coleccionable(clave), (128, 1))
    texto(lienzo, "x%02d" % sesion.coleccionables, (142, 2), tam=8)
    segundos = max(0, int(nivel.tiempo + 0.99))
    color_tiempo = "#FF6B5A" if segundos <= 30 and int(nivel.reloj * 2) % 2 == 0 else "#FFFFFF"
    texto(lienzo, "%s %03d" % (textos.t("tiempo"), segundos), (172, 2), color_texto=color_tiempo, tam=8)
    texto(lienzo, textos.t(nivel.datos["nombre"]), (ajustes.ANCHO - 4, 2), derecha=True, tam=8,
          color_texto=ajustes.COLORES["amarillo"])
    if nivel.t_vida > 0:
        verde = "#7DFF7D" if int(nivel.t_vida * 6) % 2 == 0 else "#F6C915"
        panel(lienzo, pygame.Rect(ajustes.ANCHO // 2 - 56, 22, 112, 16), alfa=150)
        texto(lienzo, textos.t("vida_extra"), (ajustes.ANCHO // 2, 24), color_texto=verde, tam=12, centrado=True,
              negrita=True)
