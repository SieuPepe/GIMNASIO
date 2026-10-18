# 12 — Identidad de marca

## Nombre

**Kevin Ruiz Valdenegro** — *Licenciado en Ciencias del Deporte y la Actividad
Física*

El nombre comercial es el del propio entrenador, así que en los correos y en los
informes la firma y la marca son la misma cosa. El lema **«Movimiento es vida»** es lo que aparece bajo el nombre en la cabecera
de los correos y en el pie de los PDF. La titulación va en el propio logotipo.

Ambos se configuran en `config.toml`, sección `[negocio]`, de modo que cambiarlos
no exige tocar código.

## Logotipo

El símbolo es una **K** de la que arranca un corredor en trazo continuo, con el
nombre debajo y la titulación como línea de base.

| Fichero | Para qué |
|---|---|
| `assets/marca/kevin-logo.png` | Logotipo completo en su color, **fondo transparente**. Cabecera de los PDF |
| `assets/marca/kevin-logo-blanco.png` | El mismo, en blanco. Barra lateral de la aplicación |
| `assets/marca/kevin-logo-fondo-blanco.png` | Versión con fondo blanco sólido, de respaldo |
| `assets/marca/kevin-iso.png` | Solo el símbolo (K + corredor), para espacios estrechos |
| `assets/marca/kevin-iso-blanco.png` | El símbolo en blanco |
| `assets/marca/kevin.ico` | Icono de Windows, de 16 a 256 px. Ventana y acceso directo |

Las versiones en blanco y el icono **se generan a partir del original**; si algún
día cambia el logotipo, hay que regenerarlas.

> Por qué hacen falta dos colores: el logotipo es marino y la barra lateral de la
> aplicación también. Puesto ahí en su color, no se vería. Por eso la interfaz
> usa `ruta_logo_claro()` y los documentos `ruta_logo()`.

## Paleta

Tomada del logotipo. El marino es el color exacto del dibujo; el resto son pasos
del mismo tono, elegidos para que cada uso llegue al contraste que necesita sobre
blanco.

| Uso | Color | Hex | Contraste sobre blanco |
|---|---|---|---|
| Marino: logotipo, barra lateral, títulos | Azul marino | `#06305A` | 13,3 : 1 |
| Principal: botones, cabeceras de tabla | Azul | `#15568F` | 7,6 : 1 |
| Intermedio: estados y serie anterior del radar | Azul medio | `#2E6FA8` | 5,3 : 1 |
| Bandas y recuadros destacados | Azul claro | `#D7E3EF` | — |
| Fondo neutro | Gris claro | `#EEF1F4` | — |
| Texto | Gris oscuro | `#2B2B2B` | 14,5 : 1 |

**Colores funcionales**, para el radar de la valoración y las alertas del panel.
Se reservan para indicar estado y no se usan nunca como color de marca:

| Significado | Hex |
|---|---|
| Bueno · por encima de la media | `#5B9279` |
| Medio · en la media | `#C9A227` |
| Bajo · atención | `#C1663F` |
| Alerta · bloqueo (dolor, cribado, consentimiento) | `#A33B3B` |

### El radar comparativo

Las dos series del informe de valoración son **el mismo tono en dos pasos**,
porque no son dos categorías distintas sino el mismo dato en dos momentos:
la anterior en azul medio `#2E6FA8` con trazo discontinuo, la actual en marino
`#06305A` con trazo continuo. Ambas pasan el 3:1 sobre papel blanco, llevan el
valor escrito en cada eje y la tabla al lado, de modo que distinguirlas nunca
depende solo del color.

## Dónde aparece la marca

| Soporte | Qué se ve |
|---|---|
| Barra lateral | Logotipo en blanco sobre marino |
| Ventana y acceso directo | `kevin.ico` |
| Informe de valoración | Logotipo en la cabecera; nombre y titulación en el pie de cada página |
| Hoja de entrenamiento | Igual |
| Correos | Cabecera marina con el nombre y la titulación debajo; botones en azul |

## Contacto

En el pie de los informes y en la firma de los correos:

> Kevin Ruiz Valdenegro · 644 300 765 · movimientoesvida.krv@gmail.com

Se configura en `config.toml`, clave `contacto` de `[negocio]`. El correo desde
el que sale todo es **movimientoesvida.krv@gmail.com**.
