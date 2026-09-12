# GIMNASIO — Gestión de usuarios y planificación del entrenamiento

Aplicación de escritorio para Windows que gestiona los usuarios de un gimnasio,
su valoración física, y la planificación del entrenamiento en ciclos
(macrociclo → mesociclo → microciclo), con generación asistida por IA y
comunicación automatizada por correo con los usuarios.

## Principio de diseño

- **Excel es la base de datos.** No hay motor de base de datos. Todos los datos
  viven en un libro `.xlsx` con una hoja por tabla, legible y editable a mano.
- **La aplicación es un ejecutable independiente.** No corre dentro de Excel:
  es un `.exe` que lee y escribe el libro.
- **Un solo operador, un solo PC.** Sin servidor, sin usuarios concurrentes.

## Estado

Fase de diseño. No hay código todavía. La documentación de `docs/` es el
contrato a validar antes de programar.

## Documentación

| Documento | Contenido |
|---|---|
| [01 — Visión y alcance](docs/01-vision-alcance.md) | Qué hace y qué no hace la aplicación |
| [02 — Modelo de datos](docs/02-modelo-datos.md) | Las hojas del Excel y sus campos |
| [03 — Arquitectura](docs/03-arquitectura.md) | Stack técnico, capas, empaquetado |
| [04 — Comunicaciones por correo](docs/04-comunicaciones-email.md) | Cadencia, cola de revisión, consentimiento, Google Forms |
| [05 — Valoración física](docs/05-valoracion-fisica.md) | Batería de test, baremos, informe al usuario |
| [06 — Cargas y progresión (1RM)](docs/06-cargas-progresion.md) | Cálculo automático de kilos y progresiones |
| [07 — Módulo de IA](docs/07-modulo-ia.md) | Ollama, generación iterativa, base de conocimiento |
| [08 — Cuestionario de satisfacción](docs/08-cuestionario.md) | Preguntas definitivas del formulario T-14 |
| [09 — Hoja de ruta](docs/09-roadmap.md) | Fases de construcción |
| [10 — Decisiones abiertas](docs/10-decisiones-abiertas.md) | Lo que falta por decidir |
