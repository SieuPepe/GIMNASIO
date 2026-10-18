"""Texto de la ayuda: una página por ventana, más los capítulos del manual.

Todo el texto vive aquí y no dentro de las ventanas, por dos razones: se puede
leer y corregir de un tirón sin tocar la interfaz, y la misma página sirve para
el botón «?» de la ventana y para el manual, sin escribirla dos veces.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Control:
    """Un botón, un campo o una casilla de la ventana."""
    nombre: str
    que_hace: str


@dataclass(frozen=True)
class Problema:
    sintoma: str
    solucion: str


@dataclass(frozen=True)
class Ayuda:
    """La página de ayuda de una ventana."""
    clave: str
    titulo: str
    donde: str
    para_que: str
    controles: tuple[Control, ...] = ()
    flujo: tuple[str, ...] = ()
    reglas: tuple[str, ...] = ()
    problemas: tuple[Problema, ...] = ()
    ver_tambien: tuple[str, ...] = ()
    seccion: str | None = None      # sección a la que puede saltar el manual
    recorrido: str | None = None    # recorrido guiado asociado

    def texto_buscable(self) -> str:
        partes = [self.titulo, self.donde, self.para_que]
        partes += [f"{c.nombre} {c.que_hace}" for c in self.controles]
        partes += list(self.flujo) + list(self.reglas)
        partes += [f"{p.sintoma} {p.solucion}" for p in self.problemas]
        return " ".join(partes)


@dataclass(frozen=True)
class Pagina:
    """Un capítulo del manual que no describe una ventana concreta."""
    clave: str
    titulo: str
    cuerpo: str
    seccion: str | None = None
    recorrido: str | None = None

    def texto_buscable(self) -> str:
        return f"{self.titulo} {self.cuerpo}"


@dataclass(frozen=True)
class Capitulo:
    titulo: str
    entradas: tuple[str, ...]
    resumen: str = ""


# ====================================================================== ventanas

VENTANAS: tuple[Ayuda, ...] = (
    Ayuda(
        clave="inicio",
        titulo="Panel de inicio",
        donde="Primer botón de la barra lateral. Es lo que ves al abrir el programa.",
        para_que=(
            "Es la lista de lo que reclama tu atención hoy. La idea es que no "
            "tengas que acordarte de nada: si algo hay que hacer, aparece aquí. "
            "Si el panel está vacío, no hay nada pendiente."),
        controles=(
            Control("Lista de avisos",
                    "Cada fila es un aviso con su gravedad en color: rojo lo que "
                    "no puede esperar, ámbar lo que conviene mirar y azul lo "
                    "meramente informativo."),
            Control("Actualizar",
                    "Vuelve a calcular los avisos. El panel ya se recalcula solo "
                    "cada vez que guardas algo, así que casi nunca hace falta."),
            Control("Buscar avisos de correo",
                    "Revisa qué programas terminan pronto y prepara los borradores "
                    "de correo que toquen. Lo que encuentre va a la bandeja de "
                    "salida, sin enviar nada todavía."),
            Control("Solo lo que requiere atención",
                    "Esconde los avisos informativos y deja lo que hay que resolver."),
            Control("Abrir",
                    "Lleva a la ventana del aviso con la persona ya señalada. Es "
                    "el camino corto: del aviso a la ficha en un clic."),
            Control("Marcar como atendida",
                    "Solo para los avisos de hecho puntual, como una molestia que "
                    "ha declarado un usuario en la encuesta. Dice «ya lo he visto», "
                    "y el aviso desaparece."),
        ),
        reglas=(
            "Hay dos clases de aviso y se comportan distinto. Los <b>de estado</b> "
            "(sin consentimiento, sin programa, programa que vence) desaparecen "
            "solos cuando resuelves la causa: no hay que marcarlos. Los <b>de hecho "
            "puntual</b> (una molestia declarada, una cita solicitada) no se van "
            "solos porque el hecho ya ocurrió; esos se marcan como atendidos.",
            "Si un aviso de estado no se va después de resolverlo, pulsa "
            "«Actualizar». Si sigue ahí, es que la causa no está resuelta.",
        ),
        ver_tambien=("correo", "usuarios"),
        seccion="inicio",
        recorrido="primer_dia",
    ),
    Ayuda(
        clave="usuarios",
        titulo="Usuarios",
        donde="Segundo botón de la barra lateral.",
        para_que=(
            "El listado de las personas que entrenan contigo y la puerta a todo "
            "lo suyo: datos personales, objetivos, salud y disponibilidad."),
        controles=(
            Control("Buscar por nombre, apellidos o correo",
                    "Filtra la lista a medida que escribes. No distingue "
                    "mayúsculas ni acentos."),
            Control("Todos los estados",
                    "Filtra por activo, en pausa o baja."),
            Control("Columna «Pendiente»",
                    "Resume de un vistazo qué le falta a esa persona: "
                    "consentimiento, objetivo, programa, valoración. Pasa el ratón "
                    "por encima y el detalle completo sale en un rótulo."),
            Control("Nuevo usuario",
                    "Abre la ficha vacía para dar de alta a alguien."),
            Control("Editar ficha",
                    "Abre la ficha de la persona elegida. También se consigue "
                    "haciendo doble clic en su fila."),
            Control("Objetivos",
                    "Historial de objetivos. Se añaden, no se sobreescriben: así "
                    "queda registrado cómo ha ido cambiando lo que busca."),
            Control("Salud",
                    "Historial de revisiones: tensión, frecuencia cardíaca, "
                    "patologías, medicación, lesiones y el resultado del cribado."),
            Control("Disponibilidad",
                    "Días por semana, duración de sesión, lugar y material. Es lo "
                    "que condiciona qué programa tiene sentido asignarle."),
            Control("Borrar",
                    "Solo funciona si la persona no tiene nada colgando. Si tiene "
                    "objetivos, salud, valoraciones o programas, el programa se "
                    "niega y te dice qué lo impide: en ese caso lo correcto es "
                    "ponerla en estado «baja», no borrarla."),
        ),
        flujo=(
            "«Nuevo usuario» y rellena nombre, fecha de nacimiento y sexo: son "
            "obligatorios porque sin ellos no hay baremos que aplicar.",
            "Registra el consentimiento, o deja que lo firme por el formulario.",
            "Añade su primer objetivo desde «Objetivos».",
            "Registra la revisión de salud desde «Salud»: el cribado se calcula ahí.",
            "Anota su disponibilidad.",
            "Ya puedes valorarlo y asignarle un programa.",
        ),
        reglas=(
            "La edad no se guarda, se calcula desde la fecha de nacimiento. Por eso "
            "los baremos de la valoración siguen siendo correctos el año que viene.",
            "Dar de baja no borra nada: el histórico se conserva entero.",
        ),
        problemas=(
            Problema("No me deja borrar a alguien",
                     "Es a propósito: tiene registros que dependen de él. Cámbialo "
                     "a estado «baja»."),
            Problema("No recibe correos",
                     "Revisa tres cosas en su ficha: que tenga correo escrito, que "
                     "«Acepta recibir correos» esté marcado y que el consentimiento "
                     "esté registrado."),
        ),
        ver_tambien=("ficha_usuario", "objetivos", "salud", "disponibilidad"),
        seccion="usuarios",
        recorrido="alta_usuario",
    ),
    Ayuda(
        clave="ejercicios",
        titulo="Catálogo de ejercicios",
        donde="Tercer botón de la barra lateral.",
        para_que=(
            "El almacén de ejercicios del que tiran todos los programas. Viene "
            "cargado con 127 ejercicios; puedes añadir los tuyos."),
        controles=(
            Control("Buscar por nombre", "Filtra mientras escribes."),
            Control("Patrón / Grupo / Material",
                    "Tres filtros que se acumulan. Sirven para responder preguntas "
                    "como «qué empujes horizontales tengo con mancuernas»."),
            Control("Solo activos",
                    "Viene marcado. Al desmarcarlo aparecen también los retirados, "
                    "en gris."),
            Control("Solo básicos",
                    "Deja los ejercicios troncales, los que forman el esqueleto de "
                    "un programa."),
            Control("Aviso de cobertura",
                    "A la derecha de las casillas. Avisa de qué patrones de "
                    "movimiento se quedan sin ningún ejercicio con el filtro "
                    "puesto. Es la forma de detectar un hueco en el catálogo."),
            Control("Nuevo ejercicio", "Abre la ficha vacía."),
            Control("Editar", "Abre la ficha del ejercicio elegido. Doble clic vale."),
            Control("Ver sustitutos",
                    "Propone ejercicios equivalentes por patrón y grupo muscular, y "
                    "puede acotarlos al material que tenga la persona. Es lo que "
                    "resuelve «hoy la máquina está ocupada»."),
            Control("Activar / desactivar",
                    "Retira un ejercicio sin borrarlo: deja de ofrecerse para "
                    "programas nuevos, pero los programas que ya lo usan siguen "
                    "intactos."),
            Control("Importar desde CSV",
                    "Carga ejercicios desde un fichero. Te pregunta si quieres "
                    "sobreescribir los que ya existen o solo añadir los que falten."),
        ),
        reglas=(
            "Los botones «Editar», «Ver sustitutos» y «Activar / desactivar» "
            "necesitan una fila elegida. Si no hay ninguna, se ven en gris claro.",
            "Un ejercicio nunca se borra del todo si algún programa lo usa: se "
            "desactiva. Así no se rompe el historial de nadie.",
        ),
        ver_tambien=("ficha_ejercicio", "sustitutos"),
        seccion="ejercicios",
    ),
    Ayuda(
        clave="valoraciones",
        titulo="Valoraciones físicas",
        donde="Cuarto botón de la barra lateral.",
        para_que=(
            "Registra las valoraciones y saca el informe en PDF. Cada valoración "
            "sigue un protocolo —un guion de pruebas— y guarda, además del dato "
            "medido, en qué categoría cae según las tablas por sexo y edad."),
        controles=(
            Control("Usuario",
                    "Filtra el listado. Arranca en «todos»."),
            Control("Columna «Global»",
                    "La puntuación de conjunto, coloreada. Solo promedia las "
                    "capacidades que de verdad has medido: lo que no se mide no "
                    "cuenta como cero."),
            Control("Columna «Hallazgos»",
                    "Cuántas asimetrías o desequilibrios ha detectado. El detalle "
                    "de los tres primeros aparece bajo la tabla al elegir la fila."),
            Control("Nueva valoración",
                    "Pregunta a quién vas a valorar y qué protocolo seguir."),
            Control("Abrir / editar",
                    "Vuelve a la valoración elegida para completarla o corregirla."),
            Control("Generar informe PDF",
                    "Saca el informe con el gráfico de radar, las tablas de "
                    "referencia y los hallazgos, y te ofrece abrirlo."),
        ),
        reglas=(
            "La fuerza se valora por <b>técnica</b>, no por kilos: una escala de 0 "
            "a 3 donde 0 significa dolor. La única prueba de fuerza con unidades "
            "es la dinamometría.",
            "Si una prueba no tiene tabla de referencia para ese sexo y esa edad, "
            "el informe lo dice («sin baremo») en lugar de inventarse una "
            "categoría.",
            "Las asimetrías izquierda/derecha se miran en porcentaje, salvo en las "
            "escalas con signo, donde se miran en unidades absolutas.",
        ),
        problemas=(
            Problema("No hay protocolos cargados",
                     "Ejecuta <tt>python herramientas/importar_valoracion.py</tt> "
                     "una vez y vuelve a entrar."),
            Problema("El radar sale con huecos",
                     "Es correcto: solo dibuja las capacidades medidas. Un cero "
                     "falso daría una imagen peor que la real."),
        ),
        ver_tambien=("valoracion", "criterios"),
        seccion="valoraciones",
        recorrido="valoracion",
    ),
    Ayuda(
        clave="programas",
        titulo="Programas de entrenamiento",
        donde="Quinto botón de la barra lateral.",
        para_que=(
            "Donde se construyen las plantillas de entrenamiento. Son plantillas, "
            "no entrenamientos de nadie: el programa se escribe una vez y se "
            "asigna a quien haga falta, cuantas veces haga falta."),
        controles=(
            Control("Árbol de ciclos (izquierda)",
                    "La estructura completa: macrociclo → mesociclos → "
                    "microciclos. Al elegir un microciclo aparecen sus sesiones. "
                    "La columna <b>Orden</b> enseña el puesto de cada ciclo entre "
                    "sus hermanos, que es el que fija la secuencia; si sale en "
                    "rojo, hay dos hermanos con el mismo número y conviene "
                    "arreglarlo. Los macrociclos se ordenan por nombre, así que "
                    "ahí la columna va vacía."),
            Control("Nuevo macrociclo", "Crea un programa nuevo, vacío."),
            Control("Añadir dentro",
                    "Crea un ciclo hijo del elegido: dentro de un macrociclo crea "
                    "un mesociclo, y dentro de un mesociclo un microciclo. El "
                    "programa no te deja saltarte un nivel."),
            Control("Editar / Clonar / Borrar",
                    "Sobre el ciclo elegido. «Clonar» copia el ciclo con todo lo "
                    "que cuelga de él —sesiones y ejercicios incluidos—, que es la "
                    "forma rápida de hacer la semana 2 a partir de la semana 1."),
            Control("Sesiones (centro)",
                    "Las sesiones del microciclo elegido, con su día de la semana."),
            Control("Nueva sesión / Editar sesión / Borrar sesión",
                    "Sobre la lista de sesiones."),
            Control("Ejercicios de la sesión (abajo)",
                    "Las líneas de la sesión elegida, en orden."),
            Control("Añadir ejercicio",
                    "Añade una línea: ejercicio, series, repeticiones, carga, "
                    "descanso y progresión."),
            Control("Editar / Subir / Bajar / Quitar",
                    "Sobre la línea elegida. «Subir» y «Bajar» cambian el orden en "
                    "que se imprime la sesión."),
            Control("Banda de avisos (abajo)",
                    "Señala incoherencias de la plantilla: un microciclo sin "
                    "sesiones, una sesión sin ejercicios, una carga que no se "
                    "podrá calcular por falta de 1RM."),
        ),
        flujo=(
            "«Nuevo macrociclo» con su nombre y su duración.",
            "Con el macrociclo elegido, «Añadir dentro» para cada mesociclo.",
            "Con un mesociclo elegido, «Añadir dentro» para cada microciclo "
            "(normalmente una semana).",
            "Con el microciclo elegido, «Nueva sesión» por cada día de entreno.",
            "Con la sesión elegida, «Añadir ejercicio» por cada línea.",
            "Para la semana siguiente, «Clonar» el microciclo y retocar.",
        ),
        reglas=(
            "La jerarquía es obligatoria: macro → meso → micro → sesión → "
            "ejercicio. No hay sesiones colgando de un mesociclo.",
            "Las progresiones se cuentan por <b>semana dentro del microciclo</b>, "
            "no por semana del plan. Un «LINEAL:+2.5» sube 2,5 kg por semana del "
            "micro, empiece el programa cuando empiece.",
            "Borrar un ciclo arrastra todo lo que cuelga de él, y no lo permite si "
            "hay una asignación que lo esté usando.",
        ),
        ver_tambien=("ciclo", "sesion", "linea", "asignaciones"),
        seccion="programas",
        recorrido="montar_programa",
    ),
    Ayuda(
        clave="asignaciones",
        titulo="Asignaciones",
        donde="Sexto botón de la barra lateral.",
        para_que=(
            "Donde un programa (la plantilla) se convierte en el entrenamiento de "
            "una persona con fechas concretas. Al asignar se congela el calendario: "
            "cada ciclo queda con su fecha de inicio y de fin."),
        controles=(
            Control("Estado",
                    "Filtro de <b>selección múltiple</b>: se despliega y se marcan "
                    "con casillas los estados que quieres ver. Arranca con "
                    "«Planificada» y «En curso» marcadas, que es lo que está vivo; "
                    "lo finalizado y lo interrumpido sigue ahí, a un clic. El "
                    "contador de arriba dice cuántas esconde el filtro."),
            Control("Ver todas",
                    "Marca los cuatro estados de golpe, sin ir casilla por casilla."),
            Control("Columna «Quedan»",
                    "Días hasta el final. Cuando baja de 14 el panel de inicio "
                    "empieza a pedir la encuesta de renovación."),
            Control("Columna «Fase actual»",
                    "En qué mesociclo y microciclo está esa persona hoy."),
            Control("Asignar programa",
                    "Elige persona, programa y fecha de inicio, y calcula el "
                    "calendario completo antes de guardarlo."),
            Control("Imprimir",
                    "Saca el PDF de las semanas que elijas, con las cargas ya "
                    "resueltas en kilos."),
            Control("Cambiar estado",
                    "Pasa la asignación a planificada, en curso, finalizada o "
                    "interrumpida."),
        ),
        reglas=(
            "El calendario se congela al asignar. Si luego cambias la plantilla, "
            "las asignaciones que ya existen no se mueven: eso es deliberado, "
            "porque si no cambiarías el entrenamiento de alguien sin querer.",
            "Una persona puede tener varias asignaciones, pero solo una en curso.",
        ),
        ver_tambien=("asignar", "imprimir", "programas"),
        seccion="asignaciones",
        recorrido="asignar",
    ),
    Ayuda(
        clave="correo",
        titulo="Bandeja de salida",
        donde="Séptimo botón de la barra lateral.",
        para_que=(
            "Todo el correo que el programa quiere enviar pasa por aquí y espera tu "
            "aprobación. Nunca sale nada que no hayas visto, salvo que enciendas "
            "el modo vacaciones."),
        controles=(
            Control("Tabla de envíos",
                    "Un envío por fila con su tipo, su estado y su fecha prevista. "
                    "En rojo los que han dado error, en naranja los que van tarde."),
            Control("Buscar avisos pendientes",
                    "Mira qué toca —programas que vencen, bienvenidas, "
                    "recordatorios— y crea los borradores."),
            Control("Tu impresión personal sobre este usuario",
                    "Lo que escribas aquí se integra en el cuerpo del correo. Es el "
                    "párrafo que hace que no parezca un correo automático."),
            Control("Actualizar vista previa",
                    "Vuelve a montar el correo con tu nota incorporada."),
            Control("Vista previa",
                    "El correo tal y como lo va a recibir la persona, con enlaces "
                    "y todo."),
            Control("Aprobar",
                    "Lo deja listo para salir, pero no lo envía todavía."),
            Control("Aprobar y enviar", "Lo aprueba y lo envía en el momento."),
            Control("Enviarme una prueba",
                    "Te lo manda a ti para verlo en el cliente de correo real "
                    "antes de mandárselo a nadie."),
            Control("Cancelar envío", "Descarta el borrador. No se enviará."),
            Control("Enviar todos los aprobados",
                    "Envía de una vez todo lo que ya tiene tu visto bueno."),
            Control("Plantillas de correo",
                    "Abre el editor de plantillas y de las URL de los formularios."),
            Control("Probar la conexión de correo",
                    "Comprueba que la cuenta y la contraseña de aplicación "
                    "funcionan. Úsalo antes de enviar nada real."),
            Control("Importar respuestas",
                    "Carga el CSV de respuestas del formulario de Google y las "
                    "interpreta: si alguien pide cita o declara una molestia, "
                    "aparece como aviso en el panel de inicio."),
            Control("Banda de modo vacaciones",
                    "Arriba, cuando está encendido. Recuerda que el correo puede "
                    "salir sin que tú lo apruebes."),
        ),
        reglas=(
            "Un correo nunca sale si la persona no tiene consentimiento registrado, "
            "no acepta correos o no tiene dirección. Eso no se puede desactivar.",
            "Si el correo lleva adjunto y el documento no se puede generar, el "
            "correo no se envía: antes eso dejaba una promesa sin cumplir.",
            "El modo vacaciones nunca envía lo que está en error, y sigue "
            "respetando el consentimiento.",
        ),
        problemas=(
            Problema("«Falta la credencial…» y el .env está escrito",
                     "El propio aviso dice ahora dónde ha buscado el fichero y qué "
                     "claves ha leído de él: eso suele resolverlo solo. Las dos "
                     "causas habituales son que el Bloc de notas haya guardado el "
                     "fichero como <tt>.env.txt</tt> (hay que elegir «Todos los "
                     "archivos» en el tipo de archivo) o que esté en otra carpeta. "
                     "El fichero tiene que estar junto a <tt>datos_krv.xlsx</tt>."),
            Problema("Falta la credencial GMAIL_APP_PASSWORD",
                     "Hay que crear una contraseña de aplicación en la cuenta de "
                     "Google y escribirla en el fichero <tt>.env</tt>. La "
                     "contraseña normal de la cuenta no sirve."),
            Problema("«No hay nada nuevo que enviar»",
                     "Correcto: ningún programa está a menos de 14 días del final "
                     "y no hay bienvenidas pendientes."),
            Problema("Un envío se queda en «sin enviar»",
                     "Pasa el ratón por la fila: el motivo del fallo está en el "
                     "rótulo. Suele ser la credencial o la falta de red."),
        ),
        ver_tambien=("plantillas", "inicio"),
        seccion="correo",
        recorrido="encuesta",
    ),
)

DIALOGOS: tuple[Ayuda, ...] = (
    Ayuda(
        clave="ficha_usuario",
        titulo="Ficha de usuario",
        donde="Usuarios → «Nuevo usuario» o «Editar ficha» (o doble clic en la fila).",
        para_que="Los datos personales, el estado y el consentimiento de una persona.",
        controles=(
            Control("Nombre *", "Obligatorio."),
            Control("Apellidos", "Opcional, pero la lista se ordena por aquí."),
            Control("Fecha de nacimiento *",
                    "Obligatoria: de ella sale la edad, y de la edad salen los "
                    "baremos de la valoración. Debajo se ve la edad calculada."),
            Control("Sexo *",
                    "Obligatorio por el mismo motivo: las tablas de referencia son "
                    "distintas para hombres y mujeres."),
            Control("Correo electrónico",
                    "Sin esto no hay correos. No es obligatorio, pero media "
                    "aplicación depende de él."),
            Control("Teléfono", "Opcional."),
            Control("Fecha de alta *", "Cuándo empezó. Por defecto, hoy."),
            Control("Estado *",
                    "Activo, en pausa o baja. «Baja» conserva todo el histórico y "
                    "es lo que hay que usar en vez de borrar."),
            Control("Acepta recibir correos",
                    "Si lo desmarcas, esa persona deja de recibir cualquier correo "
                    "automático, aunque tenga consentimiento firmado."),
            Control("Consentimiento",
                    "La casilla, la fecha y el origen. El origen dice si lo firmó "
                    "en papel, lo registraste tú a mano o llegó por el formulario."),
        ),
        reglas=(
            "Los campos con asterisco son obligatorios. Si falta alguno, al "
            "guardar sale una lista con lo que hay que corregir y no se pierde "
            "nada de lo escrito.",
            "La edad no se escribe: se calcula. Por eso no se queda vieja.",
        ),
        ver_tambien=("usuarios", "objetivos"),
    ),
    Ayuda(
        clave="objetivos",
        titulo="Objetivos",
        donde="Usuarios → «Objetivos».",
        para_que=(
            "El historial de lo que busca esa persona. Los objetivos se añaden, no "
            "se sobreescriben: así se ve cómo ha ido cambiando."),
        controles=(
            Control("Lista de arriba", "Los objetivos ya registrados, el último primero."),
            Control("Nuevo", "Vacía el formulario para añadir otro."),
            Control("Fecha *", "Cuándo se acordó."),
            Control("Tipo *",
                    "Fuerza, hipertrofia, resistencia, movilidad, salud, pérdida de "
                    "grasa, rendimiento. Es lo que luego orienta el programa."),
            Control("Descripción *", "En las palabras de la persona, si puede ser."),
            Control("Prioridad",
                    "1 es el principal. Sirve para ordenar cuando hay varios."),
            Control("Horizonte", "En cuántas semanas espera verlo."),
            Control("Métrica y Valor objetivo",
                    "Opcionales, para los objetivos que se pueden medir: «peso "
                    "muerto», «120». Sin esto el objetivo sigue valiendo, pero no "
                    "se puede comprobar."),
            Control("Estado *",
                    "Activo, conseguido o abandonado. Solo los activos cuentan como "
                    "objetivo vigente en el panel de inicio."),
            Control("Guardar registro", "Añade el objetivo al historial."),
        ),
        ver_tambien=("usuarios", "ficha_usuario"),
    ),
    Ayuda(
        clave="salud",
        titulo="Salud y cribado",
        donde="Usuarios → «Salud».",
        para_que=(
            "La revisión de salud y el cribado previo: si esa persona puede "
            "entrenar sin informe médico o no."),
        controles=(
            Control("Fecha de la revisión *", "Cuándo se hizo."),
            Control("Tensión sistólica / diastólica / Frecuencia cardíaca",
                    "Las constantes. Al lado de cada una aparece el rango de "
                    "referencia, para no tener que recordarlo."),
            Control("Patologías / Medicación / Lesiones / Contraindicaciones",
                    "Texto libre. Lo que escribas en contraindicaciones es lo que "
                    "hay que tener delante al montar el programa."),
            Control("Resultado del cribado",
                    "Se calcula con lo que has introducido y dice si hace falta "
                    "informe médico antes de entrenar."),
            Control("Guardar registro", "Añade la revisión al historial."),
        ),
        reglas=(
            "Si el cribado exige informe médico, la lista de usuarios lo marca y el "
            "panel de inicio lo recuerda. El programa no bloquea nada por su "
            "cuenta: la decisión es tuya, pero queda registrada.",
            "Las revisiones se acumulan. La más reciente es la que vale.",
        ),
        ver_tambien=("usuarios", "valoraciones"),
    ),
    Ayuda(
        clave="disponibilidad",
        titulo="Disponibilidad",
        donde="Usuarios → «Disponibilidad».",
        para_que=(
            "Cuándo, cuánto tiempo, dónde y con qué puede entrenar. Es lo que "
            "decide si un programa es realista para esa persona."),
        controles=(
            Control("Fecha *", "Desde cuándo vale esto."),
            Control("Días por semana *", "Cuántos días puede entrenar."),
            Control("Días preferidos", "Cuáles, si los tiene."),
            Control("Franja", "Mañana, mediodía, tarde o noche."),
            Control("Duración de sesión *", "Minutos de los que dispone."),
            Control("Lugar", "Gimnasio, casa o aire libre."),
            Control("Material disponible",
                    "Lo que tiene a mano. Es lo que luego usa «Ver sustitutos» "
                    "para proponer alternativas que de verdad pueda hacer."),
            Control("Guardar registro", "Añade el registro al historial."),
        ),
        ver_tambien=("usuarios", "sustitutos"),
    ),
    Ayuda(
        clave="ficha_ejercicio",
        titulo="Ficha de ejercicio",
        donde="Ejercicios → «Nuevo ejercicio» o «Editar».",
        para_que="Define un ejercicio y cómo se comporta dentro de un programa.",
        controles=(
            Control("Nombre *", "Como lo vas a buscar y como saldrá impreso."),
            Control("Patrón de movimiento *",
                    "Empuje horizontal, tracción vertical, sentadilla, bisagra de "
                    "cadera… Es la clasificación que usa el programa para buscar "
                    "sustitutos y para avisar de huecos de cobertura."),
            Control("Grupo principal *", "El músculo o la zona que manda."),
            Control("Grupos secundarios",
                    "Los que acompañan. Elige varios con la tecla Ctrl."),
            Control("Material *",
                    "Barra, mancuernas, máquina, peso corporal, gomas, kettlebell… "
                    "Condiciona los sustitutos."),
            Control("Nivel", "1 iniciación, 2 intermedio, 3 avanzado."),
            Control("Incremento de carga",
                    "El salto mínimo de peso: 2,5 kg con barra, 2 kg con "
                    "mancuernas, 5 kg en algunas máquinas. Es lo que usa el "
                    "programa para redondear los kilos al imprimir. Si el "
                    "ejercicio es de peso corporal, déjalo en «sin carga»."),
            Control("Unilateral",
                    "Si se hace un lado a la vez. Marca la diferencia al valorar "
                    "asimetrías."),
            Control("Básico",
                    "Si es un ejercicio troncal, de los que forman el esqueleto "
                    "del programa."),
            Control("Activo", "Si se puede usar en programas nuevos."),
            Control("Vídeo", "Enlace para enseñar la técnica."),
            Control("Contraindicaciones", "Cuándo no conviene."),
        ),
        reglas=(
            "Si el ejercicio usa barra o mancuernas tiene que llevar incremento de "
            "carga: sin eso el programa no sabría a qué redondear los kilos.",
        ),
        ver_tambien=("ejercicios", "sustitutos"),
    ),
    Ayuda(
        clave="sustitutos",
        titulo="Ejercicios equivalentes",
        donde="Ejercicios → «Ver sustitutos».",
        para_que=(
            "Encontrar con qué cambiar un ejercicio sin cambiar el estímulo. "
            "Resuelve el «la máquina está ocupada» y el «hoy entreno en casa»."),
        controles=(
            Control("Material disponible",
                    "El material con el que cuentas hoy."),
            Control("Solo los que puedo hacer con ese material",
                    "Filtra la propuesta a ese material (más los de peso corporal, "
                    "que siempre se pueden hacer)."),
            Control("Tabla",
                    "Hasta doce alternativas, ordenadas por lo parecidas que son al "
                    "original en patrón y grupo muscular."),
        ),
        ver_tambien=("ejercicios", "disponibilidad"),
    ),
    Ayuda(
        clave="valoracion",
        titulo="Valoración física",
        donde="Valoraciones → «Nueva valoración» o «Abrir / editar».",
        para_que=(
            "Introducir las pruebas de un protocolo. A medida que escribes, cada "
            "prueba se compara con la tabla de referencia de ese sexo y esa edad y "
            "te dice en qué categoría cae."),
        controles=(
            Control("Protocolo",
                    "El guion de pruebas. Hay varios: el estándar, uno corto, uno "
                    "centrado en fuerza… Elegir protocolo define qué filas salen."),
            Control("Fecha y Tipo", "Inicial, de seguimiento o final."),
            Control("Una fila por prueba",
                    "El valor medido y, al lado, la categoría y los puntos que le "
                    "corresponden según la tabla."),
            Control("Lado izquierdo / derecho",
                    "En las pruebas unilaterales hay una casilla por lado: así se "
                    "puede calcular la asimetría."),
            Control("Escala de técnica (0-3)",
                    "En las pruebas de fuerza no se anotan kilos sino la calidad "
                    "del gesto. <b>0 es dolor</b>, y eso no es un cero de "
                    "rendimiento: es una bandera roja."),
            Control("Compensaciones…",
                    "Abre la lista de desviaciones observables de esa prueba "
                    "(rodilla que se va adentro, pelvis que cae…) para marcar lo "
                    "que has visto."),
            Control("Recalcular",
                    "Vuelve a puntuar todo y actualiza el resumen por capacidades."),
            Control("Guardar valoración", "Escribe la valoración en el libro."),
        ),
        reglas=(
            "No hace falta rellenar todas las pruebas. Lo que dejes en blanco no "
            "cuenta: no se convierte en un cero.",
            "Si una prueba no tiene tabla para ese sexo y esa edad, se guarda el "
            "dato y se marca «sin baremo». Es información válida, simplemente no "
            "comparable.",
        ),
        ver_tambien=("valoraciones", "criterios"),
    ),
    Ayuda(
        clave="criterios",
        titulo="Compensaciones",
        donde="Dentro de una valoración, botón «Compensaciones…» de una prueba.",
        para_que=(
            "Anotar qué has visto mal en la ejecución, más allá de la nota global. "
            "Es lo que convierte un «2 sobre 3» en algo sobre lo que trabajar."),
        controles=(
            Control("Lista de casillas",
                    "Las desviaciones típicas de esa prueba. Marca las que hayas "
                    "observado."),
            Control("Aceptar", "Las guarda en la prueba."),
        ),
        reglas=(
            "Las compensaciones marcadas salen en el informe PDF, junto a la "
            "puntuación. Son la parte del informe que de verdad orienta el trabajo.",
        ),
        ver_tambien=("valoracion",),
    ),
    Ayuda(
        clave="ciclo",
        titulo="Ciclo (macro, meso o micro)",
        donde="Programas → «Nuevo macrociclo», «Añadir dentro» o «Editar».",
        para_que=(
            "Un nivel de la estructura del programa. La ventana es la misma para "
            "los tres niveles y cambia según dónde estés."),
        controles=(
            Control("Nombre *", "Cómo lo vas a reconocer en el árbol."),
            Control("Duración *",
                    "En semanas para macro y meso; en el microciclo es una semana."),
            Control("Orden",
                    "El número que dice <b>en qué puesto va este ciclo entre sus "
                    "hermanos</b>, y por tanto el orden cronológico. Los "
                    "mesociclos 1, 2 y 3 de un macrociclo se hacen en ese orden, "
                    "y de ahí salen las fechas al asignar: el 1 empieza el día de "
                    "inicio, el 2 cuando acaba el 1, y así. No tiene que ser "
                    "consecutivo —1, 2, 3 o 10, 20, 30 dan igual—; lo único que "
                    "cuenta es si un número es menor que otro. Para colar un "
                    "bloque entre el 1 y el 2, dale un orden intermedio o "
                    "renumera. Es también el orden en que se ve el árbol."),
            Control("Objetivo",
                    "Solo en el macrociclo: a qué apunta el programa entero."),
            Control("Enfoque",
                    "Solo en el mesociclo: acumulación, intensificación, descarga… "
                    "Es la intención del bloque."),
            Control("Partir de una plantilla",
                    "Solo al crear un macrociclo: arranca con una estructura ya "
                    "hecha en vez de con una hoja en blanco."),
            Control("Notas", "Lo que quieras recordar de este ciclo."),
        ),
        reglas=(
            "La duración del padre debería cuadrar con la suma de sus hijos. Si no "
            "cuadra, la banda de avisos de la ventana de programas te lo dice.",
            "El orden es un <b>número entero</b> y <b>no se puede repetir</b> "
            "entre hermanos: al guardar, el programa comprueba que esté libre y, "
            "si no, dice quién lo tiene y cuál es el primer número disponible. Al "
            "clonar un ciclo, la copia recibe el siguiente orden libre.",
        ),
        ver_tambien=("programas", "sesion"),
    ),
    Ayuda(
        clave="sesion",
        titulo="Sesión",
        donde="Programas → «Nueva sesión» o «Editar sesión».",
        para_que="Un día de entrenamiento dentro de un microciclo.",
        controles=(
            Control("Día de la semana *",
                    "Es lo que ordena las sesiones y lo que sale impreso."),
            Control("Nombre",
                    "Opcional: «Empuje», «Tren inferior». Ayuda a orientarse."),
            Control("Tipo", "Fuerza, cardio, movilidad, mixta."),
            Control("Duración estimada", "Minutos. Debe caber en su disponibilidad."),
            Control("Notas", "Indicaciones para ese día."),
        ),
        ver_tambien=("programas", "linea"),
    ),
    Ayuda(
        clave="linea",
        titulo="Ejercicio de la sesión",
        donde="Programas → «Añadir ejercicio» o «Editar» en la lista de abajo.",
        para_que=(
            "La línea de trabajo: qué ejercicio, cuánto y a qué carga. Es la "
            "ventana más importante del programa y la que conviene entender bien."),
        controles=(
            Control("Bloque *",
                    "Calentamiento, principal, accesorio o enfriamiento. Ordena la "
                    "sesión impresa."),
            Control("Ejercicio *",
                    "Se puede escribir para buscar: el desplegable filtra por "
                    "cualquier parte del nombre, sin importar acentos ni mayúsculas."),
            Control("Series *", "Número de series."),
            Control("Repeticiones",
                    "Admite rangos («8-10») y texto («al fallo», «30 s»)."),
            Control("Modo de carga",
                    "Cómo expresas la carga: <b>%1RM</b>, <b>RPE</b>, <b>RIR</b>, "
                    "<b>kg</b> directos, <b>peso corporal</b> o <b>tiempo</b>. "
                    "Importante: lo que guardas es la <i>intención</i>, no el peso."),
            Control("Valor", "El número que acompaña al modo: 75 si es %1RM, 8 si es RPE…"),
            Control("Pista",
                    "Debajo del valor. Traduce la intención a kilos con el 1RM "
                    "actual de la persona, para que veas si es razonable."),
            Control("Descanso", "Segundos entre series."),
            Control("Tempo",
                    "Cuatro cifras: bajada, pausa abajo, subida, pausa arriba. "
                    "«3-1-1-0» es una bajada de tres segundos."),
            Control("Progresión",
                    "Cómo evoluciona semana a semana dentro del microciclo. "
                    "«LINEAL:+2.5» suma 2,5 kg por semana; «PCT:70,75,80» recorre "
                    "esos porcentajes; «DESCARGA:60» baja al 60 %; "
                    "«DOBLE_PROGRESION» sube repeticiones antes que kilos; "
                    "«AUTORREGULADA:RIR2» deja que la fatiga del día decida."),
            Control("Notas", "Lo que haya que recordar de esta línea."),
        ),
        reglas=(
            "La carga se guarda como intención y se convierte en kilos <b>al "
            "imprimir</b>, con el 1RM que la persona tenga ese día. Así el mismo "
            "programa sirve para dos personas distintas y sigue siendo correcto "
            "cuando alguien mejora.",
            "Al convertir, el programa redondea al incremento del ejercicio y "
            "nunca baja del peso de la barra (20 kg).",
            "Si no hay 1RM registrado, el PDF imprime «por determinar» en vez de "
            "inventarse un número.",
            "Las progresiones se cuentan por semana <b>dentro del microciclo</b>.",
        ),
        ver_tambien=("programas", "cargas", "imprimir"),
    ),
    Ayuda(
        clave="asignar",
        titulo="Asignar un programa",
        donde="Asignaciones → «Asignar programa».",
        para_que=(
            "Convertir una plantilla en el entrenamiento de alguien, con fechas. "
            "Antes de guardar puedes ver el calendario completo que se va a "
            "congelar."),
        controles=(
            Control("Usuario *",
                    "A quién. Se puede escribir dentro para filtrar la lista por "
                    "cualquier parte del nombre o del apellido."),
            Control("Programa *",
                    "Qué macrociclo. También se puede escribir para filtrar."),
            Control("Fecha de inicio *",
                    "Desde cuándo. A partir de aquí se calculan todas las fechas."),
            Control("Objetivo asociado",
                    "Con qué objetivo de esa persona se relaciona. Opcional, pero "
                    "es lo que luego permite decir si el programa sirvió."),
            Control("Notas", "Lo que quieras anotar de esta asignación."),
            Control("Calendario que se va a congelar",
                    "La tabla de abajo: cada ciclo con sus fechas reales. "
                    "Revísalo antes de asignar."),
            Control("Aviso",
                    "Señala lo que no cuadra: el programa no encaja con su "
                    "disponibilidad, le falta algún 1RM necesario, ya tiene otra "
                    "asignación en curso."),
            Control("Asignar", "Guarda la asignación con ese calendario."),
        ),
        reglas=(
            "El calendario queda fijo. Cambiar la plantilla después no mueve lo ya "
            "asignado.",
        ),
        ver_tambien=("asignaciones", "imprimir"),
    ),
    Ayuda(
        clave="imprimir",
        titulo="Qué semanas imprimir",
        donde="Asignaciones → «Imprimir».",
        para_que=(
            "Elegir el tramo de semanas que se lleva la persona en papel. Lo normal "
            "es dar dos o tres semanas, no el programa entero."),
        controles=(
            Control("Desde la semana / Hasta la semana",
                    "El tramo. Las semanas se cuentan desde el inicio de la "
                    "asignación."),
        ),
        reglas=(
            "Las cargas se calculan en el momento de imprimir, con el 1RM que haya "
            "entonces. Un PDF de hace tres meses no coincidirá con el de hoy, y es "
            "lo correcto.",
        ),
        ver_tambien=("asignaciones", "linea"),
    ),
    Ayuda(
        clave="plantillas",
        titulo="Plantillas de correo",
        donde="Correo → «Plantillas de correo…».",
        para_que=(
            "Editar el texto de los correos automáticos y las direcciones de los "
            "formularios de Google."),
        controles=(
            Control("Lista de plantillas",
                    "Una por tipo de correo: bienvenida, consentimiento, encuesta "
                    "T-14, recordatorio, check-in de mitad, cierre de ciclo, "
                    "agradecimiento."),
            Control("Asunto y Cuerpo",
                    "El texto. Admite marcadores entre dobles llaves que se "
                    "sustituyen al enviar: <tt>{{nombre}}</tt>, "
                    "<tt>{{enlace_form}}</tt>, <tt>{{nota_personal}}</tt>, "
                    "<tt>{{dias_restantes}}</tt>."),
            Control("Secciones condicionales",
                    "<tt>{{#nota_personal}}…{{/nota_personal}}</tt> hace que ese "
                    "trozo solo aparezca si hay nota. Sirve para que el correo no "
                    "quede con un hueco raro cuando no escribes nada."),
            Control("URL del formulario",
                    "La dirección del formulario de Google. El programa le añade "
                    "los datos de la persona para que llegue prerrellenado."),
            Control("Activa", "Si esta plantilla se usa o no."),
            Control("Se puede enviar en modo vacaciones",
                    "Si este tipo de correo puede salir sin tu aprobación cuando "
                    "el modo vacaciones está encendido."),
            Control("Guardar esta plantilla", "Guarda los cambios de la elegida."),
        ),
        problemas=(
            Problema("No encuentro «Obtener enlace» en Google Forms",
                     "En el formulario, menú de tres puntos → «Obtener enlace "
                     "prerrellenado». Rellena los campos de identificación con "
                     "cualquier texto, envía, y copia la URL que te da."),
        ),
        ver_tambien=("correo",),
    ),
)

MANUAL: tuple[Ayuda, ...] = (
    Ayuda(
        clave="manual_ayuda",
        titulo="Manual y ayuda",
        donde="Último botón de la barra lateral.",
        para_que=(
            "El manual completo, dentro del propio programa. No es solo texto: "
            "desde cada página se puede abrir la ventana de la que habla y, en las "
            "tareas principales, arrancar un recorrido guiado que va señalando los "
            "controles de verdad."),
        controles=(
            Control("Buscador",
                    "Filtra el índice por cualquier palabra del manual, incluida la "
                    "descripción de cada botón. No distingue acentos ni mayúsculas."),
            Control("Índice (izquierda)",
                    "Seis capítulos: cómo empezar, las cinco tareas del día a día, "
                    "una página por ventana, los conceptos de fondo y los "
                    "problemas habituales."),
            Control("Enlaces del texto",
                    "Los que empiezan por «▸» hacen algo: abren la ventana de la "
                    "que habla la página o arrancan un recorrido. Los demás llevan "
                    "a otra página del manual."),
            Control("Abrir esta ventana",
                    "Lleva a la sección que describe la página que estás leyendo."),
            Control("Hacer el recorrido guiado",
                    "Arranca el recorrido de esa tarea sobre la ventana real."),
            Control("Guardar el manual completo",
                    "Vuelca todo el manual a un fichero HTML que se abre en el "
                    "navegador, para leerlo fuera del programa, imprimirlo o "
                    "guardarlo en PDF."),
        ),
        reglas=(
            "Además de este manual, <b>cada ventana tiene su propio botón «?»</b> "
            "arriba a la derecha, y la tecla <b>F1</b> hace lo mismo. Esa ayuda "
            "explica todos los controles de esa ventana, uno por uno.",
            "Los recorridos guiados no tocan tus datos: solo señalan y explican.",
        ),
        seccion="manual",
    ),
)

AYUDAS: dict[str, Ayuda] = {a.clave: a for a in VENTANAS + DIALOGOS + MANUAL}


# ======================================================== capítulos del manual

_PAGINAS: tuple[Pagina, ...] = (
    Pagina(
        clave="que_es",
        titulo="Qué es este programa",
        cuerpo="""
