"""Funciones comunes para las pruebas sin ventana (niveles de prueba y simulacion guionizada)."""
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "src"))
sys.path.insert(0, RAIZ)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

import ajustes  # noqa: E402
import fondos  # noqa: E402
import interfaz  # noqa: E402
import sprites  # noqa: E402
from entrada import Entrada, EntradaGuion  # noqa: E402
from motor import Sesion  # noqa: E402
from nivel import cargar_nivel  # noqa: E402
from sonido_nulo import SonidoNulo  # noqa: E402

DT = 1 / 60
CAPTURAS = os.path.join(RAIZ, "capturas")


def iniciar_pygame():
    if not pygame.get_init() or pygame.display.get_surface() is None:
        pygame.init()
        pygame.display.set_mode((ajustes.ANCHO * ajustes.ESCALA, ajustes.ALTO * ajustes.ESCALA))
        interfaz.reiniciar_fuentes()
    sprites.iniciar()
    fondos.generar_todos()


def mapa_vacio(columnas, filas=11):
    return [" " * columnas for _ in range(filas)]


def poner(mapa, fila, col, texto):
    """Escribe 'texto' en el mapa (lista de strings) a partir de (fila, col)."""
    linea = mapa[fila]
    mapa[fila] = linea[:col] + texto + linea[col + len(texto):]


def datos_prueba(mapa, region="costa", **extra):
    datos = {
        "clave": region,
        "nombre": "nivel_" + region,
        "tiempo": 240,
        "enemigo": {"costa": "cangrejo", "sierra": "condor", "amazonia": "mono", "galapagos": "iguana",
                    "cotopaxi": "ceniza"}[region],
        "coleccionable": "banano",
        "comida": "bolon",
        "bloques_especiales": {},
        "mapa": mapa,
    }
    datos.update(extra)
    return datos


def crear_nivel(datos, personaje="lorena", accesorio="poncho", sesion=None):
    iniciar_pygame()
    sesion = sesion or Sesion()
    return cargar_nivel(datos, sesion, SonidoNulo(), personaje, accesorio)


def simular(nivel, pasos, al_cuadro=None, entrada=None):
    """Ejecuta el nivel con un guion [(segundos, 'acciones'), ...]. Devuelve la entrada usada."""
    entrada = entrada or EntradaGuion(pasos)
    cuadros = 0
    while not entrada.terminado:
        entrada.actualizar(DT)
        nivel.actualizar(DT, entrada)
        cuadros += 1
        if al_cuadro:
            if al_cuadro(nivel, cuadros) is True:
                break
    return entrada


def correr_piloto(nivel, segundos_max=240.0):
    """Hace correr el piloto automatico hasta completar el nivel. Devuelve (completo, segundos)."""
    piloto = Piloto(nivel)
    t = 0.0
    while t < segundos_max and not piloto.terminado():
        piloto.actualizar(DT)
        nivel.actualizar(DT, piloto)
        t += DT
        if nivel.estado == "muerto":
            piloto.t_atasco = 0
    return nivel.estado == "completo", t


def esperar(nivel, segundos, acciones=""):
    simular(nivel, [(segundos, acciones)])


def guardar_lienzo(nivel, nombre, hud=None):
    """Dibuja el nivel y guarda la captura: arte en 320x180 ampliado + texto nitido a 1280x720."""
    lienzo = pygame.Surface((ajustes.ANCHO, ajustes.ALTO))
    capa = pygame.Surface((1280, 720), pygame.SRCALPHA)
    interfaz.configurar_capa(lienzo, capa)
    nivel.dibujar(lienzo)
    if hud:
        hud(lienzo)
    imagen = pygame.transform.scale(lienzo, (1280, 720))
    imagen.blit(capa, (0, 0))
    interfaz.configurar_capa(None, None)
    os.makedirs(CAPTURAS, exist_ok=True)
    ruta = os.path.join(CAPTURAS, nombre)
    pygame.image.save(imagen, ruta)
    return ruta


class Piloto(Entrada):
    """Robot de pruebas: corre hacia la derecha y salta ante muros, huecos y enemigos."""

    def __init__(self, nivel):
        super().__init__()
        self.nivel = nivel
        self.salto_previo = False
        self.ultimo_x = 0.0
        self.t_atasco = 0.0

    def terminado(self):
        return self.nivel.estado in ("completo", "game_over")

    def actualizar(self, dt):
        n = self.nivel
        j = n.jugador
        self.derecha = True
        self.izquierda = False
        self.correr = True
        quiere_saltar = False
        if n.estado == "jugando" and not j.muriendo:
            frente = j.x + j.w
            fila_pies = int((j.y + j.h - 1) // 16)
            fila_cabeza = int(j.y // 16)
            col_muro = int((frente + 10) // 16)
            if any(n.es_solido(col_muro, f) for f in range(fila_cabeza, fila_pies + 1)):
                quiere_saltar = True
            if j.en_suelo:
                col_borde = int((frente + 2) // 16)
                if not any(n.es_solido(col_borde, f) for f in range(fila_pies + 1, fila_pies + 7)):
                    quiere_saltar = True
                hueco_cerca = any(not any(n.rejilla[f][cc] in "#=" for f in range(n.filas))
                                  for cc in range(int(frente // 16), min(n.columnas, int(frente // 16) + 14)))
                if hueco_cerca:
                    j.invulnerable = max(j.invulnerable, 0.3)   # solo para la prueba: ignora enemigos
                for e in ([] if hueco_cerca else n.enemigos):
                    dx = e.x - frente
                    if e.activo and not e.muriendo and 0 < dx < 34 and abs((e.y + e.h) - (j.y + j.h)) < 26:
                        quiere_saltar = True
            if abs(j.x - self.ultimo_x) < 0.2:
                self.t_atasco += dt
            else:
                self.t_atasco = 0.0
                self.ultimo_x = j.x
            if self.t_atasco > 0.4:
                quiere_saltar = True
        self.salto = quiere_saltar and j.en_suelo
        self.salto_presionado = quiere_saltar or (not j.en_suelo and j.vy < 0)
        self.salto_previo = quiere_saltar


class Verificador:
    """Cuenta aciertos y fallos e imprime un resumen."""

    def __init__(self, titulo):
        self.titulo = titulo
        self.fallos = 0
        self.total = 0
        print("== %s ==" % titulo)

    def comprobar(self, condicion, descripcion, detalle=""):
        self.total += 1
        if not condicion:
            self.fallos += 1
        print("  [%s] %s %s" % ("OK" if condicion else "FALLA", descripcion, detalle))
        return condicion

    def terminar(self):
        print("-> %d/%d comprobaciones correctas" % (self.total - self.fallos, self.total))
        return self.fallos == 0
