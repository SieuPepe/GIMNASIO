# 04 — Comunicaciones por correo

## Envío

SMTP directo de Gmail: `smtp.gmail.com:465` (SSL). Requiere **contraseña de
aplicación** de 16 caracteres, que exige tener activada la verificación en dos
pasos en la cuenta de Google. La contraseña se guarda en el Almacén de
credenciales de Windows (`keyring`), nunca en el Excel ni en el `config.toml`.

Límite de Gmail gratuito: ~500 destinatarios al día. Con 100 usuarios no es un
problema.

## Cadencia definitiva

| Momento | Código | Contenido | Revisión previa |
|---|---|---|---|
| Alta del usuario | `CONSENTIMIENTO` | Aviso breve de tratamiento de datos + enlace para autorizar | No (automático) |
| Asignación del macrociclo | `BIENVENIDA` | Bienvenida + PDF del programa adjunto | Sí |
| Mitad del ciclo | `CHECKIN_MITAD` | **Una sola pregunta**: "¿cómo va? (1-10)" | Sí |
| **14 días antes del fin** | `ENCUESTA_T14` | Cuestionario completo (doc 08) | **Sí, obligatoria** |
| Fin del ciclo | `CIERRE_CICLO` | Resumen + propuesta del siguiente ciclo | Sí |

Eliminado respecto a la propuesta inicial: el correo de "14 días sin actividad"
(no procede sin registro de asistencia).

El `CHECKIN_MITAD` es configurable: se puede desactivar por completo desde
`T_CONFIG` si resulta demasiado.

## Cola de revisión: nada sale a ciegas

Requisito expreso del entrenador: antes de enviar, quiere verlo y **añadir su
impresión personal**, que se integra en el cuerpo del correo.

Flujo:

```
1. DETECCIÓN   Al arrancar la aplicación (y con un botón "revisar avisos"),
               se recorren las asignaciones EN_CURSO y se comparan las fechas
               de T_ASIG_FASES con hoy. Los que cumplen la condición generan
               una fila en T_COLA_MAIL con estado BORRADOR.

2. AVISO       El panel de inicio muestra: "3 correos pendientes de revisión".

3. REDACCIÓN   Ventana "Bandeja de salida": lista de borradores. Al seleccionar
               uno se ve el cuerpo ya montado con los datos del usuario y un
               campo de texto libre: "Tu impresión personal sobre este usuario".
               Lo que escriba ahí sustituye al marcador {{nota_entrenador}}
               dentro del cuerpo, en un bloque destacado.

4. VISTA PREVIA Se renderiza el HTML final, tal cual lo va a recibir el usuario.
               Botón "Enviarme una copia de prueba a mí mismo".

5. APROBACIÓN  Estado -> REVISADO. Se pueden aprobar varios y enviar en lote.

6. ENVÍO       Estado -> ENVIADO con fecha/hora. Si falla, -> ERROR con el
               mensaje, y se puede reintentar sin volver a redactar.
```

Ventaja añadida: si un día no abre la aplicación, nada se pierde. Los borradores
se acumulan y al abrir aparecen todos, con su fecha prevista marcada en rojo si
van con retraso.

## El arranque del correo

La idea original era abrir el correo con los datos de progreso del usuario, que
en esta fase no existen (no se registra lo ejecutado). Con lo que **sí** hay se
puede construir un arranque igualmente personal:

- La fase del plan en la que está: *"has completado el mesociclo de acumulación
  de tu plan de 24 semanas"*.
- Los datos de su valoración física, si se le ha hecho un seguimiento: *"en la
  revisión de marzo tu sentadilla estimada pasó de 60 a 72 kg"*.
- Su objetivo declarado, citado literalmente: da sensación de trato individual y
  encadena con la pregunta de si lo mantiene.
- **Y sobre todo la nota del entrenador**, que es la parte que ningún dato
  sustituye.

Cuando en fase 2 se registre lo ejecutado, el bloque de progreso se rellena con
datos reales automáticamente.

## Cuestionarios: Google Forms

### Identificación del que responde (clave)

El formulario incluye un campo **oculto prerrellenado** con el `ID_Usuario` y el
`ID_Envio`. Se consigue con la URL de "respuesta prerrellenada" de Google Forms:

