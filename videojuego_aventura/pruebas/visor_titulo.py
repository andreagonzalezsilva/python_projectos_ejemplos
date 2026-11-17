"""Herramienta de desarrollo: dibuja la tipografia Inca (alfabeto y titulos) en capturas/hoja_inca.png."""
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "src"))
sys.path.insert(0, RAIZ)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

import letras_inca  # noqa: E402


def main():
    pygame.init()
    pygame.display.set_mode((100, 100))
    hoja = pygame.Surface((1280, 720))
    hoja.fill((52, 120, 205))
    y = 10
    for cadena in ("Aventura Ecuador", "Ecuador Adventure"):
        imagen = letras_inca.crear_titulo(cadena, 66, ancho_max_px=1200)
        hoja.blit(imagen, ((1280 - imagen.get_width()) // 2, y))
        y += imagen.get_height() + 6
    letras = "ABCDEFGHIJKLM", "NOPQRSTUVWXYZ"
    for fila in letras:
        imagen = letras_inca.crear_titulo(fila, 56, con_chakana=False)
        hoja.blit(imagen, ((1280 - imagen.get_width()) // 2, y))
        y += imagen.get_height() + 4
    ruta = os.path.join(RAIZ, "capturas", "hoja_inca.png")
    pygame.image.save(hoja, ruta)
    print("guardado", ruta)


if __name__ == "__main__":
    main()