<p>Una aplicación de escritorio para llevar el entrenamiento de tus usuarios:
sus datos, su valoración física, sus programas y los correos que se les
envían.</p>

<p>Dos decisiones de fondo explican casi todo lo demás:</p>
<ul>
<li><b>Los datos viven en un Excel.</b> Un único fichero
(<tt>datos_krv.xlsx</tt>) con una hoja por tabla. No hay servidor ni base de
datos que mantener: si algún día dejas de usar el programa, los datos siguen
ahí y se abren con Excel.</li>
<li><b>La aplicación no corre sobre Excel.</b> Excel es solo el almacén. El
programa escribe el fichero de forma segura —primero en un temporal y luego lo
sustituye— y hace una copia de seguridad fechada en cada guardado.</li>
</ul>

<p>Consecuencia práctica, y la única molestia de este diseño: <b>si tienes el
Excel abierto en Excel, el programa no puede guardar</b>. Te avisa, no pierdes
nada, cierras Excel y vuelves a guardar.</p>

<p>El trabajo típico va en este orden: <b>usuario → valoración → programa →
asignación → correo</b>. Puedes salirte del orden, pero cada paso aprovecha lo
del anterior.</p>
""",
    ),
    Pagina(
        clave="arranque",
        titulo="Arrancar, guardar y copias de seguridad",
        cuerpo="""
