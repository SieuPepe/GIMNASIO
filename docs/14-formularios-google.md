# 14 — Los formularios de Google, paso a paso

Los formularios **no los crea ni los guarda el programa**: viven en tu Google
Drive, son tuyos y los respondes tú de nada. Lo único que guarda el programa es
la **dirección** de cada uno, para poder meterla en el botón del correo ya
rellenada con la identificación de cada persona.

Consecuencia práctica: si cambias de cuenta de Google, los formularios antiguos
se quedan en la cuenta antigua. Hay dos salidas, y la segunda suele salir más a
cuenta:

1. **Compartirlos** desde la cuenta antigua con la nueva (o transferir la
   propiedad). Conserva las respuestas ya recibidas, pero las nuevas siguen
   cayendo en el Drive viejo.
2. **Rehacerlos** en la cuenta nueva. Son tres formularios y se montan en media
   hora. Todo queda en el mismo sitio y no dependes de la cuenta anterior.

## El camino rápido: que te los cree un guion

En `herramientas/formularios_google.gs` hay un guion que **crea los tres
formularios en tu cuenta**, con todas sus preguntas, y escribe las direcciones
ya listas para pegar. Evita la media hora de montarlos a mano y, sobre todo,
evita equivocarse en el enunciado de una pregunta.

1. Entra en <https://script.google.com> **con la cuenta donde quieres los
   formularios**. La cuenta importa: quedan en su Drive.
2. «Nuevo proyecto».
3. Borra lo que haya y pega el contenido de `formularios_google.gs`.
4. Arriba, elige la función **`crearFormularios`** y pulsa **Ejecutar**.
5. La primera vez Google pide permiso. Es tu propio guion creando tus propios
   formularios, en tu cuenta: hay que aceptarlo.
6. Al terminar, abajo aparece el **«Registro de ejecución»** con las tres
   direcciones y el enlace para editar cada formulario.

Las direcciones salen ya con los marcadores puestos. Se pegan tal cual en el
programa y no hay que tocarlas.

Si prefieres hacerlos a mano, o quieres entender qué crea el guion, sigue
leyendo.

## Cuántos hacen falta

Tres formularios, cuatro casillas en el programa:

| Formulario | Para qué | Dónde se pega su dirección |
|---|---|---|
| **Consentimiento** | Autorización para tratar sus datos y escribirle | `CONSENTIMIENTO` |
| **Encuesta de fin de ciclo** | Satisfacción y renovación, a 14 días del final | `ENCUESTA_T14` **y** `RECORDATORIO` |
| **Check-in de mitad** | Una sola pregunta, a mitad del ciclo | `CHECKIN_MITAD` |

El recordatorio es un segundo aviso de **la misma** encuesta, así que lleva la
misma dirección. No hay que hacer un formulario aparte.

## Las dos preguntas que llevan los tres

Esto es lo que permite que una respuesta se enganche con la persona correcta sin
pedirle que se identifique. En **los tres** formularios, al principio:

| Título de la pregunta | Tipo |
|---|---|
| `ID_Usuario` | Respuesta corta |
| `ID_Envio` | Respuesta corta |

Ponlas como respuesta corta y **no las marques como obligatorias**. Las rellena
el programa por la dirección del enlace; la persona ni las ve si no baja a
mirarlas. Si quieres, en la descripción pon «No tocar, lo rellena el programa».

> El programa las reconoce por el título. Valen también `id usuario`,
> `IDUsuario` o `usuario_id`: no mira mayúsculas ni acentos.

## Formulario 1 — Consentimiento

Una sola pregunta de verdad, más las dos de identificación:

| Pregunta | Tipo | Opciones |
|---|---|---|
| ¿Autorizas que tratemos tus datos y te escribamos? | Varias opciones | **Sí, autorizo** / No |

En la descripción del formulario, el texto de qué datos se guardan y para qué.

La palabra importante es **«autorizas»** o «autorización» o «consentimiento»:
por ahí lo reconoce el programa. Y la respuesta tiene que **empezar** por «Sí»,
«Autorizo» o «Acepto».

## Formulario 2 — Encuesta de fin de ciclo

Es el grande: **14 preguntas, dos minutos**. El contenido completo, pregunta por
pregunta y con el porqué de cada una, está en
[08 — Cuestionario](08-cuestionario.md). Solo son obligatorias la 1, la 4, la 9
y la 10.

El resumen, para montarlo del tirón:

| # | Pregunta | Tipo |
|---|---|---|
| 1 | ¿Cómo te sientes físicamente ahora mismo? | Escala 1-10 |
| 2 | Tu nivel de energía comparado con el inicio | Peor / Igual / Mejor |
| 3 | ¿Cómo estás descansando y durmiendo? | Escala 1-10 |
| 4 | ¿Has tenido molestias o dolores durante el programa? | No / Leves / Sí + texto |
| 5 | ¿Qué es lo que más te ha gustado? | Párrafo |
| 6 | ¿Qué es lo que menos te ha gustado? | Párrafo |
| 7 | La dificultad general del programa ha sido | Demasiado fácil / Adecuada / Dura pero llevadera / Excesiva |
| 8 | ¿Te han resultado claros los ejercicios? | Escala 1-5 |
| 9 | ¿Qué porcentaje de las sesiones has podido completar? | <25 % / 25-50 % / 50-75 % / >75 % |
| 10 | Si te has saltado sesiones, ¿por qué? | Casillas |
| 11 | ¿Qué duración de sesión te encaja mejor? ¿Qué días y franja? | Varias |
| 12 | ¿Mantienes tu objetivo? | Lo mantengo / Lo cambio + texto |
| 13 | ¿Qué te gustaría trabajar en el próximo ciclo? | Casillas |
| 14 | ¿Quieres que hablemos para preparar tu próximo ciclo? | Sí / Todavía no |

