# 01 — Visión y alcance

## Objetivo

Herramienta de trabajo diario para el entrenador: mantener la ficha de cada
usuario, valorarlo físicamente, diseñar su planificación en ciclos, entregársela
en PDF y mantener con él una conversación periódica por correo que sirva tanto
para ajustar el entrenamiento como para que renueve.

## Dentro del alcance (fase actual)

1. **Usuarios**: ficha básica, objetivos, disponibilidad, salud y limitaciones.
2. **Consentimiento de datos**: solicitado por correo al dar de alta, con
   registro de la respuesta en el sistema.
3. **Valoración física**: batería de test en el alta y repetible en cualquier
   momento, con baremos e informe en PDF para el usuario.
4. **Catálogo de ejercicios**: base para que los programas sean datos y no texto.
5. **Planificación en árbol**: macrociclo → mesociclos → microciclos → sesiones
   → ejercicios. Un macrociclo contiene **varios** mesociclos, y cada mesociclo
   **varios** microciclos.
6. **Plantillas y clonado** de ciclos completos.
7. **Asignación**: al dar de alta un usuario se le asigna un macrociclo completo,
   con fecha de inicio; las fechas de cada fase se derivan de las duraciones.
8. **Cálculo automático de cargas** a partir del 1RM y progresiones.
9. **PDF a demanda** con el programa asignado, para el usuario.
10. **Correo automatizado** con cola de revisión previa del entrenador.
11. **Cuestionario de satisfacción** a T-14 días vía Google Forms, con
    importación de respuestas.
12. **Generación de ciclos con IA** (Ollama local u otro proveedor), en bucle
    iterativo de propuesta → feedback → nueva propuesta → aceptación.
13. **Base de conocimiento editable** para "enseñar" a la IA los criterios
    propios del entrenador.
14. **Panel de inicio con alertas** y **copia de seguridad automática**.

## Fuera del alcance (más adelante)

- Registro de lo **ejecutado** por el usuario (asistencia, cargas reales,
  adherencia). Ahora solo se registra lo **prescrito**.
- Gestión administrativa: cuotas, facturación, control de acceso, altas/bajas
  contractuales.
- Acceso del usuario a la aplicación. El usuario solo recibe correos y PDF.
- Multiusuario, red, nube.
- App móvil.

## Decisiones ya cerradas

| Punto | Decisión |
|---|---|
| Entorno | Windows, PC local, un solo operador |
| Almacenamiento | Libro Excel `.xlsx` como base de datos |
| Aplicación | Ejecutable independiente (no macros de Excel) |
| Volumen | ~100 usuarios activos |
| Correo | SMTP directo de Gmail (sin depender de Outlook) |
| Cuestionarios | Google Forms, enlazado desde el correo |
| Envío de correos | Nunca automático a ciegas: pasa por revisión del entrenador |
| Asignación | Macrociclo completo en el momento del alta |
| Entrega al usuario | PDF a demanda mediante botón |
