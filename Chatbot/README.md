# 🤖 Asistente: tu chatbot personal con Python, Flask y Gemini

Un asistente por chat que **recuerda** cómo te llamas, **administra tus tareas**, **guarda tus notas** y **consulta internet** (noticias, clima y búsqueda web). Se publica gratis en internet (PythonAnywhere) y usa una clave gratuita de Gemini.

## ¿Qué lo hace diferente de usar Gemini directamente?

Si abres Gemini en el navegador, conversas con un modelo que no conoce tu lista de tareas ni actúa sobre ella. Este proyecto usa la **API** de Gemini y le suma:

- **Memoria:** guarda los últimos 20 mensajes de cada conversación y tus preferencias (por ejemplo, tu nombre) en archivos JSON. Si reinicias el servidor, sigue recordándote.
- **Pestañas de chats:** hasta 8 conversaciones a la vez, en una lista vertical a la izquierda del chat. Cada una tiene su propio historial y el título de su primer mensaje. Botón **+ Nuevo** para abrir otra y **×** para cerrarla. El botón **«** oculta la lista (queda una franja angosta) y **»** la vuelve a mostrar; el navegador recuerda tu elección y en el teléfono empieza oculta. Tareas, notas y lo que recuerda de ti son **comunes a todas las pestañas**, así «Me llamo Ana» se sabe en todos los chats.
- **Herramientas (*function calling*):** Gemini puede pedir que Python ejecute funciones: agregar, listar y completar tareas, agregar y listar notas, guardar una preferencia y consultar internet (ver [Acceso a internet](#acceso-a-internet)). El panel de la página se actualiza solo, así *ves* que el asistente actuó.
- **Personalidad propia:** el archivo `personalidad.txt` dice cómo habla tu asistente, y `BOT_NAME` le pone nombre.
- **Tu propio sitio:** con contraseña, publicado en tu dirección `TU_USUARIO.pythonanywhere.com`.

> Un solo perfil por copia: cada estudiante despliega **su** bot con **su** clave. No hay registro de usuarios.

---

## Requisitos

- Python 3.10 o superior (se probó con 3.12).
- Una cuenta de Google para crear la clave gratuita de Gemini.
- Las tres únicas dependencias están en `requirements.txt`: `flask`, `requests` y `python-dotenv`.

## Cómo conseguir la clave gratuita de Gemini

1. Entra en <https://aistudio.google.com/apikey> con tu cuenta de Google.
2. Crea una clave (no pide tarjeta). Cópiala y **no la compartas**.
3. Pégala en tu archivo `.env` (ver abajo). Nunca la escribas en el código.

---

## Ejecutar en tu computadora (Windows, PowerShell)

Desde la carpeta `Chatbot/`:

```powershell
# 1. Crear el entorno virtual e instalar las dependencias
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt

# 2. Copiar la configuración de ejemplo
Copy-Item .env.example .env
```

> Si la terminal no reconoce `python`, usa la ruta completa: `$env:LOCALAPPDATA\Programs\Python\Python312\python.exe`, o abre una terminal nueva.

3. Abre `.env` con un editor y completa:

| Variable | Qué poner |
|---|---|
| `GEMINI_API_KEY` | Tu clave de Google AI Studio |
| `GEMINI_MODEL` | El modelo (por defecto `gemini-3.5-flash-lite`) |
| `BOT_NAME` | El nombre de tu asistente |
| `APP_PASSWORD` | La contraseña para entrar a la página |
| `SECRET_KEY` | Una cadena larga y aleatoria (la genera el comando de abajo) |
| `ZONA_HORARIA` | Por ejemplo `America/Guayaquil` |
| `TAVILY_API_KEY` | *Opcional.* Clave gratuita de Tavily para buscar en toda la web (ver [Acceso a internet](#acceso-a-internet)) |
| `BUSQUEDA_WEB` | *Opcional.* `0` (por defecto) o `1`. Con `1` usa la búsqueda de Google dentro de Gemini; **requiere facturación activada** en Google |

```powershell
# Generar una SECRET_KEY
.\.venv\Scripts\python -c "import secrets; print(secrets.token_hex(32))"
```

4. Elige cómo hablar con tu asistente:

```powershell
# Chat en la terminal (escribe "salir" para terminar)
.\.venv\Scripts\python consola.py

# Servidor web local: abre http://127.0.0.1:5000
.\.venv\Scripts\python app.py
```

Si falta algo en `.env`, la web muestra "Falta configurar: …" en la página de entrada y la consola lo imprime y termina. No se cae.

## Acceso a internet

Gemini por sí solo no tiene internet. Este proyecto le da herramientas para consultarlo. Algunas no necesitan clave:

| Herramienta | Fuente | Qué responde | Clave |
|---|---|---|---|
| `buscar_noticias` | Google Noticias (RSS) | Titulares recientes, con fuente y fecha | No |
| `consultar_clima` | Open-Meteo | Clima actual y pronóstico de 3 días de una ciudad | No |
| `buscar_wikipedia` | Wikipedia en español | Datos generales: personas, lugares, historia, ciencia | No |
| `buscar_web` | Tavily | Cualquier tema de la web (precios, resultados, recomendaciones…) | `TAVILY_API_KEY` |
| Búsqueda de Google | Gemini (`google_search`) | Cualquier tema, con fuentes | `BUSQUEDA_WEB=1` y facturación |

### Una sola búsqueda general

Para no duplicar llamadas ni gastar cuota de más, el asistente usa **una sola** herramienta de búsqueda general, elegida por esta prioridad:

1. **Google Search**, si `BUSQUEDA_WEB=1`.
2. **Tavily**, si hay `TAVILY_API_KEY`.
3. **Wikipedia**, si no hay ninguna de las anteriores.

Las noticias y el clima siempre están disponibles aparte, porque son gratis y no gastan la cuota de Tavily. Además, el asistente tiene la instrucción de hacer **una sola búsqueda por pregunta**.

### Cómo activar Tavily (opcional)

1. Crea una cuenta en <https://www.tavily.com>. El plan gratuito da **1.000 créditos al mes, sin tarjeta**. Cada búsqueda cuesta 1 crédito. Los créditos se reinician el día 1 de cada mes.
2. Copia tu clave (empieza con `tvly-`) y pégala en `.env`: `TAVILY_API_KEY=tvly-...`.
3. Reinicia la aplicación. Si no pones la clave, el asistente usa Wikipedia y todo lo demás sigue igual.

Si se acaba la cuota, el asistente avisa en el chat y las demás herramientas siguen funcionando.

> **La búsqueda de Google (`BUSQUEDA_WEB=1`) no funciona en el plan gratuito de Gemini:** da el error 429. Solo actívala si tu proyecto de Google tiene facturación. Mientras tanto déjala en `0`.

### Probar sin gastar cuota

```powershell
# Pruebas automáticas (usan un Gemini simulado; sin red y sin clave)
.\.venv\Scripts\python -m unittest discover -s pruebas -v

# La página completa con un Gemini simulado (contraseña: simulado)
.\.venv\Scripts\python pruebas\servir_simulado.py

# Pruebas reales con tu clave: tareas, noticias, Wikipedia, clima y Tavily.
# Gastan unas 10 peticiones de Gemini (y 2 créditos de Tavily si tienes clave). Solo si tienes GEMINI_API_KEY en .env
.\.venv\Scripts\python pruebas\prueba_real.py
```

> En Windows, Python no trae la base de zonas horarias. Si `ZONA_HORARIA` no se encuentra, el asistente usa la hora del sistema (lo avisa en el registro). En PythonAnywhere funciona normal.

---

## Cómo está organizado el código

Orden sugerido para explicarlo en clase:

| # | Archivo | Qué enseña |
|---|---|---|
| 1 | `configuracion.py` | Leer `.env`, variables de entorno, rutas absolutas, validar lo que falta |
| 2 | `personalidad.txt` | El *prompt de sistema*: cómo se le da carácter a un asistente |
| 3 | `gemini.py` | Una petición HTTP con `requests`: URL, cabeceras, cuerpo JSON, errores |
| 4 | `memoria.py` y `almacen.py` | Guardar JSON con escritura atómica; historial de 20 mensajes y preferencias |
| 5 | `herramientas.py` | Funciones que Gemini puede llamar y cómo se las describimos |
| 6 | `internet.py` | Consultar APIs de internet con `requests`: RSS, JSON, claves en cabeceras, errores |
| 7 | `asistente.py` | El bucle: llamar, ejecutar funciones, devolver resultados, guardar memoria |
| 8 | `app.py` | Flask: rutas, sesión, login, JSON |
| 9 | `templates/` y `static/` | HTML, CSS y unas 100 líneas de JavaScript sin librerías |

Reglas de la arquitectura:

- `gemini.py` **solo** habla con la API (envía pasos, devuelve pasos). Si Google cambia el formato, solo se cambia ese archivo.
- `asistente.responder(mensaje)` la usan por igual `app.py` y `consola.py`.
- `herramientas.py` y `memoria.py` no llaman a la API de Gemini: se prueban sin red.
- `internet.py` **solo** consulta internet (noticias, Wikipedia, clima, Tavily) y devuelve datos ordenados. Si algo falla, lanza `ErrorInternet` y `herramientas.py` lo convierte en un mensaje para Gemini. Sus pruebas simulan `requests`: no usan red.
- La clave de Tavily solo viaja en la cabecera `Authorization`. Nunca se escribe en el registro ni en el cuerpo de la petición.
- Los resultados de internet son **datos, no instrucciones**: `personalidad.txt` le dice al asistente que nunca obedezca órdenes que aparezcan dentro de una página o un titular.
- Los textos que ve el usuario viven en `textos.py` y `templates/`.
- Los datos se guardan en `datos/` (`conversaciones.json`, `tareas.json`, `notas.json`, `preferencias.json`). Esa carpeta no se sube a git. Si tenías un `historial.json` de una versión anterior, se convierte solo en la primera pestaña y el archivo viejo queda como respaldo.

### El bucle de funciones, en pocas palabras

1. Se envía a Gemini el historial + tu mensaje + la lista de herramientas.
2. Si Gemini responde con un paso `function_call`, Python ejecuta esa función y se envía el resultado como `function_result`.
3. Se repite (máximo 5 vueltas) hasta que Gemini devuelve texto. Ese texto es la respuesta.

Cada vuelta es **una petición** de tu cuota gratuita.

## Cómo personalizarlo

- **Nombre:** cambia `BOT_NAME` en `.env`.
- **Personalidad:** edita `personalidad.txt`. `{nombre_bot}` se reemplaza por `BOT_NAME`.
- **Región de las noticias:** cambia `PARAMETROS_REGION` en `internet.py` (idioma y país de Google Noticias; por defecto Ecuador).
- **Modelo:** cambia `GEMINI_MODEL` en `.env` (lista en <https://ai.google.dev/gemini-api/docs/models>). Verifica que el modelo tenga uso gratuito en <https://ai.google.dev/gemini-api/docs/pricing>.
- **Mensajes de la interfaz:** `textos.py` y `templates/`.

---

> ## ⚠️ Límites y privacidad (léelo antes de usarlo)
>
> - **Privacidad:** en el plan gratuito de Gemini, Google puede usar los mensajes para mejorar sus productos. **No escribas contraseñas, datos médicos, datos de tus compañeros ni nada sensible** en el chat, en las notas o en las preferencias.
> - **Límites:** los límites gratuitos son **por proyecto de Google**, no por clave, y se reinician a medianoche (hora del Pacífico). Son pequeños y cambian: en AI Studio se ven los vigentes de tu cuenta. Cada mensaje cuesta **1 petición**, o 2 o más si el asistente usa una herramienta.
> - **Una clave por estudiante:** crea **tu propia clave en tu propio proyecto**. Si 30 personas comparten una clave, la cuota se acaba en minutos.
> - **Disponibilidad:** el plan gratuito no está en todos los países. Ecuador está en la lista de regiones disponibles (<https://ai.google.dev/gemini-api/docs/available-regions>). En el Espacio Económico Europeo, Suiza y el Reino Unido pueden aplicar condiciones distintas para apps que usan otras personas: revisa los términos.
> - **Internet:** lo que preguntes puede enviarse como consulta a Google Noticias, Wikipedia, Open-Meteo (la ciudad) o Tavily (el texto de la búsqueda). No escribas datos sensibles tampoco en esas preguntas.
> - **Cuota de Tavily:** 1.000 búsquedas al mes por cuenta, sin tarjeta. Cada búsqueda web es 1 crédito y además suma una petición a Gemini. Igual que con Gemini, cada estudiante debe usar **su propia clave**.
> - **Tus secretos:** las claves (Gemini y Tavily) y la contraseña van solo en `.env`, que **nunca** se sube a git.
> - **Tope de tamaño:** hasta 100 tareas, 100 notas y 20 preferencias; cada mensaje, hasta 1000 caracteres.

---

## Despliegue gratis en PythonAnywhere, paso a paso

Reemplaza `TU_USUARIO` por tu nombre de usuario de PythonAnywhere. (Datos verificados el 19 de noviembre de 2026; si un botón cambió de nombre, consulta <https://help.pythonanywhere.com/>).

1. **Crea la cuenta gratuita** (tipo *Beginner*) en <https://www.pythonanywhere.com>. Tu dirección será `TU_USUARIO.pythonanywhere.com`. No pide tarjeta.
2. **Consigue la clave de Gemini** (sección de arriba).
3. **Sube el código.** En *Consoles → Bash* clona tu repositorio (`git clone https://github.com/USUARIO/REPO.git chatbot_asistente`) **o** sube un `.zip` desde *Files* y descomprímelo con `unzip`. La carpeta debe quedar, por ejemplo, en `/home/TU_USUARIO/chatbot_asistente`.
4. **Crea el entorno virtual e instala** (en la consola Bash):
   ```bash
   cd ~/chatbot_asistente
   mkvirtualenv --python=/usr/bin/python3.12 chatbot
   pip install -r requirements.txt
   ```
   Usa una versión de Python 3.10 o superior que ofrezca PythonAnywhere (el ejemplo oficial usa `python3.13`).
5. **Crea el `.env`:**
   ```bash
   cp .env.example .env
   nano .env
   ```
   Pon tu clave de Gemini, una contraseña propia y una `SECRET_KEY` generada con `python -c "import secrets; print(secrets.token_hex(32))"`. Si quieres búsqueda web, agrega también tu `TAVILY_API_KEY`. (En `nano`: Ctrl+O guarda, Ctrl+X sale.)
6. **Crea la app web:** pestaña *Web* → *Add a new web app* → *Manual configuration* y elige la misma versión de Python del paso 4. En *Virtualenv* escribe `chatbot` (se completa como `/home/TU_USUARIO/.virtualenvs/chatbot`). En *Source code* y *Working directory* pon la carpeta del proyecto (`/home/TU_USUARIO/chatbot_asistente`).
7. **Edita el archivo WSGI** (el enlace aparece en la pestaña *Web*). Borra el contenido de ejemplo y deja solo:
   ```python
   import sys
   ruta = "/home/TU_USUARIO/chatbot_asistente"
   if ruta not in sys.path:
       sys.path.insert(0, ruta)
   from app import app as application
   ```
8. **Recarga:** botón verde *Reload*. Abre `https://TU_USUARIO.pythonanywhere.com`, entra con tu contraseña y prueba: «Me llamo Ana», «Apúntame comprar pan», «¿Qué tareas tengo?», «¿Va a llover mañana en Quito?», «¿Cuáles son las últimas noticias de Ecuador?».
9. **Si algo falla**, abre el *Error log* y el *Server log* de la pestaña *Web* (ver la tabla de problemas más abajo).
10. **Para actualizar el código:** en la consola Bash, `git pull`, y luego *Reload*.
11. **Renovación mensual (obligatoria en la cuenta gratuita):** la app web se desactiva si no se renueva. Una vez al mes entra a la pestaña *Web* y pulsa el botón **«Run until 1 month from today»** (o el texto vigente). Pon un recordatorio en tu calendario.

### Qué pasa en la cuenta gratuita

- Una sola app, en `TU_USUARIO.pythonanywhere.com`, con un solo proceso y 512 MiB de disco.
- Solo puedes llamar a los sitios de la lista de permitidos: <https://www.pythonanywhere.com/whitelist/>. `googleapis.com` está en esa lista, por eso Gemini funciona. Con `requests` el proxy se usa automáticamente.
- Las herramientas de internet usan `news.google.com`, `es.wikipedia.org`, `geocoding-api.open-meteo.com`, `api.open-meteo.com` y `api.tavily.com`. Según la lista publicada por PythonAnywhere, todos están permitidos, pero **no se probaron desde una cuenta gratuita real**: la primera vez, pruébalos desde una consola Bash (por ejemplo `python -c "import requests; print(requests.get('https://geocoding-api.open-meteo.com/v1/search?name=Quito').status_code)"` debe imprimir `200`).
- Sin tareas programadas ni MySQL en cuentas nuevas, sin WebSockets ni tareas en segundo plano. Por eso el asistente **no hace recordatorios con hora**.
- El código no usa `app.run()` al importarse (solo dentro de `if __name__ == "__main__":`), porque en PythonAnywhere lo rompería.

## Solución de problemas

| Síntoma | Causa y solución |
|---|---|
| `ModuleNotFoundError` en el *Error log* | La ruta del *Virtualenv* está mal o falta `pip install -r requirements.txt` en ese entorno |
| «Falta configurar: …» en la página de entrada | Falta algo en `.env` o el valor sigue siendo el de ejemplo. Edita `.env` y pulsa *Reload* |
| «No pude conectarme con Gemini» (y en el log aparece 403 o «Tunnel connection failed») | El sitio no está en la lista de permitidos de PythonAnywhere. Revisa la lista y usa `requests` (no otra librería) |
| «Se alcanzó el límite gratuito de Gemini» (429) | Se acabó la cuota gratuita por ahora. Espera un minuto o inténtalo mañana |
| «La clave de Gemini no es válida…» | Revisa `GEMINI_API_KEY` en `.env` (sin comillas ni espacios) |
| Todos los mensajes dan «Se alcanzó el límite gratuito de Gemini» (429) y tienes `BUSQUEDA_WEB=1` | La búsqueda de Google no existe en el plan gratuito. Pon `BUSQUEDA_WEB=0` en `.env` y recarga |
| «No se pudo consultar internet ahora» | Falló la red o el servicio (noticias, clima, Wikipedia o Tavily). Inténtalo de nuevo; si persiste en PythonAnywhere, revisa que el sitio esté en la lista de permitidos |
| «La clave de búsqueda web no es válida» | Revisa `TAVILY_API_KEY` en `.env` (empieza con `tvly-`, sin comillas ni espacios) o bórrala para usar Wikipedia |
| «Se agotó el límite de búsquedas web de este mes» | Se acabaron los 1.000 créditos de Tavily. Se reinician el día 1. Mientras tanto, noticias y clima siguen funcionando |
| «No encontré esa ciudad» | Escribe la ciudad con el país, por ejemplo «Cuenca Ecuador» |
| «No se encontró el modelo» (404) | Cambia `GEMINI_MODEL` en `.env` por un modelo vigente y recarga |
| «Contraseña incorrecta» | Revisa `APP_PASSWORD` en `.env`; tras cambiarlo, recarga la app |
| La página abre pero no avanza al entrar con `http://127.0.0.1` | Ejecuta con `python app.py` (desactiva la cookie `Secure` solo en local) |
| La dirección de tu app ya no responde o aparece como desactivada | Venció la renovación mensual: pulsa el botón de extender en la pestaña *Web* |

## Alternativas de hosting (solo una nota)

El código es Flask normal, así que se puede mover a otro lugar. Se eligió PythonAnywhere porque es gratis, no pide tarjeta, no se duerme, **conserva los archivos** (la memoria y las notas son JSON) y puede llamar a Gemini. Otros planes gratuitos (Render, Railway, Cloud Run, Vercel, etc.) borran el disco al reiniciar, piden tarjeta o no tienen plan gratuito vigente. Si usas uno con disco temporal, tendrías que guardar los datos en una base de datos externa. Estos planes cambian seguido: revísalos antes de decidir.
