"""Herramienta de desarrollo: dibuja en una hoja todos los sprites y guarda los fondos.

Uso (sin ventana):  SDL_VIDEODRIVER=dummy python pruebas/visor_sprites.py
Genera capturas/hoja_sprites.png y capturas/fondo_<region>.png
"""
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "src"))
sys.path.insert(0, RAIZ)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

import ajustes  # noqa: E402
import fondos  # noqa: E402
import interfaz  # noqa: E402
import sprites  # noqa: E402

CAPTURAS = os.path.join(RAIZ, "capturas")


def main():
    pygame.init()
    pygame.display.set_mode((1280, 720))
    os.makedirs(CAPTURAS, exist_ok=True)

    t_sprites = sprites.iniciar()
    inicio = pygame.time.get_ticks()
    fondos.generar_todos()
    t_fondos = (pygame.time.get_ticks() - inicio) / 1000.0
    print("Sprites: %.2f s | Fondos: %.2f s | Total: %.2f s" % (t_sprites, t_fondos, t_sprites + t_fondos))

    hoja = pygame.Surface((400, 300))
    hoja.fill((52, 56, 84))
    y = 3
    interfaz.texto(hoja, "32 personajes (8 x 4 accesorios)", (4, y), tam=8)
    y += 11
    for fila, acc in enumerate(ajustes.ORDEN_ACCESORIOS):
        for col, clave in enumerate(ajustes.ORDEN_PERSONAJES):
            hoja.blit(sprites.personaje(clave, acc, False, "quieto", 0, True), (4 + col * 19, y + fila * 19))
    # grandes
    for col, acc in enumerate(ajustes.ORDEN_ACCESORIOS):
        hoja.blit(sprites.personaje("lorena", acc, True, "quieto", 0, True), (170 + col * 19, y))
        hoja.blit(sprites.personaje("daniela", acc, True, "quieto", 0, True), (170 + col * 19, y + 34))
    # animaciones
    ax = 250
    for i in range(4):
        hoja.blit(sprites.personaje("killari", "chullo", False, "caminar", i, True), (ax + i * 18, y))
    hoja.blit(sprites.personaje("killari", "chullo", False, "saltar", 0, True), (ax + 72, y))
    hoja.blit(sprites.personaje("killari", "chullo", False, "caer", 0, True), (ax + 90, y))
    for i in range(4):
        hoja.blit(sprites.personaje("mateo", "toquilla", False, "caminar", i, False), (ax + i * 18, y + 20))
    hoja.blit(sprites.personaje("mateo", "toquilla", False, "saltar", 0, False), (ax + 72, y + 20))
    hoja.blit(sprites.personaje("mateo", "toquilla", False, "caer", 0, False), (ax + 90, y + 20))
    for i in range(4):
        hoja.blit(sprites.personaje("joel", "otavalo", False, "caminar", i, True), (ax + i * 18, y + 40))
    hoja.blit(sprites.cabeza("joel", "otavalo"), (ax + 80, y + 44))

    y = 100
    interfaz.texto(hoja, "Enemigos", (4, y), tam=8)
    x = 4
    for tipo, anim in (("cangrejo", "caminar"), ("cangrejo", "aplastado"), ("condor", "volar"),
                       ("mono", "caminar"), ("mono", "aplastado"), ("iguana", "caminar"),
                       ("iguana", "aturdida"), ("ceniza", "caer"), ("roca", "caer")):
        n = len(sprites.CACHE["enemigos"][tipo][anim])
        for i in range(n):
            hoja.blit(sprites.enemigo(tipo, anim, i, True), (x, y + 12))
            x += 18
    y = 135
    interfaz.texto(hoja, "Comidas y coleccionables", (4, y), tam=8)
    x = 4
    for clave in ("bolon", "empanada_viento", "maito", "ceviche", "colada_morada"):
        hoja.blit(sprites.comida(clave), (x, y + 12))
        x += 20
    x += 8
    for clave in ("banano", "cacao", "rosa", "orquidea", "concha", "sello_hielo"):
        hoja.blit(sprites.coleccionable(clave), (x, y + 14))
        x += 16
    x += 6
    hoja.blit(sprites.CACHE["sello_jefe"]["activo"], (x, y + 12))
    hoja.blit(sprites.CACHE["sello_jefe"]["apagado"], (x + 18, y + 12))

    y = 168
    interfaz.texto(hoja, "Bloques, bandera, checkpoint", (4, y), tam=8)
    x = 4
    hoja.blit(sprites.bloque("ladrillo"), (x, y + 12))
    for i, s in enumerate(sprites.CACHE["bloques"]["signo"]):
        hoja.blit(s, (x + 18 + i * 17, y + 12))
    hoja.blit(sprites.bloque("usado"), (x + 18 + 4 * 17, y + 12))
    hoja.blit(sprites.CACHE["checkpoint"]["apagado"], (x + 120, y + 12))
    hoja.blit(sprites.CACHE["checkpoint"]["activo"][0], (x + 138, y + 12))
    hoja.blit(sprites.CACHE["bandera_meta"][0], (x + 160, y + 12))
    hoja.blit(sprites.CACHE["bandera_meta"][1], (x + 180, y + 12))
    hoja.blit(sprites.bandera_ecuador(40, 26, 0), (x + 205, y + 14))

    y = 252
    for fila, region in enumerate(("costa", "sierra", "amazonia", "galapagos", "cotopaxi")):
        t = sprites.terreno(region)
        x = 4 + fila * 76
        hoja.blit(t["tope"], (x, y))
        hoja.blit(t["relleno"], (x, y + 16))
        hoja.blit(t["plataforma"], (x + 17, y))
        for i, agua in enumerate(t["agua"][:2]):
            hoja.blit(agua, (x + 34 + i * 16, y))
        interfaz.texto(hoja, region[:6], (x, y + 33), tam=7)

    pygame.image.save(pygame.transform.scale(hoja, (1600, 1200)), os.path.join(CAPTURAS, "hoja_sprites.png"))

    for region in ("costa", "sierra", "amazonia", "galapagos", "cotopaxi"):
        lienzo = pygame.Surface((ajustes.ANCHO, ajustes.ALTO))
        fondos.obtener(region).dibujar(lienzo, 0)
        t = sprites.terreno(region)
        for col in range(20):
            lienzo.blit(t["tope"], (col * 16, 144))
            lienzo.blit(t["relleno"], (col * 16, 160))
        pygame.image.save(pygame.transform.scale(lienzo, (1280, 720)),
                          os.path.join(CAPTURAS, "fondo_%s.png" % region))
    print("Capturas guardadas en", CAPTURAS)


if __name__ == "__main__":
    main()
