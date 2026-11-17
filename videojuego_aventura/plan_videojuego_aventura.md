# Plan: Aventura Ecuador — videojuego estilo Mario Bros con temática ecuatoriana

> **Qué es este documento.** Es el plan completo para que una IA construya, en otro chat, un demo jugable de plataformas 2D hecho con Python y Pygame.
> Salió de una entrevista de decisiones con el docente. Todo lo que dice aquí está **decidido**. No hay que volver a preguntarlo.
> **Para qué sirve en clase:** se muestra este `.md` junto con el juego terminado, para explicar cómo la IA lo construyó fase por fase.

---

## 0. Prompt maestro (copiar y pegar en el chat de construcción)

```text
Eres un programador experto en Python y Pygame. Tu trabajo es construir, dentro de la carpeta
videojuego_aventura/, el videojuego descrito en el archivo plan_videojuego_aventura.md.

Reglas:
1. Lee el plan COMPLETO antes de escribir código. Todas las decisiones ya están tomadas, no hagas preguntas
   de diseño. Si algo no está especificado, elige lo más simple y anótalo en la sección "Decisiones tomadas
   durante la construcción" al final del plan.
2. Trabaja fase por fase (Fase 1 a Fase 8). No pases a la siguiente fase hasta ejecutar la verificación de
   la fase actual y comprobar que pasa. Si falla, corrige y vuelve a verificar.
3. Todo el código, los nombres de variables, funciones, clases y los comentarios van en ESPAÑOL, sin tildes
   ni eñes en nombres de archivos e identificadores. Los textos visibles al jugador sí llevan tildes y
   viven solo en src/textos.py (español e inglés).
4. La única dependencia externa es pygame. Prohibido descargar imágenes, sonidos o fuentes. Todo el arte y
   el sonido se genera por código.
5. Ejecuta el juego de verdad: usa el modo sin ventana (SDL_VIDEODRIVER=dummy) y guarda capturas de
   pantalla en capturas/ para revisarlas con tus propios ojos y corregir lo que se vea mal.
6. Al terminar, completa el checklist de la sección 12 y resume qué quedó hecho.
```

---

## 1. Resumen del juego

- **Título:** *Aventura Ecuador* (nombre configurable en `textos.py`).
- **Género:** plataformas 2D de desplazamiento lateral, como Super Mario Bros.
- **Idea:** un niño o una niña recorre Ecuador en 4 niveles (Costa, Sierra, Amazonía y Galápagos). Después sube a la cima del Cotopaxi para calmar al volcán.
- **Tipo de entrega:** demo listo para jugar. No es un curso ni una serie de retos.
- **Idiomas del juego:** español (por defecto) e inglés, con un desplegable **ES / EN** arriba a la derecha del menú de inicio.
- **Lo que se muestra en clase:** este plan y el juego funcionando.

### Fuera de alcance (no construir)

Multijugador, tuberías, otros power-ups además de la comida, control con mando, empaquetado `.exe`, imágenes PNG o sonidos descargados, tienda de personajes, guardado de partida a mitad de nivel.

---

## 2. Entorno

| Dato | Valor |
|---|---|
| Sistema | Windows, PowerShell |
| Python | 3.12.10, ya instalado con `winget` (modo usuario) |
| Ruta del intérprete | `%LOCALAPPDATA%\Programs\Python\Python312\python.exe` |
| Nota | La terminal ya abierta puede no tener Python en el PATH. Usa la ruta completa o abre una terminal nueva |
| Dependencia | `pygame>=2.5` (única) |
| Entorno virtual | `.venv` dentro de `videojuego_aventura/` |

Comandos base (desde `videojuego_aventura/`):

```powershell
$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
& $py -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt

# Jugar
.\.venv\Scripts\python main.py

# Prueba sin ventana
$env:SDL_VIDEODRIVER = "dummy"; $env:SDL_AUDIODRIVER = "dummy"
.\.venv\Scripts\python pruebas\prueba_humo.py
```

---

## 3. Decisiones tomadas (resumen de la entrevista)

| Tema | Decisión |
|---|---|
| Nivel del curso | Condicionales, bucles, funciones y diccionarios. Se usan clases solo donde son naturales (`Jugador`, `Enemigo`...) |
| Librería | Pygame |
| Estilo visual | Pixel art generado por código, lienzo interno 320×180 escalado ×4 a 1280×720 |
| Rendimiento | 60 FPS, con sprites y fondos en caché (se generan una sola vez al iniciar) |
| Controles | Solo teclado |
| Niveles | 4 regiones + jefe final Cotopaxi, cada región con paisaje, enemigo, coleccionable y comida propios |
| Personajes | 8 personajes con nombre popular, mismo cuerpo, 4 accesorios a elegir |
| Comida | Reemplaza al champiñón. Hace crecer al personaje. No se muestra su nombre, solo su ícono |
| Idiomas | ES / EN con desplegable en el menú |
| Sonido | Sintetizado con la biblioteca estándar. Sin archivos externos |
| Código | Todo en español, incluidos comentarios |
| Ejecución | `python main.py` y `jugar.bat` de doble clic |
| Verificación | Prueba sin ventana y capturas en `capturas/` |

---

## 4. Especificaciones técnicas

### 4.1 Pantalla y bucle

- Lienzo interno: **320×180** px. Ventana: **1280×720** (escala ×4 con `pygame.transform.scale`, enteros, sin suavizado).
- **F11** alterna pantalla completa manteniendo la proporción 16:9 (con barras negras si hace falta).
- Tamaño de baldosa: **16×16** px. Altura de nivel: **11 filas** (176 px, el HUD se dibuja encima).
- Bucle: 60 FPS con `Clock.tick(60)`. Actualizar la lógica con `dt` en segundos, limitado a 1/30 s para evitar saltos.
- Estructura de escenas: `Titulo → Seleccion → Juego → (Pausa) → FinNivel → ... → Victoria` y `GameOver`. Cada escena tiene `eventos()`, `actualizar(dt)` y `dibujar(lienzo)`.
- ~~Los textos se dibujan en el lienzo interno con fuente **sin suavizado** (`antialias=False`).~~ **Cambiado a petición del docente** (el texto se veía muy pixelado): el arte sigue en el lienzo de 320×180, pero el texto se dibuja en una capa transparente a la resolución real de la ventana (1280×720, o la de la pantalla completa) y **con suavizado**. Ver la última fila de la sección 15. Si no muestra tildes o eñes, prueba otra fuente del sistema. Revisa esto en las capturas.

