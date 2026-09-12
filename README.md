# ZEU — Gestión de usuarios y planificación del entrenamiento

*Enjoy your process*

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

**Fases 0, 1 y 2 implementadas:** cimientos, usuarios y catálogo de ejercicios.

| Fase | Contenido | Estado |
|---|---|---|
| 0 | Libro de datos, capa de acceso, copias de seguridad, configuración | Hecha |
| 1 | Usuarios, objetivos, salud y cribado PAR-Q+, disponibilidad | Hecha |
| 2 | Catálogo de ejercicios, con 127 de partida | Hecha |
| 3 | Valoración física e informe en PDF | Pendiente |
| 4 | Planificación, cargas y PDF del programa | Pendiente |
| 5 | Correo, formularios y cola de revisión | Pendiente |
| 6 | Panel de alertas completo | Pendiente |
| 7 | Módulo de IA | Pendiente |

## Puesta en marcha

Requiere **Python 3.11 o superior** en Windows.

```powershell
# 1. Dependencias (mejor dentro de un entorno virtual)
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt

# 2. Configuración: copiar las plantillas y ajustarlas
Copy-Item config.ejemplo.toml config.toml; Copy-Item .env.ejemplo .env

# 3. Crear el libro de datos vacío (29 hojas + hoja de esquema)
python herramientas/crear_libro.py

# 4. Cargar el catálogo inicial de ejercicios
python herramientas/importar_ejercicios.py

# 5. Arrancar
python -m zeu
```

Las pruebas se lanzan con `python -m unittest discover -s pruebas`.

## Estructura del código

```
zeu/
├── nucleo/     Configuración, credenciales, registro y fechas
├── datos/      Esquema del libro, acceso a Excel y repositorio
├── servicios/  Lógica de negocio
├── ui/         Ventanas (PySide6). No toca openpyxl nunca
herramientas/   Utilidades de línea de comandos
datos_iniciales/  Catálogo de ejercicios de partida (CSV)
pruebas/        Pruebas automáticas
```

Regla que no se rompe: **la interfaz nunca accede al Excel directamente**. Todo
pasa por `datos/`, de modo que cambiar el almacenamiento sería reescribir una
sola carpeta.

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
| [11 — Anexo de baremos](docs/11-anexo-baremos.md) | Tablas de referencia por sexo y edad de cada prueba |
| [12 — Identidad de marca](docs/12-marca.md) | Nombre, lema, paleta y ficheros del logotipo |
| [13 — Catálogo de ejercicios](docs/13-catalogo-ejercicios.md) | Vocabularios, formato del CSV y lo que da el catálogo |
