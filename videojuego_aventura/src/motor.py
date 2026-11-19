"""Motor: ventana, lienzo interno 320x180, bucle a 60 FPS, escenas y pantalla completa (F11)."""
import gc
import time

import pygame

import ajustes
import fondos
import guardado
import interfaz
import sprites
import textos
from entrada import EntradaTeclado


class Sesion:
    """Estado de una partida: vidas, puntaje y nivel actual."""

    def __init__(self):
        self.vidas = ajustes.VIDAS_INICIALES
        self.puntaje = 0
        self.nivel = 0
        self.grande = False
        self.coleccionables = 0   # contador hacia la vida extra (0..99)


class Escena:
    """Clase base. Cada escena tiene eventos(), actualizar(dt) y dibujar(lienzo)."""

    def __init__(self, motor):
        self.motor = motor

    def eventos(self, lista_eventos):
        pass

    def actualizar(self, dt):
        pass

    def dibujar(self, lienzo):
        pass


class Motor:
    def __init__(self, con_ventana=True):
        pygame.init()
        interfaz.reiniciar_fuentes()
        self.tamano_ventana = (ajustes.ANCHO * ajustes.ESCALA, ajustes.ALTO * ajustes.ESCALA)
        self.pantalla_completa = False
        self.ventana = pygame.display.set_mode(self.tamano_ventana)
        pygame.display.set_caption("Aventura Ecuador")
        self.lienzo = pygame.Surface((ajustes.ANCHO, ajustes.ALTO)).convert()
        self.capa_texto = None
        # todo el arte se genera una sola vez al iniciar (y queda en cache)
        inicio_arte = time.perf_counter()
        sprites.reiniciar()
        fondos.reiniciar()
        sprites.iniciar()
        fondos.generar_todos()
        interfaz.precalentar(self._rect_destino().w / ajustes.ANCHO)
        self.segundos_arte = time.perf_counter() - inicio_arte
        self.reloj = pygame.time.Clock()
        self.entrada = EntradaTeclado()
        self.escena = None
        self.corriendo = True
        self.sesion = Sesion()
        self.cuadros = 0
        self.fps_medido = 0.0
        self.sonido = None

        guardado.asegurar_archivo()
        self.datos = self._validar(guardado.leer())
        textos.fijar_idioma(self.datos["idioma"])

        # el sonido es opcional: si falla, el juego sigue sin audio
        try:
            import sonido
            self.sonido = sonido.Sonido()
        except Exception as error:  # noqa: BLE001
            print("Sin sonido:", error)
            self.sonido = None
        if self.sonido is None:
            import sonido_nulo
            self.sonido = sonido_nulo.SonidoNulo()
        # todo el material de larga vida ya existe: se saca del recolector de basura para que
        # sus pausas no se noten durante el juego
        gc.collect()
        gc.freeze()

    @staticmethod
    def _validar(datos):
        """Si puntaje.json fue editado a mano con valores raros, vuelve a los valores iniciales."""
        if datos.get("personaje") not in ajustes.PERSONAJES:
            datos["personaje"] = guardado.DATOS_INICIALES["personaje"]
        if datos.get("accesorio") not in ajustes.ACCESORIOS:
            datos["accesorio"] = guardado.DATOS_INICIALES["accesorio"]
        if datos.get("idioma") not in textos.TEXTOS:
            datos["idioma"] = "es"
        if not isinstance(datos.get("mejor_puntaje"), int):
            datos["mejor_puntaje"] = 0
        return datos

    # ------------------------------------------------------------ escenas
    def cambiar_escena(self, escena):
        self.escena = escena
        self.entrada.limpiar()

    def nueva_partida(self):
        self.sesion = Sesion()

    def guardar_preferencias(self, **cambios):
        self.datos = self._validar(guardado.actualizar(**cambios))

    def registrar_puntaje(self):
        """Guarda el puntaje si supera el mejor. Devuelve True si es un record."""
        if self.sesion.puntaje > self.datos.get("mejor_puntaje", 0):
            self.guardar_preferencias(mejor_puntaje=self.sesion.puntaje)
            return True
        return False

    def cambiar_idioma(self, idioma=None):
        if idioma is None:
            textos.alternar_idioma()
        else:
            textos.fijar_idioma(idioma)
        self.guardar_preferencias(idioma=textos.IDIOMA_ACTUAL)

    # ------------------------------------------------------------ pantalla
    def alternar_pantalla_completa(self):
        self.pantalla_completa = not self.pantalla_completa
        if self.pantalla_completa:
            self.ventana = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.ventana = pygame.display.set_mode(self.tamano_ventana)

    def _rect_destino(self):
        ancho, alto = self.ventana.get_size()
        escala = min(ancho / ajustes.ANCHO, alto / ajustes.ALTO)
        if escala >= 1:
            escala = int(escala) if escala >= 2 else escala
        w, h = int(ajustes.ANCHO * escala), int(ajustes.ALTO * escala)
        return pygame.Rect((ancho - w) // 2, (alto - h) // 2, w, h)

    def pos_mouse(self, pos):
        """Convierte una posicion de ventana en una posicion del lienzo."""
        rect = self._rect_destino()
        x = (pos[0] - rect.x) * ajustes.ANCHO / max(1, rect.w)
        y = (pos[1] - rect.y) * ajustes.ALTO / max(1, rect.h)
        return (int(x), int(y))

    def _preparar_capa_texto(self):
        """El texto se dibuja aparte, a la resolucion real de la ventana, para que se vea nitido."""
        tamano = self._rect_destino().size
        if self.capa_texto is None or self.capa_texto.get_size() != tamano:
            self.capa_texto = pygame.Surface(tamano, pygame.SRCALPHA)
            interfaz.configurar_capa(self.lienzo, self.capa_texto)
        else:
            interfaz.limpiar_capa()

    def presentar(self):
        rect = self._rect_destino()
        self.ventana.fill((0, 0, 0))
        destino = self.ventana.subsurface(rect)
        pygame.transform.scale(self.lienzo, rect.size, destino)
        if self.capa_texto is not None:
            for zona in interfaz.zonas_de_texto():
                destino.blit(self.capa_texto, zona.topleft, zona)
        pygame.display.flip()

    def guardar_captura(self, ruta):
        """Guarda la pantalla actual (arte + texto nitido) como imagen PNG."""
        tamano = self.capa_texto.get_size() if self.capa_texto is not None else self.tamano_ventana
        grande = pygame.transform.scale(self.lienzo, tamano)
        if self.capa_texto is not None:
            grande.blit(self.capa_texto, (0, 0))
        pygame.image.save(grande, ruta)

    # ------------------------------------------------------------ bucle
    def paso(self, dt, lista_eventos=None):
        """Un cuadro completo: eventos, logica, dibujo. Sirve para el bucle y para pruebas."""
        if lista_eventos is None:
            lista_eventos = pygame.event.get()
        for evento in lista_eventos:
            if evento.type == pygame.QUIT:
                self.corriendo = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_F11:
                    self.alternar_pantalla_completa()
                elif evento.key == pygame.K_m:
                    self.sonido.alternar_musica()
                elif evento.key == pygame.K_n:
                    self.sonido.alternar_efectos()
            self.entrada.procesar_evento(evento)
        self.entrada.actualizar(dt)
        if self.escena is not None:
            self.escena.eventos(lista_eventos)
            if self.escena is not None:
                self.escena.actualizar(dt)
            if self.escena is not None:
                self._preparar_capa_texto()
                self.escena.dibujar(self.lienzo)
        self.cuadros += 1

    @staticmethod
    def frecuencia_pantalla():
        """Hz del monitor (Windows). Si no se puede saber, ajustes.FPS."""
        try:
            import ctypes
            usuario, grafico = ctypes.windll.user32, ctypes.windll.gdi32
            contexto = usuario.GetDC(0)
            hz = grafico.GetDeviceCaps(contexto, 116)       # VREFRESH
            usuario.ReleaseDC(0, contexto)
            if 59 <= hz <= 360:
                return int(hz)
        except Exception:  # noqa: BLE001
            pass
        return ajustes.FPS

    def ejecutar(self, max_cuadros=None):
        """Bucle principal. Corre a la frecuencia del monitor (con 60 FPS en un monitor de 165 Hz la
        imagen va a tirones) y con un temporizador preciso: Clock.tick usa milisegundos enteros, asi que
        el dt alternaba entre 16 y 17 ms y el movimiento no era parejo."""
        fps = min(self.frecuencia_pantalla(), ajustes.FPS_MAXIMO)
        objetivo = 1.0 / fps
        espera_fina = 0.0015            # lo ultimo se espera dando vueltas: sleep() se pasa por poco
        ultimo = siguiente = time.perf_counter()
        inicio_medida = ultimo
        contados = 0
        while self.corriendo:
            resto = siguiente - time.perf_counter()
            if resto > espera_fina:
                time.sleep(resto - espera_fina)
            while time.perf_counter() < siguiente:
                pass
            ahora = time.perf_counter()
            dt = min(ahora - ultimo, ajustes.DT_MAXIMO)
            ultimo = ahora
            siguiente += objetivo
            if siguiente < ahora - objetivo:        # nos atrasamos mucho: no intentar recuperar
                siguiente = ahora + objetivo
            self.paso(dt)
            self.presentar()
            contados += 1
            if ahora - inicio_medida >= 1.0:
                self.fps_medido = contados / (ahora - inicio_medida)
                inicio_medida = ahora
                contados = 0
            if max_cuadros is not None and self.cuadros >= max_cuadros:
                break
        self.cerrar()

    def cerrar(self):
        self.registrar_puntaje()
        pygame.quit()
