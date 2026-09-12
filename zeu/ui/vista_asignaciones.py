"""Asignación de macrociclos a usuarios y hoja de entrenamiento en PDF."""

from __future__ import annotations

from datetime import date
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout,
    QHeaderView, QMessageBox, QPlainTextEdit, QPushButton, QSpinBox, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from ..datos.repositorio import Repositorio
from ..nucleo.config import Config
from ..nucleo.fechas import formatear
from ..servicios import informes
from ..servicios import programas as srv
from ..servicios import usuarios as srv_usuarios
from . import estilo
from .comunes import avisar_error, campo_fecha, desplegable, etiqueta, leer_fecha
from .vista_valoraciones import VistaValoraciones

COLUMNAS = ["ID", "Usuario", "Programa", "Inicio", "Fin", "Estado", "Fase actual", "Quedan"]
ESTADOS = [("PLANIFICADA", "Planificada"), ("EN_CURSO", "En curso"),
           ("FINALIZADA", "Finalizada"), ("INTERRUMPIDA", "Interrumpida")]


class DialogoAsignacion(QDialog):
    """Asigna un macrociclo y enseña el calendario antes de confirmar."""

    def __init__(self, repo: Repositorio, padre=None):
        super().__init__(padre)
        self.repo = repo
        self.id_asignacion = None
        self.setWindowTitle("Asignar programa")
        self.setMinimumWidth(660)

        raiz = QVBoxLayout(self)
        raiz.addWidget(etiqueta("Asignar un programa", "titulo"))

        form = QFormLayout()
        self.usuario = desplegable([
            (u["ID_Usuario"], " ".join(x for x in (u.get("Nombre"),
                                                   u.get("Apellidos")) if x))
            for u in repo.listar("T_USUARIOS", lambda u: u.get("Estado") == "ACTIVO",
                                 orden="Apellidos")])
        self.usuario.currentIndexChanged.connect(self._refrescar_objetivos)
        self.ciclo = desplegable([
            (c["ID_Ciclo"], f"{c['Nombre']}  ({c.get('Duracion_Sem')} semanas)")
            for c in srv.raices(repo)])
        self.ciclo.currentIndexChanged.connect(self._previsualizar)
        self.inicio = campo_fecha(date.today())
        self.inicio.dateChanged.connect(self._previsualizar)
        self.objetivo = desplegable([], vacio=True)
        self.notas = QPlainTextEdit(); self.notas.setMaximumHeight(50)

        form.addRow("Usuario *", self.usuario)
        form.addRow("Programa *", self.ciclo)
        form.addRow("Fecha de inicio *", self.inicio)
        form.addRow("Objetivo asociado", self.objetivo)
        form.addRow("Notas", self.notas)
        raiz.addLayout(form)

        raiz.addWidget(etiqueta("Calendario que se va a congelar"))
        self.calendario = QTableWidget(0, 4)
        self.calendario.setHorizontalHeaderLabels(["Fase", "Nivel", "Desde", "Hasta"])
        self.calendario.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.calendario.horizontalHeader().setStretchLastSection(True)
        self.calendario.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.calendario.verticalHeader().setVisible(False)
        self.calendario.setMaximumHeight(230)
        raiz.addWidget(self.calendario)

        self.aviso = etiqueta("", "aviso", ajustar=True)
        raiz.addWidget(self.aviso)

        botones = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        botones.button(QDialogButtonBox.Save).setText("Asignar")
        botones.button(QDialogButtonBox.Cancel).setText("Cancelar")
        botones.accepted.connect(self._guardar)
        botones.rejected.connect(self.reject)
        raiz.addWidget(botones)

        self._refrescar_objetivos()
        self._previsualizar()

    def _refrescar_objetivos(self) -> None:
        id_usuario = self.usuario.currentData()
        self.objetivo.clear()
        self.objetivo.addItem("", None)
        for objetivo in self.repo.listar(
                "T_OBJETIVOS", lambda o: (o.get("ID_Usuario") == id_usuario
                                          and o.get("Estado") == "ACTIVO")):
            self.objetivo.addItem(objetivo.get("Descripcion") or objetivo.get("Tipo"),
                                  objetivo["ID_Objetivo"])

    def _previsualizar(self) -> None:
        id_ciclo = self.ciclo.currentData()
        inicio = leer_fecha(self.inicio)
        self.calendario.setRowCount(0)
        if not id_ciclo or not inicio:
            return
        fases = srv.calendario(self.repo, id_ciclo, inicio)
        visibles = [f for f in fases if f.nivel != "MACRO"]
        self.calendario.setRowCount(len(visibles))
        for n, fase in enumerate(visibles):
            sangria = "" if fase.nivel == "MESO" else "      "
            for columna, texto in enumerate((f"{sangria}{fase.nombre}",
                                             fase.nivel.capitalize(),
                                             formatear(fase.inicio),
                                             formatear(fase.fin))):
                self.calendario.setItem(n, columna, QTableWidgetItem(texto))

        avisos = srv.avisos_estructura(self.repo, id_ciclo)
        id_usuario = self.usuario.currentData()
        vigente = srv.asignacion_vigente(self.repo, id_usuario) if id_usuario else None
        if vigente:
            avisos.insert(0, "Este usuario ya tiene un programa activo "
                             f"hasta el {formatear(vigente.get('F_Fin_Prevista'))}. "
                             "Al asignar otro convivirán los dos.")
        self.aviso.setText("\n".join(avisos[:3]))
        self.aviso.setVisible(bool(avisos))

    def _guardar(self) -> None:
        if not self.usuario.currentData() or not self.ciclo.currentData():
            avisar_error(self, "Faltan datos",
                         Exception("Elige usuario y programa."))
            return
        try:
            self.id_asignacion = srv.asignar(
                self.repo, self.usuario.currentData(), self.ciclo.currentData(),
                leer_fecha(self.inicio), self.objetivo.currentData(),
                self.notas.toPlainText().strip())
        except Exception as error:
            avisar_error(self, "No se ha podido asignar", error)
            return
        self.accept()


