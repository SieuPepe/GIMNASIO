# 11 — Anexo: baremos y tablas de referencia

Tablas de referencia por **sexo y edad** para cada prueba de la valoración física,
para tener orden de magnitud al interpretar un resultado.

> ## Aviso importante sobre estas tablas
>
> Son **valores orientativos de partida**, recopilados de referencias de uso
> habitual en valoración de la condición física. No son un estándar clínico y
> deben ser **revisados y ajustados por el entrenador** antes de usarse con
> usuarios reales.
>
> Razones concretas: los valores dependen del protocolo exacto de medición (un
> *sit & reach* con caja de 26 cm no da lo mismo que uno medido desde la punta de
> los pies), de la población de referencia (una tabla estadounidense de los años
> 90 no describe bien a un usuario español de hoy), y algunas pruebas
> **simplemente no tienen datos normativos publicados**.
>
> La columna **Solidez** indica cuánto fiarse de cada tabla:
>
> | Solidez | Significado |
> |---|---|
> | **Alta** | Criterio clínico o institucional ampliamente aceptado (OMS, sociedades médicas) |
> | **Media** | Tabla normativa publicada y de uso extendido, pero dependiente de protocolo y población |
> | **Baja** | Valores de uso común sin respaldo normativo sólido. Usar como referencia interna |
> | **Sin baremo** | No hay datos publicados. Se usa como medida **intraindividual**: el usuario se compara consigo mismo |
>
> Todos estos valores viven en la hoja `T_BAREMOS` del Excel y se editan sin tocar
> el programa. **Están pensados para que los cambies.**

---

## 1. Cribado previo

### 1.1 PAR-Q+ — las 7 preguntas

| # | Pregunta |
|---|---|
| 1 | ¿Le ha dicho alguna vez un médico que tiene una afección cardíaca **o** tensión arterial alta? |
| 2 | ¿Siente dolor en el pecho en reposo, durante sus actividades diarias **o** al hacer actividad física? |
| 3 | ¿Pierde el equilibrio por mareos **o** ha perdido la consciencia en los últimos 12 meses? *(Responda NO si el mareo se debió a hiperventilación durante ejercicio intenso.)* |
| 4 | ¿Le han diagnosticado alguna otra enfermedad crónica, distinta de cardiopatía o tensión alta? |
| 5 | ¿Toma actualmente medicación prescrita para una enfermedad crónica? |
| 6 | ¿Tiene, o ha tenido en los últimos 12 meses, un problema óseo, articular o de tejidos blandos que pudiera empeorar al aumentar su actividad física? *(Responda NO si el problema es pasado y hoy no le limita.)* |
| 7 | ¿Le ha dicho un médico que solo debe hacer actividad física bajo supervisión médica? |

**Interpretación:** todas "No" → apto para iniciar actividad progresiva.
Cualquier "Sí" → completar el cuestionario ampliado del PAR-Q+ sobre esa
condición y, según el caso, requerir informe médico antes de pruebas de esfuerzo.

*Solidez: alta (instrumento de cribado estandarizado).*

### 1.2 Tensión arterial en reposo

Clasificación europea (adultos, mmHg). No depende de la edad.

| Categoría | Sistólica | | Diastólica |
|---|---|---|---|
| Óptima | < 120 | y | < 80 |
| Normal | 120 – 129 | y/o | 80 – 84 |
| Normal alta | 130 – 139 | y/o | 85 – 89 |
| **Hipertensión grado 1** | 140 – 159 | y/o | 90 – 99 |
| **Hipertensión grado 2** | 160 – 179 | y/o | 100 – 109 |
| **Hipertensión grado 3** | ≥ 180 | y/o | ≥ 110 |

**Criterio de la aplicación:** a partir de grado 1 → `Requiere_Informe_Medico_SN`
y bloqueo de pruebas de esfuerzo máximo. A partir de grado 2 → no iniciar
actividad sin valoración médica.

> La clasificación estadounidense (ACC/AHA) es más estricta: llama *elevada* a
> 120-129 y *hipertensión estadio 1* a 130-139 / 80-89. Si se prefiere ese
> criterio, se cambia en `T_BAREMOS`.