## Formulario 3 — Check-in de mitad

| Pregunta | Tipo |
|---|---|
| ¿Cómo te sientes físicamente ahora mismo? | Escala 1-10 |
| ¿Has tenido molestias o dolores? | No / Leves / Sí + texto |
| ¿Quieres que hablemos? | Sí / Todavía no |

Corto a propósito: a mitad de ciclo nadie rellena catorce preguntas.

## Cuidado con cómo redactas las preguntas

El programa no entiende de números de pregunta: **reconoce cada una por las
palabras de su enunciado**. Si reescribes una pregunta y le quitas su palabra
clave, esa respuesta llegará pero el programa no sabrá qué hacer con ella.

Las palabras que busca, por respuesta:

| Respuesta | Basta con que el enunciado contenga |
|---|---|
| Sensación | «cómo te sientes», «físicamente», «sensación» |
| Energía | «energía» |
| Sueño | «descansando», «duermes», «sueño» |
| **Molestias** | «molestias», «dolores» |
| Lo que más gustó | «más te ha gustado» |
| Lo que menos gustó | «menos te ha gustado» |
| Dificultad | «dificultad» |
| Claridad | «claros», «claridad» |
| Adherencia | «porcentaje de las sesiones», «sesiones has podido» |
| Motivo de las faltas | «saltado sesiones», «motivo» |
| Preferencia horaria | «duración de sesión», «franja», «días te encaja» |
| **Cita** | «hablemos», «quieres que te llame», «cita con» |
| Próximo ciclo | «te gustaría trabajar», «te gustaría probar» |
| Objetivo | «objetivo» |
| Consentimiento | «autorizo», «autorización», «consentimiento» |

Las dos en negrita son las que encienden avisos en el panel de inicio, así que
son las que más conviene no tocar.

De las respuestas se mira **la primera palabra**: así «Sí», «Sí, quiero» y «Sí,
llámame» valen igual, y «Todavía no» o «Ninguna» se entienden como un no.

## Sacar el enlace prerrellenado

Este es el paso que no se encuentra a la primera. El enlace normal de un
formulario **no sirve**: hace falta el de «respuesta prerrellenada», que es el
que lleva los huecos para la identificación.

1. Abre el formulario **en modo edición**.
2. Arriba a la derecha, el botón de **tres puntos verticales** (⋮).
3. **«Obtener enlace prerrellenado»**. Se abre el formulario como si fueras a
   responderlo.
4. Escribe cualquier cosa en `ID_Usuario` y en `ID_Envio` —por ejemplo `AAA` y
   `BBB`—. **No rellenes nada más.**
5. Abajo, botón **«Obtener vínculo»**, y luego **«Copiar vínculo»**.

Te queda una dirección parecida a esta:

```
https://docs.google.com/forms/d/e/1FAIp.../viewform?usp=pp_url&entry.123456=AAA&entry.789012=BBB
```

**Y aquí hay un paso que no se puede saltar.** Antes de pegarla, cambia los dos
valores de prueba por los marcadores que el programa sabe sustituir:

- donde pusiste `AAA` (el de `ID_Usuario`) → `{{id_usuario}}`
- donde pusiste `BBB` (el de `ID_Envio`) → `{{id_envio}}`

Queda así:

```
...viewform?usp=pp_url&entry.123456={{id_usuario}}&entry.789012={{id_envio}}
```

Esos marcadores son los huecos: el programa pone ahí la identificación de cada
persona al enviar cada correo. Sin ellos, todo el mundo recibiría el mismo
enlace vacío y las respuestas llegarían sin saber de quién son.

No pasa nada si se te olvida: el programa comprueba cada correo antes de
enviarlo y, si el enlace no lleva el identificador, no lo manda y lo dice en la
bandeja. Pero es más cómodo dejarlo bien a la primera —o usar el guion de
arriba, que ya los pone.

## Dónde se pega en el programa

Dos sitios, el que te pille mejor:

- **La primera vez**: el asistente de puesta en marcha las pide en su tercera
  pantalla.
- **Después**: Correo → «Plantillas de correo…», eliges la plantilla y rellenas
  «URL del formulario».

Mientras una plantilla no tenga su dirección, el panel de inicio lo avisa en
rojo: «La plantilla X no tiene formulario». No es un fallo, es el recordatorio.

## Traer las respuestas de vuelta

Las respuestas se quedan en Google hasta que las traes:

1. En el formulario, pestaña **«Respuestas»** → icono de hoja de cálculo verde
   → **«Descargar respuestas (.csv)»**.
2. En el programa, Correo → **«Importar respuestas…»** y eliges ese fichero.

El programa engancha cada respuesta con su persona por `ID_Usuario`, y si
alguien ha declarado molestias o ha pedido cita, aparece como aviso en el panel
de inicio.

Las preguntas que llevan detalle ocupan dos columnas en el CSV —«¿has tenido
molestias?» y «cuéntame dónde»— y el programa las junta en una sola respuesta,
así que el aviso del panel sale con la explicación dentro.

Se pueden importar las mismas respuestas dos veces sin miedo: las repetidas se
reconocen y no se duplican.
