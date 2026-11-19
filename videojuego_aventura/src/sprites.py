"""Arte procedural (pixel art generado por codigo) y cache de sprites.

Los sprites se escriben como mapas de pixeles de texto: cada caracter es un color
de una paleta (diccionario). Todo se genera UNA sola vez con iniciar() y se guarda
en el diccionario CACHE. Los personajes se arman con capas: cuerpo + cabello + accesorio.
"""
import math
import random
import time

import pygame

import ajustes
from ajustes import color

CACHE = {}

NEGRO = color("#14121C")


# ======================================================================
#  Herramientas
# ======================================================================
def sombrear(c, factor=0.75):
    """Oscurece un color."""
    return tuple(max(0, min(255, int(v * factor))) for v in c[:3])


def aclarar(c, cantidad=0.25):
    """Mezcla un color con blanco."""
    return tuple(int(v + (255 - v) * cantidad) for v in c[:3])


def f(n, s, ancho=16):
    """Fila de ancho fijo: n puntos (transparente) + s + puntos hasta completar."""
    fila = ("." * n + s).ljust(ancho, ".")
    if len(fila) != ancho:
        raise ValueError("fila de sprite demasiado ancha (%d): %r" % (len(fila), fila))
    return fila


def paleta_a_rgb(paleta):
    """Convierte los colores '#RRGGBB' de una paleta a tuplas."""
    salida = {}
    for letra, valor in paleta.items():
        salida[letra] = color(valor) if isinstance(valor, str) else valor
    return salida


def capa_exacta(filas, paleta, ancho=16):
    """Convierte un mapa de texto en Surface. Las filas deben medir exactamente 'ancho'."""
    paleta = paleta_a_rgb(paleta)
    superficie = pygame.Surface((ancho, len(filas)), pygame.SRCALPHA)
    for y, fila in enumerate(filas):
        if len(fila) != ancho:
            raise ValueError("fila %d mide %d, debe medir %d: %r" % (y, len(fila), ancho, fila))
        for x, letra in enumerate(fila):
            if letra in paleta:
                superficie.set_at((x, y), paleta[letra])
    return superficie.convert_alpha()


def contornear(superficie, c=NEGRO):
    """Agrega un contorno oscuro de 1 px alrededor de los pixeles visibles."""
    ancho, alto = superficie.get_size()
    copia = superficie.copy()
    for y in range(alto):
        for x in range(ancho):
            if superficie.get_at((x, y)).a > 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < ancho and 0 <= ny < alto and superficie.get_at((nx, ny)).a > 0:
                    copia.set_at((x, y), c)
                    break
    return copia


def desde_texto(filas, paleta, ancho=16, alto=16, contorno=True, ancla="abajo"):
    """Mapa de texto de tamano libre -> Surface ancho x alto, centrado y con contorno."""
    paleta = paleta_a_rgb(paleta)
    w = max(len(r) for r in filas)
    h = len(filas)
    superficie = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    ox = (ancho - w) // 2
    oy = alto - h - 1 if ancla == "abajo" else (alto - h) // 2
    for y, fila in enumerate(filas):
        for x, letra in enumerate(fila):
            if letra in paleta:
                superficie.set_at((ox + x, oy + y), paleta[letra])
    if contorno:
        superficie = contornear(superficie)
    return superficie.convert_alpha()


def voltear(superficie):
    return pygame.transform.flip(superficie, True, False)


def par(superficie):
    """(izquierda, derecha): los sprites se dibujan mirando a la derecha."""
    return (voltear(superficie), superficie)


def estirar(superficie, extra):
    """Crea una version mas alta repitiendo filas. extra = {fila: copias_adicionales}."""
    ancho, alto = superficie.get_size()
    nuevo_alto = alto + sum(extra.values())
    nueva = pygame.Surface((ancho, nuevo_alto), pygame.SRCALPHA)
    destino = 0
    for y in range(alto):
        veces = 1 + extra.get(y, 0)
        for _ in range(veces):
            nueva.blit(superficie, (0, destino), pygame.Rect(0, y, ancho, 1))
            destino += 1
    return nueva.convert_alpha()


# ======================================================================
#  Personajes: cuerpo + cabello + accesorio
# ======================================================================
def _cabeza_torso():
    return [
        f(0, ""),
        f(0, ""),
        f(4, "oooooooo"),
        f(4, "osssssso"),
        f(4, "osssssso"),
        f(4, "ossesseo"),
        f(4, "ossssmso"),
        f(5, "oSSSSo"),
        f(3, "o" + "c" * 8 + "o"),
        f(3, "os" + "c" * 6 + "so"),
        f(3, "os" + "C" * 6 + "so"),
        f(4, "o" + "P" + "p" * 4 + "Po"),
    ]


_PIERNAS = {
    "quieto": [
        f(4, "oppppppo"),
        f(4, "opp" + "oo" + "ppo"),
        f(3, "ozzzo" + "ozzzo"),
        f(3, "o" * 10),
    ],
    "paso_a": [
        f(4, "oppppppo"),
        f(3, "oppo" + "." + "oppo"),
        f(2, "ozzzo" + "." + "ozzzo"),
        f(2, "ooooo" + "." + "ooooo"),
    ],
    "paso_b": [
        f(4, "oppppppo"),
        f(5, "opppppo"),
        f(4, "ozzzzzzo"),
        f(4, "oooooooo"),
    ],
    "paso_c": [
        f(4, "oppppppo"),
        f(4, "oppo" + "." + "oppo"),
        f(3, "ozzzo" + "." + "ozzzo"),
        f(3, "ooooo" + "." + "ooooo"),
    ],
    "salto": [
        f(4, "oppppppo"),
        f(3, "oppo" + "..." + "oppo"),
        f(2, "ozzo" + "...." + "ozzzzo"),
        f(0, ""),
    ],
    "caida": [
        f(4, "oppppppo"),
        f(3, "oppo" + "." + "oppo"),
        f(3, "ozzo" + "." + "ozzo"),
        f(0, ""),
    ],
}

