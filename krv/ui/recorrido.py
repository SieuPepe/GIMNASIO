"""Recorridos guiados: señalan el control de verdad y explican qué es.

Un recorrido es una lista de pasos. Cada paso puede llevar a una sección y
señalar un widget concreto; la ventana se oscurece salvo ese widget y al lado
sale una burbuja con la explicación. Es la parte interactiva del manual: no
cuenta dónde está el botón, lo enseña.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QEvent, QPoint, QRect, Qt
from PySide6.QtGui import QColor, QKeySequence, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from . import estilo


@dataclass(frozen=True)
class Paso:
    titulo: str
    texto: str
    seccion: str | None = None
    objetivo: str | None = None   # ruta de atributos desde la ventana principal


@dataclass(frozen=True)
class Guion:
    clave: str
    titulo: str
    resumen: str
    pasos: tuple[Paso, ...]


# =============================================================== los recorridos

GUIONES: tuple[Guion, ...] = (
    Guion(
        clave="primer_dia",
        titulo="Darse una vuelta por el programa",
        resumen="Cinco minutos para saber qué hay en cada sitio.",
        pasos=(
            Paso("La barra lateral",
                 "Aquí está todo. El orden no es casual: es el orden en que se "
                 "trabaja. Usuarios, su catálogo de ejercicios, su valoración, el "
                 "programa, la asignación y el correo.",
                 seccion="inicio", objetivo="lateral"),
            Paso("El panel de inicio",
                 "Tu lista de tareas. Cada fila es algo que reclama atención, con "
                 "la gravedad en color. Si esta lista está vacía, estás al día y "
                 "no tienes que acordarte de nada.",
                 objetivo="vista_inicio.tabla"),
            Paso("Solo lo que requiere atención",
                 "Esta casilla esconde lo informativo y deja lo que hay que "
                 "resolver. Útil cuando la lista crece.",
                 objetivo="vista_inicio.solo_urgentes"),
            Paso("Del aviso a la ficha",
                 "«Abrir» lleva a la ventana del aviso con la persona ya "
                 "señalada. Es el camino corto, sin tener que buscarla.",
                 objetivo="vista_inicio.btn_abrir"),
            Paso("Buscar avisos de correo",
                 "Revisa qué programas terminan pronto y prepara los borradores. "
                 "Ojo: prepara, no envía. Todo espera tu aprobación en la bandeja.",
                 objetivo="vista_inicio.btn_buscar"),
            Paso("El botón «?»",
                 "Cada ventana tiene el suyo arriba a la derecha, y explica todos "
                 "sus controles uno por uno. La tecla F1 hace lo mismo. Si te "
                 "pierdes, es el primer sitio al que ir.",
                 objetivo="vista_inicio.btn_ayuda"),
        ),
    ),
    Guion(
        clave="alta_usuario",
        titulo="Dar de alta a una persona",
        resumen="El camino completo desde la ficha vacía hasta poder asignarle un programa.",
        pasos=(
            Paso("La lista de usuarios",
                 "Una fila por persona. Se busca escribiendo arriba, sin "
                 "preocuparse por acentos ni mayúsculas.",
                 seccion="usuarios", objetivo="vista_usuarios.tabla"),
            Paso("La columna «Pendiente»",
                 "Esta es la columna que de verdad usarás: dice de un vistazo qué "
                 "le falta a cada uno. Pasa el ratón por encima y sale el detalle.",
                 objetivo="vista_usuarios.tabla"),
            Paso("Nuevo usuario",
                 "Abre la ficha. Nombre, fecha de nacimiento y sexo son "
                 "obligatorios: de ahí salen la edad y los baremos de la "
                 "valoración. La edad no se escribe, se calcula.",
                 objetivo="vista_usuarios.btn_nuevo"),
            Paso("Objetivos, salud y disponibilidad",
                 "Tres ventanas aparte, y los tres guardan historial: no "
                 "sobreescriben, añaden. Así se ve cómo ha ido cambiando la "
                 "persona. La disponibilidad es la que decide si un programa es "
                 "realista para ella.",
                 objetivo="vista_usuarios.acciones"),
            Paso("El consentimiento",
                 "Sin consentimiento registrado no sale ningún correo automático. "
                 "Se puede registrar a mano en la ficha o dejar que lo firme por "
                 "el formulario.",
                 objetivo="vista_usuarios.detalle"),
        ),
    ),
    Guion(
        clave="valoracion",
        titulo="Hacer una valoración física",
        resumen="Cómo se introducen las pruebas y cómo sale el informe.",
        pasos=(
            Paso("Las valoraciones hechas",
                 "Una fila por valoración, con su puntuación global coloreada y "
                 "cuántos hallazgos ha detectado.",
                 seccion="valoraciones", objetivo="vista_valoraciones.tabla"),
            Paso("Nueva valoración",
                 "Pregunta a quién vas a valorar y qué protocolo seguir. El "
                 "protocolo es el guion de pruebas: define qué filas aparecen.",
                 objetivo="vista_valoraciones.btn_nueva"),
            Paso("Cómo se puntúa",
                 "Cada dato se compara con la tabla de ese sexo y esa edad. En "
                 "fuerza no se anotan kilos sino la técnica de 0 a 3, y el 0 "
                 "significa dolor. La dinamometría es la única de fuerza con "
                 "unidades.",
                 objetivo="vista_valoraciones.tabla"),
            Paso("Los hallazgos",
                 "Bajo la tabla salen las asimetrías y desequilibrios de la "
                 "valoración elegida. Es lo que convierte una nota en algo sobre "
                 "lo que trabajar.",
                 objetivo="vista_valoraciones.detalle"),
            Paso("El informe PDF",
                 "Lleva el radar, las tablas de referencia y los hallazgos. El "
                 "radar solo dibuja lo que has medido: lo que no se mide no sale "
                 "como un cero.",
                 objetivo="vista_valoraciones.acciones"),
        ),
    ),
    Guion(
        clave="montar_programa",
        titulo="Montar un programa de entrenamiento",
        resumen="Del macrociclo vacío a la sesión con sus ejercicios.",
        pasos=(
            Paso("El árbol",
                 "La estructura del programa: macrociclo arriba, dentro los "
                 "mesociclos, y dentro de cada uno sus microciclos. Es una "
                 "plantilla, no el entrenamiento de nadie todavía.",
                 seccion="programas", objetivo="vista_programas.arbol"),
            Paso("Nuevo macrociclo",
                 "Crea el programa. Puedes partir de una plantilla ya hecha en vez "
                 "de una hoja en blanco.",
                 objetivo="vista_programas.btn_nuevo"),
            Paso("Añadir dentro",
                 "Es el botón que construye la jerarquía: dentro de un macrociclo "
                 "crea un mesociclo, y dentro de un mesociclo un microciclo. No "
                 "deja saltarse niveles.",
                 objetivo="vista_programas.btn_hijo"),
            Paso("Clonar: el atajo que importa",
                 "Copia un ciclo con sus sesiones y sus ejercicios. Es lo que hace "
                 "que montar doce semanas no sea un castigo: haces la semana 1, "
                 "clonas y retocas.",
                 objetivo="vista_programas.acciones_ciclo"),
            Paso("Las sesiones del microciclo",
                 "Al elegir un microciclo aparecen aquí sus sesiones, con su día "
                 "de la semana.",
                 objetivo="vista_programas.sesiones"),
            Paso("Los ejercicios de la sesión",
                 "Las líneas de trabajo, en orden. «Subir» y «Bajar» cambian el "
                 "orden en que se imprimen.",
                 objetivo="vista_programas.tabla"),
            Paso("Añadir ejercicio",
                 "La ventana más importante del programa. Ahí se decide la carga, "
                 "y la carga se guarda como intención —%1RM, RPE, RIR— no como "
                 "kilos: los kilos se calculan al imprimir con el 1RM de cada uno.",
                 objetivo="vista_programas.btn_nueva_linea"),
            Paso("La banda de avisos",
                 "Señala lo que no cuadra en la plantilla: microciclos sin "
                 "sesiones, sesiones vacías, cargas que no se podrán calcular por "
                 "falta de 1RM. Conviene dejarla en blanco antes de asignar.",
                 objetivo="vista_programas.avisos"),
        ),
    ),
    Guion(
        clave="asignar",
        titulo="Asignar un programa y sacarlo en papel",
        resumen="Cómo una plantilla se convierte en el entrenamiento de alguien.",
        pasos=(
            Paso("Las asignaciones",
                 "Cada fila es una persona con un programa y unas fechas. La "
                 "columna «Quedan» son los días hasta el final: cuando baja de 14, "
                 "el panel empieza a pedir la encuesta de renovación.",
                 seccion="asignaciones", objetivo="vista_asignaciones.tabla"),
            Paso("Asignar programa",
                 "Persona, programa y fecha de inicio. Antes de guardar se ve el "
                 "calendario completo que se va a congelar, con las fechas reales "
                 "de cada ciclo.",
                 objetivo="vista_asignaciones.btn_nueva"),
            Paso("El calendario queda firme",
                 "Una vez asignado, cambiar la plantilla no mueve esta asignación. "
                 "Es deliberado: si no, cambiarías el entrenamiento de alguien sin "
                 "darte cuenta.",
                 objetivo="vista_asignaciones.detalle"),
            Paso("Imprimir",
                 "Eliges desde y hasta qué semana. Las cargas se convierten a "
                 "kilos en ese momento, con el 1RM que la persona tenga hoy. Si no "
                 "hay 1RM, el PDF pone «por determinar» en vez de inventarse un "
                 "peso.",
                 objetivo="vista_asignaciones.acciones"),
        ),
    ),
    Guion(
        clave="encuesta",
        titulo="El aviso de los 14 días, de punta a punta",
        resumen="El automatismo central: cómo se prepara, se aprueba y se envía.",
        pasos=(
            Paso("La bandeja de salida",
                 "Todo el correo pasa por aquí y espera. Nunca sale nada que no "
                 "hayas visto, salvo que enciendas el modo vacaciones.",
                 seccion="correo", objetivo="vista_correo.tabla"),
            Paso("Buscar avisos pendientes",
                 "Mira qué toca —programas que vencen a 14 días, bienvenidas, "
                 "recordatorios— y redacta los borradores, con el enlace al "
                 "formulario ya prerrellenado con la identificación de la persona.",
                 objetivo="vista_correo.btn_buscar"),
            Paso("Tu impresión personal",
                 "Esto es lo que hace que no parezca un correo automático. Lo que "
                 "escribas aquí se integra dentro del cuerpo, no pegado al final.",
                 objetivo="vista_correo.nota"),
            Paso("La vista previa",
                 "El correo tal y como lo va a recibir. Pulsa «Actualizar vista "
                 "previa» después de escribir tu nota para verla incorporada.",
                 objetivo="vista_correo.vista"),
            Paso("Aprobar y enviar",
                 "«Aprobar» lo deja listo sin enviarlo; «Aprobar y enviar» lo "
                 "manda ya. «Enviarme una prueba» te lo manda a ti primero, que es "
                 "lo prudente las primeras veces.",
                 objetivo="vista_correo.acciones"),
            Paso("Importar respuestas",
                 "Cuando contesten, carga aquí el CSV del formulario. Si alguien "
                 "pide cita o declara una molestia, aparece como aviso en el panel "
                 "de inicio.",
                 objetivo="vista_correo.btn_importar"),
            Paso("Probar la conexión",
                 "Antes de enviar nada real, comprueba que la cuenta y la "
                 "contraseña de aplicación funcionan.",
                 objetivo="vista_correo.btn_probar"),
        ),
    ),
)

RECORRIDOS: dict[str, Guion] = {g.clave: g for g in GUIONES}


# ==================================================================== el motor

class _Burbuja(QFrame):
    """El cartel con la explicación del paso."""

    def __init__(self, padre: QWidget):
        super().__init__(padre)
        self.setObjectName("burbuja")
        self.setFixedWidth(360)

        caja = QVBoxLayout(self)
        caja.setContentsMargins(16, 14, 16, 12)
        self.titulo = QLabel()
        self.titulo.setObjectName("burbuja_titulo")
        self.titulo.setWordWrap(True)
        caja.addWidget(self.titulo)
        self.texto = QLabel()
        self.texto.setWordWrap(True)
        self.texto.setObjectName("burbuja_texto")
        caja.addWidget(self.texto)

        pie = QHBoxLayout()
        self.contador = QLabel()
        self.contador.setObjectName("burbuja_contador")
        pie.addWidget(self.contador)
        pie.addStretch()
        self.btn_salir = QPushButton("Salir")
        self.btn_salir.setProperty("burbuja_plano", True)
        self.btn_atras = QPushButton("Anterior")
        self.btn_atras.setProperty("burbuja_plano", True)
        self.btn_siguiente = QPushButton("Siguiente")
        for boton in (self.btn_salir, self.btn_atras, self.btn_siguiente):
            pie.addWidget(boton)
        caja.addLayout(pie)


class Recorrido(QWidget):
    """Capa que oscurece la ventana, destaca un control y explica el paso.

    Se monta como hijo de la ventana principal y se traga los clics: el
    recorrido explica, no pide que trastees mientras está abierto.
    """

    def __init__(self, principal: QWidget, guion: Guion):
        super().__init__(principal)
        self.principal = principal
        self.guion = guion
        self.indice = 0
        self._objetivo: QWidget | None = None

        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setGeometry(principal.rect())

        self.burbuja = _Burbuja(self)
        self.burbuja.btn_salir.clicked.connect(self.terminar)
        self.burbuja.btn_atras.clicked.connect(self.anterior)
        self.burbuja.btn_siguiente.clicked.connect(self.siguiente)

        principal.installEventFilter(self)
        self.show()
        self.raise_()
        self.setFocus()
        self._pintar_paso()

    # ---------------------------------------------------------------- recorrer
    @property
    def paso(self) -> Paso:
        return self.guion.pasos[self.indice]

    def siguiente(self) -> None:
        if self.indice + 1 >= len(self.guion.pasos):
            self.terminar()
            return
        self.indice += 1
        self._pintar_paso()

    def anterior(self) -> None:
        if self.indice > 0:
            self.indice -= 1
            self._pintar_paso()

    def terminar(self) -> None:
        self.principal.removeEventFilter(self)
        self.hide()
        self.deleteLater()

    # ------------------------------------------------------------------ pintar
    def _resolver(self, ruta: str | None) -> QWidget | None:
        """Busca el widget que señala el paso, por su ruta de atributos."""
        if not ruta:
            return None
        objeto = self.principal
        for parte in ruta.split("."):
            objeto = getattr(objeto, parte, None)
            if objeto is None:
                return None
        if isinstance(objeto, (list, tuple)):          # grupos de botones
            visibles = [w for w in objeto if isinstance(w, QWidget)]
            if not visibles:
                return None
            # Un solo rectángulo que abarque todo el grupo.
            objeto = visibles[0] if len(visibles) == 1 else _Grupo(visibles)
        return objeto if isinstance(objeto, (QWidget, _Grupo)) else None

    def _pintar_paso(self) -> None:
        paso = self.paso
        if paso.seccion and hasattr(self.principal, "ir_a"):
            self.principal.ir_a(paso.seccion)
        self._objetivo = self._resolver(paso.objetivo)

        total = len(self.guion.pasos)
        self.burbuja.titulo.setText(paso.titulo)
        self.burbuja.texto.setText(paso.texto)
        self.burbuja.contador.setText(f"{self.indice + 1} de {total}")
        self.burbuja.btn_atras.setEnabled(self.indice > 0)
        self.burbuja.btn_siguiente.setText(
            "Terminar" if self.indice + 1 == total else "Siguiente")

        self.setGeometry(self.principal.rect())
        self.raise_()
        self._colocar_burbuja()
        self.update()

    def _hueco(self) -> QRect | None:
        """El rectángulo del control destacado, en coordenadas de esta capa."""
        objetivo = self._objetivo
        if objetivo is None:
            return None
        if isinstance(objetivo, _Grupo):
            rectangulo = None
            for widget in objetivo.widgets:
                if not widget.isVisible():
                    continue
                trozo = QRect(widget.mapTo(self.principal, QPoint(0, 0)), widget.size())
                rectangulo = trozo if rectangulo is None else rectangulo.united(trozo)
            return rectangulo.adjusted(-6, -6, 6, 6) if rectangulo else None
        if not objetivo.isVisible():
            return None
        rectangulo = QRect(objetivo.mapTo(self.principal, QPoint(0, 0)), objetivo.size())
        return rectangulo.adjusted(-6, -6, 6, 6)

    def _colocar_burbuja(self) -> None:
        hueco = self._hueco()
        ancho, alto = self.burbuja.width(), self.burbuja.sizeHint().height()
        self.burbuja.resize(ancho, alto)
        if hueco is None:
            self.burbuja.move((self.width() - ancho) // 2, (self.height() - alto) // 2)
            return
        # Debajo si cabe, si no encima; y si tampoco, al lado.
        x = min(max(12, hueco.center().x() - ancho // 2), self.width() - ancho - 12)
        if hueco.bottom() + alto + 18 <= self.height():
            y = hueco.bottom() + 14
        elif hueco.top() - alto - 18 >= 0:
            y = hueco.top() - alto - 14
        else:
            y = max(12, min(hueco.center().y() - alto // 2, self.height() - alto - 12))
            x = (hueco.right() + 14 if hueco.right() + ancho + 26 <= self.width()
                 else max(12, hueco.left() - ancho - 14))
        self.burbuja.move(x, y)

    def paintEvent(self, evento) -> None:
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.Antialiasing)
        sombra = QPainterPath()
        sombra.addRect(self.rect())
        hueco = self._hueco()
        if hueco is not None:
            recorte = QPainterPath()
            recorte.addRoundedRect(hueco, 5, 5)
            sombra = sombra.subtracted(recorte)
        pintor.fillPath(sombra, QColor(6, 48, 90, 160))
        if hueco is not None:
            pintor.setPen(QPen(QColor(estilo.BLANCO), 2))
            pintor.drawRoundedRect(hueco, 5, 5)

    # ------------------------------------------------------------------ teclado
    def keyPressEvent(self, evento) -> None:
        if evento.key() in (Qt.Key_Escape,):
            self.terminar()
        elif evento.key() in (Qt.Key_Right, Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.siguiente()
        elif evento.key() == Qt.Key_Left:
            self.anterior()
        else:
            super().keyPressEvent(evento)

    def mousePressEvent(self, evento) -> None:
        """Se traga el clic para que no se toque la ventana por debajo."""
        evento.accept()

    def eventFilter(self, objeto, evento) -> bool:
        if objeto is self.principal and evento.type() == QEvent.Resize:
            self.setGeometry(self.principal.rect())
            self._colocar_burbuja()
            self.update()
        return False


class _Grupo:
    """Varios widgets destacados a la vez, como una fila de botones."""

    def __init__(self, widgets: list[QWidget]):
        self.widgets = widgets