### 4.2 Controles

| Acción | Teclas |
|---|---|
| Mover | Flechas izquierda/derecha o **A / D** |
| Saltar | **Espacio** o **W** o flecha arriba (mantener = salto más alto) |
| Correr | **Shift** (izquierdo o derecho) |
| Pausa | **Esc** |
| Silenciar | **M** |
| Pantalla completa | **F11** |
| Cambiar idioma | **L** (además del desplegable con el mouse, solo en el menú de inicio) |
| Menús | Flechas + **Enter**; el desplegable también se usa con clic |

**Abstracción de entrada:** el jugador no lee el teclado directamente. Lee un objeto `Entrada` con `izquierda`, `derecha`, `salto`, `salto_presionado`, `correr`. Hay dos versiones: `EntradaTeclado` (real) y `EntradaGuion` (pruebas automáticas que reproducen una lista de acciones por tiempo). Esto permite probar sin ventana.

### 4.3 Física del jugador (valores iniciales, ajustables en `ajustes.py`)

| Constante | Valor |
|---|---|
| Gravedad | 900 px/s² |
| Velocidad al caminar | 90 px/s |
| Velocidad al correr | 140 px/s |
| Aceleración / frenado en suelo | 600 / 700 px/s² |
| Control en el aire | 60 % de la aceleración |
| Velocidad inicial del salto | -300 px/s (≈ 3 baldosas de altura) |
| Salto variable | Si se suelta el botón mientras sube, la velocidad vertical se multiplica por 0,5 |
| Velocidad máxima de caída | 400 px/s |
| Tiempo de gracia al borde (coyote) | 0,08 s |
| Salto adelantado (buffer) | 0,10 s |
| Tamaño pequeño | 12×16 px de hitbox (sprite 16×16) |
| Tamaño grande | 12×30 px de hitbox (sprite 16×32) |

- Colisiones por ejes separados: primero mueve en X y resuelve, luego en Y.
- La hitbox es ligeramente más pequeña que el sprite para que el juego se sienta justo.
- Distancia máxima de un hueco en los niveles: **4 baldosas** (alcanzable corriendo).

### 4.4 Reglas de juego

- **Vidas:** 3 al empezar.
- **Muerte:** golpe de enemigo siendo pequeño, caer al vacío, tocar agua `W` o acabarse el tiempo. Se pierde una vida y se reaparece en el último checkpoint (o al inicio).
- **Sin vidas:** pantalla *Game Over* y vuelta al menú.
- **Tiempo por nivel:** 240 s (el jefe: 180 s).
- **Puntos:**
  - Pisar enemigo: **100**.
  - Coleccionable: **10**.
  - Comida cuando ya eres grande: **1000**.
  - Al llegar a la bandera: **segundos restantes × 10**.
- **Vida extra:** cada **100 coleccionables** recogidos (el contador se reinicia).
- **Comida (crecer):** ver sección 6.
- **Invulnerabilidad:** 2 s con parpadeo después de que un golpe te reduzca de grande a pequeño.
- **Checkpoint:** baldosa `K` marcada con una banderita pequeña, se activa al pasar.
- **Meta:** al tocar la bandera de Ecuador, el nivel termina y suma el bono. Sigue la animación de cuenta.
- **Guardado** en `puntaje.json` (se crea solo):

```json
{ "mejor_puntaje": 0, "idioma": "es", "personaje": "lorena", "accesorio": "poncho" }
```

---

## 5. Personajes

Todos usan **el mismo cuerpo, la misma silueta y las mismas animaciones** (quieto, caminar de 4 cuadros, saltar, caer, agacharse opcional). Solo cambian el **tono de piel**, el **cabello** y el **accesorio**. Esto evita estereotipos y mantiene el arte simple.

Ropa base compartida (colores de la bandera): camiseta amarilla `#F6C915`, pantalón azul `#1F3E8C`, zapatos rojos `#C8242B`.

| Nombre | Aspecto | Piel | Cabello |
|---|---|---|---|
| **Lorena** | niña trigueña | `#C68E5E` | castaño oscuro ondulado, largo |
| **Camila** | niña de piel clara | `#F1C9A5` | castaño claro, lacio con cola |
| **Killari** | niña indígena | `#A8693F` | negro, trenza larga |
| **Daniela** | niña afroecuatoriana | `#6B4226` | negro rizado, voluminoso |
| **Andrés** | niño trigueño | `#C68E5E` | negro corto |
| **Mateo** | niño de piel clara | `#F1C9A5` | castaño corto |
| **Yaku** | niño indígena | `#A8693F` | negro con trenza corta |
| **Joel** | niño afroecuatoriano | `#6B4226` | negro rizado corto |

### Accesorios (4, se elige uno)

| Clave | Accesorio | Descripción |
|---|---|---|
| `poncho` | Poncho rojo | Capa corta roja con franjas y flecos, sobre los hombros |
| `toquilla` | Sombrero de paja toquilla | Sombrero beige claro de ala ancha con cinta negra |
| `otavalo` | Sombrero otavaleño | Sombrero de fieltro oscuro (`#2B2B33`) de ala corta con cinta |
| `chullo` | Chullo andino | Gorro multicolor con orejeras y borlas |

Total: **8 × 4 = 32 combinaciones**, generadas combinando capas (cuerpo + cabello + accesorio) y guardadas en caché.

Los nombres de personajes y accesorios están en un diccionario fácil de editar en `ajustes.py`, para poder cambiarlos después.

---

## 6. Comida que hace crecer (en lugar del champiñón)

