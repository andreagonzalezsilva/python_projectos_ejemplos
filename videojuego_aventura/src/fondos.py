"""Fondos: cielo con degradado y tres capas de parallax (20 %, 50 % y 80 % de la camara)."""
import math
import random

import pygame

import ajustes
from ajustes import color
from sprites import aclarar, sombrear

ANCHO_CAPA = 480          # las capas se repiten cada 480 px
FACTORES = (0.2, 0.5, 0.8)
_CACHE = {}


# ---------------------------------------------------------------- utilidades
def _cielo(arriba, abajo, bandas=22):
    """Degradado vertical en bandas (se dibuja una sola vez)."""
    superficie = pygame.Surface((ajustes.ANCHO, ajustes.ALTO))
    a, b = color(arriba), color(abajo)
    alto_banda = ajustes.ALTO / bandas
    for i in range(bandas):
        t = i / (bandas - 1)
        c = tuple(int(a[k] + (b[k] - a[k]) * t) for k in range(3))
        pygame.draw.rect(superficie, c, (0, int(i * alto_banda), ajustes.ANCHO, int(alto_banda) + 2))
    return superficie.convert()


def _capa():
    return pygame.Surface((ANCHO_CAPA, ajustes.ALTO), pygame.SRCALPHA)


def _envolver(superficie, dibujo):
    """Ejecuta dibujo(desplazo) tres veces para que la capa se repita sin cortes."""
    for desplazo in (-ANCHO_CAPA, 0, ANCHO_CAPA):
        dibujo(desplazo)


def _nube(s, x, y, ancho=40, c="#FFFFFF", sombra="#DCEBF5"):
    c, sombra = color(c), color(sombra)
    for dx, dy, r in ((0, 0, 7), (ancho * 0.3, -4, 9), (ancho * 0.6, -1, 8), (ancho * 0.85, 2, 6)):
        pygame.draw.circle(s, sombra, (int(x + dx), int(y + dy + 2)), r)
    for dx, dy, r in ((0, 0, 7), (ancho * 0.3, -4, 9), (ancho * 0.6, -1, 8), (ancho * 0.85, 2, 6)):
        pygame.draw.circle(s, c, (int(x + dx), int(y + dy)), r)


