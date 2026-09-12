"""Bandeja de salida: revisar, aprobar y enviar. Ver docs/04."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QFileDialog, QHBoxLayout, QHeaderView, QMessageBox,
    QPlainTextEdit, QPushButton, QSplitter, QTableWidget, QTableWidgetItem,
    QTextBrowser, QVBoxLayout, QWidget,
)

from ..datos.repositorio import Repositorio
from ..nucleo import config as cfg_mod
from ..nucleo.config import Config
from ..nucleo.fechas import formatear
from ..servicios import cola as srv
from ..servicios import correo as srv_correo
from ..servicios import respuestas as srv_respuestas
from . import estilo
from .comunes import avisar_error, confirmar, etiqueta
from .dialogo_plantillas import DialogoPlantillas

COLUMNAS = ["ID", "Usuario", "Tipo", "Programado", "Estado", "Aviso"]
ESTADO_VISIBLE = {"BORRADOR": "Borrador", "REVISADO": "Aprobado", "ERROR": "Sin enviar"}
NOMBRE_PLANTILLA = {
    "CONSENTIMIENTO": "Consentimiento", "BIENVENIDA": "Bienvenida",
    "CHECKIN_MITAD": "Check-in de mitad", "ENCUESTA_T14": "Encuesta T-14",
    "RECORDATORIO": "Recordatorio", "CIERRE_CICLO": "Cierre de ciclo",
    "AGRADECIMIENTO": "Agradecimiento",
}


class VistaCorreo(QWidget):
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
        raiz.addWidget(etiqueta("Bandeja de salida", "titulo"))
        self.contador = etiqueta("", "subtitulo")
        raiz.addWidget(self.contador)
        self.banda_vacaciones = etiqueta("", "aviso", ajustar=True)
        raiz.addWidget(self.banda_vacaciones)

        superior = QHBoxLayout()
        buscar = QPushButton("Buscar avisos pendientes")
        buscar.clicked.connect(self.buscar)
        superior.addWidget(buscar)
        importar = QPushButton("Importar respuestas…")
        importar.setProperty("plano", True)
        importar.clicked.connect(self.importar_respuestas)
        superior.addWidget(importar)
        plantillas = QPushButton("Plantillas de correo…")
        plantillas.setProperty("plano", True)
        plantillas.clicked.connect(self.editar_plantillas)
        superior.addWidget(plantillas)
        probar = QPushButton("Probar la conexión de correo")
        probar.setProperty("plano", True)
        probar.clicked.connect(self.probar_conexion)
        superior.addWidget(probar)
        superior.addStretch()
        raiz.addLayout(superior)

        division = QSplitter(Qt.Horizontal)
        izquierda = QWidget()
        caja = QVBoxLayout(izquierda)
        caja.setContentsMargins(0, 0, 8, 0)
        self.tabla = QTableWidget(0, len(COLUMNAS))
        self.tabla.setHorizontalHeaderLabels(COLUMNAS)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)
        cabecera = self.tabla.horizontalHeader()
        cabecera.setSectionResizeMode(QHeaderView.ResizeToContents)
        cabecera.setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla.itemSelectionChanged.connect(self._cargar_seleccion)
        caja.addWidget(self.tabla)
        division.addWidget(izquierda)

        derecha = QWidget()
        caja_derecha = QVBoxLayout(derecha)
        caja_derecha.setContentsMargins(8, 0, 0, 0)
        caja_derecha.addWidget(etiqueta("Tu impresión personal sobre este usuario"))
        self.nota = QPlainTextEdit()
        self.nota.setMaximumHeight(84)
        self.nota.setPlaceholderText(
            "Se integra en el cuerpo del correo. Es la parte que ningún dato "
            "sustituye: escribe como le hablarías en la sala.")
        self.nota.textChanged.connect(self._marcar_sucio)
        caja_derecha.addWidget(self.nota)

        fila = QHBoxLayout()
        actualizar = QPushButton("Actualizar vista previa")
        actualizar.setProperty("plano", True)
        actualizar.clicked.connect(self.guardar_nota)
        fila.addWidget(actualizar)
        fila.addStretch()
        caja_derecha.addLayout(fila)

        caja_derecha.addWidget(etiqueta("Vista previa: así lo va a recibir"))
        self.vista = QTextBrowser()
        self.vista.setOpenExternalLinks(True)
        caja_derecha.addWidget(self.vista, 1)
        self.problemas = etiqueta("", "alerta", ajustar=True)
        caja_derecha.addWidget(self.problemas)
        division.addWidget(derecha)
        division.setSizes([520, 660])
        raiz.addWidget(division, 1)

        botones = QHBoxLayout()
        self.acciones = []
        for texto, metodo, plano in (("Aprobar", self.aprobar, False),
                                     ("Aprobar y enviar", self.enviar, False),
                                     ("Enviarme una prueba", self.prueba, True),
                                     ("Cancelar envío", self.cancelar, True)):
            boton = QPushButton(texto)
            boton.setProperty("plano", plano)
            boton.clicked.connect(metodo)
            botones.addWidget(boton)
            self.acciones.append(boton)
        botones.addStretch()
        self.btn_lote = QPushButton("Enviar todos los aprobados")
        self.btn_lote.clicked.connect(self.enviar_aprobados)
        botones.addWidget(self.btn_lote)
        raiz.addLayout(botones)

    # -- datos --
    def refrescar(self) -> None:
        envios = srv.pendientes(self.repo)
        retrasados = {e["ID_Envio"] for e in srv.con_retraso(self.repo)}
        aprobados = [e for e in envios if e.get("Estado") == "REVISADO"]
        con_error = [e for e in envios if e.get("Estado") == "ERROR"]
        partes = [f"{len(envios)} correos pendientes", f"{len(aprobados)} aprobados"]
        if retrasados:
            partes.append(f"{len(retrasados)} con retraso")
        if con_error:
            partes.append(f"{len(con_error)} sin enviar por un error")
        self.contador.setText(" · ".join(partes) if envios
                              else "No hay nada pendiente de enviar.")

        estado = srv.estado_vacaciones(self.repo)
        if estado.activo:
            self.banda_vacaciones.setText(
                f"MODO VACACIONES ACTIVO hasta el {formatear(estado.caducidad)}: "
                "los correos aptos se envían solos, sin revisión.")
        elif estado.motivo:
            self.banda_vacaciones.setText(f"Modo vacaciones: {estado.motivo}.")
        self.banda_vacaciones.setVisible(bool(estado.activo or estado.motivo))

        self.tabla.blockSignals(True)
        self.tabla.setRowCount(len(envios))
        for fila, envio in enumerate(envios):
            usuario = self.repo.obtener("T_USUARIOS", envio.get("ID_Usuario")) or {}
            con_retraso = envio["ID_Envio"] in retrasados
            valores = [
                envio["ID_Envio"],
                " ".join(x for x in (usuario.get("Nombre"), usuario.get("Apellidos")) if x),
                NOMBRE_PLANTILLA.get(envio.get("Codigo_Plantilla"),
                                     envio.get("Codigo_Plantilla") or ""),
                formatear(envio.get("F_Programada")),
                ESTADO_VISIBLE.get(envio.get("Estado"), envio.get("Estado") or ""),
                (envio.get("Error") or "")[:60] if envio.get("Error")
                else ("con retraso" if con_retraso else ""),
            ]
            for columna, texto in enumerate(valores):
                item = QTableWidgetItem(texto)
                item.setData(Qt.UserRole, envio["ID_Envio"])
                if envio.get("Error"):
                    item.setForeground(QColor(estilo.ALERTA))
                    item.setToolTip(envio["Error"])
                elif con_retraso:
                    item.setForeground(QColor(estilo.BAJO))
                self.tabla.setItem(fila, columna, item)
        self.tabla.blockSignals(False)
        self._cargar_seleccion()

    def seleccionado(self) -> str | None:
        filas = self.tabla.selectionModel().selectedRows() if self.tabla.rowCount() else []
        return self.tabla.item(filas[0].row(), 0).data(Qt.UserRole) if filas else None

    def _marcar_sucio(self) -> None:
        self.problemas.setText("Has cambiado la nota: pulsa «Actualizar vista previa».")
        self.problemas.setVisible(True)

    def _cargar_seleccion(self) -> None:
        identificador = self.seleccionado()
        for boton in self.acciones:
            boton.setEnabled(identificador is not None)
        if not identificador:
            self.vista.setHtml("")
            self.nota.blockSignals(True)
            self.nota.setPlainText("")
            self.nota.blockSignals(False)
            self.problemas.setVisible(False)
            return
        envio = self.repo.obtener("T_COLA_MAIL", identificador) or {}
        self.nota.blockSignals(True)
        self.nota.setPlainText(envio.get("Nota_Entrenador") or "")
        self.nota.blockSignals(False)
        self._previsualizar(envio)

    def _previsualizar(self, envio: dict) -> None:
        try:
            asunto, html = srv.montar(self.repo, self.cfg, envio)
        except Exception as error:
            self.vista.setHtml(f"<p>No se puede montar el correo: {error}</p>")
            return
        self.vista.setHtml(f"<p style='color:#6C7A85'><b>Asunto:</b> {asunto}</p>" + html)
        problemas = srv.comprobar(self.repo, self.cfg, envio)
        self.problemas.setText("\n".join(problemas))
        self.problemas.setVisible(bool(problemas))

    # -- acciones --
    def buscar(self) -> None:
        creados = srv.generar_borradores(self.repo, self.cfg)
        if creados and self.guardar():
            self.refrescar()
        QMessageBox.information(
            self, "Avisos", f"{len(creados)} borradores nuevos."
            if creados else "No hay nada nuevo que enviar.")

    def guardar_nota(self) -> None:
        identificador = self.seleccionado()
        if not identificador:
            return
        self.repo.actualizar("T_COLA_MAIL", identificador,
                             {"Nota_Entrenador": self.nota.toPlainText().strip()})
        if self.guardar():
            self._previsualizar(self.repo.obtener("T_COLA_MAIL", identificador) or {})

    def aprobar(self) -> None:
        identificador = self.seleccionado()
        if not identificador:
            return
        self.guardar_nota()
        self.repo.actualizar("T_COLA_MAIL", identificador,
                             {"Estado": "REVISADO", "Error": ""})
        if self.guardar():
            self.refrescar()

    def _enviador(self):
        try:
            return srv_correo.EnviadorSMTP(self.cfg)
        except RuntimeError as error:
            avisar_error(self, "Falta configurar el correo", error)
            return None

    def _informar(self, resultado) -> None:
        lineas = [f"{len(resultado.enviados)} enviados."]
        if resultado.fallidos:
            lineas.append("\nCon error:\n• " + "\n• ".join(
                f"{i}: {m}" for i, m in resultado.fallidos[:8]))
        if resultado.omitidos:
            lineas.append("\nOmitidos:\n• " + "\n• ".join(
                f"{i}: {m}" for i, m in resultado.omitidos[:8]))
        QMessageBox.information(self, "Envío terminado", "\n".join(lineas))

    def enviar(self) -> None:
        identificador = self.seleccionado()
        if not identificador:
            return
        self.guardar_nota()
        envio = self.repo.obtener("T_COLA_MAIL", identificador) or {}
        usuario = self.repo.obtener("T_USUARIOS", envio.get("ID_Usuario")) or {}
        if not confirmar(self, "Enviar",
                         f"¿Enviar este correo a {usuario.get('Email')}?\n\n"
                         "Un correo enviado no se puede recuperar."):
            return
        enviador = self._enviador()
        if not enviador:
            return
        resultado = srv.enviar(self.repo, self.cfg, enviador, [identificador])
        self.guardar()
        self.refrescar()
        self._informar(resultado)

    def enviar_aprobados(self) -> None:
        aprobados = [e["ID_Envio"] for e in srv.pendientes(self.repo)
                     if e.get("Estado") == "REVISADO"]
        if not aprobados:
            QMessageBox.information(self, "Nada que enviar",
                                    "No hay correos aprobados. Revisa y aprueba primero.")
            return
        if not confirmar(self, "Enviar en lote",
                         f"¿Enviar {len(aprobados)} correos aprobados?"):
            return
        enviador = self._enviador()
        if not enviador:
            return
        resultado = srv.enviar(self.repo, self.cfg, enviador, aprobados)
        self.guardar()
        self.refrescar()
        self._informar(resultado)

    def prueba(self) -> None:
        identificador = self.seleccionado()
        if not identificador:
            return
        self.guardar_nota()
        envio = self.repo.obtener("T_COLA_MAIL", identificador) or {}
        try:
            asunto, html = srv.montar(self.repo, self.cfg, envio)
            enviador = self._enviador()
            if not enviador:
                return
            enviador.enviar(enviador.remitente, f"[PRUEBA] {asunto}", html)
        except Exception as error:
            avisar_error(self, "No se ha podido enviar la prueba", error)
            return
        QMessageBox.information(self, "Prueba enviada",
                                "Te lo has enviado a ti mismo. Revísalo antes de "
                                "mandárselo al usuario.")

    def cancelar(self) -> None:
        identificador = self.seleccionado()
        if identificador and confirmar(self, "Cancelar envío",
                                       "¿Descartar este correo? No se enviará."):
            self.repo.actualizar("T_COLA_MAIL", identificador, {"Estado": "CANCELADO"})
            if self.guardar():
                self.refrescar()

    def editar_plantillas(self) -> None:
        DialogoPlantillas(self.repo, self).exec()
        self.guardar()
        self.refrescar()

    def probar_conexion(self) -> None:
        correcto, mensaje = srv_correo.probar_conexion(self.cfg)
        (QMessageBox.information if correcto else QMessageBox.warning)(
            self, "Conexión de correo", mensaje)

    def importar_respuestas(self) -> None:
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Fichero de respuestas de Google Forms",
            str(cfg_mod.RAIZ), "Ficheros CSV (*.csv)")
        if not ruta:
            return
        try:
            resultado = srv_respuestas.importar(self.repo, self.cfg, Path(ruta))
        except Exception as error:
            avisar_error(self, "No se han podido importar", error)
            return
        self.guardar()
        self.refrescar()
        lineas = [resultado.resumen()]
        if resultado.acciones:
            lineas.append("\nLo que ha cambiado:\n• " + "\n• ".join(resultado.acciones[:10]))
        if resultado.avisos:
            lineas.append("\n" + "\n".join(resultado.avisos))
        QMessageBox.information(self, "Respuestas importadas", "\n".join(lineas))
