# 12 — Identidad de marca

## Nombre y lema

- **Nombre comercial:** ZEU
- **Lema:** *ENJOY YOUR PROCESS*

El lema no es decorativo para este proyecto: "disfruta tu proceso" es exactamente
lo que hacen el informe de valoración comparativo y el cuestionario de renovación
— poner el foco en el recorrido, no solo en el resultado. Merece aparecer en el
pie de los informes y en la firma de los correos.

## Aplicación

| Soporte | Uso de la marca |
|---|---|
| Ventana de la aplicación | Logo en la barra superior y en la pantalla de inicio. Título de ventana: *ZEU — Gestión de entrenamiento* |
| Informe de valoración (PDF) | Logo en la portada; logo pequeño y lema en el pie de cada página |
| Programa de entrenamiento (PDF) | Cabecera con logo, nombre del usuario y fase del ciclo |
| Correos | Logo en la cabecera del HTML y firma con lema y datos de contacto |
| Icono del ejecutable | Versión cuadrada del logo (`.ico`) |

## Paleta

Tomada del logotipo. **Los valores son aproximados**: en cuanto haya un fichero
vectorial o los hex exactos, se sustituyen aquí y se propagan solos, porque todos
los generadores (PDF, HTML de correo, interfaz) leen los colores de un único
módulo.

| Uso | Color | Hex aproximado |
|---|---|---|
| Principal (azul del logotipo) | Azul acero | `#4A7FA5` |
| Principal oscuro (títulos, texto destacado) | Azul profundo | `#356283` |
| Claro (fondos de tabla, bandas) | Azul muy claro | `#D9E4EC` |
| Fondo neutro | Gris claro del logotipo | `#E2E2E2` |
| Texto | Gris oscuro | `#333333` |

**Colores funcionales** para el radar de valoración y las alertas, elegidos para
convivir con el azul de marca sin competir con él:

| Significado | Hex |
|---|---|
| Bueno / por encima de la media | `#5B9279` |
| Medio / en la media | `#C9A227` |
| Bajo / atención | `#C1663F` |
| Alerta / bloqueo (dolor, cribado) | `#A33B3B` |

En el radar comparativo: la valoración anterior en gris (`#9AA5AD`) y la actual en
el azul de marca. La mejora se ve sola, sin necesidad de explicarla.

## Ficheros

Se esperan en `assets/marca/`:

| Fichero | Para qué | Estado |
|---|---|---|
| `zeu-logo.png` | Logo completo con lema, fondo transparente, ≥ 1200 px de ancho | **Pendiente** |
| `zeu-logo.svg` | Versión vectorial, si existe | Deseable |
| `zeu-iso.png` | Solo el recuadro "ZEU!", para cabeceras estrechas e icono | Deseable |
| `zeu.ico` | Icono del ejecutable | Se genera a partir del anterior |

El logo se ha recibido por conversación, pero **no está en el repositorio**: hay
que guardar el fichero en esa carpeta.

Nota práctica: el logo recibido tiene fondo gris sólido. Para las cabeceras de los
PDF y de los correos hace falta la versión con **fondo transparente**, o el gris
recortará un rectángulo sobre el papel blanco. Si no hay original disponible, se
puede recortar el fondo, pero saldrá mejor desde el fichero de diseño.

## Datos de contacto

Pendientes: dirección, teléfono, correo de contacto y web, si la hay. Aparecen en
el pie de los informes y en la firma de los correos.

## Horario de sala

Configurado en `config.toml` (`horario_sala`), y usado en el correo de
confirmación de cita:

> **Lunes a sábado de 07:00 a 21:00 · Domingo de 07:00 a 14:00**
