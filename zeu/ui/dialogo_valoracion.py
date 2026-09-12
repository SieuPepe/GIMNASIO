"""Realización de una valoración física siguiendo un protocolo."""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFrame,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton,
    QScrollArea, QVBoxLayout, QWidget,
)

from ..datos.repositorio import Repositorio
from ..nucleo.fechas import edad as calcular_edad
from ..servicios import usuarios as srv_usuarios
from ..servicios import valoracion as srv
from . import estilo
from .comunes import avisar_error, campo_fecha, desplegable, etiqueta, leer_fecha

VACIO = -1000.0   # valor centinela de los campos numéricos sin rellenar

ETIQUETA_CAPACIDAD = {
    "COMPOSICION": "Composición corporal", "FUERZA": "Fuerza",
    "CONTROL_MOTOR": "Control motor", "POTENCIA": "Potencia",
    "RESISTENCIA": "Resistencia cardiorrespiratoria", "MOVILIDAD": "Movilidad",
    "EQUILIBRIO": "Equilibrio",
}
ORDEN_CAPACIDAD = ["COMPOSICION", "FUERZA", "CONTROL_MOTOR", "POTENCIA",
                   "RESISTENCIA", "MOVILIDAD", "EQUILIBRIO"]
COLOR_PUNTOS = [(85, estilo.BUENO), (60, estilo.MEDIO), (0, estilo.BAJO)]


def color_de(puntos: int | None) -> str:
    if puntos is None:
        return "#6C7A85"
    for umbral, color in COLOR_PUNTOS:
        if puntos >= umbral:
            return color
    return estilo.BAJO


class DialogoCriterios(QDialog):
    """Compensaciones observadas en una prueba técnica."""

    def __init__(self, repo: Repositorio, id_test: str, marcados: set[str], padre=None):
        super().__init__(padre)
        prueba = repo.obtener("T_CAT_TESTS", id_test) or {}
        self.setWindowTitle(f"Compensaciones — {prueba.get('Nombre')}")
        self.setMinimumWidth(460)
        raiz = QVBoxLayout(self)
        raiz.addWidget(etiqueta("Marca lo que has observado", "titulo"))
        raiz.addWidget(etiqueta(prueba.get("Protocolo") or "", "subtitulo", ajustar=True))

        self.casillas: dict[str, QCheckBox] = {}
        criterios = repo.listar("T_TEST_CRITERIOS",
                                lambda c: c.get("ID_Test") == id_test, orden="Orden")
        for criterio in criterios:
            casilla = QCheckBox(criterio.get("Descripcion"))
            if criterio.get("Es_Dolor_SN"):
                casilla.setStyleSheet(f"color: {estilo.ALERTA}; font-weight: bold;")
                casilla.setToolTip("Marcarlo fuerza la puntuación 0 y bloquea el patrón")
            casilla.setChecked(criterio["ID_Criterio"] in marcados)
            self.casillas[criterio["ID_Criterio"]] = casilla
            raiz.addWidget(casilla)

        botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        raiz.addWidget(botones)

    def marcados(self) -> set[str]:
        return {clave for clave, casilla in self.casillas.items() if casilla.isChecked()}


