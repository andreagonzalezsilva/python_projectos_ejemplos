"""Todos los textos visibles del juego, en espanol e ingles.

Para cambiar un texto basta con editar este diccionario. La funcion t() devuelve
el texto en el idioma activo; si la clave no existe devuelve la clave.
"""

IDIOMA_ACTUAL = "es"
IDIOMAS = ["es", "en"]
NOMBRES_IDIOMA = {"es": "ES – Español", "en": "EN – English"}

TEXTOS = {
    "es": {
        "titulo": "Aventura Ecuador",
        "jugar": "Jugar",
        "salir": "Salir",
        "elige_personaje": "Elige tu personaje",
        "elige_accesorio": "Elige tu accesorio",
        "mejor_puntaje": "Mejor puntaje",
        "pausa": "Pausa",
        "continuar": "Continuar",
        "salir_menu": "Salir al menú",
        "nivel_costa": "Costa",
        "nivel_sierra": "Sierra",
        "nivel_amazonia": "Amazonía",
        "nivel_galapagos": "Galápagos",
        "nivel_cotopaxi": "Cotopaxi",
        "game_over": "Fin del juego",
        "victoria": "¡Lo lograste!",
        "poncho": "Poncho",
        "toquilla": "Paja toquilla",
        "otavalo": "Sombrero otavaleño",
        "chullo": "Chullo",
        "puntaje": "Puntaje",
        "tiempo": "Tiempo",
        "bono_tiempo": "Bono de tiempo",
        "nivel_completo": "¡Nivel completo!",
        "puntaje_total": "Puntaje total",
        "nuevo_record": "¡Nuevo récord!",
        "enter_continuar": "Pulsa Enter para continuar",
        "controles": "Flechas: mover  Espacio: saltar  Shift: correr",
        "idioma_tecla": "L: idioma",
        "prueba_texto": "Galápagos, Año, Andrés",
        "vidas": "Vidas",
        "region": "Región",
        "mensaje_sellos": "¡Toca los 3 sellos de hielo!",
        "mensaje_volcan_calmado": "¡El volcán se calmó! Ve a la bandera",
    },
    "en": {
        "titulo": "Ecuador Adventure",
        "jugar": "Play",
        "salir": "Quit",
        "elige_personaje": "Choose your character",
        "elige_accesorio": "Choose your accessory",
        "mejor_puntaje": "High score",
        "pausa": "Paused",
        "continuar": "Resume",
        "salir_menu": "Quit to menu",
        "nivel_costa": "Coast",
        "nivel_sierra": "Highlands",
        "nivel_amazonia": "Amazon",
        "nivel_galapagos": "Galápagos",
        "nivel_cotopaxi": "Cotopaxi",
        "game_over": "Game over",
        "victoria": "You did it!",
        "poncho": "Poncho",
        "toquilla": "Toquilla straw hat",
        "otavalo": "Otavalo hat",
        "chullo": "Chullo hat",
        "puntaje": "Score",
        "tiempo": "Time",
        "bono_tiempo": "Time bonus",
        "nivel_completo": "Level complete!",
        "puntaje_total": "Total score",
        "nuevo_record": "New record!",
        "enter_continuar": "Press Enter to continue",
        "controles": "Arrows: move  Space: jump  Shift: run",
        "idioma_tecla": "L: language",
        "prueba_texto": "Galápagos, Año, Andrés",
        "vidas": "Lives",
        "region": "Region",
        "mensaje_sellos": "Touch the 3 ice seals!",
        "mensaje_volcan_calmado": "The volcano calmed down! Go to the flag",
    },
}


def fijar_idioma(idioma):
    """Cambia el idioma activo si es uno de los soportados."""
    global IDIOMA_ACTUAL
    if idioma in TEXTOS:
        IDIOMA_ACTUAL = idioma


def alternar_idioma():
    """Pasa de espanol a ingles y viceversa. Devuelve el nuevo idioma."""
    siguiente = IDIOMAS[(IDIOMAS.index(IDIOMA_ACTUAL) + 1) % len(IDIOMAS)]
    fijar_idioma(siguiente)
    return IDIOMA_ACTUAL


def t(clave):
    """Devuelve el texto de la clave en el idioma activo (o la clave si falta)."""
    return TEXTOS[IDIOMA_ACTUAL].get(clave, clave)
