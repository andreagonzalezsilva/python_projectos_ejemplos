"""Tipografia "Inca" generada por codigo (sin descargar fuentes).

Cada letra es un diccionario de trazos sobre una cuadricula: en vez de diagonales usa ESCALERAS,
como las piramides escalonadas y las puertas trapezoidales del arte andino. Los trazos son
rectangulos, asi que a cualquier resolucion los bordes salen limpios. El acabado es dorado con
bisel, contorno oscuro y sombra. Tambien dibuja la chakana (la cruz escalonada andina).
"""
import pygame

# ---------------------------------------------------------------- medidas (en "unidades")
GROSOR = 0.95                      # grosor del trazo
ANCHO_LETRA = 4 + GROSOR           # una letra ocupa 4 unidades de camino + el grosor
ALTO_LETRA = 6 + GROSOR
SEPARACION = 1.0                   # espacio entre letras
ESPACIO = 3.0                      # espacio entre palabras

# ---------------------------------------------------------------- las letras
# Cada glifo es una lista de lineas quebradas; cada linea es una lista de puntos (x, y)
# con x de 0 a 4 e y de 0 a 6. Los tramos son siempre horizontales o verticales.
GLIFOS = {
    "A": [[(0, 6), (0, 4), (1, 4), (1, 2), (2, 2), (2, 0), (2, 2), (3, 2), (3, 4), (4, 4), (4, 6)],
          [(1, 4), (3, 4)]],
    "B": [[(0, 0), (0, 6)],
          [(0, 0), (3, 0), (3, 1), (4, 1), (4, 2), (3, 2), (3, 3), (0, 3)],
          [(3, 3), (3, 4), (4, 4), (4, 5), (3, 5), (3, 6), (0, 6)]],
    "C": [[(4, 1), (3, 1), (3, 0), (1, 0), (1, 1), (0, 1), (0, 5), (1, 5), (1, 6), (3, 6), (3, 5), (4, 5)]],
    "D": [[(0, 0), (0, 6)],
          [(0, 0), (2.6, 0), (2.6, 1), (4, 1), (4, 5), (2.6, 5), (2.6, 6), (0, 6)]],
    "E": [[(4, 0), (0, 0), (0, 6), (4, 6)], [(0, 3), (3, 3)]],
    "F": [[(4, 0), (0, 0), (0, 6)], [(0, 3), (3, 3)]],
    "G": [[(4, 1), (3, 1), (3, 0), (1, 0), (1, 1), (0, 1), (0, 5), (1, 5), (1, 6), (3, 6), (3, 5), (4, 5),
           (4, 3), (2, 3)]],
    "H": [[(0, 0), (0, 6)], [(4, 0), (4, 6)], [(0, 3), (4, 3)]],
    "I": [[(0, 0), (4, 0)], [(2, 0), (2, 6)], [(0, 6), (4, 6)]],
    "J": [[(4, 0), (4, 5), (3, 5), (3, 6), (1, 6), (1, 5), (0, 5)]],
    "K": [[(0, 0), (0, 6)],
          [(0, 3), (1, 3), (1, 2), (2, 2), (2, 1), (3, 1), (3, 0), (4, 0)],
          [(1, 3), (1, 4), (2, 4), (2, 5), (3, 5), (3, 6), (4, 6)]],
    "L": [[(0, 0), (0, 6), (4, 6)]],
    "M": [[(0, 6), (0, 0), (1, 0), (1, 2), (2, 2), (2, 4), (2, 2), (3, 2), (3, 0), (4, 0), (4, 6)]],
    "N": [[(0, 6), (0, 0), (1, 0), (1, 2), (2, 2), (2, 4), (3, 4), (3, 6), (4, 6), (4, 0)]],
    "O": [[(1, 0), (3, 0), (3, 1), (4, 1), (4, 5), (3, 5), (3, 6), (1, 6), (1, 5), (0, 5), (0, 1), (1, 1), (1, 0)]],
    "P": [[(0, 6), (0, 0), (3, 0), (3, 1), (4, 1), (4, 2), (3, 2), (3, 3), (0, 3)]],
    "Q": [[(1, 0), (3, 0), (3, 1), (4, 1), (4, 5), (3, 5), (3, 6), (1, 6), (1, 5), (0, 5), (0, 1), (1, 1), (1, 0)],
          [(2, 4), (3, 4), (3, 5), (4, 5), (4, 6)]],
    "R": [[(0, 6), (0, 0), (3, 0), (3, 1), (4, 1), (4, 2), (3, 2), (3, 3), (0, 3)],
          [(1, 3), (1, 4), (2, 4), (2, 5), (3, 5), (3, 6), (4, 6)]],
    "S": [[(4, 1), (3, 1), (3, 0), (1, 0), (1, 1), (0, 1), (0, 2), (1, 2), (1, 3), (3, 3), (3, 4), (4, 4),
           (4, 5), (3, 5), (3, 6), (1, 6), (1, 5), (0, 5)]],
    "T": [[(0, 0), (4, 0)], [(2, 0), (2, 6)]],
    "U": [[(0, 0), (0, 5), (1, 5), (1, 6), (3, 6), (3, 5), (4, 5), (4, 0)]],
    "V": [[(0, 0), (0, 2), (1, 2), (1, 4), (2, 4), (2, 6), (2, 4), (3, 4), (3, 2), (4, 2), (4, 0)]],
    "W": [[(0, 0), (0, 6), (1, 6), (1, 4), (2, 4), (2, 2), (2, 4), (3, 4), (3, 6), (4, 6), (4, 0)]],
    "X": [[(0, 0), (1, 0), (1, 2), (2, 2), (2, 4), (3, 4), (3, 6), (4, 6)],
          [(4, 0), (3, 0), (3, 2), (2, 2), (2, 4), (1, 4), (1, 6), (0, 6)]],
    "Y": [[(0, 0), (0, 2), (1, 2), (1, 3), (3, 3), (3, 2), (4, 2), (4, 0)], [(2, 3), (2, 6)]],
    "Z": [[(0, 0), (4, 0), (4, 1), (3, 1), (3, 2), (2, 2), (2, 4), (1, 4), (1, 5), (0, 5), (0, 6), (4, 6)]],
}