class FilaPrueba(QWidget):
    """Una prueba dentro del formulario: entrada(s) y su categoría en vivo."""

    def __init__(self, repo: Repositorio, prueba: dict, obligatoria: bool, al_cambiar):
        super().__init__()
        self.repo = repo
        self.prueba = prueba
        self.obligatoria = obligatoria
        self.al_cambiar = al_cambiar
        self.criterios: dict[str, set[str]] = {}
        self.entradas: dict[str, QWidget] = {}

        caja = QHBoxLayout(self)
        caja.setContentsMargins(0, 2, 0, 2)

        nombre = prueba.get("Nombre") + ("  *" if obligatoria else "")
        titulo = QLabel(nombre)
        titulo.setMinimumWidth(260)
        titulo.setWordWrap(True)
        titulo.setToolTip(prueba.get("Protocolo") or "")
        caja.addWidget(titulo, 3)

        lados = (["DERECHO", "IZQUIERDO"] if prueba.get("Bilateral_SN") else ["NA"])
        for lado in lados:
            if lado != "NA":
                caja.addWidget(QLabel("Dcho" if lado == "DERECHO" else "Izdo"))
            caja.addWidget(self._crear_entrada(lado), 1)

        if prueba.get("Tipo_Medida") in ("TECNICA", "MIXTA"):
            for lado in lados:
                boton = QPushButton("Compensaciones…")
                boton.setProperty("plano", True)
                boton.clicked.connect(lambda _=False, l=lado: self._abrir_criterios(l))
                caja.addWidget(boton)

        unidad = QLabel(prueba.get("Unidad") or "")
        unidad.setMinimumWidth(60)
        caja.addWidget(unidad)

        self.categoria = QLabel("")
        self.categoria.setMinimumWidth(150)
        caja.addWidget(self.categoria, 1)

    def _crear_entrada(self, lado: str) -> QWidget:
        tipo = self.prueba.get("Tipo_Medida")
        if tipo == "TECNICA":
            combo = QComboBox()
            combo.addItem("—", None)
            for valor, texto in srv.TECNICA.items():
                combo.addItem(f"{valor} · {texto[:34]}", valor)
            combo.currentIndexChanged.connect(self.al_cambiar)
            combo.setMinimumWidth(240)
            self.entradas[f"tec_{lado}"] = combo
            return combo

        campo = QDoubleSpinBox()
        campo.setDecimals(int(self.prueba.get("Decimales") or 0))
        campo.setRange(VACIO, 99999)
        campo.setValue(VACIO)
        campo.setSpecialValueText("—")
        campo.setMinimumWidth(110)
        if self.prueba.get("Calculada_SN"):
            campo.setReadOnly(True)
            campo.setButtonSymbols(QDoubleSpinBox.NoButtons)
            campo.setStyleSheet("background: #F2F5F7; color: #4A7FA5;")
            campo.setToolTip("Se calcula a partir de otras pruebas")
        else:
            campo.valueChanged.connect(self.al_cambiar)
        self.entradas[f"val_{lado}"] = campo

        if self.prueba.get("Tipo_Medida") == "MIXTA":
            combo = QComboBox()
            combo.addItem("técnica —", None)
            for valor in srv.TECNICA:
                combo.addItem(f"técnica {valor}", valor)
            combo.currentIndexChanged.connect(self.al_cambiar)
            self.entradas[f"tec_{lado}"] = combo
            contenedor = QWidget()
            fila = QHBoxLayout(contenedor)
            fila.setContentsMargins(0, 0, 0, 0)
            fila.addWidget(campo)
            fila.addWidget(combo)
            return contenedor
        return campo

    def _abrir_criterios(self, lado: str) -> None:
        dialogo = DialogoCriterios(self.repo, self.prueba["ID_Test"],
                                   self.criterios.get(lado, set()), self)
        if not dialogo.exec():
            return
        self.criterios[lado] = dialogo.marcados()
        dolorosos = {
            c["ID_Criterio"] for c in self.repo.listar(
                "T_TEST_CRITERIOS", lambda x: x.get("ID_Test") == self.prueba["ID_Test"])
            if c.get("Es_Dolor_SN")}
        if self.criterios[lado] & dolorosos:
            combo = self.entradas.get(f"tec_{lado}")
            if combo:
                combo.setCurrentIndex(combo.findData(0))
        self.al_cambiar()

    # -- lectura y escritura --
    def valor(self, lado: str = "NA") -> float | None:
        campo = self.entradas.get(f"val_{lado}")
        if campo is None:
            return None
        valor = campo.value()
        return None if valor == VACIO else valor

    def tecnica(self, lado: str = "NA") -> int | None:
        combo = self.entradas.get(f"tec_{lado}")
        return combo.currentData() if combo else None

    def poner_valor(self, valor: float | None, lado: str = "NA") -> None:
        campo = self.entradas.get(f"val_{lado}")
        if campo is not None:
            campo.setValue(VACIO if valor is None else float(valor))

    def lados(self) -> list[str]:
        return ["DERECHO", "IZQUIERDO"] if self.prueba.get("Bilateral_SN") else ["NA"]

    def vacia(self) -> bool:
        return all(self.valor(l) is None and self.tecnica(l) is None for l in self.lados())

    def mostrar_categoria(self, texto: str, puntos: int | None) -> None:
        self.categoria.setText(texto)
        self.categoria.setStyleSheet(f"color: {color_de(puntos)}; font-weight: bold;")