class DialogoImprimir(QDialog):
    def __init__(self, total: int, actual: int, padre=None):
        super().__init__(padre)
        self.setWindowTitle("Imprimir programa")
        raiz = QVBoxLayout(self)
        raiz.addWidget(etiqueta("¿Qué semanas quieres imprimir?", "titulo"))
        form = QFormLayout()
        self.desde = QSpinBox(); self.desde.setRange(1, total); self.desde.setValue(actual)
        self.hasta = QSpinBox(); self.hasta.setRange(1, total)
        self.hasta.setValue(min(actual + 3, total))
        form.addRow("Desde la semana", self.desde)
        form.addRow("Hasta la semana", self.hasta)
        raiz.addLayout(form)
        raiz.addWidget(etiqueta(
            f"El plan tiene {total} semanas. Imprimirlas todas de golpe da un "
            "documento muy largo; lo habitual es entregar el bloque en curso.",
            "subtitulo", ajustar=True))
        botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        raiz.addWidget(botones)


class VistaAsignaciones(QWidget):
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
        raiz.addWidget(etiqueta("Asignaciones", "titulo"))
        self.contador = etiqueta("", "subtitulo")
        raiz.addWidget(self.contador)

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
        raiz.addWidget(self.tabla)

        self.detalle = etiqueta("", "subtitulo", ajustar=True)
        raiz.addWidget(self.detalle)

        botones = QHBoxLayout()
        nueva = QPushButton("Asignar programa")
        nueva.clicked.connect(self.nueva)
        botones.addWidget(nueva)
        self.acciones = []
        for texto, metodo in (("Hoja de entrenamiento (PDF)", self.imprimir),
                              ("Cambiar estado", self.cambiar_estado)):
            boton = QPushButton(texto)
            boton.setProperty("plano", True)
            boton.clicked.connect(metodo)
            botones.addWidget(boton)
            self.acciones.append(boton)
        botones.addStretch()
        raiz.addLayout(botones)

    def refrescar(self) -> None:
        asignaciones = self.repo.listar("T_ASIGNACIONES", orden="F_Inicio",
                                        descendente=True)
        self.contador.setText(
            f"{len(asignaciones)} asignaciones · "
            f"{len([a for a in asignaciones if a.get('Estado') == 'EN_CURSO'])} en curso"
            if asignaciones else
            "Nadie tiene programa asignado todavía.")

        self.tabla.blockSignals(True)
        self.tabla.setRowCount(len(asignaciones))
        for fila, asignacion in enumerate(asignaciones):
            usuario = self.repo.obtener("T_USUARIOS", asignacion.get("ID_Usuario")) or {}
            ciclo = self.repo.obtener("T_CICLOS", asignacion.get("ID_Ciclo")) or {}
            fase = srv.fase_actual(self.repo, asignacion["ID_Asignacion"])
            micro = self.repo.obtener("T_CICLOS", fase.get("ID_Ciclo")) if fase else None
            dias = srv.dias_para_fin(asignacion)
            valores = [
                asignacion["ID_Asignacion"],
                " ".join(x for x in (usuario.get("Nombre"), usuario.get("Apellidos")) if x),
                ciclo.get("Nombre", ""),
                formatear(asignacion.get("F_Inicio")),
                formatear(asignacion.get("F_Fin_Prevista")),
                (asignacion.get("Estado") or "").replace("_", " ").capitalize(),
                micro.get("Nombre") if micro else "—",
                f"{dias} días" if dias is not None and dias >= 0 else
                (f"vencido hace {-dias}" if dias is not None else ""),
            ]
            for columna, texto in enumerate(valores):
                item = QTableWidgetItem(texto)
                item.setData(Qt.UserRole, asignacion["ID_Asignacion"])
                if (columna == 7 and dias is not None
                        and asignacion.get("Estado") == "EN_CURSO" and dias <= 14):
                    item.setForeground(QColor(estilo.BAJO if dias >= 0 else estilo.ALERTA))
                    item.setToolTip("Toca generar el cuestionario de renovación")
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
        asignacion = self.repo.obtener("T_ASIGNACIONES", self.seleccionada()) or {}
        semanas = srv.semanas_de(self.repo, self.seleccionada())
        sin_rm = self._sin_1rm(asignacion, semanas)
        texto = f"{len(semanas)} semanas planificadas."
        if sin_rm:
            texto += (" Faltan repeticiones máximas de: " + ", ".join(sorted(sin_rm)[:5])
                      + ". Esas cargas saldrán como «por determinar».")
        self.detalle.setText(texto)

    def _sin_1rm(self, asignacion: dict, semanas) -> set[str]:
        faltan: set[str] = set()
        for semana in semanas[:4]:
            for sesion in semana.sesiones:
                for linea in srv.lineas(self.repo, sesion["ID_Sesion"]):
                    carga = srv.resolver_carga(self.repo, linea,
                                               asignacion.get("ID_Usuario"),
                                               semana.en_micro)
                    if carga.sin_1rm:
                        ejercicio = self.repo.obtener(
                            "T_EJERCICIOS", linea.get("ID_Ejercicio")) or {}
                        faltan.add(ejercicio.get("Nombre") or "?")
        return faltan

    # -- acciones --
    def nueva(self) -> None:
        if not self.repo.listar("T_USUARIOS", lambda u: u.get("Estado") == "ACTIVO"):
            QMessageBox.information(self, "Sin usuarios", "Da de alta a algún usuario.")
            return
        if not srv.raices(self.repo):
            QMessageBox.information(
                self, "Sin programas",
                "No hay ningún macrociclo. Crea uno en «Programas» o carga las "
                "plantillas con herramientas/crear_plantillas.py")
            return
        dialogo = DialogoAsignacion(self.repo, padre=self)
        if dialogo.exec() and self.guardar():
            self.refrescar()

    def cambiar_estado(self) -> None:
        identificador = self.seleccionada()
        if not identificador:
            return
        from PySide6.QtWidgets import QInputDialog
        actual = (self.repo.obtener("T_ASIGNACIONES", identificador) or {}).get("Estado")
        textos = [t for _, t in ESTADOS]
        elegido, aceptado = QInputDialog.getItem(
            self, "Estado de la asignación", "Nuevo estado:", textos,
            textos.index(dict(ESTADOS).get(actual, textos[0])), False)
        if not aceptado:
            return
        clave = next(c for c, t in ESTADOS if t == elegido)
        try:
            self.repo.actualizar("T_ASIGNACIONES", identificador, {"Estado": clave})
        except Exception as error:
            avisar_error(self, "No se ha podido cambiar", error)
            return
        if self.guardar():
            self.refrescar()

    def imprimir(self) -> None:
        identificador = self.seleccionada()
        if not identificador:
            return
        semanas = srv.semanas_de(self.repo, identificador)
        if not semanas:
            QMessageBox.information(self, "Sin semanas",
                                    "Este programa no tiene microciclos con sesiones.")
            return
        actual = 1
        fase = srv.fase_actual(self.repo, identificador)
        if fase:
            coincide = [s for s in semanas if s.id_micro == fase.get("ID_Ciclo")]
            if coincide:
                actual = coincide[0].numero
        dialogo = DialogoImprimir(len(semanas), actual, self)
        if not dialogo.exec():
            return
        try:
            ruta = informes.generar_programa(
                self.repo, self.cfg, identificador,
                desde=dialogo.desde.value(), hasta=dialogo.hasta.value())
        except Exception as error:
            avisar_error(self, "No se ha podido generar la hoja", error)
            return
        if QMessageBox.question(
                self, "Hoja generada", f"Guardada en:\n{ruta}\n\n¿Abrirla?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes) == QMessageBox.Yes:
            VistaValoraciones._abrir(ruta)
