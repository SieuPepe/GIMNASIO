"""Piezas de interfaz reutilizadas por varias ventanas."""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate, QEvent, Qt, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QComboBox, QDateEdit, QLabel, QLineEdit, QListView, QMessageBox,
    QTableWidget, QWidget,
)

from ..datos.libro import LibroBloqueado, LibroModificadoFuera
from ..datos.repositorio import ErrorValidacion


def campo_fecha(valor: date | None = None, opcional: bool = False) -> QDateEdit:
    campo = QDateEdit()
    campo.setCalendarPopup(True)
    campo.setDisplayFormat("dd/MM/yyyy")
    if opcional:
        campo.setSpecialValueText(" ")
        campo.setMinimumDate(QDate(1900, 1, 1))
    campo.setDate(QDate(valor.year, valor.month, valor.day) if valor
                  else (QDate(1900, 1, 1) if opcional else QDate.currentDate()))
    return campo


def leer_fecha(campo: QDateEdit) -> date | None:
    qd = campo.date()
    if qd == QDate(1900, 1, 1) and campo.specialValueText().strip() == "":
        return None
    return date(qd.year(), qd.month(), qd.day())


def desplegable(opciones: list[tuple[str, str]], valor: str | None = None,
                vacio: bool = False) -> QComboBox:
    """opciones = [(valor_guardado, texto_visible)]"""
    combo = QComboBox()
    if vacio:
        combo.addItem("", None)
    for clave, texto in opciones:
        combo.addItem(texto, clave)
    if valor is not None:
        indice = combo.findData(valor)
        if indice >= 0:
            combo.setCurrentIndex(indice)
    return combo


def etiqueta(texto: str, objeto: str | None = None, ajustar: bool = False) -> QLabel:
    lbl = QLabel(texto)
    if objeto:
        lbl.setObjectName(objeto)
    if ajustar:
        lbl.setWordWrap(True)
    lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
    return lbl


def avisar_error(padre: QWidget, titulo: str, error: Exception) -> None:
    """Traduce los errores de la capa de datos a algo que se entienda."""
    if isinstance(error, ErrorValidacion):
        texto = "Revisa estos puntos:\n\n• " + "\n• ".join(error.errores)
    elif isinstance(error, LibroBloqueado):
        texto = (f"{error}\n\nEl libro de datos está abierto en Excel. "
                 "Ciérralo y vuelve a guardar: no se ha perdido nada.")
    elif isinstance(error, LibroModificadoFuera):
        texto = (f"{error}\n\nAlguien ha modificado el libro por fuera. "
                 "Cierra la aplicación sin guardar y vuelve a abrirla para "
                 "trabajar sobre la versión actual.")
    else:
        texto = str(error)
    QMessageBox.warning(padre, titulo, texto)


def confirmar(padre: QWidget, titulo: str, pregunta: str) -> bool:
    return QMessageBox.question(
        padre, titulo, pregunta,
        QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes


def preseleccionar(tabla: QTableWidget) -> None:
    """Deja elegida la primera fila de la tabla.

    Los botones que necesitan una fila nacen apagados, y eso se lee como que
    el programa no responde. Con una fila ya elegida, al entrar en la vista
    todos los botones hacen algo.
    """
    if tabla.rowCount() and not tabla.selectionModel().selectedRows():
        tabla.selectRow(0)


def abrir_fichero(ruta) -> None:
    """Abre un fichero con el programa que le corresponda en el sistema."""
    import subprocess
    import sys
    try:
        if sys.platform.startswith("win"):
            import os
            os.startfile(str(ruta))          # noqa: S606
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(ruta)])
        else:
            subprocess.Popen(["xdg-open", str(ruta)])
    except Exception:
        pass


def hacer_buscable(combo: QComboBox) -> QComboBox:
    """Deja escribir dentro del desplegable para filtrar sus opciones.

    Filtra por cualquier parte del texto y sin mirar mayúsculas ni acentos, y no
    admite valores nuevos: lo que se escribe sirve para buscar, no para añadir.
    """
    combo.setEditable(True)
    combo.setInsertPolicy(QComboBox.NoInsert)
    completador = combo.completer()
    if completador is not None:
        completador.setCaseSensitivity(Qt.CaseInsensitive)
        completador.setFilterMode(Qt.MatchContains)
        completador.setCompletionMode(completador.CompletionMode.PopupCompletion)
    return combo


class DesplegableMultiple(QComboBox):
    """Desplegable con casillas: se pueden elegir varias opciones a la vez.

    Qt no trae nada parecido, así que esto es un desplegable normal con los
    elementos marcables y la lista que no se cierra al pulsar. Arriba se ve el
    resumen de lo elegido.
    """

    cambiado = Signal()

    def __init__(self, opciones: list[tuple[str, str]],
                 marcadas: list[str] | None = None,
                 texto_vacio: str = "Nada seleccionado",
                 texto_todas: str = "Todos", padre=None):
        super().__init__(padre)
        self.texto_vacio = texto_vacio
        self.texto_todas = texto_todas

        self.setModel(QStandardItemModel(self))
        self.setView(QListView())
        for clave, texto in opciones:
            item = QStandardItem(texto)
            item.setData(clave, Qt.UserRole)
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setCheckState(
                Qt.Checked if marcadas is None or clave in marcadas else Qt.Unchecked)
            self.model().appendRow(item)

        # Una caja de texto de solo lectura hace de resumen: el texto del
        # desplegable normal no admite varias opciones.
        self.setEditable(True)
        self.setLineEdit(QLineEdit())
        self.lineEdit().setReadOnly(True)
        self.lineEdit().setCursor(Qt.PointingHandCursor)
        self.lineEdit().installEventFilter(self)
        self.view().viewport().installEventFilter(self)
        self._resumir()

    # -- lectura y escritura --
    def marcadas(self) -> list[str]:
        modelo = self.model()
        return [modelo.item(i).data(Qt.UserRole) for i in range(modelo.rowCount())
                if modelo.item(i).checkState() == Qt.Checked]

    def marcar(self, claves: list[str]) -> None:
        modelo = self.model()
        for i in range(modelo.rowCount()):
            item = modelo.item(i)
            item.setCheckState(
                Qt.Checked if item.data(Qt.UserRole) in claves else Qt.Unchecked)
        self._resumir()
        self.cambiado.emit()

    # -- comportamiento --
    def eventFilter(self, objeto, evento) -> bool:
        if (objeto is self.view().viewport()
                and evento.type() == QEvent.MouseButtonRelease):
            indice = self.view().indexAt(evento.position().toPoint())
            if indice.isValid():
                item = self.model().itemFromIndex(indice)
                item.setCheckState(Qt.Unchecked
                                   if item.checkState() == Qt.Checked else Qt.Checked)
                self._resumir()
                self.cambiado.emit()
            return True      # la lista se queda abierta para seguir marcando
        if objeto is self.lineEdit() and evento.type() == QEvent.MouseButtonRelease:
            self.showPopup()
            return True
        return super().eventFilter(objeto, evento)

    def _resumir(self) -> None:
        modelo = self.model()
        marcadas = self.marcadas()
        if not marcadas:
            texto = self.texto_vacio
        elif len(marcadas) == modelo.rowCount():
            texto = self.texto_todas
        else:
            texto = ", ".join(
                modelo.item(i).text() for i in range(modelo.rowCount())
                if modelo.item(i).checkState() == Qt.Checked)
        self.lineEdit().setText(texto)
        self.setToolTip(texto)
