"""Diálogos del editor de planificación: ciclo, sesión y línea de ejercicio."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout,
    QLineEdit, QPlainTextEdit, QSpinBox, QVBoxLayout,
)

from ..datos.esquema import BLOQUE, ENFOQUE, MODO_CARGA
from ..datos.repositorio import Repositorio
from ..servicios import ejercicios as srv_ejercicios
from ..servicios import programas as srv
from .comunes import avisar_error, desplegable, etiqueta
from .ficha_ejercicio import texto_patron

TIPOS_SESION = [("FUERZA", "Fuerza"), ("CARDIO", "Cardio"), ("MOVILIDAD", "Movilidad"),
                ("MIXTA", "Mixta"), ("DESCANSO_ACTIVO", "Descanso activo")]
PROGRESIONES = [
    ("", "Ninguna"),
    ("LINEAL:+2.5", "Lineal +2,5 kg por semana"),
    ("LINEAL:+1.25", "Lineal +1,25 kg por semana"),
    ("LINEAL:+5", "Lineal +5 kg por semana"),
    ("DOBLE_PROGRESION", "Doble progresión (reps y luego carga)"),
    ("DESCARGA:60", "Descarga al 60 %"),
    ("AUTORREGULADA:RIR2", "Autorregulada por RIR"),
]
ETIQUETA_MODO = {
    "PCT1RM": "% del 1RM", "RPE": "RPE", "RIR": "Repeticiones en reserva",
    "KG": "Kilos fijos", "PESO_CORPORAL": "Peso corporal", "TIEMPO": "Tiempo (s)",
}


class DialogoCiclo(QDialog):
    def __init__(self, repo: Repositorio, id_ciclo: str | None = None,
                 tipo: str = "MACRO", id_padre: str | None = None, padre=None):
        super().__init__(padre)
        self.repo = repo
        self.id_ciclo = id_ciclo
        self.datos = repo.obtener("T_CICLOS", id_ciclo) if id_ciclo else {}
        self.tipo = self.datos.get("Tipo") or tipo
        self.id_padre = self.datos.get("ID_Padre") or id_padre
        nombres = {"MACRO": "Macrociclo", "MESO": "Mesociclo", "MICRO": "Microciclo"}
        self.setWindowTitle(nombres[self.tipo])
        self.setMinimumWidth(480)

        raiz = QVBoxLayout(self)
        raiz.addWidget(etiqueta(nombres[self.tipo], "titulo"))
        if self.id_padre:
            padre_ciclo = repo.obtener("T_CICLOS", self.id_padre) or {}
            raiz.addWidget(etiqueta(f"Dentro de «{padre_ciclo.get('Nombre')}»", "subtitulo"))

        form = QFormLayout()
        self.nombre = QLineEdit(self.datos.get("Nombre") or "")
        self.duracion = QSpinBox(); self.duracion.setRange(1, 104)
        self.duracion.setValue(int(self.datos.get("Duracion_Sem") or 4))
        self.duracion.setSuffix(" semanas")
        self.orden = QSpinBox(); self.orden.setRange(1, 50)
        self.orden.setValue(int(self.datos.get("Orden") or
                                len(srv.hijos(repo, self.id_padre)) + 1))
        self.objetivo = QLineEdit(self.datos.get("Objetivo_Ciclo") or "")
        self.enfoque = desplegable([(e, e.capitalize()) for e in ENFOQUE],
                                   self.datos.get("Enfoque"), vacio=True)
        self.plantilla = QCheckBox("Es una plantilla reutilizable")
        self.plantilla.setChecked(bool(self.datos.get("Es_Plantilla_SN")))
        self.notas = QPlainTextEdit(self.datos.get("Notas") or "")
        self.notas.setMaximumHeight(60)

        form.addRow("Nombre *", self.nombre)
        form.addRow("Duración *", self.duracion)
        form.addRow("Orden", self.orden)
        if self.tipo != "MICRO":
            form.addRow("Objetivo", self.objetivo)
        if self.tipo == "MESO":
            form.addRow("Enfoque", self.enfoque)
        if self.tipo == "MACRO":
            form.addRow("", self.plantilla)
        form.addRow("Notas", self.notas)
        raiz.addLayout(form)
        raiz.addWidget(etiqueta(
            "La duración de los hijos debería sumar la del padre. Si no cuadra, la "
            "aplicación avisa pero no impide guardar.", "subtitulo", ajustar=True))

        botones = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        botones.button(QDialogButtonBox.Save).setText("Guardar")
        botones.button(QDialogButtonBox.Cancel).setText("Cancelar")
        botones.accepted.connect(self._guardar)
        botones.rejected.connect(self.reject)
        raiz.addWidget(botones)

    def _guardar(self) -> None:
        datos = {
            "Nombre": self.nombre.text().strip(), "Tipo": self.tipo,
            "ID_Padre": self.id_padre, "Orden": self.orden.value(),
            "Duracion_Sem": self.duracion.value(),
            "Objetivo_Ciclo": self.objetivo.text().strip(),
            "Enfoque": self.enfoque.currentData(),
            "Es_Plantilla_SN": self.plantilla.isChecked(),
            "Notas": self.notas.toPlainText().strip(),
        }
        try:
            if self.id_ciclo:
                self.repo.actualizar("T_CICLOS", self.id_ciclo, datos)
            else:
                datos["Origen"] = "MANUAL"
                self.id_ciclo = self.repo.insertar("T_CICLOS", datos)
        except Exception as error:
            avisar_error(self, "No se ha podido guardar", error)
            return
        self.accept()


class DialogoSesion(QDialog):
    def __init__(self, repo: Repositorio, id_ciclo: str,
                 id_sesion: str | None = None, padre=None):
        super().__init__(padre)
        self.repo = repo
        self.id_ciclo = id_ciclo
        self.id_sesion = id_sesion
        self.datos = repo.obtener("T_SESIONES", id_sesion) if id_sesion else {}
        self.setWindowTitle("Sesión")
        self.setMinimumWidth(440)

        raiz = QVBoxLayout(self)
        raiz.addWidget(etiqueta("Sesión", "titulo"))
        form = QFormLayout()
        self.dia = QSpinBox(); self.dia.setRange(1, 7)
        self.dia.setValue(int(self.datos.get("Num_Dia") or
                              len(srv.sesiones(repo, id_ciclo)) + 1))
        self.nombre = QLineEdit(self.datos.get("Nombre") or "")
        self.tipo = desplegable(TIPOS_SESION, self.datos.get("Tipo") or "FUERZA")
        self.duracion = QSpinBox(); self.duracion.setRange(0, 180)
        self.duracion.setSingleStep(5); self.duracion.setSuffix(" min")
        self.duracion.setValue(int(self.datos.get("Duracion_Est_Min") or 60))
        self.notas = QPlainTextEdit(self.datos.get("Notas") or "")
        self.notas.setMaximumHeight(56)
        form.addRow("Día de la semana *", self.dia)
        form.addRow("Nombre", self.nombre)
        form.addRow("Tipo", self.tipo)
        form.addRow("Duración estimada", self.duracion)
        form.addRow("Notas", self.notas)
        raiz.addLayout(form)

        botones = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        botones.button(QDialogButtonBox.Save).setText("Guardar")
        botones.button(QDialogButtonBox.Cancel).setText("Cancelar")
        botones.accepted.connect(self._guardar)
        botones.rejected.connect(self.reject)
        raiz.addWidget(botones)

    def _guardar(self) -> None:
        datos = {"ID_Ciclo": self.id_ciclo, "Num_Dia": self.dia.value(),
                 "Nombre": self.nombre.text().strip(), "Tipo": self.tipo.currentData(),
                 "Duracion_Est_Min": self.duracion.value(),
                 "Notas": self.notas.toPlainText().strip()}
        try:
            if self.id_sesion:
                self.repo.actualizar("T_SESIONES", self.id_sesion, datos)
            else:
                self.id_sesion = self.repo.insertar("T_SESIONES", datos)
        except Exception as error:
            avisar_error(self, "No se ha podido guardar", error)
            return
        self.accept()


class DialogoLinea(QDialog):
    def __init__(self, repo: Repositorio, id_sesion: str,
                 id_linea: str | None = None, padre=None):
        super().__init__(padre)
        self.repo = repo
        self.id_sesion = id_sesion
        self.id_linea = id_linea
        self.datos = repo.obtener("T_SESION_DET", id_linea) if id_linea else {}
        self.setWindowTitle("Ejercicio de la sesión")
        self.setMinimumWidth(520)

        raiz = QVBoxLayout(self)
        raiz.addWidget(etiqueta("Ejercicio de la sesión", "titulo"))
        form = QFormLayout()

        self.bloque = desplegable([(b, b.replace("_", " ").capitalize()) for b in BLOQUE],
                                  self.datos.get("Bloque") or "PRINCIPAL")
        self.ejercicio = QComboBox()
        for e in srv_ejercicios.activos(repo):
            self.ejercicio.addItem(
                f"{e['Nombre']}  ·  {texto_patron(e.get('Patron'), corto=True)}",
                e["ID_Ejercicio"])
        indice = self.ejercicio.findData(self.datos.get("ID_Ejercicio"))
        if indice >= 0:
            self.ejercicio.setCurrentIndex(indice)
        self.ejercicio.setEditable(True)
        self.ejercicio.completer().setCaseSensitivity(False)
        self.ejercicio.currentIndexChanged.connect(self._pista_material)

        self.series = QSpinBox(); self.series.setRange(1, 12)
        self.series.setValue(int(self.datos.get("Series") or 3))
        self.reps = QLineEdit(str(self.datos.get("Reps") or "10"))
        self.reps.setPlaceholderText("10, 8-10, AMRAP, 30 s…")
        self.modo = desplegable([(m, ETIQUETA_MODO.get(m, m)) for m in MODO_CARGA],
                                self.datos.get("Modo_Carga") or "RIR")
        self.modo.currentIndexChanged.connect(self._pista_modo)
        self.valor = QDoubleSpinBox(); self.valor.setRange(0, 1000)
        self.valor.setDecimals(1)
        self.valor.setValue(float(self.datos.get("Valor_Carga") or 2))
        self.descanso = QSpinBox(); self.descanso.setRange(0, 600)
        self.descanso.setSingleStep(15); self.descanso.setSuffix(" s")
        self.descanso.setValue(int(self.datos.get("Descanso_Seg") or 90))
        self.tempo = QLineEdit(self.datos.get("Tempo") or "")
        self.tempo.setPlaceholderText("3-0-1-0")
        self.progresion = desplegable(PROGRESIONES, self.datos.get("Progresion") or "")
        self.progresion.setEditable(True)
        self.notas = QLineEdit(self.datos.get("Notas") or "")

        form.addRow("Bloque *", self.bloque)
        form.addRow("Ejercicio *", self.ejercicio)
        form.addRow("Series *", self.series)
        form.addRow("Repeticiones", self.reps)
        form.addRow("Modo de carga", self.modo)
        form.addRow("Valor", self.valor)
        self.pista = etiqueta("", "subtitulo", ajustar=True)
        form.addRow("", self.pista)
        form.addRow("Descanso", self.descanso)
        form.addRow("Tempo", self.tempo)
        form.addRow("Progresión", self.progresion)
        form.addRow("Notas", self.notas)
        raiz.addLayout(form)

        botones = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        botones.button(QDialogButtonBox.Save).setText("Guardar")
        botones.button(QDialogButtonBox.Cancel).setText("Cancelar")
        botones.accepted.connect(self._guardar)
        botones.rejected.connect(self.reject)
        raiz.addWidget(botones)
        self._pista_modo()

    def _pista_modo(self) -> None:
        modo = self.modo.currentData()
        textos = {
            "PCT1RM": "Porcentaje del 1RM del usuario. Los kilos se calculan al imprimir.",
            "RPE": "Esfuerzo percibido de 1 a 10. Se traduce a porcentaje según las repeticiones.",
            "RIR": "Repeticiones que deja en reserva. RIR 2 equivale a RPE 8.",
            "KG": "Carga fija en kilos, igual para todos los usuarios.",
            "PESO_CORPORAL": "Sin carga externa.",
            "TIEMPO": "Segundos de trabajo, para isométricos y cardio.",
        }
        self.pista.setText(textos.get(modo, ""))
        self.valor.setEnabled(modo not in ("PESO_CORPORAL",))
        self._pista_material()

    def _pista_material(self) -> None:
        ejercicio = self.repo.obtener("T_EJERCICIOS", self.ejercicio.currentData())
        if not ejercicio:
            return
        incremento = ejercicio.get("Incremento_Kg")
        if incremento and self.modo.currentData() in ("PCT1RM", "RPE", "RIR", "KG"):
            self.pista.setText(
                self.pista.text() +
                f" Se redondeará a múltiplos de {incremento:g} kg.")

    def _guardar(self) -> None:
        siguiente = len(srv.lineas(self.repo, self.id_sesion)) + 1
        datos = {
            "ID_Sesion": self.id_sesion,
            "Orden": self.datos.get("Orden") or siguiente,
            "Bloque": self.bloque.currentData(),
            "ID_Ejercicio": self.ejercicio.currentData(),
            "Series": self.series.value(), "Reps": self.reps.text().strip(),
            "Modo_Carga": self.modo.currentData(),
            "Valor_Carga": (None if self.modo.currentData() == "PESO_CORPORAL"
                            else self.valor.value()),
            "Descanso_Seg": self.descanso.value(),
            "Tempo": self.tempo.text().strip(),
            "Progresion": (self.progresion.currentData()
                           if self.progresion.currentData() is not None
                           else self.progresion.currentText().strip()),
            "Notas": self.notas.text().strip(),
        }
        try:
            if self.id_linea:
                self.repo.actualizar("T_SESION_DET", self.id_linea, datos)
            else:
                self.id_linea = self.repo.insertar("T_SESION_DET", datos)
        except Exception as error:
            avisar_error(self, "No se ha podido guardar", error)
            return
        self.accept()
