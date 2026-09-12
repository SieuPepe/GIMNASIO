# 10 — Decisiones abiertas

## Cerradas en esta ronda

| Punto | Decisión |
|---|---|
| Hardware | i5-1235U · 16 GB · sin GPU → IA local troceada + generador por reglas ([03](03-arquitectura.md#hardware-de-destino-y-qué-implica), [07](07-modulo-ia.md#el-hardware-manda-i5-1235u-16-gb-sin-gpu)) |
| Correo | Google Forms confirmado. Cuenta de Gmail personal. Se creará proyecto en Google Cloud con cuenta de servicio |
| Credenciales | Fichero `.env` con contraseña de aplicación, fuera del repositorio |
| Revisión de correos | Vista previa del correo ya interpretado por la IA → aprobar → enviar |
| Modo vacaciones | Aprobado, con caducidad obligatoria y tope diario |
| Cita | Sin reserva de horario. Solo confirmación de interés + indicación del horario de sala |
| Valoración | Varias plantillas (protocolos). Fuerza por técnica salvo dinamómetro. Quitado el test de abdominales. Añadidos *reverse plank*, *side plank*, *step down*, *pull up*, Sorensen, zancada y *scratch test*. Anexo de baremos por sexo y edad |
| Catálogo y plantillas | No existen propios → los preparamos nosotros como carga inicial |

---

## Abiertas

### 1. Validación de la batería de valoración (lo más urgente)

Necesita tu revisión como entrenador, en dos puntos concretos:

**a) Clasificación de las pruebas isométricas.** Plancha lateral, plancha
invertida y Sorensen las he dejado como **cronometradas** (`CUANTITATIVA`), porque
es lo que son y porque las *relaciones* entre ellas son su aportación más valiosa
(detectan desequilibrio flexores/extensores y asimetría derecha-izquierda). Tú
dijiste que en fuerza la valoración inicial es de técnica. ¿Las quieres
cronometradas, por técnica, o ambas cosas? Se cambia con una celda del catálogo.

**b) Los baremos del [Anexo 11](11-anexo-baremos.md).** Son valores orientativos
recopilados de referencias de uso habitual, con su solidez indicada prueba por
prueba. Hay que revisarlos. En particular, los marcados como **solidez baja** —
plancha frontal, dominada y suspensión, escala de *scratch test* para adultos
jóvenes — y la **plancha invertida, que no tiene baremo publicado** y por ahora
solo sirve como comparación del usuario consigo mismo. Si tienes tablas propias o
de referencia que uses, son mejores que estas.

### 2. Protocolos de valoración definitivos

He propuesto seis plantillas ([05](05-valoracion-fisica.md#protocolos-de-partida-propuestos)):
estándar adulto activo, principiante/sedentario, mayor de 65, reincorporación tras
lesión, rendimiento y revisión rápida. ¿Son los perfiles que realmente ves en tu
sala? ¿Falta alguno (embarazo y posparto, población con patología metabólica)?
¿Sobra alguno?

### 3. Modelo de IA local

Hay que **medir en tu equipo**, no decidir sobre el papel. Candidatos:
`qwen2.5:7b-instruct`, `llama3.1:8b-instruct`, `mistral:7b-instruct`.
¿Tienes ya Ollama instalado? Si no, es el primer paso del módulo de IA, y la
pantalla de diagnóstico de la aplicación dará los datos para elegir.

### 4. Identidad visual de los PDF

Logotipo, nombre comercial, colores y pie de página con datos de contacto. Hace
falta para los informes de valoración y para los programas de entrenamiento. Un
PNG del logo y tres datos bastan para empezar.

### 5. Horario de sala

Para el correo de confirmación de cita hace falta el texto del horario en que
estás en sala (`config.toml`). ¿Cuál es?

### 6. Datos existentes

¿Hay usuarios en algún Excel o cuaderno que haya que migrar, o se empieza de cero?
Si hay algo, conviene verlo antes de fijar los campos definitivos.

### 7. Texto del consentimiento

El texto de la solicitud debería revisarlo alguien con criterio legal. Se pidió
que sea breve y sin muro legal, lo cual es razonable, pero conviene que lo que se
envíe sea suficiente: se tratan datos de salud, que el RGPD considera de categoría
especial. Hay un borrador en
[04](04-comunicaciones-email.md#consentimiento-de-datos).

### 8. Nombre de la aplicación

Aparecerá en la ventana, en los PDF y en los correos. Por ahora está como
"GIMNASIO".
