---
name: grill-me
description: Entrevista al usuario a fondo sobre un plan, una decisión o una idea hasta llegar a un entendimiento compartido. Úsala cuando el usuario quiera poner a prueba sus ideas, pida que lo "interroguen" o que lo "pongan a prueba", o use frases como "hazme preguntas", "grill me" o "pregúntame a fondo".
---

# Skill: grill-me

Entrevista al usuario sin descanso hasta llegar a un entendimiento compartido. Piensa el tema como un **árbol de decisiones**: cada decisión se ramifica en las decisiones que dependen de ella.

Recorre el árbol en **rondas**. La **frontera** es el conjunto de decisiones cuyos requisitos ya están resueltos: las preguntas que puedes hacer _ahora_ sin adivinar respuestas que todavía no conoces. Haz toda la frontera en una sola ronda: numera cada pregunta y da tu respuesta recomendada. Luego espera las respuestas del usuario antes de la siguiente ronda.

Presenta cada ronda así:

```
❓ **P1** - **<título de la pregunta>**: <cuerpo de la pregunta; puede tener varios párrafos e incluir opciones>

➡️ <tu respuesta recomendada>

---

❓ **P2** - **<título de la pregunta>**: <cuerpo de la pregunta; puede tener varios párrafos e incluir opciones>

➡️ <tu respuesta recomendada>
```

Redacta cada pregunta para que un "sí" acepte tu respuesta recomendada.

Cada respuesta del usuario reorganiza el árbol: las decisiones resueltas empujan la frontera hacia afuera y desbloquean preguntas que dependían de ellas. Recalcula la frontera y haz la siguiente ronda. Una pregunta que depende de otra que aún está abierta en esta ronda pertenece a una ronda _posterior_, no a esta.

Encontrar **hechos** es tu trabajo, nunca el del usuario. Cuando una pregunta de la frontera necesite un dato del entorno (archivos, herramientas, código, etc.), busca tú la información: revisa los archivos del proyecto o usa un subagente con contexto nuevo si la tarea es larga. No bloquees la conversación por ello: mientras la búsqueda corre, solo las preguntas que dependen de ella esperan; haz el resto de la frontera ya. Las **decisiones** son del usuario: preséntaselas y espera su respuesta.

La sesión termina cuando la frontera está vacía: cada rama del árbol fue visitada y no queda nada asumido en silencio. No actúes sobre el plan hasta que el usuario confirme que llegaron a un entendimiento compartido.

## Cómo usarla en este repositorio

- Si el usuario planea un proyecto del curso (por ejemplo, un juego, un chatbot o un script), pregúntale por los objetivos, el público, las dependencias y cómo lo probará antes de escribir código.
- Mantén las preguntas claras y en español sencillo, pensando en que son estudiantes.
- No ejecutes cambios en el código mientras el entendimiento no esté confirmado.