*Solidez: alta.*

### 1.3 Frecuencia cardíaca en reposo

Medida sentado, tras 5 minutos de reposo. Adultos, lpm.

| Categoría | Hombres | Mujeres |
|---|---|---|
| Muy buena (perfil entrenado) | < 60 | < 65 |
| Buena | 60 – 69 | 65 – 74 |
| Media | 70 – 79 | 75 – 82 |
| Alta | 80 – 89 | 83 – 90 |
| Muy alta | ≥ 90 | ≥ 91 |

Fuera de rango clínico: < 50 (bradicardia) o > 100 (taquicardia) en reposo →
mención en el informe y derivación si es persistente.

*Solidez: media (los rangos 60-100 lpm son criterio clínico aceptado; la
graduación interna es orientativa).*

---

## 2. Composición corporal

### 2.1 IMC (kg/m²)

| Categoría | IMC |
|---|---|
| Bajo peso | < 18,5 |
| Normopeso | 18,5 – 24,9 |
| Sobrepeso | 25,0 – 29,9 |
| Obesidad grado I | 30,0 – 34,9 |
| Obesidad grado II | 35,0 – 39,9 |
| Obesidad grado III | ≥ 40,0 |

**Advertencia que debe salir en el informe:** el IMC no distingue masa muscular
de masa grasa. En un usuario con mucha masa muscular dará "sobrepeso" sin que
signifique nada. Se acompaña siempre de % de grasa y perímetro de cintura.

*Solidez: alta (criterio OMS).*

### 2.2 Porcentaje de grasa corporal

| Categoría | Hombres | Mujeres |
|---|---|---|
| Grasa esencial | 2 – 5 % | 10 – 13 % |
| Deportista | 6 – 13 % | 14 – 20 % |
| *Fitness* | 14 – 17 % | 21 – 24 % |
| Aceptable | 18 – 24 % | 25 – 31 % |
| Obesidad | ≥ 25 % | ≥ 32 % |

Los valores se desplazan al alza con la edad: por encima de 60 años, entre 2 y 4
puntos más en cada categoría se considera normal.

*Solidez: media. Depende mucho del método: pliegues, bioimpedancia y DEXA no dan
lo mismo. **Anotar siempre el método** y comparar solo mediciones hechas igual.*

### 2.3 Perímetro de cintura — riesgo cardiometabólico

| Riesgo | Hombres | Mujeres |
|---|---|---|
| Bajo | < 94 cm | < 80 cm |
| **Aumentado** | 94 – 101 cm | 80 – 87 cm |
| **Alto** | ≥ 102 cm | ≥ 88 cm |

*Solidez: alta (criterio OMS para población europea).*

### 2.4 Índices derivados

| Índice | Cálculo | Umbral de riesgo |
|---|---|---|
| Cintura / cadera | cintura ÷ cadera | ≥ 0,90 hombres · ≥ 0,85 mujeres |
| Cintura / altura | cintura ÷ altura | ≥ 0,50 (ambos sexos, todas las edades) |

El índice cintura/altura es el más simple y uno de los mejores predictores: la
regla práctica es *"la cintura debe medir menos de la mitad de la altura"*.

*Solidez: alta.*

---

## 3. Fuerza y control motor

### 3.1 Dinamometría manual (*handgrip*)

Media de tres intentos con la mano dominante, codo a 90°, en kg.

| Edad | Hombres: bajo · medio · alto | Mujeres: bajo · medio · alto |
|---|---|---|
| 20 – 29 | < 41 · 41 – 54 · > 54 | < 24 · 24 – 34 · > 34 |
| 30 – 39 | < 42 · 42 – 56 · > 56 | < 25 · 25 – 35 · > 35 |
| 40 – 49 | < 40 · 40 – 54 · > 54 | < 24 · 24 – 34 · > 34 |
| 50 – 59 | < 36 · 36 – 50 · > 50 | < 21 · 21 – 31 · > 31 |
| 60 – 69 | < 31 · 31 – 45 · > 45 | < 18 · 18 – 28 · > 28 |
| ≥ 70 | < 26 · 26 – 39 · > 39 | < 15 · 15 – 24 · > 24 |

