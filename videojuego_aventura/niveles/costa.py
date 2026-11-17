"""Nivel 1 - Costa: playa, manglar y mar. Cangrejos, bananos y cacao. Comida: bolon.

Leyenda: # suelo  = plataforma  B ladrillo  ? bloque especial  C coleccionable
         E enemigo  K checkpoint  P inicio  F bandera  W agua  S sello de hielo
"""

NIVEL_COSTA = {
    "clave": "costa",
    "nombre": "nivel_costa",
    "tiempo": 240,
    "paleta": {"cielo_arriba": "#7ED6F0", "cielo_abajo": "#CFF1FA", "suelo": "#E8D08A", "agua": "#1E88C8"},
    "fondo": ["mar_lejano", "palmeras", "olas_cercanas"],
    "enemigo": "cangrejo",
    "coleccionable": ["banano", "cacao"],
    "comida": "bolon",
    "musica": "costa",
    "bloques_especiales": {            # (columna, fila): contenido
        (9, 5): "coleccionable",
        (11, 5): "comida",
        (13, 5): "coleccionable",
        (73, 5): "comida",
        (75, 5): "coleccionable",
        (112, 5): "coleccionable",
        (114, 5): "comida",
    },
    "mapa": [
        "                                                                                                                                                      ",
        "                                                                                                                                                      ",
        "                                                                                                                                                      ",
        "          CCCC                                                           CCC                                   CCCCC       CC                         ",
        "                            CCC                                                         CCC                CC             C  C                        ",
        "         ?B?B?                                     C             CC     B?B?B                             C  C  ?B?      C    C                       ",
        "                           C   C                  C C           C  C                   C   C             C    C       CCCC              CCCC          ",
        "                          C     C   CCCC         C   C         C    C                 C     C   CCC     C      C     #####                            ",
        "   P        E CCCCC             CEC ####  CCC  K      CC     CC      E    ECCC              CEC ### K                #####    CCECKC E   E  E E F     ",
        "############################WWW###################WWW====WWW====WWW#####################WWW################WWWW###########WWW#########################",
        "############################WWW###################WWWWWWWWWWWWWWWWW#####################WWW################WWWW###########WWW#########################",
    ],
}