# variantes del salto y la caida: otra posicion de las piernas para cada cuadro
_PIERNAS["salto_a"] = _PIERNAS["salto"]
_PIERNAS["salto_b"] = [
    f(4, "oppppppo"),
    f(3, "oppo" + "..." + "oppo"),
    f(2, "ozzzzo" + "...." + "ozzo"),
    f(0, ""),
]
_PIERNAS["caida_a"] = _PIERNAS["caida"]
_PIERNAS["caida_b"] = [
    f(4, "oppppppo"),
    f(2, "oppo" + "...." + "oppo"),
    f(2, "ozzo" + "...." + "ozzo"),
    f(0, ""),
]

# Brazos: cada fila lista las columnas 0-4 (la mitad derecha es el espejo). '.' = no tocar.
# salto: brazos arriba (cuadro a y b se alternan, como celebrando); caida: brazos abiertos que aletean.
_BRAZOS = {
    "salto_a": {0: ".oooo", 1: ".osso", 2: ".osso", 3: ".osso", 4: ".osso", 5: ".osso", 6: ".osso",
                7: ".osso", 8: ".osss"},
    "salto_b": {0: "ooo..", 1: "osso.", 2: "osso.", 3: ".osso", 4: ".osso", 5: ".osso", 6: ".osso",
                7: ".osso", 8: ".osss"},
    "caida_a": {5: "oooo.", 6: "osss.", 7: "ossso", 8: "ooo.."},
    "caida_b": {3: "oooo.", 4: "osss.", 5: "ossso", 6: "ooo.."},
}
_TORSO_ESTRECHO = {"salto_a", "salto_b"}      # con los brazos arriba el torso se ve mas angosto


def _con_brazos(filas, cuadro):
    for n, parte in _BRAZOS.get(cuadro, {}).items():
        fila = list(filas[n])
        for i, letra in enumerate(parte):
            if letra != ".":
                fila[i] = letra
                fila[15 - i] = letra
        filas[n] = "".join(fila)
    if cuadro in _TORSO_ESTRECHO:
        filas[9] = f(4, "o" + "c" * 6 + "o")
        filas[10] = f(4, "o" + "C" * 6 + "o")
    return filas


_PEINADOS = {
    "corto": [
        f(0, ""),
        f(5, "oooooo"),
        f(4, "o" + "h" * 6 + "o"),
        f(4, "o" + "h" * 6),
        f(4, "ohH"),
        f(4, "oh"),
    ],
    "largo_ondulado": [
        f(0, ""),
        f(5, "oooooo"),
        f(3, "o" + "h" * 7 + "o"),
        f(3, "o" + "hHhhhhh"),
        f(3, "ohhH"),
        f(2, "ohhHh"),
        f(2, "oHhhh"),
        f(2, "ohhHho"),
        f(1, "ohHho"),
        f(1, "ohHo"),
        f(1, "oHhho"),
        f(2, "ohho"),
        f(2, "ooo"),
    ],
    "cola": [
        f(0, ""),
        f(5, "oooooo"),
        f(4, "o" + "h" * 6 + "o"),
        f(2, "oaho" + "h" * 5),
        f(1, "ohHho" + "h"),
        f(1, "ohhho"),
        f(1, "oHho"),
        f(2, "oho"),
        f(2, "oo"),
    ],
    "trenza_larga": [
        f(0, ""),
        f(5, "oooooo"),
        f(4, "o" + "h" * 6 + "o"),
        f(3, "o" + "hhhhhhh"),
        f(3, "ohhH"),
        f(2, "ohHh"),
        f(2, "oHhh"),
        f(2, "ohHo"),
        f(1, "ohHo"),
        f(1, "oHho"),
        f(1, "ohHo"),
        f(1, "oaao"),
        f(1, "ooo"),
    ],
    "rizado_grande": [
        f(4, "oooooooo"),
        f(2, "o" + "hhHhhhhHhh" + "o"),
        f(1, "o" + "hhhhHhhhhhH" + "o"),
        f(1, "o" + "hhhHhhhhhh"),
        f(1, "ohhhhHh"),
        f(1, "ohHhhh"),
        f(1, "ohhhh"),
        f(2, "ohho"),
    ],
    "trenza_corta": [
        f(0, ""),
        f(5, "oooooo"),
        f(4, "o" + "h" * 6 + "o"),
        f(3, "o" + "hhhhhhh"),
        f(3, "ohhH"),
        f(2, "ohHh"),
        f(2, "oHho"),
        f(2, "oaao"),
        f(2, "ooo"),
    ],
    "rizado_corto": [
        f(5, "ohohoh"),
        f(4, "o" + "hHhhHh" + "o"),
        f(4, "o" + "h" * 6 + "o"),
        f(4, "o" + "hhHhhh"),
        f(4, "ohH"),
        f(4, "oh"),
    ],
}

