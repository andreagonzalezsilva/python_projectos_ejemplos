"""Nivel 5 - Cotopaxi (jefe): toca los 3 sellos de hielo para calmar al volcan.

Leyenda: # suelo  = plataforma  B ladrillo  ? bloque especial  C coleccionable
         E enemigo  K checkpoint  P inicio  F bandera  W agua  S sello de hielo
"""

NIVEL_COTOPAXI = {
    "clave": "cotopaxi",
    "nombre": "nivel_cotopaxi",
    "tiempo": 180,
    "jefe": True,
    "paleta": {"cielo_arriba": "#3B1A2A", "cielo_abajo": "#C4452B", "suelo": "#2E2A33", "nieve": "#E8EEF5", "lava": "#FF8A1F", "hielo": "#9FE3FF"},
    "fondo": ["cielo_ceniza", "montanas", "humo_lava"],
    "enemigo": "ceniza",
    "coleccionable": "sello_hielo",
    "comida": "colada_morada",
    "musica": "cotopaxi",
    "bloques_especiales": {            # (columna, fila): contenido
        (24, 5): "comida",
    },
    "mapa": [
        "                                        ",
        "                                        ",
        "#                                      #",
        "#                                      #",
        "#                CCS                   #",
        "#                =====  ?              #",
        "#      S    CCK               S        #",
        "#     ====  ===             ====       #",
        "#  P      CC          E   K      ECC F #",
        "########################################",
        "########################################",
    ],
}
