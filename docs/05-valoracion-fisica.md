# 05 — Valoración física

> Las tablas de referencia numéricas de cada prueba están en el
> **[Anexo 11 — Baremos y tablas de referencia](11-anexo-baremos.md)**.

## Para qué sirve

1. **Entregable de valor al usuario**: informe en PDF con su punto de partida.
2. **Entrada de la planificación**: sin valoración, cualquier programa es una
   suposición.
3. **Materia prima para la IA**: datos normalizados en lugar de impresiones.

## Cuándo se hace

- **INICIAL**: en el alta.
- **SEGUIMIENTO**: a criterio del entrenador (lo natural, al cerrar cada
  mesociclo o cada 8-12 semanas).
- **FINAL_CICLO**: al cerrar una asignación, para el informe comparativo que
  acompaña a la propuesta del ciclo siguiente.

Alerta en el panel: usuarios cuya última valoración supera los N meses
(configurable, por defecto 4).

---

## Protocolos: varias plantillas de valoración

**No todos los usuarios hacen la misma batería.** No estaba contemplado en la
versión anterior de este documento y se añade ahora como pieza central.

La valoración se organiza en **protocolos**: plantillas que agrupan un
subconjunto de pruebas del catálogo, en un orden, con indicación de cuáles son
obligatorias.

### Tablas

**`T_PROTOCOLOS`**
`ID_Protocolo` · Nombre · Descripción · `Perfil_Objetivo` · `Edad_Min` ·
`Edad_Max` · `Sexo` (o ambos) · `Duracion_Est_Min` · `Material_Necesario` ·
`Es_Predeterminado_SN` · `Activo_SN`

**`T_PROTOCOLO_DET`**
`ID_Protocolo` · `ID_Test` · Orden · `Obligatorio_SN` · `Notas_Protocolo`

### Protocolos de partida propuestos

| Protocolo | Para quién | Contenido |
|---|---|---|
| **Estándar adulto activo** | Adulto sano, sin limitaciones | Batería completa |
| **Principiante / sedentario** | Sin experiencia previa | Cribado + composición + técnica + dinamómetro + Rockport. Sin saltos ni dominadas |
| **Mayor de 65** | Población mayor | Cribado ampliado + composición + equilibrio + movilidad (*scratch*, *sit & reach*) + dinamómetro + marcha. Sin esfuerzo máximo |
| **Reincorporación tras lesión** | Vuelta desde lesión | Cribado + técnica del patrón afectado + asimetrías + movilidad. Sin test máximos |
| **Rendimiento / deportista** | Con experiencia | Completa + Course Navette + saltos + dominadas |
| **Revisión rápida (seguimiento)** | Seguimiento entre ciclos | Composición + dinamómetro + 2-3 pruebas de control. 20 minutos |

Editables y ampliables desde el Excel. El entrenador puede crear los suyos.

### Cómo funciona en la aplicación

1. Al crear una valoración se elige el protocolo. La aplicación **sugiere** el más
   adecuado según edad, sexo y datos de salud del usuario, pero el entrenador
   decide.
2. Se abre la ventana con **solo las pruebas de ese protocolo**, en su orden, con
   el protocolo escrito de cada una a la vista.
3. Las pruebas obligatorias no cumplimentadas impiden cerrar la valoración; las
   opcionales se pueden dejar en blanco.
4. Se puede **añadir una prueba fuera de protocolo** en cualquier momento.
5. Queda registrado qué protocolo se usó (`T_VALORACIONES.ID_Protocolo`), lo cual
   es imprescindible para que las comparativas sean honestas: solo se comparan
   pruebas presentes en ambas valoraciones.

---

## Tipos de medida

Cada prueba del catálogo declara su `Tipo_Medida`:

| Tipo | Qué se registra | Ejemplos |
|---|---|---|
| `CUANTITATIVA` | Un número con unidad, baremado por sexo y edad | Dinamometría, VO2máx, *sit & reach*, tiempos isométricos |
| `TECNICA` | Una puntuación de calidad de movimiento 0-3 + criterios observados | Sentadilla, zancada, *step down* |
| `MIXTA` | Número **y** puntuación técnica | Dominada (repeticiones + técnica) |
| `CUALITATIVA` | Categoría o texto | Cribado, observaciones posturales |

### Escala de técnica (0-3)

| Puntuación | Criterio |
|---|---|
| **0** | **Aparece dolor durante el movimiento.** Se detiene la prueba y se deriva |
| **1** | No completa el movimiento, o compensaciones graves no corregibles en el momento |
| **2** | Completa el movimiento con compensaciones leves, corregibles con indicación verbal |
| **3** | Ejecución correcta en todo el rango, sin compensaciones |

