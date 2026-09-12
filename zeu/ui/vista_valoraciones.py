"""Listado de valoraciones físicas y generación del informe."""

from __future__ import annotations

import subprocess
import sys
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QHBoxLayout, QHeaderView, QMessageBox,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from ..datos.repositorio import Repositorio
from ..nucleo.config import Config
from ..nucleo.fechas import formatear
from ..servicios import informes
from ..servicios import valoracion as srv
from . import estilo
from .comunes import avisar_error, etiqueta
from .dialogo_valoracion import DialogoValoracion

COLUMNAS = ["ID", "Fecha", "Usuario", "Tipo", "Protocolo", "Pruebas", "Global", "Hallazgos"]


class VistaValoraciones(QWidget):
    def __init__(self, repo: Repositorio, cfg: Config,
                 guardar: Callable[[], bool], padre=None):
        super().__init__(padre)
        self.repo = repo
        self.cfg = cfg
        self.guardar = guardar
        self._construir()
        self.refrescar()

    def _construir(self) -> None:
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(24, 20, 24, 20)
        raiz.addWidget(etiqueta("Valoraciones físicas", "titulo"))
        self.contador = etiqueta("", "subtitulo")
        raiz.addWidget(self.contador)

        filtros = QHBoxLayout()
        self.filtro_usuario = QComboBox()
        self.filtro_usuario.currentIndexChanged.connect(self.refrescar)
        filtros.addWidget(etiqueta("Usuario:"))
        filtros.addWidget(self.filtro_usuario, 2)
        filtros.addStretch()
        raiz.addLayout(filtros)

        self.tabla = QTableWidget(0, len(COLUMNAS))
        self.tabla.setHorizontalHeaderLabels(COLUMNAS)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)
        cabecera = self.tabla.horizontalHeader()
        cabecera.setSectionResizeMode(QHeaderView.ResizeToContents)
        cabecera.setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabla.itemSelectionChanged.connect(self._actualizar_botones)
        self.tabla.itemDoubleClicked.connect(lambda *_: self.editar())
        raiz.addWidget(self.tabla)

        self.detalle = etiqueta("", "subtitulo", ajustar=True)
        raiz.addWidget(self.detalle)

        botones = QHBoxLayout()
        nueva = QPushButton("Nueva valoración")
        nueva.clicked.connect(self.nueva)
        botones.addWidget(nueva)
        self.acciones = []
        for texto, metodo in (("Abrir / editar", self.editar),
                              ("Generar informe PDF", self.informe)):
            boton = QPushButton(texto)
            boton.setProperty("plano", True)
            boton.clicked.connect(metodo)
            botones.addWidget(boton)
            self.acciones.append(boton)
        botones.addStretch()
        raiz.addLayout(botones)

    # -- datos --
    def _recargar_usuarios(self) -> None:
        actual = self.filtro_usuario.currentData()
        self.filtro_usuario.blockSignals(True)
        self.filtro_usuario.clear()
        self.filtro_usuario.addItem("Todos los usuarios", None)
        for usuario in self.repo.listar("T_USUARIOS", orden="Apellidos"):
            nombre = " ".join(x for x in (usuario.get("Nombre"),
                                          usuario.get("Apellidos")) if x)
            self.filtro_usuario.addItem(nombre, usuario.get("ID_Usuario"))
        indice = self.filtro_usuario.findData(actual)
        self.filtro_usuario.setCurrentIndex(max(0, indice))
        self.filtro_usuario.blockSignals(False)

    def refrescar(self) -> None:
        self._recargar_usuarios()
        id_usuario = self.filtro_usuario.currentData()
        valoraciones = self.repo.listar(
            "T_VALORACIONES",
            (lambda v: v.get("ID_Usuario") == id_usuario) if id_usuario else None,
            orden="Fecha", descendente=True)

        hay_protocolos = bool(self.repo.listar("T_PROTOCOLOS"))
        self.contador.setText(
            f"{len(valoraciones)} valoraciones"
            if hay_protocolos else
            "No hay protocolos cargados: impórtalos antes de valorar a nadie "
            "(herramientas/importar_valoracion.py).")

        self.tabla.blockSignals(True)
        self.tabla.setRowCount(len(valoraciones))
        for fila, valoracion in enumerate(valoraciones):
            resumen = srv.resumir(self.repo, valoracion["ID_Valoracion"])
            usuario = resumen.usuario
            protocolo = self.repo.obtener("T_PROTOCOLOS",
                                          valoracion.get("ID_Protocolo")) or {}
            alertas = [h for h in resumen.hallazgos if h.gravedad == "ALERTA"]
            valores = [
                valoracion["ID_Valoracion"], formatear(valoracion.get("Fecha")),
                " ".join(x for x in (usuario.get("Nombre"), usuario.get("Apellidos")) if x),
                (valoracion.get("Tipo") or "").replace("_", " ").capitalize(),
                protocolo.get("Nombre", ""),
                str(len(resumen.detalle)),
                f"{resumen.global_}/100" if resumen.global_ is not None else "—",
                f"{len(resumen.hallazgos)}" if resumen.hallazgos else "",
            ]
            for columna, texto in enumerate(valores):
                item = QTableWidgetItem(texto)
                item.setData(Qt.UserRole, valoracion["ID_Valoracion"])
                if columna == 7 and alertas:
                    item.setForeground(QColor(estilo.ALERTA))
                    item.setToolTip("\n".join(f"{h.titulo}: {h.detalle}" for h in alertas))
                self.tabla.setItem(fila, columna, item)
        self.tabla.blockSignals(False)
        self._actualizar_botones()

    def seleccionada(self) -> str | None:
        filas = self.tabla.selectionModel().selectedRows() if self.tabla.rowCount() else []
        return self.tabla.item(filas[0].row(), 0).data(Qt.UserRole) if filas else None

    def _actualizar_botones(self) -> None:
        hay = self.seleccionada() is not None
        for boton in self.acciones:
            boton.setEnabled(hay)
        if not hay:
            self.detalle.setText("")
            return
        resumen = srv.resumir(self.repo, self.seleccionada())
        if resumen.hallazgos:
            self.detalle.setText(" · ".join(
                f"{h.titulo}: {h.detalle}" for h in resumen.hallazgos[:3]))
        else:
            self.detalle.setText("Sin asimetrías ni desequilibrios destacables.")

    # -- acciones --
    def nueva(self) -> None:
        usuarios = self.repo.listar("T_USUARIOS", lambda u: u.get("Estado") == "ACTIVO")
        if not usuarios:
            QMessageBox.information(self, "Sin usuarios",
                                    "Da de alta a algún usuario antes de valorar.")
            return
        if not self.repo.listar("T_PROTOCOLOS"):
            QMessageBox.information(
                self, "Sin protocolos",
                "No hay protocolos de valoración cargados.\n\n"
                "Ejecuta: python herramientas/importar_valoracion.py")
            return
        id_usuario = self.filtro_usuario.currentData()
        if not id_usuario:
            QMessageBox.information(
                self, "Elige un usuario",
                "Selecciona arriba a quién vas a valorar y vuelve a pulsar.")
            return
        dialogo = DialogoValoracion(self.repo, id_usuario=id_usuario, padre=self)
        if dialogo.exec() and self.guardar():
            self.refrescar()

    def editar(self) -> None:
        identificador = self.seleccionada()
        if not identificador:
            return
        dialogo = DialogoValoracion(self.repo, id_valoracion=identificador, padre=self)
        if dialogo.exec() and self.guardar():
            self.refrescar()

    def informe(self) -> None:
        identificador = self.seleccionada()
        if not identificador:
            return
        try:
            ruta = informes.generar(self.repo, self.cfg, identificador)
        except Exception as error:
            avisar_error(self, "No se ha podido generar el informe", error)
            return
        try:
            self.repo.actualizar("T_VALORACIONES", identificador, {"Ruta_PDF": str(ruta)})
            self.guardar()
        except Exception:
            pass          # el PDF ya está generado; guardar la ruta es secundario
        if QMessageBox.question(
                self, "Informe generado",
                f"Informe guardado en:\n{ruta}\n\n¿Quieres abrirlo?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes) == QMessageBox.Yes:
            self._abrir(ruta)

    @staticmethod
    def _abrir(ruta) -> None:
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
