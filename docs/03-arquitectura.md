# 03 — Arquitectura

## Cambio de enfoque

El planteamiento inicial era una aplicación *dentro* de Excel (macros VBA).
Se descarta: Excel pasa a ser **solo el almacén de datos** y la aplicación es un
**ejecutable propio**.

Razones:

- La integración con **Ollama** (HTTP + JSON), **SMTP**, **Google Sheets** y la
  **generación de PDF** es incómoda y frágil en VBA, y natural en Python.
- El código queda en **ficheros de texto versionables en Git**. Con VBA dentro
  del `.xlsm` el historial de Git es un binario opaco y no se puede revisar.
- El entrenador puede tener el Excel abierto para mirar datos sin que eso rompa
  la aplicación (con las salvedades de la sección *Concurrencia*).
- Interfaz de verdad: árboles, pestañas, diálogos, tablas editables.

## Stack propuesto

| Capa | Tecnología | Motivo |
|---|---|---|
| Lenguaje | Python 3.12 | Ecosistema completo para todo lo que necesitamos |
| Interfaz | PySide6 (Qt oficial, licencia LGPL) | `QTreeWidget` resuelve el árbol de ciclos; formularios y tablas nativas |
| Acceso al Excel | openpyxl | Lectura/escritura de `.xlsx` sin necesitar Excel instalado |
| PDF | ReportLab + matplotlib | Informes con tablas y gráficas (radar de valoración, evolución) |
| Correo | `smtplib` + `ssl` (SMTP Gmail) | Sin dependencia de Outlook |
| Secretos | Fichero `.env` fuera del repositorio (`python-dotenv`) | Sencillo y suficiente para un PC de un solo usuario |
| IA | `requests` contra la API de Ollama; capa de proveedor intercambiable | Local por defecto, ampliable a proveedores en la nube |
| Google Forms | `gspread` + cuenta de servicio (o importación manual de CSV) | Lectura de la hoja de respuestas |
| Empaquetado | PyInstaller (modo carpeta) + instalador Inno Setup | `.exe` de doble clic |

> PySide6 frente a PyQt6: PySide6 es la distribución oficial de Qt y su licencia
> LGPL permite uso comercial sin abrir el código. PyQt6 es GPL. Por eso PySide6.

## Estructura de capas

```
gimnasio/
├── ui/            Ventanas y diálogos (PySide6). Nada de lógica de negocio aquí.
├── servicios/     Lógica: ciclos, cargas, valoración, correo, IA, informes.
├── datos/         Repositorios: la única parte que sabe que detrás hay un Excel.
├── modelos/       Dataclasses: Usuario, Ciclo, Sesion, Valoracion...
└── nucleo/        Configuración, log, copias de seguridad, utilidades de fecha.
```

Regla dura: **la interfaz nunca toca openpyxl**. Todo pasa por `datos/`. Si algún
día se cambiara el almacenamiento, solo se reescribe esa carpeta.

## El Excel como base de datos: reglas de juego

Un libro `datos_gimnasio.xlsx`, una hoja por tabla, primera fila de cabeceras con
nombres fijos, una fila por registro, primera columna siempre el ID.

Lo que el código garantiza y una base de datos daría gratis:

1. **IDs**: generados por la aplicación con prefijo y contador (`USR-0001`,
   `CIC-0042`). Nunca se reutilizan, aunque se borre el registro.
2. **Escritura atómica**: se escribe en un temporal y se reemplaza el original al
   final. Si el proceso muere a mitad, el libro anterior sigue intacto.
3. **Copia de seguridad**: antes de cada sesión de escritura se copia el libro a
   `backups/datos_gimnasio_AAAAMMDD_HHMMSS.xlsx`, conservando las últimas N
   (configurable, por defecto 30). **En un sistema sin base de datos esto no es
   opcional: es la única red de seguridad.**
4. **Integridad referencial**: comprobada en código al guardar (no se puede
   borrar un ejercicio usado en una sesión; se marca como inactivo).
5. **Validación de esquema al arrancar**: si faltan hojas o columnas, la
   aplicación avisa y ofrece crearlas, en lugar de fallar a mitad de uso.

### Concurrencia (el único riesgo real)

Si el entrenador tiene el libro abierto en Excel, Windows lo bloquea y openpyxl
no podrá guardar. Y si lo tiene abierto y guarda desde Excel después de que la
aplicación haya escrito, pierde los cambios de la aplicación.

Mitigación:

- La aplicación mantiene el libro **cerrado** entre operaciones: lee al arrancar,
  trabaja en memoria, escribe al confirmar cada cambio.
- Detecta el fichero de bloqueo de Excel (`~$datos_gimnasio.xlsx`) y avisa
  claramente: *"cierra el Excel antes de guardar"*, en vez de dar un error técnico.
