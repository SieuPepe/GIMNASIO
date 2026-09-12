# 08 — Cuestionario de satisfacción (T-14 días)

Formulario de Google enlazado desde el correo `ENCUESTA_T14`. Objetivo doble:
ajustar el entrenamiento y conseguir que el usuario encadene otro ciclo.

Diseño: **13 preguntas, 2 minutos**. Más largo baja la tasa de respuesta de forma
brusca. Solo son obligatorias las preguntas 1, 4, 9 y 10.

## Bloque 1 — Sensación física

| # | Pregunta | Tipo | `Codigo_Pregunta` |
|---|---|---|---|
| 1 | ¿Cómo te sientes físicamente ahora mismo? | Escala 1-10 | `SENSACION` |
| 2 | Tu nivel de energía en el día a día, comparado con el inicio del programa | Peor / Igual / Mejor | `ENERGIA` |
| 3 | ¿Cómo estás descansando y durmiendo? | Escala 1-10 | `SUENO` |
| 4 | ¿Has tenido molestias o dolores durante el programa? | No / Leves / Sí + texto | `MOLESTIAS` |

La 4 es la más importante en términos de seguridad: detecta una lesión en curso
antes de que se convierta en un abandono. Una respuesta "Sí" genera una alerta
destacada en el panel de inicio.

## Bloque 2 — El programa

| # | Pregunta | Tipo | Código |
|---|---|---|---|
| 5 | ¿Qué es lo que **más** te ha gustado? | Lista de sesiones/ejercicios + texto libre | `GUSTA_MAS` |
| 6 | ¿Qué es lo que **menos** te ha gustado? | Lista + texto libre | `GUSTA_MENOS` |
| 7 | La dificultad general del programa ha sido | Demasiado fácil / Adecuada / Dura pero llevadera / Excesiva | `DIFICULTAD` |
| 8 | ¿Te han resultado claros los ejercicios y cómo ejecutarlos? | Escala 1-5 | `CLARIDAD` |

La 7 calibra directamente la progresión del ciclo siguiente y es una entrada
excelente para la IA.

## Bloque 3 — Adherencia

| # | Pregunta | Tipo | Código |
|---|---|---|---|
| 9 | Aproximadamente, ¿qué porcentaje de las sesiones has podido completar? | <25 % / 25-50 % / 50-75 % / >75 % | `ADHERENCIA` |
| 10 | Si te has saltado sesiones, ¿por qué? | Casillas múltiples: falta de tiempo · horario incompatible · falta de motivación · molestias o lesión · viajes o trabajo · el programa se me hacía aburrido · otros | `MOTIVO_FALTAS` |
| 11 | ¿Qué duración de sesión te encaja mejor? Y ¿qué días y franja horaria? | 30/45/60/75+ min + días + franja | `PREFERENCIA_HORARIA` |

Mientras no exista el registro de lo ejecutado, la 9 es la **única** medida de
adherencia que se tiene. Es la pregunta que casi nadie hace y la que más explica.
La 11 alimenta directamente `T_DISPONIBILIDAD`, que condiciona el próximo plan.

## Bloque 4 — Objetivo y ciclo siguiente

| # | Pregunta | Tipo | Código |
|---|---|---|---|
| 12 | Tu objetivo al empezar era *"{{objetivo}}"*. ¿Lo mantienes? | Lo mantengo / Lo cambio + texto | `OBJETIVO` |
| 13 | ¿Qué te gustaría trabajar o probar en el próximo ciclo? | Casillas múltiples: más fuerza · más resistencia · pérdida de grasa · movilidad y flexibilidad · trabajo de core · entrenar en casa · clases o grupo · nuevos ejercicios y variedad + texto libre | `PROXIMO_CICLO` |

La 12 va **prerrellenada con su objetivo literal** del sistema: da sensación de
trato individual y encadena con lo que viene.

La 13 convierte la encuesta en una conversación sobre el siguiente ciclo, en lugar
de un cierre. Es la pregunta con más valor comercial del formulario.

## Cierre

Texto final con la llamada a la acción, y la pregunta de cita según lo que se
decida en el documento 04:

| # | Pregunta | Tipo | Código |
|---|---|---|---|
| 14 | ¿Quieres que hablemos para preparar tu próximo ciclo? | Sí, llámame / Sí, por correo / Todavía no | `QUIERE_CITA` |
| 15 | Si quieres que te llame, indica dos franjas que te encajen | Texto libre | `FRANJAS_CITA` |

Una respuesta afirmativa en la 14 genera una alerta en el panel de inicio. Esto es
la opción 1 de la sección "Reserva de cita" del documento 04, pendiente de
validar.

## Descartado

- **NPS** ("del 0 al 10, ¿recomendarías el gimnasio?"). Era la pregunta 14 de la
  propuesta inicial. Se elimina por decisión del entrenador.

## Campos ocultos

| Campo | Contenido | Para qué |
|---|---|---|
| `ID_Usuario` | `USR-0042` | Vincular la respuesta a la persona sin pedirle que se identifique |
| `ID_Envio` | `ENV-0311` | Saber a qué correo responde, controlar recordatorios y medir la tasa de respuesta |

Se rellenan mediante la URL de respuesta prerrellenada de Google Forms, distinta
para cada usuario y generada por la aplicación.

## Aprovechamiento de las respuestas

| Respuesta | Destino |
|---|---|
| `MOLESTIAS` = Sí | Alerta en el panel + revisión de `T_SALUD` |
| `DIFICULTAD` | Ajuste de intensidad del siguiente ciclo, y al expediente de la IA |
| `ADHERENCIA` + `MOTIVO_FALTAS` | Decisión de rediseñar frecuencia o duración |
| `PREFERENCIA_HORARIA` | Actualiza `T_DISPONIBILIDAD` |
| `OBJETIVO` = Lo cambio | Nueva fila en `T_OBJETIVOS`, el anterior pasa a MODIFICADO |
| `PROXIMO_CICLO` | Entrada directa del expediente para generar el ciclo siguiente |
| `QUIERE_CITA` = Sí | Alerta en el panel |
| `GUSTA_MAS` / `GUSTA_MENOS` | Al expediente de la IA como texto |

El punto importante: las respuestas **no se quedan en un informe**. Vuelven al
sistema y modifican el siguiente plan. Eso es lo que hace que el ciclo se cierre.
