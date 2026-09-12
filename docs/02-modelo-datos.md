# 02 — Modelo de datos

Un libro `datos_gimnasio.xlsx`. Una hoja por tabla. Se listan los campos
relevantes; los tipos van implícitos por el nombre (`F_` = fecha, `_SN` =
Sí/No, `ID_` = referencia).

## Decisiones de diseño no obvias

**1. El árbol se resuelve con `ID_Padre` (lista de adyacencia).**
Una sola hoja `T_CICLOS` contiene macrociclos, mesociclos y microciclos. El campo
`ID_Padre` apunta al nivel superior. Esto permite que un macrociclo tenga
**varios** mesociclos y cada mesociclo **varios** microciclos, con profundidad
ilimitada, sin cambiar el esquema. Es la forma correcta de guardar jerarquías en
tablas planas.

**2. Formato largo donde el contenido puede crecer.**
Valoraciones y respuestas de cuestionario usan *una fila por dato* (`ID, Concepto,
Valor`) en lugar de *una columna por dato*. Así se pueden añadir test nuevos o
cambiar preguntas del formulario sin tocar la estructura del libro ni migrar nada.

**3. La carga se guarda como intención, no como kilos.**
En `T_SESION_DET` no se guarda "80 kg" sino "80 % del 1RM" (o RPE, o RIR). Los
kilos se calculan al imprimir, con el 1RM vigente del usuario. Al actualizar un
1RM, toda la planificación futura se recalcula sola. Ver [06](06-cargas-progresion.md).

**4. Los correos son una cola de estados, no un disparo.**
`T_COLA_MAIL` guarda el borrador, la nota personal del entrenador y el estado.
Nada sale sin pasar por revisión. Ver [04](04-comunicaciones-email.md).

---

## Bloque: usuarios

### `T_USUARIOS`
`ID_Usuario` · Nombre · Apellidos · `F_Nacimiento` · Sexo · Email · Teléfono ·
`F_Alta` · Estado (ACTIVO/INACTIVO/BAJA) · Notas

Consentimiento: `Consentimiento_SN` · `F_Consentimiento` ·
`Origen_Consentimiento` (FORM/PRESENCIAL) · `Acepta_Emails_SN`

> La edad **no se guarda**: se calcula desde `F_Nacimiento`. Guardar la edad es
> el error clásico que hace que los datos envejezcan mal.

### `T_SALUD`
`ID_Salud` · `ID_Usuario` · `F_Registro` · las 7 respuestas del PAR-Q+
(`PARQ_1_SN` … `PARQ_7_SN`) · `Apto_SN` · `Requiere_Informe_Medico_SN` ·
Patologías · Medicación · Lesiones_Historial · Contraindicaciones · Observaciones

Histórico: una fila por revisión, se usa la más reciente.

### `T_OBJETIVOS`
`ID_Objetivo` · `ID_Usuario` · `F_Registro` · Tipo (PERDER_GRASA / HIPERTROFIA /
FUERZA / SALUD_GENERAL / RENDIMIENTO / REHABILITACION / OTRO) · Descripción ·
Prioridad (1-3) · `Horizonte_Sem` · Métrica (texto: "peso", "1RM sentadilla"…) ·
`Valor_Objetivo` · Estado (ACTIVO / CUMPLIDO / MODIFICADO / DESCARTADO)

Histórico. Permite ver cómo evoluciona el objetivo del usuario ciclo a ciclo, que
es justo lo que pregunta el cuestionario T-14.

### `T_DISPONIBILIDAD`
`ID_Usuario` · `Dias_Semana` (nº) · `Dias_Preferidos` · Franja (MAÑANA/MEDIODIA/
TARDE/NOCHE) · `Min_Sesion` · Lugar (GIMNASIO/CASA/MIXTO) · `Material_Disponible`

Restricción de entrada clave para la planificación y para la IA: un plan de 5 días
con barra olímpica no sirve a quien entrena 3 días en casa con mancuernas.

---

## Bloque: valoración física

### `T_PROTOCOLOS` (plantillas de valoración)
`ID_Protocolo` · Nombre · Descripción · `Perfil_Objetivo` · `Edad_Min` ·
`Edad_Max` · Sexo · `Duracion_Est_Min` · `Material_Necesario` ·
`Es_Predeterminado_SN` · `Activo_SN`