# Chakana: la cruz escalonada andina. Rectangulos (x0, y0, x1, y1) en una cuadricula de 11x11:
# dos brazos de 3 de ancho y un cuadrado central que forma los escalones de las esquinas.
CHAKANA = [(4, 0, 7, 11), (0, 4, 11, 7), (2, 2, 9, 9)]
CHAKANA_HUECO = [(5, 5, 6, 6)]
CHAKANA_CUADRICULA = 11

# ---------------------------------------------------------------- colores
ORO_ARRIBA = (255, 238, 150)
ORO_MEDIO = (246, 201, 21)
ORO_ABAJO = (186, 112, 8)
BRILLO = (255, 250, 210)
SOMBRA_BISEL = (140, 80, 0)
CONTORNO = (38, 20, 8)


def soporta(cadena):
    """True si todas las letras de la cadena existen en la tipografia."""
    return all(c == " " or c.upper() in GLIFOS for c in cadena)


def ancho_en_unidades(cadena):
    total = 0.0
    for c in cadena:
        total += ESPACIO if c == " " else ANCHO_LETRA + SEPARACION
    return total - SEPARACION if cadena and cadena[-1] != " " else total


def _rects_glifo(letra, x0, y0, u):
    rects = []
    for linea in GLIFOS[letra]:
        for (xa, ya), (xb, yb) in zip(linea, linea[1:]):
            izq = x0 + min(xa, xb) * u
            der = x0 + (max(xa, xb) + GROSOR) * u
            arriba = y0 + min(ya, yb) * u
            abajo = y0 + (max(ya, yb) + GROSOR) * u
            rects.append(pygame.Rect(round(izq), round(arriba), round(der) - round(izq),
                                     round(abajo) - round(arriba)))
    return rects


def _degradado(tam, y_arriba, y_abajo):
    """Superficie opaca con el degradado dorado vertical."""
    ancho, alto = tam
    s = pygame.Surface(tam, pygame.SRCALPHA)
    for y in range(alto):
        t = min(1.0, max(0.0, (y - y_arriba) / max(1, y_abajo - y_arriba)))
        if t < 0.45:
            a, b, f = ORO_ARRIBA, ORO_MEDIO, t / 0.45
        else:
            a, b, f = ORO_MEDIO, ORO_ABAJO, (t - 0.45) / 0.55
        c = tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3))
        pygame.draw.line(s, (*c, 255), (0, y), (ancho, y))
    return s