_ACCESORIOS = {
    "poncho": (
        {"o": "#14121C", "r": "#C8242B", "R": "#8E1A20", "y": "#F6C915"},
        {
            8: f(3, "o" + "r" * 8 + "o"),
            9: f(2, "o" + "r" * 10 + "o"),
            10: f(2, "o" + "rr" + "yyyyyy" + "rr" + "o"),
            11: f(2, "o" + "RrRrRrRrRr" + "o"),
            12: f(2, "R.R.R.R.R.R."),
        },
    ),
    "toquilla": (
        {"o": "#14121C", "b": "#F6EBC0", "B": "#C9AE6A", "k": "#14121C"},
        {
            0: f(5, "oBBBBo"),
            1: f(4, "o" + "bbbbbb" + "o"),
            2: f(4, "o" + "kkkkkk" + "o"),
            3: f(1, "o" + "b" * 12 + "o"),
            4: f(2, "B" * 3 + "." * 6 + "B" * 3),
        },
    ),
    "otavalo": (
        {"o": "#14121C", "d": "#2B2B33", "D": "#4A4A58", "g": "#D8D8E4"},
        {
            0: f(5, "oooooo"),
            1: f(4, "o" + "dDdddd" + "o"),
            2: f(2, "o" + "dd" + "gggggg" + "dd" + "o"),
            3: f(3, "o" + "dd" + "oooo" + "dd" + "o"),
        },
    ),
    "chullo": (
        {"o": "#14121C", "R": "#D8332B", "Y": "#F6C915", "B": "#2A62C9", "W": "#F4F4F4",
         "G": "#3CA64A"},
        {
            0: f(6, "oWWo"),
            1: f(4, "oRYRYRYo"),
            2: f(4, "oBWBWBWo"),
            3: "..." + "oRR" + "....." + "RRo" + "..",
            4: "..." + "oYY" + "....." + "YYo" + "..",
            5: "..." + "oGo" + "....." + "oGo" + "..",
        },
    ),
}


def _capa_filas(filas_dict, paleta):
    """Superficie 16x16 a partir de un diccionario {numero_de_fila: fila}."""
    superficie = pygame.Surface((16, 16), pygame.SRCALPHA)
    filas = [f(0, "")] * 16
    filas = list(filas)
    for n, fila in filas_dict.items():
        filas[n] = fila
    return capa_exacta(filas, paleta)


def _capa_cabello(peinado, cabello_hex):
    base = color(cabello_hex)
    paleta = {"o": NEGRO, "h": base, "H": aclarar(base, 0.22), "a": color("#C8242B")}
    filas = {n: fila for n, fila in enumerate(_PEINADOS[peinado])}
    return _capa_filas(filas, paleta)


def _capa_accesorio(clave):
    paleta, filas = _ACCESORIOS[clave]
    return _capa_filas(filas, paleta)


def _capa_cuerpo(piel_hex, cuadro):
    """Cuerpo desnudo de cabello y accesorio, con la ropa compartida."""
    piel = color(piel_hex)
    paleta = {
        "o": NEGRO, "s": piel, "S": sombrear(piel, 0.8), "e": NEGRO,
        "m": sombrear(piel, 0.55),
        "c": color(ajustes.ROPA["camiseta"]), "C": sombrear(color(ajustes.ROPA["camiseta"]), 0.8),
        "p": color(ajustes.ROPA["pantalon"]), "P": sombrear(color(ajustes.ROPA["pantalon"]), 0.8),
        "z": color(ajustes.ROPA["zapatos"]),
    }
    filas = _con_brazos(_cabeza_torso(), cuadro)
    filas = filas + _PIERNAS[cuadro]
    return capa_exacta(filas, paleta)


# la fila que se repite para crecer: torso (9) y piernas (13)
_ESTIRAR_GRANDE = {9: 7, 13: 9}

_CUADROS = {
    "quieto": ["quieto"],
    "caminar": ["paso_a", "paso_b", "paso_c", "paso_b"],
    "saltar": ["salto_a", "salto_b"],
    "caer": ["caida_a", "caida_b"],
}


def _generar_personajes():
    cuerpos = {}
    for piel in {datos["piel"] for datos in ajustes.PERSONAJES.values()}:
        for cuadro in _PIERNAS:
            cuerpos[(piel, cuadro)] = _capa_cuerpo(piel, cuadro)
    cabellos = {}
    for clave, datos in ajustes.PERSONAJES.items():
        cabellos[clave] = _capa_cabello(datos["peinado"], datos["cabello"])
    accesorios = {clave: _capa_accesorio(clave) for clave in ajustes.ACCESORIOS}

    personajes = {}
    cabezas = {}
    for clave, datos in ajustes.PERSONAJES.items():
        for acc in ajustes.ACCESORIOS:
            por_tam = {"pequeno": {}, "grande": {}}
            for anim, cuadros in _CUADROS.items():
                lista_peq, lista_gra = [], []
                for cuadro in cuadros:
                    s = pygame.Surface((16, 16), pygame.SRCALPHA)
                    s.blit(cuerpos[(datos["piel"], cuadro)], (0, 0))
                    s.blit(cabellos[clave], (0, 0))
                    s.blit(accesorios[acc], (0, 0))
                    s = s.convert_alpha()
                    lista_peq.append(par(s))
                    lista_gra.append(par(estirar(s, _ESTIRAR_GRANDE)))
                por_tam["pequeno"][anim] = lista_peq
                por_tam["grande"][anim] = lista_gra
            personajes[(clave, acc)] = por_tam
            cabeza = pygame.Surface((16, 10), pygame.SRCALPHA)
            cabeza.blit(por_tam["pequeno"]["quieto"][0][1], (0, 0))
            cabezas[(clave, acc)] = cabeza.convert_alpha()
    CACHE["personajes"] = personajes
    CACHE["cabezas"] = cabezas