**Punto de corte clínico (dinapenia), cualquier edad:**
**< 27 kg en hombres · < 16 kg en mujeres.** Por debajo, se marca en el informe y
se prioriza el trabajo de fuerza; en mayores de 65 es criterio de cribado de
sarcopenia.

**Asimetría:** una diferencia superior al 10-15 % entre mano dominante y no
dominante merece mención.

*Solidez: el punto de corte clínico, alta. La tabla por décadas, media.*

### 3.2 Pruebas de técnica (escala 0-3)

Sin tabla numérica: se puntúa con la escala 0-3 del documento 05 y se registran
los criterios observados.

**Sentadilla profunda con brazos arriba** — criterios a observar:

| # | Criterio (marcar si aparece) |
|---|---|
| 1 | No alcanza la profundidad (muslo paralelo al suelo) |
| 2 | Los talones se despegan del suelo |
| 3 | Las rodillas colapsan hacia dentro (valgo) |
| 4 | Inclinación excesiva del tronco hacia delante |
| 5 | Pérdida de la curvatura lumbar en el fondo (retroversión) |
| 6 | Los brazos caen hacia delante (falta de movilidad de hombro/dorsal) |
| 7 | Desplazamiento lateral: carga más una pierna |
| 8 | **Dolor** en cualquier punto del recorrido → puntuación 0 |

**Zancada (*lunge*)** — se valora cada lado por separado:

| # | Criterio |
|---|---|
| 1 | Pérdida de equilibrio, necesita apoyo |
| 2 | Valgo de la rodilla adelantada |
| 3 | Caída de la pelvis del lado libre |
| 4 | Tronco inclinado o rotado |
| 5 | La rodilla de atrás no baja lo suficiente / rango incompleto |
| 6 | Diferencia clara entre un lado y el otro |
| 7 | **Dolor** → 0 |

*Solidez: no aplicable (valoración cualitativa estructurada).*

### 3.3 *Step down* (descenso lateral)

Desde un escalón de 20 cm, descenso controlado con una pierna hasta tocar el
suelo con el talón contrario, 5 repeticiones por lado. Se valora cada lado.

| # | Criterio |
|---|---|
| 1 | Usa los brazos para equilibrarse |
| 2 | Inclina o rota el tronco |
| 3 | Caída de la pelvis del lado libre (Trendelenburg) |
| 4 | La rodilla se desplaza hacia dentro respecto al pie |
| 5 | El pie de apoyo se mueve o pierde estabilidad |
| 6 | Descenso brusco, no controlado |
| 7 | **Dolor** → 0 |

Referencia de interpretación habitual: 0-1 criterios = buena calidad ·
2-3 = moderada · ≥ 4 = deficiente. La **asimetría entre lados** es el dato más
útil de esta prueba.

*Solidez: media (prueba de uso extendido en cribado de control lumbopélvico).*

### 3.4 Dominada (*pull up*) y suspensión

Repeticiones máximas, agarre prono, rango completo. Solo en protocolos de
rendimiento y adulto activo.

| Categoría | Hombres | Mujeres |
|---|---|---|
| Insuficiente | 0 | 0 |
| Bajo | 1 – 3 | — |
| Medio | 4 – 8 | 1 – 2 |
| Alto | 9 – 13 | 3 – 5 |
| Muy alto | > 13 | > 5 |

Como la mayoría de usuarios marcará 0, se recomienda usar en su lugar la
**suspensión isométrica (*dead hang*)**, que discrimina mucho mejor:

| Categoría | Hombres | Mujeres |
|---|---|---|
| Bajo | < 20 s | < 15 s |
| Medio | 20 – 45 s | 15 – 35 s |
| Alto | 46 – 75 s | 36 – 60 s |
| Muy alto | > 75 s | > 60 s |

*Solidez: baja. Valores de uso común en el sector, sin tabla normativa
poblacional. Útiles como referencia interna y para seguimiento.*

### 3.5 Resistencia isométrica del tronco