def _tintar(mascara, c):
    """Copia de una mascara blanca con otro color (se conserva la transparencia)."""
    s = mascara.copy()
    relleno = pygame.Surface(s.get_size(), pygame.SRCALPHA)
    relleno.fill((*c, 255))
    s.blit(relleno, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return s


def _borde(mascara, dx, dy):
    """Franja de la mascara que queda al correrla (dx, dy): sirve para el bisel."""
    corrida = pygame.Surface(mascara.get_size(), pygame.SRCALPHA)
    corrida.blit(mascara, (dx, dy))
    franja = mascara.copy()
    franja.blit(corrida, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
    return franja


def _acabado(mascara, caja, u):
    """Convierte una mascara blanca en una pieza dorada con bisel, contorno y sombra."""
    ancho, alto = mascara.get_size()
    radio = max(2, int(round(u * 0.28)))
    bisel = max(1, int(round(u * 0.2)))

    contorno = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    oscuro = _tintar(mascara, CONTORNO)
    for dx in range(-radio, radio + 1):
        for dy in range(-radio, radio + 1):
            if dx * dx + dy * dy <= radio * radio:
                contorno.blit(oscuro, (dx, dy))
    sombra = _tintar(contorno, (0, 0, 0))
    velo = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    velo.fill((255, 255, 255, 120))
    sombra.blit(velo, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    oro = _degradado((ancho, alto), caja.top, caja.bottom)
    oro.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    luz = _tintar(_borde(mascara, bisel, bisel), BRILLO)
    umbra = _tintar(_borde(mascara, -bisel, -bisel), SOMBRA_BISEL)

    final = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    final.blit(sombra, (radio, radio + radio // 2))
    final.blit(contorno, (0, 0))
    final.blit(oro, (0, 0))
    final.blit(umbra, (0, 0))
    final.blit(luz, (0, 0))
    return final


def _chakana_rects(x0, y0, lado):
    celda = lado / float(CHAKANA_CUADRICULA)
    def r(c):
        izq, arr = x0 + round(c[0] * celda), y0 + round(c[1] * celda)
        return pygame.Rect(izq, arr, x0 + round(c[2] * celda) - izq, y0 + round(c[3] * celda) - arr)
    return [r(c) for c in CHAKANA], [r(c) for c in CHAKANA_HUECO]


def crear_titulo(cadena, alto_px, con_chakana=True, ancho_max_px=None):
    """Titulo dorado de 'alto_px' pixeles de alto de letra. Devuelve None si hay letras sin glifo."""
    cadena = cadena.upper()
    if not soporta(cadena):
        return None
    u = alto_px / ALTO_LETRA
    ancho_texto = ancho_en_unidades(cadena) * u
    lado_chakana = alto_px * 1.05
    hueco = u * 2.2
    ancho_total = ancho_texto + (2 * (lado_chakana + hueco) if con_chakana else 0)
    if ancho_max_px and ancho_total > ancho_max_px:
        return crear_titulo(cadena, alto_px * ancho_max_px / ancho_total, con_chakana, None)

    margen = int(u * 1.2) + 4
    ancho = int(round(ancho_total)) + 2 * margen
    alto = int(round(max(alto_px, lado_chakana))) + 2 * margen
    mascara = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    blanco = (255, 255, 255, 255)
    centro_y = alto / 2
    x = margen + (lado_chakana + hueco if con_chakana else 0)
    y0 = centro_y - alto_px / 2
    for letra in cadena:
        if letra == " ":
            x += ESPACIO * u
            continue
        for rect in _rects_glifo(letra, x, y0, u):
            pygame.draw.rect(mascara, blanco, rect)
        x += (ANCHO_LETRA + SEPARACION) * u
    if con_chakana:
        for izq in (margen, margen + ancho_total - lado_chakana):
            relleno, huecos = _chakana_rects(int(round(izq)), int(round(centro_y - lado_chakana / 2)),
                                             int(round(lado_chakana)))
            for rect in relleno:
                pygame.draw.rect(mascara, blanco, rect)
            for rect in huecos:
                pygame.draw.rect(mascara, (0, 0, 0, 0), rect)
    caja = pygame.Rect(0, int(y0), ancho, int(alto_px))
    return _acabado(mascara, caja, u)