Cada región tiene su comida. **En el juego solo se ve el ícono, nunca el nombre del plato.**

| Nivel | Clave | Plato | Cómo se dibuja (16×16) |
|---|---|---|---|
| Costa | `bolon` | Bolón de verde | Bola dorada con puntos de queso y un poco de vapor |
| Sierra | `empanada_viento` | Empanada de viento | Empanada inflada, dorada, con azúcar blanca encima |
| Amazonía | `maito` | Maito de pescado | Paquete verde de hoja de bijao atado con cuerda |
| Galápagos | `ceviche` | Ceviche de canchalagua | Tazón con mezcla naranja y rodaja de limón |
| Cotopaxi | `colada_morada` | Colada morada con guagua de pan | Vaso morado con una guagüita de pan. **Da una vida extra** |

**Mecánica (igual que el champiñón de Mario):**

1. Un bloque `?` golpeado **desde abajo** hace un rebote corto y suelta la comida de esa región.
2. La comida sale, se desliza a la derecha a 40 px/s, cae por la gravedad y rebota en las paredes.
3. Al tocarla, el jugador pasa de **pequeño (16×16)** a **grande (16×32)**, con una animación corta de crecimiento y breve pausa del juego.
4. Si ya eres grande, la comida da **1000 puntos**.
5. Si un enemigo te golpea siendo grande, **vuelves a pequeño** con 2 s de invulnerabilidad parpadeando. No mueres.
6. Siendo grande puedes **romper bloques de ladrillo `B`** golpeándolos desde abajo. Siendo pequeño solo los haces rebotar.
7. Cada nivel tiene **2 o 3 bloques `?` con comida**. Los `?` restantes pueden dar 1 coleccionable.
8. Si el jugador está pequeño cuando pasa un checkpoint y luego muere, reaparece pequeño.

---

## 7. Niveles

Cada nivel es un **diccionario de Python** en `niveles/<region>.py`. El motor es el mismo para todos. Solo cambian los datos.

### 7.1 Tabla de niveles

| # | Región | Paisaje y fondo (parallax en 3 capas) | Enemigo | Coleccionable | Comida | Notas |
|---|---|---|---|---|---|---|
| 1 | **Costa** | Playa, manglar, mar y palmeras. Cielo celeste, arena clara | Cangrejo | Banano y cacao (alternados) | Bolón | Huecos con agua `W`, plataformas sobre el mar |
| 2 | **Sierra** | Andes, volcanes nevados lejanos, páramo, casitas. Cielo azul intenso | Cóndor | Rosas | Empanada de viento | Riscos de varios niveles de altura, plataformas altas |
| 3 | **Amazonía** | Selva densa, lianas, río, neblina verde | Mono | Orquídeas | Maito | Plataformas altas entre árboles, saltos más verticales |
| 4 | **Galápagos** | Roca volcánica negra, mar turquesa, cactus, cielo cálido | Iguana | Conchas | Ceviche | Pozas de agua `W`, roca irregular |
| 5 | **Cotopaxi** (jefe) | Cima nevada, cielo rojizo oscuro, resplandor naranja | Ceniza y rocas | Sellos de hielo | Colada morada | Arena de ~40 baldosas, una sola pantalla de ancho scrolleable |

**Largo de nivel:** unas **150 baldosas** (2400 px) para los niveles 1 a 4. Altura: 11 filas. Cada nivel debe tener **al menos 2 checkpoints**, **2 o 3 bloques `?` con comida**, entre 8 y 12 enemigos y entre 60 y 100 coleccionables.

### 7.2 Paletas por región (guía, ajustar con criterio visual)

| Región | Cielo | Suelo / roca | Acento |
|---|---|---|---|
| Costa | `#7ED6F0` → `#CFF1FA` | arena `#E8D08A` | mar `#1E88C8`, palmeras `#2E8B3A` |
| Sierra | `#3F8FE0` → `#9CCBF2` | pasto `#6B9B3A`, tierra `#7A5230` | nieve `#FFFFFF`, volcán `#6C7A96` |
| Amazonía | `#A8D8A0` → `#5FAE6B` | tierra `#5A3D24` | follaje `#1F6B2E`, flores `#C060D0` |
| Galápagos | `#F6C98A` → `#7FD3D8` | lava `#34343E`, `#4A4A56` | mar `#2BB5C0`, cactus `#6FA83A` |
| Cotopaxi | `#3B1A2A` → `#C4452B` | roca `#2E2A33`, nieve `#E8EEF5` | lava `#FF8A1F`, hielo `#9FE3FF` |

### 7.3 Leyenda del mapa de texto

| Símbolo | Significado |
|---|---|
| ` ` (espacio) | Vacío |
| `#` | Suelo sólido (el terreno de la región) |
| `=` | Plataforma sólida (flotante) |
| `B` | Ladrillo (se rompe estando grande) |
| `?` | Bloque con comida o coleccionable (se define en `bloques_especiales`) |
| `C` | Coleccionable |
| `E` | Enemigo de la región |
| `K` | Checkpoint |
| `P` | Punto de inicio del jugador |
| `F` | Bandera de Ecuador (meta). Se dibuja con mástil y bandera tricolor (amarillo, azul, rojo) |
| `W` | Agua o vacío mortal |
| `S` | Sello de hielo (solo nivel del jefe) |

Todas las filas del mapa deben tener **exactamente el mismo largo**. El cargador debe validarlo y lanzar un error claro con el número de fila.

### 7.4 Ejemplo de diccionario de nivel (formato obligatorio)

```python
# niveles/costa.py
NIVEL_COSTA = {
    "clave": "costa",
    "nombre": "nivel_costa",          # clave en textos.py, no el texto final
    "tiempo": 240,
    "paleta": {
        "cielo_arriba": "#7ED6F0",
        "cielo_abajo": "#CFF1FA",
        "suelo": "#E8D08A",
        "agua": "#1E88C8",
    },
    "fondo": ["mar_lejano", "palmeras", "olas_cercanas"],   # capas de parallax
    "enemigo": "cangrejo",
    "coleccionable": "banano",
    "comida": "bolon",
    "musica": "costa",
    "bloques_especiales": {            # (columna, fila): contenido
        (11, 5): "comida",
        (9, 5): "coleccionable",
    },
    "mapa": [
        "                                        ",
        "                                        ",
        "                                        ",
        "              C C C                     ",
        "                                        ",
        "         ?B?B?              C C         ",
        "                 ===                    ",
        "                                        ",
        "   P                  E       K         ",
        "##################WWWW##################",
        "##################WWWW##################",
    ],
}
```

