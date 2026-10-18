"""Ventanas independientes de información adicional del usuario:
objetivos, salud y disponibilidad. Cada una mantiene su histórico.
"""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QDialog, QFormLayout, QGroupBox, QHBoxLayout,
    QHeaderView, QLineEdit, QPlainTextEdit, QPushButton, QSpinBox,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from ..datos.esquema import tabla as buscar_tabla
from ..datos.repositorio import Repositorio
from ..nucleo.fechas import formatear
from ..servicios import usuarios as srv
from .comunes import (avisar_error, campo_fecha, confirmar, desplegable,
                      etiqueta, leer_fecha)

TIPOS_OBJETIVO = [
    ("PERDER_GRASA", "Perder grasa"), ("HIPERTROFIA", "Hipertrofia"),
    ("FUERZA", "Fuerza"), ("SALUD_GENERAL", "Salud general"),
    ("RENDIMIENTO", "Rendimiento"), ("REHABILITACION", "Rehabilitación"),
    ("OTRO", "Otro"),
]
ESTADOS_OBJETIVO = [
    ("ACTIVO", "Activo"), ("CUMPLIDO", "Cumplido"),
    ("MODIFICADO", "Modificado"), ("DESCARTADO", "Descartado"),
]
FRANJAS = [("MANANA", "Mañana"), ("MEDIODIA", "Mediodía"), ("TARDE", "Tarde"),
           ("NOCHE", "Noche"), ("VARIABLE", "Variable")]
LUGARES = [("GIMNASIO", "Gimnasio"), ("CASA", "Casa"), ("MIXTO", "Mixto")]


def _poner_fecha(campo, valor: date | None) -> None:
    valor = valor or date.today()
    campo.setDate(QDate(valor.year, valor.month, valor.day))


def _tabla(cabeceras: list[str]) -> QTableWidget:
    tabla = QTableWidget(0, len(cabeceras))
    tabla.setHorizontalHeaderLabels(cabeceras)
    tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
    tabla.setSelectionMode(QAbstractItemView.SingleSelection)
    tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
    tabla.verticalHeader().setVisible(False)
    tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    tabla.horizontalHeader().setStretchLastSection(True)
    tabla.setMaximumHeight(170)
    return tabla


