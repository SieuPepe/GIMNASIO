"""Panel de inicio: todo lo que requiere atención, en un sitio."""

from __future__ import annotations

from datetime import date
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QFrame, QGridLayout, QHBoxLayout, QHeaderView,
    QLabel, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from ..datos.repositorio import Repositorio
from ..nucleo.config import Config
from ..nucleo.fechas import formatear_largo, plural
from ..servicios import alertas as srv
from ..servicios import cola as srv_cola
from . import estilo
from .comunes import etiqueta

COLUMNAS = ["", "Dónde", "Qué pasa", "Detalle"]
COLOR_GRAVEDAD = {srv.ALERTA: estilo.ALERTA, srv.AVISO: estilo.MEDIO, srv.INFO: estilo.AZUL}
MARCA_GRAVEDAD = {srv.ALERTA: "!", srv.AVISO: "·", srv.INFO: "i"}


class Tarjeta(QFrame):
    """Un número grande que lleva a su pantalla."""

    def __init__(self, numero: str, texto: str, color: str,
                 al_pulsar: Callable[[], None] | None = None):
        super().__init__()
        self.al_pulsar = al_pulsar
        self.setStyleSheet(
            f"QFrame {{ background: white; border: 1px solid #DCE3E8;"
            f" border-top: 3px solid {color}; border-radius: 4px; }}"
            f"QFrame:hover {{ background: #F7FAFC; }}")
        if al_pulsar:
            self.setCursor(Qt.PointingHandCursor)
        caja = QVBoxLayout(self)
        caja.setContentsMargins(16, 12, 16, 12)
        grande = QLabel(numero)
        grande.setStyleSheet(
            f"font-size: 28px; font-weight: bold; color: {color}; border: none;")
        pequeno = QLabel(texto)
        pequeno.setStyleSheet("color: #6C7A85; border: none;")
        pequeno.setWordWrap(True)
        caja.addWidget(grande)
        caja.addWidget(pequeno)

    def mouseReleaseEvent(self, evento) -> None:      # noqa: N802 (API de Qt)
        if self.al_pulsar:
            self.al_pulsar()
        super().mouseReleaseEvent(evento)