Cuatro pruebas cronometradas hasta la pérdida de la posición. **Su valor
principal no son los tiempos absolutos, sino las relaciones entre ellos**, que
detectan desequilibrios.

**Tiempos de referencia en adultos jóvenes sanos (segundos, orden de magnitud):**

| Prueba | Hombres | Mujeres | Solidez |
|---|---|---|---|
| Extensores lumbares (**Sorensen**) | ≈ 145 s | ≈ 190 s | Media |
| Plancha lateral (*side plank*), cada lado | ≈ 95 s | ≈ 75 s | Media |
| Flexores del tronco | ≈ 135 s | ≈ 135 s | Media |
| Plancha frontal (sobre codos) | 60 – 120 s aceptable · > 120 s bueno | 45 – 90 s aceptable · > 90 s bueno | Baja |
| Plancha invertida (*reverse plank*) | — | — | **Sin baremo** |

Los tiempos descienden de forma marcada con la edad: a partir de los 50 años es
razonable esperar entre un 30 y un 50 % menos que estos valores.

**Relaciones — la parte que de verdad interpreta la prueba:**

| Relación | Valor esperado | Qué indica si se sale |
|---|---|---|
| Flexores ÷ Sorensen | < 1,0 | > 1,0 → extensores lumbares débiles en relación a los flexores. Factor de riesgo de dolor lumbar |
| Plancha lateral ÷ Sorensen | < 0,75 | > 0,75 → desequilibrio del plano frontal |
| Lateral derecha ÷ lateral izquierda | 0,95 – 1,05 | Fuera de rango → **asimetría relevante**, indicación de trabajo unilateral |

La asimetría derecha-izquierda es el hallazgo más frecuente y el más accionable.

**Plancha invertida:** no hay datos normativos publicados. Se registra igualmente
porque como medida **intraindividual** (comparación con uno mismo entre
valoraciones) es perfectamente válida. En el informe aparece sin categoría, solo
con la evolución.

*Solidez: media para los tiempos de las tres primeras y para las relaciones;
baja para la plancha frontal; sin baremo la invertida.*

### 3.6 *Sit-to-Stand* / *Chair Stand Test*

Levantarse y sentarse de una silla sin apoyar los brazos (cruzados sobre el
pecho), con la espalda recta y llegando a la extensión completa de cadera.

Cubre justo el hueco que deja haber sacado los test de 1RM de la valoración
inicial: da un **número de fuerza de tren inferior** sin carga externa, sin
riesgo y aplicable a cualquier perfil, del principiante al mayor de 80.

Dos variantes, ambas en el catálogo:

**a) 30 segundos — repeticiones completas en medio minuto.**
Es la variante del *Senior Fitness Test*. Rangos considerados **normales** (dentro
de estos valores, la persona está en la media de su edad):

| Edad | Hombres | Mujeres |
|---|---|---|
| 60 – 64 | 14 – 19 | 12 – 17 |
| 65 – 69 | 12 – 18 | 11 – 16 |
| 70 – 74 | 12 – 17 | 10 – 15 |
| 75 – 79 | 11 – 17 | 10 – 15 |
| 80 – 84 | 10 – 15 | 9 – 14 |
| 85 – 89 | 8 – 14 | 8 – 13 |
| 90 – 94 | 7 – 12 | 4 – 11 |

Por debajo del límite inferior → debilidad de tren inferior y riesgo aumentado de
pérdida de autonomía. Por encima del superior → por encima de la media de su edad.

**Para menores de 60 no hay tabla normativa publicada de esta variante.** Escala
orientativa de uso interno:

| Categoría | Hombres < 60 | Mujeres < 60 |
|---|---|---|
| Bajo | < 17 | < 15 |
| Medio | 17 – 25 | 15 – 22 |
| Alto | > 25 | > 22 |

**b) 5 repeticiones — tiempo en completar cinco ciclos (segundos).**
Más rápida y mejor para población adulta general. Valores medios:

