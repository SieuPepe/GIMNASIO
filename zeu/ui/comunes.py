"""Piezas de interfaz reutilizadas por varias ventanas."""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import QComboBox, QDateEdit, QLabel, QMessageBox, QWidget

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
