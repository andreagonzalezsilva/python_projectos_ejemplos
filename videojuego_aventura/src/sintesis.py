"""Sintesis de la musica: instrumentos, bateria y mezcla. Solo biblioteca estandar, sin archivos externos.

Las canciones se calculan UNA sola vez y se guardan en cache_sonido/ (ver sonido.py), asi que aqui se puede
gastar tiempo en que suenen bien: cada instrumento tiene su timbre y su envolvente (ataque, caida, sostenido,
relajo), las notas flojas y fuertes cambian de volumen, hay "swing" y un eco suave.

Unidad de tiempo: la semicorchea (1/16 de compas). Un compas tiene 16 unidades.
"""
import array
import math
import random
from functools import lru_cache

FRECUENCIA = 22050
AMPLITUD_MAX = 32767
UNIDADES_COMPAS = 16

# ======================================================================
#  Notas y acordes
# ======================================================================
_NOMBRES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
_CLASE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def clase_nota(texto):
    """'A#' -> 10, 'Bb' -> 10, 'C' -> 0."""
    valor = _CLASE[texto[0]]
    for signo in texto[1:]:
        valor += 1 if signo == "#" else -1
    return valor % 12


def indice_nota(nota):
    """'A4' -> 57 (semitonos desde C0)."""
    return int(nota[-1]) * 12 + clase_nota(nota[:-1])


def frecuencia(indice):
    return 440.0 * 2 ** ((indice - 57) / 12)


_ACORDES = {"": (0, 4, 7, 12), "m": (0, 3, 7, 12), "7": (0, 4, 7, 10), "m7": (0, 3, 7, 10)}


def leer_acorde(texto):
    """'Am' -> (9, 'm'); 'Bb7' -> (10, '7')."""
    largo = 2 if len(texto) > 1 and texto[1] in "#b" else 1
    return clase_nota(texto[:largo]), texto[largo:]


def raiz_grave(clase):
    """Nota de bajo: entre E2 y D#3 (se oye en bocinas pequenas)."""
    return 12 * (2 if clase >= 4 else 3) + clase


# ======================================================================
#  Ondas (tablas afinadas)
# ======================================================================
def _seno(p):
    return math.sin(math.tau * p)


def _suma(*parciales):
    def onda(p):
        return sum(amp * math.sin(math.tau * h * p) for h, amp in parciales)
    return onda


def _pulso(ancho):
    return lambda p: 1.0 if (p % 1.0) < ancho else -1.0


ONDAS = {
    "seno": _seno,
    "flauta": _suma((1, 1.0), (2, 0.16), (3, 0.05)),
    "bajo": _suma((1, 1.0), (2, 0.45), (3, 0.2)),
    "piano": _suma((1, 1.0), (2, 0.5), (3, 0.3), (4, 0.15)),
    "acero": _suma((1, 1.0), (2, 0.5), (3, 0.35), (5, 0.2)),
    "marimba": _suma((1, 1.0), (4, 0.3)),
    "laton": _suma(*[(h, 1.0 / h) for h in range(1, 8)]),
    "diente": lambda p: 2.0 * (p % 1.0) - 1.0,
    "cuadrada50": _pulso(0.5),
    "cuadrada25": _pulso(0.25),
    "pulso125": _pulso(0.125),
    "triangular": lambda p: 4.0 * abs((p % 1.0) - 0.5) - 1.0,
}


@lru_cache(maxsize=None)
def tabla(frec, tipo):
    """Tabla con varios periodos de la onda cuya longitud casi no desafina: repetirla da la nota exacta."""
    mejor = None
    for m in range(1, 41):
        largo = m * FRECUENCIA / frec
        error = abs(largo - round(largo)) / largo
        if mejor is None or error < mejor[0]:
            mejor = (error, m, int(round(largo)))
        if error < 0.0003:
            break
    _, m, largo = mejor
    onda = ONDAS[tipo]
    valores = [onda(m * i / largo) for i in range(largo)]
    pico = max(abs(v) for v in valores) or 1.0
    return tuple(v / pico for v in valores)


