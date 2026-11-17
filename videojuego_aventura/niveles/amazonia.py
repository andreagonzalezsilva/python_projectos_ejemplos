"""Nivel 3 - Amazonia: selva y rio. Monos y orquideas. Comida: maito.

Leyenda: # suelo  = plataforma  B ladrillo  ? bloque especial  C coleccionable
         E enemigo  K checkpoint  P inicio  F bandera  W agua  S sello de hielo
"""

NIVEL_AMAZONIA = {
    "clave": "amazonia",
    "nombre": "nivel_amazonia",
    "tiempo": 240,
    "paleta": {"cielo_arriba": "#A8D8A0", "cielo_abajo": "#5FAE6B", "suelo": "#5A3D24", "follaje": "#1F6B2E"},
    "fondo": ["niebla_selva", "arboles", "lianas_helechos"],
    "enemigo": "mono",
    "coleccionable": "orquidea",
    "comida": "maito",
    "musica": "amazonia",
    "bloques_especiales": {            # (columna, fila): contenido
        (9, 5): "coleccionable",
        (11, 5): "comida",
        (13, 5): "coleccionable",
        (77, 5): "comida",
        (105, 5): "coleccionable",
        (107, 5): "comida",
    },
    "mapa": [
        "                                                                                                                                                      ",
        "                                                                                                                                                      ",
        "                                                                                                                                                      ",
        "          CCCC                                                              CCC                                   CC            CC                    ",
        "                    CCC                         CCCCC                                 CC                         C  C          C  C                   ",
        "         ?B?B?                               CCC     CCC                    ?B?      C  C               B?B?                                          ",
        "                   C   C        CCCC        C        CC C                                           CCC         C    C     CC C    C                  ",
        "                  C     C     ##               CC   ====               ##           C    C          ##               CC   ====                        ",
        "   P  E       CCCC      CCEC  ##        KCC   ====        CCEC    ECC  ##                 CCEC K  E ##              ====          E   ECCCE  E  F     ",
        "####################WWW#####################WWWWWWWWWWWWW#############################WWW#########################WWWWWWWWWWWWW#######################",
        "####################WWW#####################WWWWWWWWWWWWW#############################WWW#########################WWWWWWWWWWWWW#######################",
    ],
}
