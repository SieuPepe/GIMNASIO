# Kevin Ruiz Valdenegro — Gestión de usuarios y planificación del entrenamiento

*Licenciado en Ciencias del Deporte y la Actividad Física*

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

**Fases 0 a 6 implementadas:** cimientos, usuarios, ejercicios, valoración
física, planificación, comunicación por correo y panel de alertas.

| Fase | Contenido | Estado |
|---|---|---|
| 0 | Libro de datos, capa de acceso, copias de seguridad, configuración | Hecha |
| 1 | Usuarios, objetivos, salud y cribado PAR-Q+, disponibilidad | Hecha |
| 2 | Catálogo de ejercicios, con 127 de partida | Hecha |
| 3 | Valoración física, protocolos, baremos e informe en PDF | Hecha |
| 4 | Planificación en árbol, cargas, asignaciones y PDF | Hecha |
| 5 | Correo, formularios, cola de revisión y modo vacaciones | Hecha |
| 6 | Panel de alertas con navegación a cada ficha | Hecha |
| — | Manual interactivo, ayuda por ventana y recorridos guiados | Hecha |
| 7 | Módulo de IA | Pendiente |
| 8 | Instalador .exe con dos modos y asistente de configuración | Hecha |
| 8.5 | Datos de demostración | Hecha |
| 8.7 | Copias de seguridad fuera del equipo | Pendiente |
| 9 | App para el móvil | Pendiente |

## Instalación

Para el ordenador de destino: **`KevinRuizValdenegro_Instalador.exe`**, un solo
fichero. No necesita que allí haya Python ni nada instalado.

Si en lugar del instalador tienes la carpeta del proyecto:

```powershell
powershell -ExecutionPolicy Bypass -File instalar.ps1
```

En los dos casos pregunta qué quieres hacer:

| Modo | Qué hace con tus datos |
|---|---|
| **Instalación desde cero** | Rehace el libro con un usuario de ejemplo que tiene de todo. Copia de seguridad y confirmación antes. |
| **Actualizar la versión** | No toca el libro ni la configuración. Copia de seguridad antes, y añade las columnas nuevas si las hay. |

En los dos modos: comprueba Python, prepara el entorno virtual, instala las
dependencias y crea el acceso directo del Escritorio con el icono. Se niega a
seguir si el libro está abierto en Excel.

La primera vez, el programa abre un **asistente** que pregunta la cuenta de
correo —y la prueba contra Gmail antes de guardarla—, las direcciones de los
formularios de Google y los datos de la marca. No hace falta nada más.

Instalado, **el programa y los datos van separados**: el programa donde van los
programas, y el Excel, la configuración, las copias y los PDF en
`Documentos\Kevin Ruiz Valdenegro`. El desinstalador no toca esa carpeta.

### Fabricar el instalador

```powershell
powershell -ExecutionPolicy Bypass -File construir.ps1
```

Pasa las pruebas, empaqueta el programa con PyInstaller (`krv.spec`) y monta el
`.exe` con Inno Setup (`instalador/krv.iss`). Hace falta [Inno Setup 6.3 o
superior](https://jrsoftware.org/isdl.php) en la máquina donde se construye.

## Ayuda dentro del programa

No hace falta leer esta documentación para usarlo:

- **Botón «?»** arriba a la derecha de cada ventana, o la tecla **F1**: explica
  todos los controles de esa ventana, uno por uno. Hay página para las 22
  ventanas del programa.
- **«Ayuda y manual»**, último botón de la barra lateral: el manual completo,
  con buscador. Desde cada página se puede abrir la ventana de la que habla, y
  se puede volcar entero a un HTML para imprimirlo o guardarlo en PDF.
- **Seis recorridos guiados** que oscurecen la ventana, señalan el control del
  que hablan y lo explican: darse una vuelta, dar de alta a alguien, valorar,
  montar un programa, asignarlo y el aviso de los 14 días.

## Puesta en marcha

Requiere **Python 3.11 o superior** en Windows.

```powershell
# 1. Dependencias (mejor dentro de un entorno virtual)
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt

# 2. Configuración: copiar las plantillas y ajustarlas
Copy-Item config.ejemplo.toml config.toml; Copy-Item .env.ejemplo .env

# 3. Crear el libro de datos vacío (29 hojas + hoja de esquema)
python herramientas/crear_libro.py

# 4. Cargar todos los datos iniciales: ejercicios, valoración, plantillas y correos
python herramientas/preparar_datos.py

# 5. Crear el acceso directo del Escritorio (icono, sin ventana negra)
powershell -ExecutionPolicy Bypass -File herramientas\crear_acceso_directo.ps1

# 6. Arrancar
python -m krv
```

### Arrancar con un icono

El paso 5 deja en el Escritorio un acceso directo **Kevin Ruiz Valdenegro** con
el logotipo. Arranca la aplicación con doble clic y **sin ventana de consola
detrás**, porque usa `pythonw.exe` en lugar de `python.exe`.

La contrapartida de no tener consola es que, si algo falla antes de que se abra
la ventana, no se ve el error. Para eso está **`ARRANCAR.bat`** en la carpeta
del proyecto: hace lo mismo pero dejando la ventana abierta con el mensaje. Los
errores quedan además en `logs/krv.log`.

Las pruebas se lanzan con `python -m unittest discover -s pruebas`.

### Al actualizar a una versión nueva

Si el libro de datos se creó con una versión anterior, le pueden faltar hojas o
columnas. **No hay que rehacer nada ni se pierde ningún dato:** la aplicación lo
detecta al arrancar y ofrece actualizarlo, haciendo copia de seguridad antes.
También se puede hacer a mano:

```powershell
python herramientas/migrar_libro.py --revisar   # dice qué falta, sin tocar nada
python herramientas/migrar_libro.py             # lo aplica
```

Las herramientas de línea de comandos lo hacen por su cuenta, así que
`preparar_datos.py` funciona igual sobre un libro antiguo.

### Si vienes de la versión anterior

El fichero de datos se llamaba `datos_zeu.xlsx` y ahora el nombre por defecto es
`datos_krv.xlsx`. Para renombrarlo sin perder nada, con la aplicación cerrada:

```powershell
cd $HOME\GIMNASIO; Rename-Item datos_zeu.xlsx datos_krv.xlsx; (Get-Content config.toml) -replace 'datos_zeu\.xlsx','datos_krv.xlsx' | Set-Content config.toml
```

También puedes dejarlo como está: la ruta sale de `config.toml`, así que la
aplicación funciona igual con cualquier nombre.

## Estructura del código

```
krv/
├── nucleo/     Configuración, credenciales, registro y fechas
├── datos/      Esquema del libro, acceso a Excel y repositorio
├── servicios/  Lógica de negocio
├── ui/         Ventanas (PySide6). No toca openpyxl nunca
│   ├── ayuda_contenido.py   Todo el texto del manual y de la ayuda
│   ├── ayuda.py             Panel «?» de cada ventana
│   ├── vista_manual.py      El manual navegable
│   └── recorrido.py         Motor y guiones de los recorridos guiados
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
| [14 — Formularios de Google](docs/14-formularios-google.md) | Cómo montarlos y de dónde sale el enlace prerrellenado |