`niveles/__init__.py` expone `LISTA_NIVELES = [NIVEL_COSTA, NIVEL_SIERRA, NIVEL_AMAZONIA, NIVEL_GALAPAGOS, NIVEL_COTOPAXI]`.

---

## 8. Enemigos

Todos se vencen **pisándolos** (caer sobre ellos desde arriba, con rebote del jugador). Tocarlos de lado o desde abajo daña al jugador.

| Enemigo | Región | Comportamiento | Velocidad |
|---|---|---|---|
| **Cangrejo** | Costa | Camina de lado. Da la vuelta en paredes y en bordes del suelo | 30 px/s |
| **Cóndor** | Sierra | Vuela en onda senoidal (amplitud ≈ 20 px) hacia la izquierda y vuelve. Se activa al entrar en pantalla | 50 px/s |
| **Mono** | Amazonía | Camina y **salta** cada ~1,2 s hacia el jugador si está a menos de 8 baldosas | 40 px/s, salto -220 |
| **Iguana** | Galápagos | Lenta. Resiste: el **primer pisotón la aplasta y la deja aturdida** 3 s (no daña), el **segundo la elimina** | 20 px/s |

Cada enemigo tiene 2 cuadros de animación mínimos. Al morir hacen una animación corta (aplastarse o caer) y desaparecen.

---

## 9. Jefe final: Cotopaxi (nivel 5)

Arena de unas 40 baldosas con 3 plataformas altas. En cada una hay un **sello de hielo** `S`. El volcán se ve enorme al fondo con **barra de vida** (3 segmentos).

**Ciclo de erupción:**

1. **Calma** (4 s). El jugador se mueve libremente.
2. **Aviso** (1,5 s). El volcán brilla, la pantalla tiembla ligeramente y aparecen sombras en el suelo.
3. **Erupción** (3 s). Caen bolas de ceniza y rocas desde arriba en las posiciones avisadas. Tocarlas daña como un enemigo.
4. Se repite.

**Cómo se vence:**

- El jugador debe tocar los **3 sellos de hielo** (un sello se activa al tocarlo).
- Cada sello activado quita un segmento de vida al volcán y acorta la siguiente erupción.
- Con los 3 sellos, el volcán se calma, se acaba la ceniza y **aparece la bandera de Ecuador** al final de la arena.
- Hay un bloque `?` con la **colada morada** (vida extra) en la arena.
- Llegar a la bandera muestra la **pantalla de victoria** con el puntaje total y el mejor puntaje.

---

## 10. Interfaz y flujo de pantallas

1. **Título / menú de inicio**
   - Logo del juego, fondo con parallax animado y botones **Jugar** y **Salir**.
   - **Arriba a la derecha: desplegable de idioma `ES / EN`.** Cerrado muestra el idioma actual. Abierto muestra `ES – Español` y `EN – English`. Se maneja con clic y también con la tecla **L**. Al cambiar, todos los textos se actualizan al instante y el idioma se guarda en `puntaje.json`.
   - Muestra el mejor puntaje guardado.
2. **Selección de personaje**
   - Cuadrícula de **8 personajes** con su nombre. Debajo, selector de **4 accesorios**.
   - Vista previa animada (caminando) del personaje con el accesorio elegido, dibujada más grande.
   - Navegación con flechas, **Enter** confirma. Se guarda la última elección.
3. **Juego**
   - Cámara que sigue al jugador con suavizado y no muestra fuera del mapa.
   - **HUD** arriba: vidas (ícono de cabeza + número), puntaje, coleccionables (ícono de la región), tiempo y nombre del nivel.
   - Al empezar cada nivel aparece un cartel breve con el nombre de la región.
4. **Pausa** (Esc): opciones Continuar y Salir al menú.
5. **Fin de nivel:** cuenta animada del bono por tiempo y paso al siguiente nivel.
6. **Game Over** y **Victoria**, con puntaje y mejor puntaje.

### 10.1 `textos.py` (español e inglés)

Todos los textos visibles viven aquí, en un diccionario por idioma. Una función `t("clave")` devuelve el texto en el idioma activo. Si una clave falta, devuelve la clave (para detectar errores).

```python
# src/textos.py
IDIOMA_ACTUAL = "es"

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
    },
}


def t(clave):
    return TEXTOS[IDIOMA_ACTUAL].get(clave, clave)
```

(No hay textos con nombres de platos, porque la comida solo se muestra como ícono.)

---

## 11. Gráficos y sonido generados por código

### 11.1 Arte (pixel art procedural)

- Los sprites se definen como **mapas de píxeles de texto** (cada carácter es un color de una paleta tipo diccionario) y se convierten a `pygame.Surface` con `convert_alpha()`. Todo se genera **una sola vez** al iniciar y se guarda en caché.
- Se usan **capas**: cuerpo → ropa → cabello (por personaje) → accesorio. Se combinan al crear los 32 personajes y sus animaciones.
- Detalles de calidad profesional que se esperan: contorno oscuro de 1 px en sprites, sombreado de 2 tonos, animaciones de 2 a 4 cuadros, parpadeo al ser golpeado, partículas simples (polvo al aterrizar, chispas al recoger), y rebote al golpear bloques.
- **Fondos de 3 capas** con parallax (la capa lejana se mueve al 20 %, la media al 50 %, la cercana al 80 % de la cámara).
- Cielos con degradado dibujado una sola vez en una superficie.
- La **bandera de Ecuador** se dibuja con franja amarilla (la mitad superior), azul y roja, con un pequeño escudo central simplificado.
- Herramienta de desarrollo: `pruebas/visor_sprites.py` que dibuja en una hoja todos los sprites, para revisar el arte.

