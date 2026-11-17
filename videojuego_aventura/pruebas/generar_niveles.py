"""Herramienta de desarrollo: disena los 5 mapas con un pequeno lenguaje de funciones y
escribe los archivos niveles/<region>.py con el mapa de texto literal.

Uso: python pruebas/generar_niveles.py
Los archivos generados se pueden editar a mano despues; el juego solo lee los diccionarios.
"""
import json
import math
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILAS = 11
SUELO = 9          # fila donde empieza el suelo normal (filas 9 y 10)


class Plano:
    def __init__(self, columnas):
        self.n = columnas
        self.g = [[" "] * columnas for _ in range(FILAS)]

    def poner(self, col, fila, simbolo, solo_vacio=False):
        if 0 <= col < self.n and 0 <= fila < FILAS:
            if not solo_vacio or self.g[fila][col] == " ":
                self.g[fila][col] = simbolo

    def texto(self, col, fila, cadena):
        for i, s in enumerate(cadena):
            if s != " ":
                self.poner(col + i, fila, s)

    def perfil(self, segmentos):
        """segmentos: (col_inicio, col_fin, altura | 'W' agua | '_' abismo)."""
        for c0, c1, h in segmentos:
            for col in range(c0, c1 + 1):
                if h == "W":
                    self.poner(col, 9, "W")
                    self.poner(col, 10, "W")
                elif h == "_":
                    pass
                else:
                    for fila in range(SUELO - h, FILAS):
                        self.poner(col, fila, "#")

    def tablones(self, lista, fila=9, ancho=2, simbolo="="):
        """Plataformas flotantes (c0, [fila], [ancho])."""
        for item in lista:
            c0 = item[0]
            f = item[1] if len(item) > 1 else fila
            a = item[2] if len(item) > 2 else ancho
            for col in range(c0, c0 + a):
                self.poner(col, f, simbolo)

    def bloques(self, col, fila, cadena):
        self.texto(col, fila, cadena)

    def monedas(self, col, fila, cantidad, paso=1):
        for i in range(cantidad):
            self.poner(col + i * paso, fila, "C", solo_vacio=True)

    def arco(self, col, fila, cantidad, alto=3):
        for i in range(cantidad):
            t = i / max(1, cantidad - 1)
            self.poner(col + i, fila - int(round(math.sin(math.pi * t) * alto)), "C", solo_vacio=True)

    def sobre_suelo(self, col):
        """Fila libre justo encima del suelo de esa columna."""
        for fila in range(FILAS):
            if self.g[fila][col] in "#=":
                return fila - 1
        return SUELO - 1

    def marcar(self, columnas, simbolo, fila=None):
        for col in columnas:
            self.poner(col, self.sobre_suelo(col) if fila is None else fila, simbolo)

    def enemigos(self, columnas, fila=None):
        self.marcar(columnas, "E", fila)

    def checkpoints(self, columnas, fila=None):
        self.marcar(columnas, "K", fila)

    def lineas(self):
        return ["".join(f) for f in self.g]

    def contar(self, simbolo):
        return sum(f.count(simbolo) for f in self.lineas())


def fila_superficie(plano, col):
    """Primera fila solida desde arriba en una columna (o None si es abismo)."""
    for fila in range(FILAS):
        if plano.g[fila][col] in "#=":
            return fila
    return None