class _DialogoHistorico(QDialog):
    """Base de las tres ventanas: histórico arriba, formulario abajo."""

    TABLA = ""
    CAMPO_FECHA = "F_Registro"

    def __init__(self, repo: Repositorio, id_usuario: str, titulo: str, padre=None):
        super().__init__(padre)
        self.repo = repo
        self.id_usuario = id_usuario
        self.seleccionado: str | None = None
        usuario = repo.obtener("T_USUARIOS", id_usuario) or {}
        self.nombre_usuario = " ".join(
            x for x in (usuario.get("Nombre"), usuario.get("Apellidos")) if x)
        self.setWindowTitle(f"{titulo} — {self.nombre_usuario}")
        self.setMinimumWidth(700)

    def _montar(self, cabeceras: list[str], formulario: QWidget) -> None:
        raiz = QVBoxLayout(self)
        raiz.addWidget(etiqueta(self.windowTitle().split(" — ")[0], "titulo"))
        raiz.addWidget(etiqueta(self.nombre_usuario, "subtitulo"))

        self.tabla = _tabla(cabeceras)
        self.tabla.itemSelectionChanged.connect(self._cambio_seleccion)
        raiz.addWidget(etiqueta("Histórico"))
        raiz.addWidget(self.tabla)

        fila_botones = QHBoxLayout()
        self.btn_nuevo = QPushButton("Nuevo registro")
        self.btn_nuevo.setProperty("plano", True)
        self.btn_nuevo.clicked.connect(self._nuevo)
        self.btn_borrar = QPushButton("Borrar el seleccionado")
        self.btn_borrar.setProperty("plano", True)
        self.btn_borrar.clicked.connect(self._borrar)
        fila_botones.addWidget(self.btn_nuevo)
        fila_botones.addWidget(self.btn_borrar)
        fila_botones.addStretch()
        raiz.addLayout(fila_botones)

        raiz.addWidget(formulario)

        pie = QHBoxLayout()
        pie.addStretch()
        guardar = QPushButton("Guardar registro")
        guardar.clicked.connect(self._guardar)
        cerrar = QPushButton("Cerrar")
        cerrar.setProperty("plano", True)
        cerrar.clicked.connect(self.accept)
        pie.addWidget(guardar)
        pie.addWidget(cerrar)
        raiz.addLayout(pie)
        self._refrescar()
        # Al abrir se muestra el registro vigente, no un formulario en blanco:
        # lo primero que quiere ver el entrenador es qué hay, no qué falta.
        if self.tabla.rowCount():
            self.tabla.selectRow(0)

    # -- histórico --
    def _registros(self) -> list[dict]:
        return self.repo.listar(
            self.TABLA, lambda f: f.get("ID_Usuario") == self.id_usuario,
            orden=self.CAMPO_FECHA, descendente=True)

    def _refrescar(self, seleccionar: str | None = None) -> None:
        registros = self._registros()
        clave = buscar_tabla(self.TABLA).clave
        self.tabla.blockSignals(True)
        self.tabla.setRowCount(len(registros))
        for fila, registro in enumerate(registros):
            for columna, texto in enumerate(self._fila(registro)):
                item = QTableWidgetItem(texto)
                item.setData(Qt.UserRole, registro)
                self.tabla.setItem(fila, columna, item)
        self.tabla.blockSignals(False)
        if seleccionar:
            # Tras guardar, dejar seleccionado el registro recién escrito: que el
            # formulario se vacíe de golpe parece que se ha perdido lo tecleado.
            for fila, registro in enumerate(registros):
                if registro.get(clave) == seleccionar:
                    self.tabla.selectRow(fila)
                    return
        self.tabla.clearSelection()
        self.seleccionado = None
        self._nuevo()

    def _cambio_seleccion(self) -> None:
        filas = self.tabla.selectionModel().selectedRows()
        if not filas:
            return
        registro = self.tabla.item(filas[0].row(), 0).data(Qt.UserRole)
        self.seleccionado = registro.get(buscar_tabla(self.TABLA).clave)
        self._cargar(registro)

    def _nuevo(self) -> None:
        self.tabla.clearSelection()
        self.seleccionado = None
        self._cargar({})

    def _borrar(self) -> None:
        if not self.seleccionado:
            return
        if not confirmar(self, "Borrar registro",
                         "¿Seguro que quieres borrar este registro del histórico?"):
            return
        try:
            self.repo.borrar(self.TABLA, self.seleccionado)
        except Exception as error:
            avisar_error(self, "No se ha podido borrar", error)
            return
        self._refrescar()

    def _guardar(self) -> None:
        datos = self._recoger()
        datos["ID_Usuario"] = self.id_usuario
        try:
            if self.seleccionado:
                self.repo.actualizar(self.TABLA, self.seleccionado, datos)
                guardado = self.seleccionado
            else:
                guardado = self.repo.insertar(self.TABLA, datos)
        except Exception as error:
            avisar_error(self, "No se ha podido guardar", error)
            return
        self._refrescar(seleccionar=guardado)

    # -- a implementar por cada ventana --
    def _fila(self, registro: dict) -> list[str]:
        raise NotImplementedError

    def _cargar(self, registro: dict) -> None:
        raise NotImplementedError

    def _recoger(self) -> dict:
        raise NotImplementedError


