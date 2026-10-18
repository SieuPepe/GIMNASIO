"""Catálogo de ejercicios: listado, filtros, alta y sustituciones."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QFileDialog, QHBoxLayout,
    QHeaderView, QLineEdit, QMessageBox, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from ..datos.repositorio import Repositorio
from ..nucleo.config import RAIZ
from ..servicios import ejercicios as srv
from ..servicios.importacion import importar_ejercicios
from . import estilo
from .comunes import avisar_error, confirmar, desplegable, etiqueta
from .ficha_ejercicio import FichaEjercicio, texto_patron

COLUMNAS = ["ID", "Nombre", "Patrón", "Grupo", "Material", "Nivel", "Básico", "Estado"]
CSV_INICIAL = RAIZ / "datos_iniciales" / "ejercicios.csv"


class DialogoSustitutos(QDialog):
    """Ejercicios equivalentes, opcionalmente acotados al material disponible."""

    def __init__(self, repo: Repositorio, id_ejercicio: str, padre=None):
        super().__init__(padre)
        self.repo = repo
        self.id_ejercicio = id_ejercicio
        original = repo.obtener("T_EJERCICIOS", id_ejercicio) or {}
        self.setWindowTitle(f"Sustitutos de {original.get('Nombre')}")
        self.setMinimumWidth(660)

        raiz = QVBoxLayout(self)
        raiz.addWidget(etiqueta("Ejercicios equivalentes", "titulo"))
        raiz.addWidget(etiqueta(
            f"{original.get('Nombre')} · {texto_patron(original.get('Patron'))} · "
            f"{srv.legible(original.get('Material'))}", "subtitulo"))

        filtro = QHBoxLayout()
        filtro.addWidget(etiqueta("Material disponible:"))
        self.material = desplegable(
            [(m, m.replace("_", " ").capitalize()) for m in srv.MATERIALES], vacio=True)
        self.material.setCurrentIndex(0)
        self.material.currentIndexChanged.connect(self.refrescar)
        self.solo_con_material = QCheckBox("Solo los que puedo hacer con ese material")
        self.solo_con_material.stateChanged.connect(self.refrescar)
        filtro.addWidget(self.material)
        filtro.addWidget(self.solo_con_material)
        filtro.addStretch()
        raiz.addLayout(filtro)

        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(["Nombre", "Grupo", "Nivel", "Material"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)
        raiz.addWidget(self.tabla)

        cerrar = QPushButton("Cerrar")
        cerrar.clicked.connect(self.accept)
        pie = QHBoxLayout(); pie.addStretch(); pie.addWidget(cerrar)
        raiz.addLayout(pie)
        self.refrescar()

    def refrescar(self) -> None:
        material = None
        if self.solo_con_material.isChecked() and self.material.currentData():
            material = {self.material.currentData(), "PESO_CORPORAL"}
        encontrados = srv.sustitutos(self.repo, self.id_ejercicio, material=material, limite=12)
        self.tabla.setRowCount(len(encontrados))
        for fila, e in enumerate(encontrados):
            for columna, texto in enumerate((
                    e.get("Nombre"), (e.get("Grupo_Principal") or "").capitalize(),
                    str(e.get("Nivel") or ""), srv.legible(e.get("Material")))):
                self.tabla.setItem(fila, columna, QTableWidgetItem(texto))


class VistaEjercicios(QWidget):
    def __init__(self, repo: Repositorio, guardar: Callable[[], bool], padre=None):
        super().__init__(padre)
        self.repo = repo
        self.guardar = guardar
        self._construir()
        self.refrescar()

    def _construir(self) -> None:
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(24, 20, 24, 20)
        raiz.addWidget(etiqueta("Catálogo de ejercicios", "titulo"))
        self.contador = etiqueta("", "subtitulo")
        raiz.addWidget(self.contador)

        filtros = QHBoxLayout()
        self.busqueda = QLineEdit()
        self.busqueda.setPlaceholderText("Buscar por nombre…")
        self.busqueda.textChanged.connect(self.refrescar)
        self.patron = desplegable(
            [(p, texto_patron(p)) for p in srv.PATRONES], vacio=True)
        self.patron.setItemText(0, "Todos los patrones")
        self.grupo = desplegable(
            [(g, g.replace("_", " ").capitalize()) for g in srv.GRUPOS], vacio=True)
        self.grupo.setItemText(0, "Todos los grupos")
        self.material = desplegable(
            [(m, m.replace("_", " ").capitalize()) for m in srv.MATERIALES], vacio=True)
        self.material.setItemText(0, "Todo el material")
        for combo in (self.patron, self.grupo, self.material):
            combo.currentIndexChanged.connect(self.refrescar)
        filtros.addWidget(self.busqueda, 2)
        filtros.addWidget(self.patron, 1)
        filtros.addWidget(self.grupo, 1)
        filtros.addWidget(self.material, 1)
        raiz.addLayout(filtros)

        marcas = QHBoxLayout()
        self.solo_activos = QCheckBox("Solo activos")
        self.solo_activos.setChecked(True)
        self.solo_basicos = QCheckBox("Solo básicos")
        for casilla in (self.solo_activos, self.solo_basicos):
            casilla.stateChanged.connect(self.refrescar)
            marcas.addWidget(casilla)
        marcas.addStretch()
        self.cobertura = etiqueta("", "subtitulo", ajustar=True)
        marcas.addWidget(self.cobertura, 3)
        raiz.addLayout(marcas)

        self.tabla = QTableWidget(0, len(COLUMNAS))
        self.tabla.setHorizontalHeaderLabels(COLUMNAS)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)
        cabecera = self.tabla.horizontalHeader()
        cabecera.setSectionResizeMode(QHeaderView.ResizeToContents)
        # El nombre se queda con el espacio sobrante; el material lleva ancho fijo
        # con el texto completo en el tooltip. Sin esto, lo primero que se corta
        # es justamente el nombre.
        cabecera.setSectionResizeMode(1, QHeaderView.Stretch)
        cabecera.setSectionResizeMode(4, QHeaderView.Interactive)
        self.tabla.setColumnWidth(4, 180)
        self.tabla.itemSelectionChanged.connect(self._actualizar_botones)
        self.tabla.itemDoubleClicked.connect(lambda *_: self.editar())
        raiz.addWidget(self.tabla)

        botones = QHBoxLayout()
        nuevo = QPushButton("Nuevo ejercicio")
        nuevo.clicked.connect(self.nuevo)
        botones.addWidget(nuevo)
        self.acciones = []
        for texto, metodo in (("Editar", self.editar),
                              ("Ver sustitutos", self.ver_sustitutos),
                              ("Activar / desactivar", self.alternar_activo)):
            boton = QPushButton(texto)
            boton.setProperty("plano", True)
            boton.clicked.connect(metodo)
            botones.addWidget(boton)
            self.acciones.append(boton)
        botones.addStretch()
        importar = QPushButton("Importar desde CSV…")
        importar.setProperty("plano", True)
        importar.clicked.connect(self.importar)
        botones.addWidget(importar)
        raiz.addLayout(botones)

    # -- datos --
    def _visibles(self) -> list[dict]:
        todos = self.repo.listar("T_EJERCICIOS", orden="Nombre")
        if self.solo_activos.isChecked():
            todos = [e for e in todos if e.get("Activo_SN")]
        return srv.filtrar(
            todos,
            patron=self.patron.currentData(),
            grupo=self.grupo.currentData(),
            material=self.material.currentData(),
            solo_basicos=self.solo_basicos.isChecked(),
            busqueda=self.busqueda.text())

    def refrescar(self) -> None:
        ejercicios = self._visibles()
        total = len(self.repo.listar("T_EJERCICIOS"))
        activos = len([e for e in self.repo.listar("T_EJERCICIOS") if e.get("Activo_SN")])
        self.contador.setText(
            f"{len(ejercicios)} visibles · {activos} activos de {total} en el catálogo"
            if total else
            "El catálogo está vacío. Usa «Importar desde CSV…» para cargar el inicial.")

        faltan = srv.patrones_sin_cobertura(ejercicios)
        if faltan and total:
            self.cobertura.setText(
                "Sin cobertura con este filtro: " +
                ", ".join(texto_patron(p) for p in faltan))
        else:
            self.cobertura.setText("")

        self.tabla.blockSignals(True)
        self.tabla.setRowCount(len(ejercicios))
        for fila, e in enumerate(ejercicios):
            valores = [
                e.get("ID_Ejercicio"), e.get("Nombre"),
                texto_patron(e.get("Patron"), corto=True),
                (e.get("Grupo_Principal") or "").replace("_", " ").capitalize(),
                srv.legible(e.get("Material")),
                str(e.get("Nivel") or ""), "Sí" if e.get("Es_Basico_SN") else "",
                "Activo" if e.get("Activo_SN") else "Inactivo",
            ]
            for columna, texto in enumerate(valores):
                item = QTableWidgetItem(texto)
                item.setData(Qt.UserRole, e.get("ID_Ejercicio"))
                if columna in (1, 4):
                    item.setToolTip(texto)
                if not e.get("Activo_SN"):
                    item.setForeground(QColor("#9AA5AD"))
                self.tabla.setItem(fila, columna, item)
        self.tabla.blockSignals(False)
        self._actualizar_botones()

    def seleccionado(self) -> str | None:
        filas = self.tabla.selectionModel().selectedRows() if self.tabla.rowCount() else []
        return self.tabla.item(filas[0].row(), 0).data(Qt.UserRole) if filas else None

    def _actualizar_botones(self) -> None:
        hay = self.seleccionado() is not None
        for boton in self.acciones:
            boton.setEnabled(hay)

    # -- acciones --
    def nuevo(self) -> None:
        if FichaEjercicio(self.repo, padre=self).exec() and self.guardar():
            self.refrescar()

    def editar(self) -> None:
        identificador = self.seleccionado()
        if identificador and FichaEjercicio(self.repo, identificador, padre=self).exec():
            if self.guardar():
                self.refrescar()

    def ver_sustitutos(self) -> None:
        identificador = self.seleccionado()
        if identificador:
            DialogoSustitutos(self.repo, identificador, padre=self).exec()

    def alternar_activo(self) -> None:
        identificador = self.seleccionado()
        if not identificador:
            return
        ejercicio = self.repo.obtener("T_EJERCICIOS", identificador) or {}
        activo = bool(ejercicio.get("Activo_SN"))
        # Baja lógica: un ejercicio usado en un programa no puede desaparecer,
        # solo dejar de ofrecerse para programas nuevos.
        try:
            self.repo.actualizar("T_EJERCICIOS", identificador, {"Activo_SN": not activo})
        except Exception as error:
            avisar_error(self, "No se ha podido cambiar el estado", error)
            return
        if self.guardar():
            self.refrescar()

    def importar(self) -> None:
        inicial = str(CSV_INICIAL if CSV_INICIAL.exists() else RAIZ)
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Elegir el fichero de ejercicios", inicial, "Ficheros CSV (*.csv)")
        if not ruta:
            return
        hay_catalogo = bool(self.repo.listar("T_EJERCICIOS"))
        actualizar = False
        if hay_catalogo:
            actualizar = confirmar(
                self, "Ejercicios que ya existen",
                "¿Sobreescribir los ejercicios que ya estén en el catálogo con lo que "
                "diga el fichero?\n\nSi respondes que no, solo se darán de alta los "
                "que falten y no se tocará nada de lo que ya tienes.")
        try:
            resultado = importar_ejercicios(self.repo, Path(ruta), actualizar=actualizar)
        except Exception as error:
            avisar_error(self, "No se ha podido importar", error)
            return

        if resultado.altas or resultado.modificados:
            self.guardar()
        self.refrescar()

        detalle = [resultado.resumen()]
        if resultado.errores:
            detalle.append("\nErrores:\n• " + "\n• ".join(resultado.errores[:10]))
        if resultado.avisos:
            detalle.append("\nAvisos:\n• " + "\n• ".join(resultado.avisos[:10]))
        QMessageBox.information(self, "Importación terminada", "\n".join(detalle))