<p><b>Para abrir el programa</b> tienes el icono del escritorio, o
<tt>ARRANCAR.bat</tt> en la carpeta, o desde una consola:</p>
<p><tt>cd $HOME\\GIMNASIO; python -m krv</tt></p>

<p><b>Guardar.</b> No hay botón de guardar. El programa escribe en el Excel
después de cada cambio que aceptas, y la barra de abajo lo confirma. Si falla,
sale un aviso explicando por qué: lo habitual es tener el fichero abierto en
Excel.</p>

<p><b>Copias de seguridad.</b> Cada guardado deja una copia fechada en la
carpeta <tt>backups</tt>, y el programa va borrando las más viejas para que no
crezca sin control. Si algo sale mal, se recupera copiando una de esas copias
encima del fichero de datos, con el programa cerrado.</p>

<p><b>Ojo con lo que esas copias no cubren.</b> Están en el mismo disco que el
original, así que te protegen de un error al editar pero no de que se rompa el
ordenador. Hasta que el programa sepa copiarse fuera solo, <b>copia de vez en
cuando tu carpeta de datos</b> a un disco externo o a una carpeta en la nube.
Es una sola carpeta: la que abre «Carpeta de mis datos» en el menú de inicio.</p>

<p><b>Si alguien ha tocado el Excel por fuera</b> mientras el programa estaba
abierto, al guardar te avisa y te pide que cierres sin guardar y vuelvas a
abrir. Es para no machacar lo que haya hecho el otro.</p>