# ======================================================================
#  Enemigos (mapas de texto de tamano libre, con contorno automatico)
# ======================================================================
def _generar_enemigos():
    enemigos = {}

    pal_cangrejo = {"r": "#E0482E", "R": "#A82C1C", "l": "#F4885A", "w": "#FFFFFF", "k": "#14121C"}
    cangrejo_a = [
        "ll.........ll",
        "lrl.......lrl",
        ".rr..w.w..rr.",
        "..rr.k.k.rr..",
        "..rrrrrrrrr..",
        ".rrrrrrrrrrr.",
        "RrrlrrrrlrrrR",
        ".RrrrrrrrrrR.",
        "R.R.R...R.R.R",
    ]
    cangrejo_b = [
        ".............",
        "ll.........ll",
        "lrr..w.w..rrl",
        ".rr..k.k..rr.",
        "..rrrrrrrrr..",
        ".rrrrrrrrrrr.",
        "RrrlrrrrlrrrR",
        ".RrrrrrrrrrR.",
        ".R.R.R.R.R.R.",
    ]
    cangrejo_muerto = [
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        "RRRRRRRRRRRRR",
        "rrlrrrrrrlrrr",
        "xRRrrrrrrRRxx",
    ]
    pal_cangrejo["x"] = "#A82C1C"
    enemigos["cangrejo"] = {
        "caminar": [par(desde_texto(cangrejo_a, pal_cangrejo)), par(desde_texto(cangrejo_b, pal_cangrejo))],
        "aplastado": [par(desde_texto(cangrejo_muerto, pal_cangrejo))],
    }

    pal_condor = {"k": "#2A2A36", "K": "#46465A", "w": "#F4F4F4", "y": "#F2B632", "r": "#C8242B"}
    condor_a = [
        "k...........k",
        "kk.........kk",
        "kKk.......kKk",
        ".kKkk.kk.kkKk",
        "..kKkkkkkkKk.",
        "...kkkkkwwk..",
        "....kkkkkkyy.",
        ".....kkkkk.y.",
        "......y.y....",
    ]
    condor_b = [
        ".............",
        ".............",
        "..........k..",
        "kk..kkkkk.kk.",
        "kKkkKkkkkkKkk",
        ".kKkkkkkwwKk.",
        "..kkkkkkkkyy.",
        "...kkkkkk..y.",
        "......y.y....",
    ]
    enemigos["condor"] = {
        "volar": [par(desde_texto(condor_a, pal_condor)), par(desde_texto(condor_b, pal_condor))],
        "aplastado": [par(desde_texto(condor_b, pal_condor))],
    }

    pal_mono = {"b": "#8A5A32", "B": "#5E3A1E", "t": "#E2B98A", "k": "#14121C", "w": "#FFFFFF"}
    mono_a = [
        "...bbbb.....",
        "..bbbbbb....",
        "..btwtwtb...",
        "..bttkttb..B",
        "...tttt...BB",
        "..bbbbbb.B..",
        ".bbbbbbbbB..",
        ".bbtttbbb...",
        "..bbtttbb...",
        "..bb..bb....",
        ".BBB..BBB...",
    ]
    mono_b = [
        "...bbbb.....",
        "..bbbbbb....",
        "..btwtwtb...",
        "..bttkttb..B",
        "...tttt...BB",
        "..bbbbbb.B..",
        ".bbbbbbbbB..",
        ".bbtttbbb...",
        "..bbtttbb...",
        "...bbbb.....",
        "...BBBB.....",
    ]
    enemigos["mono"] = {
        "caminar": [par(desde_texto(mono_a, pal_mono)), par(desde_texto(mono_b, pal_mono))],
        "aplastado": [par(desde_texto(["", "", "", "", "", "", "", "", "BBBBBBBBBB.", "bbbtttbbbb.", "bbbbbbbbbbb"], pal_mono))],
    }

    pal_iguana = {"g": "#5C9E3A", "G": "#3A6E26", "y": "#C8D858", "k": "#14121C", "r": "#C8242B",
                  "s": "#F6C915"}
    iguana_a = [
        ".........gg.....",
        "......gGgggg....",
        ".....ggggkggg...",
        ".G..ggggggggrr..",
        "GgGgggggggggg...",
        ".GgggggggGgg....",
        "..gggyyyggg.....",
        "..gg.gg.gg.g....",
        ".GG..GG.GG.GG...",
    ]
    iguana_b = [
        ".........gg.....",
        "......gGgggg....",
        ".....ggggkggg...",
        "GG..ggggggggrr..",
        ".gGgggggggggg...",
        "..Gggggggggg....",
        "..gggyyyggg.....",
        "...gg.gg.gg.....",
        "...GG.GG..GG....",
    ]
    iguana_mareada = [
        "................",
        "................",
        "...s.....s......",
        "......s.........",
        "................",
        "GGGGGGGGGgggg...",
        "gGgggggggggggg..",
        "gggyyygggxkgggg.",
        "GGGGGGGGGGGGGG..",
    ]
    pal_iguana["x"] = "#14121C"
    enemigos["iguana"] = {
        "caminar": [par(desde_texto(iguana_a, pal_iguana)), par(desde_texto(iguana_b, pal_iguana))],
        "aturdida": [par(desde_texto(iguana_mareada, pal_iguana))],
        "aplastado": [par(desde_texto(iguana_mareada, pal_iguana))],
    }

    # proyectiles del jefe: ceniza y roca (16x16, sin voltear)
    pal_ceniza = {"g": "#4A4650", "G": "#2E2A33", "n": "#FF8A1F", "y": "#FFD24A", "k": "#14121C"}
    ceniza = [
        "....GGGGGG....",
        "..GGggggggGG..",
        ".GggggnnggggG.",
        ".GgggnyyngggG.",
        "GggggnyynggggG",
        "GgggggnnggggGG",
        ".GggggggggggG.",
        "..GGggggggGG..",
        "....GGGGGG....",
    ]
    roca = [
        "...kkkkk...",
        "..kBbbbbkk.",
        ".kBbbbBbbbk",
        ".kbbBbbbbbk",
        "kbbbbbbBbbk",
        "kbBbbbbbbbk",
        ".kbbbbBbbk.",
        "..kkbbbkk..",
    ]
    pal_roca = {"k": "#14121C", "b": "#6B5A4A", "B": "#4A3C30"}
    enemigos["ceniza"] = {"caer": [par(desde_texto(ceniza, pal_ceniza, contorno=True))]}
    enemigos["roca"] = {"caer": [par(desde_texto(roca, pal_roca, contorno=False))]}
    CACHE["enemigos"] = enemigos