# ======================================================================
#  Niveles
# ======================================================================
def nivel_costa():
    p = Plano(150)
    p.perfil([(0, 27, 0), (28, 30, "W"), (31, 35, 0), (36, 39, 1), (40, 49, 0), (50, 66, "W"),
              (67, 87, 0), (88, 90, "W"), (91, 95, 0), (96, 98, 1), (99, 106, 0), (107, 110, "W"),
              (111, 116, 0), (117, 121, 2), (122, 124, "W"), (125, 149, 0)])
    p.tablones([(53, 9, 4), (60, 9, 4)])
    p.marcar([3], "P")
    p.marcar([144], "F")
    p.bloques(9, 5, "?B?B?")
    p.bloques(72, 5, "B?B?B")
    p.bloques(112, 5, "?B?")
    p.checkpoints([47, 100, 130])
    p.enemigos([12, 33, 69, 74, 93, 128, 133, 137, 140, 142])
    # coleccionables: filas de suelo y arcos sobre los saltos
    p.monedas(14, 8, 5)
    p.arco(26, 7, 7, 3)
    p.monedas(32, 8, 3)
    p.monedas(36, 7, 4)
    p.monedas(42, 8, 3)
    p.arco(49, 7, 5, 2)
    p.monedas(54, 8, 2)
    p.monedas(61, 8, 2)
    p.arco(63, 7, 6, 2)
    p.monedas(74, 8, 4)
    p.monedas(73, 3, 3)
    p.arco(86, 7, 7, 3)
    p.monedas(92, 8, 3)
    p.monedas(96, 7, 3)
    p.arco(104, 7, 8, 3)
    p.monedas(111, 3, 5)
    p.monedas(118, 6, 4)
    p.arco(121, 5, 6, 2)
    p.monedas(126, 8, 6)
    p.monedas(136, 6, 4)
    p.monedas(10, 3, 4)
    return {
        "clave": "costa", "nombre": "nivel_costa", "tiempo": 240,
        "paleta": {"cielo_arriba": "#7ED6F0", "cielo_abajo": "#CFF1FA", "suelo": "#E8D08A", "agua": "#1E88C8"},
        "fondo": ["mar_lejano", "palmeras", "olas_cercanas"],
        "enemigo": "cangrejo", "coleccionable": ["banano", "cacao"], "comida": "bolon", "musica": "costa",
        "bloques_especiales": {(9, 5): "coleccionable", (11, 5): "comida", (13, 5): "coleccionable",
                               (73, 5): "comida", (75, 5): "coleccionable",
                               (112, 5): "coleccionable", (114, 5): "comida"},
        "mapa": p.lineas(),
    }


def nivel_sierra():
    p = Plano(150)
    p.perfil([(0, 13, 0), (14, 20, 1), (21, 28, 2), (29, 32, "_"), (33, 42, 2), (43, 48, 0),
              (49, 52, "_"), (53, 60, 1), (61, 70, 3), (71, 74, "_"), (75, 84, 3), (85, 92, 1),
              (93, 96, "_"), (97, 106, 2), (107, 116, 4), (117, 120, "_"), (121, 130, 4),
              (131, 138, 2), (139, 149, 0)])
    p.marcar([3], "P")
    p.marcar([145], "F")
    p.bloques(9, 5, "?B?B?")
    p.bloques(86, 4, "B?B")
    p.bloques(140, 5, "?B?B")
    p.checkpoints([45, 100])
    # condores: vuelan en el aire sobre el camino
    for col, fila in ((17, 6), (36, 5), (55, 6), (66, 4), (80, 4), (88, 6), (102, 5), (125, 3), (135, 5)):
        p.poner(col, fila, "E")
    p.monedas(14, 7, 5)
    p.arco(27, 5, 8, 3)
    p.monedas(34, 6, 4)
    p.monedas(44, 8, 4)
    p.arco(48, 6, 6, 3)
    p.monedas(54, 7, 4)
    p.monedas(62, 5, 4)
    p.arco(70, 3, 7, 2)
    p.monedas(76, 5, 5)
    p.monedas(86, 7, 4)
    p.arco(92, 6, 6, 3)
    p.monedas(98, 6, 5)
    p.monedas(108, 3, 5)
    p.arco(116, 2, 7, 2)
    p.monedas(122, 3, 5)
    p.monedas(132, 6, 4)
    p.monedas(140, 8, 6)
    p.monedas(6, 8, 3)
    p.monedas(23, 5, 3)
    return {
        "clave": "sierra", "nombre": "nivel_sierra", "tiempo": 240,
        "paleta": {"cielo_arriba": "#3F8FE0", "cielo_abajo": "#9CCBF2", "suelo": "#6B9B3A", "tierra": "#7A5230"},
        "fondo": ["volcanes", "paramo", "pasto_cercano"],
        "enemigo": "condor", "coleccionable": "rosa", "comida": "empanada_viento", "musica": "sierra",
        "bloques_especiales": {(9, 5): "coleccionable", (11, 5): "comida", (13, 5): "coleccionable",
                               (87, 4): "comida", (140, 5): "coleccionable", (142, 5): "comida"},
        "mapa": p.lineas(),
    }