<p><b>Si el programa pide migrar el libro</b> al arrancar, es que el fichero es
de una versión anterior y le faltan columnas nuevas. Acepta: hace una copia
antes de tocar nada.</p>

<p><b>Los textos de tu marca</b> —nombre comercial, lema, contacto, horario—
viven en <tt>config.toml</tt>, junto al programa. Ese fichero es tuyo y no se
actualiza nunca solo, así que si cambias de lema hay que tocarlo a mano. El
nombre y el lema aparecen en la cabecera de cada correo y en los PDF. En la
portada de este manual se ve lo que el programa está usando ahora mismo.</p>
""",
    ),
    Pagina(
        clave="instalar",
        titulo="Instalar y actualizar",
        cuerpo="""
<p>Hay un instalador de verdad: un solo fichero
<tt>KevinRuizValdenegro_Instalador.exe</tt> que se lleva al ordenador y se abre
con doble clic. <b>No hace falta que ahí haya Python ni nada instalado</b>: el
programa viaja entero dentro.</p>

<p>Pregunta qué quieres hacer, y hay dos caminos muy distintos:</p>

<h2>1 · Instalación desde cero</h2>
<p>Para un ordenador nuevo. Instala las dependencias, crea el acceso directo
del Escritorio con el icono, y deja el libro de datos recién hecho con un
<b>usuario de ejemplo que tiene de todo</b>: objetivos, salud, disponibilidad,
dos valoraciones, dos programas asignados y correos en varios estados. Sirve
para ver el programa entero funcionando antes de meter a nadie de verdad; ese
usuario se borra cuando ya no haga falta.</p>