| Edad | Tiempo medio |
|---|---|
| 20 – 49 | 6 – 8 s |
| 50 – 59 | 8 – 10 s |
| 60 – 69 | ≈ 11,5 s |
| 70 – 79 | ≈ 12,5 s |
| ≥ 80 | ≈ 15 s |

**Puntos de corte de interés clínico, cualquier edad:**
**> 12 s** → riesgo de caída aumentado · **> 15 s** → indicador de fragilidad.
Ambos se marcan en el informe.

**Criterio de la aplicación:** por debajo del rango normal de su edad, o por encima
de 12 s en la variante de 5 repeticiones, se prioriza el trabajo de fuerza de tren
inferior en la planificación y se registra como hallazgo en el informe.

Conviene además anotar la **altura de la silla** (estándar ≈ 43-45 cm) y si usa
apoyo de brazos: sin eso, dos mediciones no son comparables.

*Solidez: media para la tabla de 60+ y para los puntos de corte de 5
repeticiones. Baja para la escala de menores de 60 en la variante de 30 s.*

---

## 4. Potencia

### 4.1 Salto vertical (CMJ / test de Sargent), cm

| Edad | Hombres: bajo · medio · alto | Mujeres: bajo · medio · alto |
|---|---|---|
| 20 – 29 | < 40 · 40 – 54 · > 54 | < 25 · 25 – 37 · > 37 |
| 30 – 39 | < 35 · 35 – 49 · > 49 | < 22 · 22 – 33 · > 33 |
| 40 – 49 | < 30 · 30 – 43 · > 43 | < 19 · 19 – 29 · > 29 |
| 50 – 59 | < 25 · 25 – 37 · > 37 | < 16 · 16 – 25 · > 25 |
| ≥ 60 | < 20 · 20 – 30 · > 30 | < 12 · 12 – 20 · > 20 |

### 4.2 Salto horizontal a pies juntos, cm

| Edad | Hombres: bajo · medio · alto | Mujeres: bajo · medio · alto |
|---|---|---|
| 20 – 29 | < 190 · 190 – 230 · > 230 | < 140 · 140 – 175 · > 175 |
| 30 – 39 | < 175 · 175 – 215 · > 215 | < 130 · 130 – 165 · > 165 |
| 40 – 49 | < 160 · 160 – 200 · > 200 | < 120 · 120 – 150 · > 150 |
| 50 – 59 | < 145 · 145 – 180 · > 180 | < 105 · 105 – 135 · > 135 |
| ≥ 60 | < 125 · 125 – 160 · > 160 | < 90 · 90 – 115 · > 115 |

*Solidez: media-baja. Los valores de salto varían mucho según protocolo (con o
sin contramovimiento, con o sin brazos). **Fijar un protocolo y no cambiarlo**
importa más que el baremo exacto.*

---

## 5. Resistencia cardiorrespiratoria — potencia aeróbica

### 5.1 VO₂máx: baremos por sexo y edad

ml/kg/min. Es la tabla de referencia para la potencia aeróbica, y el eje
`RESISTENCIA` del radar del informe se calcula con ella.

**Hombres**

| Edad | Muy bajo | Bajo | Medio | Bueno | Excelente | Superior |
|---|---|---|---|---|---|---|
| 20 – 29 | < 33 | 33 – 36 | 37 – 41 | 42 – 45 | 46 – 52 | > 52 |
| 30 – 39 | < 31 | 31 – 34 | 35 – 38 | 39 – 42 | 43 – 49 | > 49 |
| 40 – 49 | < 30 | 30 – 32 | 33 – 36 | 37 – 40 | 41 – 45 | > 45 |
| 50 – 59 | < 26 | 26 – 30 | 31 – 34 | 35 – 38 | 39 – 42 | > 42 |
| ≥ 60 | < 20 | 20 – 25 | 26 – 31 | 32 – 35 | 36 – 40 | > 40 |

**Mujeres**