# ======================================================================
#  Comidas, coleccionables, bloques, banderas
# ======================================================================
def _generar_comidas():
    comidas = {}
    pal = {"g": "#E8B030", "G": "#F8D868", "d": "#B07818", "q": "#FFF4C8", "w": "#E8E8F0",
           "y": "#F2C04A", "Y": "#FFE9A0", "D": "#C88A28", "s": "#FFFFFF",
           "v": "#2E8B3A", "V": "#1B5E27", "t": "#D2B070", "u": "#7A3AA8", "U": "#4F2078",
           "p": "#B068E0", "b": "#EAD2A0", "B": "#C69A5E", "r": "#F26B21", "R": "#C8481A",
           "l": "#9ED63A", "L": "#6AA81E", "c": "#F4F4F4", "C": "#9AB4DA", "k": "#14121C"}
    bolon = [
        "...w..w....",
        "....w..w...",
        "...........",
        "...gggggg..",
        "..gGGggqgg.",
        ".gGggggggqg",
        ".ggggqgggGg",
        ".gqgggggggg",
        ".ggggggqggg",
        ".gdgggggggd",
        "..dddddddd.",
        "...dddddd..",
    ]
    empanada = [
        "...yyyyyyy...",
        ".yyYYyyysyyy.",
        "yyYsyyyyyysyy",
        "yyyyyysyyyyyy",
        "yyysyyyyyysyy",
        "yDyDyDyDyDyDy",
        ".DDDDDDDDDDD.",
    ]
    maito = [
        "..tt....tt..",
        "...tVvvVt...",
        ".vvvvvvvvvv.",
        "VvVvvvvVvvvV",
        "VvvvvvvvvvvV",
        "tttttttttttt",
        "VvvvVvvvvvvV",
        "VvvvvvvvVvvV",
        ".VvvvvvvvvV.",
        "..VVVVVVVV..",
    ]
    ceviche = [
        "..rr.rr.l...",
        ".rRrrRrLLl..",
        "rrRrrrrLlLl.",
        "rrrrRrrlLLl.",
        "cccccccccccc",
        ".CcccccccccC",
        "..CccccccCC.",
        "...CCCCCCC..",
    ]
    colada = [
        "....bb.....",
        "...bBBb....",
        "..bbbbbb...",
        "...bbbb....",
        "..bbbbbb...",
        ".uuuuuuuuu.",
        "uppuuuuuuUu",
        "uuuuuuuuuUu",
        ".uuuuuuuUu.",
        "..UuuuuUU..",
        "...UUUUU...",
    ]
    comidas["bolon"] = desde_texto(bolon, pal)
    comidas["empanada_viento"] = desde_texto(empanada, pal)
    comidas["maito"] = desde_texto(maito, pal)
    comidas["ceviche"] = desde_texto(ceviche, pal)
    comidas["colada_morada"] = desde_texto(colada, pal)
    CACHE["comidas"] = comidas

    pal_c = {"y": "#F6D52A", "Y": "#FFF080", "o": "#B8941A", "m": "#7A4A22", "M": "#A8662F",
             "n": "#4A2A14", "r": "#E0304A", "R": "#A01C30", "v": "#2E8B3A", "p": "#C060D0",
             "P": "#8A38A0", "w": "#FFFFFF", "k": "#F4B8C8", "a": "#FF9AA8", "h": "#9FE3FF",
             "H": "#4FB8E8", "b": "#E0F6FF", "g": "#6FB040"}
    banano = [
        "......yy..",
        ".....yYy..",
        "....yYyy..",
        "...yYyy...",
        "..yYyyo...",
        ".yyyyoo...",
        "yyyyoo....",
        "ooo.......",
    ]
    cacao = [
        "...mm.....",
        "..mMmMm...",
        ".mMmMmMm..",
        ".mMMmMMm..",
        ".mMmMmMm..",
        ".mMMmMMm..",
        "..mMmMm...",
        "...nmn....",
    ]
    rosa = [
        "...rrr....",
        "..rRrRr...",
        "..rrrRr...",
        "..rRrrr...",
        "...rrr.vv.",
        "....v.vv..",
        "...vv.....",
        "....v.....",
    ]
    orquidea = [
        "..pp..pp..",
        ".pPpppPpp.",
        ".ppwwwwpp.",
        "..pwPPwp..",
        "...pwwp...",
        "....pp....",
        "....g.....",
        "...gg.....",
    ]
    concha = [
        "...kkkk...",
        "..kakkak..",
        ".kakkkkak.",
        ".kkakkakk.",
        ".kakkkkak.",
        "..kkkkkk..",
        "...kkkk...",
    ]
    sello = [
        "....hh....",
        ".h..hh..h.",
        "..h.hh.h..",
        "...hbbh...",
        "hhhbbbbhhh",
        "hhhbbbbhhh",
        "...hbbh...",
        "..h.hh.h..",
        ".h..hh..h.",
        "....hh....",
    ]
    cole = {
        "banano": desde_texto(banano, pal_c, 12, 12, ancla="centro"),
        "cacao": desde_texto(cacao, pal_c, 12, 12, ancla="centro"),
        "rosa": desde_texto(rosa, pal_c, 12, 12, ancla="centro"),
        "orquidea": desde_texto(orquidea, pal_c, 12, 12, ancla="centro"),
        "concha": desde_texto(concha, pal_c, 12, 12, ancla="centro"),
        "sello_hielo": desde_texto(sello, pal_c, 12, 12, ancla="centro"),
    }
    CACHE["coleccionables"] = cole
    # sello de hielo grande para el jefe (16x16): se activa al tocarlo
    pal_s = {"h": "#9FE3FF", "H": "#4FB8E8", "b": "#FFFFFF", "k": "#14121C", "g": "#6C7A96"}
    sello_grande = [
        ".......hh.......",
        "...h...hh...h...",
        "....h..hh..h....",
        ".....h.hh.h.....",
        "......hbbh......",
        ".hhhhhbbbbhhhhh.",
        ".hhhhhbbbbhhhhh.",
        "......hbbh......",
        ".....h.hh.h.....",
        "....h..hh..h....",
        "...h...hh...h...",
        ".......hh.......",
    ]
    apagado = [f.replace("h", "g").replace("b", "H") for f in sello_grande]
    CACHE["sello_jefe"] = {
        "activo": desde_texto(sello_grande, pal_s, contorno=True, ancla="centro"),
        "apagado": desde_texto(apagado, pal_s, contorno=True, ancla="centro"),
    }


