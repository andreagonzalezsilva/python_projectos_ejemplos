"""Nivel 2 - Sierra: Andes y volcanes. Condores y rosas. Comida: empanada de viento.

Leyenda: # suelo  = plataforma  B ladrillo  ? bloque especial  C coleccionable
         E enemigo  K checkpoint  P inicio  F bandera  W agua  S sello de hielo
"""

NIVEL_SIERRA = {
    "clave": "sierra",
    "nombre": "nivel_sierra",
    "tiempo": 240,
    "paleta": {"cielo_arriba": "#3F8FE0", "cielo_abajo": "#9CCBF2", "suelo": "#6B9B3A", "tierra": "#7A5230"},
    "fondo": ["volcanes", "paramo", "pasto_cercano"],
    "enemigo": "condor",
    "coleccionable": "rosa",
    "comida": "empanada_viento",
    "musica": "sierra",
    "bloques_especiales": {            # (columna, fila): contenido
        (9, 5): "coleccionable",
        (11, 5): "comida",
        (13, 5): "coleccionable",
        (87, 4): "comida",
        (140, 5): "coleccionable",
        (142, 5): "comida",
    },
    "mapa": [
        "                                                                                                                      CCC                             ",
        "                                                                        CCC                                          C   C                            ",
        "                              CC                                       C   C                                        C     C                           ",
        "                             C  C                 CC                  C     C                 CC            CCCCC         CCCEC                       ",
        "                            C    C               C  C             E             E     B?B    C  C                                                     ",
        "         ?B?B?         CCC C      C E                         CCCC          CCCCC                     E    ##########    ##########    E    ?B?B      ",
        "                 E                CCCC          C    C E     ##########    ##########   E   C    CCCKCC    ##########    ########## CCCC              ",
        "              CCCCC  ########    ##########           CCCC   ##########    ########## CCCC       ####################    ##################           ",
        "   P  CCC     ###############    ########## CKCC     ##################    ##################    ####################    ################## CCCCCF    ",
        "#############################    ################    ##################    ##################    ####################    #############################",
        "#############################    ################    ##################    ##################    ####################    #############################",
    ],
}