def nivel_amazonia():
    p = Plano(150)
    p.perfil([(0, 19, 0), (20, 22, "W"), (23, 29, 0), (30, 31, 2), (32, 43, 0), (44, 56, "W"),
              (57, 70, 0), (71, 72, 2), (73, 85, 0), (86, 88, "W"), (89, 99, 0), (100, 101, 2),
              (102, 113, 0), (114, 126, "W"), (127, 149, 0)])
    # plataformas (troncos) entre arboles: sobre el rio forman una escalera
    p.tablones([(46, 8, 4), (52, 7, 4)])
    p.tablones([(116, 8, 4), (122, 7, 4)])
    p.marcar([3], "P")
    p.marcar([144], "F")
    p.bloques(9, 5, "?B?B?")
    p.bloques(76, 5, "?B?")
    p.bloques(104, 5, "B?B?")
    p.checkpoints([40, 95])
    p.enemigos([6, 26, 60, 66, 92, 98, 130, 134, 138, 141])
    p.monedas(14, 8, 4)
    p.arco(18, 7, 7, 3)
    p.monedas(24, 8, 4)
    p.monedas(32, 6, 4)
    p.monedas(47, 7, 2)
    p.monedas(53, 6, 2)
    p.arco(44, 6, 13, 2)
    p.monedas(58, 8, 4)
    p.arco(84, 7, 6, 3)
    p.monedas(90, 8, 4)
    p.monedas(100, 6, 3)
    p.arco(112, 6, 6, 3)
    p.monedas(117, 7, 2)
    p.monedas(123, 6, 2)
    p.arco(126, 6, 6, 3)
    p.monedas(134, 8, 5)
    p.monedas(40, 8, 3)
    p.monedas(66, 8, 3)
    p.monedas(10, 3, 4)
    p.monedas(76, 3, 3)
    return {
        "clave": "amazonia", "nombre": "nivel_amazonia", "tiempo": 240,
        "paleta": {"cielo_arriba": "#A8D8A0", "cielo_abajo": "#5FAE6B", "suelo": "#5A3D24", "follaje": "#1F6B2E"},
        "fondo": ["niebla_selva", "arboles", "lianas_helechos"],
        "enemigo": "mono", "coleccionable": "orquidea", "comida": "maito", "musica": "amazonia",
        "bloques_especiales": {(9, 5): "coleccionable", (11, 5): "comida", (13, 5): "coleccionable",
                               (77, 5): "comida", (105, 5): "coleccionable", (107, 5): "comida"},
        "mapa": p.lineas(),
    }