- Comprueba la fecha de modificación del libro antes de escribir: si cambió por
  fuera desde la última lectura, avisa antes de sobrescribir.
- Recomendación de uso: para mirar datos, abrir una **copia**, no el original.

## Rendimiento

Con ~100 usuarios el volumen es pequeño (del orden de miles de filas en las
tablas mayores: detalle de sesiones y valoraciones). openpyxl carga el libro
completo en memoria en un par de segundos. No hay problema de escala en el
horizonte previsible; si algún día lo hubiera, la capa `datos/` lo absorbe.

## Configuración y secretos

Dos ficheros junto al ejecutable:

- **`config.toml`** — parámetros no sensibles:

```toml
[negocio]
nombre_comercial = "ZEU"
lema             = "Enjoy your process"
horario_sala     = "Lunes a sábado de 07:00 a 21:00 · Domingo de 07:00 a 14:00"

[datos]
libro   = "C:/ZEU/datos_gimnasio.xlsx"
backups = "C:/ZEU/backups"
copias_a_conservar = 30

[correo]
dias_aviso_previo = 14
modo_vacaciones   = false
caducidad_modo_vacaciones = ""
tope_envios_dia   = 20

[ia]
url_ollama = "http://localhost:11434"
modelo     = "qwen2.5:7b-instruct"
```
- **`.env`** — credenciales:

```ini
GMAIL_USUARIO=micuenta@gmail.com
GMAIL_APP_PASSWORD=xxxxxxxxxxxxxxxx
GOOGLE_SERVICE_ACCOUNT_JSON=C:\GIMNASIO\secretos\cuenta-servicio.json
OPENAI_API_KEY=            # opcional, si se usa proveedor en la nube
```

### Sobre guardar credenciales en `.env`

Funciona y es lo más sencillo, que es la razón para elegirlo. La contrapartida a
tener presente: **el fichero está en texto plano**, así que cualquiera con acceso
a ese PC, o a una copia de seguridad de ese PC, puede leer la contraseña.

En este caso el riesgo es asumible y se acota así:

1. Se usa una **contraseña de aplicación** de Gmail, no la contraseña de la
   cuenta. Es específica para esta aplicación, no da acceso a la cuenta de Google
   y **se puede revocar en cualquier momento** desde la configuración de Google si
   algo va mal.
2. El `.env` está en `.gitignore`: **nunca** llega al repositorio.
3. Se excluye de las copias de seguridad que salgan del PC (y de cualquier copia
   en la nube).
4. El JSON de la cuenta de servicio de Google se guarda en una subcarpeta propia,
   también excluida.

Si en algún momento se quiere endurecer, mover los secretos al Almacén de
credenciales de Windows (`keyring`) es un cambio de unas pocas líneas, porque
todo el acceso a credenciales pasa por una única función. Se deja preparado así,
pero **arrancamos con `.env`**.

## Hardware de destino y qué implica

> **El equipo de destino final será otro, todavía sin definir.** Lo que sigue
> describe el equipo de desarrollo y prueba disponible hoy, y sirve como
> **suelo**: la aplicación está diseñada para funcionar bien en él, de modo que en
> cualquier máquina igual o mejor funcionará igual o mejor. Nada del diseño
> depende del hardware salvo la velocidad del módulo de IA. Ver
> [10 — Decisiones abiertas](10-decisiones-abiertas.md).

**Equipo de referencia actual: Intel Core i5-1235U · 16 GB de RAM · sin GPU
dedicada.**

Para la aplicación en sí (interfaz, Excel, PDF, correo) es más que suficiente: no
hay nada exigente en ese trabajo.

Para la IA local sí tiene consecuencias, y condicionan el diseño del módulo:

- Es un procesador portátil de 10 núcleos (2 de rendimiento + 8 de eficiencia) sin
  aceleración gráfica aprovechable. La inferencia va **por CPU**.
- Con 16 GB de RAM el techo práctico son modelos de **7-8 mil millones de
  parámetros cuantizados a 4 bits** (ocupan del orden de 4-5 GB). Un modelo de
  14B cuantizado (≈ 9 GB) entra por los pelos pero deja el equipo muy justo.
- Velocidad esperable: **del orden de 4 a 8 palabras por segundo** con un modelo
  de 7-8B. Un texto corto (el cuerpo de un correo, 200-300 palabras) sale en
  **menos de un minuto**. Una planificación completa en JSON, que son varios
  miles de palabras, tardaría **muchos minutos** en una sola tirada.

Consecuencia de diseño, desarrollada en el [documento 07](07-modulo-ia.md):
la generación **no se hace de una sola vez**. Se trocea (esqueleto → cada
mesociclo → cada sesión), lo que la vuelve viable en este equipo y además más
fiable. Y las tareas cortas (redactar correos, resumir feedback) van en local sin
problema.
