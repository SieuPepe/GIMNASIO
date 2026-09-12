"""Listado de usuarios y acceso a sus ventanas de información adicional."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from ..datos.repositorio import Repositorio
from ..servicios import usuarios as srv
from . import estilo
from .comunes import avisar_error, confirmar, etiqueta
from .dialogos_usuario import DialogoDisponibilidad, DialogoObjetivos, DialogoSalud
from .ficha_usuario import FichaUsuario

COLUMNAS = ["ID", "Nombre", "Edad", "Sexo", "Correo", "Objetivo activo", "Estado", "Pendiente"]


class VistaUsuarios(QWidget):
    def __init__(self, repo: Repositorio, guardar: Callable[[], bool], padre=None):
        super().__init__(padre)
        self.repo = repo
        self.guardar = guardar
        self._construir()
        self.refrescar()

    def _construir(self) -> None:
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(24, 20, 24, 20)
        raiz.addWidget(etiqueta("Usuarios", "titulo"))
        self.contador = etiqueta("", "subtitulo")
        raiz.addWidget(self.contador)

        filtros = QHBoxLayout()
        self.busqueda = QLineEdit()
        self.busqueda.setPlaceholderText("Buscar por nombre, apellidos o correo…")
        self.busqueda.textChanged.connect(self.refrescar)
        self.filtro_estado = QComboBox()
        self.filtro_estado.addItem("Todos los estados", None)
        for clave, texto in (("ACTIVO", "Activos"), ("INACTIVO", "Inactivos"), ("BAJA", "Bajas")):
            self.filtro_estado.addItem(texto, clave)
        self.filtro_estado.setCurrentIndex(1)
        self.filtro_estado.currentIndexChanged.connect(self.refrescar)
        filtros.addWidget(self.busqueda, 3)
        filtros.addWidget(self.filtro_estado, 1)
        raiz.addLayout(filtros)

        self.tabla = QTableWidget(0, len(COLUMNAS))
        self.tabla.setHorizontalHeaderLabels(COLUMNAS)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.tabla.itemSelectionChanged.connect(self._actualizar_botones)
        self.tabla.itemDoubleClicked.connect(lambda *_: self.editar())
        raiz.addWidget(self.tabla)

        self.detalle = etiqueta("", "subtitulo", ajustar=True)
        raiz.addWidget(self.detalle)

        botones = QHBoxLayout()
        nuevo = QPushButton("Nuevo usuario")
        nuevo.clicked.connect(self.nuevo)
        botones.addWidget(nuevo)

        self.acciones: list[QPushButton] = []
        for texto, metodo in (
            ("Editar ficha", self.editar),
            ("Objetivos", lambda: self._abrir(DialogoObjetivos)),
            ("Salud y cribado", lambda: self._abrir(DialogoSalud)),
            ("Disponibilidad", lambda: self._abrir(DialogoDisponibilidad)),
        ):
            boton = QPushButton(texto)
            boton.setProperty("plano", True)
            boton.clicked.connect(metodo)
            botones.addWidget(boton)
            self.acciones.append(boton)

        botones.addStretch()
        self.btn_borrar = QPushButton("Borrar")
        self.btn_borrar.setProperty("plano", True)
        self.btn_borrar.clicked.connect(self.borrar)
        self.acciones.append(self.btn_borrar)
        botones.addWidget(self.btn_borrar)
        raiz.addLayout(botones)

    # -- datos --
    def _visibles(self) -> list[dict]:
        texto = self.busqueda.text().strip().lower()
        estado = self.filtro_estado.currentData()

        def coincide(u: dict) -> bool:
            if estado and u.get("Estado") != estado:
                return False
            if not texto:
                return True
            campos = " ".join(str(u.get(c) or "") for c in ("Nombre", "Apellidos", "Email"))
            return texto in campos.lower()

        return self.repo.listar("T_USUARIOS", coincide, orden="Apellidos")

    def refrescar(self) -> None:
        usuarios = self._visibles()
        total = len(self.repo.listar("T_USUARIOS"))
        self.contador.setText(
            f"{len(usuarios)} de {total} usuarios" if total else
            "Todavía no hay usuarios. Empieza por «Nuevo usuario».")

        self.tabla.blockSignals(True)
        self.tabla.setRowCount(len(usuarios))
        for fila, usuario in enumerate(usuarios):
            resumen = srv.resumen(self.repo, usuario)
            pendientes = srv.avisos(self.repo, usuario)
            valores = [
                resumen["id"], resumen["nombre_completo"],
                str(resumen["edad"]) if resumen["edad"] is not None else "",
                {"H": "Hombre", "M": "Mujer"}.get(resumen["sexo"], ""),
                resumen["email"], resumen["objetivo"], resumen["estado"],
                f"{len(pendientes)}" if pendientes else "",
            ]
            for columna, texto in enumerate(valores):
                item = QTableWidgetItem(texto)
                item.setData(Qt.UserRole, usuario.get("ID_Usuario"))
                if columna == 7 and pendientes:
                    item.setForeground(QColor(estilo.BAJO))
                    item.setToolTip("\n".join(pendientes))
                if resumen["cribado"] and resumen["cribado"].requiere_informe:
                    if columna == 1:
                        item.setForeground(QColor(estilo.ALERTA))
                        item.setToolTip("El cribado exige informe médico")
                self.tabla.setItem(fila, columna, item)
        self.tabla.blockSignals(False)
        self._actualizar_botones()

    def seleccionado(self) -> str | None:
        filas = self.tabla.selectionModel().selectedRows() if self.tabla.rowCount() else []
        if not filas:
            return None
        return self.tabla.item(filas[0].row(), 0).data(Qt.UserRole)

    def _actualizar_botones(self) -> None:
        hay = self.seleccionado() is not None
        for boton in self.acciones:
            boton.setEnabled(hay)
        id_usuario = self.seleccionado()
        if not id_usuario:
            self.detalle.setText("")
            return
        usuario = self.repo.obtener("T_USUARIOS", id_usuario) or {}
        pendientes = srv.avisos(self.repo, usuario)
        self.detalle.setText(
            "Pendiente: " + " · ".join(pendientes) if pendientes
            else "Ficha completa: consentimiento, cribado, objetivo y disponibilidad.")

    # -- acciones --
    def nuevo(self) -> None:
        dialogo = FichaUsuario(self.repo, padre=self)
        if dialogo.exec() and self.guardar():
            self.refrescar()

    def editar(self) -> None:
        id_usuario = self.seleccionado()
        if not id_usuario:
            return
        dialogo = FichaUsuario(self.repo, id_usuario, padre=self)
        if dialogo.exec() and self.guardar():
            self.refrescar()

    def _abrir(self, clase) -> None:
        id_usuario = self.seleccionado()
        if not id_usuario:
            return
        dialogo = clase(self.repo, id_usuario, padre=self)
        dialogo.exec()
        self.guardar()
        self.refrescar()

    def borrar(self) -> None:
        id_usuario = self.seleccionado()
        if not id_usuario:
            return
        usuario = self.repo.obtener("T_USUARIOS", id_usuario) or {}
        nombre = " ".join(x for x in (usuario.get("Nombre"), usuario.get("Apellidos")) if x)
        if not confirmar(self, "Borrar usuario",
                         f"¿Borrar a {nombre}?\n\nSi tiene objetivos, salud o "
                         "disponibilidad registrados, no se podrá borrar: en ese caso "
                         "es mejor marcarlo como BAJA."):
            return
        try:
            self.repo.borrar("T_USUARIOS", id_usuario)
        except Exception as error:
            avisar_error(self, "No se ha podido borrar", error)
            return
        if self.guardar():
            self.refrescar()
