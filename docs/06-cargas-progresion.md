# 06 — Cálculo de cargas y progresión

Marcado como **muy importante y valioso**. Es lo que convierte la planificación de
un documento estático en algo que se recalcula solo.

## La idea

En la planificación no se guardan kilos. Se guarda la **intención**:
*"3 series de 5 repeticiones al 80 % del 1RM"*. Los kilos se calculan en el
momento de generar el PDF, con el 1RM vigente de ese usuario para ese ejercicio.

Consecuencia: cuando se actualiza un 1RM (por una valoración o a mano), **toda la
planificación futura se recalcula sola**. La misma plantilla de macrociclo sirve
para un principiante y para alguien avanzado, sin duplicarla.

## Modos de carga (`T_SESION_DET.Modo_Carga`)

| Modo | `Valor_Carga` | Cálculo |
|---|---|---|
| `PCT1RM` | 80 | `1RM × 0,80`, redondeado al incremento del ejercicio |
| `RPE` | 8 | Se traduce a % según la tabla RPE/repeticiones y luego como `PCT1RM` |
| `RIR` | 2 | Ídem (RIR 2 ≈ RPE 8) |
| `KG` | 40 | Carga fija, sin cálculo |
| `PESO_CORPORAL` | — | Sin carga externa |
| `TIEMPO` | 45 | Segundos, para isométricos y cardio |

Si un usuario no tiene 1RM registrado en un ejercicio prescrito por porcentaje, el
PDF imprime **"por determinar"** con una nota, y la aplicación lo lista en las
alertas del panel. Nunca se inventa un número.

## Estimación del 1RM

A partir de una serie submáxima (peso `w`, repeticiones `r`):

| Fórmula | Expresión |
|---|---|
| **Epley** (por defecto) | `1RM = w × (1 + r / 30)` |
| Brzycki | `1RM = w × 36 / (37 − r)` |
| Lombardi | `1RM = w × r^0,10` |

Fórmula por defecto configurable en `T_CONFIG`.

Aviso de fiabilidad, que se guarda en `T_1RM.Fiabilidad`:

- `r ≤ 5` → fiabilidad **alta**
- `6 ≤ r ≤ 10` → **media**
- `r > 10` → **baja**; la aplicación avisa de que la estimación se degrada y
  sugiere repetir el test con más peso y menos repeticiones.

## Redondeo a carga real

El detalle que hace que sea usable de verdad: no sirve imprimir "77,3 kg".
Cada ejercicio tiene su `Incremento_Kg` en `T_EJERCICIOS`:

- Barra: 2,5 kg (discos de 1,25 kg a cada lado)
- Mancuernas: 2 kg (o según el juego disponible)
- Máquina de placas: 5 kg
- Poleas: 2,5 kg

El cálculo redondea **hacia abajo** al múltiplo más cercano, y además comprueba que
el resultado sea alcanzable con el material declarado (una barra de 20 kg no puede
cargar 17,5 kg). En la impresión se indica: `80 % → 77,5 kg`.

## Progresión entre semanas

Cada microciclo puede declarar una **pauta de progresión** por línea de ejercicio
(`T_SESION_DET.Progresion`):

| Pauta | Comportamiento |
|---|---|
| `NINGUNA` | Misma carga todas las semanas |
| `LINEAL:+2.5` | Suma 2,5 kg por semana (básicos) |
| `LINEAL:+1.25` | Accesorios |
| `PCT:70,75,80,82` | Porcentaje explícito semana a semana (ondulación) |
| `DESCARGA:60` | Semana de descarga al 60 % de la carga de la semana anterior |
| `DOBLE_PROGRESION` | Sube repeticiones dentro del rango hasta el techo; al llegar, sube carga y vuelve al suelo del rango |
| `AUTORREGULADA:RIR2` | Mantiene el RIR objetivo; la carga la ajusta el usuario en la sesión |

La progresión se evalúa al generar el PDF, que imprime **la semana concreta** con
sus kilos ya resueltos. Así el usuario recibe un documento sin cálculos que hacer.

## Estructura del PDF del programa

Encabezado: usuario, nombre del macrociclo, fase actual, fechas, objetivo.
Una página por microciclo. Por sesión, una tabla:

| Bloque | Ejercicio | Series | Reps | Carga | Descanso | Notas |
|---|---|---|---|---|---|---|
| Principal | Sentadilla trasera | 4 | 5 | 80 % → **77,5 kg** | 3 min | Tempo 3-0-1 |
| Accesorio | Prensa 45° | 3 | 10-12 | RIR 2 | 90 s | |

Pie de página con espacio para que el usuario anote lo que hizo de verdad — que es
la vía manual de recoger lo ejecutado hasta que exista el módulo de registro.

## Control de volumen (opcional, propuesta)

Con el patrón y el grupo muscular de cada ejercicio se puede calcular
automáticamente el **volumen semanal por grupo** (series efectivas) y avisar si
queda fuera de un rango razonable (p. ej. menos de 8 o más de 22 series semanales
por grupo). Es una comprobación baratísima de implementar que evita errores
groseros, tanto propios como de la IA.
