"""Nivel 4 - Galapagos: roca volcanica. Iguanas y conchas. Comida: ceviche.

Leyenda: # suelo  = plataforma  B ladrillo  ? bloque especial  C coleccionable
         E enemigo  K checkpoint  P inicio  F bandera  W agua  S sello de hielo
"""

NIVEL_GALAPAGOS = {
    "clave": "galapagos",
    "nombre": "nivel_galapagos",
    "tiempo": 240,
    "paleta": {"cielo_arriba": "#F6C98A", "cielo_abajo": "#7FD3D8", "suelo": "#34343E", "lava": "#4A4A56", "agua": "#2BB5C0", "cactus": "#6FA83A"},
    "fondo": ["mar_islas", "cactus_lava", "rocas_cercanas"],
    "enemigo": "iguana",
    "coleccionable": "concha",
    "comida": "ceviche",
    "musica": "galapagos",
    "bloques_especiales": {            # (columna, fila): contenido
        (8, 5): "coleccionable",
        (10, 5): "comida",
        (12, 5): "coleccionable",
        (65, 4): "comida",
        (67, 4): "coleccionable",
        (126, 5): "coleccionable",
        (128, 5): "comida",
    },
    "mapa": [
        "                                                                                                                                                      ",
        "                                                                                                                                                      ",
        "                                                                CCC                                                                                   ",
        "        CCCC                               CC                                 CC                                         CCC                          ",
        "                       CC                 C  C              CCC B?B?         C  C                 CCC                                                 ",
        "        ?B?B?         C  C      CCCC     C    C                         CCCCC    C                            CCCC      C   C ?B?                     ",
        "             CCC     C    C             C      C           C   CCCC        C      C              C   C                 C     C            CCCCC       ",
        "                    C     CEC  ######         ECCCK       C    EC      ######     CECC          C     CCEKE  ######                         E   F     ",
        "   P    E   ####         ################    ######## CCCC    ###############    ########## CCCC     ####################     CCECC   E ##############",
        "######################WWW################WWWW##############WWW###############WWWW################WWWW####################WWW##########################",
        "######################WWW################WWWW##############WWW###############WWWW################WWWW####################WWW##########################",
    ],
}
