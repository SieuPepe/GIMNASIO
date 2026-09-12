# 07 — Módulo de IA

Tres funciones pedidas:

1. Generar planes de entrenamiento a partir de las características del usuario.
2. Bucle iterativo: la IA propone → el entrenador evalúa y da feedback → la IA
   corrige → hasta que el entrenador está satisfecho → se genera el ciclo.
3. Una ventana para **enseñar** a la IA los criterios propios del entrenador.

## Capa de proveedor intercambiable

Una interfaz única (`ProveedorIA`) con implementaciones:

- **Ollama local** (`http://localhost:11434`) — opción por defecto. Los datos de
  salud **no salen del PC**, que para datos de categoría especial del RGPD es el
  argumento decisivo.
- **Proveedor en la nube** (API compatible, configurable) — opción para cuando la
  calidad del modelo local no baste.

El proveedor y el modelo se eligen en la configuración y se registran en
`T_IA_LOG` en cada interacción, para saber qué generó qué.

### Seudonimización

Sea local o en la nube, el expediente que se manda al modelo **no lleva nombre,
apellidos, correo ni teléfono**. Va como `USR-0042`, con sexo, edad, métricas,
objetivos, limitaciones y disponibilidad. La correspondencia con la persona se
queda en el Excel. No cuesta nada hacerlo así y elimina el problema de raíz.

### El hardware manda: i5-1235U, 16 GB, sin GPU

La inferencia va por CPU. Con 16 GB de RAM el techo práctico son modelos de 7-8
mil millones de parámetros cuantizados a 4 bits, a razón de unas **4-8 palabras
por segundo**.

Eso lleva a clasificar las tareas de IA en tres grupos, y a tratar cada una de
forma distinta:

| Tarea | Salida | Tiempo local | Decisión |
|---|---|---|---|
| Redactar el cuerpo de un correo | 200-300 palabras | < 1 min | **Local, sin discusión** |
| Resumir el feedback de una encuesta | 50-100 palabras | segundos | **Local** |
| Redactar los "puntos fuertes / áreas de mejora" de un informe | 150 palabras | < 1 min | **Local** |
| Sugerir un ejercicio alternativo | 20 palabras | segundos | **Local** |
| **Generar un macrociclo completo en JSON** | 3.000-6.000 palabras | 15-40 min de una tirada | **Troceada** (ver abajo) |

Y a dos decisiones de diseño importantes:

### Decisión 1: la generación se trocea

Pedir una periodización de 24 semanas en una sola respuesta JSON es lo peor que se
puede hacer con un modelo pequeño: tarda mucho, se le degrada la coherencia a
mitad y un solo error de sintaxis tira la respuesta entera a la basura.

En su lugar, se generará **en pasos encadenados**, cada uno con una salida corta:

```
Paso 1  Esqueleto del macrociclo: nombre, objetivo y la lista de mesociclos
        con su enfoque y duración.            (~200 palabras, ~30 s)
        -> El entrenador lo revisa y lo aprueba ANTES de seguir.

Paso 2  Para cada mesociclo: sus microciclos, con enfoque y duración.
        (~150 palabras cada uno)

Paso 3  Para cada microciclo distinto: sus sesiones y las líneas de ejercicio,
        con el catálogo filtrado en el contexto.   (~400 palabras cada una)

Paso 4  La aplicación monta el árbol completo y lo valida.
```

Ventajas, más allá de la velocidad:

- **Se puede parar en el paso 1.** Si el esqueleto no convence, se corrige ahí y
  no se han gastado 30 minutos generando sesiones de una estructura equivocada.
- Cada respuesta es pequeña, luego la probabilidad de JSON válido es mucho mayor,
  y un reintento cuesta segundos y no minutos.
- Los microciclos repetidos no se regeneran: se clonan.
- Hay **barra de progreso real** ("mesociclo 2 de 4, sesión 1 de 3"), el proceso
  corre en segundo plano, se puede cancelar, y se puede retomar donde se quedó.

Con esto, una planificación completa vendrá a tardar del orden de **15 a 30
minutos** en este equipo. Es asumible para algo que se hace una vez por usuario y
por ciclo, y que se puede dejar corriendo mientras se atiende la sala.

### Decisión 2: primero un generador por reglas, y la IA encima

Antes de la IA se construye un **generador determinista**: a partir del objetivo,
el nivel, los días disponibles, el material y la valoración física, monta una
planificación correcta aplicando plantillas y las reglas de `T_REGLAS`. Sin
modelo de lenguaje, en milisegundos, y siempre válida.

Sobre esa base, la IA tiene dos modos de trabajo:

| Modo | Qué hace | Coste |
|---|---|---|
| **Refinar** (recomendado por defecto) | Parte del plan generado por reglas y lo ajusta, sustituye ejercicios, adapta el enfoque y redacta las notas | Salidas cortas, rápido y muy fiable |
| **Generar** | Crea la planificación desde cero por los pasos de arriba | Más creativo, más lento, más validación |