def nivel_galapagos():
    p = Plano(150)
    p.perfil([(0, 11, 0), (12, 15, 1), (16, 21, 0), (22, 24, "W"), (25, 30, 1), (31, 36, 2),
              (37, 40, 1), (41, 44, "W"), (45, 52, 1), (53, 58, 0), (59, 61, "W"), (62, 70, 1),
              (71, 76, 2), (77, 80, "W"), (81, 90, 1), (91, 96, 0), (97, 100, "W"), (101, 108, 1),
              (109, 114, 2), (115, 120, 1), (121, 123, "W"), (124, 135, 0), (136, 149, 1)])
    p.marcar([3], "P")
    p.marcar([144], "F")
    p.bloques(8, 5, "?B?B?")
    p.bloques(64, 4, "B?B?")
    p.bloques(126, 5, "?B?")
    p.checkpoints([50, 105])
    p.enemigos([8, 27, 46, 63, 83, 104, 106, 128, 134, 140])
    p.monedas(13, 6, 3)
    p.arco(20, 7, 8, 3)
    p.monedas(26, 7, 3)
    p.monedas(32, 5, 4)
    p.arco(40, 6, 8, 3)
    p.monedas(46, 7, 4)
    p.monedas(54, 8, 4)
    p.arco(58, 7, 7, 3)
    p.monedas(63, 6, 4)
    p.monedas(72, 5, 4)
    p.arco(75, 6, 8, 3)
    p.monedas(82, 7, 4)
    p.monedas(92, 8, 4)
    p.arco(96, 7, 7, 3)
    p.monedas(102, 7, 4)
    p.monedas(110, 5, 4)
    p.arco(119, 6, 7, 3)
    p.monedas(126, 8, 5)
    p.monedas(138, 6, 5)
    p.monedas(8, 3, 4)
    p.monedas(64, 2, 3)
    p.monedas(31, 7, 3)
    return {
        "clave": "galapagos", "nombre": "nivel_galapagos", "tiempo": 240,
        "paleta": {"cielo_arriba": "#F6C98A", "cielo_abajo": "#7FD3D8", "suelo": "#34343E", "lava": "#4A4A56",
                   "agua": "#2BB5C0", "cactus": "#6FA83A"},
        "fondo": ["mar_islas", "cactus_lava", "rocas_cercanas"],
        "enemigo": "iguana", "coleccionable": "concha", "comida": "ceviche", "musica": "galapagos",
        "bloques_especiales": {(8, 5): "coleccionable", (10, 5): "comida", (12, 5): "coleccionable",
                               (65, 4): "comida", (67, 4): "coleccionable", (126, 5): "coleccionable",
                               (128, 5): "comida"},
        "mapa": p.lineas(),
    }


def nivel_cotopaxi():
    p = Plano(40)
    p.perfil([(0, 39, 0)])
    # muros laterales de la arena
    for fila in range(2, 9):
        p.poner(0, fila, "#")
        p.poner(39, fila, "#")
    p.marcar([3], "P")
    p.marcar([37], "F")
    # tres plataformas altas con sellos de hielo
    p.tablones([(6, 7, 4)])
    p.poner(7, 6, "S")
    p.tablones([(12, 7, 3)])
    p.tablones([(17, 5, 5)])
    p.poner(19, 4, "S")
    p.tablones([(28, 7, 4)])
    p.poner(30, 6, "S")
    p.bloques(24, 5, "?")
    p.checkpoints([14, 26])
    p.enemigos([22, 33])
    p.monedas(10, 8, 2)
    p.monedas(12, 6, 3)
    p.monedas(17, 4, 3)
    p.monedas(34, 8, 2)
    return {
        "clave": "cotopaxi", "nombre": "nivel_cotopaxi", "tiempo": 180, "jefe": True,
        "paleta": {"cielo_arriba": "#3B1A2A", "cielo_abajo": "#C4452B", "suelo": "#2E2A33", "nieve": "#E8EEF5",
                   "lava": "#FF8A1F", "hielo": "#9FE3FF"},
        "fondo": ["cielo_ceniza", "montanas", "humo_lava"],
        "enemigo": "ceniza", "coleccionable": "sello_hielo", "comida": "colada_morada", "musica": "cotopaxi",
        "bloques_especiales": {(24, 5): "comida"},
        "mapa": p.lineas(),
    }


# ======================================================================
#  Escritura de archivos
# ======================================================================
ENCABEZADOS = {
    "costa": ("NIVEL_COSTA", "Nivel 1 - Costa: playa, manglar y mar. Cangrejos, bananos y cacao. Comida: bolon."),
    "sierra": ("NIVEL_SIERRA", "Nivel 2 - Sierra: Andes y volcanes. Condores y rosas. Comida: empanada de viento."),
    "amazonia": ("NIVEL_AMAZONIA", "Nivel 3 - Amazonia: selva y rio. Monos y orquideas. Comida: maito."),
    "galapagos": ("NIVEL_GALAPAGOS", "Nivel 4 - Galapagos: roca volcanica. Iguanas y conchas. Comida: ceviche."),
    "cotopaxi": ("NIVEL_COTOPAXI", "Nivel 5 - Cotopaxi (jefe): toca los 3 sellos de hielo para calmar al volcan."),
}