Un **0 en cualquier prueba técnica** marca la valoración con alerta y bloquea la
prescripción de ese patrón hasta su revisión. Es la misma lógica de seguridad del
cribado.

Cada prueba técnica lleva su **lista de criterios observables** (`T_TEST_CRITERIOS`:
`ID_Test` · `ID_Criterio` · Descripción · Orden). En la ventana aparecen como
casillas, y lo marcado se guarda en `T_VALORACION_CRITERIOS`. Así la puntuación
queda justificada y el informe puede decir *qué* falla, no solo *cuánto*.

---

## Batería de pruebas

### Cribado previo (antes de cualquier esfuerzo)

| Prueba | Registro | Tablas |
|---|---|---|
| PAR-Q+ (7 preguntas) | Sí/No cada una | [Anexo §1](11-anexo-baremos.md#1-cribado-previo) |
| Tensión arterial en reposo | mmHg | [Anexo §1.2](11-anexo-baremos.md#12-tensión-arterial-en-reposo) |
| Frecuencia cardíaca en reposo | lpm | [Anexo §1.3](11-anexo-baremos.md#13-frecuencia-cardíaca-en-reposo) |

Cualquier "Sí" en el PAR-Q+, o una tensión en grado de hipertensión, marca
`Requiere_Informe_Medico_SN`, **bloquea las pruebas de esfuerzo máximo** y exige
confirmación expresa para continuar.

### Composición corporal — `CUANTITATIVA`

Peso · Altura · IMC *(calculado)* · % grasa (pliegues o bioimpedancia) ·
Perímetros: cintura, cadera, abdomen, brazo relajado y contraído, muslo, pecho ·
Índice cintura-cadera *(calculado)* · Índice cintura-altura *(calculado)*

Tablas: [Anexo §2](11-anexo-baremos.md#2-composición-corporal)

### Fuerza y control motor

**Cambio respecto a la versión anterior:** en la valoración inicial la fuerza
**no se mide en unidades**, se valora la **calidad de ejecución**. La única prueba
cuantitativa es la dinamometría. Los test de 1RM submáximo salen de la valoración
inicial y quedan como prueba de seguimiento opcional, dentro del protocolo de
rendimiento.

| Prueba | Tipo | Registro | Tablas |
|---|---|---|---|
| **Dinamometría manual** | `CUANTITATIVA` | kg, mano dominante y no dominante | [§3.1](11-anexo-baremos.md#31-dinamometría-manual-handgrip) |
| **Sentadilla profunda** (con brazos arriba) | `TECNICA` | 0-3 + criterios | [§3.2](11-anexo-baremos.md#32-pruebas-de-técnica-escala-0-3) |
| **Zancada** (*lunge*) | `TECNICA` | 0-3 + criterios, cada lado | [§3.2](11-anexo-baremos.md#32-pruebas-de-técnica-escala-0-3) |
| **Step down** (descenso lateral del escalón) | `TECNICA` | 0-3 + criterios, cada lado | [§3.3](11-anexo-baremos.md#33-step-down-descenso-lateral) |
| **Dominada** (*pull up*) | `MIXTA` | repeticiones + técnica 0-3 | [§3.4](11-anexo-baremos.md#34-dominada-pull-up-y-suspensión) |
| **Plancha frontal** | `CUANTITATIVA` | segundos | [§3.5](11-anexo-baremos.md#35-resistencia-isométrica-del-tronco) |
| **Plancha lateral** (*side plank*) | `CUANTITATIVA` | segundos, cada lado | [§3.5](11-anexo-baremos.md#35-resistencia-isométrica-del-tronco) |
| **Plancha invertida** (*reverse plank*) | `CUANTITATIVA` | segundos | [§3.5](11-anexo-baremos.md#35-resistencia-isométrica-del-tronco) |
| **Sorensen** (extensores lumbares) | `CUANTITATIVA` | segundos | [§3.5](11-anexo-baremos.md#35-resistencia-isométrica-del-tronco) |

**Eliminado:** test de abdominales en 60 segundos.

> **Punto a confirmar:** plancha lateral, plancha invertida y Sorensen son
> pruebas *cronometradas*, no de técnica. Las he clasificado como cuantitativas
> porque es lo que son y porque existen valores de referencia, sobre todo para
> las **relaciones entre ellas** (§3.5 del anexo), que es su aportación más útil:
> detectan desequilibrios flexores/extensores y asimetrías derecha-izquierda. Si
> prefieres valorarlas solo por técnica, se cambia con una celda del catálogo.

### Potencia — `CUANTITATIVA`

| Prueba | Unidad | Tablas |
|---|---|---|
| Salto vertical (CMJ / Sargent) | cm | [§4](11-anexo-baremos.md#4-potencia) |
| Salto horizontal a pies juntos | cm | [§4](11-anexo-baremos.md#4-potencia) |

Fuera de los protocolos de principiante, mayores y reincorporación.

### Resistencia cardiorrespiratoria — `CUANTITATIVA`

Todas las pruebas desembocan en la **misma variable comparable: el VO₂máx
estimado (ml/kg/min)**, que es la medida de potencia aerobica. Así da igual qué
prueba se use con cada usuario: el baremo y el radar del informe son los mismos.

| Prueba | Perfil | Fórmula y tablas |
|---|---|---|
| Rockport (1 milla andando) | Principiantes, sedentarios, mayores | [§5.2](11-anexo-baremos.md#52-fórmulas-de-estimación-del-vo₂máx) |
| Course Navette 20 m | Jóvenes, deportistas | [§5.2](11-anexo-baremos.md#52-fórmulas-de-estimación-del-vo₂máx) |
| Cooper 12 min | Corredores | [§5.2](11-anexo-baremos.md#52-fórmulas-de-estimación-del-vo₂máx) |

Baremos de VO₂máx por sexo y edad: [§5.1](11-anexo-baremos.md#51-vo₂máx-baremos-por-sexo-y-edad)

### Movilidad y equilibrio — `CUANTITATIVA`

| Prueba | Unidad | Tablas |
|---|---|---|
| *Sit & reach* | cm | [§6.1](11-anexo-baremos.md#61-sit--reach-flexibilidad-isquiosural-y-lumbar) |
| ***Scratch test*** (movilidad de hombro, manos a la espalda) | cm de separación | [§6.2](11-anexo-baremos.md#62-scratch-test-movilidad-de-hombro) |
| Dorsiflexión de tobillo (rodilla a pared) | cm | [§6.3](11-anexo-baremos.md#63-dorsiflexión-de-tobillo-rodilla-a-pared) |
| Apoyo monopodal con ojos cerrados | segundos | [§6.4](11-anexo-baremos.md#64-apoyo-monopodal-con-ojos-cerrados) |

---

## Puntuación y radar

Cada prueba produce una `Puntuacion` 0-100 a través de su baremo. Las pruebas
técnicas se convierten con una escala fija (0 → 0, 1 → 33, 2 → 66, 3 → 100).

Las puntuaciones se agregan por **capacidad** (media de las pruebas medidas de
esa capacidad presentes en el protocolo):

`FUERZA` · `POTENCIA` · `RESISTENCIA` · `MOVILIDAD` · `EQUILIBRIO` ·
`COMPOSICION` · `CONTROL_MOTOR`

Regla importante: **solo se puntúan las capacidades con al menos una prueba
medida.** Un protocolo reducido genera un radar con menos ejes, no un radar con
ceros. Un cero falso es peor que un hueco.

## El informe en PDF

1. **Portada**: nombre, fecha, protocolo aplicado, logotipo.
2. **Resumen en una página**: radar de capacidades, con el número de pruebas que
   sustenta cada eje.
3. **Detalle por prueba**: valor medido, categoría, y la referencia normativa para
   su sexo y edad tomada del anexo.
4. **Hallazgos de control motor**: qué compensaciones se han observado en las
   pruebas técnicas, en texto legible para el usuario.
5. **Asimetrías y relaciones**: diferencias derecha-izquierda y las relaciones de
   resistencia del tronco. Es información que el usuario no ha visto nunca y que
   se explica en dos frases.
6. **Comparativa** con la valoración anterior del mismo protocolo: radar
   superpuesto y tabla de diferencias. La página que vende el siguiente ciclo.
7. **Puntos fuertes y áreas de mejora**, derivados de las puntuaciones y editables
   antes de generar el PDF.
8. **Conclusión del entrenador**: texto libre.

## Enlace con la planificación

- Las puntuaciones y los hallazgos técnicos entran en el expediente de la IA.
- Un **0 técnico** en un patrón prohíbe prescribir ese patrón (regla dura).
- Un **2** lo permite con nota de corrección técnica en la sesión.
- Las asimetrías > umbral generan sugerencia de trabajo unilateral.
- Los test de 1RM submáximo, cuando se hagan (protocolo de rendimiento o
  seguimiento), escriben en `T_1RM` con `Origen = VALORACION`.
