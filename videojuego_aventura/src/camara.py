"""Camara que sigue al jugador con suavizado y nunca muestra fuera del mapa."""
import ajustes


class Camara:
    def __init__(self, ancho_nivel_px):
        self.ancho_nivel = ancho_nivel_px
        self.x = 0.0
        self.temblor = 0.0          # intensidad en px (la usa el jefe)
        self._mirada = 0.0

    def _limitar(self, valor):
        return max(0.0, min(valor, max(0, self.ancho_nivel - ajustes.ANCHO)))

    def centrar(self, jugador):
        """Salta de golpe a la posicion del jugador (al empezar o reaparecer)."""
        self.x = self._limitar(jugador.x + jugador.w / 2 - ajustes.ANCHO / 2)

    def seguir(self, jugador, dt):
        """Se acerca suavemente al jugador, mirando un poco hacia donde camina."""
        direccion = 1 if jugador.derecha else -1
        self._mirada += (direccion * 24 - self._mirada) * min(1.0, 3 * dt)
        objetivo = self._limitar(jugador.x + jugador.w / 2 - ajustes.ANCHO / 2 + self._mirada)
        self.x += (objetivo - self.x) * min(1.0, 8 * dt)
        self.x = self._limitar(self.x)

    @property
    def entero(self):
        return int(round(self.x))
