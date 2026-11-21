# curso_intro_python

Repositorio de **proyectos de ejemplo para aprender Python**. Cada carpeta es un proyecto completo y funcional que puedes ejecutar, leer, modificar y explicar.

La idea es aprender haciendo: en vez de solo ver código aislado, trabajarás con programas reales que usan **funciones, clases, archivos, bibliotecas externas, APIs y interfaces gráficas o web**.

---

## Contenido del repositorio

| Carpeta / archivo | Tipo | Qué es | Qué aprendes |
|---|---|---|---|
| [`videojuego_aventura/`](#proyecto-1-videojuego-aventura-ecuador) | Videojuego 2D | Juego de plataformas estilo Mario Bros con temática ecuatoriana | Bucles de juego, condicionales, clases, Pygame, sonido y gráficos generados por código |
| [`Chatbot/`](#proyecto-2-chatbot-asistente) | Aplicación web | Asistente con Flask que usa la API de Gemini, memoria y herramientas | Peticiones HTTP, JSON, Flask, archivos, variables de entorno y APIs externas |
| `saldo.py` | Script | Consulta el saldo de tu clave de OpenRouter | Leer `.env`, hacer peticiones HTTP y mostrar datos |
| `ejemplo_projectos.txt` | Texto | Lista de los proyectos propuestos para el curso | Planificación de un proyecto |

---

## Antes de empezar

### 1. Instala Python

Necesitas **Python 3.10 o superior** (los proyectos se probaron con 3.12).

- Descárgalo desde <https://www.python.org/downloads/>.
- En Windows, marca la casilla **«Add python.exe to PATH»** durante la instalación.

Comprueba la instalación en una terminal:

```powershell
python --version
```

Si la terminal no reconoce `python`, prueba con `py --version` o abre una terminal nueva.

### 2. Conoce el entorno virtual (`.venv`)

Un **entorno virtual** es una carpeta aislada donde se instalan las bibliotecas de un proyecto, sin mezclarlas con las demás. Cada proyecto de este repositorio usa su propio `.venv`.

### 3. Clona el repositorio

```powershell
git clone https://github.com/andreagonzalezsilva/python_projectos_ejemplos.git
cd python_projectos_ejemplos
```

---

## Proyecto 1: Videojuego «Aventura Ecuador»

Carpeta: [`videojuego_aventura/`](videojuego_aventura/)

Un videojuego de plataformas 2D hecho con **Pygame**. Un niño o una niña recorre Ecuador en cuatro niveles (Costa, Sierra, Amazonía y Galápagos) y al final sube a la cima del Cotopaxi para calmar al volcán.

Todo el arte y el sonido se generan con código: no hay imágenes ni archivos de audio descargados.

### Qué tiene el juego

- **Cuatro niveles** con fondos y enemigos propios, más un **jefe** final.
- **Menú** con idioma **ES / EN** (desplegable arriba a la derecha).
- **Puntaje** guardado en `puntaje.json`.
- **Música y efectos** sintetizados por código.

### Controles

| Acción | Teclas |
|---|---|
| Mover | Flechas ← → o `A` / `D` |
| Saltar | `Espacio`, `W` o flecha ↑ |
| Correr | `Shift` |
| Pausa | `Esc` |
| Pantalla completa | `F11` |

### Cómo correrlo (Windows)

**Opción A: doble clic.** Abre la carpeta `videojuego_aventura/` y ejecuta `jugar.bat`. El script crea el entorno virtual, instala Pygame y arranca el juego.

**Opción B: desde la terminal (PowerShell).** Desde la carpeta `videojuego_aventura/`:

```powershell
# 1. Crear el entorno virtual
python -m venv .venv

# 2. Instalar las dependencias (solo Pygame)
.\.venv\Scripts\python -m pip install -r requirements.txt

# 3. Ejecutar el juego
.\.venv\Scripts\python main.py
```

### Cómo correrlo (macOS o Linux)

```bash
cd videojuego_aventura
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

### Estructura del código

| Archivo / carpeta | Qué hace |
|---|---|
| `main.py` | Punto de entrada: crea el motor y abre el menú de título |
| `src/motor.py` | Bucle principal: actualiza y dibuja la escena en cada cuadro |
| `src/escenas.py` | Pantallas del juego (título, selección de nivel, pausa, victoria…) |
| `src/nivel.py` | Lógica de un nivel: colisiones, monedas, meta |
| `src/jugador.py`, `src/enemigos.py`, `src/jefe.py` | Personajes, cada uno con su propia clase |
| `src/entrada.py` | Lee el teclado. El resto del juego nunca lee el teclado directamente |
| `src/textos.py` | Todos los textos visibles, en español e inglés |
| `niveles/` | Un archivo por nivel: costa, sierra, amazonía, galápagos y cotopaxi |
| `pruebas/` | Scripts para probar partes del juego sin jugarlo a mano |
| `plan_videojuego_aventura.md` | El plan completo con el que se diseñó el juego, fase por fase |

### Ideas para practicar

- Cambia la velocidad del jugador en `src/jugador.py` y observa cómo cambia la sensación de juego.
- Agrega un texto nuevo en `src/textos.py` y muéstralo en pantalla.
- Ejecuta `pruebas/prueba_humo.py` para ver cómo se puede probar el juego sin ventana.

---

## Proyecto 2: Chatbot «Asistente»

Carpeta: [`Chatbot/`](Chatbot/)

Un asistente personal en una **página web** hecha con **Flask**. Usa la API gratuita de **Google Gemini** y puede:

- **Recordar** tu nombre y tus preferencias.
- **Administrar tareas y notas**.
- **Consultar internet**: noticias, clima, Wikipedia y, opcionalmente, búsqueda web.
- Mantener **varias conversaciones** a la vez, en pestañas.

Documentación completa, con los archivos en orden sugerido para explicarlos en clase, en [`Chatbot/README.md`](Chatbot/README.md).

### Requisitos previos

- Una **clave gratuita de Gemini**: entra en <https://aistudio.google.com/apikey> con tu cuenta de Google, crea la clave y guárdala. No necesita tarjeta.
- Opcional: una clave gratuita de Tavily para búsqueda web (<https://www.tavily.com>).

### Cómo correrlo (Windows, PowerShell)

Desde la carpeta `Chatbot/`:

```powershell
# 1. Crear el entorno virtual e instalar las dependencias
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt

# 2. Crear tu archivo de configuración a partir del ejemplo
Copy-Item .env.example .env
```

Abre el archivo `.env` con un editor y completa, como mínimo:

| Variable | Qué poner |
|---|---|
| `GEMINI_API_KEY` | Tu clave de Google AI Studio |
| `APP_PASSWORD` | La contraseña que usarás para entrar a la página |
| `SECRET_KEY` | Una cadena larga y aleatoria (ver el comando de abajo) |

Genera una `SECRET_KEY` con:

```powershell
.\.venv\Scripts\python -c "import secrets; print(secrets.token_hex(32))"
```

Luego ejecuta el servidor web:

```powershell
.\.venv\Scripts\python app.py
```

Abre <http://127.0.0.1:5000> en el navegador, escribe tu contraseña y empieza a chatear.

> **Para detener el servidor**, vuelve a la terminal y presiona `Ctrl + C`.

### Cómo correrlo (macOS o Linux)

```bash
cd Chatbot
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env     # luego edita .env con tus datos
python app.py
```

### Probar sin gastar cuota de Gemini

El proyecto incluye pruebas que usan un Gemini **simulado**, así que no gastan tu cuota ni necesitan red:

```powershell
# Pruebas automáticas
.\.venv\Scripts\python -m unittest discover -s pruebas -v

# Página completa con un Gemini simulado (contraseña: simulado)
.\.venv\Scripts\python pruebas\servir_simulado.py
```

### Estructura del código

| Archivo | Qué enseña |
|---|---|
| `configuracion.py` | Leer `.env`, variables de entorno y validar lo que falta |
| `personalidad.txt` | El *prompt de sistema*: cómo se le da carácter al asistente |
| `gemini.py` | Una petición HTTP con `requests`: URL, cabeceras, JSON y errores |
| `memoria.py` y `almacen.py` | Guardar datos en JSON, historial y preferencias |
| `herramientas.py` | Funciones que Gemini puede llamar |
| `internet.py` | Consultar APIs externas: RSS, JSON, clima, Wikipedia |
| `asistente.py` | El bucle: llamar a Gemini, ejecutar funciones y devolver resultados |
| `app.py` | Flask: rutas, sesión, login y respuestas JSON |
| `templates/` y `static/` | HTML, CSS y JavaScript para la página |

### Ideas para practicar

- Cambia `BOT_NAME` en `.env` y observa cómo cambia el asistente.
- Edita `personalidad.txt` para darle otro carácter.
- Agrega una nueva función en `herramientas.py` y explica cómo Gemini decide usarla.

> **Privacidad:** no escribas contraseñas, datos médicos ni información sensible en el chat. Las claves van solo en `.env`, que no se sube a git.

---

## Script: `saldo.py` (clave de OpenRouter)

Muestra cuánto has consumido de tu clave de OpenRouter y cuánto saldo te queda.

1. Crea un archivo `.env` en la raíz del repositorio con tu clave:

   ```text
   OPENROUTER_API_KEY=sk-or-v1-...
   ```

2. Ejecútalo:

   ```powershell
   python saldo.py
   ```

El script no necesita instalar bibliotecas: usa solo la biblioteca estándar de Python.

---

## Solución de problemas

| Síntoma | Solución |
|---|---|
| `python` no se reconoce | Usa `py` en lugar de `python`, o reinstala Python marcando «Add to PATH» |
| `No module named 'flask'` o `'pygame'` | No instalaste las dependencias. Ejecuta `pip install -r requirements.txt` con el Python de `.venv` |
| En la página del chatbot aparece «Falta configurar» | Falta algo en `.env`. Revisa la tabla de variables de arriba |
| «Contraseña incorrecta» | Revisa `APP_PASSWORD` en `.env` y reinicia `app.py` |
| El juego no abre en Windows | Ejecuta `jugar.bat` o revisa que el entorno virtual esté activo (`.venv`) |