```
https://docs.google.com/forms/d/e/XXXX/viewform?usp=pp_url&entry.123456789=USR-0042&entry.987654321=ENV-0311
```

La aplicación genera ese enlace para cada usuario al montar el correo y lo guarda
en `T_COLA_MAIL.Enlace_Form_Prefill`. Así el usuario no tiene que escribir su
nombre ni su correo, y cada respuesta queda vinculada sin ambigüedad al envío que
la provocó.

### Importación de respuestas

Google Forms vuelca las respuestas a una hoja de cálculo de Google. Dos vías:

| Vía | Cómo | Valoración |
|---|---|---|
| **A. Cuenta de servicio** (recomendada) | Proyecto gratuito en Google Cloud, cuenta de servicio, se comparte la hoja de respuestas con su correo, la aplicación lee con `gspread` | Automática, botón "Importar respuestas". Configuración inicial de ~15 min, una sola vez |
| **B. CSV manual** | Descargar el CSV de respuestas y arrastrarlo a la aplicación | Cero configuración, pero un paso manual cada vez |

Se implementarán **las dos**: B como respaldo permanente, A como camino normal.

> Descartada la opción de "publicar la hoja en la web" como CSV público: la URL es
> accesible sin autenticación y contendría datos personales de salud.

### Recordatorio

A los 4-5 días del envío, solo a quien no ha respondido (se sabe cruzando
`T_COLA_MAIL` con `T_RESPUESTAS`). Genera un borrador nuevo en la cola, con
revisión igualmente.

### Cierre del bucle

Al importar una respuesta se genera un borrador de agradecimiento: *"recibido,
ya estoy preparando tu siguiente ciclo"*. El silencio tras responder es lo que
hace que a la siguiente no respondan.

## Consentimiento de datos

Al dar de alta un usuario, correo automático breve (sin muro legal) con un
enlace a un **formulario de consentimiento de Google** de una sola pregunta, con
el `ID_Usuario` prerrellenado:

> *"Autorizo a [nombre del gimnasio] a guardar y tratar mis datos personales y
> los datos físicos y de salud necesarios para diseñar y seguir mi
> entrenamiento. Puedo revocar esta autorización en cualquier momento
> escribiendo a [correo]."*
> — [ ] Autorizo  [ ] No autorizo

Al importar, se marca `Consentimiento_SN` y `F_Consentimiento` en `T_USUARIOS`.

Por qué formulario y no un botón en el correo: un botón que escriba en el sistema
necesitaría un servidor propio, que no tenemos. Y el formulario tiene una ventaja
adicional: deja **constancia con fecha y hora** de la autorización, que es
exactamente lo que el RGPD exige poder demostrar. El botón `mailto:` no deja
prueba tan limpia.

El panel de inicio muestra una alerta con los usuarios **sin consentimiento
registrado**, y la aplicación advierte al intentar enviarles cualquier otro
correo.

Alternativa si se prefiere no usar un segundo formulario: la autorización se
recoge en papel/presencialmente y se marca a mano en la ficha
(`Origen_Consentimiento = PRESENCIAL`). Ambas vías quedan soportadas.

## Reserva de cita: pendiente de definir

Es la pieza que falta por cerrar. Sin servidor propio, las opciones son:

| Opción | Cómo funciona | Pros y contras |
|---|---|---|
| **1. Dentro del propio formulario** | Una pregunta más: *"¿quieres que te llame para preparar tu siguiente ciclo?"* + *"indica dos franjas que te encajen"*. Genera una alerta en el panel | Cero herramientas nuevas, todo en el flujo existente. El entrenador cierra la cita por teléfono. **Recomendada para empezar** |
| **2. Google Calendar - Citas** | Página de reserva con la disponibilidad real; el usuario elige hueco | Buena experiencia, pero la función de horarios de citas es de Google Workspace (cuenta de pago) |
| **3. Calendly (plan gratuito)** | Enlace de reserva en el correo | Funciona bien y es gratis en su nivel básico, pero es un servicio externo más, y la cita no vuelve automáticamente al Excel |

Propuesta: empezar por la **1**, y evaluar la **2** o la **3** cuando el flujo
esté rodado y se sepa cuánta gente pide cita de verdad.