class DialogoObjetivos(_DialogoHistorico):
    TABLA = "T_OBJETIVOS"

    def __init__(self, repo, id_usuario, padre=None):
        super().__init__(repo, id_usuario, "Objetivos", padre)
        caja = QGroupBox("Objetivo")
        form = QFormLayout(caja)
        self.fecha = campo_fecha(date.today())
        self.tipo = desplegable(TIPOS_OBJETIVO, vacio=True)
        self.descripcion = QPlainTextEdit()
        self.descripcion.setMaximumHeight(60)
        self.descripcion.setPlaceholderText(
            "Con sus palabras: es el texto que se le citará en el cuestionario de renovación")
        self.prioridad = QSpinBox(); self.prioridad.setRange(1, 3); self.prioridad.setValue(1)
        self.horizonte = QSpinBox(); self.horizonte.setRange(0, 104); self.horizonte.setSuffix(" semanas")
        self.metrica = QLineEdit(); self.metrica.setPlaceholderText("peso, 1RM sentadilla, perímetro de cintura...")
        self.valor = QLineEdit(); self.valor.setPlaceholderText("valor a alcanzar")
        self.estado = desplegable(ESTADOS_OBJETIVO, "ACTIVO")
        form.addRow("Fecha *", self.fecha)
        form.addRow("Tipo *", self.tipo)
        form.addRow("Descripción *", self.descripcion)
        form.addRow("Prioridad", self.prioridad)
        form.addRow("Horizonte", self.horizonte)
        form.addRow("Métrica", self.metrica)
        form.addRow("Valor objetivo", self.valor)
        form.addRow("Estado *", self.estado)
        self._montar(["Fecha", "Tipo", "Descripción", "Prior.", "Estado"], caja)

    def _fila(self, r):
        tipo = dict(TIPOS_OBJETIVO).get(r.get("Tipo"), r.get("Tipo") or "")
        estado = dict(ESTADOS_OBJETIVO).get(r.get("Estado"), r.get("Estado") or "")
        return [formatear(r.get("F_Registro")), tipo, r.get("Descripcion") or "",
                str(r.get("Prioridad") or ""), estado]

    def _cargar(self, r):
        _poner_fecha(self.fecha, r.get("F_Registro"))
        self.tipo.setCurrentIndex(max(0, self.tipo.findData(r.get("Tipo"))))
        self.descripcion.setPlainText(r.get("Descripcion") or "")
        self.prioridad.setValue(int(r.get("Prioridad") or 1))
        self.horizonte.setValue(int(r.get("Horizonte_Sem") or 0))
        self.metrica.setText(r.get("Metrica") or "")
        self.valor.setText(str(r.get("Valor_Objetivo") or ""))
        self.estado.setCurrentIndex(max(0, self.estado.findData(r.get("Estado") or "ACTIVO")))

    def _recoger(self):
        return {
            "F_Registro": leer_fecha(self.fecha),
            "Tipo": self.tipo.currentData(),
            "Descripcion": self.descripcion.toPlainText().strip(),
            "Prioridad": self.prioridad.value(),
            "Horizonte_Sem": self.horizonte.value() or None,
            "Metrica": self.metrica.text().strip(),
            "Valor_Objetivo": self.valor.text().strip().replace(",", ".") or None,
            "Estado": self.estado.currentData(),
        }