| Edad | Muy bajo | Bajo | Medio | Bueno | Excelente | Superior |
|---|---|---|---|---|---|---|
| 20 – 29 | < 24 | 24 – 27 | 28 – 32 | 33 – 36 | 37 – 41 | > 41 |
| 30 – 39 | < 20 | 20 – 23 | 24 – 28 | 29 – 32 | 33 – 37 | > 37 |
| 40 – 49 | < 17 | 17 – 21 | 22 – 24 | 25 – 29 | 30 – 35 | > 35 |
| 50 – 59 | < 15 | 15 – 19 | 20 – 22 | 23 – 27 | 28 – 31 | > 31 |
| ≥ 60 | < 13 | 13 – 17 | 18 – 20 | 21 – 24 | 25 – 30 | > 30 |

**Órdenes de magnitud para situarse:**

| Perfil | VO₂máx aproximado |
|---|---|
| Adulto sedentario | 25 – 35 (H) · 20 – 30 (M) |
| Adulto activo, entrena 2-3 días | 40 – 48 (H) · 33 – 40 (M) |
| Aficionado con años de entrenamiento | 50 – 60 (H) · 42 – 50 (M) |
| Deportista de resistencia de nivel | 65 – 80 (H) · 55 – 70 (M) |
| Umbral de autonomía funcional en mayores | ≈ 15 – 18 |

*Solidez: media. Es la tabla de percentiles de uso más extendido en valoración de
la condición física. Deriva de población estadounidense medida en tapiz rodante:
un test de campo dará valores algo distintos.*

### 5.2 Fórmulas de estimación del VO₂máx

**Rockport — 1 milla (1.609 m) andando lo más rápido posible sin correr.**
Se registra el tiempo y la FC inmediatamente al terminar.

```
VO2max = 132,853 − (0,0769 × peso_lb) − (0,3877 × edad)
         + (6,315 × sexo) − (3,2649 × tiempo_min) − (0,1565 × FC_final)
```
`sexo` = 1 hombre, 0 mujer · `peso_lb` = peso en kg × 2,2046

Es la prueba **recomendada por defecto**: segura, sin esfuerzo máximo, válida para
sedentarios y mayores, y solo necesita una distancia medida y un pulsómetro.

**Course Navette 20 m** — se registra la velocidad del último palier completado
(km/h):
```
VO2max = 31,025 + (3,238 × V) − (3,248 × edad) + (0,1536 × V × edad)
```

**Cooper — distancia recorrida en 12 minutos (metros):**
```
VO2max = (distancia_m − 504,9) / 44,73
```

*Solidez: alta en cuanto a que son las ecuaciones estándar de cada prueba. El
error de estimación propio de estas fórmulas es del orden de ±10-15 %, lo que
importa al comparar: **usar siempre la misma prueba con el mismo usuario.***

### 5.3 Prueba del escalón de Harvard (*Harvard Step Test*)

**Protocolo.** Subir y bajar un escalón a ritmo de **30 subidas por minuto**
(metrónomo a 120 ppm: sube-sube-baja-baja) durante **5 minutos**, o hasta que la
persona no pueda mantener el ritmo.

- Altura del escalón: **50 cm hombres · 43 cm mujeres**.
- Se anota la **duración real** en segundos (importante si no llega a los 5 min).
- Tras terminar, la persona se sienta y se cuentan las pulsaciones en tres
  ventanas de recuperación: **1:00–1:30**, **2:00–2:30** y **3:00–3:30**.

**Índice de capacidad física (IF), versión completa:**

```
IF = (duración_segundos × 100) / (2 × (P1 + P2 + P3))
```

**Versión corta**, solo con el primer recuento (menos precisa, más rápida):

```
IF = (duración_segundos × 100) / (5,5 × P1)
```

**Clasificación del índice:**

| Índice | Categoría | Puntuación |
|---|---|---|
| < 55 | Deficiente | 10 |
| 55 – 64 | Bajo | 30 |
| 65 – 79 | Medio | 50 |
| 80 – 89 | Bueno | 75 |
| ≥ 90 | Excelente | 100 |

Sin diferencias de baremo por edad ni sexo: la altura distinta del escalón ya
compensa parcialmente, y el índice se interpreta igual para todos. Esto es a la
vez su ventaja (tabla única, muy simple) y su limitación (un índice de 70 no
significa lo mismo a los 25 que a los 65).