class DialogoValoracion(QDialog):
    def __init__(self, repo: Repositorio, id_usuario: str | None = None,
                 id_valoracion: str | None = None, padre=None):
        super().__init__(padre)
        self.repo = repo
        self.id_valoracion = id_valoracion
        self.filas: dict[str, FilaPrueba] = {}
        self.existente = repo.obtener("T_VALORACIONES", id_valoracion) if id_valoracion else {}
        self.id_usuario = id_usuario or (self.existente or {}).get("ID_Usuario")
        self.setWindowTitle("Valoración física")
        self.resize(1020, 760)
        self._construir()

    # -- construcción --
    def _construir(self) -> None:
        raiz = QVBoxLayout(self)
        usuario = self.repo.obtener("T_USUARIOS", self.id_usuario) or {}
        nombre = " ".join(x for x in (usuario.get("Nombre"), usuario.get("Apellidos")) if x)
        self.edad = (calcular_edad(usuario["F_Nacimiento"])
                     if usuario.get("F_Nacimiento") else None)
        self.sexo = usuario.get("Sexo")

        raiz.addWidget(etiqueta("Valoración física", "titulo"))
        raiz.addWidget(etiqueta(
            f"{nombre} · {self.edad} años · "
            f"{'Hombre' if self.sexo == 'H' else 'Mujer'}", "subtitulo"))

        cabecera = QHBoxLayout()
        self.fecha = campo_fecha((self.existente or {}).get("Fecha") or date.today())
        self.tipo = desplegable(
            [("INICIAL", "Inicial"), ("SEGUIMIENTO", "Seguimiento"),
             ("FINAL_CICLO", "Fin de ciclo")], (self.existente or {}).get("Tipo") or "INICIAL")
        self.protocolo = desplegable(
            [(p["ID_Protocolo"], p["Nombre"]) for p in self._protocolos()],
            (self.existente or {}).get("ID_Protocolo"))
        if not self.id_valoracion:
            sugerido = self._protocolo_sugerido()
            if sugerido:
                self.protocolo.setCurrentIndex(self.protocolo.findData(sugerido))
        self.protocolo.currentIndexChanged.connect(self._cargar_protocolo)
        for texto, campo in (("Fecha", self.fecha), ("Tipo", self.tipo),
                             ("Protocolo", self.protocolo)):
            cabecera.addWidget(etiqueta(texto))
            cabecera.addWidget(campo)
        cabecera.addStretch()
        raiz.addLayout(cabecera)

        self.aviso_cribado = etiqueta("", "alerta", ajustar=True)
        raiz.addWidget(self.aviso_cribado)

        self.contenido = QWidget()
        self.disposicion = QVBoxLayout(self.contenido)
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setWidget(self.contenido)
        area.setFrameShape(QFrame.NoFrame)
        raiz.addWidget(area, 1)

        self.resumen = etiqueta("", "correcto", ajustar=True)
        raiz.addWidget(self.resumen)

        self.observaciones = QPlainTextEdit((self.existente or {}).get("Observaciones") or "")
        self.observaciones.setMaximumHeight(56)
        self.observaciones.setPlaceholderText("Observaciones y conclusión del entrenador")
        raiz.addWidget(self.observaciones)

        botones = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        botones.button(QDialogButtonBox.Save).setText("Guardar valoración")
        botones.button(QDialogButtonBox.Cancel).setText("Cancelar")
        botones.accepted.connect(self._guardar)
        botones.rejected.connect(self.reject)
        raiz.addWidget(botones)

        self._mostrar_cribado()
        self._cargar_protocolo()

    def _protocolos(self) -> list[dict]:
        return self.repo.listar("T_PROTOCOLOS", lambda p: bool(p.get("Activo_SN")),
                                orden="Nombre")

    def _protocolo_sugerido(self) -> str | None:
        """Sugiere por edad y sexo, pero decide el entrenador."""
        for protocolo in self._protocolos():
            if protocolo.get("Sexo") not in ("AMBOS", None, self.sexo):
                continue
            if self.edad is None:
                continue
            if (protocolo.get("Edad_Min") or 0) <= self.edad <= (protocolo.get("Edad_Max") or 120):
                if protocolo.get("ID_Protocolo") != "PRO-RAP":
                    return protocolo["ID_Protocolo"]
        predeterminado = next((p for p in self._protocolos()
                               if p.get("Es_Predeterminado_SN")), None)
        return predeterminado["ID_Protocolo"] if predeterminado else None

    def _mostrar_cribado(self) -> None:
        salud = srv_usuarios.salud_vigente(self.repo, self.id_usuario)
        if not salud:
            self.aviso_cribado.setText(
                "Este usuario no tiene cribado de salud. Conviene hacerlo antes de "
                "cualquier prueba de esfuerzo.")
            self.bloqueo_maximo = True
            return
        cribado = srv_usuarios.evaluar_cribado(salud)
        self.bloqueo_maximo = cribado.bloquea_esfuerzo_maximo
        if cribado.bloquea_esfuerzo_maximo:
            self.aviso_cribado.setText(
                "El cribado bloquea las pruebas de esfuerzo máximo: " +
                "; ".join(cribado.motivos) +
                ". Esas pruebas aparecen desactivadas.")
        else:
            self.aviso_cribado.setVisible(False)

    def _cargar_protocolo(self) -> None:
        while self.disposicion.count():
            elemento = self.disposicion.takeAt(0)
            if elemento.widget():
                elemento.widget().setParent(None)
                elemento.widget().deleteLater()
        self.filas = {}

        id_protocolo = self.protocolo.currentData()
        lineas = self.repo.listar("T_PROTOCOLO_DET",
                                  lambda l: l.get("ID_Protocolo") == id_protocolo,
                                  orden="Orden")
        por_capacidad: dict[str, list[tuple[dict, bool]]] = {}
        for linea in lineas:
            prueba = self.repo.obtener("T_CAT_TESTS", linea.get("ID_Test"))
            if not prueba or not prueba.get("Activo_SN"):
                continue
            por_capacidad.setdefault(prueba["Capacidad"], []).append(
                (prueba, bool(linea.get("Obligatorio_SN"))))

        for capacidad in ORDEN_CAPACIDAD:
            if capacidad not in por_capacidad:
                continue
            grupo = QGroupBox(ETIQUETA_CAPACIDAD.get(capacidad, capacidad))
            caja = QVBoxLayout(grupo)
            for prueba, obligatoria in por_capacidad[capacidad]:
                fila = FilaPrueba(self.repo, prueba, obligatoria, self._recalcular)
                if prueba.get("Requiere_Esfuerzo_Maximo_SN") and self.bloqueo_maximo:
                    fila.setEnabled(False)
                    fila.mostrar_categoria("bloqueada por el cribado", None)
                self.filas[prueba["ID_Test"]] = fila
                caja.addWidget(fila)
            self.disposicion.addWidget(grupo)
        self.disposicion.addStretch()

        if self.id_valoracion:
            self._cargar_valores()
        self._recalcular()

    def _cargar_valores(self) -> None:
        for linea in self.repo.listar(
                "T_VALORACION_DET",
                lambda l: l.get("ID_Valoracion") == self.id_valoracion):
            fila = self.filas.get(linea.get("ID_Test"))
            if not fila:
                continue
            lado = linea.get("Lado") or "NA"
            fila.poner_valor(linea.get("Valor"), lado)
            combo = fila.entradas.get(f"tec_{lado}")
            if combo is not None and linea.get("Valor_Tecnica") is not None:
                combo.setCurrentIndex(combo.findData(int(linea["Valor_Tecnica"])))
        for linea in self.repo.listar(
                "T_VALORACION_CRITERIOS",
                lambda l: l.get("ID_Valoracion") == self.id_valoracion):
            fila = self.filas.get(linea.get("ID_Test"))
            if fila and linea.get("Observado_SN"):
                fila.criterios.setdefault(linea.get("Lado") or "NA", set()).add(
                    linea.get("ID_Criterio"))

    # -- cálculo en vivo --
    def _valores_actuales(self) -> dict[str, float]:
        valores: dict[str, float] = {}
        for id_test, fila in self.filas.items():
            for lado in fila.lados():
                valor = fila.valor(lado)
                if valor is None:
                    continue
                if lado == "NA":
                    valores[id_test] = valor
                else:
                    valores[f"{id_test}_{lado}"] = valor
                    valores.setdefault(id_test, valor)
        return valores

    def _recalcular(self) -> None:
        valores = self._valores_actuales()
        derivadas = srv.derivadas(valores, self.sexo, self.edad)
        for id_test, valor in derivadas.items():
            fila = self.filas.get(id_test)
            if fila:
                fila.poner_valor(valor)
                valores[id_test] = valor

        puntuaciones: list[int] = []
        for id_test, fila in self.filas.items():
            textos = []
            for lado in fila.lados():
                tecnica = fila.tecnica(lado)
                valor = valores.get(id_test if lado == "NA" else f"{id_test}_{lado}")
                bruto = tecnica if tecnica is not None else valor
                if bruto is None:
                    continue
                puntos = srv.buscar_baremo(self.repo, id_test, float(bruto),
                                           self.sexo, self.edad)
                if puntos.hay:
                    puntuaciones.append(puntos.puntos)
                    prefijo = "" if lado == "NA" else ("D: " if lado == "DERECHO" else "I: ")
                    textos.append(f"{prefijo}{puntos.categoria.replace('_', ' ').lower()}")
                elif not self.repo.obtener("T_CAT_TESTS", id_test).get("Tiene_Baremo_SN"):
                    textos.append("sin baremo")
            fila.mostrar_categoria(" · ".join(textos), puntuaciones[-1] if textos and
                                   puntuaciones else None)

        rellenas = [f for f in self.filas.values() if not f.vacia()]
        faltan = [f.prueba["Nombre"] for f in self.filas.values()
                  if f.obligatoria and f.vacia() and f.isEnabled()]
        media = round(sum(puntuaciones) / len(puntuaciones)) if puntuaciones else None
        texto = f"{len(rellenas)} de {len(self.filas)} pruebas registradas"
        if media is not None:
            texto += f" · puntuación media {media}/100"
        if faltan:
            texto += "\nFaltan pruebas obligatorias: " + ", ".join(faltan)
        self.resumen.setObjectName("aviso" if faltan else "correcto")
        self.resumen.setText(texto)
        self.resumen.style().unpolish(self.resumen)
        self.resumen.style().polish(self.resumen)

    # -- guardado --
    def _guardar(self) -> None:
        faltan = [f.prueba["Nombre"] for f in self.filas.values()
                  if f.obligatoria and f.vacia() and f.isEnabled()]
        if faltan:
            avisar_error(self, "Faltan pruebas obligatorias", Exception(
                "El protocolo exige estas pruebas:\n• " + "\n• ".join(faltan)))
            return
        try:
            self._escribir()
        except Exception as error:
            avisar_error(self, "No se ha podido guardar", error)
            return
        self.accept()

    def _escribir(self) -> None:
        cabecera = {
            "ID_Usuario": self.id_usuario,
            "ID_Protocolo": self.protocolo.currentData(),
            "Fecha": leer_fecha(self.fecha),
            "Tipo": self.tipo.currentData(),
            "Bloqueo_Esfuerzo_Maximo_SN": self.bloqueo_maximo,
            "Observaciones": self.observaciones.toPlainText().strip(),
        }
        if self.id_valoracion:
            self.repo.actualizar("T_VALORACIONES", self.id_valoracion, cabecera)
            for tabla in ("T_VALORACION_DET", "T_VALORACION_CRITERIOS", "T_CAPACIDADES"):
                for fila in list(self.repo.listar(
                        tabla, lambda f: f.get("ID_Valoracion") == self.id_valoracion)):
                    clave = fila[list(fila.keys())[0]]
                    self.repo.borrar(tabla, clave, forzar=True)
        else:
            self.id_valoracion = self.repo.insertar("T_VALORACIONES", cabecera)

        valores = self._valores_actuales()
        valores.update(srv.derivadas(valores, self.sexo, self.edad))
        for id_test, fila in self.filas.items():
            prueba = self.repo.obtener("T_CAT_TESTS", id_test) or {}
            for lado in fila.lados():
                clave = id_test if lado == "NA" else f"{id_test}_{lado}"
                valor = valores.get(clave) if not prueba.get("Calculada_SN") else valores.get(id_test)
                tecnica = fila.tecnica(lado)
                if valor is None and tecnica is None:
                    continue
                bruto = tecnica if tecnica is not None else valor
                puntos = srv.buscar_baremo(self.repo, id_test, float(bruto),
                                           self.sexo, self.edad)
                self.repo.insertar("T_VALORACION_DET", {
                    "ID_Valoracion": self.id_valoracion, "ID_Test": id_test,
                    "Lado": lado, "Valor": valor, "Valor_Tecnica": tecnica,
                    "Unidad": prueba.get("Unidad"),
                    "Puntuacion": puntos.puntos, "Categoria": puntos.categoria})
                for criterio in sorted(fila.criterios.get(lado, set())):
                    self.repo.insertar("T_VALORACION_CRITERIOS", {
                        "ID_Valoracion": self.id_valoracion, "ID_Test": id_test,
                        "ID_Criterio": criterio, "Lado": lado, "Observado_SN": True})

        detalle = self.repo.listar("T_VALORACION_DET",
                                   lambda f: f.get("ID_Valoracion") == self.id_valoracion)
        for capacidad, (puntos, cuantas) in srv.capacidades(self.repo, detalle).items():
            self.repo.insertar("T_CAPACIDADES", {
                "ID_Valoracion": self.id_valoracion, "Capacidad": capacidad,
                "Puntuacion": puntos, "N_Pruebas": cuantas})
