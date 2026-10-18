"""El manual, dentro de la propia aplicación.

Es un manual que hace cosas: desde la página que habla de una ventana se puede
abrir esa ventana, y desde la que explica una tarea se puede arrancar el
recorrido guiado que la enseña sobre los controles de verdad.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout, QLineEdit, QMessageBox, QPushButton, QSplitter, QTextBrowser,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from ..nucleo.config import Config
from . import ayuda as may
from . import estilo
from .ayuda_contenido import CAPITULOS, entrada, titulo_de
from .comunes import abrir_fichero, avisar_error, etiqueta
from .recorrido import GUIONES, RECORRIDOS

CLAVE_RECORRIDOS = "__recorridos__"
PORTADA = "__portada__"


class VistaManual(QWidget):
    """Árbol de capítulos a la izquierda, contenido a la derecha."""

    def __init__(self, cfg: Config, ir_a: Callable[[str], None],
                 recorrido: Callable[[str], None], padre=None):
        super().__init__(padre)
        self.cfg = cfg
        self.ir_a = ir_a
        self.lanzar_recorrido = recorrido
        self.clave_actual = PORTADA
        self._construir()
        self._llenar_arbol()
        self.mostrar(PORTADA)

    # ------------------------------------------------------------- construcción
    def _construir(self) -> None:
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(24, 20, 24, 20)
        raiz.addLayout(may.cabecera("Manual y ayuda", "manual_ayuda", self))
        raiz.addWidget(etiqueta(
            "Cada ventana tiene además su propio botón «?» arriba a la derecha, "
            "o la tecla F1.", "subtitulo"))

        self.busqueda = QLineEdit()
        self.busqueda.setPlaceholderText(
            "Buscar en todo el manual: «1RM», «consentimiento», «clonar»…")
        self.busqueda.textChanged.connect(self._filtrar)
        raiz.addWidget(self.busqueda)

        division = QSplitter(Qt.Horizontal)

        self.arbol = QTreeWidget()
        self.arbol.setHeaderHidden(True)
        self.arbol.setMinimumWidth(265)
        self.arbol.currentItemChanged.connect(self._elegido)
        division.addWidget(self.arbol)

        self.texto = QTextBrowser()
        self.texto.setOpenLinks(False)
        self.texto.setOpenExternalLinks(False)
        self.texto.anchorClicked.connect(self._enlace)
        division.addWidget(self.texto)
        division.setStretchFactor(0, 0)
        division.setStretchFactor(1, 1)
        raiz.addWidget(division, 1)

        pie = QHBoxLayout()
        self.btn_ventana = QPushButton("Abrir esta ventana")
        self.btn_ventana.setProperty("plano", True)
        self.btn_ventana.clicked.connect(self._abrir_ventana)
        pie.addWidget(self.btn_ventana)
        self.btn_recorrido = QPushButton("Hacer el recorrido guiado")
        self.btn_recorrido.clicked.connect(self._hacer_recorrido)
        pie.addWidget(self.btn_recorrido)
        pie.addStretch()
        exportar = QPushButton("Guardar el manual completo…")
        exportar.setProperty("plano", True)
        exportar.clicked.connect(self.exportar)
        pie.addWidget(exportar)
        raiz.addLayout(pie)

    def _llenar_arbol(self) -> None:
        self.arbol.clear()
        portada = QTreeWidgetItem(["Portada"])
        portada.setData(0, Qt.UserRole, PORTADA)
        self.arbol.addTopLevelItem(portada)

        for capitulo in CAPITULOS:
            padre = QTreeWidgetItem([capitulo.titulo])
            padre.setToolTip(0, capitulo.resumen)
            padre.setFlags(padre.flags() & ~Qt.ItemIsSelectable)
            self.arbol.addTopLevelItem(padre)
            for clave in capitulo.entradas:
                hijo = QTreeWidgetItem([titulo_de(clave)])
                hijo.setData(0, Qt.UserRole, clave)
                padre.addChild(hijo)

        grupo = QTreeWidgetItem(["Recorridos guiados"])
        grupo.setFlags(grupo.flags() & ~Qt.ItemIsSelectable)
        self.arbol.addTopLevelItem(grupo)
        indice = QTreeWidgetItem(["Todos los recorridos"])
        indice.setData(0, Qt.UserRole, CLAVE_RECORRIDOS)
        grupo.addChild(indice)
        for guion in GUIONES:
            hijo = QTreeWidgetItem([guion.titulo])
            hijo.setData(0, Qt.UserRole, f"recorrido:{guion.clave}")
            hijo.setToolTip(0, guion.resumen)
            grupo.addChild(hijo)

        self.arbol.expandAll()

    # -------------------------------------------------------------- contenido
    def mostrar(self, clave: str) -> None:
        self.clave_actual = clave
        if clave == PORTADA:
            self.texto.setHtml(self._html_portada())
        elif clave == CLAVE_RECORRIDOS:
            self.texto.setHtml(self._html_recorridos())
        else:
            self.texto.setHtml(may.a_html(clave))
        self.texto.verticalScrollBar().setValue(0)
        self._actualizar_pie()

    def _actualizar_pie(self) -> None:
        objeto = entrada(self.clave_actual)
        seccion = getattr(objeto, "seccion", None)
        guion = getattr(objeto, "recorrido", None)
        self.btn_ventana.setEnabled(bool(seccion))
        self.btn_ventana.setText(
            f"Abrir «{titulo_de(seccion)}»" if seccion else "Abrir esta ventana")
        self.btn_recorrido.setEnabled(bool(guion))
        self.btn_recorrido.setText(
            f"Recorrido: {RECORRIDOS[guion].titulo}"
            if guion and guion in RECORRIDOS else "Hacer el recorrido guiado")

    def _html_portada(self) -> str:
        filas = []
        for capitulo in CAPITULOS:
            primera = capitulo.entradas[0]
            filas.append(
                f'<p><a href="{may.ESQUEMA_VENTANA}:{primera}"><b>{capitulo.titulo}'
                f"</b></a><br>{capitulo.resumen}</p>")
        recorridos = " &nbsp;·&nbsp; ".join(
            f'<a href="{may.ESQUEMA_RECORRIDO}:{g.clave}">{g.titulo}</a>'
            for g in GUIONES)
        return may.CABECERA + f"""
