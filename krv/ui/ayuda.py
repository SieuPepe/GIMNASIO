"""Ayuda de ventana: el botón «?» de cada título y el panel que abre.

El texto no está aquí, está en ayuda_contenido.py. Esto solo lo convierte en
HTML y lo enseña, y se encarga de que los enlaces del panel sepan llevar a la
ventana de la que hablan.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QPushButton, QTextBrowser, QVBoxLayout, QWidget,
)

from . import estilo
from .ayuda_contenido import Ayuda, Pagina, entrada, titulo_de
from .comunes import etiqueta

ESQUEMA_VENTANA = "krv"      # krv:usuarios  -> abre esa página de ayuda
ESQUEMA_SECCION = "seccion"  # seccion:usuarios -> lleva a esa sección
ESQUEMA_RECORRIDO = "recorrido"  # recorrido:alta_usuario -> arranca el recorrido


# ------------------------------------------------------------------ a HTML

CABECERA = f"""
<style>
  body {{ font-family: "Segoe UI", "Noto Sans", sans-serif; font-size: 13px;
         color: {estilo.GRIS_TEXTO}; }}
  h1 {{ font-size: 19px; color: {estilo.AZUL_OSCURO}; margin: 0 0 2px 0; }}
  h2 {{ font-size: 14px; color: {estilo.AZUL_OSCURO}; margin: 18px 0 6px 0; }}
  .donde {{ color: #6C7A85; font-size: 12px; margin: 0 0 12px 0; }}
  .control {{ margin: 0 0 7px 0; }}
  .nombre {{ color: {estilo.AZUL_OSCURO}; font-weight: bold; }}
  .regla {{ margin: 0 0 7px 0; }}
  .sintoma {{ color: {estilo.AZUL_OSCURO}; font-weight: bold; }}
  a {{ color: {estilo.AZUL}; text-decoration: none; }}
  tt {{ background: {estilo.GRIS_FONDO}; }}
</style>
"""


def _enlace(clave: str) -> str:
    return f'<a href="{ESQUEMA_VENTANA}:{clave}">{titulo_de(clave)}</a>'


def _html_ayuda(ayuda: Ayuda, con_acciones: bool = True) -> str:
    partes = [f"<h1>{ayuda.titulo}</h1>", f'<p class="donde">{ayuda.donde}</p>',
              f"<p>{ayuda.para_que}</p>"]

    if con_acciones:
        acciones = []
        if ayuda.seccion:
            acciones.append(
                f'<a href="{ESQUEMA_SECCION}:{ayuda.seccion}">▸ Abrir esta ventana</a>')
        if ayuda.recorrido:
            acciones.append(
                f'<a href="{ESQUEMA_RECORRIDO}:{ayuda.recorrido}">'
                "▸ Hacer el recorrido guiado</a>")
        if acciones:
            partes.append("<p>" + " &nbsp;·&nbsp; ".join(acciones) + "</p>")

    if ayuda.controles:
        partes.append("<h2>Qué hace cada cosa</h2>")
        for control in ayuda.controles:
            partes.append(f'<p class="control"><span class="nombre">'
                          f"{control.nombre}</span> — {control.que_hace}</p>")

    if ayuda.flujo:
        partes.append("<h2>El camino habitual</h2><ol>")
        partes += [f"<li>{paso}</li>" for paso in ayuda.flujo]
        partes.append("</ol>")

    if ayuda.reglas:
        partes.append("<h2>Cosas que conviene saber</h2>")
        partes += [f'<p class="regla">• {regla}</p>' for regla in ayuda.reglas]

    if ayuda.problemas:
        partes.append("<h2>Si algo no sale</h2>")
        for problema in ayuda.problemas:
            partes.append(f'<p class="regla"><span class="sintoma">'
                          f"{problema.sintoma}</span><br>{problema.solucion}</p>")

    if ayuda.ver_tambien:
        partes.append("<h2>Ver también</h2><p>" +
                      " &nbsp;·&nbsp; ".join(_enlace(c) for c in ayuda.ver_tambien) +
                      "</p>")

    return CABECERA + "".join(partes)


def _html_pagina(pagina: Pagina, con_acciones: bool = True) -> str:
    partes = [f"<h1>{pagina.titulo}</h1>"]
    if con_acciones:
        acciones = []
        if pagina.seccion:
            acciones.append(
                f'<a href="{ESQUEMA_SECCION}:{pagina.seccion}">▸ Abrir esa ventana</a>')
        if pagina.recorrido:
            acciones.append(
                f'<a href="{ESQUEMA_RECORRIDO}:{pagina.recorrido}">'
                "▸ Hacer el recorrido guiado</a>")
        if acciones:
            partes.append("<p>" + " &nbsp;·&nbsp; ".join(acciones) + "</p>")
    partes.append(pagina.cuerpo)
    return CABECERA + "".join(partes)


def a_html(clave: str, con_acciones: bool = True) -> str:
    """El HTML de una página, sea de ventana o de manual."""
    objeto = entrada(clave)
    if objeto is None:
        return CABECERA + f"<h1>Sin ayuda</h1><p>No hay página para «{clave}».</p>"
    if isinstance(objeto, Ayuda):
        return _html_ayuda(objeto, con_acciones)
    return _html_pagina(objeto, con_acciones)


# ------------------------------------------------------- navegación de enlaces

def seguir_enlace(origen: QWidget, url) -> bool:
    """Interpreta los enlaces del panel. Devuelve si lo ha podido atender.

    Los esquemas propios (krv:, seccion:, recorrido:) se resuelven buscando en
    la ventana principal, que es la única que sabe navegar y montar recorridos.
    """
    esquema = url.scheme()
    destino = url.path() or url.toString().split(":", 1)[-1]
    principal = origen.window()
    # El panel de ayuda es una ventana suelta: la principal es su padre.
    if not hasattr(principal, "ir_a") and origen.parent() is not None:
        principal = origen.parent().window()

    if esquema == ESQUEMA_SECCION:
        if hasattr(principal, "ir_a"):
            principal.ir_a(destino)
            return True
    elif esquema == ESQUEMA_RECORRIDO:
        if hasattr(principal, "iniciar_recorrido"):
            principal.iniciar_recorrido(destino)
            return True
    elif esquema == ESQUEMA_VENTANA:
        if hasattr(principal, "abrir_manual"):
            principal.abrir_manual(destino)
        else:
            abrir_ayuda(origen, destino)
        return True
    return False


# ------------------------------------------------------------------- el panel

class PanelAyuda(QDialog):
    """La ayuda de una ventana, en una ventana aparte que no bloquea.

    No es modal a propósito: la idea es tenerla abierta al lado mientras se
    trastea con la ventana de la que habla.
    """

    def __init__(self, clave: str, padre: QWidget | None = None):
        super().__init__(padre)
        self.clave = clave
        self.setModal(False)
        self.setWindowTitle(f"Ayuda · {titulo_de(clave)}")
        self.resize(560, 640)

        raiz = QVBoxLayout(self)
        self.texto = QTextBrowser()
        self.texto.setOpenLinks(False)
        self.texto.setOpenExternalLinks(False)
        self.texto.anchorClicked.connect(self._enlace)
        raiz.addWidget(self.texto)

        pie = QHBoxLayout()
        self.btn_manual = QPushButton("Abrir el manual completo")
        self.btn_manual.setProperty("plano", True)
        self.btn_manual.clicked.connect(self._manual)
        pie.addWidget(self.btn_manual)
        pie.addStretch()
        cerrar = QPushButton("Cerrar")
        cerrar.clicked.connect(self.close)
        pie.addWidget(cerrar)
        raiz.addLayout(pie)

        self.mostrar(clave)

    def mostrar(self, clave: str) -> None:
        self.clave = clave
        self.setWindowTitle(f"Ayuda · {titulo_de(clave)}")
        self.texto.setHtml(a_html(clave))

    def _enlace(self, url) -> None:
        if url.scheme() == ESQUEMA_VENTANA:
            self.mostrar(url.path() or url.toString().split(":", 1)[-1])
            return
        if seguir_enlace(self, url):
            # Ir a una sección o arrancar un recorrido deja la ayuda estorbando.
            self.close()

    def _manual(self) -> None:
        principal = self.parent().window() if self.parent() else None
        if principal is not None and hasattr(principal, "abrir_manual"):
            principal.abrir_manual(self.clave)
            self.close()
        else:
            self.mostrar("que_es")


_ABIERTOS: dict[str, PanelAyuda] = {}


def abrir_ayuda(padre: QWidget, clave: str) -> PanelAyuda:
    """Abre (o trae al frente) el panel de ayuda de una ventana."""
    panel = _ABIERTOS.get(clave)
    if panel is None or not panel.isVisible():
        panel = PanelAyuda(clave, padre)
        _ABIERTOS[clave] = panel
    panel.show()
    panel.raise_()
    panel.activateWindow()
    return panel


# ------------------------------------------------- la cabecera con el botón «?»

def cabecera(titulo: str, clave: str, padre: QWidget) -> QHBoxLayout:
    """Fila de título con el botón de ayuda a la derecha.

    Todas las ventanas la usan, así que el «?» está siempre en el mismo sitio y
    F1 funciona en todas por igual.
    """
    fila = QHBoxLayout()
    fila.addWidget(etiqueta(titulo, "titulo"))
    fila.addStretch()
    boton = QPushButton("?")
    boton.setObjectName("ayuda")
    boton.setFixedSize(26, 26)
    boton.setToolTip(f"Ayuda de «{titulo_de(clave)}»   (F1)")
    boton.setCursor(Qt.PointingHandCursor)
    boton.clicked.connect(lambda: abrir_ayuda(padre, clave))
    fila.addWidget(boton, 0, Qt.AlignTop)
    padre.btn_ayuda = boton      # el recorrido guiado lo señala
    atajo_ayuda(padre, clave)
    return fila


def boton_ayuda(clave: str, padre: QWidget) -> QPushButton:
    """Solo el botón, para las ventanas que montan su cabecera a mano."""
    boton = QPushButton("?")
    boton.setObjectName("ayuda")
    boton.setFixedSize(26, 26)
    boton.setToolTip(f"Ayuda de «{titulo_de(clave)}»   (F1)")
    boton.setCursor(Qt.PointingHandCursor)
    boton.clicked.connect(lambda: abrir_ayuda(padre, clave))
    padre.btn_ayuda = boton
    atajo_ayuda(padre, clave)
    return boton


def atajo_ayuda(ventana: QWidget, clave: str) -> None:
    """Deja F1 abriendo la ayuda de esa ventana."""
    atajo = QShortcut(QKeySequence.HelpContents, ventana)
    atajo.activated.connect(lambda: abrir_ayuda(ventana, clave))