<p><b>Este modo rehace el libro de datos.</b> Si ya había uno, se hace una copia
de seguridad fechada antes de tocarlo y se pide confirmación expresa.</p>

<p>Al arrancar sale el <b>asistente de primera configuración</b>, que pregunta
la cuenta de correo desde la que vas a escribir y, si los tienes a mano, las
direcciones de tus formularios de Google.</p>

<h2>2 · Actualizar la versión</h2>
<p>Renueva el programa y <b>no toca ni tus datos ni tu configuración</b>. Antes
de nada hace una copia de seguridad del libro, y después le añade las columnas
nuevas si esta versión las necesita. Tu <tt>config.toml</tt> y tu <tt>.env</tt>
se quedan como están.</p>

<h2>El cuidado con el Excel</h2>
<p>El libro es el único sitio donde viven los datos, así que el instalador:</p>
<ul>
<li>Se niega a seguir si el libro está abierto en Excel.</li>
<li>Hace una copia fechada <b>antes</b> de cualquier cosa, en los dos modos.</li>
<li>Solo rehace el libro si eliges la instalación desde cero y lo confirmas.</li>
</ul>

<p>Si algo sale mal, la copia está junto al libro, con el nombre
<tt>datos_krv_antes_de_instalar_<i>fecha</i>.xlsx</tt>: se recupera copiándola
encima del original, con el programa cerrado. Y cuando la instalación desde
cero rehace el libro, el anterior tampoco se borra: se aparta con el nombre
<tt>datos_krv_reemplazado_<i>fecha</i>.xlsx</tt>.</p>

