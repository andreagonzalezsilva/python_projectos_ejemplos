"""Sonido sintetizado con la biblioteca estandar (array, math, random). Sin archivos externos.

Genera ondas cuadrada, triangular y de ruido a 22050 Hz, mono, 16 bits.
Si no hay dispositivo de audio, crear Sonido() lanza una excepcion y el motor usa SonidoNulo.
"""
import array
import math
import random

import pygame

FRECUENCIA = 22050
AMPLITUD_MAX = 32767

# ======================================================================
#  Notas y ondas
# ======================================================================
_NOTAS = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}


def frecuencia(nota):
    """'A4' -> 440.0. 'R' (silencio) -> 0."""
    if nota == "R":
        return 0.0
    nombre, octava = nota[:-1], int(nota[-1])
    semitonos = 12 * (octava - 4) + _NOTAS[nombre] - 9
    return 440.0 * 2 ** (semitonos / 12)


def segmento(f_inicio, f_fin, duracion, tipo="cuadrada", volumen=0.3):
    """Un sonido que desliza su frecuencia de f_inicio a f_fin, con envolvente que decae."""
    n = int(FRECUENCIA * duracion)
    salida = []
    fase = 0.0
    azar = random.Random(11)
    ataque = max(1, int(0.003 * FRECUENCIA))
    for i in range(n):
        t = i / n
        if tipo == "ruido":
            valor = azar.uniform(-1, 1)
        else:
            fase += (f_inicio + (f_fin - f_inicio) * t) / FRECUENCIA
            fase -= int(fase)
            if tipo == "cuadrada":
                valor = 1.0 if fase < 0.5 else -1.0
            else:
                valor = 4 * abs(fase - 0.5) - 1
        envolvente = (1 - t) ** 1.4 * min(1.0, i / ataque)
        salida.append(int(AMPLITUD_MAX * volumen * valor * envolvente))
    return salida


