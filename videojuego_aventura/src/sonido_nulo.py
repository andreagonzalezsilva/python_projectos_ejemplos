"""Sonido vacio: se usa cuando no hay dispositivo de audio. Acepta todas las llamadas y no hace nada."""


class SonidoNulo:
    hay_audio = False
    musica_silenciada = True
    efectos_silenciados = True

    def efecto(self, nombre):
        pass

    def musica(self, nombre):
        pass

    def parar_musica(self):
        pass

    def alternar_musica(self):
        return False

    def alternar_efectos(self):
        return False
