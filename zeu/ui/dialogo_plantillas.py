"""Plantillas de correo: sobre todo, la URL del formulario de Google."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QDialog, QDialogButtonBox, QFormLayout,
    QHeaderView, QLineEdit, QTableWidget, QTableWidgetItem, QTextBrowser,
    QVBoxLayout,
)

from ..datos.repositorio import Repositorio
from ..servicios import correo as srv_correo
from .comunes import avisar_error, etiqueta

NOMBRES = {
    "CONSENTIMIENTO": "Consentimiento de datos", "BIENVENIDA": "Bienvenida al ciclo",
    "CHECKIN_MITAD": "Check-in de mitad", "ENCUESTA_T14": "Encuesta a T-14 días",
    "RECORDATORIO": "Recordatorio de la encuesta", "CIERRE_CICLO": "Cierre de ciclo",
    "AGRADECIMIENTO": "Agradecimiento por responder",
}
AYUDA = (
    "Para que un correo pueda llevar su botón, necesita la <b>URL de respuesta "
    "prerrellenada</b> del formulario de Google:<br><br>"
    "1. En el formulario, menú <b>⋮ → Obtener enlace prerrellenado</b>.<br>"
    "2. Escribe <code>USUARIO</code> en el campo oculto del identificador de "
    "usuario y <code>ENVIO</code> en el del envío, y pulsa <b>Obtener enlace</b>.<br>"
    "3. Copia la URL y <b>sustituye</b> en ella <code>USUARIO</code> por "
    "<code>{{id_usuario}}</code> y <code>ENVIO</code> por <code>{{id_envio}}</code>.<br><br>"
    "Queda algo así:<br><code>https://docs.google.com/forms/d/e/XXXX/viewform?"
    "usp=pp_url&amp;entry.111={{id_usuario}}&amp;entry.222={{id_envio}}</code><br><br>"
    "Así cada usuario recibe su enlace y la respuesta queda atada a su envío sin "
    "que él tenga que identificarse."
)


class DialogoPlantillas(QDialog):
    def __init__(self, repo: Repositorio, padre=None):
        super().__init__(padre)
        self.repo = repo
        self.actual: str | None = None
        self.setWindowTitle("Plantillas de correo")
        self.setMinimumSize(820, 620)

        raiz = QVBoxLayout(self)
        raiz.addWidget(etiqueta("Plantillas de correo", "titulo"))
        raiz.addWidget(etiqueta(
            "El texto de cada correo se edita en la hoja T_PLANTILLAS_MAIL del "
            "libro. Aquí se configura lo que hace falta para poder enviarlos.",
            "subtitulo", ajustar=True))

        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(
            ["Correo", "Necesita formulario", "URL configurada", "Activa"])
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.tabla.setMaximumHeight(210)
        self.tabla.itemSelectionChanged.connect(self._cargar)
        raiz.addWidget(self.tabla)

        form = QFormLayout()
        self.url = QLineEdit()
        self.url.setPlaceholderText(
            "https://docs.google.com/forms/d/e/…?usp=pp_url&entry.111={{id_usuario}}…")
        self.activa = QCheckBox("Plantilla activa")
        self.vacaciones = QCheckBox("Puede salir sin revisión en modo vacaciones")
        form.addRow("URL del formulario", self.url)
        form.addRow("", self.activa)
        form.addRow("", self.vacaciones)
        raiz.addLayout(form)

        self.aviso = etiqueta("", "aviso", ajustar=True)
        raiz.addWidget(self.aviso)

        ayuda = QTextBrowser()
        ayuda.setHtml(AYUDA)
        ayuda.setMaximumHeight(190)
        raiz.addWidget(ayuda)

        botones = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Close)
        botones.button(QDialogButtonBox.Save).setText("Guardar esta plantilla")
        botones.button(QDialogButtonBox.Close).setText("Cerrar")
        botones.accepted.connect(self._guardar)
        botones.rejected.connect(self.accept)
        raiz.addWidget(botones)
        self._refrescar()

    def _refrescar(self, seleccionar: str | None = None) -> None:
        plantillas = self.repo.listar("T_PLANTILLAS_MAIL", orden="Codigo")
        self.tabla.blockSignals(True)
        self.tabla.setRowCount(len(plantillas))
        for fila, plantilla in enumerate(plantillas):
            necesita = "{{enlace_form}}" in (plantilla.get("Cuerpo_HTML") or "")
            tiene = bool((plantilla.get("URL_Form") or "").strip())
            valores = [
                NOMBRES.get(plantilla.get("Codigo"), plantilla.get("Codigo") or ""),
                "Sí" if necesita else "",
                ("Sí" if tiene else "FALTA") if necesita else "",
                "Sí" if plantilla.get("Activo_SN") else "No"]
            for columna, texto in enumerate(valores):
                item = QTableWidgetItem(texto)
                item.setData(Qt.UserRole, plantilla["ID_Plantilla"])
                self.tabla.setItem(fila, columna, item)
        self.tabla.blockSignals(False)
        objetivo = seleccionar or self.actual
        for fila in range(self.tabla.rowCount()):
            if self.tabla.item(fila, 0).data(Qt.UserRole) == objetivo:
                self.tabla.selectRow(fila)
                break
        else:
            if self.tabla.rowCount():
                self.tabla.selectRow(0)
        self._cargar()

    def _cargar(self) -> None:
        filas = self.tabla.selectionModel().selectedRows() if self.tabla.rowCount() else []
        if not filas:
            self.actual = None
            return
        self.actual = self.tabla.item(filas[0].row(), 0).data(Qt.UserRole)
        plantilla = self.repo.obtener("T_PLANTILLAS_MAIL", self.actual) or {}
        self.url.setText(plantilla.get("URL_Form") or "")
        self.activa.setChecked(bool(plantilla.get("Activo_SN")))
        self.vacaciones.setChecked(bool(plantilla.get("Permite_Modo_Vacaciones_SN")))
        necesita = "{{enlace_form}}" in (plantilla.get("Cuerpo_HTML") or "")
        self.url.setEnabled(necesita)
        self.aviso.setText(
            "Este correo no lleva botón a ningún formulario: no necesita URL."
            if not necesita else
            ("Sin esta URL, este correo no se puede enviar."
             if not (plantilla.get("URL_Form") or "").strip() else ""))
        self.aviso.setVisible(bool(self.aviso.text()))

    def _guardar(self) -> None:
        if not self.actual:
            return
        url = self.url.text().strip()
        if url and "{{id_usuario}}" not in url:
            avisar_error(self, "Falta el identificador en la URL", Exception(
                "La URL no lleva {{id_usuario}}. Sin eso no se sabría quién ha "
                "respondido.\n\nSustituye en el enlace prerrellenado el valor que "
                "escribiste por {{id_usuario}} (y por {{id_envio}} el del envío)."))
            return
        try:
            self.repo.actualizar("T_PLANTILLAS_MAIL", self.actual, {
                "URL_Form": url, "Activo_SN": self.activa.isChecked(),
                "Permite_Modo_Vacaciones_SN": self.vacaciones.isChecked()})
        except Exception as error:
            avisar_error(self, "No se ha podido guardar", error)
            return
        self._refrescar(self.actual)