class DialogoDisponibilidad(_DialogoHistorico):
    TABLA = "T_DISPONIBILIDAD"

    def __init__(self, repo, id_usuario, padre=None):
        super().__init__(repo, id_usuario, "Disponibilidad", padre)
        caja = QGroupBox("Disponibilidad")
        form = QFormLayout(caja)
        self.fecha = campo_fecha(date.today())
        self.dias = QSpinBox(); self.dias.setRange(1, 7); self.dias.setValue(3)
        self.preferidos = QLineEdit(); self.preferidos.setPlaceholderText("L, X, V")
        self.franja = desplegable(FRANJAS, vacio=True)
        self.minutos = QSpinBox(); self.minutos.setRange(15, 180)
        self.minutos.setSingleStep(15); self.minutos.setValue(60); self.minutos.setSuffix(" min")
        self.lugar = desplegable(LUGARES, "GIMNASIO")
        self.material = QPlainTextEdit(); self.material.setMaximumHeight(60)
        self.material.setPlaceholderText(
            "Barra, discos, mancuernas hasta 24 kg, poleas, banco...")
        form.addRow("Fecha *", self.fecha)
        form.addRow("Días por semana *", self.dias)
        form.addRow("Días preferidos", self.preferidos)
        form.addRow("Franja", self.franja)
        form.addRow("Duración de sesión *", self.minutos)
        form.addRow("Lugar", self.lugar)
        form.addRow("Material disponible", self.material)
        form.addRow("", etiqueta(
            "Condiciona la planificación: un plan de 5 días con barra no sirve a "
            "quien entrena 3 días en casa con mancuernas.", "subtitulo", ajustar=True))
        self._montar(["Fecha", "Días", "Preferidos", "Franja", "Sesión", "Lugar"], caja)

    def _fila(self, r):
        return [formatear(r.get("F_Registro")), str(r.get("Dias_Semana") or ""),
                r.get("Dias_Preferidos") or "",
                dict(FRANJAS).get(r.get("Franja"), r.get("Franja") or ""),
                f"{r.get('Min_Sesion') or ''} min",
                dict(LUGARES).get(r.get("Lugar"), r.get("Lugar") or "")]

    def _cargar(self, r):
        _poner_fecha(self.fecha, r.get("F_Registro"))
        self.dias.setValue(int(r.get("Dias_Semana") or 3))
        self.preferidos.setText(r.get("Dias_Preferidos") or "")
        self.franja.setCurrentIndex(max(0, self.franja.findData(r.get("Franja"))))
        self.minutos.setValue(int(r.get("Min_Sesion") or 60))
        self.lugar.setCurrentIndex(max(0, self.lugar.findData(r.get("Lugar") or "GIMNASIO")))
        self.material.setPlainText(r.get("Material_Disponible") or "")

    def _recoger(self):
        return {
            "F_Registro": leer_fecha(self.fecha),
            "Dias_Semana": self.dias.value(),
            "Dias_Preferidos": self.preferidos.text().strip(),
            "Franja": self.franja.currentData(),
            "Min_Sesion": self.minutos.value(),
            "Lugar": self.lugar.currentData(),
            "Material_Disponible": self.material.toPlainText().strip(),
        }