### 11.2 Sonido (sintetizado)

- `sonido.py` genera ondas **cuadrada, triangular y de ruido** usando solo `array`, `math` y `random`, y crea `pygame.mixer.Sound(buffer=...)`. Frecuencia de muestreo 22050 Hz, mono, 16 bits.
- Efectos: saltar, coleccionable, pisar enemigo, golpe, comida, romper ladrillo, checkpoint, vida extra, victoria, game over, temblor del volcán.
- Música: una melodía corta en bucle por región, escrita como una lista de notas dentro de un diccionario (nota, duración) para mantenerlo simple.
- **M** silencia o activa todo. Si no hay dispositivo de audio, el juego funciona igual sin sonido (capturar la excepción).

---

## 12. Estructura de carpetas

```text
videojuego_aventura/
├── plan_videojuego_aventura.md     ← este documento
├── requirements.txt                ← pygame>=2.5
├── jugar.bat                       ← crea .venv, instala y ejecuta
├── main.py                         ← punto de entrada
├── puntaje.json                    ← se crea solo (mejor puntaje, idioma, personaje)
├── src/
│   ├── ajustes.py                  ← constantes: pantalla, física, colores, personajes, accesorios
│   ├── textos.py                   ← textos ES/EN y función t()
│   ├── guardado.py                 ← leer y escribir puntaje.json
│   ├── motor.py                    ← bucle principal, escenas, escala del lienzo, F11
│   ├── entrada.py                  ← EntradaTeclado y EntradaGuion
│   ├── sprites.py                  ← pixel art procedural, caché, personajes (32), enemigos, comidas, bloques
│   ├── fondos.py                   ← cielos y capas de parallax por región
│   ├── camara.py                   ← cámara con suavizado
│   ├── jugador.py                  ← física, animación, estados pequeño/grande
│   ├── enemigos.py                 ← Cangrejo, Condor, Mono, Iguana
│   ├── objetos.py                  ← Comida, Coleccionable, Bloque, Checkpoint, Bandera, Sello
│   ├── nivel.py                    ← cargador de diccionarios, validación, colisiones con el mapa
│   ├── jefe.py                     ← Cotopaxi, ceniza y rocas
│   ├── interfaz.py                 ← HUD, botones, desplegable de idioma
│   ├── escenas.py                  ← Titulo, Seleccion, Juego, Pausa, FinNivel, GameOver, Victoria
│   └── sonido.py                   ← efectos y música sintetizados
├── niveles/
│   ├── __init__.py                 ← LISTA_NIVELES
│   ├── costa.py
│   ├── sierra.py
│   ├── amazonia.py
│   ├── galapagos.py
│   └── cotopaxi.py
├── pruebas/
│   ├── prueba_humo.py              ← arranca sin ventana, recorre escenas y niveles, guarda capturas
│   └── visor_sprites.py            ← hoja con todos los sprites
├── capturas/                       ← capturas para revisar y para ilustrar este .md
└── assets/                         ← vacía. Reservada para sprites PNG o sonidos futuros
```

`jugar.bat` (mínimo):

```bat
@echo off
cd /d "%~dp0"
if not exist .venv (
    py -3 -m venv .venv || python -m venv .venv
)
.venv\Scripts\python -m pip install -q -r requirements.txt
.venv\Scripts\python main.py
pause
```

---

## 13. Fases de construcción

Cada fase tiene: **Qué se pide a la IA → Qué se construye → Cómo se verifica.** No avanzar sin pasar la verificación.

### Fase 1 — Entorno y esqueleto

- **Qué se pide:** "Crea el entorno virtual, instala pygame y arma el esqueleto: ventana de 1280×720 con lienzo interno de 320×180, bucle a 60 FPS, escenas vacías, `ajustes.py`, `textos.py`, `guardado.py`, `jugar.bat` y `requirements.txt`."
- **Qué se construye:** `requirements.txt`, `jugar.bat`, `main.py`, `src/ajustes.py`, `src/textos.py`, `src/guardado.py`, `src/motor.py`, `src/entrada.py`.
- **Cómo se verifica:**
  - El comando de prueba abre la ventana sin errores, corre 120 cuadros y sale.
  - `textos.t("jugar")` devuelve `Jugar` en español y `Play` en inglés.
  - `puntaje.json` se crea y se lee bien.
  - Captura del lienzo con un texto con tildes y eñes (por ejemplo `Galápagos`, `Año`) para comprobar que la fuente las dibuja.

### Fase 2 — Arte procedural

- **Qué se pide:** "Genera todos los sprites por código: 32 personajes (8 personajes × 4 accesorios) con animaciones, 4 enemigos, 5 comidas, 5 coleccionables, bloques, bandera de Ecuador, partículas, y los fondos de parallax de las 5 regiones."
- **Qué se construye:** `src/sprites.py`, `src/fondos.py`, `pruebas/visor_sprites.py`.
- **Cómo se verifica:**
  - El visor guarda `capturas/hoja_sprites.png` y se revisa con los ojos: contornos limpios, los 8 personajes se distinguen entre sí, los accesorios son reconocibles.
  - Cada fondo se guarda como `capturas/fondo_<region>.png`.
  - La generación completa tarda menos de 2 segundos (medir e imprimir).

### Fase 3 — Jugador, física y cámara

- **Qué se pide:** "Implementa el jugador con las constantes de la sección 4.3, colisiones por ejes, salto variable, coyote y buffer, y la cámara con suavizado. Usa un nivel de prueba temporal."
- **Qué se construye:** `src/jugador.py`, `src/camara.py`, `src/nivel.py` (versión mínima con suelo y plataformas).
- **Cómo se verifica con `EntradaGuion`:**
  - Salto corto y salto largo llegan a alturas distintas (≈ 1,5 y ≈ 3 baldosas).
  - Correr cruza un hueco de 4 baldosas; caminar no.
  - El jugador no atraviesa suelo ni paredes. Captura de la escena.