<h2>Dónde queda cada cosa</h2>
<p>Instalado, el programa y tus datos viven separados, y esto conviene saberlo:</p>
<ul>
<li><b>El programa</b> va donde van los programas. No hay nada tuyo ahí, así que
se puede desinstalar y reinstalar sin miedo.</li>
<li><b>Tus datos</b> van a <tt>Documentos\\Kevin Ruiz Valdenegro</tt>: el Excel,
la configuración, las copias de seguridad, los registros y los PDF que generes.
Esa carpeta tiene su propio acceso directo en el menú de inicio.</li>
</ul>
<p>El desinstalador <b>nunca</b> toca esa carpeta: quitar el programa no borra
nada tuyo. Y para pasarte a otro ordenador basta con copiarla.</p>

<h2>Si trabajas sobre el código</h2>
<p>Si en vez del instalador tienes la carpeta del proyecto, el equivalente es
<tt>instalar.ps1</tt>, que prepara el entorno de Python y hace lo mismo con los
dos modos. Y <tt>construir.ps1</tt> es el que fabrica el instalador: empaqueta
el programa y monta el <tt>.exe</tt>.</p>
""",
    ),
    Pagina(
        clave="primer_dia",
        titulo="El primer día: qué hacer por orden",
        cuerpo="""
<p>Si acabas de instalar el programa, este es el camino corto para tenerlo
funcionando:</p>

<ol>
<li><b>Comprueba el correo.</b> Ve a <i>Correo</i> → «Probar la conexión de
correo». Si se queja de la credencial, hay que crear una contraseña de
aplicación en la cuenta de Google y escribirla en el fichero <tt>.env</tt>. Es
mejor resolver esto antes de tener usuarios esperando un correo.</li>
<li><b>Mira el catálogo de ejercicios.</b> Viene con 127. Añade los tuyos y
desactiva los que no vas a usar.</li>
<li><b>Revisa las plantillas de correo</b> y pon las direcciones de tus
formularios de Google.</li>
<li><b>Monta un macrociclo</b>, aunque sea partiendo de una de las plantillas
que vienen hechas. Sin programa no hay nada que asignar.</li>
<li><b>Da de alta a la primera persona</b> y recorre el camino completo:
objetivos, salud, disponibilidad, valoración, asignación. Así ves los huecos
antes de tener veinte personas dentro.</li>
</ol>

<p>El <i>Panel de inicio</i> es tu lista de tareas a partir de ahí. Si está
vacío, estás al día.</p>
""",
        seccion="inicio",
        recorrido="primer_dia",
    ),
    Pagina(
        clave="como_alta",
        titulo="Cómo doy de alta a alguien",
        cuerpo="""
<ol>
<li><i>Usuarios</i> → «Nuevo usuario». Nombre, fecha de nacimiento y sexo son
obligatorios: de ahí salen la edad y los baremos de la valoración.</li>
<li>Escribe su correo y deja marcado «Acepta recibir correos».</li>
<li><b>Consentimiento.</b> Dos caminos: lo registras tú en la ficha (si lo has
firmado en papel), o le envías el correo de consentimiento y lo firma por el
formulario. Sin consentimiento registrado no le saldrá ningún correo
automático.</li>
<li>«Objetivos» → su primer objetivo. Tipo, descripción y estado «activo».</li>
<li>«Salud» → la revisión. Las constantes llevan su rango de referencia al
lado, y el cribado se calcula solo.</li>
<li>«Disponibilidad» → días, minutos, lugar y material.</li>
<li>Ya puedes valorarlo y asignarle un programa.</li>
</ol>

