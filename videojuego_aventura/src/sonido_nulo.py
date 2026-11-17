"""Sonido vacio: se usa cuando no hay dispositivo de audio. Acepta todas las llamadas y no hace nada."""


class SonidoNulo:
    silenciado = True

    def efecto(self, nombre):
        pass

    def musica(self, nombre):
        pass

    def parar_musica(self):
        pass

    def alternar_silencio(self):
        pass