class VistaInicio(QWidget):
    def __init__(self, repo: Repositorio, cfg: Config,
                 ir_a: Callable[[str, str | None], None] | None = None,
                 guardar: Callable[[], bool] | None = None, padre=None):
        super().__init__(padre)
        self.repo = repo
        self.cfg = cfg
        self.ir_a = ir_a or (lambda seccion, id_usuario=None: None)
        self.guardar = guardar or (lambda: True)
        self.alertas: list[srv.Alerta] = []
        self._construir()
        self.refrescar()

    def _construir(self) -> None:
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(24, 20, 24, 20)
        cabecera = QHBoxLayout()
        titulo = QVBoxLayout()
        titulo.addWidget(etiqueta("Panel de inicio", "titulo"))
        self.subtitulo = etiqueta("", "subtitulo")
        titulo.addWidget(self.subtitulo)
        cabecera.addLayout(titulo)
        cabecera.addStretch()
        actualizar = QPushButton("Actualizar")
        actualizar.setProperty("plano", True)
        actualizar.clicked.connect(self.refrescar)
        cabecera.addWidget(actualizar)
        buscar = QPushButton("Buscar avisos de correo")
        buscar.clicked.connect(self.buscar_correos)
        cabecera.addWidget(buscar)
        raiz.addLayout(cabecera)

        self.rejilla = QGridLayout()
        self.rejilla.setSpacing(12)
        raiz.addLayout(self.rejilla)

        fila = QHBoxLayout()
        self.encabezado_lista = etiqueta("")
        fila.addWidget(self.encabezado_lista)
        fila.addStretch()
        self.solo_urgentes = QCheckBox("Solo lo que requiere atención")
        self.solo_urgentes.stateChanged.connect(self._pintar_lista)
        fila.addWidget(self.solo_urgentes)
        raiz.addLayout(fila)

        self.tabla = QTableWidget(0, len(COLUMNAS))
        self.tabla.setHorizontalHeaderLabels(COLUMNAS)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)
        cabecera_tabla = self.tabla.horizontalHeader()
        cabecera_tabla.setSectionResizeMode(QHeaderView.ResizeToContents)
        cabecera_tabla.setSectionResizeMode(3, QHeaderView.Stretch)
        self.tabla.itemDoubleClicked.connect(lambda *_: self.abrir())
        self.tabla.itemSelectionChanged.connect(self._actualizar_botones)
        raiz.addWidget(self.tabla, 1)

        botones = QHBoxLayout()
        self.btn_abrir = QPushButton("Abrir")
        self.btn_abrir.clicked.connect(self.abrir)
        botones.addWidget(self.btn_abrir)
        self.btn_atender = QPushButton("Marcar como atendida")
        self.btn_atender.setProperty("plano", True)
        self.btn_atender.clicked.connect(self.atender)
        botones.addWidget(self.btn_atender)
        botones.addStretch()
        raiz.addLayout(botones)

    # -- datos --
    def refrescar(self) -> None:
        self.alertas = srv.revisar(self.repo, self.cfg)
        conteo = srv.contar(self.alertas)
        usuarios = self.repo.listar("T_USUARIOS", lambda u: u.get("Estado") == "ACTIVO")
        en_curso = self.repo.listar("T_ASIGNACIONES",
                                    lambda a: a.get("Estado") == "EN_CURSO")
        pendientes = srv_cola.pendientes(self.repo)

        self.subtitulo.setText(
            formatear_largo(date.today()).capitalize()
            + f" · {plural(len(usuarios), 'usuario activo', 'usuarios activos')}")

        while self.rejilla.count():
            elemento = self.rejilla.takeAt(0)
            anterior = elemento.widget()
            if anterior is not None:
                # Hay que quedarse con la referencia antes de desvincularlo:
                # tras setParent(None) el elemento ya no devuelve el widget.
                anterior.setParent(None)
                anterior.deleteLater()
        tarjetas = [
            (str(conteo[srv.ALERTA]), "requieren atención",
             estilo.ALERTA if conteo[srv.ALERTA] else estilo.BUENO, None),
            (str(conteo[srv.AVISO]), "conviene mirar",
             estilo.MEDIO if conteo[srv.AVISO] else estilo.BUENO, None),
            (str(len(en_curso)), "programas en curso", estilo.AZUL, "asignaciones"),
            (str(len(pendientes)), "correos en la bandeja",
             estilo.AZUL if pendientes else estilo.BUENO, "correo"),
        ]
        for columna, (numero, texto, color, seccion) in enumerate(tarjetas):
            accion = (lambda s=seccion: self.ir_a(s, None)) if seccion else None
            self.rejilla.addWidget(Tarjeta(numero, texto, color, accion), 0, columna)

        self._pintar_lista()

    def _visibles(self) -> list[srv.Alerta]:
        if self.solo_urgentes.isChecked():
            return [a for a in self.alertas if a.gravedad == srv.ALERTA]
        return self.alertas

    def _pintar_lista(self) -> None:
        visibles = self._visibles()
        self.encabezado_lista.setText(
            plural(len(visibles), "cosa pendiente", "cosas pendientes") if visibles
            else "Nada pendiente. Todo al día.")

        self.tabla.blockSignals(True)
        self.tabla.setRowCount(len(visibles))
        for fila, alerta in enumerate(visibles):
            valores = [MARCA_GRAVEDAD.get(alerta.gravedad, ""), alerta.grupo,
                       alerta.titulo, alerta.detalle]
            for columna, texto in enumerate(valores):
                item = QTableWidgetItem(texto)
                item.setData(Qt.UserRole, fila)
                if columna == 0:
                    item.setForeground(QColor(COLOR_GRAVEDAD.get(alerta.gravedad)))
                    fuente = QFont()
                    fuente.setBold(True)
                    item.setFont(fuente)
                    item.setTextAlignment(Qt.AlignCenter)
                if columna == 2 and alerta.gravedad == srv.ALERTA:
                    fuente = QFont()
                    fuente.setBold(True)
                    item.setFont(fuente)
                item.setToolTip(f"{alerta.titulo}\n{alerta.detalle}")
                self.tabla.setItem(fila, columna, item)
        self.tabla.blockSignals(False)
        self._actualizar_botones()

    def seleccionada(self) -> srv.Alerta | None:
        filas = self.tabla.selectionModel().selectedRows() if self.tabla.rowCount() else []
        if not filas:
            return None
        return self._visibles()[self.tabla.item(filas[0].row(), 0).data(Qt.UserRole)]

    def _actualizar_botones(self) -> None:
        alerta = self.seleccionada()
        self.btn_abrir.setEnabled(bool(alerta and alerta.seccion))
        self.btn_atender.setEnabled(bool(alerta and alerta.atendible))

    # -- acciones --
    def abrir(self) -> None:
        alerta = self.seleccionada()
        if alerta and alerta.seccion:
            self.ir_a(alerta.seccion, alerta.id_usuario)

    def atender(self) -> None:
        alerta = self.seleccionada()
        if not alerta or not alerta.atendible:
            return
        srv.marcar_atendida(self.repo, alerta.id_respuesta)
        if self.guardar():
            self.refrescar()

    def buscar_correos(self) -> None:
        creados = srv_cola.generar_borradores(self.repo, self.cfg)
        if creados:
            self.guardar()
        self.refrescar()
        QMessageBox.information(
            self, "Avisos de correo",
            plural(len(creados), "borrador nuevo", "borradores nuevos")
            + " en la bandeja." if creados else "No hay nada nuevo que enviar.")
