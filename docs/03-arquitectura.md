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
| Secretos | `keyring` (Almacén de credenciales de Windows) | La contraseña de aplicación de Gmail **no** se guarda en el Excel |
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

- `config.toml` junto al ejecutable: ruta del libro, carpeta de copias, remitente
  de correo, servidor SMTP, URL de Ollama, modelo por defecto, rutas de PDF.
- La **contraseña de aplicación de Gmail** y la clave de cuenta de servicio de
  Google se guardan en el Almacén de credenciales de Windows vía `keyring`.
  Nunca en el Excel ni en el `config.toml`, y nunca en el repositorio.