### Fase 4 — Cargador de niveles, bloques y comida

- **Qué se pide:** "Carga los niveles desde diccionarios con la leyenda de la sección 7.3, con validación. Implementa bloques `?` y `B`, la comida que crece, checkpoints, bandera y fin de nivel."
- **Qué se construye:** `src/nivel.py` completo, `src/objetos.py`, `niveles/__init__.py` y `niveles/costa.py` (primer nivel).
- **Cómo se verifica:**
  - Una fila de mapa con largo incorrecto lanza un error claro con el número de fila.
  - Prueba guionizada: golpear `?` suelta comida, el jugador la come y pasa de 16×16 a 16×32. Estando grande rompe un `B`.
  - Tocar la bandera termina el nivel con bono por tiempo.

### Fase 5 — Enemigos, coleccionables, vidas y puntaje

- **Qué se pide:** "Implementa los 4 enemigos con sus comportamientos, pisar para eliminar, daño pequeño/grande, invulnerabilidad, coleccionables, puntaje, vidas, vida extra a los 100 y muerte con reaparición en checkpoint."
- **Qué se construye:** `src/enemigos.py`, ajustes en `jugador.py` y `nivel.py`.
- **Cómo se verifica con prueba guionizada:**
  - Pisar suma 100. Tocar de lado siendo pequeño quita una vida. Siendo grande vuelve a pequeño.
  - La iguana necesita dos pisotones.
  - Reaparecer tras morir lleva al último checkpoint.
  - 100 coleccionables dan una vida extra.

### Fase 6 — Menús, selección de personaje, idioma e interfaz

- **Qué se pide:** "Construye título con el desplegable ES/EN arriba a la derecha, selección de personaje y accesorio con vista previa animada, HUD, pausa, Game Over y Victoria. Guarda idioma, personaje, accesorio y mejor puntaje."
- **Qué se construye:** `src/interfaz.py`, `src/escenas.py`, ajustes en `motor.py`.
- **Cómo se verifica:**
  - Con clic simulado y con la tecla **L**, el idioma cambia y el texto de todas las pantallas cambia al instante.
  - Se reinicia el programa y recuerda idioma y personaje.
  - Capturas: `capturas/menu_es.png`, `capturas/menu_en.png`, `capturas/seleccion.png`, `capturas/hud.png`.

### Fase 7 — Cuatro niveles completos y el jefe Cotopaxi

- **Qué se pide:** "Diseña los niveles 2 a 4 con sus paisajes, enemigos y comidas. Completa el nivel 1. Implementa el jefe Cotopaxi con su ciclo de erupción, los 3 sellos de hielo, la barra de vida y la victoria."
- **Qué se construye:** `niveles/sierra.py`, `niveles/amazonia.py`, `niveles/galapagos.py`, `niveles/cotopaxi.py`, `src/jefe.py`.
- **Cómo se verifica:**
  - Los 5 niveles cargan y se pueden **completar** con un guion de entrada (o con una ruta de prueba). Cada uno tiene `P`, al menos 2 `K` y una `F`.
  - Los huecos nunca superan 4 baldosas.
  - Capturas: `capturas/nivel_costa.png`, `nivel_sierra.png`, `nivel_amazonia.png`, `nivel_galapagos.png`, `nivel_cotopaxi.png`.
  - En el jefe: los 3 sellos activados detienen la ceniza y aparece la bandera.

### Fase 8 — Sonido, pulido, pruebas y entrega

- **Qué se pide:** "Agrega los efectos y las músicas sintetizadas. Pule: animaciones, partículas, transiciones, rendimiento. Completa `prueba_humo.py`, genera las capturas finales y haz el checklist de aceptación."
- **Qué se construye:** `src/sonido.py`, `pruebas/prueba_humo.py` final, `capturas/`.
- **Cómo se verifica:** checklist de la sección 14.

---

## 14. Checklist de aceptación

- [x] `jugar.bat` crea el entorno, instala pygame y abre el juego sin errores. *(Se ejecutó el `.bat` completo: instala pygame y abre el juego. El `.venv` ya existía, así que la rama que lo crea con `py -3` se probó a mano con la ruta completa de Python 3.12.)*
- [x] El comando de prueba sin ventana (`SDL_VIDEODRIVER=dummy`) termina con código 0 y recorre menú → selección → 5 niveles → victoria. *(`pruebas/prueba_humo.py`: 22/22 con audio y 22/22 con `--sin-audio`.)*
- [x] Rendimiento: se mantiene en 60 FPS (o muy cerca) en una PC común. La generación inicial de sprites tarda menos de 2 s. *(Arte completo en 0,02 s. Cuadro medio 0,62 ms (p99 0,92 ms) incluyendo el escalado ×4. Medido sin ventana: los FPS con ventana real dependen del monitor y no se pudieron observar.)*
- [x] Hay 8 personajes × 4 accesorios y todos se ven distintos entre sí. La selección se recuerda al reiniciar. *(`capturas/hoja_sprites.png`, `capturas/seleccion.png`.)*
- [x] Desplegable **ES / EN** arriba a la derecha del menú de inicio. También funciona con **L**. Todos los textos cambian. No quedan claves sin traducir. *(La prueba de humo vigila `t()` durante todo el recorrido: 0 claves perdidas.)*
- [x] Se dibujan bien las tildes y las eñes (Amazonía, Galápagos, Andrés). *(Revisado en capturas: `seleccion.png` y el HUD de cada nivel.)*
- [x] La comida de cada región aparece al golpear `?`, hace crecer al jugador y **no muestra su nombre**, solo el ícono.
- [x] Siendo grande, un golpe reduce a pequeño. Siendo pequeño, quita una vida. Grande rompe ladrillos.
- [x] Los 4 enemigos se comportan como se describe y se eliminan pisándolos (la iguana, con dos pisotones).
- [x] Checkpoints, bandera de Ecuador, bono por tiempo y vida extra a los 100 coleccionables funcionan.
- [x] El jefe Cotopaxi se vence activando los 3 sellos y termina en la pantalla de Victoria. *(Los 3 sellos se alcanzan saltando: lo comprueba `prueba_jefe.py`. En la prueba de humo el recorrido del jefe usa una ruta de prueba que teletransporta al jugador a cada sello.)*
- [x] `puntaje.json` guarda mejor puntaje, idioma, personaje y accesorio.
- [x] Sonidos y músicas funcionan. **M** silencia. Sin dispositivo de audio, el juego no se cae. *(Se generan y reproducen sin errores, **M** silencia y vuelve a activar, y sin dispositivo se usa `SonidoNulo`. Pendiente humano: oír el resultado una vez con altavoces; la verificación fue sin salida de audio.)*
- [x] Todo el código y los comentarios están en español. Los identificadores no llevan tildes ni eñes. *(Se comprobó con `tokenize`: ningún identificador con caracteres no ASCII.)*
- [x] No se descargó ningún archivo externo. La única dependencia es pygame. *(Las fuentes son las del sistema.)*
- [x] En `capturas/` hay al menos: `menu_es.png`, `menu_en.png`, `seleccion.png`, `nivel_costa.png`, `nivel_sierra.png`, `nivel_amazonia.png`, `nivel_galapagos.png`, `nivel_cotopaxi.png` y `hud.png`. Se revisaron visualmente.
- [x] Se completó la sección 15 con los cambios y los problemas encontrados.