_SIGNO = [
    "..kkkkkkkk..",
    ".kkwwwwwwkk.",
    ".kkwkkkkwkk.",
    ".kkkkkkkwkk.",
    "...kkkkwkk..",
    "....kwwk....",
    "....kwk.....",
    "............",
    "....kwk.....",
    "....kkk.....",
]


def _generar_bloques():
    # ladrillo
    ladrillo = pygame.Surface((16, 16))
    ladrillo.fill(color("#2A1A14"))
    base, claro = color("#C8602E"), color("#E88A52")
    for fila in range(4):
        y = fila * 4
        desfase = 0 if fila % 2 == 0 else 4
        for x0 in range(-8 + desfase, 16, 8):
            rect = pygame.Rect(x0 + 1, y + 1, 7, 3)
            rect = rect.clip(pygame.Rect(0, 0, 16, 16))
            pygame.draw.rect(ladrillo, base, rect)
            pygame.draw.line(ladrillo, claro, (rect.x, rect.y), (rect.right - 1, rect.y))
    # signo de pregunta (bloque ?) en 4 cuadros que "brillan"
    signos = []
    for cuadro in range(4):
        s = pygame.Surface((16, 16))
        s.fill(color("#2A1A14"))
        pygame.draw.rect(s, color("#E8A820"), (1, 1, 14, 14))
        pygame.draw.rect(s, color("#F8D060"), (1, 1, 14, 1))
        pygame.draw.rect(s, color("#F8D060"), (1, 1, 1, 14))
        pygame.draw.rect(s, color("#B07810"), (1, 14, 14, 1))
        pygame.draw.rect(s, color("#B07810"), (14, 1, 1, 14))
        for px, py in ((2, 2), (13, 2), (2, 13), (13, 13)):
            s.set_at((px, py), color("#7A4A08"))
        glifo = desde_texto(_SIGNO, {"k": "#7A4A08", "w": "#FFF6C0" if cuadro != 2 else "#FFFFFF"},
                            contorno=False, ancla="centro")
        s.blit(glifo, (1, 1))
        if cuadro == 2:
            pygame.draw.rect(s, color("#FFFFFF"), (3, 3, 2, 1))
        signos.append(s.convert())
    usado = pygame.Surface((16, 16))
    usado.fill(color("#2A1A14"))
    pygame.draw.rect(usado, color("#8A7A6A"), (1, 1, 14, 14))
    pygame.draw.rect(usado, color("#A89A8A"), (1, 1, 14, 1))
    pygame.draw.rect(usado, color("#6A5A4A"), (1, 14, 14, 1))
    for px, py in ((3, 3), (12, 3), (3, 12), (12, 12)):
        usado.set_at((px, py), color("#4A3A2A"))
    CACHE["bloques"] = {"ladrillo": ladrillo.convert(), "signo": signos, "usado": usado.convert()}

    fragmento = pygame.Surface((4, 4))
    fragmento.fill(color("#C8602E"))
    pygame.draw.rect(fragmento, color("#E88A52"), (0, 0, 4, 1))
    CACHE["fragmento"] = fragmento.convert()


def bandera_ecuador(ancho, alto, cuadro=0):
    """Bandera tricolor: amarillo (mitad), azul y rojo, con escudo simple. Ondea con 'cuadro'."""
    superficie = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    amarillo, azul, rojo = color("#F6C915"), color("#1F3E8C"), color("#C8242B")
    mitad = alto // 2
    cuarto = (alto - mitad) // 2
    pygame.draw.rect(superficie, amarillo, (0, 0, ancho, mitad))
    pygame.draw.rect(superficie, azul, (0, mitad, ancho, cuarto))
    pygame.draw.rect(superficie, rojo, (0, mitad + cuarto, ancho, alto - mitad - cuarto))
    cx, cy = ancho // 2, alto // 2
    if ancho >= 10:
        pygame.draw.ellipse(superficie, color("#5BA0D8"), (cx - 2, cy - 2, 4, 5))
        pygame.draw.rect(superficie, color("#7A4A22"), (cx - 1, cy + 1, 2, 1))
        superficie.set_at((cx, cy - 1), color("#FFFFFF"))
    ondulada = pygame.Surface((ancho, alto + 2), pygame.SRCALPHA)
    for x in range(ancho):
        desplazo = int(round(math.sin(x * 0.7 + cuadro * math.pi / 2) * 1))
        ondulada.blit(superficie, (x, 1 + desplazo), pygame.Rect(x, 0, 1, alto))
    return ondulada.convert_alpha()