# ======================================================================
#  Instrumentos: onda, envolvente (ataque, caida, sostenido, relajo, vibrato, tau), volumen, legato
#  tau > 0: la nota se apaga sola como una cuerda o un tecla; si no, es de viento (ataque/caida/sostenido).
# ======================================================================
INSTRUMENTOS = {
    "mario":         dict(onda="cuadrada25", env=(0.003, 0.07, 0.70, 0.03, 0.0, 0.0), vol=0.20, legato=0.90),
    "trompeta":      dict(onda="laton", env=(0.022, 0.09, 0.75, 0.05, 0.0, 0.0), vol=0.24, legato=0.90),
    "flauta":        dict(onda="flauta", env=(0.035, 0.06, 0.88, 0.07, 0.07, 0.0), vol=0.34, legato=0.96, soplo=0.05),
    "acero":         dict(onda="acero", env=(0.004, 0.0, 1.0, 0.05, 0.0, 0.30), vol=0.30, legato=1.0),
    "laton_aspero":  dict(onda="diente", env=(0.004, 0.05, 0.85, 0.03, 0.0, 0.0), vol=0.17, legato=0.85, desafina=0.007),
    "piano":         dict(onda="piano", env=(0.003, 0.0, 1.0, 0.03, 0.0, 0.22), vol=0.15, legato=1.0),
    "charango":      dict(onda="piano", env=(0.002, 0.0, 1.0, 0.02, 0.0, 0.09), vol=0.10, legato=1.0),
    "ukelele":       dict(onda="piano", env=(0.002, 0.0, 1.0, 0.02, 0.0, 0.07), vol=0.13, legato=1.0),
    "marimba":       dict(onda="marimba", env=(0.002, 0.0, 1.0, 0.03, 0.0, 0.14), vol=0.24, legato=1.0),
    "acorde_aspero": dict(onda="diente", env=(0.003, 0.06, 0.5, 0.04, 0.0, 0.0), vol=0.09, legato=1.0),
    "bajo_salsa":    dict(onda="bajo", env=(0.004, 0.06, 0.55, 0.05, 0.0, 0.0), vol=0.42, legato=0.75),
    "bajo_redondo":  dict(onda="bajo", env=(0.010, 0.08, 0.80, 0.08, 0.0, 0.0), vol=0.42, legato=0.90),
    "bajo_mario":    dict(onda="bajo", env=(0.004, 0.08, 0.50, 0.04, 0.0, 0.0), vol=0.42, legato=0.70),
    "bajo_aspero":   dict(onda="diente", env=(0.003, 0.05, 0.70, 0.03, 0.0, 0.0), vol=0.24, legato=0.80),
}


