"""Alta y edición de un ejercicio del catálogo."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QGroupBox,
    QLineEdit, QListWidget, QListWidgetItem, QPlainTextEdit, QSpinBox, QVBoxLayout,
)

from ..datos.repositorio import Repositorio
from ..servicios import ejercicios as srv
from .comunes import avisar_error, desplegable, etiqueta

ETIQUETAS_PATRON = {
    "EMPUJE_H": "Empuje horizontal", "EMPUJE_V": "Empuje vertical",
    "TRACCION_H": "Tracción horizontal", "TRACCION_V": "Tracción vertical",
    "DOMINANTE_RODILLA": "Dominante de rodilla", "DOMINANTE_CADERA": "Dominante de cadera",
    "CORE": "Core", "LOCOMOCION": "Locomoción", "MONOARTICULAR": "Monoarticular",
    "MOVILIDAD": "Movilidad",
}


# Versión corta para las tablas, donde el ancho es oro.
ETIQUETAS_PATRON_CORTO = {
    "EMPUJE_H": "Empuje H", "EMPUJE_V": "Empuje V",
    "TRACCION_H": "Tracción H", "TRACCION_V": "Tracción V",
    "DOMINANTE_RODILLA": "Dom. rodilla", "DOMINANTE_CADERA": "Dom. cadera",
    "CORE": "Core", "LOCOMOCION": "Locomoción",
    "MONOARTICULAR": "Monoarticular", "MOVILIDAD": "Movilidad",
}


def texto_patron(clave: str | None, corto: bool = False) -> str:
    tabla = ETIQUETAS_PATRON_CORTO if corto else ETIQUETAS_PATRON
    return tabla.get(clave, clave or "")


def _lista_multiple(opciones, seleccionados: set[str], alto: int = 90) -> QListWidget:
    widget = QListWidget()
    widget.setSelectionMode(QListWidget.MultiSelection)
    widget.setMaximumHeight(alto)
    for opcion in opciones:
        item = QListWidgetItem(opcion.replace("_", " ").capitalize())
        item.setData(32, opcion)
        widget.addItem(item)
        if opcion in seleccionados:
            item.setSelected(True)
    return widget


def _seleccion(widget: QListWidget) -> list[str]:
    return [i.data(32) for i in widget.selectedItems()]


class FichaEjercicio(QDialog):
    def __init__(self, repo: Repositorio, id_ejercicio: str | None = None, padre=None):
        super().__init__(padre)
        self.repo = repo
        self.id_ejercicio = id_ejercicio
        self.datos = repo.obtener("T_EJERCICIOS", id_ejercicio) if id_ejercicio else {}
        self.setWindowTitle("Ejercicio" if id_ejercicio else "Nuevo ejercicio")
        self.setMinimumWidth(560)
        self._construir()

    def _construir(self) -> None:
        raiz = QVBoxLayout(self)
        raiz.addWidget(etiqueta(
            "Editar ejercicio" if self.id_ejercicio else "Nuevo ejercicio", "titulo"))
        if self.id_ejercicio:
            raiz.addWidget(etiqueta(self.id_ejercicio, "subtitulo"))

        clasificacion = QGroupBox("Clasificación")
        form = QFormLayout(clasificacion)
        self.nombre = QLineEdit(self.datos.get("Nombre") or "")
        self.patron = desplegable(
            [(p, texto_patron(p)) for p in srv.PATRONES],
            self.datos.get("Patron"), vacio=not self.id_ejercicio)
        self.grupo = desplegable(
            [(g, g.replace("_", " ").capitalize()) for g in srv.GRUPOS],
            self.datos.get("Grupo_Principal"), vacio=not self.id_ejercicio)
        self.secundarios = _lista_multiple(
            srv.GRUPOS, set(srv.lista(self.datos.get("Grupos_Secundarios"))))
        form.addRow("Nombre *", self.nombre)
        form.addRow("Patrón de movimiento *", self.patron)
        form.addRow("Grupo principal *", self.grupo)
        form.addRow("Grupos secundarios", self.secundarios)
        form.addRow("", etiqueta(
            "El patrón es lo que permite equilibrar una sesión y buscar sustitutos.",
            "subtitulo", ajustar=True))
        raiz.addWidget(clasificacion)

        ejecucion = QGroupBox("Ejecución")
        form2 = QFormLayout(ejecucion)
        self.material = _lista_multiple(
            srv.MATERIALES, srv.material_de(self.datos), alto=110)
        self.nivel = QSpinBox(); self.nivel.setRange(1, 3)
        self.nivel.setValue(int(self.datos.get("Nivel") or 1))
        self.incremento = QDoubleSpinBox()
        self.incremento.setRange(0, 25); self.incremento.setSingleStep(0.25)
        self.incremento.setSuffix(" kg"); self.incremento.setSpecialValueText("sin carga")
        self.incremento.setValue(float(self.datos.get("Incremento_Kg") or 0))
        self.unilateral = QCheckBox("Se ejecuta por lados")
        self.unilateral.setChecked(bool(self.datos.get("Unilateral_SN")))
        self.basico = QCheckBox("Es un ejercicio básico")
        self.basico.setChecked(bool(self.datos.get("Es_Basico_SN")))
        self.activo = QCheckBox("Activo en el catálogo")
        self.activo.setChecked(bool(self.datos.get("Activo_SN", True))
                               if self.id_ejercicio else True)
        form2.addRow("Material *", self.material)
        form2.addRow("Nivel", self.nivel)
        form2.addRow("Incremento de carga", self.incremento)
        form2.addRow("", etiqueta(
            "Salto mínimo real: 2,5 kg en barra, 2 en mancuernas, 5 en máquina de placas. "
            "Es lo que evita imprimir «77,3 kg».", "subtitulo", ajustar=True))
        form2.addRow("", self.unilateral)
        form2.addRow("", self.basico)
        form2.addRow("", self.activo)
        raiz.addWidget(ejecucion)

        otros = QGroupBox("Otros datos")
        form3 = QFormLayout(otros)
        self.video = QLineEdit(self.datos.get("Video_URL") or "")
        self.video.setPlaceholderText("Enlace al vídeo de referencia")
        self.contra = QPlainTextEdit(self.datos.get("Contraindicaciones") or "")
        self.contra.setMaximumHeight(56)
        self.contra.setPlaceholderText("Dolor de hombro anterior; lumbalgia aguda…")
        form3.addRow("Vídeo", self.video)
        form3.addRow("Contraindicaciones", self.contra)
        raiz.addWidget(otros)

        botones = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        botones.button(QDialogButtonBox.Save).setText("Guardar")
        botones.button(QDialogButtonBox.Cancel).setText("Cancelar")
        botones.accepted.connect(self._guardar)
        botones.rejected.connect(self.reject)
        raiz.addWidget(botones)

    def _recoger(self) -> dict:
        return {
            "Nombre": self.nombre.text().strip(),
            "Patron": self.patron.currentData(),
            "Grupo_Principal": self.grupo.currentData(),
            "Grupos_Secundarios": srv.texto(_seleccion(self.secundarios)),
            "Material": srv.texto(_seleccion(self.material)),
            "Nivel": self.nivel.value(),
            "Unilateral_SN": self.unilateral.isChecked(),
            "Es_Basico_SN": self.basico.isChecked(),
            "Incremento_Kg": self.incremento.value() or None,
            "Video_URL": self.video.text().strip(),
            "Contraindicaciones": self.contra.toPlainText().strip(),
            "Activo_SN": self.activo.isChecked(),
        }

    def _guardar(self) -> None:
        datos = self._recoger()
        if not datos["Material"]:
            avisar_error(self, "Falta el material", Exception(
                "Indica al menos un material. Si no hace falta ninguno, marca «Peso corporal»."))
            return
        try:
            if self.id_ejercicio:
                self.repo.actualizar("T_EJERCICIOS", self.id_ejercicio, datos)
            else:
                self.id_ejercicio = self.repo.insertar("T_EJERCICIOS", datos)
        except Exception as error:
            avisar_error(self, "No se ha podido guardar", error)
            return
        self.accept()