> **Dos advertencias de uso:**
>
> 1. **Es una prueba exigente.** Cinco minutos a 30 subidas por minuto en un
>    escalón de 50 cm es un esfuerzo duro para alguien desentrenado. Va marcada
>    con `Requiere_Esfuerzo_Maximo_SN = Sí`, así que **el cribado previo la
>    bloquea** ante cualquier señal de alerta, y queda fuera de los protocolos de
>    principiante, mayores y reincorporación. Para esos perfiles, Rockport.
> 2. **El índice no es VO₂máx.** Mide la velocidad de recuperación cardíaca, que
>    está relacionada con la condición aeróbica pero no es la misma variable, y
>    las conversiones que circulan a ml/kg/min no son fiables. Ver abajo cómo lo
>    resuelve la aplicación.

**Variante modificada**, para quien no puede con el protocolo completo: escalón de
30-35 cm, 3 minutos, mismo cálculo. **No comparable** con el protocolo estándar:
se registra como prueba distinta, no como la misma con otra altura.

*Solidez: media. El protocolo y la clasificación son los clásicos de la prueba;
la ausencia de ajuste por edad y sexo es su debilidad conocida.*

### 5.4 Cómo conviven las pruebas de resistencia en el informe

Rockport, Course Navette y Cooper desembocan todas en **VO₂máx estimado**, así que
son intercambiables entre sí y comparten el baremo de §5.1.

Harvard produce un **índice propio**, en otra escala y sin equivalencia fiable con
el VO₂máx. La aplicación lo trata así:

- Guarda el índice tal cual, con su categoría y su puntuación 0-100 de la tabla de
  arriba.
- Esa puntuación alimenta el eje `RESISTENCIA` del radar igual que lo haría un
  VO₂máx, porque **la escala 0-100 sí es común**.
- Pero en las **comparativas entre valoraciones no mezcla pruebas**: un Harvard
  solo se compara con otro Harvard. Si en la valoración inicial se hizo Rockport y
  en la de seguimiento Harvard, el informe muestra ambas por separado y **no
  dibuja una flecha de evolución** entre ellas.

Es la misma regla que con los protocolos: antes que una comparación cómoda pero
falsa, un hueco honesto.

---

## 6. Movilidad y equilibrio

### 6.1 *Sit & reach* (flexibilidad isquiosural y lumbar)

Convención de esta tabla: **0 = las manos llegan justo a la punta de los pies**.
Valores positivos = sobrepasa los pies. Si se usa caja con la marca de los pies en
26 cm, sumar 26 a estos valores.

| Edad | Hombres: bajo · medio · alto | Mujeres: bajo · medio · alto |
|---|---|---|
| 20 – 29 | < −5 · −5 a +7 · > +7 | < −2 · −2 a +10 · > +10 |
| 30 – 39 | < −6 · −6 a +6 · > +6 | < −3 · −3 a +9 · > +9 |
| 40 – 49 | < −8 · −8 a +4 · > +4 | < −4 · −4 a +8 · > +8 |
| 50 – 59 | < −10 · −10 a +2 · > +2 | < −5 · −5 a +7 · > +7 |
| ≥ 60 | < −12 · −12 a 0 · > 0 | < −7 · −7 a +5 · > +5 |

*Solidez: media. Muy sensible al protocolo — **anotar la convención usada** o los
seguimientos no serán comparables.*

### 6.2 *Scratch test* (movilidad de hombro)

Una mano por encima del hombro y la otra por detrás de la espalda, intentando que
los dedos se toquen. Se mide la distancia entre las puntas de los dedos medios:
**valor negativo = separación (no se tocan)**, 0 = se tocan justo,
**positivo = solapamiento**. Se mide **cada lado**.

**Adultos hasta 59 años** — escala de interpretación:

| Categoría | Hombres | Mujeres |
|---|---|---|
| Limitación marcada | < −10 cm | < −8 cm |
| Limitación leve | −10 a −3 cm | −8 a −2 cm |
| Normal | −2 a +2 cm | −1 a +3 cm |
| Buena movilidad | > +2 cm | > +3 cm |