class DialogoSalud(_DialogoHistorico):
    """Cribado PAR-Q+, constantes y antecedentes. Ver docs/11 §1."""

    TABLA = "T_SALUD"

    def __init__(self, repo, id_usuario, padre=None):
        super().__init__(repo, id_usuario, "Salud y cribado", padre)
        self.setMinimumWidth(760)

        contenedor = QWidget()
        vertical = QVBoxLayout(contenedor)
        vertical.setContentsMargins(0, 0, 0, 0)

        cabecera = QFormLayout()
        self.fecha = campo_fecha(date.today())
        cabecera.addRow("Fecha de la revisión *", self.fecha)
        vertical.addLayout(cabecera)

        parq = QGroupBox("PAR-Q+ — marcar las respuestas afirmativas")
        caja_parq = QVBoxLayout(parq)
        self.parq: dict[str, QCheckBox] = {}
        for clave, texto in srv.PARQ.items():
            casilla = QCheckBox(texto)
            casilla.stateChanged.connect(self._evaluar)
            self.parq[clave] = casilla
            caja_parq.addWidget(casilla)
        vertical.addWidget(parq)

        constantes = QGroupBox("Constantes en reposo")
        form_c = QFormLayout(constantes)
        self.sistolica = QSpinBox(); self.sistolica.setRange(0, 260); self.sistolica.setSuffix(" mmHg")
        self.diastolica = QSpinBox(); self.diastolica.setRange(0, 200); self.diastolica.setSuffix(" mmHg")
        self.fc = QSpinBox(); self.fc.setRange(0, 220); self.fc.setSuffix(" lpm")
        for campo in (self.sistolica, self.diastolica, self.fc):
            campo.valueChanged.connect(self._evaluar)
        form_c.addRow("Tensión sistólica", self.sistolica)
        form_c.addRow("Tensión diastólica", self.diastolica)
        form_c.addRow("Frecuencia cardíaca", self.fc)
        vertical.addWidget(constantes)

        self.veredicto = etiqueta("", "correcto", ajustar=True)
        vertical.addWidget(self.veredicto)

        self.requiere_informe = QCheckBox("Requiere informe médico antes de esfuerzo máximo")
        vertical.addWidget(self.requiere_informe)

        antecedentes = QGroupBox("Antecedentes")
        form_a = QFormLayout(antecedentes)
        self.patologias = QPlainTextEdit(); self.patologias.setMaximumHeight(48)
        self.medicacion = QPlainTextEdit(); self.medicacion.setMaximumHeight(48)
        self.lesiones = QPlainTextEdit(); self.lesiones.setMaximumHeight(48)
        self.contraindicaciones = QPlainTextEdit(); self.contraindicaciones.setMaximumHeight(48)
        self.contraindicaciones.setPlaceholderText(
            "Movimientos a evitar. La planificación los respetará como regla dura.")
        form_a.addRow("Patologías", self.patologias)
        form_a.addRow("Medicación", self.medicacion)
        form_a.addRow("Lesiones", self.lesiones)
        form_a.addRow("Contraindicaciones", self.contraindicaciones)
        vertical.addWidget(antecedentes)

        self._montar(["Fecha", "PAR-Q+", "Tensión", "FC", "Informe médico"], contenedor)

    def _evaluar(self) -> None:
        cribado = srv.evaluar_cribado(self._recoger())
        if cribado.apto:
            self.veredicto.setObjectName("correcto")
            self.veredicto.setText(
                "Apto para actividad física progresiva. Sin hallazgos en el cribado.")
        else:
            self.veredicto.setObjectName("alerta" if cribado.requiere_informe else "aviso")
            cabecera = ("Requiere informe médico antes de pruebas de esfuerzo máximo."
                        if cribado.requiere_informe
                        else "Hay hallazgos que condicionan la valoración.")
            self.veredicto.setText(cabecera + "\n• " + "\n• ".join(cribado.motivos))
            if cribado.requiere_informe:
                self.requiere_informe.setChecked(True)
        # Releer la hoja de estilos para que el cambio de objectName se aplique
        self.veredicto.style().unpolish(self.veredicto)
        self.veredicto.style().polish(self.veredicto)

    def _fila(self, r):
        positivas = sum(1 for clave in srv.PARQ if r.get(clave))
        ta = (f"{r.get('TA_Sistolica')}/{r.get('TA_Diastolica')}"
              if r.get("TA_Sistolica") else "")
        return [formatear(r.get("F_Registro")),
                f"{positivas} afirmativas" if positivas else "todo no",
                ta, str(r.get("FC_Reposo") or ""),
                "SÍ" if r.get("Requiere_Informe_Medico_SN") else ""]

    def _cargar(self, r):
        _poner_fecha(self.fecha, r.get("F_Registro"))
        for clave, casilla in self.parq.items():
            casilla.blockSignals(True)
            casilla.setChecked(bool(r.get(clave)))
            casilla.blockSignals(False)
        self.sistolica.setValue(int(r.get("TA_Sistolica") or 0))
        self.diastolica.setValue(int(r.get("TA_Diastolica") or 0))
        self.fc.setValue(int(r.get("FC_Reposo") or 0))
        self.requiere_informe.setChecked(bool(r.get("Requiere_Informe_Medico_SN")))
        self.patologias.setPlainText(r.get("Patologias") or "")
        self.medicacion.setPlainText(r.get("Medicacion") or "")
        self.lesiones.setPlainText(r.get("Lesiones_Historial") or "")
        self.contraindicaciones.setPlainText(r.get("Contraindicaciones") or "")
        self._evaluar()

    def _recoger(self):
        datos = {
            "F_Registro": leer_fecha(self.fecha),
            "TA_Sistolica": self.sistolica.value() or None,
            "TA_Diastolica": self.diastolica.value() or None,
            "FC_Reposo": self.fc.value() or None,
            "Requiere_Informe_Medico_SN": self.requiere_informe.isChecked(),
            "Patologias": self.patologias.toPlainText().strip(),
            "Medicacion": self.medicacion.toPlainText().strip(),
            "Lesiones_Historial": self.lesiones.toPlainText().strip(),
            "Contraindicaciones": self.contraindicaciones.toPlainText().strip(),
        }
        for clave, casilla in self.parq.items():
            datos[clave] = casilla.isChecked()
        datos["Apto_SN"] = not any(datos[c] for c in srv.PARQ)
        return datos