Esto es lo que hace que el módulo sea útil **desde el primer día** y no dependa de
que el modelo local dé la talla. Si un día se cambia a un equipo con GPU, o a un
proveedor en la nube, el modo "Generar" mejora y el resto sigue igual.

### Formato estructurado obligado

Ollama admite exigir que la respuesta cumpla un **esquema JSON** concreto
(parámetro `format` con el esquema). Con esto, incluso un modelo de 7B devuelve
JSON sintácticamente válido casi siempre. Se usará en todas las llamadas que
esperen datos, sin excepción.

### Modelos a probar en este equipo

Candidatos razonables para 16 GB sin GPU, cuantización Q4:
`qwen2.5:7b-instruct` · `llama3.1:8b-instruct` · `mistral:7b-instruct`.

No se puede decidir sobre el papel: hay que **medir en el equipo real** velocidad
y calidad con los mismos casos de prueba. La aplicación llevará una pantalla de
diagnóstico que mide palabras por segundo y porcentaje de respuestas válidas por
modelo, para poder comparar con datos y no por impresión.

### Si hiciera falta más

Queda como opción documentada, no como plan: un proveedor en la nube para el modo
"Generar", con el expediente seudonimizado. El volumen es pequeño (unas pocas
generaciones a la semana con 100 usuarios), así que el coste sería bajo. Se decide
más adelante, con los datos de la pantalla de diagnóstico encima de la mesa.

## Generación: el expediente y el contrato de salida

### Entrada — expediente del usuario
La aplicación monta un JSON con: edad, sexo, composición corporal, resultados de
la última valoración con sus puntuaciones, objetivos con prioridad, limitaciones y
lesiones, disponibilidad (días, minutos, material, lugar), historial de ciclos
anteriores y su feedback, 1RM conocidos, y la estructura pedida (duración total,
número de mesociclos).

### Contexto — lo que el entrenador ha enseñado
Se inyectan las **reglas duras** (siempre, todas) y los **artículos de
conocimiento** relevantes, seleccionados por coincidencia de etiquetas con el
perfil del usuario (objetivo, nivel, limitaciones).

### Catálogo cerrado
Se le pasa la lista de `ID_Ejercicio` permitidos, filtrada por el material que el
usuario tiene y sin los contraindicados por sus lesiones. **La IA solo puede
elegir de esa lista.** Esto por sí solo elimina la mayor parte de los problemas.

### Salida — JSON con esquema fijo
Se exige una estructura equivalente al modelo de datos:

```json
{
  "macrociclo": {
    "nombre": "...", "objetivo": "...", "duracion_sem": 24,
    "mesociclos": [
      { "nombre": "...", "enfoque": "ACUMULACION", "duracion_sem": 6,
        "microciclos": [
          { "nombre": "...", "duracion_sem": 3,
            "sesiones": [
              { "num_dia": 1, "tipo": "FUERZA",
                "lineas": [
                  { "bloque": "PRINCIPAL", "id_ejercicio": "EJ-0012",
                    "series": 4, "reps": "5", "modo_carga": "PCT1RM",
                    "valor_carga": 80, "descanso_seg": 180,
                    "progresion": "LINEAL:+2.5" }
                ]}]}]}]},
  "justificacion": "por qué esta estructura para este usuario"
}
```

El campo `justificacion` no es decorativo: es lo que el entrenador lee para decidir
si la propuesta tiene sentido, y lo que revela cuándo el modelo está improvisando.

## Validación antes de mostrar nada

Ninguna respuesta de la IA llega al Excel sin pasar por el validador:

| Comprobación | Acción si falla |
|---|---|
| JSON válido y conforme al esquema | Reintento automático con el error como mensaje |
| Todos los `id_ejercicio` existen y están activos | Se marca la línea y se sugiere sustituto del mismo patrón |
| Ningún ejercicio contraindicado para sus lesiones | **Error bloqueante** |
| Material requerido ⊆ material disponible | Se marca la línea |
| Sesiones por semana ≤ días disponibles | Error bloqueante |
| Duración estimada de sesión ≤ minutos disponibles | Aviso |
| Suma de duraciones de hijos = duración del padre | Aviso |
| Volumen semanal por grupo muscular dentro de rango | Aviso |
| Cumplimiento de las reglas duras de `T_REGLAS` | Según la regla: aviso o bloqueo |

Los avisos se muestran como una lista al lado de la propuesta. Es información útil
para el feedback de la siguiente iteración.

## Bucle iterativo

```
┌─ Ventana "Generar ciclo con IA" ───────────────────────────────┐
│ Usuario: [Ana G. — USR-0042  ▾]     Modelo: [ollama/... ▾]     │
│ Estructura pedida: 24 semanas · 4 mesociclos · 3 días/semana   │
│                                          [Generar propuesta]   │
├────────────────────────────┬───────────────────────────────────┤
│ ÁRBOL DE LA PROPUESTA      │ JUSTIFICACIÓN DE LA IA            │
│ (editable a mano)          │ ...                               │
│                            ├───────────────────────────────────┤
│                            │ AVISOS DEL VALIDADOR (3)          │
│                            │ · Volumen de pectoral bajo (6)    │
├────────────────────────────┴───────────────────────────────────┤
│ Tu feedback: "sube el volumen de empuje horizontal y quita     │
│ el peso muerto convencional en el primer mesociclo"            │
│          [Reintentar con feedback]   [Aceptar y guardar]       │
└────────────────────────────────────────────────────────────────┘
```