def _generar_banderas():
    # meta: mastil de 5 baldosas con bandera de Ecuador en lo alto
    alto = 96
    cuadros = []
    for cuadro in range(4):
        s = pygame.Surface((16, alto), pygame.SRCALPHA)
        pygame.draw.rect(s, color("#14121C"), (3, 4, 4, alto - 4))
        pygame.draw.rect(s, color("#D8D8E4"), (4, 4, 2, alto - 4))
        pygame.draw.circle(s, color("#14121C"), (5, 3), 3)
        pygame.draw.circle(s, color("#F6C915"), (5, 3), 2)
        s.blit(bandera_ecuador(10, 8, cuadro), (6, 6))
        cuadros.append(s.convert_alpha())
    CACHE["bandera_meta"] = cuadros
    # la meta animada: el mastil solo y la tela aparte (la tela sube por el mastil)
    mastil = pygame.Surface((16, alto), pygame.SRCALPHA)
    pygame.draw.rect(mastil, color("#14121C"), (3, 4, 4, alto - 4))
    pygame.draw.rect(mastil, color("#D8D8E4"), (4, 4, 2, alto - 4))
    pygame.draw.circle(mastil, color("#14121C"), (5, 3), 3)
    pygame.draw.circle(mastil, color("#F6C915"), (5, 3), 2)
    CACHE["bandera_mastil"] = mastil.convert_alpha()
    CACHE["bandera_tela"] = [bandera_ecuador(10, 8, cuadro) for cuadro in range(4)]
    # checkpoint: banderita pequena (apagada = blanca, activa = tricolor)
    apagada = pygame.Surface((16, 16), pygame.SRCALPHA)
    pygame.draw.rect(apagada, color("#14121C"), (4, 1, 3, 15))
    pygame.draw.rect(apagada, color("#A0A0B0"), (5, 1, 1, 15))
    pygame.draw.rect(apagada, color("#14121C"), (6, 2, 8, 6))
    pygame.draw.rect(apagada, color("#E0E0EA"), (7, 3, 6, 4))
    activas = []
    for cuadro in range(4):
        s = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.rect(s, color("#14121C"), (4, 1, 3, 15))
        pygame.draw.rect(s, color("#A0A0B0"), (5, 1, 1, 15))
        s.blit(bandera_ecuador(7, 5, cuadro), (7, 2))
        activas.append(s.convert_alpha())
    CACHE["checkpoint"] = {"apagado": apagada.convert_alpha(), "activo": activas}


# ======================================================================
#  Terreno por region
# ======================================================================
def _ruido(superficie, base_color, semilla, cantidad=22, variacion=0.12, rect=None):
    azar = random.Random(semilla)
    rect = rect or superficie.get_rect()
    for _ in range(cantidad):
        x = azar.randrange(rect.x, rect.right)
        y = azar.randrange(rect.y, rect.bottom)
        if azar.random() < 0.5:
            superficie.set_at((x, y), sombrear(base_color, 1 - variacion))
        else:
            superficie.set_at((x, y), aclarar(base_color, variacion))


_TERRENO = {
    # clave: (relleno, borde_superior, detalle_superior, plataforma, plataforma_borde, agua)
    "costa": ("#E8D08A", "#F6E6AE", "#D2B66A", "#9A6A3A", "#C48A52", "#1E88C8"),
    "sierra": ("#7A5230", "#6B9B3A", "#8CC04C", "#8A8A98", "#B4B4C4", "#2A6AB0"),
    "amazonia": ("#5A3D24", "#1F6B2E", "#3C9A48", "#7A5230", "#9A6E40", "#3E8E7E"),
    "galapagos": ("#34343E", "#4A4A56", "#62626E", "#4A4A56", "#6C6C7A", "#2BB5C0"),
    "cotopaxi": ("#2E2A33", "#E8EEF5", "#FFFFFF", "#9FE3FF", "#DFF6FF", "#FF8A1F"),
}