<p>Si quieres darle la bienvenida con su programa adjunto, asigna primero el
programa: el correo de bienvenida lleva las primeras semanas en PDF, y si el
PDF no se puede generar el correo no sale.</p>
""",
        seccion="usuarios",
        recorrido="alta_usuario",
    ),
    Pagina(
        clave="como_valorar",
        titulo="Cómo hago una valoración",
        cuerpo="""
<ol>
<li><i>Valoraciones</i> → «Nueva valoración». Te pregunta a quién.</li>
<li>Elige el protocolo: eso define qué pruebas aparecen.</li>
<li>Ve rellenando. Cada valor se compara al momento con la tabla de ese sexo y
esa edad, y a la derecha aparece la categoría.</li>
<li>En las pruebas de fuerza no anotas kilos: anotas la <b>técnica</b> de 0 a
3. El 0 es dolor, no es un cero de rendimiento.</li>
<li>Pulsa «Compensaciones…» en las pruebas donde hayas visto algo: esa es la
parte del informe que orienta el trabajo.</li>
<li>En las pruebas unilaterales rellena los dos lados: así se calcula la
asimetría.</li>
<li>«Guardar valoración», y luego «Generar informe PDF».</li>
</ol>

<p>No hace falta rellenarlo todo. Lo que dejes en blanco no cuenta: el programa
no lo convierte en un cero y el radar del informe deja ese eje sin dibujar.</p>
""",
        seccion="valoraciones",
        recorrido="valoracion",
    ),
    Pagina(
        clave="como_programa",
        titulo="Cómo monto un programa",
        cuerpo="""
<p>Un programa es una <b>plantilla</b>: se escribe una vez y se asigna a quien
haga falta. No es el entrenamiento de nadie hasta que lo asignas.</p>

<ol>
<li><i>Programas</i> → «Nuevo macrociclo». Puedes partir de una plantilla ya
hecha.</li>
<li>Con el macrociclo elegido, «Añadir dentro» para cada <b>mesociclo</b>
(bloques de 3-5 semanas con una intención: acumular, intensificar, descargar).</li>
<li>Con un mesociclo elegido, «Añadir dentro» para cada <b>microciclo</b>
(normalmente una semana).</li>
<li>Con el microciclo elegido, «Nueva sesión» por cada día de entreno.</li>
<li>Con la sesión elegida, «Añadir ejercicio» por cada línea.</li>
<li>Para la semana siguiente: elige el microciclo y pulsa <b>«Clonar»</b>. Copia
el ciclo con sus sesiones y sus ejercicios, y solo tienes que retocar.</li>
</ol>

<p>Vigila la banda de avisos de abajo: te señala microciclos sin sesiones,
sesiones sin ejercicios y cargas que no se podrán calcular por falta de 1RM.</p>
""",
        seccion="programas",
        recorrido="montar_programa",
    ),
    Pagina(
        clave="como_asignar",
        titulo="Cómo asigno y cómo imprimo",
        cuerpo="""
<ol>
<li><i>Asignaciones</i> → «Asignar programa».</li>
<li>Persona, programa y fecha de inicio. Abajo aparece el <b>calendario que se
va a congelar</b>: cada ciclo con sus fechas reales.</li>
<li>Lee el aviso si sale: suele decir que el programa no encaja con su
disponibilidad, que falta algún 1RM o que ya tiene otra asignación en curso.</li>
<li>«Asignar». A partir de aquí las fechas son firmes: cambiar la plantilla no
mueve esta asignación.</li>
<li>Para el papel: elige la asignación, «Imprimir», y di <b>desde</b> y
<b>hasta</b> qué semana. Lo normal es dar dos o tres semanas, no el programa
entero.</li>
</ol>

<p>Las cargas se convierten a kilos en el momento de imprimir, con el 1RM que
la persona tenga ese día. Si no hay 1RM, el PDF pone «por determinar» en vez de
inventarse un peso.</p>
""",
        seccion="asignaciones",
        recorrido="asignar",
    ),
    Pagina(
        clave="como_encuesta",
        titulo="Cómo funciona el aviso de los 14 días",
        cuerpo="""
<p>Es el automatismo central del programa, y está montado para que
<b>nunca</b> salga un correo que no hayas visto.</p>

<ol>
<li>Cuando a una asignación le quedan <b>14 días</b>, el panel de inicio lo
avisa.</li>
<li>Pulsas «Buscar avisos de correo» (en el panel o en la bandeja): el programa
redacta el borrador con el enlace al formulario de satisfacción y renovación,
ya prerrellenado con la identificación de esa persona.</li>
<li>El borrador <b>espera en la bandeja de salida</b>. No sale nada.</li>
<li>Lo lees, escribes tu <b>impresión personal</b> en el cuadro de la derecha y
pulsas «Actualizar vista previa»: tu párrafo queda integrado en el cuerpo, no
pegado al final.</li>
<li>Si quieres verlo como lo verá la persona, «Enviarme una prueba».</li>
<li>«Aprobar y enviar», o «Aprobar» y luego «Enviar todos los aprobados» cuando
hayas repasado varios.</li>
<li>Cuando conteste, «Importar respuestas…» con el CSV del formulario. Si pide
cita o declara una molestia, aparece como aviso en el panel de inicio.</li>
</ol>

<p><b>Modo vacaciones.</b> Si te vas y quieres que el correo siga saliendo sin
tu aprobación, se enciende en la configuración. Solo salen los tipos de correo
que hayas marcado como permitidos, nunca lo que esté en error, y el
consentimiento se sigue respetando. Mientras está encendido, la bandeja lo
avisa con una banda arriba.</p>
""",
        seccion="correo",
        recorrido="encuesta",
    ),
    Pagina(
        clave="arbol",
        titulo="Concepto: el árbol de ciclos",
        cuerpo="""
<p>La jerarquía es siempre la misma y no se puede saltar ningún nivel:</p>

<p><tt>Macrociclo → Mesociclo → Microciclo → Sesión → Ejercicio</tt></p>

<ul>
<li><b>Macrociclo</b>: el programa completo, con su objetivo. De 8 a 24 semanas
es lo habitual.</li>
<li><b>Mesociclo</b>: un bloque con una intención —acumulación,
intensificación, descarga—. De 3 a 5 semanas.</li>
<li><b>Microciclo</b>: normalmente una semana.</li>
<li><b>Sesión</b>: un día concreto.</li>
<li><b>Ejercicio</b>: una línea de trabajo, con sus series y su carga.</li>
</ul>

<p>Un macrociclo puede tener tantos mesociclos como quieras, y cada mesociclo
tantos microciclos como quieras. «Clonar» copia un ciclo con todo lo que
cuelga, y es la herramienta que hace que montar 12 semanas no sea un castigo.</p>
""",
        seccion="programas",
    ),
    Pagina(
        clave="cargas",
        titulo="Concepto: la carga se guarda como intención",
        cuerpo="""
<p>Esta es la idea que más cuesta al principio y la que más valor tiene.</p>

<p>Cuando pones una carga en una línea no guardas kilos: guardas <b>qué
pretendes</b>. Los modos son:</p>

<ul>
<li><b>%1RM</b> — un porcentaje de su máximo. «75».</li>
<li><b>RPE</b> — esfuerzo percibido de 1 a 10. «8» es «me quedaban dos».</li>
<li><b>RIR</b> — repeticiones en reserva. «2» es lo mismo dicho al revés.</li>
<li><b>KG</b> — kilos directos, cuando quieres fijarlos tú.</li>
<li><b>Peso corporal</b> — sin carga externa.</li>
<li><b>Tiempo</b> — para planchas e isométricos.</li>
</ul>

<p><b>Los kilos se calculan al imprimir</b>, con el 1RM que la persona tenga ese
día, redondeando al incremento del ejercicio y sin bajar nunca del peso de la
barra. Un RPE o un RIR se traducen a porcentaje usando una tabla que tiene en
cuenta las repeticiones.</p>

<p>Esto tiene tres consecuencias buenas: el mismo programa sirve para dos
personas distintas; cuando alguien mejora su 1RM el programa se actualiza solo;
y si no hay 1RM el PDF dice «por determinar» en lugar de inventarse un peso.</p>
""",
        seccion="programas",
    ),
    Pagina(
        clave="progresiones",
        titulo="Concepto: las progresiones",
        cuerpo="""
<p>La progresión dice cómo cambia la carga <b>semana a semana dentro del
microciclo</b>. Ojo con esto: se cuenta por semana del micro, no por semana del
plan entero.</p>

<ul>
<li><b>LINEAL:+2.5</b> — suma 2,5 kg cada semana.</li>
<li><b>PCT:70,75,80</b> — recorre esos porcentajes del 1RM, uno por semana.</li>
<li><b>DESCARGA:60</b> — baja al 60 % de lo previsto. Para semanas de descarga.</li>
<li><b>DOBLE_PROGRESION</b> — primero sube repeticiones hasta el techo del
rango, y solo entonces sube kilos.</li>
<li><b>AUTORREGULADA:RIR2</b> — no fija el peso: fija la reserva. El peso lo
decide la fatiga de ese día.</li>
</ul>