- Cada iteración conserva el historial de la conversación, así que el modelo ve
  sus intentos anteriores y el feedback recibido.
- Todas las iteraciones se registran en `T_IA_LOG`, con el feedback textual.
- El árbol es **editable a mano** en cualquier momento: la IA da el borrador, el
  entrenador tiene siempre la última palabra.
- "Aceptar y guardar" escribe en `T_CICLOS` / `T_SESIONES` / `T_SESION_DET` con
  `Origen = IA`, y ya es un ciclo normal: se puede clonar, usar como plantilla y
  asignar.

## Ventana "Enseñar a la IA"

Dos tipos de contenido, en dos pestañas:

### Reglas (`T_REGLAS`) — restricciones
Formato condición → acción, con tipo **DURA** (el validador bloquea) o **BLANDA**
(se sugiere al modelo y se avisa si no se cumple):

| Condición | Acción | Tipo |
|---|---|---|
| Lesión lumbar en el historial | Prohibir peso muerto convencional y *good morning* | DURA |
| Nivel de usuario = principiante | Máximo 3 sesiones semanales el primer mesociclo | DURA |
| Objetivo = hipertrofia | Volumen semanal de 10-20 series por grupo | BLANDA |
| Cualquier mesociclo de más de 4 semanas | Incluir una semana de descarga | BLANDA |
| Más de 3 días/semana | No dos sesiones de fuerza máxima consecutivas | BLANDA |

### Conocimiento (`T_CONOCIMIENTO`) — criterio
Artículos de texto libre con categoría y etiquetas: preferencias metodológicas,
progresiones que funcionan con su población, criterios de selección de ejercicios,
maneras de explicar las cosas. Se seleccionan por etiquetas y se inyectan en el
contexto.

### Aprendizaje a partir de las correcciones (la parte interesante)

Cada vez que el entrenador da feedback en el bucle iterativo, la aplicación
propone convertir ese feedback en conocimiento permanente:

> *Has corregido 3 veces que el volumen de empuje horizontal era bajo.
> ¿Guardar como artículo de conocimiento para futuras generaciones?*
> `[Guardar]  [Editar antes de guardar]  [No]`

Se guarda con `Origen = APRENDIZAJE`. Así la IA deja de repetir el mismo error y
el sistema mejora con el uso, que es exactamente lo que se pedía con "ir enseñando
a la IA". El entrenador siempre confirma: nada entra en la base de conocimiento
de forma automática.

## Ampliación futura: selección por similitud semántica

Con muchos artículos de conocimiento, la selección por etiquetas se queda corta.
Ollama sirve también modelos de *embeddings*, con lo que se podría calcular la
similitud entre el perfil del usuario y cada artículo, y seleccionar los más
próximos. Los vectores caben en una hoja del Excel. No es necesario al principio:
con etiquetas se llega bastante lejos.

---

## Redacción de correos con IA

Tarea corta, perfectamente viable en local, y la que más se va a usar.

**Entrada:** la plantilla del correo, su `Instruccion_IA`, los datos del usuario
(nombre, objetivo literal, fase del plan, tiempo que lleva, resultados de su
última valoración si los hay) y **la nota personal del entrenador**, cuando la
haya escrito.

**Salida:** el cuerpo del correo en HTML sencillo, con la nota del entrenador
integrada de forma natural en el texto — no pegada como un bloque aparte.

**Flujo normal:**

```
Disparador (T-14 días) -> la IA redacta -> pantalla de revisión:
   cuerpo montado + campo para tu impresión personal
   -> [Reescribir con la IA]  (para incorporar tu nota al texto)
   -> vista previa tal cual la recibirá el usuario
   -> [Aprobar y enviar]
```

Restricciones que se le imponen al modelo:

- No inventar datos. Solo puede usar lo que se le pasa. Si no hay datos de
  progreso, no los menciona.
- No prometer nada (descuentos, plazos, resultados).
- No dar consejo médico.
- Tono y extensión fijados en la instrucción de la plantilla.
- El enlace del formulario lo pone la aplicación, no el modelo.

Y una comprobación automática antes de mostrar el borrador: que el enlace del
formulario esté presente y sea el correcto, que el nombre del usuario sea el suyo,
y que no aparezca ningún marcador `{{...}}` sin sustituir. Son los tres errores
que dejarían en evidencia un correo automático.

El cuerpo redactado por la IA se guarda en `T_COLA_MAIL.Cuerpo_IA` junto al final
editado. Comparar ambos a lo largo del tiempo es la forma de ir afinando la
instrucción de cada plantilla.