No todos los usuarios hacen la misma batería. Un protocolo es un subconjunto de
pruebas del catálogo, pensado para un perfil (principiante, mayor de 65,
reincorporación tras lesión, rendimiento, revisión rápida). Ver [05](05-valoracion-fisica.md#protocolos-varias-plantillas-de-valoración).

### `T_PROTOCOLO_DET`
`ID_Protocolo` · `ID_Test` · Orden · `Obligatorio_SN` · `Notas_Protocolo`

### `T_CAT_TESTS` (catálogo de pruebas)
`ID_Test` · Nombre · Capacidad (FUERZA / POTENCIA / RESISTENCIA / MOVILIDAD /
EQUILIBRIO / COMPOSICION / CONTROL_MOTOR) · **`Tipo_Medida`** (CUANTITATIVA /
TECNICA / MIXTA / CUALITATIVA) · Unidad · `Bilateral_SN` · Protocolo (texto) ·
`Mejor_Es` (ALTO / BAJO) · Material · `Requiere_Esfuerzo_Maximo_SN` ·
`Tiene_Baremo_SN` · `Activo_SN`

`Tipo_Medida` es lo que permite que en la misma batería convivan una dinamometría
en kg y una sentadilla puntuada por técnica. `Bilateral_SN` hace que la prueba se
registre por lados y se calcule la asimetría.
`Requiere_Esfuerzo_Maximo_SN` es lo que el cribado bloquea.
`Tiene_Baremo_SN = No` (p. ej. plancha invertida) → se registra el valor, sale en
la evolución, pero no entra en el radar.

### `T_TEST_CRITERIOS` (criterios observables de las pruebas técnicas)
`ID_Test` · `ID_Criterio` · Descripción · Orden · `Es_Dolor_SN`

La lista de compensaciones que se marcan como casillas al puntuar una prueba
técnica. El criterio marcado como dolor fuerza puntuación 0.

### `T_BAREMOS` (tablas normativas)
`ID_Test` · Sexo (H / M / AMBOS) · `Edad_Min` · `Edad_Max` · `Valor_Min` ·
`Valor_Max` · Categoría · `Puntuacion` (0-100) · `Fuente` · `Solidez`

Editables desde el Excel. Valores iniciales en el
[Anexo 11](11-anexo-baremos.md), cargables con un botón.

### `T_VALORACIONES` (cabecera)
`ID_Valoracion` · `ID_Usuario` · **`ID_Protocolo`** · Fecha · Tipo (INICIAL /
SEGUIMIENTO / FINAL_CICLO) · Evaluador · `ID_Asignacion` · Observaciones ·
`Bloqueo_Esfuerzo_Maximo_SN` · `Ruta_PDF`

Guardar el protocolo usado es imprescindible para que las comparativas sean
honestas: solo se comparan pruebas presentes en ambas valoraciones.

### `T_VALORACION_DET` (formato largo)
`ID_Valoracion` · `ID_Test` · Lado (DERECHO / IZQUIERDO / NA) · Valor ·
`Valor_Tecnica` (0-3) · Unidad · `Puntuacion` · Categoría · Notas

### `T_VALORACION_CRITERIOS`
`ID_Valoracion` · `ID_Test` · `ID_Criterio` · Lado · `Observado_SN`

### `T_CAPACIDADES` (agregado calculado)
`ID_Valoracion` · Capacidad · `Puntuacion` · `N_Pruebas`

Se guarda para que el radar del informe sea reproducible años después, aunque los
baremos hayan cambiado entretanto. `N_Pruebas = 0` → el eje no se dibuja.

## Bloque: entrenamiento

### `T_EJERCICIOS`
`ID_Ejercicio` · Nombre · `Patron` (EMPUJE_H / EMPUJE_V / TRACCION_H / TRACCION_V /
DOMINANTE_RODILLA / DOMINANTE_CADERA / CORE / LOCOMOCION / MONOARTICULAR) ·
`Grupo_Principal` · `Grupos_Secundarios` · Material · Nivel (1-3) ·
`Unilateral_SN` · `Es_Basico_SN` · `Video_URL` · Contraindicaciones ·
`Incremento_Kg` · `Activo_SN`

`Patron` es lo que permite a la IA equilibrar una sesión y sustituir un ejercicio
por otro equivalente. `Incremento_Kg` es el salto mínimo de carga real
(2,5 kg en barra, 2 kg en mancuernas, 5 kg en una máquina de placas).

### `T_CICLOS`
`ID_Ciclo` · Nombre · Tipo (MACRO / MESO / MICRO) · `ID_Padre` · Orden ·
`Duracion_Sem` · `Objetivo_Ciclo` · Enfoque (ADAPTACION / ACUMULACION /
INTENSIFICACION / REALIZACION / DESCARGA) · `Es_Plantilla_SN` · Origen (MANUAL /
IA / CLONADO) · `ID_Origen` · Notas

Validación: la suma de `Duracion_Sem` de los hijos debe coincidir con la del
padre; si no, la aplicación avisa (no bloquea, avisa).

### `T_SESIONES`
`ID_Sesion` · `ID_Ciclo` (un MICRO) · `Num_Dia` · Nombre · Tipo (FUERZA / CARDIO /
MOVILIDAD / MIXTA / DESCANSO_ACTIVO) · `Duracion_Est_Min` · Notas

### `T_SESION_DET`
`ID_Linea` · `ID_Sesion` · Orden · Bloque (CALENTAMIENTO / PRINCIPAL / ACCESORIO /
CORE / VUELTA_CALMA) · `ID_Ejercicio` · `Grupo_Serie` (para superseries/circuitos) ·
Series · `Reps` (texto: "8", "8-10", "AMRAP") · `Modo_Carga` (PCT1RM / RPE / RIR /
KG / PESO_CORPORAL / TIEMPO) · `Valor_Carga` · Tempo · `Descanso_Seg` ·
`Progresion` (ver doc 06) · Notas

### `T_1RM`
`ID_Registro` · `ID_Usuario` · `ID_Ejercicio` · Fecha · `Valor_1RM` · Método
(DIRECTO / EPLEY / BRZYCKI / LOMBARDI) · `Peso_Usado` · `Reps_Usadas` ·
Origen (MANUAL / VALORACION / TEST) · `Fiabilidad` (ALTA/MEDIA/BAJA)

Histórico: se usa el más reciente por usuario y ejercicio, y el histórico da la
gráfica de progreso.

### `T_ASIGNACIONES`
`ID_Asignacion` · `ID_Usuario` · `ID_Ciclo` (normalmente el MACRO) · `F_Inicio` ·
`F_Fin_Prevista` · Estado (PLANIFICADA / EN_CURSO / FINALIZADA / INTERRUMPIDA) ·
`ID_Asignacion_Anterior` · `ID_Objetivo` · Notas

### `T_ASIG_FASES` (calendario derivado)
`ID_Asignacion` · `ID_Ciclo` · Nivel · `F_Inicio` · `F_Fin` · Estado

Se calcula desde las duraciones al asignar, pero **se guarda**: así un cambio de
la plantilla no altera el calendario de quien ya la está haciendo, y el
disparador de T-14 días tiene una fecha firme contra la que comparar.

---

## Bloque: comunicación

### `T_PLANTILLAS_MAIL`
`ID_Plantilla` · Código (CONSENTIMIENTO / BIENVENIDA / CHECKIN_MITAD /
ENCUESTA_T14 / CIERRE_CICLO / AGRADECIMIENTO / RECORDATORIO) · Asunto ·
`Cuerpo_HTML` · `Requiere_Revision_SN` · `Permite_Modo_Vacaciones_SN` ·
`Instruccion_IA` · `URL_Form` · `Activo_SN`

`Instruccion_IA` es la indicación con la que la IA personaliza el cuerpo del
correo para cada usuario. `Permite_Modo_Vacaciones_SN` decide si ese tipo de
correo puede salir sin revisión cuando el modo vacaciones está activo.

Con marcadores tipo `{{nombre}}`, `{{programa}}`, `{{objetivo}}`,
`{{nota_entrenador}}`, `{{enlace_form}}`.

### `T_COLA_MAIL`
`ID_Envio` · `ID_Usuario` · `ID_Asignacion` · `Codigo_Plantilla` · `F_Generado` ·
`F_Programada` · Estado (BORRADOR / REVISADO / ENVIADO / ERROR / CANCELADO) ·
`Nota_Entrenador` · `Cuerpo_IA` · `Asunto_Final` · `Cuerpo_Final` · `F_Envio` ·
`Aprobado_Por` (ENTRENADOR / MODO_VACACIONES) · `Enlace_Form_Prefill` ·
`F_Recordatorio` · `Respondido_SN` · `Error`

`Cuerpo_IA` guarda lo que redactó la IA antes de que el entrenador lo tocara, para
poder comparar y mejorar la instrucción. `Aprobado_Por` deja constancia de qué
salió sin revisión humana.

### `T_RESPUESTAS` (formato largo)
`ID_Respuesta` · `ID_Usuario` · `ID_Envio` · `F_Respuesta` · `Codigo_Pregunta` ·
`Valor` · `Origen` (FORM / MANUAL)

---

## Bloque: IA

### `T_CONOCIMIENTO`
`ID_Conocimiento` · Categoría · Título · Contenido · Tags · Prioridad (1-3) ·
Origen (MANUAL / APRENDIZAJE) · `F_Creacion` · `Activo_SN`

### `T_REGLAS`
`ID_Regla` · Tipo (DURA / BLANDA) · Ámbito · Condición · Acción · Prioridad ·
`Activo_SN`

### `T_IA_LOG`
`ID_Interaccion` · `ID_Usuario` · `F_Hora` · Proveedor · Modelo · Iteración ·
`Feedback_Entrenador` · `ID_Ciclo_Generado` · `Tokens` · `Duracion_Seg` · Estado

---

## Bloque: sistema

### `T_CONFIG`
Clave · Valor · Descripción — parámetros editables sin recompilar (días de aviso
previo = 14, fórmula de 1RM por defecto, nº de copias a conservar…).

### `T_CONTADORES`
Prefijo · `Ultimo_Valor` — generación de IDs.

### `T_LOG`
`F_Hora` · Nivel · Módulo · Mensaje — auditoría de escrituras y errores.
