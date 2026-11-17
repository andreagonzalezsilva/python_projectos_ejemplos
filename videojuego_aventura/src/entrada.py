"""Abstraccion de entrada. El jugador lee un objeto Entrada, nunca el teclado directo.

EntradaTeclado lee el teclado real. EntradaGuion reproduce una lista de acciones
por tiempo, para poder probar el juego sin ventana ni persona.
"""
import pygame


class Entrada:
    """Interfaz comun: cinco valores que el jugador consulta en cada cuadro."""

    def __init__(self):
        self.izquierda = False
        self.derecha = False
        self.salto = False             # True solo en el cuadro en que se pulsa
        self.salto_presionado = False  # True mientras se mantiene
        self.correr = False

    def procesar_evento(self, evento):
        pass

    def actualizar(self, dt):
        pass

    def limpiar(self):
        self.izquierda = self.derecha = self.salto = False
        self.salto_presionado = self.correr = False


class EntradaTeclado(Entrada):
    TECLAS_IZQUIERDA = (pygame.K_LEFT, pygame.K_a)
    TECLAS_DERECHA = (pygame.K_RIGHT, pygame.K_d)
    TECLAS_SALTO = (pygame.K_SPACE, pygame.K_w, pygame.K_UP)
    TECLAS_CORRER = (pygame.K_LSHIFT, pygame.K_RSHIFT)

    def __init__(self):
        super().__init__()
        self._salto_pendiente = False

    def procesar_evento(self, evento):
        if evento.type == pygame.KEYDOWN and evento.key in self.TECLAS_SALTO:
            self._salto_pendiente = True

    def actualizar(self, dt):
        teclas = pygame.key.get_pressed()
        self.izquierda = any(teclas[k] for k in self.TECLAS_IZQUIERDA)
        self.derecha = any(teclas[k] for k in self.TECLAS_DERECHA)
        self.salto_presionado = any(teclas[k] for k in self.TECLAS_SALTO)
        self.correr = any(teclas[k] for k in self.TECLAS_CORRER)
        self.salto = self._salto_pendiente
        self._salto_pendiente = False


class EntradaGuion(Entrada):
    """Reproduce pasos seguidos: [(duracion_en_segundos, "derecha correr salto"), ...]."""

    def __init__(self, pasos):
        super().__init__()
        self.pasos = list(pasos)
        self.indice = 0
        self.tiempo_paso = 0.0
        self._salto_anterior = False

    @property
    def terminado(self):
        return self.indice >= len(self.pasos)

    def actualizar(self, dt):
        if self.terminado:
            self.limpiar()
            self._salto_anterior = False
            return
        duracion, acciones = self.pasos[self.indice]
        acciones = acciones.split()
        self.izquierda = "izquierda" in acciones
        self.derecha = "derecha" in acciones
        self.correr = "correr" in acciones
        self.salto_presionado = "salto" in acciones
        self.salto = self.salto_presionado and not self._salto_anterior
        self._salto_anterior = self.salto_presionado
        self.tiempo_paso += dt
        if self.tiempo_paso >= duracion - 1e-9:
            self.tiempo_paso -= duracion
            self.indice += 1
