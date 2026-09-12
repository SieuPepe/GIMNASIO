# 05 — Valoración física

## Para qué sirve

Tres funciones a la vez:

1. **Entregable de valor al usuario**: un informe en PDF con su foto fija de
   partida. Es material de enganche de primer orden, sobre todo cuando se repite
   y se puede comparar.
2. **Entrada de la planificación**: sin valoración, cualquier programa es una
   suposición. Y sin valoración no hay 1RM, luego no hay cálculo de cargas.
3. **Materia prima para la IA**: datos numéricos y normalizados, que es lo que un
   modelo puede usar bien (frente a "el usuario está flojo de piernas").

## Cuándo se hace

- **INICIAL**: en el alta, obligatoria.
- **SEGUIMIENTO**: en cualquier momento, a criterio del entrenador. Lo natural es
  al final de cada mesociclo o cada 8-12 semanas.
- **FINAL_CICLO**: al cerrar una asignación, para el informe comparativo que se
  entrega junto a la propuesta del ciclo siguiente.

Alerta en el panel de inicio: usuarios cuya última valoración tiene más de N meses
(configurable, por defecto 4).

## Estructura: catálogo + baremos

La batería **no está en el código**. Está en dos hojas del Excel que el entrenador
edita a su gusto:

- `T_CAT_TESTS`: qué pruebas existen, en qué unidad, qué capacidad miden, si mejor
  es más alto o más bajo, y el protocolo escrito.
- `T_BAREMOS`: para cada prueba, sexo y rango de edad, los tramos de valor y la
  puntuación 0-100 y categoría que corresponden.

La aplicación solo aplica: mete el valor medido, busca el tramo del baremo según
sexo y edad del usuario, y devuelve puntuación y categoría. Añadir una prueba
nueva no requiere tocar el programa.

## Batería propuesta (a validar)

Propuesta de partida. Como entrenador, ajústala: quita lo que no vayas a medir y
añade lo que uses.

### Cribado previo (antes de cualquier esfuerzo)
| Prueba | Registro |
|---|---|
| PAR-Q+ (7 preguntas) | Sí/No cada una |
| Tensión arterial en reposo | mmHg |
| Frecuencia cardíaca en reposo | lpm |

> Cualquier "Sí" en el PAR-Q+ o una tensión por encima de 140/90 debe marcar
> `Requiere_Informe_Medico_SN` y **bloquear los test de esfuerzo máximo** hasta
> tener el visto bueno médico. La aplicación lo hará de forma explícita: avisa y
> pide confirmación por escrito para continuar.

### Composición corporal
Peso · Altura · IMC (calculado) · % grasa (pliegues o bioimpedancia) ·
Perímetros: cintura, cadera, abdomen, brazo relajado y contraído, muslo, pecho ·
Índice cintura-cadera (calculado) · Índice cintura-altura (calculado)

### Fuerza
| Prueba | Unidad | Observaciones |
|---|---|---|
| Dinamometría manual (handgrip) | kg | Rápida, segura, buen predictor general de salud |
| Sentadilla — test de repeticiones submáximas | kg × reps | → 1RM estimado |
| Press banca — test de repeticiones submáximas | kg × reps | → 1RM estimado |
| Flexiones máximas | reps | Alternativa sin material |
| Plancha frontal isométrica | segundos | Resistencia del core |
| Abdominales en 60 s | reps | |

### Potencia
| Prueba | Unidad |
|---|---|
| Salto vertical (CMJ / test de Sargent) | cm |
| Salto horizontal a pies juntos | cm |

### Resistencia cardiorrespiratoria
Elegir **una** según medios y perfil del usuario:
| Prueba | Unidad | Perfil |
|---|---|---|
| Test de Rockport (1 milla andando) | min + FC → VO2máx estimado | Principiantes, sedentarios, mayores |
| Test del escalón YMCA | FC de recuperación → VO2máx | Espacio reducido |
| Course Navette (20 m) | palieres → VO2máx | Jóvenes, deportistas |
| Test de Cooper (12 min) | metros → VO2máx | Corredores |

### Movilidad y equilibrio
| Prueba | Unidad |
|---|---|
| Sit & reach | cm |
| Sentadilla profunda con brazos arriba (*overhead squat*) | escala 0-3 |
| Movilidad de hombro (test de Apley / rascado) | cm de separación |
| Dorsiflexión de tobillo (rodilla a pared) | cm |
| Apoyo monopodal con ojos cerrados | segundos |

## El informe en PDF

Contenido propuesto:

1. **Portada**: nombre, fecha, datos básicos, logotipo.
2. **Resumen en una página**: gráfica de radar con las 5-6 capacidades
   (fuerza, potencia, resistencia, movilidad, equilibrio, composición corporal),
   cada una puntuada 0-100 a partir de los baremos. Es lo que el usuario mira
   y lo que recuerda.
3. **Detalle por prueba**: valor medido, categoría, y referencia normativa para su
   sexo y edad.
4. **Comparativa**, si hay valoración anterior: radar superpuesto (antes/ahora) y
   tabla de diferencias con flechas. **Esta es la página que vende el siguiente
   ciclo.**
5. **Puntos fuertes y áreas de mejora**: se derivan de las puntuaciones más altas
   y más bajas, con texto que el entrenador puede editar antes de generar el PDF.
6. **Conclusión y recomendación del entrenador**: texto libre.

> Nota: esto reintroduce por la puerta de atrás la funcionalidad de gráficas, que
> quedó fuera de la lista de prioridades. No es contradicción: el radar y la
> comparativa son parte del informe de valoración, no un módulo aparte de
> estadística. Las gráficas de evolución general (peso a lo largo del tiempo,
> etc.) siguen fuera de esta fase.

## Enlace con el 1RM

Los test de repeticiones submáximas escriben automáticamente en `T_1RM` con
`Origen = VALORACION`, aplicando la fórmula configurada. A partir de ahí, todo el
cálculo de cargas del documento 06 funciona solo.
