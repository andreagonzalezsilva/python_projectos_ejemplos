"""Las canciones del juego como datos (diccionarios), igual que los niveles.

Cada cancion se arma con FRASES de 4 compases. Una frase es (melodia, acordes):
  melodia: notas "NOTA:unidades" separadas por espacios; | separa compases; R = silencio.
           La unidad es una semicorchea. Sin ":n" una nota dura 2 (una corchea). Cada compas suma 16.
  acordes: un acorde por compas (C, Am, G7, Bb, Em...). De ahi salen el bajo y el acompanamiento.
"forma" dice en que orden suenan las frases. El timbre y el ritmo de cada seccion se eligen con
"lead", "bajo", "acomp" (instrumento, patron) y "bateria" (primera mitad, segunda mitad).
Los instrumentos y los patrones estan en sintesis.py.
"""

# bateria: 16 posiciones por compas. x = golpe, o = golpe suave, . = nada
_FIJO_TITULO = ({"bombo": "x.......x.......", "caja": "....x.......x...", "charles": "..o...o...o...o."},
                {"bombo": "x.......x.x.....", "caja": "....x.......x...", "charles": "x.o.x.o.x.o.x.o."})

MUSICAS = {
    # ---- Titulo: aventura alegre, al estilo de un clasico de plataformas
    "titulo": {
        "tempo": 140, "transponer": -12, "swing": 0.0, "eco": (3, 0.18),
        "lead": "mario", "bajo": ("bajo_mario", "mario"), "acomp": ("piano", "oompah"),
        "bateria": _FIJO_TITULO, "relleno": {"caja": "............xxxx"},
        "frases": {
            "A": ("G4:2 C5:2 E5:2 G5:3 E5:1 G5:2 C6:4 | B5:2 G5:2 D5:2 G5:2 B5:3 A5:1 G5:4 | "
                  "A4:2 C5:2 E5:2 A5:3 G5:1 E5:2 C5:2 E5:2 | F5:2 A5:2 G5:2 F5:2 E5:2 D5:2 C5:2 R:2",
                  "C G Am F"),
            "B": ("C6:3 B5:1 G5:2 E5:2 G5:3 E5:1 C5:2 R:2 | E5:2 G5:2 B5:2 E6:3 D6:1 B5:2 G5:2 B5:2 | "
                  "A5:2 F5:2 C5:2 F5:2 A5:3 G5:1 F5:4 | D5:2 G5:2 B5:2 D6:2 G5:4 B5:2 A5:2",
                  "C Em F G"),
            "C": ("F5:2 A5:2 C6:2 A5:2 F5:2 A5:2 C6:2 A5:2 | E5:2 G5:2 C6:2 G5:2 E5:2 G5:2 C6:4 | "
                  "D5:2 G5:2 B5:2 G5:2 D5:2 B4:2 D5:2 G5:2 | C5:4 E5:2 G5:2 C6:6 R:2",
                  "F C G C"),
            "D": ("A5:3 E5:1 C5:2 E5:2 A5:3 C6:1 B5:2 A5:2 | D6:3 A5:1 F5:2 A5:2 D6:3 F6:1 E6:2 D6:2 | "
                  "G5:2 B5:2 D6:2 G6:3 F6:1 D6:2 B5:2 D6:2 | C6:6 G5:2 E5:2 C5:4 R:2",
                  "Am Dm G C"),
        },
        "forma": "A B C D A C B D",
    },

    # ---- Costa: salsa. Trompeta, piano montuno, clave, cencerro y congas
    "costa": {
        "tempo": 168, "transponer": -12, "swing": 0.0, "eco": (3, 0.12),
        "lead": "trompeta", "bajo": ("bajo_salsa", "salsa"), "acomp": ("piano", "guajeo"),
        "bateria": ({"clave": "x..x..x...x.x...", "cencerro": "o.o.o.o.o.o.o.o.", "conga": "..o.x.x...o.x.x.",
                     "bombo": "o.......o.......", "maraca": "x.x.x.x.x.x.x.x."},
                    {"clave": "x..x..x...x.x...", "cencerro": "x.o.x.o.x.o.x.o.", "conga": "..o.x.x...o.x.x.",
                     "conga_grave": "....o.......o.o.", "bombo": "o.......o.......", "maraca": "x.x.x.x.x.x.x.x."}),
        "relleno": {"conga": "............xxxx"},
        "frases": {
            "A": ("R:2 A5:2 C6:3 B5:1 A5:2 E5:2 A5:2 R:2 | D5:2 F5:2 A5:3 G5:1 F5:2 D5:2 F5:4 | "
                  "E5:2 G#5:2 B5:3 A5:1 G#5:2 E5:2 D5:2 B4:2 | A4:3 C5:1 E5:2 A5:6 R:4",
                  "Am Dm E7 Am"),
            "B": ("G5:3 G5:1 E5:2 G5:2 C6:3 B5:1 G5:2 E5:2 | A5:3 A5:1 F5:2 A5:2 C6:3 A5:1 F5:2 C5:2 | "
                  "B5:3 B5:1 G5:2 B5:2 D6:3 B5:1 F5:2 G5:2 | E6:4 C6:2 G5:2 C6:6 R:2",
                  "C F G7 C"),
            "C": ("A5:2 A5:2 R:2 A5:2 C6:4 B5:2 A5:2 | F5:2 F5:2 R:2 F5:2 A5:4 G5:2 F5:2 | "
                  "D5:2 D5:2 R:2 D5:2 F5:4 E5:2 D5:2 | E5:2 E5:2 G#5:2 B5:2 E6:6 R:2",
                  "Am F Dm E7"),
            "D": ("C6:2 B5:2 A5:2 E5:2 C6:2 B5:2 A5:2 E5:2 | D6:2 C6:2 A5:2 F5:2 D6:2 C6:2 A5:2 F5:2 | "
                  "E6:3 D6:1 B5:2 G#5:2 E6:3 D6:1 B5:2 G#5:2 | A5:2 C6:2 E6:2 A6:6 R:4",
                  "Am Dm E7 Am"),
        },
        "forma": "A B C D A C B D",
    },

    # ---- Sierra: flauta andina (quena), charango y bombo, ritmo de sanjuanito
    "sierra": {
        "tempo": 132, "transponer": 0, "swing": 0.0, "eco": (3, 0.25),
        "lead": "flauta", "bajo": ("bajo_redondo", "andino"), "acomp": ("charango", "charango"),
        "bateria": ({"bombo_andino": "x.......x.......", "maraca": "x.x.xxx.x.x.xxx."},
                    {"bombo_andino": "x.....x.x.....x.", "maraca": "x.x.xxx.x.x.xxx.", "charles": "..o...o...o...o."}),
        "relleno": {"bombo_andino": "............x.xx"},
        "frases": {
            "A": ("E5:3 E5:1 D5:2 C5:2 A4:4 C5:2 D5:2 | E5:3 E5:1 D5:2 B4:2 G4:4 B4:2 D5:2 | "
                  "C5:3 C5:1 D5:2 E5:2 F5:4 E5:2 D5:2 | E5:2 D5:2 B4:2 G#4:2 B4:4 R:4",
                  "Am G F E7"),
            "B": ("G5:3 E5:1 G5:2 A5:2 G5:2 E5:2 D5:2 E5:2 | D5:3 B4:1 D5:2 E5:2 D5:2 B4:2 A4:2 B4:2 | "
                  "C5:3 A4:1 C5:2 D5:2 E5:4 D5:2 C5:2 | B4:2 C5:2 B4:2 G#4:2 E4:4 R:4",
                  "C G Am E7"),
            "C": ("A5:4 G5:2 E5:2 G5:3 A5:1 C6:4 | A5:3 F5:1 D5:2 F5:2 A5:4 G5:2 F5:2 | "
                  "G5:4 D5:2 B4:2 D5:3 G5:1 B5:4 | B5:2 G#5:2 E5:2 B4:2 E5:8",
                  "Am Dm G E7"),
            "D": ("C5:2 F5:2 A5:3 F5:1 C6:4 A5:2 F5:2 | B5:2 G5:2 D5:3 G5:1 B5:4 G5:2 D5:2 | "
                  "A5:2 E5:2 C5:2 E5:2 A5:2 E5:2 C5:2 E5:2 | A4:2 C5:2 E5:2 A5:4 R:6",
                  "F G Am Am"),
        },
        "forma": "A B C D A B C D",
    },

    # ---- Amazonia: aventura en la selva. Metales heroicos, marimba y tambores
    "amazonia": {
        "tempo": 144, "transponer": -12, "swing": 0.0, "eco": (3, 0.15),
        "lead": "trompeta", "bajo": ("bajo_redondo", "galope"), "acomp": ("marimba", "ostinato"),
        "bateria": ({"tom": "x..x..x.x..x..x.", "bombo": "x.......x.......", "maraca": "x.x.x.x.x.x.x.x."},
                    {"tom": "x..x..x.x..x..x.", "bombo": "x.......x.x.....", "caja": "....x.......x...",
                     "maraca": "x.x.x.x.x.x.x.x."}),
        "relleno": {"tom": "..........xxxxxx"},
        "frases": {
            "A": ("D5:3 D5:1 F5:2 A5:2 D6:3 C6:1 A5:2 F5:2 | D5:3 D5:1 F5:2 A#5:2 D6:3 C6:1 A#5:2 F5:2 | "
                  "E5:3 E5:1 G5:2 C6:2 E6:3 D6:1 C6:2 G5:2 | C#6:2 E6:2 A5:2 C#6:2 E6:4 R:4",
                  "Dm Bb C A7"),
            "B": ("G5:2 A#5:2 D6:3 C6:1 A#5:2 G5:2 A#5:4 | A5:2 D6:2 F6:3 E6:1 D6:2 A5:2 D6:4 | "
                  "A5:3 C#6:1 E6:2 C#6:2 A5:3 E5:1 C#5:4 | D6:6 A5:2 F5:2 D5:4 R:2",
                  "Gm Dm A Dm"),
            "C": ("D6:1 D6:1 F6:2 D6:2 A#5:2 D6:1 D6:1 F6:2 D6:2 A#5:2 | C6:1 C6:1 F6:2 C6:2 A5:2 C6:1 C6:1 F6:2 C6:2 A5:2 | "
                  "D6:1 D6:1 G6:2 D6:2 A#5:2 D6:1 D6:1 G6:2 D6:2 A#5:2 | E6:2 C#6:2 A5:2 E5:2 A5:4 R:4",
                  "Bb F Gm A"),
            "D": ("F6:3 E6:1 D6:2 A5:2 F5:3 A5:1 D6:4 | E6:3 D6:1 C6:2 G5:2 E5:3 G5:1 C6:4 | "
                  "D6:3 C6:1 A#5:2 F5:2 D5:3 F5:1 A#5:4 | C#6:2 E6:2 G6:2 E6:2 A5:4 R:4",
                  "Dm C Bb A"),
        },
        "forma": "A B C D A B D C",
    },

    # ---- Galapagos: vacaciones en la isla. Tambor de acero, ukelele a contratiempo, ritmo de reggae
    "galapagos": {
        "tempo": 118, "transponer": -12, "swing": 0.2, "eco": (3, 0.22),
        "lead": "acero", "bajo": ("bajo_redondo", "reggae"), "acomp": ("ukelele", "skank"),
        "bateria": ({"bombo": "........x.......", "caja": "........x.......", "charles": "o.o.o.o.o.o.o.o.",
                     "maraca": ".o.o.o.o.o.o.o.o"},
                    {"bombo": "........x.......", "caja": "........x.......", "charles": "x.o.x.o.x.o.x.o.",
                     "maraca": ".o.o.o.o.o.o.o.o", "cencerro": "....o.......o..."}),
        "relleno": {"conga": "............xxxx"},
        "frases": {
            "A": ("B5:3 D6:1 B5:2 G5:2 A5:3 B5:1 G5:4 | C6:3 E6:1 C6:2 G5:2 A5:3 C6:1 G5:4 | "
                  "D6:3 C6:1 B5:2 A5:2 F#5:3 A5:1 D6:4 | B5:2 A5:2 G5:2 D5:2 G5:4 R:4",
                  "G C D G"),
            "B": ("E6:3 D6:1 B5:2 G5:2 B5:3 D6:1 E6:4 | C6:3 B5:1 G5:2 E5:2 G5:3 C6:1 E6:4 | "
                  "D6:3 B5:1 G5:2 B5:2 D6:3 G6:1 D6:4 | A5:2 F#5:2 A5:2 D6:2 C6:4 R:4",
                  "Em C G D"),
            "C": ("E5:2 G5:2 C6:4 B5:2 A5:2 G5:4 | D5:2 G5:2 B5:4 A5:2 G5:2 B5:4 | "
                  "C6:2 B5:2 A5:4 G5:2 E5:2 A5:4 | F#5:2 A5:2 D6:4 C6:2 A5:2 F#5:4",
                  "C G Am D"),
            "D": ("G5:3 B5:1 D6:4 B5:3 G5:1 D5:4 | E5:3 G5:1 B5:4 G5:3 E5:1 B4:4 | "
                  "C6:3 E6:1 D6:2 C6:2 B5:2 A5:2 G5:4 | D6:2 C6:2 B5:2 A5:2 G5:6 R:2",
                  "G Em C D"),
        },
        "forma": "A B C D A C B D",
    },

    # ---- Cotopaxi (jefe): tenso y aspero. Notas cortas, bajo en semicorcheas y redoble seco
    "cotopaxi": {
        "tempo": 160, "transponer": -12, "swing": 0.0, "eco": None,
        "lead": "laton_aspero", "bajo": ("bajo_aspero", "pulso16"), "acomp": ("acorde_aspero", "stab"),
        "bateria": ({"bombo": "x...x...x...x...", "redoble": "....x.......x...", "charles": "x.x.x.x.x.x.x.x."},
                    {"bombo": "x..xx...x..xx...", "redoble": "....x.......x...", "charles": "x.x.x.x.x.x.x.x.",
                     "charles_abierto": "..o...o...o...o."}),
        "relleno": {"redoble": "..........xxxxxx"},
        "frases": {
            "A": ("E5:2 E5:2 R:2 E5:2 G5:2 E5:2 B5:4 | C6:2 C6:2 R:2 B5:2 C6:2 G5:2 E5:4 | "
                  "D6:2 D6:2 R:2 C6:2 D6:2 A5:2 F#5:4 | B5:2 D#6:2 F#6:4 D#6:2 B5:2 F#5:2 R:2",
                  "Em C D B7"),
            "B": ("E5:1 F5:1 F#5:1 G5:1 G#5:1 A5:1 A#5:1 B5:1 B5:4 R:4 | E6:2 B5:2 G5:2 E5:2 B4:2 E5:2 G5:2 B5:2 | "
                  "C6:3 G5:1 E5:2 G5:2 C6:3 G5:1 E5:2 G5:2 | B5:3 A5:1 G#5:2 F#5:2 D#5:2 F#5:2 B4:4",
                  "Em Em C B7"),
            "C": ("A5:2 A5:2 A5:2 C6:2 A5:2 E5:2 A5:4 | G5:2 G5:2 G5:2 B5:2 G5:2 E5:2 G5:4 | "
                  "F#5:2 F#5:2 F#5:2 A5:2 F#5:2 D#5:2 F#5:4 | E5:2 G5:2 B5:2 E6:6 R:4",
                  "Am Em B7 Em"),
            "D": ("G5:2 E6:2 D6:2 C6:2 G5:2 E6:2 D6:2 C6:2 | A5:2 F#6:2 E6:2 D6:2 A5:2 F#6:2 E6:2 D6:2 | "
                  "B5:2 G6:2 F#6:2 E6:2 B5:2 G6:2 F#6:2 E6:2 | D#6:2 F#6:2 B6:4 R:8",
                  "C D Em B7"),
        },
        "forma": "A B C D A C B D A B",
    },

    # ---- Victoria: fanfarria
    "victoria": {
        "tempo": 150, "transponer": -12, "swing": 0.0, "eco": (3, 0.2),
        "lead": "trompeta", "bajo": ("bajo_mario", "mario"), "acomp": ("piano", "oompah"),
        "bateria": _FIJO_TITULO, "relleno": {"caja": "............xxxx"},
        "frases": {
            "A": ("G4:2 C5:2 E5:2 G5:4 E5:2 G5:4 | A5:2 F5:2 C5:2 A5:4 F5:2 A5:4 | "
                  "B5:2 G5:2 D5:2 B5:4 G5:2 D6:4 | C6:8 G5:2 E5:2 C5:4",
                  "C F G C"),
            "B": ("E5:2 G5:2 C6:2 E6:2 D6:2 C6:2 G5:2 E5:2 | D5:2 G5:2 B5:2 D6:2 C6:2 B5:2 A5:2 G5:2 | "
                  "F5:2 A5:2 C6:2 F6:2 E6:2 D6:2 C6:2 A5:2 | C6:4 G5:2 C6:2 E6:8",
                  "C G F C"),
        },
        "forma": "A B A B",
    },
}