def py(valor):
    """Escribe un valor de Python con comillas dobles (para que los archivos queden uniformes)."""
    if isinstance(valor, bool):
        return str(valor)
    if isinstance(valor, str):
        return json.dumps(valor, ensure_ascii=False)
    if isinstance(valor, (list, tuple)):
        return "[" + ", ".join(py(v) for v in valor) + "]"
    if isinstance(valor, dict):
        return "{" + ", ".join("%s: %s" % (py(k), py(v)) for k, v in valor.items()) + "}"
    return repr(valor)


def escribir(datos):
    clave = datos["clave"]
    nombre_var, descripcion = ENCABEZADOS[clave]
    ruta = os.path.join(RAIZ, "niveles", clave + ".py")
    lineas = ['"""%s' % descripcion, "", "Leyenda: # suelo  = plataforma  B ladrillo  ? bloque especial  C coleccionable",
              "         E enemigo  K checkpoint  P inicio  F bandera  W agua  S sello de hielo", '"""', "",
              "%s = {" % nombre_var]
    for campo in ("clave", "nombre", "tiempo", "jefe", "paleta", "fondo", "enemigo", "coleccionable", "comida", "musica"):
        if campo in datos:
            lineas.append("    %s: %s," % (py(campo), py(datos[campo])))
    lineas.append('    "bloques_especiales": {            # (columna, fila): contenido')
    for (c, f), contenido in sorted(datos["bloques_especiales"].items()):
        lineas.append("        (%d, %d): %s," % (c, f, py(contenido)))
    lineas.append("    },")
    lineas.append('    "mapa": [')
    for fila in datos["mapa"]:
        lineas.append('        "%s",' % fila)
    lineas.append("    ],")
    lineas.append("}")
    with open(ruta, "w", encoding="utf-8") as archivo:
        archivo.write("\n".join(lineas) + "\n")
    return ruta


def avisos_enemigos(datos):
    """Un enemigo no debe estar a menos de 12 baldosas antes del borde de un hueco."""
    mapa = datos["mapa"]
    if datos["enemigo"] == "condor":
        return []
    def hay_suelo(c):
        return any(mapa[f][c] in "#=" for f in range(FILAS))
    avisos = []
    for f, fila in enumerate(mapa):
        for c, s in enumerate(fila):
            if s != "E":
                continue
            for c2 in range(c + 1, min(len(fila) - 1, c + 12) + 1):
                if not hay_suelo(c2) and hay_suelo(c2 - 1):
                    avisos.append("enemigo en col %d demasiado cerca del hueco en col %d" % (c, c2))
                    break
    return avisos


def main():
    os.makedirs(os.path.join(RAIZ, "niveles"), exist_ok=True)
    for crear in (nivel_costa, nivel_sierra, nivel_amazonia, nivel_galapagos, nivel_cotopaxi):
        datos = crear()
        p = datos["mapa"]
        texto = "".join(p)
        for aviso in avisos_enemigos(datos):
            print("   AVISO", datos["clave"], aviso)
        print("%-10s %3d col | C=%3d E=%2d K=%d ?=%2d" % (datos["clave"], len(p[0]), texto.count("C"),
              texto.count("E"), texto.count("K"), texto.count("?")), "->", escribir(datos))
    with open(os.path.join(RAIZ, "niveles", "__init__.py"), "w", encoding="utf-8") as archivo:
        archivo.write('"""Lista de niveles en el orden en que se juegan."""\n'
                      "from niveles.costa import NIVEL_COSTA\n"
                      "from niveles.sierra import NIVEL_SIERRA\n"
                      "from niveles.amazonia import NIVEL_AMAZONIA\n"
                      "from niveles.galapagos import NIVEL_GALAPAGOS\n"
                      "from niveles.cotopaxi import NIVEL_COTOPAXI\n\n"
                      "LISTA_NIVELES = [NIVEL_COSTA, NIVEL_SIERRA, NIVEL_AMAZONIA, NIVEL_GALAPAGOS, NIVEL_COTOPAXI]\n")


if __name__ == "__main__":
    main()