def _volcan(s, x, base_y, ancho, alto, roca, nieve, azar):
    pico = (x, base_y - alto)
    izq, der = (x - ancho // 2, base_y), (x + ancho // 2, base_y)
    pygame.draw.polygon(s, roca, [izq, pico, der])
    pygame.draw.polygon(s, sombrear(roca, 0.82), [pico, der, (x + ancho // 6, base_y)])
    corte = base_y - alto + int(alto * 0.38)
    t = (corte - pico[1]) / alto
    xi, xd = x - int(ancho / 2 * t), x + int(ancho / 2 * t)
    puntos = [pico, (xi, corte)]
    n = 6
    for i in range(1, n):
        px = xi + (xd - xi) * i / n
        puntos.append((int(px), corte - 3 + (i % 2) * 7 + azar.randrange(-1, 2)))
    puntos.append((xd, corte))
    pygame.draw.polygon(s, nieve, puntos)
    pygame.draw.polygon(s, sombrear(nieve, 0.9), [pico, (xd, corte), (x + (xd - x) // 3, corte - 2)])


def _palmera(s, x, base_y, alto, inclina, azar):
    tronco, tronco_c = color("#7A5230"), color("#5A3A20")
    puntos = []
    for i in range(0, alto + 1, 3):
        t = i / alto
        px = x + inclina * (t ** 2)
        puntos.append((int(px), int(base_y - i)))
    for a, b in zip(puntos, puntos[1:]):
        pygame.draw.line(s, tronco_c, (a[0] + 1, a[1]), (b[0] + 1, b[1]), 3)
        pygame.draw.line(s, tronco, a, b, 2)
    cima = puntos[-1]
    verde, verde_c = color("#2E8B3A"), color("#1F6B2E")
    for ang in (-170, -140, -110, -70, -40, -10, 20, 160):
        rad = math.radians(ang)
        largo = 20 + azar.randrange(-2, 4)
        ant = cima
        for k in range(1, 6):
            t = k / 5
            px = cima[0] + math.cos(rad) * largo * t
            py = cima[1] + math.sin(rad) * largo * t + 14 * t * t
            pygame.draw.line(s, verde_c, (ant[0], ant[1] + 1), (int(px), int(py) + 1), 3)
            pygame.draw.line(s, verde, ant, (int(px), int(py)), 2)
            ant = (int(px), int(py))
    pygame.draw.circle(s, color("#5A3A20"), (cima[0] - 1, cima[1] + 2), 2)
    pygame.draw.circle(s, color("#5A3A20"), (cima[0] + 2, cima[1] + 2), 2)


def _arbol_amazonia(s, x, alto_tronco, azar, c_tronco="#4A3020", c_copa="#1F6B2E"):
    tronco, copa = color(c_tronco), color(c_copa)
    pygame.draw.rect(s, tronco, (x - 4, 150 - alto_tronco, 8, alto_tronco))
    pygame.draw.rect(s, sombrear(tronco, 0.7), (x + 1, 150 - alto_tronco, 3, alto_tronco))
    pygame.draw.polygon(s, tronco, [(x - 9, 150), (x - 4, 130), (x + 4, 130), (x + 9, 150)])
    for _ in range(7):
        cx = x + azar.randrange(-26, 27)
        cy = 150 - alto_tronco + azar.randrange(-14, 10)
        r = azar.randrange(11, 18)
        pygame.draw.circle(s, sombrear(copa, 0.8), (cx + 1, cy + 3), r)
    for _ in range(7):
        cx = x + azar.randrange(-26, 27)
        cy = 150 - alto_tronco + azar.randrange(-14, 10)
        r = azar.randrange(10, 16)
        pygame.draw.circle(s, copa, (cx, cy), r)
        pygame.draw.circle(s, aclarar(copa, 0.15), (cx - 3, cy - 3), r // 2)


def _casa(s, x, y):
    pygame.draw.rect(s, color("#F4F0E4"), (x, y, 14, 9))
    pygame.draw.rect(s, color("#D8D0BC"), (x + 9, y, 5, 9))
    pygame.draw.polygon(s, color("#B8452E"), [(x - 2, y), (x + 7, y - 7), (x + 16, y)])
    pygame.draw.rect(s, color("#5A3A20"), (x + 3, y + 3, 3, 6))
    pygame.draw.rect(s, color("#5BA0D8"), (x + 9, y + 2, 3, 3))


# ---------------------------------------------------------------- Costa
def _costa():
    azar = random.Random(11)
    lejana = _capa()
    horizonte = 92

    pygame.draw.rect(lejana, color("#5CB8E0"), (0, horizonte, ANCHO_CAPA, 6))
    pygame.draw.rect(lejana, color("#3AA0D8"), (0, horizonte + 6, ANCHO_CAPA, 20))
    pygame.draw.rect(lejana, color("#1E88C8"), (0, horizonte + 26, ANCHO_CAPA, 80))
    for y in range(horizonte + 4, 180, 5):
        for _ in range(7):
            x = azar.randrange(ANCHO_CAPA)
            pygame.draw.line(lejana, aclarar(color("#3AA0D8"), 0.35), (x, y), (x + azar.randrange(5, 12), y))
    pygame.draw.circle(lejana, color("#FFF2B0"), (380, 38), 17)
    pygame.draw.circle(lejana, color("#FFFBE0"), (380, 38), 12)

    def nubes(d):
        _nube(lejana, 40 + d, 30, 44)
        _nube(lejana, 200 + d, 50, 36)
        _nube(lejana, 310 + d, 22, 30)
    _envolver(lejana, nubes)
    for bx in (90, 270):
        pygame.draw.polygon(lejana, color("#FFFFFF"), [(bx, horizonte - 10), (bx, horizonte), (bx + 9, horizonte)])
        pygame.draw.line(lejana, color("#5A3A20"), (bx - 1, horizonte - 11), (bx - 1, horizonte + 1))
        pygame.draw.rect(lejana, color("#5A3A20"), (bx - 4, horizonte, 14, 2))

    media = _capa()

    def palmeras(d):
        for x, alto, inc in ((40, 66, 12), (160, 80, -14), (290, 60, 10), (400, 74, -10)):
            _palmera(media, x + d, 150, alto, inc, azar)
        for x in (100, 220, 350, 450):
            for dx, dy, r in ((0, 0, 9), (9, 2, 8), (-8, 3, 7)):
                pygame.draw.circle(media, color("#1F6B2E"), (x + dx + d, 144 + dy), r)
            for dx, dy, r in ((1, -2, 6), (8, 1, 6), (-7, 1, 5)):
                pygame.draw.circle(media, color("#2E8B3A"), (x + dx + d, 143 + dy), r)
    _envolver(media, palmeras)

    cercana = _capa()

    def olas(d):
        for i in range(0, ANCHO_CAPA, 24):
            x = i + d
            pygame.draw.ellipse(cercana, color("#F4FBFF"), (x, 132, 22, 5))
            pygame.draw.ellipse(cercana, color("#BEE6F6"), (x + 6, 137, 20, 4))
        pygame.draw.rect(cercana, color("#7FCCE8"), (0, 141, ANCHO_CAPA, 3))
        for x in (30, 150, 270, 390):
            pygame.draw.ellipse(cercana, color("#D8BE78"), (x + d, 140, 26, 8))
            pygame.draw.ellipse(cercana, color("#F2DE9C"), (x + d + 2, 139, 20, 5))
            pygame.draw.rect(cercana, color("#7A5230"), (x + d + 10, 126, 1, 14))
            pygame.draw.polygon(cercana, color("#C8242B"), [(x + d + 11, 127), (x + d + 18, 130), (x + d + 11, 133)])
    _envolver(cercana, olas)
    return _cielo("#7ED6F0", "#CFF1FA"), [lejana, media, cercana]


# ---------------------------------------------------------------- Sierra
def _sierra():
    azar = random.Random(22)
    lejana = _capa()
    for x, ancho, alto in ((70, 190, 110), (250, 150, 85), (400, 170, 100)):
        _volcan(lejana, x, 150, ancho, alto, color("#6C7A96"), color("#FFFFFF"), azar)
    _volcan(lejana, 0, 150, 130, 70, color("#7C8AA6"), color("#F4F8FF"), azar)

    def nubes(d):
        _nube(lejana, 160 + d, 26, 40, "#FFFFFF", "#CFE0F2")
        _nube(lejana, 360 + d, 42, 34, "#FFFFFF", "#CFE0F2")
    _envolver(lejana, nubes)

    media = _capa()
    for x in range(0, ANCHO_CAPA + 1):
        y = 122 + math.sin(x * 0.025) * 8 + math.sin(x * 0.07) * 3
        pygame.draw.line(media, color("#5C8A34"), (x, int(y)), (x, 160))
        pygame.draw.line(media, color("#7DB048"), (x, int(y)), (x, int(y) + 1))
    for x in range(0, ANCHO_CAPA + 1):
        y = 135 + math.sin(x * 0.04 + 2) * 6
        pygame.draw.line(media, color("#6B9B3A"), (x, int(y)), (x, 160))
    for x, y in ((60, 116), (210, 124), (380, 117)):
        _casa(media, x, y)
    for x, y in ((100, 124), (250, 121), (330, 125), (440, 121)):
        pygame.draw.rect(media, color("#5A3A20"), (x, y, 2, 10))
        for dx, dy, r in ((0, -4, 5), (-3, 0, 4), (3, 1, 4)):
            pygame.draw.circle(media, color("#2E6B3A"), (x + 1 + dx, y + dy), r)

    cercana = _capa()
    for x in range(0, ANCHO_CAPA + 1):
        y = 142 + math.sin(x * 0.05) * 3
        pygame.draw.line(cercana, color("#4E7A2C"), (x, int(y)), (x, 170))
    for x in range(10, ANCHO_CAPA, 9):
        pygame.draw.line(cercana, color("#8CC04C"), (x, 142), (x + azar.randrange(-2, 3), 136))
        pygame.draw.line(cercana, color("#8CC04C"), (x + 3, 142), (x + 4, 137))
    for x in range(20, ANCHO_CAPA, 35):
        cx = x + azar.randrange(-5, 5)
        cercana.set_at((cx, 140), color("#FFD84A"))
        cercana.set_at((cx + 1, 140), color("#FF9AB0"))
    for x in range(0, ANCHO_CAPA, 60):
        pygame.draw.rect(cercana, color("#7A5230"), (x, 132, 2, 11))
    pygame.draw.line(cercana, color("#7A5230"), (0, 135), (ANCHO_CAPA, 135))
    pygame.draw.line(cercana, color("#7A5230"), (0, 139), (ANCHO_CAPA, 139))
    return _cielo("#3F8FE0", "#9CCBF2"), [lejana, media, cercana]


# ---------------------------------------------------------------- Amazonia
def _amazonia():
    azar = random.Random(33)
    lejana = _capa()
    for x in range(0, ANCHO_CAPA, 14):
        r = azar.randrange(14, 24)
        y = 80 + azar.randrange(-14, 14)
        pygame.draw.circle(lejana, color("#86C48C"), (x, y), r)
        pygame.draw.circle(lejana, color("#86C48C"), (x - ANCHO_CAPA if x < 20 else x, y), r)
    pygame.draw.rect(lejana, color("#86C48C"), (0, 90, ANCHO_CAPA, 90))
    for y in range(70, 150, 12):
        pygame.draw.rect(lejana, (230, 255, 235, 70), (0, y, ANCHO_CAPA, 6))
    pygame.draw.rect(lejana, (214, 245, 220, 110), (0, 110, ANCHO_CAPA, 30))

    media = _capa()
    for x, alto in ((30, 120), (120, 135), (200, 110), (290, 128), (380, 118), (450, 132)):
        _arbol_amazonia(media, x, alto, azar)
    for x in range(10, ANCHO_CAPA, 40):
        largo = azar.randrange(30, 70)
        pts = [(x + math.sin(i * 0.5) * 3, i) for i in range(0, largo, 3)]
        pygame.draw.lines(media, color("#1F4B22"), False, pts, 1)

    cercana = _capa()
    for x in range(0, ANCHO_CAPA, 22):
        largo = azar.randrange(24, 80)
        pts = [(x + math.sin(i * 0.2 + x) * 3, i) for i in range(0, largo, 2)]
        pygame.draw.lines(cercana, color("#2E7A32"), False, pts, 2)
        pygame.draw.circle(cercana, color("#C060D0"), (int(pts[-1][0]), int(pts[-1][1])), 2)
    for x in range(0, ANCHO_CAPA, 38):
        for ang in (-60, -25, 15, 55):
            rad = math.radians(ang - 90)
            punta = (x + math.cos(rad) * 24, 148 + math.sin(rad) * 20)
            pygame.draw.polygon(cercana, color("#2F8A3A"), [(x, 150), (punta[0] - 3, punta[1]), (punta[0] + 3, punta[1] + 2)])
            pygame.draw.line(cercana, color("#58B860"), (x, 150), punta)
    return _cielo("#A8D8A0", "#5FAE6B"), [lejana, media, cercana]


# ---------------------------------------------------------------- Galapagos
def _galapagos():
    azar = random.Random(44)
    lejana = _capa()
    pygame.draw.rect(lejana, color("#6FD0D2"), (0, 100, ANCHO_CAPA, 80))
    pygame.draw.rect(lejana, color("#2BB5C0"), (0, 118, ANCHO_CAPA, 62))
    pygame.draw.circle(lejana, color("#FFE0A0"), (120, 92), 20)
    pygame.draw.circle(lejana, color("#FFF4D0"), (120, 92), 14)
    pygame.draw.rect(lejana, color("#6FD0D2"), (0, 100, ANCHO_CAPA, 80))
    pygame.draw.rect(lejana, color("#2BB5C0"), (0, 118, ANCHO_CAPA, 62))
    for x, ancho, alto in ((70, 90, 24), (260, 120, 30), (410, 70, 18)):
        pygame.draw.ellipse(lejana, color("#5C6A7A"), (x - ancho // 2, 100 - alto + 6, ancho, alto * 2 - 10))
    pygame.draw.rect(lejana, color("#6FD0D2"), (0, 100, ANCHO_CAPA, 80))
    pygame.draw.rect(lejana, color("#2BB5C0"), (0, 118, ANCHO_CAPA, 62))
    for x, ancho, alto in ((70, 90, 24), (260, 120, 30), (410, 70, 18)):
        pygame.draw.polygon(lejana, color("#5C6A7A"),
                            [(x - ancho // 2, 101), (x - ancho // 4, 101 - alto), (x + ancho // 6, 101 - alto + 6),
                             (x + ancho // 2, 101)])
    for y in range(104, 180, 6):
        for _ in range(6):
            x = azar.randrange(ANCHO_CAPA)
            pygame.draw.line(lejana, aclarar(color("#2BB5C0"), 0.4), (x, y), (x + azar.randrange(4, 10), y))

    def nubes(d):
        _nube(lejana, 30 + d, 36, 40, "#FFF0DC", "#F2CFA6")
        _nube(lejana, 300 + d, 28, 36, "#FFF0DC", "#F2CFA6")
    _envolver(lejana, nubes)

    media = _capa()
    for x in range(0, ANCHO_CAPA + 1):
        y = 118 + math.sin(x * 0.05) * 6 + math.sin(x * 0.27) * 2
        pygame.draw.line(media, color("#2E2E38"), (x, int(y)), (x, 160))
        pygame.draw.line(media, color("#3E3E4A"), (x, int(y)), (x, int(y) + 1))
    for x in (50, 170, 300, 420):
        base = 126
        pygame.draw.rect(media, color("#5A4A30"), (x, base - 10, 4, 12))
        # palas del cactus: ovalos verticales apilados, con espinas
        for dx, dy, ancho, alto in ((-1, -22, 8, 12), (-9, -18, 6, 9), (7, -26, 7, 12), (3, -36, 7, 11)):
            pygame.draw.ellipse(media, color("#4E8A2A"), (x + dx, base + dy, ancho, alto))
            pygame.draw.ellipse(media, color("#6FA83A"), (x + dx + 1, base + dy + 1, ancho - 3, alto - 3))
            for sy in range(2, alto - 1, 3):
                media.set_at((x + dx + ancho // 2, base + dy + sy), color("#F4F0C8"))
    cercana = _capa()
    for x in range(0, ANCHO_CAPA):
        y = 140 + math.sin(x * 0.09) * 5 + math.sin(x * 0.31) * 2
        pygame.draw.line(cercana, color("#24242C"), (x, int(y)), (x, 170))
        pygame.draw.line(cercana, color("#4A4A56"), (x, int(y)), (x, int(y)))
    return _cielo("#F6C98A", "#7FD3D8"), [lejana, media, cercana]


# ---------------------------------------------------------------- Cotopaxi
def _cotopaxi():
    azar = random.Random(55)
    lejana = _capa()
    for _ in range(40):
        x, y = azar.randrange(ANCHO_CAPA), azar.randrange(0, 80)
        lejana.set_at((x, y), color("#FFB070") if azar.random() < 0.5 else color("#FF8A60"))
    for x in range(0, ANCHO_CAPA + 1):
        y = 110 + math.sin(x * 0.03) * 12 + math.sin(x * 0.11) * 5
        pygame.draw.line(lejana, color("#5A2A3A"), (x, int(y)), (x, 180))
    pygame.draw.rect(lejana, (255, 138, 31, 90), (0, 128, ANCHO_CAPA, 12))

    media = _capa()
    for x, ancho, alto in ((60, 120, 70), (200, 150, 90), (340, 130, 66), (450, 100, 56)):
        _volcan(media, x, 150, ancho, alto, color("#3A3040"), color("#E8EEF5"), azar)
    cercana = _capa()

    def humo(d):
        for x, y, r in ((40, 120, 18), (130, 135, 22), (230, 118, 16), (330, 132, 24), (420, 122, 18)):
            for dx, dy, rr in ((0, 0, r), (r * 0.8, 3, r * 0.8), (-r * 0.7, 4, r * 0.7)):
                pygame.draw.circle(cercana, (46, 36, 52, 150), (int(x + dx + d), int(y + dy)), int(rr))
    _envolver(cercana, humo)
    for x in range(0, ANCHO_CAPA):
        y = 150 + math.sin(x * 0.2) * 2
        pygame.draw.line(cercana, (255, 138, 31, 160), (x, int(y)), (x, 160))
    return _cielo("#3B1A2A", "#C4452B"), [lejana, media, cercana]


_CREADORES = {
    "costa": _costa,
    "sierra": _sierra,
    "amazonia": _amazonia,
    "galapagos": _galapagos,
    "cotopaxi": _cotopaxi,
}


class Fondo:
    """Cielo + tres capas de parallax de una region."""

    def __init__(self, region):
        cielo, capas = _CREADORES[region]()
        self.region = region
        self.cielo = cielo
        self.capas = [c.convert_alpha() for c in capas]

    def dibujar(self, lienzo, cam_x, deriva=0.0):
        lienzo.blit(self.cielo, (0, 0))
        for capa, factor in zip(self.capas, FACTORES):
            x0 = int(-(cam_x + deriva * (factor + 0.3)) * factor) % ANCHO_CAPA
            lienzo.blit(capa, (x0 - ANCHO_CAPA, 0))
            lienzo.blit(capa, (x0, 0))


def obtener(region):
    """Devuelve el fondo de la region (se crea una sola vez)."""
    if region not in _CACHE:
        _CACHE[region] = Fondo(region)
    return _CACHE[region]


def generar_todos():
    for region in _CREADORES:
        obtener(region)


def reiniciar():
    _CACHE.clear()

