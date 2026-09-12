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

### Nota realista sobre el modelo local

Generar una periodización completa en JSON válido y coherente es una tarea
exigente. Un modelo local pequeño (del orden de 7-8 mil millones de parámetros)
tiende a producir JSON malformado, a inventarse ejercicios que no están en el
catálogo y a perder la coherencia entre mesociclos. Modelos locales de mayor
tamaño lo hacen bastante mejor, pero requieren una GPU con suficiente memoria.

Por eso: la arquitectura soporta ambos, la validación (más abajo) es estricta, y
**hay que probar con el hardware real** antes de decidir. Es una de las preguntas
abiertas del documento 10.

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