<p>Si una línea no lleva progresión, la carga se repite igual todas las semanas
del microciclo.</p>
""",
        seccion="programas",
    ),
    Pagina(
        clave="baremos",
        titulo="Concepto: baremos y categorías",
        cuerpo="""
<p>Un <b>baremo</b> es la tabla que convierte un dato medido en una categoría
comparable, y depende del <b>sexo</b> y de la <b>edad</b>. Por eso esos dos
campos son obligatorios en la ficha.</p>

<p>Cada tabla lleva anotada su <b>solidez</b>: alta cuando viene de referencias
consolidadas, media cuando es razonable pero menos firme, y baja cuando es
orientativa. El anexo del manual técnico
(<tt>docs/11-anexo-baremos.md</tt>) dice de dónde sale cada una.</p>

<p>Tres reglas que conviene conocer:</p>
<ul>
<li>Si no hay tabla para ese sexo y esa edad, se guarda el dato y se marca
<b>«sin baremo»</b>. No se inventa una categoría.</li>
<li>La puntuación global solo promedia las capacidades que has medido. Lo que
no se mide no cuenta como cero.</li>
<li>En fuerza, la escala es de técnica (0-3) y el <b>0 significa dolor</b>. No
es el peor rendimiento: es una señal de alarma.</li>
</ul>
""",
        seccion="valoraciones",
    ),
    Pagina(
        clave="alertas",
        titulo="Concepto: las dos clases de aviso",
        cuerpo="""
<p>El panel de inicio mezcla dos cosas que se comportan distinto, y entenderlo
ahorra confusión:</p>

<p><b>Avisos de estado.</b> Describen una situación: «sin consentimiento», «sin
programa activo», «el programa vence en 9 días». Desaparecen solos en cuanto la
situación cambia. No hay que marcarlos, y no se pueden marcar.</p>

<p><b>Avisos de hecho puntual.</b> Describen algo que ya pasó: «ha declarado
una molestia en la encuesta», «ha pedido cita». Eso no se desarma solo, porque
el hecho ocurrió. Esos llevan el botón <b>«Marcar como atendida»</b>, que es tu
forma de decir «ya lo he visto».</p>

<p>Si un aviso de estado no se va después de resolverlo, pulsa «Actualizar». Si
sigue, es que la causa no está resuelta de verdad.</p>
""",
        seccion="inicio",
    ),
    Pagina(
        clave="consentimiento",
        titulo="Concepto: consentimiento y correo",
        cuerpo="""
<p>El programa no envía un correo a nadie que no cumpla las tres condiciones:</p>

<ol>
<li>Tiene <b>dirección de correo</b> escrita en su ficha.</li>
<li>Tiene <b>«Acepta recibir correos»</b> marcado.</li>
<li>Tiene <b>consentimiento registrado</b>, con su fecha y su origen.</li>
</ol>

<p>Esto no se puede desactivar, ni siquiera en modo vacaciones. Si alguien no
recibe correos, revisa esas tres casillas antes de buscar en otro sitio.</p>

<p>El consentimiento se puede registrar de tres maneras, y el campo «origen» lo
distingue: <b>papel</b> (lo firmó en persona), <b>manual</b> (lo registras tú) o
<b>formulario</b> (llegó por el formulario de Google, y entonces la fecha la
pone el programa).</p>
""",
        seccion="usuarios",
    ),
    Pagina(
        clave="problemas",
        titulo="Cuando algo va mal",
        cuerpo="""
<p><b>«El libro de datos está abierto en Excel».</b> Cierra Excel y vuelve a
guardar. No se ha perdido nada: el programa detecta el fichero de bloqueo que
Excel deja y prefiere no escribir.</p>

<p><b>«Alguien ha modificado el libro por fuera».</b> Cierra la aplicación sin
guardar y vuelve a abrirla. Si guardaras encima, machacarías lo que haya hecho
el otro.</p>

<p><b>Pide migrar el libro al arrancar.</b> El fichero es de una versión
anterior. Acepta: hace copia antes de tocar nada.</p>

<p><b>«Falta la credencial GMAIL_APP_PASSWORD».</b> Hace falta una contraseña
de aplicación de Google (la contraseña normal de la cuenta no sirve): en la
cuenta de Google, Seguridad → Verificación en dos pasos → Contraseñas de
aplicaciones. Esos 16 caracteres van al fichero <tt>.env</tt>.</p>

<p><b>Dice que falta la credencial pero el <tt>.env</tt> está escrito.</b> El
aviso dice dónde ha buscado el fichero y qué claves ha leído; empieza por ahí.
Lo que más pasa:</p>
<ul>
<li>El Bloc de notas lo ha guardado como <tt>.env.txt</tt>. Al guardar hay que
poner el tipo de archivo en «Todos los archivos». El programa también lee ese
nombre, pero conviene arreglarlo.</li>
<li>El fichero está en otra carpeta. Tiene que estar junto a
<tt>datos_krv.xlsx</tt>.</li>
<li>Está guardado con una codificación rara. El programa ya se las apaña con
UTF-8, UTF-8 con marca y UTF-16, pero si lo ves raro, vuelve a escribirlo.</li>
</ul>

<p><b>«No se puede leer la configuración» al arrancar.</b> El
<tt>config.toml</tt> tiene algo que el programa no entiende. Cada línea debe
ser <tt>clave = "valor"</tt> y las secciones van entre corchetes, como
<tt>[negocio]</tt>. El aviso dice la línea exacta. Si lo editaste desde
PowerShell y no ves nada raro, no te vuelvas loco: el programa ya se apaña con
la marca invisible que añaden algunos comandos. Y si no quieres pelearte,
renombra el fichero: arrancará con los valores de fábrica, que son los
correctos, y lo rehaces desde <tt>config.ejemplo.toml</tt>.</p>

<p><b>El nombre o el lema salen antiguos</b> —en el título de la ventana, en
la cabecera de los correos o en los PDF—. Esos textos salen de
<tt>config.toml</tt>, que es <b>tuyo</b>: no se toca al actualizar el programa,
precisamente para no pisarte tus ajustes. Cambia ahí <tt>nombre_comercial</tt> y
<tt>lema</tt>, y vuelve a arrancar.</p>

<p>Para ver qué está usando el programa ahora mismo y de qué fichero sale, mira
el apartado <b>«Tu marca, tal y como la está usando el programa»</b> en la
portada de este manual. Si borras una línea de <tt>config.toml</tt>, el programa
usa su valor de fábrica, que ya es el correcto.</p>

<p><b>Un botón parece no hacer nada.</b> Mírale el color: los botones de borde
azul que necesitan una fila elegida se ven en <b>gris claro</b> cuando no hay
ninguna. Elige una fila de la tabla y vuelve a probar.</p>

<p><b>No encuentro un ejercicio en el desplegable.</b> Escribe dentro del
desplegable: filtra por cualquier parte del nombre. Si no aparece, igual está
desactivado: míralo en <i>Ejercicios</i> desmarcando «Solo activos».</p>

<p><b>No hay protocolos de valoración.</b> Ejecuta una vez
<tt>python herramientas/importar_valoracion.py</tt>.</p>

<p><b>Algo que no está en esta lista.</b> La carpeta <tt>logs</tt> guarda lo que
ha pasado, con fecha. Es lo primero que conviene mirar.</p>
""",
    ),
)

PAGINAS: dict[str, Pagina] = {p.clave: p for p in _PAGINAS}

CAPITULOS: tuple[Capitulo, ...] = (
    Capitulo("Empezar aquí",
             ("que_es", "instalar", "arranque", "primer_dia",
              "manual_ayuda"),
             "Qué es, cómo se arranca y qué hacer el primer día."),
    Capitulo("Cómo se hace",
             ("como_alta", "como_valorar", "como_programa", "como_asignar",
              "como_encuesta"),
             "Las cinco tareas del día a día, paso a paso."),
    Capitulo("Las ventanas principales",
             ("inicio", "usuarios", "ejercicios", "valoraciones", "programas",
              "asignaciones", "correo"),
             "Una página por cada sección de la barra lateral."),
    Capitulo("Las ventanas de detalle",
             ("ficha_usuario", "objetivos", "salud", "disponibilidad",
              "ficha_ejercicio", "sustitutos", "valoracion", "criterios",
              "ciclo", "sesion", "linea", "asignar", "imprimir", "plantillas"),
             "Los formularios y diálogos que se abren desde las secciones."),
    Capitulo("Conceptos que conviene entender",
             ("arbol", "cargas", "progresiones", "baremos", "alertas",
              "consentimiento"),
             "Las ideas de fondo. Entendidas estas, el resto se deduce."),
    Capitulo("Cuando algo va mal", ("problemas",),
             "Los tropiezos habituales y qué hacer con ellos."),
)


def entrada(clave: str) -> Ayuda | Pagina | None:
    """Devuelve la página del manual o la ayuda de ventana que lleva esa clave."""
    return AYUDAS.get(clave) or PAGINAS.get(clave)


def titulo_de(clave: str) -> str:
    objeto = entrada(clave)
    return objeto.titulo if objeto else clave