---

## 15. Decisiones tomadas durante la construcción

Cómo ejecutar todas las pruebas (desde `videojuego_aventura/`, con `$env:SDL_VIDEODRIVER="dummy"; $env:SDL_AUDIODRIVER="dummy"`):
`prueba_fisica.py`, `prueba_niveles.py`, `prueba_reglas.py`, `prueba_menus.py`, `prueba_niveles_completos.py`, `prueba_jefe.py`, `prueba_humo.py` y `prueba_humo.py --sin-audio`. Resultado final: todas terminan con código 0 (13 + 12 + 28 + 21 + 39 + 20 + 22 + 22 comprobaciones).

| Fase | Decisión o problema | Solución |
|---|---|---|
| 1 | Los módulos de `src/` se importan unos a otros por nombre (`import ajustes`), sin paquete. | `main.py` y las pruebas agregan `src/` y la raíz a `sys.path`. La clase base `Escena` vive en `motor.py` para evitar importaciones circulares. |
| 1 | Fuente para 320×180 sin suavizado: se probaron 9 fuentes del sistema. | Texto normal: `trebuchetms` 9 px (alternativas `consolas`, `dejavusansmono`). Títulos: `verdana` negrita ampliada ×2 con contorno (la negrita de Trebuchet dejaba huecos entre letras). |
| 1 | Al reiniciar pygame, las fuentes guardadas en caché daban `Text has zero width`. | `interfaz.reiniciar_fuentes()` se llama al crear el `Motor`. |
| 1 | `puntaje.json` podía quedar con valores inválidos si alguien lo edita a mano. | `Motor._validar()` vuelve a los valores iniciales de personaje, accesorio, idioma y puntaje. |
| 2 | Personajes: 32 combinaciones por capas (cuerpo por tono de piel + cabello + accesorio). La versión grande (16×32) se obtiene repitiendo 7 filas del torso y 9 de las piernas. | Se generan 448 cuadros en ~0,01 s. El sombrero de paja toquilla se veía casi negro (demasiado contorno): se rehízo con copa y ala beige. Se quitó el brazo levantado del salto (píxeles sueltos). |
| 2 | Los fondos mostraban franjas verticales al rellenar colinas cada 2 px. | Se rellena cada 1 px; el cactus de Galápagos se redibujó con palas ovaladas. |
| 3 | Constantes de física: **sin cambios**. Resultado medido: salto corto 1,34 baldosas, salto largo 2,97. | `prueba_fisica.py` lo comprueba con `EntradaGuion`. |
| 3 | **Desviación del plan:** con 90 px/s, 0,67 s de vuelo y 12 px de hitbox, caminar **sí** cruza un hueco de 4 baldosas (60 px de vuelo contra 52 px necesarios). Correr cruza hasta unas 6. | Se mantuvo el límite de diseño de 4 baldosas. La prueba exige: correr cruza 4 y 5, caminar no cruza 5, ni corriendo se cruzan 8. Para que caminar tampoco cruce 4 habría que bajar `VEL_CAMINAR` a unos 75 px/s en `ajustes.py`. |
| 4 | Validación del mapa: 11 filas, mismo largo, símbolos válidos, una sola `P`, al menos una `F`. | `ErrorNivel` indica la fila contando desde 1 (ej.: "la fila 5 mide 77 caracteres y debe medir 80"). |
| 4 | El coleccionable de un nivel puede ser una lista (Costa alterna `banano` y `cacao`). | `datos["coleccionable"]` acepta texto o lista. |
| 4 | El piloto de pruebas saltó por encima del mástil de la bandera y chocó con el muro final. | Mástil de 96 px (6 baldosas) y 32 px de zona de contacto invisible sobre la punta. |
| 5 | Reglas no especificadas: tras morir, el tiempo del nivel se reinicia, los enemigos vencidos no reviven y el tamaño al reaparecer es el que se tenía al pasar el checkpoint. | Implementado en `Nivel._reaparecer()` y verificado en `prueba_reglas.py`. |
| 5 | La colada morada (jefe) da vida extra y además hace crecer si el jugador es pequeño. El pisotón a la iguana da 100 puntos las dos veces. | Documentado aquí. En el Cotopaxi también camina una `Ceniza` (enemigo normal) además de la ceniza y las rocas que caen. |
| 6 | El desplegable cerrado muestra `ES`/`EN` y abierto muestra `ES – Español` y `EN – English`. **L** cambia el idioma también en la selección. | `interfaz.Desplegable`. |
| 6 | "Sombrero otavaleño" no cabía en su botón y se cortaba con un punto. | `interfaz.texto_ajustado()` parte el texto en dos líneas. |
| 7 | Los 5 mapas se diseñaron con un pequeño lenguaje de funciones (`pruebas/generar_niveles.py`) que valida huecos, conteos y checkpoints y escribe `niveles/*.py` con el mapa literal. | Los archivos se pueden editar a mano; el juego solo lee los diccionarios. Valores finales (coleccionables / enemigos): Costa 90 / 10, Sierra 91 / 9, Amazonía 81 / 11, Galápagos 96 / 10. |
| 7 | Reglas de diseño aprendidas con el piloto automático: las plataformas flotantes angostas (2 baldosas) no se pueden tomar con un salto corriendo (vuela 93 px); un enemigo cerca de un hueco empuja al jugador al agua; un jugador grande (30 px) no pasa bajo plataformas a una sola baldosa del suelo. | Plataformas de 4 baldosas, enemigos a más de 12 baldosas antes de un hueco (el generador avisa), plataformas flotantes solo sobre agua o abismo, bloques a 4 filas sobre el suelo. En la Sierra se quitaron las piedras de los abismos. |
| 7 | "Plataformas altas" en la Sierra: se resolvió con riscos de hasta 4 baldosas de altura, subidos en escalones de 2. | Ver `niveles/sierra.py`. |
| 7 | Para probar los niveles 1 a 4 se escribió un `Piloto` (en `pruebas/ayuda.py`) que corre y salta ante muros, bordes y enemigos. | Para que no se atasque ignora enemigos (con invulnerabilidad de prueba) cuando hay un hueco cerca. El jefe se prueba con salto real a cada sello (`prueba_jefe.py`). |
| 8 | **Error encontrado al ejecutar `main.py` de verdad:** el arte nunca se generaba al arrancar (las pruebas lo hacían por su cuenta) y fallaba con `KeyError: 'terreno'`. | `Motor.__init__` genera sprites y fondos una sola vez y guarda el tiempo en `segundos_arte`. |
| 8 | Sonido: ondas cuadrada, triangular y ruido con `array`, `math` y `random` a 22050 Hz mono 16 bits. 18 efectos y 7 músicas (una por región, más título y victoria). | Todo se genera en menos de 0,3 s. Las músicas se escriben como texto (`"E5 G5:2"` = nota y corcheas). Sin audio, `Motor` usa `SonidoNulo`. |
| 8 | Archivos extra respecto al árbol de la sección 12: `src/sonido_nulo.py` y las pruebas por fase (`prueba_fisica`, `prueba_niveles`, `prueba_reglas`, `prueba_menus`, `prueba_niveles_completos`, `prueba_jefe`) más `ayuda.py` y `generar_niveles.py`. | Cada prueba corresponde a la verificación de una fase. |
| 8 | Límites de esta verificación. | No se escuchó el audio, no se midieron FPS con ventana real, y la pantalla completa (F11) solo se probó con el controlador `dummy`. Conviene jugar unos minutos en un PC con pantalla y altavoces. |
| Después | **Texto muy pixelado** (comentario del docente): al dibujarse en 320×180 y ampliarse ×4, cada letra quedaba con bloques de 4×4 píxeles. | El texto ahora va a una capa transparente de la resolución real de la ventana (`Motor.capa_texto`, `interfaz.configurar_capa()`), con fuentes del sistema suavizadas (`trebuchetms` para el texto, `verdana` negrita para los títulos). El tamaño sigue expresándose en píxeles del lienzo (`tam=9`), así que el diseño de las pantallas no cambió. Solo se copian a pantalla las zonas con texto, y el costo por cuadro casi no varió (0,62 → 0,74 ms). Si no hay capa (una prueba que dibuja en otra superficie) se usa el texto pixelado de antes. En pantalla completa la capa se agranda sola, así que el texto se ve nítido a cualquier tamaño. Efectos secundarios: la pausa ya no muestra el HUD, y el aviso "L: idioma" se oculta cuando el desplegable está abierto. |
| Después | **Título más Inca** (comentario del docente): la letra de verdana se veía correcta pero genérica. Las fuentes del sistema no son portables (Papyrus o Algerian existen en esta PC, pero no en todas) y no está permitido descargar fuentes. | Tipografía propia generada por código, `src/letras_inca.py`: las 26 letras se definen como trazos horizontales y verticales, y las diagonales se hacen con **escaleras**, como las pirámides escalonadas y las puertas trapezoidales andinas. Se dibujan con rectángulos a la resolución de la ventana (bordes limpios a cualquier tamaño) con degradado dorado, bisel, contorno oscuro y sombra, y con una **chakana** (cruz escalonada andina) a cada lado. Se usa solo en el título del menú (`interfaz.titulo_inca()`); si el texto trae una letra que no está en la tipografía, usa el título normal. Se revisa con `pruebas/visor_titulo.py` (genera `capturas/hoja_inca.png`). |

Capturas incluidas en `capturas/`: `hoja_sprites.png`, `fondo_<region>.png` (5), `menu_es.png`, `menu_en.png`, `menu_desplegable.png`, `seleccion.png`, `hud.png`, `cartel_nivel.png`, `pausa.png`, `nivel_<region>.png` (5), `fin_nivel.png`, `fase7_jefe_aviso.png`, `fase7_jefe_derrotado.png`, `victoria.png`, `game_over.png` y otras de cada fase.

---

## 16. Para explicar en clase

Una idea para usar este documento con los estudiantes:

1. Mostrar el juego funcionando.
2. Abrir este `.md` y recorrer la sección 3 (decisiones) y las fases.
3. Para cada fase, mostrar la captura correspondiente y qué archivo creó.
4. Señalar los conceptos de Python que ya conocen: **diccionarios** (niveles, textos, paletas, personajes), **bucles** (bucle de juego, recorrido del mapa), **condicionales** (colisiones, reglas) y **funciones** (`t()`, `cargar_nivel()`).
5. Mostrar que cambiar un dato (por ejemplo un nombre de personaje en `ajustes.py` o un texto en `textos.py`) cambia el juego sin tocar el motor.