@lru_cache(maxsize=2048)
def envolvente(n, ataque, caida, sost, relajo, vibrato, tau):
    a = max(1, int(ataque * FRECUENCIA))
    d = max(1, int(caida * FRECUENCIA))
    r = max(1, min(int(relajo * FRECUENCIA), n // 2))
    sal = []
    for i in range(n):
        if tau > 0:
            v = min(1.0, i / a) * math.exp(-i / (tau * FRECUENCIA))
        elif i < a:
            v = i / a
        elif i < a + d:
            v = 1.0 - (1.0 - sost) * (i - a) / d
        else:
            v = sost
        if vibrato and i > 0.12 * FRECUENCIA:
            t = i / FRECUENCIA
            v *= 1.0 + vibrato * min(1.0, (t - 0.12) / 0.2) * math.sin(math.tau * 5.6 * t)
        if i >= n - r:
            v *= (n - 1 - i) / r
        sal.append(v)
    return tuple(sal)


@lru_cache(maxsize=1)
def _soplo():
    azar = random.Random(21)
    return tuple(azar.uniform(-1, 1) * math.exp(-i / 350.0) for i in range(1200))


@lru_cache(maxsize=1500)
def nota(nombre, indice, n, vel):
    """Muestras (floats) de una nota: instrumento, nota (indice), n muestras, velocidad 1..8."""
    ins = INSTRUMENTOS[nombre]
    frec = frecuencia(indice)
    t = tabla(frec, ins["onda"])
    base = (t * (n // len(t) + 1))[:n]
    if ins.get("desafina"):
        t2 = tabla(frec * (1 + ins["desafina"]), ins["onda"])
        base = [(a + b) * 0.5 for a, b in zip(base, (t2 * (n // len(t2) + 1))[:n])]
    env = envolvente(n, *ins["env"])
    ganancia = ins["vol"] * AMPLITUD_MAX * vel / 8.0
    muestras = [b * e * ganancia for b, e in zip(base, env)]
    if ins.get("soplo"):
        k = min(len(muestras), 1200)
        ruido = _soplo()
        extra = ins["soplo"] * ganancia
        muestras[:k] = [m + r * extra for m, r in zip(muestras[:k], ruido)]
    return tuple(muestras)


# ======================================================================
#  Bateria
# ======================================================================
def _barrido(f0, f1, tau_f, duracion, tau_a):
    n = int(duracion * FRECUENCIA)
    fase = 0.0
    sal = []
    for i in range(n):
        t = i / FRECUENCIA
        fase += (f1 + (f0 - f1) * math.exp(-t / tau_f)) / FRECUENCIA
        sal.append(math.sin(math.tau * fase) * math.exp(-t / tau_a))
    return sal


def _ruido(duracion, tau, semilla, agudo=False):
    azar = random.Random(semilla)
    n = int(duracion * FRECUENCIA)
    crudo = [azar.uniform(-1, 1) for _ in range(n + 1)]
    if agudo:
        crudo = [crudo[i + 1] - crudo[i] for i in range(n)]
    return [crudo[i] * math.exp(-i / FRECUENCIA / tau) for i in range(n)]


def _tonos(duracion, parciales, tau):
    n = int(duracion * FRECUENCIA)
    return [sum(a * math.sin(math.tau * f * i / FRECUENCIA) for f, a in parciales) * math.exp(-i / FRECUENCIA / tau)
            for i in range(n)]


def _sumar_listas(*listas):
    n = max(len(x) for x in listas)
    return [sum(x[i] for x in listas if i < len(x)) for i in range(n)]


@lru_cache(maxsize=None)
def golpe(nombre, suave=False):
    """Un golpe de bateria o percusion (floats). 'suave' = la mitad de fuerte."""
    if nombre == "bombo":
        x, vol = _barrido(140, 48, 0.035, 0.16, 0.06), 0.85
    elif nombre == "bombo_andino":
        x, vol = _sumar_listas(_barrido(100, 58, 0.05, 0.32, 0.12), _ruido(0.02, 0.01, 3)), 0.9
    elif nombre == "caja":
        x, vol = _sumar_listas([v * 0.7 for v in _ruido(0.14, 0.035, 5)], [v * 0.55 for v in _barrido(200, 170, 0.02, 0.14, 0.03)]), 0.6
    elif nombre == "redoble":
        x, vol = _sumar_listas([v * 0.9 for v in _ruido(0.16, 0.05, 6)], [v * 0.4 for v in _barrido(220, 160, 0.02, 0.16, 0.04)]), 0.62
    elif nombre == "charles":
        x, vol = _ruido(0.05, 0.012, 7, agudo=True), 0.30
    elif nombre == "charles_abierto":
        x, vol = _ruido(0.18, 0.06, 8, agudo=True), 0.26
    elif nombre == "maraca":
        x, vol = _ruido(0.07, 0.022, 9, agudo=True), 0.22
    elif nombre == "cencerro":
        x, vol = _tonos(0.16, ((587, 1.0), (845, 0.8), (1174, 0.3)), 0.045), 0.28
    elif nombre == "clave":
        x, vol = _tonos(0.07, ((2300, 1.0),), 0.012), 0.5
    elif nombre == "conga":
        x, vol = _barrido(330, 240, 0.03, 0.18, 0.06), 0.55
    elif nombre == "conga_grave":
        x, vol = _barrido(240, 165, 0.03, 0.2, 0.07), 0.6
    elif nombre == "tom":
        x, vol = _barrido(190, 100, 0.05, 0.24, 0.09), 0.7
    else:
        raise KeyError(nombre)
    escala = AMPLITUD_MAX * vol * (0.5 if suave else 1.0)
    return tuple(v * escala for v in x)


# ======================================================================
#  Patrones: bajo y acompanamiento (offset, duracion, grado) en unidades de un compas
# ======================================================================
PATRONES_BAJO = {
    "mario": [(0, 2, "r"), (2, 2, "q"), (4, 2, "o"), (6, 2, "q"), (8, 2, "r"), (10, 2, "q"), (12, 2, "o"), (14, 2, "q")],
    "salsa": [(0, 3, "r"), (6, 2, "r"), (8, 2, "q"), (11, 1, "r"), (12, 2, "o"), (14, 2, "q")],
    "andino": [(0, 4, "r"), (4, 2, "q"), (6, 1, "q"), (7, 1, "q"), (8, 4, "r"), (12, 2, "q"), (14, 1, "q"), (15, 1, "r")],
    "galope": [(0, 2, "r"), (2, 1, "r"), (3, 1, "r"), (4, 2, "q"), (6, 2, "r"), (8, 2, "r"), (10, 1, "r"), (11, 1, "r"),
               (12, 2, "q"), (14, 2, "r")],
    "reggae": [(0, 6, "r"), (8, 3, "q"), (12, 2, "r"), (14, 2, "t")],
    "pulso16": [(i, 1, "o" if i % 4 == 2 else "r") for i in range(16)],
}

# grado: indice del acorde (0 raiz, 1 tercera, 2 quinta, 3 septima u octava), "A" = acorde entero, "P" = raiz y quinta
PATRONES_ACOMP = {
    "oompah": [(4, 2, "A"), (12, 2, "A")],
    "guajeo": [(0, 2, 0), (3, 2, 1), (6, 2, 2), (8, 2, 1), (11, 2, 2), (14, 2, 1)],
    "charango": [(i, 1, (0, 2, 1, 2)[i % 4]) for i in range(16)],
    "ostinato": [(0, 1, 0), (1, 1, 2), (2, 2, 3), (4, 1, 0), (5, 1, 2), (6, 2, 3), (8, 1, 0), (9, 1, 2), (10, 2, 3),
                 (12, 1, 0), (13, 1, 2), (14, 2, 3)],
    "skank": [(2, 1, "A"), (6, 1, "A"), (10, 1, "A"), (14, 1, "A")],
    "stab": [(0, 2, "P"), (6, 2, "P"), (8, 2, "P"), (14, 2, "P")],
}


# ======================================================================
#  Lectura de la partitura
# ======================================================================
def leer_melodia(texto):
    """'E5 G5:3 R:1' -> [(inicio, duracion, 'E5')...]. Sin :n una nota dura 2 unidades (una corchea)."""
    eventos, pos = [], 0
    for token in texto.split():
        if token == "|":
            continue
        nombre, _, cantidad = token.partition(":")
        dur = int(cantidad) if cantidad else 2
        if nombre != "R":
            eventos.append((pos, dur, nombre))
        pos += dur
    return eventos, pos


def validar(datos):
    """Revisa que cada compas de cada frase mida 16 unidades. Devuelve la lista de problemas."""
    problemas = []
    for clave, (melodia, acordes) in datos["frases"].items():
        compases = [c for c in melodia.split("|")]
        if len(compases) != 4:
            problemas.append("frase %s: %d compases (debe haber 4)" % (clave, len(compases)))
        for i, c in enumerate(compases, 1):
            largo = leer_melodia(c)[1]
            if largo != UNIDADES_COMPAS:
                problemas.append("frase %s, compas %d mide %d (debe medir 16)" % (clave, i, largo))
        if len(acordes.split()) != 4:
            problemas.append("frase %s: %d acordes (debe haber 4)" % (clave, len(acordes.split())))
    return problemas


# ======================================================================
#  Mezcla
# ======================================================================
def _sumar(buf, inicio, muestras):
    total = len(buf)
    inicio %= total
    n = len(muestras)
    fin = inicio + n
    if fin <= total:
        buf[inicio:fin] = [a + b for a, b in zip(buf[inicio:fin], muestras)]
    else:
        corte = total - inicio
        buf[inicio:] = [a + b for a, b in zip(buf[inicio:], muestras[:corte])]
        buf[:n - corte] = [a + b for a, b in zip(buf[:n - corte], muestras[corte:])]


def _velocidad(unidad, azar):
    """Las notas en el pulso suenan mas fuertes que las de contratiempo, y ninguna igual a otra."""
    if unidad % 16 == 0:
        base = 1.0
    elif unidad % 8 == 0:
        base = 0.94
    elif unidad % 4 == 0:
        base = 0.86
    elif unidad % 2 == 0:
        base = 0.77
    else:
        base = 0.68
    return max(1, min(8, int(round(8 * base * azar.uniform(0.93, 1.04)))))


def crear_cancion(datos):
    """Devuelve array('h') con la cancion lista para reproducir en bucle."""
    azar = random.Random(datos.get("semilla", 1))
    forma = datos["forma"].split()
    u = 60.0 / datos["tempo"] / 4.0                  # segundos por unidad (semicorchea)
    swing = datos.get("swing", 0.0)

    def muestra(unidades):
        seg = unidades * u
        if swing and unidades % 4 == 2:
            seg += swing * 2 * u                     # la corchea de contratiempo se retrasa un poco
        return int(round(seg * FRECUENCIA))

    unidades_frase = 4 * UNIDADES_COMPAS
    total = muestra(len(forma) * unidades_frase)
    resto = [0.0] * total
    solista = [0.0] * total
    octava = datos.get("transponer", 0)
    ins_lead = datos["lead"]
    ins_bajo, pat_bajo = datos["bajo"]
    ins_acomp, pat_acomp = datos["acomp"]
    bateria = datos["bateria"]
    mitad = len(forma) // 2

    for numero, nombre in enumerate(forma):
        melodia, acordes = datos["frases"][nombre]
        origen = numero * unidades_frase
        segunda = numero >= mitad

        # ---- melodia
        eventos, _ = leer_melodia(melodia)
        for pos, dur, texto in eventos:
            unidad = origen + pos
            ini, fin = muestra(unidad), muestra(unidad + dur)
            largo = max(8, int((fin - ini) * INSTRUMENTOS[ins_lead]["legato"]))
            _sumar(solista, ini, nota(ins_lead, indice_nota(texto) + octava, largo, _velocidad(pos, azar)))

        # ---- bajo y acompanamiento, compas por compas
        for c, acorde in enumerate(acordes.split()):
            clase, tipo = leer_acorde(acorde)
            base_compas = origen + c * UNIDADES_COMPAS
            raiz = raiz_grave(clase)
            tercera = 4 if tipo in ("", "7") else 3
            grados = {"r": raiz, "q": raiz + 7, "o": raiz + 12, "t": raiz + tercera}
            for pos, dur, grado in PATRONES_BAJO[pat_bajo]:
                unidad = base_compas + pos
                ini, fin = muestra(unidad), muestra(unidad + dur)
                largo = max(8, int((fin - ini) * INSTRUMENTOS[ins_bajo]["legato"]))
                _sumar(resto, ini, nota(ins_bajo, grados[grado], largo, _velocidad(pos, azar)))

            raiz_alta = 48 + clase
            tonos = [raiz_alta + i for i in _ACORDES[tipo]]
            for pos, dur, grado in PATRONES_ACOMP[pat_acomp]:
                unidad = base_compas + pos
                ini, fin = muestra(unidad), muestra(unidad + dur)
                largo = max(8, int((fin - ini) * INSTRUMENTOS[ins_acomp]["legato"]))
                if grado == "A":
                    elegidos = tonos[:3]
                elif grado == "P":
                    elegidos = [tonos[0], tonos[2]]
                else:
                    elegidos = [tonos[grado]]
                vel = _velocidad(pos, azar)
                for t in elegidos:
                    _sumar(resto, ini, nota(ins_acomp, t, largo, vel))

        # ---- bateria (la ultima compas de cada frase lleva un relleno)
        patrones = bateria[1] if segunda and len(bateria) > 1 else bateria[0]
        for c in range(4):
            base_compas = origen + c * UNIDADES_COMPAS
            todos = dict(patrones)
            if c == 3 and datos.get("relleno"):
                for tambor, patron in datos["relleno"].items():
                    previo = todos.get(tambor, "." * UNIDADES_COMPAS)
                    todos[tambor] = "".join("x" if "x" in (a, b) else ("o" if "o" in (a, b) else ".")
                                            for a, b in zip(previo, patron))
            for tambor, patron in todos.items():
                for pos, marca in enumerate(patron):
                    if marca == ".":
                        continue
                    _sumar(resto, muestra(base_compas + pos), golpe(tambor, marca == "o"))

    # ---- eco suave sobre la melodia (circular, para que el bucle no se corte)
    eco = datos.get("eco")
    if eco:
        retraso, ganancia = muestra(eco[0]), eco[1]
        atras = solista[-retraso:] + solista[:-retraso]
        solista = [a + b * ganancia for a, b in zip(solista, atras)]

    mezcla = [a + b for a, b in zip(resto, solista)]
    # volumen parejo entre canciones: se ajusta por RMS y un limitador suave (tanh) doma los golpes de bateria
    muestreo = mezcla[::7]
    rms = math.sqrt(sum(x * x for x in muestreo) / len(muestreo)) or 1.0
    g = datos.get("nivel", 0.19) * AMPLITUD_MAX / rms
    techo = 0.92 * AMPLITUD_MAX
    resultado = array.array("h", [int(techo * math.tanh(x * g / techo)) for x in mezcla])
    nota.cache_clear()          # las notas ya mezcladas ocupan mucha memoria: no hace falta guardarlas
    envolvente.cache_clear()
    return resultado


def duracion_cancion(datos):
    """Segundos que dura la cancion antes de repetirse."""
    return len(datos["forma"].split()) * 4 * UNIDADES_COMPAS * 60.0 / datos["tempo"] / 4.0
