"""Editor de planificación: árbol de ciclos, sesiones y ejercicios."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QHeaderView, QInputDialog, QMessageBox,
    QPushButton, QSplitter, QTableWidget, QTableWidgetItem, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget,
)

from ..datos.repositorio import Repositorio
from ..servicios import programas as srv
from . import estilo
from .comunes import avisar_error, confirmar, etiqueta
from .dialogos_programa import DialogoCiclo, DialogoLinea, DialogoSesion

COLUMNAS_LINEA = ["#", "Bloque", "Ejercicio", "Series", "Reps", "Carga", "Desc.", "Progresión"]


class VistaProgramas(QWidget):
    def __init__(self, repo: Repositorio, guardar: Callable[[], bool], padre=None):
        super().__init__(padre)
        self.repo = repo
        self.guardar = guardar
        self._construir()
        self.refrescar()

    def _construir(self) -> None:
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(24, 20, 24, 20)
        raiz.addWidget(etiqueta("Programas de entrenamiento", "titulo"))
        self.contador = etiqueta("", "subtitulo")
        raiz.addWidget(self.contador)

        division = QSplitter(Qt.Horizontal)

        izquierda = QWidget()
        caja_izquierda = QVBoxLayout(izquierda)
        caja_izquierda.setContentsMargins(0, 0, 8, 0)
        self.arbol = QTreeWidget()
        self.arbol.setHeaderLabels(["Ciclo", "Semanas"])
        self.arbol.setColumnWidth(0, 290)
        self.arbol.itemSelectionChanged.connect(self._cambio_seleccion)
        self.arbol.itemDoubleClicked.connect(lambda *_: self.editar_ciclo())
        caja_izquierda.addWidget(self.arbol)

        fila1 = QHBoxLayout()
        nuevo = QPushButton("Nuevo macrociclo")
        nuevo.clicked.connect(lambda: self.nuevo_ciclo("MACRO"))
        fila1.addWidget(nuevo)
        self.btn_hijo = QPushButton("Añadir dentro")
        self.btn_hijo.setProperty("plano", True)
        self.btn_hijo.clicked.connect(self.nuevo_hijo)
        fila1.addWidget(self.btn_hijo)
        caja_izquierda.addLayout(fila1)

        fila2 = QHBoxLayout()
        self.acciones_ciclo = []
        for texto, metodo in (("Editar", self.editar_ciclo),
                              ("Clonar", self.clonar_ciclo),
                              ("Borrar", self.borrar_ciclo)):
            boton = QPushButton(texto)
            boton.setProperty("plano", True)
            boton.clicked.connect(metodo)
            fila2.addWidget(boton)
            self.acciones_ciclo.append(boton)
        caja_izquierda.addLayout(fila2)
        division.addWidget(izquierda)

        derecha = QWidget()
        caja_derecha = QVBoxLayout(derecha)
        caja_derecha.setContentsMargins(8, 0, 0, 0)
        self.titulo_micro = etiqueta("", "subtitulo", ajustar=True)
        caja_derecha.addWidget(self.titulo_micro)

        self.sesiones = QTreeWidget()
        self.sesiones.setHeaderLabels(["Día", "Sesión", "Tipo", "Ejercicios"])
        self.sesiones.setMaximumHeight(150)
        self.sesiones.itemSelectionChanged.connect(self._refrescar_lineas)
        self.sesiones.itemDoubleClicked.connect(lambda *_: self.editar_sesion())
        caja_derecha.addWidget(self.sesiones)

        fila3 = QHBoxLayout()
        self.btn_nueva_sesion = QPushButton("Nueva sesión")
        self.btn_nueva_sesion.setProperty("plano", True)
        self.btn_nueva_sesion.clicked.connect(self.nueva_sesion)
        fila3.addWidget(self.btn_nueva_sesion)
        self.acciones_sesion = []
        for texto, metodo in (("Editar sesión", self.editar_sesion),
                              ("Borrar sesión", self.borrar_sesion)):
            boton = QPushButton(texto)
            boton.setProperty("plano", True)
            boton.clicked.connect(metodo)
            fila3.addWidget(boton)
            self.acciones_sesion.append(boton)
        fila3.addStretch()
        caja_derecha.addLayout(fila3)

        self.tabla = QTableWidget(0, len(COLUMNAS_LINEA))
        self.tabla.setHorizontalHeaderLabels(COLUMNAS_LINEA)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)
        cabecera = self.tabla.horizontalHeader()
        cabecera.setSectionResizeMode(QHeaderView.ResizeToContents)
        cabecera.setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabla.itemDoubleClicked.connect(lambda *_: self.editar_linea())
        self.tabla.itemSelectionChanged.connect(self._actualizar_botones)
        caja_derecha.addWidget(self.tabla)

        fila4 = QHBoxLayout()
        self.btn_nueva_linea = QPushButton("Añadir ejercicio")
        self.btn_nueva_linea.clicked.connect(self.nueva_linea)
        fila4.addWidget(self.btn_nueva_linea)
        self.acciones_linea = []
        for texto, metodo in (("Editar", self.editar_linea), ("Subir", self.subir),
                              ("Bajar", self.bajar), ("Quitar", self.borrar_linea)):
            boton = QPushButton(texto)
            boton.setProperty("plano", True)
            boton.clicked.connect(metodo)
            fila4.addWidget(boton)
            self.acciones_linea.append(boton)
        fila4.addStretch()
        caja_derecha.addLayout(fila4)
        division.addWidget(derecha)
        division.setSizes([420, 760])
        raiz.addWidget(division, 1)

        self.avisos = etiqueta("", "aviso", ajustar=True)
        raiz.addWidget(self.avisos)

    # -- árbol --
    def refrescar(self) -> None:
        seleccionado = self.ciclo_seleccionado()
        self.arbol.clear()
        macros = srv.raices(self.repo)
        for macro in macros:
            self.arbol.addTopLevelItem(self._nodo(macro))
        self.arbol.expandToDepth(0)
        self.contador.setText(
            f"{len(macros)} macrociclos · {len(self.repo.listar('T_CICLOS'))} ciclos en total"
            if macros else
            "No hay ningún programa. Crea uno o carga las plantillas de partida "
            "con herramientas/crear_plantillas.py")
        if seleccionado:
            self._seleccionar(seleccionado)
        self._cambio_seleccion()

    def _nodo(self, ciclo: dict) -> QTreeWidgetItem:
        etiquetas = {"MACRO": "", "MESO": "", "MICRO": ""}
        item = QTreeWidgetItem([
            f"{etiquetas.get(ciclo['Tipo'], '')}{ciclo['Nombre']}",
            str(ciclo.get("Duracion_Sem") or "")])
        item.setData(0, Qt.UserRole, ciclo["ID_Ciclo"])
        if ciclo["Tipo"] == "MACRO":
            fuente = QFont(); fuente.setBold(True)
            item.setFont(0, fuente)
            if ciclo.get("Es_Plantilla_SN"):
                item.setForeground(0, QColor(estilo.AZUL_OSCURO))
        elif ciclo["Tipo"] == "MICRO":
            item.setForeground(0, QColor("#4A5A66"))
        for hijo in srv.hijos(self.repo, ciclo["ID_Ciclo"]):
            item.addChild(self._nodo(hijo))
        return item

    def _seleccionar(self, id_ciclo: str) -> None:
        def buscar(item):
            if item.data(0, Qt.UserRole) == id_ciclo:
                return item
            for n in range(item.childCount()):
                if (encontrado := buscar(item.child(n))):
                    return encontrado
            return None
        for n in range(self.arbol.topLevelItemCount()):
            if (item := buscar(self.arbol.topLevelItem(n))):
                self.arbol.setCurrentItem(item)
                return

    def ciclo_seleccionado(self) -> str | None:
        item = self.arbol.currentItem()
        return item.data(0, Qt.UserRole) if item else None

    def _tipo_seleccionado(self) -> str | None:
        ciclo = self.repo.obtener("T_CICLOS", self.ciclo_seleccionado() or "")
        return ciclo.get("Tipo") if ciclo else None

    def _cambio_seleccion(self) -> None:
        id_ciclo = self.ciclo_seleccionado()
        tipo = self._tipo_seleccionado()
        for boton in self.acciones_ciclo:
            boton.setEnabled(id_ciclo is not None)
        self.btn_hijo.setEnabled(tipo in ("MACRO", "MESO"))
        if tipo == "MACRO":
            self.btn_hijo.setText("Añadir mesociclo")
        elif tipo == "MESO":
            self.btn_hijo.setText("Añadir microciclo")
        else:
            self.btn_hijo.setText("Añadir dentro")

        self.sesiones.clear()
        if tipo == "MICRO":
            ciclo = self.repo.obtener("T_CICLOS", id_ciclo) or {}
            self.titulo_micro.setText(
                f"Sesiones de «{ciclo.get('Nombre')}» ({ciclo.get('Duracion_Sem')} semanas)")
            for sesion in srv.sesiones(self.repo, id_ciclo):
                cuantas = len(srv.lineas(self.repo, sesion["ID_Sesion"]))
                item = QTreeWidgetItem([
                    str(sesion.get("Num_Dia") or ""), sesion.get("Nombre") or "",
                    (sesion.get("Tipo") or "").replace("_", " ").capitalize(),
                    f"{cuantas}"])
                item.setData(0, Qt.UserRole, sesion["ID_Sesion"])
                self.sesiones.addTopLevelItem(item)
            if self.sesiones.topLevelItemCount():
                self.sesiones.setCurrentItem(self.sesiones.topLevelItem(0))
        else:
            self.titulo_micro.setText(
                "Selecciona un microciclo para ver y editar sus sesiones."
                if id_ciclo else "")
        self.btn_nueva_sesion.setEnabled(tipo == "MICRO")
        self._refrescar_lineas()

        raiz_macro = id_ciclo
        ciclo = self.repo.obtener("T_CICLOS", id_ciclo or "") or {}
        while ciclo.get("ID_Padre"):
            raiz_macro = ciclo["ID_Padre"]
            ciclo = self.repo.obtener("T_CICLOS", raiz_macro) or {}
        avisos = srv.avisos_estructura(self.repo, raiz_macro) if raiz_macro else []
        self.avisos.setText("\n".join(avisos[:4]))
        self.avisos.setVisible(bool(avisos))

    # -- sesiones y líneas --
    def sesion_seleccionada(self) -> str | None:
        item = self.sesiones.currentItem()
        return item.data(0, Qt.UserRole) if item else None

    def _refrescar_lineas(self) -> None:
        id_sesion = self.sesion_seleccionada()
        self.tabla.setRowCount(0)
        if id_sesion:
            filas = srv.lineas(self.repo, id_sesion)
            self.tabla.setRowCount(len(filas))
            for n, linea in enumerate(filas):
                ejercicio = self.repo.obtener("T_EJERCICIOS", linea.get("ID_Ejercicio")) or {}
                carga = srv.resolver_carga(self.repo, linea, None)
                descanso = linea.get("Descanso_Seg")
                valores = [
                    str(linea.get("Orden") or n + 1),
                    (linea.get("Bloque") or "").replace("_", " ").capitalize(),
                    ejercicio.get("Nombre") or "?",
                    str(linea.get("Series") or ""), str(linea.get("Reps") or ""),
                    carga.texto, f"{int(descanso)}s" if descanso else "",
                    srv.nota_progresion(linea.get("Progresion"))]
                for columna, texto in enumerate(valores):
                    item = QTableWidgetItem(texto)
                    item.setData(Qt.UserRole, linea["ID_Linea"])
                    self.tabla.setItem(n, columna, item)
        self._actualizar_botones()

    def linea_seleccionada(self) -> str | None:
        filas = self.tabla.selectionModel().selectedRows() if self.tabla.rowCount() else []
        return self.tabla.item(filas[0].row(), 0).data(Qt.UserRole) if filas else None

    def _actualizar_botones(self) -> None:
        hay_sesion = self.sesion_seleccionada() is not None
        self.btn_nueva_linea.setEnabled(hay_sesion)
        for boton in self.acciones_sesion:
            boton.setEnabled(hay_sesion)
        for boton in self.acciones_linea:
            boton.setEnabled(self.linea_seleccionada() is not None)

    # -- acciones de ciclo --
    def nuevo_ciclo(self, tipo: str, id_padre: str | None = None) -> None:
        dialogo = DialogoCiclo(self.repo, tipo=tipo, id_padre=id_padre, padre=self)
        if dialogo.exec() and self.guardar():
            self.refrescar()
            self._seleccionar(dialogo.id_ciclo)

    def nuevo_hijo(self) -> None:
        tipo = self._tipo_seleccionado()
        if tipo in ("MACRO", "MESO"):
            self.nuevo_ciclo({"MACRO": "MESO", "MESO": "MICRO"}[tipo],
                             self.ciclo_seleccionado())

    def editar_ciclo(self) -> None:
        id_ciclo = self.ciclo_seleccionado()
        if id_ciclo and DialogoCiclo(self.repo, id_ciclo, padre=self).exec():
            if self.guardar():
                self.refrescar()

    def clonar_ciclo(self) -> None:
        id_ciclo = self.ciclo_seleccionado()
        if not id_ciclo:
            return
        original = self.repo.obtener("T_CICLOS", id_ciclo) or {}
        nombre, aceptado = QInputDialog.getText(
            self, "Clonar ciclo", "Nombre de la copia:",
            text=f"{original.get('Nombre')} (copia)")
        if not aceptado or not nombre.strip():
            return
        try:
            nuevo = srv.clonar(self.repo, id_ciclo, nombre.strip())
        except Exception as error:
            avisar_error(self, "No se ha podido clonar", error)
            return
        if self.guardar():
            self.refrescar()
            self._seleccionar(nuevo)

    def borrar_ciclo(self) -> None:
        id_ciclo = self.ciclo_seleccionado()
        if not id_ciclo:
            return
        ciclo = self.repo.obtener("T_CICLOS", id_ciclo) or {}
        usado = self.repo.listar("T_ASIGNACIONES",
                                 lambda a: a.get("ID_Ciclo") == id_ciclo)
        if usado:
            QMessageBox.warning(
                self, "Está asignado",
                f"«{ciclo.get('Nombre')}» está asignado a {len(usado)} usuario(s). "
                "Borrarlo dejaría su planificación sin referencia.")
            return
        cuantos = len(srv.descendientes(self.repo, id_ciclo))
        if not confirmar(self, "Borrar ciclo",
                         f"¿Borrar «{ciclo.get('Nombre')}» y los {cuantos} ciclos que "
                         "cuelgan de él, con sus sesiones y ejercicios?"):
            return
        try:
            srv.borrar_ciclo(self.repo, id_ciclo)
        except Exception as error:
            avisar_error(self, "No se ha podido borrar", error)
            return
        if self.guardar():
            self.refrescar()

    # -- acciones de sesión y línea --
    def nueva_sesion(self) -> None:
        id_ciclo = self.ciclo_seleccionado()
        if id_ciclo and DialogoSesion(self.repo, id_ciclo, padre=self).exec():
            if self.guardar():
                self._cambio_seleccion()

    def editar_sesion(self) -> None:
        id_sesion = self.sesion_seleccionada()
        if id_sesion and DialogoSesion(self.repo, self.ciclo_seleccionado(),
                                       id_sesion, padre=self).exec():
            if self.guardar():
                self._cambio_seleccion()

    def borrar_sesion(self) -> None:
        id_sesion = self.sesion_seleccionada()
        if not id_sesion or not confirmar(
                self, "Borrar sesión", "¿Borrar la sesión y todos sus ejercicios?"):
            return
        for linea in srv.lineas(self.repo, id_sesion):
            self.repo.borrar("T_SESION_DET", linea["ID_Linea"], forzar=True)
        self.repo.borrar("T_SESIONES", id_sesion, forzar=True)
        if self.guardar():
            self._cambio_seleccion()

    def nueva_linea(self) -> None:
        id_sesion = self.sesion_seleccionada()
        if id_sesion and DialogoLinea(self.repo, id_sesion, padre=self).exec():
            if self.guardar():
                self._cambio_seleccion()

    def editar_linea(self) -> None:
        id_linea = self.linea_seleccionada()
        if id_linea and DialogoLinea(self.repo, self.sesion_seleccionada(),
                                     id_linea, padre=self).exec():
            if self.guardar():
                self._refrescar_lineas()

    def borrar_linea(self) -> None:
        id_linea = self.linea_seleccionada()
        if id_linea:
            self.repo.borrar("T_SESION_DET", id_linea, forzar=True)
            if self.guardar():
                self._refrescar_lineas()

    def _mover(self, delta: int) -> None:
        id_linea = self.linea_seleccionada()
        if not id_linea:
            return
        filas = srv.lineas(self.repo, self.sesion_seleccionada())
        posicion = next((n for n, l in enumerate(filas) if l["ID_Linea"] == id_linea), None)
        destino = posicion + delta if posicion is not None else None
        if destino is None or not 0 <= destino < len(filas):
            return
        filas[posicion], filas[destino] = filas[destino], filas[posicion]
        for n, linea in enumerate(filas, start=1):
            self.repo.actualizar("T_SESION_DET", linea["ID_Linea"], {"Orden": n})
        if self.guardar():
            self._refrescar_lineas()
            self.tabla.selectRow(destino)

    def subir(self) -> None:
        self._mover(-1)

    def bajar(self) -> None:
        self._mover(1)
