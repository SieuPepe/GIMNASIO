# 09 — Hoja de ruta

Orden pensado para que en cada fase haya algo **utilizable**, no un esqueleto a
medias. Las estimaciones son de esfuerzo relativo, no de calendario.

## Fase 0 — Cimientos
- Estructura del proyecto, configuración, log, copias de seguridad.
- Generador del libro `datos_gimnasio.xlsx` con todas las hojas y cabeceras.
- Capa `datos/`: lectura, escritura atómica, IDs, validación de esquema.
- Ventana principal vacía con su navegación.

**Resultado:** el libro existe y la aplicación arranca. Sin esto nada más es posible.
**Hecha.**

## Fase 1 — Usuarios
- Ficha de usuario: alta, edición, búsqueda, listado.
- Ventanas independientes de **objetivos**, **salud/PAR-Q+** y **disponibilidad**.
- Marca de consentimiento (manual en esta fase).

**Resultado:** ya se puede meter la cartera de usuarios real. Utilizable desde el
primer día, y los datos que se metan ahora sirven para todo lo demás.
**Hecha.**

## Fase 2 — Catálogo de ejercicios
- Catálogo con patrón, grupo, material, nivel, incremento de carga, vídeo.
- **Carga inicial preparada por nosotros:** no hay listado propio de partida, así
  que se entrega un catálogo de ~100 ejercicios habituales ya clasificados por
  patrón, grupo muscular, material, nivel e incremento de carga, importable y
  editable. El entrenador revisa, quita y añade.

**Resultado:** la base sin la cual los programas serían texto libre.
**Hecha.** 127 ejercicios de partida. Detalle en [13](13-catalogo-ejercicios.md).

## Fase 3 — Valoración física
- Catálogo de test, **protocolos (plantillas de valoración)** y baremos editables.
- Carga inicial de los baremos del [Anexo 11](11-anexo-baremos.md) con un botón.
- Pruebas de técnica con escala 0-3 y criterios observables.
- Ventana de valoración con cálculo de puntuaciones y categorías.
- Cribado PAR-Q+ con bloqueo de test máximos.
- Informe en PDF con radar y comparativa.
- Alimentación automática de `T_1RM` desde los test de fuerza.

**Resultado:** el primer entregable de valor para el usuario. Ya se le puede dar
algo en la mano.

## Fase 4 — Planificación
- Árbol de ciclos: macro → meso → micro, con `ID_Padre`.
- Editor de sesiones y de líneas de ejercicio.
- Plantillas, clonado y duplicado de ciclos.
- **Plantillas de macrociclo de partida preparadas por nosotros** (tampoco hay
  propias): 3 o 4 estructuras tipo — principiante 12 semanas, hipertrofia 16,
  fuerza 16, salud general 12 — para tener de qué partir el primer día.
- Cálculo de cargas, redondeo y progresiones (documento 06).
- Asignación de macrociclo a usuario y cálculo del calendario de fases.
- **PDF del programa a demanda.**

**Resultado:** el núcleo del negocio. Con las fases 0 a 4 la herramienta ya
sustituye a las hojas suelta y a los planes en Word.

## Fase 5 — Comunicación
- Envío SMTP con credencial en el almacén de Windows.
- Plantillas de correo con marcadores.
- Detección de disparadores y **cola de revisión** con nota personal.
- Formularios de Google: generación de enlaces prerrellenados.
- Importación de respuestas (CSV y cuenta de servicio).
- Correo y formulario de consentimiento.
- Recordatorios y agradecimiento.
- **Modo vacaciones** con sus salvaguardas.

**Resultado:** el requisito del aviso a T-14 días, cerrado de punta a punta.

## Fase 6 — Panel y alertas
- Pantalla de inicio: programas que vencen en menos de 14 días, usuarios sin
  programa activo, sin consentimiento, sin 1RM necesario, valoraciones caducadas,
  correos pendientes de revisar, encuestas sin responder, molestias declaradas,
  citas solicitadas.

**Resultado:** deja de haber que acordarse de nada.

## Fase 7 — IA
- Capa de proveedor + Ollama, con pantalla de diagnóstico de modelos.
- **Generador determinista por reglas** (base sobre la que trabaja la IA).
- Redacción de correos con IA (se adelanta a la fase 5, porque es la tarea corta
  y no depende del resto del módulo).
- Expediente seudonimizado del usuario.
- Generación con esquema JSON y validador estricto.
- Bucle iterativo con feedback.
- Ventana "Enseñar a la IA": reglas y conocimiento.
- Propuesta de aprendizaje a partir de las correcciones.

**Resultado:** lo que hace que este software no sea uno más.

## Fase 8 — Empaquetado
- PyInstaller, instalador, manual breve de uso.
- Prueba en el PC real de destino.

## Más adelante (fuera de esta planificación)
- Registro de lo **ejecutado**: asistencia, cargas reales, adherencia medida.
  Desbloquea el bloque de progreso real en los correos y multiplica la calidad de
  los datos para la IA.
- Gestión administrativa: cuotas, altas y bajas.
- Gráficas generales de evolución por usuario.
- Semáforo de riesgo de abandono.
- Selección de conocimiento por similitud semántica (*embeddings*).
