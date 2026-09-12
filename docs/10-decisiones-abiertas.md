# 10 — Decisiones abiertas

## Cerradas en esta ronda

| Punto | Decisión |
|---|---|
| Hardware de referencia | i5-1235U · 16 GB · sin GPU → IA local troceada + generador por reglas. El equipo final será otro, aún sin definir |
| Marca | Nombre comercial **ZEU**, lema *Enjoy your process*. Paleta y aplicación en [12](12-marca.md) |
| Horario de sala | Lunes a sábado 07:00-21:00 · Domingo 07:00-14:00 |
| Pruebas añadidas | *Sit-to-Stand* / *Chair Stand* en fuerza y escalón de Harvard en resistencia, ambas con sus tablas |
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

### 3. Equipo de destino final

El PC donde va a trabajar la aplicación será otro y aún no está definido. No
bloquea nada: el diseño está pensado sobre el equipo actual como suelo, así que
cualquier máquina igual o mejor lo mueve igual o mejor. Pero **sí condiciona
cuánto rinde el módulo de IA**, así que conviene saberlo antes de la fase 7.

Si hay margen para elegir, lo único que cambia la IA de forma cualitativa es una
**GPU dedicada con 8 GB de memoria de vídeo o más**: permite modelos bastante
mejores y multiplica la velocidad por un factor grande, con lo que la generación
completa pasaría de decenas de minutos a unos pocos. El resto de componentes
(procesador, disco) apenas influyen; 32 GB de RAM ayudarían si no hay GPU.

Si no hay margen, no pasa nada: el generador determinista por reglas y el modo
"refinar" de la IA están pensados justamente para funcionar sin GPU.

### 4. Modelo de IA local

Ollama ya está instalado en el equipo actual, así que se puede empezar a medir
cuando queramos. Candidatos: `qwen2.5:7b-instruct`, `llama3.1:8b-instruct`,
`mistral:7b-instruct`. La pantalla de diagnóstico de la aplicación dará velocidad
y porcentaje de respuestas válidas de cada uno con los mismos casos de prueba.

### 5. Ficheros de marca y datos de contacto

Falta subir el logotipo al repositorio, en `assets/marca/` (ver
[12](12-marca.md)). Se necesita una versión con **fondo transparente**: el fichero
recibido tiene fondo gris sólido y en una cabecera sobre papel blanco recortaría
un rectángulo.

También faltan los datos de contacto que van en el pie de informes y correos:
dirección, teléfono, correo y web.

Y confirmar la **paleta**: los hex del documento 12 están tomados a ojo del
logotipo. Si existe el fichero de diseño con los valores exactos, mejor.

### 6. Datos existentes

¿Hay usuarios en algún Excel o cuaderno que haya que migrar, o se empieza de cero?
Si hay algo, conviene verlo antes de fijar los campos definitivos.

### 7. Texto del consentimiento

El texto de la solicitud debería revisarlo alguien con criterio legal. Se pidió
que sea breve y sin muro legal, lo cual es razonable, pero conviene que lo que se
envíe sea suficiente: se tratan datos de salud, que el RGPD considera de categoría
especial. Hay un borrador en
[04](04-comunicaciones-email.md#consentimiento-de-datos).

### 8. Altura de silla y escalón

Para que las mediciones sean comparables entre valoraciones hay que fijar y anotar
el material: **altura de la silla** del *sit-to-stand* (estándar 43-45 cm) y
**altura del escalón** del Harvard (50 cm hombres / 43 cm mujeres). ¿Qué tienes
disponible en sala? Si no coincide con el estándar, se anota en el protocolo del
test y se tiene en cuenta al interpretar.
