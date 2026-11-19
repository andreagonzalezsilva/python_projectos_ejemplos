"""Sonido sintetizado con la biblioteca estandar (array, math, random). Sin archivos externos.

Efectos: ondas cuadrada, triangular y de ruido a 22050 Hz, mono, 16 bits. La musica la crea sintesis.py
a partir de las partituras de musica.py y se guarda en cache_sonido/.
Si no hay dispositivo de audio, crear Sonido() lanza una excepcion y el motor usa SonidoNulo.
"""
import array
import hashlib
import json
import math
import os
import random

import pygame

from musica import MUSICAS
from sintesis import AMPLITUD_MAX, FRECUENCIA, crear_cancion

_RAIZ = os.path.dirname(os.path.abspath(__file__))

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


def a_sonido(muestras, volumen=1.0):
    buffer = array.array("h", [max(-32768, min(32767, int(m))) for m in muestras])
    sonido = pygame.mixer.Sound(buffer=buffer.tobytes())
    sonido.set_volume(volumen)
    return sonido


# ======================================================================
#  Efectos: lista de (frec_inicio, frec_fin, duracion, tipo, volumen)
# ======================================================================
FACTOR_TONO = 1.0        # los efectos suenan a este multiplo de su frecuencia (menor que 1 = mas graves)

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
    "vida_extra": [(659, 659, 0.09, "cuadrada", 0.3), (784, 784, 0.09, "cuadrada", 0.3),
                   (1319, 1319, 0.09, "cuadrada", 0.3), (1047, 1047, 0.09, "cuadrada", 0.3),
                   (1175, 1175, 0.09, "cuadrada", 0.3), (1568, 1568, 0.12, "cuadrada", 0.3),
                   (2093, 2093, 0.1, "cuadrada", 0.3), (1568, 1568, 0.08, "cuadrada", 0.3),
                   (2093, 2093, 0.5, "triangular", 0.5)],
    "meta": [(523, 523, 0.1, "cuadrada", 0.22), (587, 587, 0.1, "cuadrada", 0.22),
             (659, 659, 0.1, "cuadrada", 0.22), (784, 784, 0.1, "cuadrada", 0.22),
             (1047, 1047, 0.1, "cuadrada", 0.22), (1319, 1319, 0.1, "cuadrada", 0.22),
             (1568, 1568, 0.1, "cuadrada", 0.22), (2093, 2093, 0.1, "cuadrada", 0.22),
             (2093, 2093, 0.5, "triangular", 0.5)],
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
#  Cache en disco: las canciones se sintetizan una vez y se guardan en cache_sonido/
# ======================================================================
VERSION_SINTESIS = 2        # subirla si cambia como se genera el sonido (invalida la cache)
CARPETA_CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache_sonido")


def _huella(nombre):
    """Cambia si cambia la cancion o el codigo que la sintetiza: asi nunca se usa una cache vieja."""
    with open(os.path.join(_RAIZ, "sintesis.py"), "rb") as archivo:
        codigo = archivo.read()
    texto = json.dumps([VERSION_SINTESIS, FRECUENCIA, MUSICAS[nombre]], sort_keys=True)
    return hashlib.md5(texto.encode("utf-8") + codigo).hexdigest()[:10]


def cancion_en_cache(nombre):
    """Bytes (16 bits, mono) de la cancion. Los lee de la cache o los sintetiza y los guarda."""
    ruta = os.path.join(CARPETA_CACHE, "%s_%s.raw" % (nombre, _huella(nombre)))
    try:
        with open(ruta, "rb") as archivo:
            return archivo.read()
    except OSError:
        pass
    datos = crear_cancion(MUSICAS[nombre]).tobytes()
    try:
        os.makedirs(CARPETA_CACHE, exist_ok=True)
        for viejo in os.listdir(CARPETA_CACHE):
            if viejo.startswith(nombre + "_"):
                os.remove(os.path.join(CARPETA_CACHE, viejo))
        with open(ruta + ".tmp", "wb") as archivo:
            archivo.write(datos)
        os.replace(ruta + ".tmp", ruta)
    except OSError:
        pass            # sin permiso de escritura: funciona igual, solo sin cache
    return datos


# ======================================================================
#  Clase Sonido
# ======================================================================
class Sonido:
    hay_audio = True

    def __init__(self):
        # pygame.init() ya abrio el mezclador con 44100 Hz estereo y un init() posterior se ignora: los
        # sonidos (22050 Hz mono) se oian 4 veces mas rapidos y 2 octavas mas agudos. Hay que cerrarlo y
        # abrirlo con el formato exacto. Buffer de 1024: aguanta un cuadro lento sin crujidos.
        pygame.mixer.quit()
        pygame.mixer.init(FRECUENCIA, -16, 1, 1024, allowedchanges=0)
        pygame.mixer.set_num_channels(10)
        pygame.mixer.set_reserved(1)
        self.canal_musica = pygame.mixer.Channel(0)
        self.musica_silenciada = False
        self.efectos_silenciados = False
        self.volumen_efectos = 0.7
        self.volumen_musica = 0.45
        self.efectos = {}
        for nombre, partes in EFECTOS.items():
            muestras = []
            for f0, f1, dur, tipo, vol in partes:
                muestras.extend(segmento(f0 * FACTOR_TONO, f1 * FACTOR_TONO, dur, tipo, vol))
            self.efectos[nombre] = a_sonido(muestras, self.volumen_efectos)
        self.canciones = {}
        self.actual = None
        # todo se prepara AHORA (al arrancar), nunca durante el juego. Con la cache en disco esto tarda
        # unos milisegundos; solo la primera vez hay que sintetizar las canciones.
        for nombre in MUSICAS:
            self._cancion(nombre)

    def efecto(self, nombre):
        if self.efectos_silenciados:
            return
        sonido = self.efectos.get(nombre)
        if sonido is not None:
            sonido.play()

    def _cancion(self, nombre):
        if nombre not in self.canciones:
            self.canciones[nombre] = pygame.mixer.Sound(buffer=cancion_en_cache(nombre))
        return self.canciones[nombre]

    def musica(self, nombre):
        """Empieza (en bucle) la musica indicada. Si ya suena, no la reinicia."""
        if nombre not in MUSICAS:
            return
        if self.actual == nombre and self.canal_musica.get_busy():
            return
        self.actual = nombre
        self._aplicar_volumen_musica()
        self.canal_musica.play(self._cancion(nombre), loops=-1)

    def parar_musica(self):
        self.canal_musica.stop()
        self.actual = None

    def _aplicar_volumen_musica(self):
        self.canal_musica.set_volume(0.0 if self.musica_silenciada else self.volumen_musica)

    def alternar_musica(self):
        """Silencia o activa solo la musica (la cancion sigue corriendo en silencio y vuelve a tiempo)."""
        self.musica_silenciada = not self.musica_silenciada
        self._aplicar_volumen_musica()
        return not self.musica_silenciada

    def alternar_efectos(self):
        """Silencia o activa solo los efectos de sonido."""
        self.efectos_silenciados = not self.efectos_silenciados
        if self.efectos_silenciados:
            for canal in range(1, pygame.mixer.get_num_channels()):
                pygame.mixer.Channel(canal).stop()
        return not self.efectos_silenciados