def nota_constante(frec, duracion, tipo, volumen):
    """Nota de musica: onda de un periodo repetida (rapido) y un pequeno fundido al final."""
    n = int(FRECUENCIA * duracion)
    if frec <= 0:
        return [0] * n
    periodo = max(2, int(round(FRECUENCIA / frec)))
    alto = int(AMPLITUD_MAX * volumen)
    if tipo == "cuadrada":
        mitad = periodo // 2
        onda = [alto] * mitad + [-alto] * (periodo - mitad)
    else:
        onda = [int(alto * (4 * abs(i / periodo - 0.5) - 1)) for i in range(periodo)]
    muestras = (onda * (n // periodo + 1))[:n]
    fundido = min(n, int(0.012 * FRECUENCIA))
    for k in range(fundido):
        muestras[n - 1 - k] = int(muestras[n - 1 - k] * k / fundido)
    return muestras


def a_sonido(muestras, volumen=1.0):
    buffer = array.array("h", [max(-32768, min(32767, int(m))) for m in muestras])
    sonido = pygame.mixer.Sound(buffer=buffer.tobytes())
    sonido.set_volume(volumen)
    return sonido


# ======================================================================
#  Efectos: lista de (frec_inicio, frec_fin, duracion, tipo, volumen)
# ======================================================================
EFECTOS = {
    "saltar": [(280, 640, 0.16, "cuadrada", 0.22)],
    "coleccionable": [(988, 988, 0.05, "cuadrada", 0.2), (1319, 1319, 0.16, "cuadrada", 0.2)],
    "pisar": [(420, 110, 0.12, "cuadrada", 0.3), (0, 0, 0.05, "ruido", 0.18)],
    "golpe": [(0, 0, 0.1, "ruido", 0.3), (300, 90, 0.2, "cuadrada", 0.25)],
    "comida_sale": [(262, 262, 0.07, "triangular", 0.4), (330, 330, 0.07, "triangular", 0.4),
                    (392, 392, 0.07, "triangular", 0.4), (523, 523, 0.12, "triangular", 0.4)],
    "comida": [(392, 392, 0.06, "cuadrada", 0.2), (523, 523, 0.06, "cuadrada", 0.2),
               (659, 659, 0.06, "cuadrada", 0.2), (784, 784, 0.06, "cuadrada", 0.2),
               (1047, 1047, 0.16, "cuadrada", 0.2)],
    "romper": [(0, 0, 0.18, "ruido", 0.35), (200, 60, 0.12, "cuadrada", 0.2)],
    "checkpoint": [(523, 523, 0.08, "cuadrada", 0.2), (659, 659, 0.08, "cuadrada", 0.2),
                   (784, 784, 0.18, "cuadrada", 0.2)],
    "vida_extra": [(659, 659, 0.08, "cuadrada", 0.2), (784, 784, 0.08, "cuadrada", 0.2),
                   (1319, 1319, 0.08, "cuadrada", 0.2), (1047, 1047, 0.08, "cuadrada", 0.2),
                   (1175, 1175, 0.08, "cuadrada", 0.2), (1568, 1568, 0.24, "cuadrada", 0.2)],
    "meta": [(392, 392, 0.1, "cuadrada", 0.2), (523, 523, 0.1, "cuadrada", 0.2),
             (659, 659, 0.1, "cuadrada", 0.2), (784, 784, 0.1, "cuadrada", 0.2),
             (1047, 1047, 0.35, "cuadrada", 0.2)],
    "victoria_nivel": [(523, 523, 0.12, "cuadrada", 0.2), (523, 523, 0.12, "cuadrada", 0.2),
                       (523, 523, 0.12, "cuadrada", 0.2), (659, 659, 0.3, "cuadrada", 0.2),
                       (784, 784, 0.4, "cuadrada", 0.2)],
    "morir": [(523, 392, 0.15, "cuadrada", 0.22), (392, 261, 0.18, "cuadrada", 0.22),
              (261, 130, 0.35, "cuadrada", 0.22)],
    "game_over": [(392, 392, 0.2, "triangular", 0.4), (330, 330, 0.2, "triangular", 0.4),
                  (262, 262, 0.2, "triangular", 0.4), (196, 130, 0.6, "triangular", 0.4)],
    "temblor": [(50, 38, 0.8, "triangular", 0.5), (0, 0, 0.5, "ruido", 0.15)],
    "sello": [(1047, 1047, 0.05, "triangular", 0.4), (1319, 1319, 0.05, "triangular", 0.4),
              (1568, 1568, 0.05, "triangular", 0.4), (2093, 2093, 0.25, "triangular", 0.4)],
    "menu": [(660, 660, 0.04, "cuadrada", 0.14)],
    "elegir": [(660, 660, 0.04, "cuadrada", 0.16), (990, 990, 0.1, "cuadrada", 0.16)],
    "cuenta": [(1500, 1500, 0.02, "cuadrada", 0.12)],
}

# ======================================================================
#  Musica: cada nota es "NOTA:corcheas" (sin :n vale 1 corchea). R = silencio.
# ======================================================================
MUSICAS = {
    "titulo": {
        "tempo": 104,
        "melodia": "C5:2 E5:2 G5:2 E5:2 F5:2 A5:2 G5:4 E5:2 G5:2 C6:2 G5:2 F5:2 D5:2 C5:4",
        "bajo": "C3:4 G2:4 F2:4 C3:4 C3:4 G2:4 F2:4 G2:4",
    },
    "costa": {
        "tempo": 132,
        "melodia": "E5 G5 E5 C5 E5 G5 C6:2 D5 F5 D5 B4 D5 F5 B5:2 "
                   "C5 E5 G5 E5 A5 G5 E5 C5 D5 E5 D5 B4 C5:4",
        "bajo": "C3:2 G3:2 C3:2 G3:2 G2:2 D3:2 G2:2 D3:2 A2:2 E3:2 F2:2 C3:2 G2:2 D3:2 C3:4",
        "percusion": True,
    },
    "sierra": {
        "tempo": 116,
        "melodia": "A4 C5 E5 E5 D5 C5 B4:2 A4 C5 E5 A5 G5 E5 D5:2 "
                   "C5 D5 E5 E5 D5 C5 B4 A4 G4 A4 B4 C5 A4:4",
        "bajo": "A2:2 E3:2 A2:2 E3:2 A2:2 E3:2 A2:2 E3:2 F2:2 C3:2 G2:2 D3:2 E2:2 B2:2 A2:4",
        "percusion": True,
    },
    "amazonia": {
        "tempo": 100,
        "melodia": "D4:2 F4:2 A4:2 C5:2 A4:3 F4 D4:4 G4:2 A4:2 C5:2 D5:2 C5:3 A4 D5:4",
        "bajo": "D3:4 A2:4 D3:4 F3:4 G2:4 D3:4 A2:4 D3:4",
        "percusion": True,
    },
    "galapagos": {
        "tempo": 116,
        "melodia": "G4 B4 D5 F#5 D5 B4 G4:2 A4 B4 D5 G5 D5 B4 A4:2 "
                   "B4 D5 F#5 A5 F#5 D5 B4:2 C5 D5 E5 D5 B4:4",
        "bajo": "G2:4 D3:4 A2:4 E3:4 B2:4 F#3:4 C3:4 D3:4",
    },
    "cotopaxi": {
        "tempo": 150,
        "melodia": "E4 E4 G4 E4 B4 E4 A4 G4 E4 E4 G4 E4 C5 B4 A4 G4 "
                   "B4 B4 D5 B4 G5 F#5 E5 D5 C5 B4 A4 G4 B4:4",
        "bajo": "E2 E2 E3 E2 E2 E2 E3 E2 E2 E2 E3 E2 E2 E2 E3 E2 "
                "B1 B1 B2 B1 B1 B1 B2 B1 C2 C2 C3 C2 B1:4",
        "percusion": True,
    },
    "victoria": {
        "tempo": 150,
        "melodia": "C5 C5 C5 C5:3 G4:2 A4 A4 A4 A4:3 F5:2 G5 F5 E5 D5 C5:4 D5 E5 D5 C5 C5:4",
        "bajo": "C3:4 C3:4 F2:4 F2:4 C3:4 G2:4 G2:4 C3:4",
    },
}


def _leer_notas(texto):
    """'E5 G5:2 R' -> [('E5', 1), ('G5', 2), ('R', 1)]"""
    notas = []
    for token in texto.split():
        if ":" in token:
            nombre, cantidad = token.split(":")
            notas.append((nombre, int(cantidad)))
        else:
            notas.append((token, 1))
    return notas


def _pista(texto, corchea_seg, tipo, volumen, largo):
    muestras = []
    for nota, cantidad in _leer_notas(texto):
        muestras.extend(nota_constante(frecuencia(nota), cantidad * corchea_seg, tipo, volumen))
    return muestras + [0] * max(0, largo - len(muestras))


def crear_cancion(datos):
    """Mezcla melodia (cuadrada), bajo (triangular) y percusion (ruido) en una lista de muestras."""
    corchea = 60.0 / datos["tempo"] / 2
    largo = int(sum(c for _, c in _leer_notas(datos["melodia"])) * corchea * FRECUENCIA)
    melodia = _pista(datos["melodia"], corchea, "cuadrada", 0.12, largo)
    bajo = _pista(datos["bajo"], corchea, "triangular", 0.22, largo)
    mezcla = [a + b for a, b in zip(melodia, bajo)]
    if datos.get("percusion"):
        azar = random.Random(3)
        golpe = int(0.03 * FRECUENCIA)
        por_corchea = int(corchea * FRECUENCIA)
        for inicio in range(por_corchea, largo - golpe, por_corchea * 2):
            for k in range(golpe):
                mezcla[inicio + k] += int(AMPLITUD_MAX * 0.05 * azar.uniform(-1, 1) * (1 - k / golpe))
    return mezcla[:largo]


# ======================================================================
#  Clase Sonido
# ======================================================================
class Sonido:
    def __init__(self):
        pygame.mixer.init(FRECUENCIA, -16, 1, 512)
        pygame.mixer.set_num_channels(10)
        pygame.mixer.set_reserved(1)
        self.canal_musica = pygame.mixer.Channel(0)
        self.silenciado = False
        self.volumen_efectos = 0.7
        self.volumen_musica = 0.45
        self.efectos = {}
        for nombre, partes in EFECTOS.items():
            muestras = []
            for f0, f1, dur, tipo, vol in partes:
                muestras.extend(segmento(f0, f1, dur, tipo, vol))
            self.efectos[nombre] = a_sonido(muestras, self.volumen_efectos)
        self.canciones = {}
        self.actual = None

    def efecto(self, nombre):
        if self.silenciado:
            return
        sonido = self.efectos.get(nombre)
        if sonido is not None:
            sonido.play()

    def _cancion(self, nombre):
        if nombre not in self.canciones:
            self.canciones[nombre] = a_sonido(crear_cancion(MUSICAS[nombre]), 1.0)
        return self.canciones[nombre]

    def musica(self, nombre):
        """Empieza (en bucle) la musica indicada. Si ya suena, no la reinicia."""
        if nombre not in MUSICAS:
            return
        if self.actual == nombre and self.canal_musica.get_busy():
            return
        self.actual = nombre
        self.canal_musica.set_volume(0.0 if self.silenciado else self.volumen_musica)
        self.canal_musica.play(self._cancion(nombre), loops=-1)

    def parar_musica(self):
        self.canal_musica.stop()
        self.actual = None

    def alternar_silencio(self):
        self.silenciado = not self.silenciado
        self.canal_musica.set_volume(0.0 if self.silenciado else self.volumen_musica)
        if self.silenciado:
            pygame.mixer.stop()
            # stop() tambien detiene la musica: se reanuda en silencio para poder volver a oirla
            if self.actual:
                self.canal_musica.play(self._cancion(self.actual), loops=-1)
                self.canal_musica.set_volume(0.0)