def _generar_terreno(region):
    relleno_h, borde_h, detalle_h, plat_h, platb_h, agua_h = _TERRENO[region]
    relleno, borde, detalle = color(relleno_h), color(borde_h), color(detalle_h)
    semilla = hash(region) & 0xFFFF

    inter = pygame.Surface((16, 16))
    inter.fill(relleno)
    _ruido(inter, relleno, semilla, 26)
    if region == "costa":
        for x, y in ((3, 5), (10, 9), (6, 13)):
            inter.set_at((x, y), color("#C8AC62"))
    if region in ("galapagos", "cotopaxi"):
        azar = random.Random(semilla + 1)
        for _ in range(3):
            x = azar.randrange(1, 12)
            y = azar.randrange(2, 13)
            pygame.draw.line(inter, sombrear(relleno, 0.7), (x, y), (x + 3, y + azar.randrange(-1, 3)))
    tope = inter.copy()
    azar = random.Random(semilla + 2)
    if region == "costa":
        pygame.draw.rect(tope, borde, (0, 0, 16, 3))
        pygame.draw.rect(tope, detalle, (0, 3, 16, 1))
        for _ in range(5):
            tope.set_at((azar.randrange(16), azar.randrange(3)), detalle)
    else:
        alto_borde = 4 if region in ("sierra", "amazonia") else 3
        pygame.draw.rect(tope, borde, (0, 0, 16, alto_borde))
        for x in range(16):
            largo = alto_borde + azar.randrange(0, 3)
            pygame.draw.line(tope, borde, (x, 0), (x, largo - 1))
            if azar.random() < 0.4:
                tope.set_at((x, 0), detalle)
        pygame.draw.line(tope, sombrear(borde, 0.7), (0, alto_borde + 1), (15, alto_borde + 1))
    # plataforma flotante
    plat = pygame.Surface((16, 16))
    plat.fill(color("#14121C"))
    pbase, pborde = color(plat_h), color(platb_h)
    pygame.draw.rect(plat, pbase, (0, 0, 16, 16))
    if region == "costa":
        for y in (0, 5, 10):
            pygame.draw.rect(plat, sombrear(pbase, 0.7), (0, y + 4, 16, 1))
            pygame.draw.rect(plat, pborde, (0, y, 16, 1))
        pygame.draw.line(plat, sombrear(pbase, 0.7), (8, 0), (8, 15))
    elif region == "sierra":
        pygame.draw.rect(plat, pborde, (0, 0, 16, 2))
        pygame.draw.rect(plat, sombrear(pbase, 0.75), (0, 8, 16, 1))
        pygame.draw.rect(plat, sombrear(pbase, 0.75), (8, 0, 1, 8))
        pygame.draw.rect(plat, sombrear(pbase, 0.75), (4, 9, 1, 7))
        pygame.draw.rect(plat, sombrear(pbase, 0.75), (12, 9, 1, 7))
    elif region == "amazonia":
        pygame.draw.rect(plat, pborde, (0, 0, 16, 2))
        for y in (4, 8, 12):
            pygame.draw.line(plat, sombrear(pbase, 0.7), (0, y), (15, y))
        pygame.draw.rect(plat, color("#3C9A48"), (0, 0, 16, 2))
        for x in (2, 7, 12):
            plat.set_at((x, 2), color("#3C9A48"))
    elif region == "galapagos":
        _ruido(plat, pbase, semilla + 5, 20, 0.2)
        pygame.draw.rect(plat, pborde, (0, 0, 16, 2))
    else:
        pygame.draw.rect(plat, pborde, (0, 0, 16, 2))
        pygame.draw.line(plat, color("#FFFFFF"), (2, 4), (6, 8))
        pygame.draw.line(plat, color("#6AB8E0"), (0, 15), (15, 15))
    pygame.draw.rect(plat, color("#14121C"), (0, 15, 16, 1))
    pygame.draw.rect(plat, color("#14121C"), (0, 0, 1, 16))
    pygame.draw.rect(plat, color("#14121C"), (15, 0, 1, 16))
    pygame.draw.rect(plat, color("#14121C"), (0, 0, 16, 1))
    # agua o lava: 4 cuadros
    agua_c = color(agua_h)
    aguas = []
    for cuadro in range(4):
        s = pygame.Surface((16, 16), pygame.SRCALPHA)
        s.fill((*sombrear(agua_c, 0.8), 255))
        for x in range(16):
            ola = int(round(math.sin((x + cuadro * 4) * 0.4) * 1.2))
            pygame.draw.line(s, (*aclarar(agua_c, 0.35), 255), (x, 2 + ola), (x, 3 + ola))
            pygame.draw.line(s, (*agua_c, 255), (x, 4 + ola), (x, 15))
        azar = random.Random(cuadro)
        for _ in range(4):
            s.set_at((azar.randrange(16), azar.randrange(7, 16)), (*aclarar(agua_c, 0.2), 255))
        # la superficie deja ver un poco de fondo
        for x in range(16):
            for y in range(0, 2 + int(round(math.sin((x + cuadro * 4) * 0.4) * 1.2))):
                s.set_at((x, y), (0, 0, 0, 0))
        aguas.append(s.convert_alpha())
    CACHE.setdefault("terreno", {})[region] = {
        "relleno": inter.convert(), "tope": tope.convert(),
        "plataforma": plat.convert(), "agua": aguas,
    }


# ======================================================================
#  Punto de entrada
# ======================================================================
def iniciar():
    """Genera todo el arte una sola vez. Devuelve los segundos que tardo."""
    if CACHE.get("listo"):
        return 0.0
    inicio = time.perf_counter()
    _generar_personajes()
    _generar_enemigos()
    _generar_comidas()
    _generar_bloques()
    _generar_banderas()
    for region in _TERRENO:
        _generar_terreno(region)
    CACHE["listo"] = True
    return time.perf_counter() - inicio


def reiniciar():
    CACHE.clear()


# --------------------------------------------------------------- consultas
def personaje(clave, accesorio, grande, anim, cuadro, derecha):
    lista = CACHE["personajes"][(clave, accesorio)]["grande" if grande else "pequeno"][anim]
    return lista[cuadro % len(lista)][1 if derecha else 0]


def cabeza(clave, accesorio):
    return CACHE["cabezas"][(clave, accesorio)]


def enemigo(tipo, anim, cuadro, derecha):
    lista = CACHE["enemigos"][tipo][anim]
    return lista[cuadro % len(lista)][1 if derecha else 0]


def comida(clave):
    return CACHE["comidas"][clave]


def coleccionable(clave):
    return CACHE["coleccionables"][clave]


def bloque(nombre):
    return CACHE["bloques"][nombre]


def terreno(region):
    return CACHE["terreno"][region]
