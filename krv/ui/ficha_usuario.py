"""Ficha del usuario: los datos básicos."""

from __future__ import annotations

from datetime import date

from PySide6.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QFormLayout, QGroupBox, QHBoxLayout,
    QLineEdit, QPlainTextEdit, QVBoxLayout,
)

from ..datos.repositorio import Repositorio
from ..nucleo.fechas import edad as calcular_edad
from ..servicios import usuarios as srv
from .comunes import avisar_error, campo_fecha, desplegable, etiqueta, leer_fecha

ESTADOS = [("ACTIVO", "Activo"), ("INACTIVO", "Inactivo"), ("BAJA", "Baja")]
SEXOS = [("H", "Hombre"), ("M", "Mujer")]
ORIGENES = [("FORM", "Formulario"), ("PRESENCIAL", "Presencial")]


class FichaUsuario(QDialog):
    def __init__(self, repo: Repositorio, id_usuario: str | None = None, padre=None):
        super().__init__(padre)
        self.repo = repo
        self.id_usuario = id_usuario
        self.datos = repo.obtener("T_USUARIOS", id_usuario) if id_usuario else {}
        self.setWindowTitle("Ficha de usuario" if id_usuario else "Nuevo usuario")
        self.setMinimumWidth(560)
        self._construir()

    def _construir(self) -> None:
        raiz = QVBoxLayout(self)
        titulo = "Editar usuario" if self.id_usuario else "Alta de usuario"
        raiz.addWidget(etiqueta(titulo, "titulo"))
        if self.id_usuario:
            raiz.addWidget(etiqueta(f"Identificador {self.id_usuario}", "subtitulo"))

        personales = QGroupBox("Datos personales")
        form = QFormLayout(personales)
        self.nombre = QLineEdit(self.datos.get("Nombre") or "")
        self.apellidos = QLineEdit(self.datos.get("Apellidos") or "")
        self.nacimiento = campo_fecha(self.datos.get("F_Nacimiento") or date(1990, 1, 1))
        self.sexo = desplegable(SEXOS, self.datos.get("Sexo"), vacio=not self.id_usuario)
        self.email = QLineEdit(self.datos.get("Email") or "")
        self.telefono = QLineEdit(self.datos.get("Telefono") or "")
        self.email.setPlaceholderText("Sin correo no podrá recibir los cuestionarios")

        self.edad_texto = etiqueta("", "subtitulo")
        self.nacimiento.dateChanged.connect(self._refrescar_edad)

        form.addRow("Nombre *", self.nombre)
        form.addRow("Apellidos", self.apellidos)
        form.addRow("Fecha de nacimiento *", self.nacimiento)
        form.addRow("", self.edad_texto)
        form.addRow("Sexo *", self.sexo)
        form.addRow("Correo electrónico", self.email)
        form.addRow("Teléfono", self.telefono)
        raiz.addWidget(personales)

        gestion = QGroupBox("Gestión")
        form2 = QFormLayout(gestion)
        self.alta = campo_fecha(self.datos.get("F_Alta") or date.today())
        self.estado = desplegable(ESTADOS, self.datos.get("Estado") or "ACTIVO")
        self.acepta = QCheckBox("Acepta recibir correos")
        self.acepta.setChecked(bool(self.datos.get("Acepta_Emails_SN", True)))
        form2.addRow("Fecha de alta *", self.alta)
        form2.addRow("Estado *", self.estado)
        form2.addRow("", self.acepta)
        raiz.addWidget(gestion)

        consentimiento = QGroupBox("Consentimiento de tratamiento de datos")
        form3 = QFormLayout(consentimiento)
        self.consentido = QCheckBox("Consentimiento registrado")
        self.consentido.setChecked(bool(self.datos.get("Consentimiento_SN")))
        self.f_consentimiento = campo_fecha(self.datos.get("F_Consentimiento"), opcional=True)
        self.origen = desplegable(ORIGENES, self.datos.get("Origen_Consentimiento"), vacio=True)
        form3.addRow("", self.consentido)
        form3.addRow("Fecha", self.f_consentimiento)
        form3.addRow("Origen", self.origen)
        form3.addRow("", etiqueta(
            "Se tratan datos de salud. Sin consentimiento registrado, la aplicación "
            "no enviará correos a este usuario.", "subtitulo", ajustar=True))
        raiz.addWidget(consentimiento)

        self.notas = QPlainTextEdit(self.datos.get("Notas") or "")
        self.notas.setMaximumHeight(70)
        caja_notas = QVBoxLayout()
        caja_notas.addWidget(etiqueta("Notas"))
        caja_notas.addWidget(self.notas)
        raiz.addLayout(caja_notas)

        botones = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        botones.button(QDialogButtonBox.Save).setText("Guardar")
        botones.button(QDialogButtonBox.Cancel).setText("Cancelar")
        botones.accepted.connect(self._guardar)
        botones.rejected.connect(self.reject)
        raiz.addWidget(botones)
        self._refrescar_edad()

    def _refrescar_edad(self) -> None:
        nacimiento = leer_fecha(self.nacimiento)
        if nacimiento and nacimiento.year > 1900:
            self.edad_texto.setText(f"{calcular_edad(nacimiento)} años")
        else:
            self.edad_texto.setText("")

    def _recoger(self) -> dict:
        return {
            "Nombre": self.nombre.text().strip(),
            "Apellidos": self.apellidos.text().strip(),
            "F_Nacimiento": leer_fecha(self.nacimiento),
            "Sexo": self.sexo.currentData(),
            "Email": self.email.text().strip(),
            "Telefono": self.telefono.text().strip(),
            "F_Alta": leer_fecha(self.alta),
            "Estado": self.estado.currentData(),
            "Consentimiento_SN": self.consentido.isChecked(),
            "F_Consentimiento": leer_fecha(self.f_consentimiento),
            "Origen_Consentimiento": self.origen.currentData(),
            "Acepta_Emails_SN": self.acepta.isChecked(),
            "Notas": self.notas.toPlainText().strip(),
        }

    def _guardar(self) -> None:
        datos = self._recoger()
        try:
            if self.id_usuario:
                self.repo.actualizar("T_USUARIOS", self.id_usuario, datos)
            else:
                self.id_usuario = srv.alta(self.repo, datos)
        except Exception as error:  # validación o integridad
            avisar_error(self, "No se ha podido guardar", error)
            return
        self.accept()