<h1>Manual de {self.cfg.negocio.nombre_comercial}</h1>
<p class="donde">{self.cfg.negocio.lema}</p>

<p>Este manual está dentro del programa a propósito: desde cada página puedes
abrir la ventana de la que habla, y en las tareas principales puedes pedir un
<b>recorrido guiado</b> que te va señalando los controles de verdad, uno a uno.</p>

<h2>Si es tu primera vez</h2>
<p><a href="{may.ESQUEMA_RECORRIDO}:primer_dia">▸ Darse una vuelta por el
programa</a> — seis pasos, cinco minutos. Es la forma más rápida de saber qué
hay en cada sitio.</p>

<h2>Capítulos</h2>
{''.join(filas)}

<h2>Recorridos guiados</h2>
<p>{recorridos}</p>

<h2>Cómo encontrar algo</h2>
<p>Escribe en el buscador de arriba: filtra el índice por cualquier palabra que
aparezca en el manual, también dentro de la descripción de los botones. Y en
cualquier ventana del programa, el botón <b>«?»</b> de la esquina —o <b>F1</b>—
abre directamente la ayuda de esa ventana.</p>

<h2>Tu marca, tal y como la está usando el programa</h2>
<p>Esto es lo que va impreso en los PDF y en la cabecera de cada correo. Si algo
no cuadra, sale de tu fichero de configuración, que es tuyo y no se toca al
actualizar el programa.</p>
{self._html_marca()}
"""

    def _html_marca(self) -> str:
        """Lo que el programa está usando de verdad como marca, y de dónde sale.

        Que el nombre o el lema se queden antiguos es un tropiezo fácil: la
        configuración es del usuario y no se actualiza con el programa. Verlos
        aquí, con el fichero del que salen, evita tener que adivinarlo.
        """
        negocio = self.cfg.negocio
        origen = self.cfg.ruta_config
        filas = [("Nombre comercial", negocio.nombre_comercial),
                 ("Lema", negocio.lema),
                 ("Contacto", negocio.contacto),
                 ("Horario de sala", negocio.horario_sala or "—"),
                 ("Remite los correos desde", self.cfg.correo.remitente)]
        celdas = "".join(
            f'<tr><td class="donde">{nombre}</td><td><b>{valor}</b></td></tr>'
            for nombre, valor in filas)
        if origen and Path(origen).exists():
            pie = (f'<p class="donde">Sale de {origen}. Para cambiarlo, edita ese '
                   "fichero y vuelve a arrancar el programa.</p>")
        else:
            pie = ('<p class="donde">No hay fichero de configuración, así que son '
                   "los valores de fábrica. Para cambiarlos, copia "
                   "<tt>config.ejemplo.toml</tt> como <tt>config.toml</tt>.</p>")
        return f'<table cellpadding="4">{celdas}</table>{pie}'

    def _html_recorridos(self) -> str:
        bloques = []
        for guion in GUIONES:
            pasos = "".join(f"<li>{p.titulo}</li>" for p in guion.pasos)
            bloques.append(
                f'<h2>{guion.titulo}</h2><p>{guion.resumen}</p>'
                f'<p><a href="{may.ESQUEMA_RECORRIDO}:{guion.clave}">'
                f"▸ Empezar este recorrido ({len(guion.pasos)} pasos)</a></p>"
                f"<ol>{pasos}</ol>")
        return may.CABECERA + f"""
