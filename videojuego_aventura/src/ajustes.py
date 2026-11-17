"""Constantes del juego: pantalla, fisica, colores, personajes y accesorios.

Todo lo que se pueda querer cambiar (velocidades, nombres, colores) vive aqui.
"""

# ---------------------------------------------------------------- pantalla
ANCHO = 320            # ancho del lienzo interno (px)
ALTO = 180             # alto del lienzo interno (px)
ESCALA = 4             # la ventana mide 1280x720
FPS = 60
DT_MAXIMO = 1 / 30     # limite del paso de tiempo para evitar saltos
BALDOSA = 16           # tamano de una baldosa (px)
FILAS_NIVEL = 11       # altura del nivel en baldosas (176 px)

# ---------------------------------------------------------------- fisica del jugador
GRAVEDAD = 900
VEL_CAMINAR = 90
VEL_CORRER = 140
ACEL_SUELO = 600
FRENO_SUELO = 700
CONTROL_AIRE = 0.6
VEL_SALTO = -300
CORTE_SALTO = 0.5
VEL_CAIDA_MAX = 400
TIEMPO_COYOTE = 0.08
TIEMPO_BUFFER = 0.10
HITBOX_PEQUENO = (12, 16)
HITBOX_GRANDE = (12, 30)
REBOTE_PISOTON = -200
TIEMPO_INVULNERABLE = 2.0

# ---------------------------------------------------------------- reglas
VIDAS_INICIALES = 3
TIEMPO_NIVEL = 240
TIEMPO_JEFE = 180
PUNTOS_ENEMIGO = 100
PUNTOS_COLECCIONABLE = 10
PUNTOS_COMIDA_GRANDE = 1000
PUNTOS_POR_SEGUNDO = 10
COLECCIONABLES_VIDA = 100

# ---------------------------------------------------------------- comida
VEL_COMIDA = 40

# ---------------------------------------------------------------- enemigos
VEL_CANGREJO = 30
VEL_CONDOR = 50
AMPLITUD_CONDOR = 20
VEL_MONO = 40
SALTO_MONO = -220
INTERVALO_SALTO_MONO = 1.2
VEL_IGUANA = 20
TIEMPO_ATURDIDA = 3.0

# ---------------------------------------------------------------- jefe
JEFE_CALMA = 4.0
JEFE_AVISO = 1.5
JEFE_ERUPCION = 3.0

# ---------------------------------------------------------------- colores
COLORES = {
    "negro": "#14121C",
    "blanco": "#FFFFFF",
    "amarillo": "#F6C915",
    "azul": "#1F3E8C",
    "rojo": "#C8242B",
    "gris": "#8A8FA0",
    "oscuro": "#2B2B33",
    "fondo_menu": "#1B2A5E",
    "texto": "#FFFFFF",
    "sombra": "#14121C",
    "seleccion": "#F6C915",
}


def color(hexa):
    """Convierte '#RRGGBB' en una tupla (r, g, b)."""
    hexa = hexa.lstrip("#")
    return (int(hexa[0:2], 16), int(hexa[2:4], 16), int(hexa[4:6], 16))


# ---------------------------------------------------------------- personajes
# Mismo cuerpo para todos. Cambian piel, cabello y peinado.
PERSONAJES = {
    "lorena": {"nombre": "Lorena", "piel": "#C68E5E", "cabello": "#3B2416", "peinado": "largo_ondulado"},
    "camila": {"nombre": "Camila", "piel": "#F1C9A5", "cabello": "#8B5A33", "peinado": "cola"},
    "killari": {"nombre": "Killari", "piel": "#A8693F", "cabello": "#15121A", "peinado": "trenza_larga"},
    "daniela": {"nombre": "Daniela", "piel": "#6B4226", "cabello": "#15121A", "peinado": "rizado_grande"},
    "andres": {"nombre": "Andrés", "piel": "#C68E5E", "cabello": "#15121A", "peinado": "corto"},
    "mateo": {"nombre": "Mateo", "piel": "#F1C9A5", "cabello": "#8B5A33", "peinado": "corto"},
    "yaku": {"nombre": "Yaku", "piel": "#A8693F", "cabello": "#15121A", "peinado": "trenza_corta"},
    "joel": {"nombre": "Joel", "piel": "#6B4226", "cabello": "#15121A", "peinado": "rizado_corto"},
}
ORDEN_PERSONAJES = ["lorena", "camila", "killari", "daniela", "andres", "mateo", "yaku", "joel"]

# Accesorios: la clave es tambien la clave de texto en textos.py
ACCESORIOS = {
    "poncho": {"descripcion": "Capa corta roja"},
    "toquilla": {"descripcion": "Sombrero de paja toquilla"},
    "otavalo": {"descripcion": "Sombrero de fieltro oscuro"},
    "chullo": {"descripcion": "Gorro andino"},
}
ORDEN_ACCESORIOS = ["poncho", "toquilla", "otavalo", "chullo"]

# ropa compartida
ROPA = {"camiseta": "#F6C915", "pantalon": "#1F3E8C", "zapatos": "#C8242B"}
