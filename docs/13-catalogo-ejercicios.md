# 13 — Catálogo de ejercicios

Sin catálogo, un programa es texto libre y no se puede hacer nada con él. Con
catálogo se puede equilibrar una sesión por patrón de movimiento, buscar
sustitutos, filtrar por el material que el usuario tiene de verdad y darle a la
IA una lista cerrada de la que elegir.

## El fichero

`datos_iniciales/ejercicios.csv` — **127 ejercicios** de partida, preparados para
este proyecto y pensados para que el entrenador los revise, corrija y amplíe.

Formato pensado para abrirse bien en el Excel español sin tocar nada:

| Aspecto | Elección |
|---|---|
| Separador de campos | punto y coma `;` |
| Varios valores en un campo | barra vertical `\|` |
| Codificación | UTF-8 con BOM, para que los acentos salgan bien |

Se importa desde la propia aplicación (**Ejercicios → Importar desde CSV…**) o
desde la línea de comandos:

```
python herramientas/importar_ejercicios.py [ruta.csv] [--actualizar]
```

Sin `--actualizar` solo da de alta lo que falta y **no toca nada de lo que ya
tienes**. Con `--actualizar`, sobreescribe con lo que diga el fichero. Si una
fila no trae `ID_Ejercicio`, el nombre hace de clave para no duplicar.

## Reparto por patrón

| Patrón | Nº | Patrón | Nº |
|---|---|---|---|
| Monoarticular | 23 | Movilidad | 13 |
| Dominante de rodilla | 15 | Locomoción | 12 |
| Core | 14 | Tracción horizontal | 9 |
| Empuje horizontal | 13 | Tracción vertical | 8 |
| Dominante de cadera | 13 | Empuje vertical | 7 |

## Vocabularios

Son listas cerradas a propósito: si el material se escribe de veinte maneras, el
filtro por material deja de servir. La aplicación avisa al importar cuando
encuentra un valor fuera del vocabulario, pero no bloquea.

**Patrón de movimiento** — `EMPUJE_H` · `EMPUJE_V` · `TRACCION_H` · `TRACCION_V` ·
`DOMINANTE_RODILLA` · `DOMINANTE_CADERA` · `CORE` · `LOCOMOCION` ·
`MONOARTICULAR` · `MOVILIDAD`

**Grupo muscular** — `PECTORAL` · `DORSAL` · `TRAPECIO` · `DELTOIDES` · `BICEPS` ·
`TRICEPS` · `ANTEBRAZO` · `CUADRICEPS` · `ISQUIOSURALES` · `GLUTEO` ·
`ADUCTORES` · `ABDUCTORES` · `GEMELOS` · `CORE` · `ERECTORES` ·
`CUERPO_COMPLETO` · `CARDIOVASCULAR`

**Material** — `PESO_CORPORAL` · `BARRA` · `DISCOS` · `MANCUERNAS` · `KETTLEBELL` ·
`POLEA` · `MAQUINA` · `BANCO` · `BANCO_LUMBAR` · `RACK` · `BARRA_DOMINADAS` ·
`PARALELAS` · `GOMA` · `TRX` · `CAJON` · `COLCHONETA` · `RODILLO` ·
`BALON_MEDICINAL` · `RUEDA_ABDOMINAL` · `COMBA` · `PALO` · `TRINEO` · `CINTA` ·
`BICICLETA` · `REMO_ERGOMETRO` · `ELIPTICA`

## Dos convenciones que importan

**`PESO_CORPORAL` significa que la resistencia es el propio cuerpo**, no que no
haga falta material. Una dominada declara `BARRA_DOMINADAS|PESO_CORPORAL`:
necesita la barra, pero no hay kilos que prescribir. Por eso el filtro de
material no cuenta `PESO_CORPORAL` como requisito, y por eso esos ejercicios no
llevan incremento de carga.

**`Incremento_Kg` es el salto mínimo real** de ese ejercicio: 2,5 kg en barra
(discos de 1,25 a cada lado), 2 en mancuernas, 5 en máquina de placas, 2,5 en
polea, 4 en kettlebell. Es lo que evita que el programa imprima «77,3 kg» en
lugar de «77,5 kg». Una prueba automática comprueba que **todo ejercicio con
carga externa lo declara**.

## Lo que da el catálogo

- **Sustitutos**: mismo patrón de movimiento, ordenados por parecido (grupo
  principal, nivel, si es básico), y opcionalmente acotados al material
  disponible. Resuelve el «no tengo barra» sin rehacer el programa.
- **Catálogo filtrado** por material, nivel y antecedentes de salud. En la fase 7
  es exactamente lo que se le pasa a la IA: si la lista va filtrada, el modelo no
  puede prescribir algo imposible.
- **Aviso de patrones sin cobertura**: al filtrar por el material de un usuario
  es fácil quedarse sin ninguna tracción vertical y montarle un plan
  desequilibrado sin darse cuenta. La aplicación lo dice antes de que pase. Con
  solo mancuernas, por ejemplo, desaparecen la tracción vertical y el core.
- **Volumen semanal por grupo**, contando el grupo principal entero y los
  secundarios a media serie. Alimenta el control de volumen de
  [06](06-cargas-progresion.md).
- **Cribado de contraindicaciones**: cruza los antecedentes del usuario con las
  contraindicaciones del ejercicio buscando términos clínicos comunes (hombro,
  lumbar, hernia, femoropatelar…).

> Sobre esto último, conviene ser claro: **cruzar texto libre nunca es fiable del
> todo**. Sirve para *señalar para revisar*, no para bloquear. El bloqueo de
> verdad vendrá de las reglas duras de `T_REGLAS` en la fase 7, que son
> explícitas y las escribe el entrenador.

## Bajas

Un ejercicio nunca se borra: se **desactiva**. Si estuviera usado en un programa,
borrarlo rompería el histórico. Al desactivarlo deja de ofrecerse para programas
nuevos y sigue existiendo en los antiguos.