<h1>Recorridos guiados</h1>
<p>Un recorrido oscurece la ventana, destaca el control del que habla y explica
qué hace. Se avanza con «Siguiente» o con las flechas del teclado, y se sale
con «Salir» o con la tecla Escape. No toca nada de tus datos.</p>
{''.join(bloques)}
"""

    # --------------------------------------------------------------- reacciones
    def _elegido(self, item: QTreeWidgetItem | None, _anterior=None) -> None:
        if item is None:
            return
        clave = item.data(0, Qt.UserRole)
        if not clave:
            return
        if clave.startswith("recorrido:"):
            self.mostrar(CLAVE_RECORRIDOS)
            self.lanzar_recorrido(clave.split(":", 1)[1])
            return
        self.mostrar(clave)

    def _enlace(self, url) -> None:
        esquema = url.scheme()
        destino = url.path() or url.toString().split(":", 1)[-1]
        if esquema == may.ESQUEMA_VENTANA:
            self.ir_al_tema(destino)
        elif esquema == may.ESQUEMA_SECCION:
            self.ir_a(destino)
        elif esquema == may.ESQUEMA_RECORRIDO:
            self.lanzar_recorrido(destino)

    def ir_al_tema(self, clave: str) -> None:
        """Enseña una página y deja el árbol señalándola."""
        self.mostrar(clave)
        for i in range(self.arbol.topLevelItemCount()):
            padre = self.arbol.topLevelItem(i)
            if padre.data(0, Qt.UserRole) == clave:
                self.arbol.setCurrentItem(padre)
                return
            for j in range(padre.childCount()):
                hijo = padre.child(j)
                if hijo.data(0, Qt.UserRole) == clave:
                    self.arbol.setCurrentItem(hijo)
                    return

    def _abrir_ventana(self) -> None:
        objeto = entrada(self.clave_actual)
        if objeto is not None and getattr(objeto, "seccion", None):
            self.ir_a(objeto.seccion)

    def _hacer_recorrido(self) -> None:
        objeto = entrada(self.clave_actual)
        if objeto is not None and getattr(objeto, "recorrido", None):
            self.lanzar_recorrido(objeto.recorrido)

    # ---------------------------------------------------------------- buscador
    def _filtrar(self, texto: str) -> None:
        buscado = _normalizar(texto)
        for i in range(self.arbol.topLevelItemCount()):
            padre = self.arbol.topLevelItem(i)
            visibles = 0
            for j in range(padre.childCount()):
                hijo = padre.child(j)
                clave = hijo.data(0, Qt.UserRole) or ""
                objeto = entrada(clave)
                fuente = (objeto.texto_buscable() if objeto is not None
                          else hijo.text(0))
                encaja = not buscado or buscado in _normalizar(fuente)
                hijo.setHidden(not encaja)
                visibles += encaja
            sin_hijos = padre.childCount() == 0
            propio = not buscado or buscado in _normalizar(padre.text(0))
            padre.setHidden(not (visibles or (sin_hijos and propio)))
        if buscado:
            self.arbol.expandAll()

    # --------------------------------------------------------------- exportar
    def exportar(self) -> None:
        """Vuelca el manual entero a un HTML, para leerlo fuera o imprimirlo."""
        carpeta = Path(self.cfg.datos.libro).parent / "salidas" / "manual"
        try:
            carpeta.mkdir(parents=True, exist_ok=True)
            ruta = carpeta / "manual_krv.html"
            ruta.write_text(self._html_completo(), encoding="utf-8")
        except Exception as error:
            avisar_error(self, "No se ha podido guardar el manual", error)
            return
        if QMessageBox.question(
                self, "Manual guardado",
                f"Manual guardado en:\n{ruta}\n\nSe abre en el navegador, y desde "
                "ahí se puede imprimir o guardar en PDF.\n\n¿Quieres abrirlo?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes) == QMessageBox.Yes:
            abrir_fichero(ruta)

    def _html_completo(self) -> str:
        """Todo el manual en un solo documento, sin los enlaces que solo
        funcionan dentro del programa."""
        partes = [f"<h1>Manual de {self.cfg.negocio.nombre_comercial}</h1>",
                  f'<p class="donde">{self.cfg.negocio.lema}</p>',
                  "<p>Documento generado por el propio programa. Dentro de la "
                  "aplicación, este mismo manual es navegable y puede abrir las "
                  "ventanas de las que habla.</p>", "<h2>Índice</h2><ul>"]
        for capitulo in CAPITULOS:
            partes.append(f"<li><b>{capitulo.titulo}</b>: " +
                          ", ".join(titulo_de(c) for c in capitulo.entradas) +
                          "</li>")
        partes.append("</ul>")
        for capitulo in CAPITULOS:
            partes.append(f"<hr><h1>{capitulo.titulo}</h1><p>{capitulo.resumen}</p>")
            for clave in capitulo.entradas:
                cuerpo = may.a_html(clave, con_acciones=False)
                partes.append(cuerpo.replace(may.CABECERA, ""))
        partes.append("<hr><h1>Recorridos guiados</h1>")
        for guion in GUIONES:
            pasos = "".join(f"<li><b>{p.titulo}</b> — {p.texto}</li>"
                            for p in guion.pasos)
            partes.append(f"<h2>{guion.titulo}</h2><p>{guion.resumen}</p>"
                          f"<ol>{pasos}</ol>")
        return ("<!doctype html><html lang=\"es\"><head><meta charset=\"utf-8\">"
                f"<title>Manual · {self.cfg.negocio.nombre_comercial}</title>"
                f"{may.CABECERA}</head><body>" + "".join(partes) +
                "</body></html>")


def _normalizar(texto: str) -> str:
    """Minúsculas y sin acentos: para que «valoracion» encuentre «valoración»."""
    import unicodedata
    plano = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in plano if not unicodedata.combining(c))