**A partir de 60 años** — rangos considerados normales:

| Edad | Hombres | Mujeres |
|---|---|---|
| 60 – 64 | −16,5 a 0 cm | −7,5 a +4,0 cm |
| 65 – 69 | −19,0 a −2,5 cm | −9,0 a +4,0 cm |
| 70 – 74 | −20,5 a −2,5 cm | −10,0 a +2,5 cm |
| 75 – 79 | −23,0 a −5,0 cm | −12,5 a +1,5 cm |
| 80 – 84 | −24,0 a −5,0 cm | −14,0 a 0 cm |
| ≥ 85 | −25,5 a −7,5 cm | −18,0 a −2,5 cm |

**La asimetría entre lados (> 5 cm) es tan informativa como el valor absoluto**, y
es lo que orienta el trabajo de movilidad.

*Solidez: media para 60+ (tabla del Senior Fitness Test, convertida de pulgadas);
baja para la escala de adultos jóvenes.*

### 6.3 Dorsiflexión de tobillo (rodilla a pared)

De pie frente a una pared, pie en el suelo, se intenta tocar la pared con la
rodilla sin despegar el talón. Se mide la distancia del dedo gordo a la pared.

| Categoría | Distancia |
|---|---|
| Limitación marcada | < 6 cm |
| Limitación | 6 – 9 cm |
| Normal | 10 – 13 cm |
| Buena | > 13 cm |

**Asimetría > 1,5 cm** entre lados: relevante, muy frecuente tras esguinces, y
causa habitual de compensaciones en la sentadilla.

*Solidez: media.*

### 6.4 Apoyo monopodal con ojos cerrados

Segundos hasta perder la posición, mejor de dos intentos. Muy dependiente de la
edad, por lo que el baremo por décadas es imprescindible.

| Edad | Deficiente | Normal | Bueno |
|---|---|---|---|
| 18 – 39 | < 15 s | 15 – 30 s | > 30 s |
| 40 – 49 | < 13 s | 13 – 28 s | > 28 s |
| 50 – 59 | < 10 s | 10 – 21 s | > 21 s |
| 60 – 69 | < 5 s | 5 – 10 s | > 10 s |
| 70 – 79 | < 3 s | 3 – 5 s | > 5 s |
| ≥ 80 | < 2 s | 2 – 4 s | > 4 s |

Sin diferencias relevantes entre sexos en esta prueba.

*Solidez: media.*

---

## 7. Cómo se traducen estas tablas a `T_BAREMOS`

Cada fila de las tablas de este anexo se convierte en una o varias filas de la
hoja `T_BAREMOS`:

| `ID_Test` | `Sexo` | `Edad_Min` | `Edad_Max` | `Valor_Min` | `Valor_Max` | `Categoria` | `Puntuacion` |
|---|---|---|---|---|---|---|---|
| VO2MAX | H | 20 | 29 | 0 | 32,9 | MUY_BAJO | 10 |
| VO2MAX | H | 20 | 29 | 33 | 36,9 | BAJO | 30 |
| VO2MAX | H | 20 | 29 | 37 | 41,9 | MEDIO | 50 |
| VO2MAX | H | 20 | 29 | 42 | 45,9 | BUENO | 70 |
| VO2MAX | H | 20 | 29 | 46 | 52 | EXCELENTE | 85 |
| VO2MAX | H | 20 | 29 | 52,1 | 999 | SUPERIOR | 100 |

Reglas de la aplicación:

- Busca la fila cuyo sexo, rango de edad y rango de valor contienen la medición.
- Si `T_CAT_TESTS.Mejor_Es = BAJO` (perímetro de cintura, tensión), la puntuación
  se invierte.
- Si **no encuentra baremo** para esa combinación, guarda el valor medido sin
  categoría ni puntuación. Aparece en el informe como dato y en la evolución, pero
  **no entra en el radar**. Nunca se inventa una categoría.
- La aplicación incluirá un botón **"cargar baremos iniciales"** que rellena
  `T_BAREMOS` con todas las tablas de este anexo, para tener un punto de partida
  editable desde el primer día.
