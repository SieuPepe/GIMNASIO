"""Asistente de primera configuración.

Sale solo la primera vez, cuando todavía no hay cuenta de correo configurada.
Pregunta lo único que el programa no puede averiguar por su cuenta —la cuenta
desde la que se escribe y los formularios— y escribe los dos ficheros de
configuración.

Escribe el .env sin marca de orden de bytes y con salto de línea normal: eso ya
no importa para leerlo, pero deja el fichero limpio si alguien lo abre a mano.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout, QLabel, QLineEdit, QMessageBox, QVBoxLayout, QWizard,
    QWizardPage,
)

from ..datos.repositorio import Repositorio
from ..nucleo import config
from ..servicios import correo as srv_correo
from .comunes import etiqueta

# Plantillas que llevan un botón a un formulario de Google, con una ayuda de
# qué formulario es cada una.
FORMULARIOS = (
    ("CONSENTIMIENTO", "Autorización para tratar sus datos y escribirle"),
    ("ENCUESTA_T14", "Satisfacción y renovación, 14 días antes de terminar"),
    ("RECORDATORIO", "Recordatorio de la encuesta anterior"),
    ("CHECKIN_MITAD", "Cómo va la cosa, a mitad del ciclo"),
)


def hace_falta() -> bool:
    """Si todavía no hay cuenta de correo configurada."""
    return not config.credencial("GMAIL_APP_PASSWORD")


def donde_se_busca() -> str:
    """Qué fichero de credenciales se está usando, dicho en una línea.

    Si el asistente vuelve a salir cuando no debería, esto es lo que lo
    explica: o no hay fichero, o está en otro sitio del que se mira.
    """
    actual = config.ruta_env()
    if actual is None:
        return (f"No hay ningún fichero de credenciales en:\n"
                f"{config.CARPETA_DATOS}")
    if config.credencial("GMAIL_APP_PASSWORD"):
        return f"Cuenta ya configurada en {actual}"
    return f"{actual} existe, pero no trae GMAIL_APP_PASSWORD"


class _Bienvenida(QWizardPage):
    """Lo primero que se ve. Deja claro qué es esta ventana.

    Es fácil confundirla con el instalador —sale justo después y se le parece—,
    así que dice quién es, de dónde está corriendo el programa y dónde va a
    guardar. Con eso, si algún día sale cuando no toca, se ve de un vistazo por
    qué.
    """

    def __init__(self, cfg: config.Config):
        super().__init__()
        self.setTitle("Configuración inicial del programa")
        self.setSubTitle(
            "Esto no es el instalador: el programa ya está instalado. Es la "
            "única pregunta que hay que contestar la primera vez.")
        caja = QVBoxLayout(self)
        caja.addWidget(etiqueta(
            "Hay una sola cosa que el programa no puede averiguar solo: la "
            "<b>cuenta de correo</b> desde la que vas a escribir a tus "
            "usuarios. También te preguntará por las direcciones de tus "
            "formularios de Google, aunque eso se puede dejar para después."
            "<br><br>"
            "Todo lo demás ya viene puesto y se puede cambiar cuando quieras.",
            ajustar=True))
        caja.addSpacing(14)
        caja.addWidget(etiqueta(
            f"<b>Por qué sale esta ventana:</b><br>{donde_se_busca()}"
            f"<br><br><b>El programa se está ejecutando desde:</b><br>"
            f"{config.RAIZ}", "subtitulo", ajustar=True))
        caja.addStretch()


class _Correo(QWizardPage):
    """La cuenta de envío y su contraseña de aplicación, probadas de verdad."""

    def __init__(self, cfg: config.Config):
        super().__init__()
        self.cfg = cfg
        self.probado = False
        self.setTitle("La cuenta desde la que escribes")
        self.setSubTitle(
            "Tiene que ser una cuenta de Gmail con verificación en dos pasos "
            "activada, y hace falta una contraseña de aplicación: 16 letras que "
            "se generan en la cuenta de Google, en Seguridad → Contraseñas de "
            "aplicaciones. La contraseña normal de la cuenta no sirve.")

        caja = QVBoxLayout(self)
        formulario = QFormLayout()
        self.cuenta = QLineEdit(cfg.correo.remitente)
        self.cuenta.setPlaceholderText("tucuenta@gmail.com")
        self.clave = QLineEdit()
        self.clave.setEchoMode(QLineEdit.Password)
        self.clave.setPlaceholderText("Las 16 letras de la contraseña de aplicación")
        formulario.addRow("Cuenta de correo", self.cuenta)
        formulario.addRow("Contraseña de aplicación", self.clave)
        caja.addLayout(formulario)

        self.resultado = etiqueta("", ajustar=True)
        caja.addWidget(self.resultado)
        self.pista = etiqueta("", "subtitulo", ajustar=True)
        caja.addWidget(self.pista)
        caja.addStretch()

        # Nada de campos «obligatorios» de Qt: esos se dan por cumplidos solo
        # cuando el texto cambia respecto al que tenían al registrarse, así que
        # un campo que ya viene relleno nunca cuenta como completo y el botón
        # Siguiente se queda apagado para siempre. Aquí se decide a mano, y de
        # paso se puede decir qué falta en vez de dejar el botón muerto.
        self.registerField("cuenta", self.cuenta)
        self.registerField("clave", self.clave)
        for campo in (self.cuenta, self.clave):
            campo.textChanged.connect(self._revisar)
        self._revisar()

    def clave_limpia(self) -> str:
        """Google la enseña en grupos de cuatro; se pega con espacios."""
        return self.clave.text().strip().replace(" ", "")

    def isComplete(self) -> bool:
        return "@" in self.cuenta.text().strip() and len(self.clave_limpia()) >= 8

    def _revisar(self) -> None:
        cuenta = self.cuenta.text().strip()
        clave = self.clave_limpia()
        if "@" not in cuenta:
            self.pista.setText("Falta la cuenta de correo.")
        elif not clave:
            self.pista.setText("Falta la contraseña de aplicación.")
        elif len(clave) < 8:
            self.pista.setText("Esa contraseña es muy corta: la de Google tiene "
                               "16 letras.")
        elif len(clave) != 16:
            self.pista.setText("Aviso: la contraseña de aplicación de Google "
                               f"tiene 16 letras y has escrito {len(clave)}. "
                               "Puedes seguir, pero compruébala.")
        else:
            self.pista.setText("Listo. Conviene pulsar «Probar la conexión» "
                               "antes de seguir.")
        self.completeChanged.emit()

    def probar(self) -> None:
        """Intenta conectar de verdad con lo que se ha escrito."""
        cuenta = self.cuenta.text().strip()
        clave = self.clave_limpia()
        if not cuenta or not clave:
            self.resultado.setText("Escribe la cuenta y la contraseña primero.")
            self.resultado.setObjectName("aviso")
            self._repintar()
            return
        import os
        os.environ["GMAIL_USUARIO"] = cuenta
        os.environ["GMAIL_APP_PASSWORD"] = clave
        self.cfg.correo.remitente = cuenta
        bien, mensaje = srv_correo.probar_conexion(self.cfg)
        self.probado = bien
        self.resultado.setText(mensaje)
        self.resultado.setObjectName("correcto" if bien else "alerta")
        self._repintar()

    def _repintar(self) -> None:
        self.resultado.style().unpolish(self.resultado)
        self.resultado.style().polish(self.resultado)


class _Formularios(QWizardPage):
    """Las URL de los formularios de Google. Se pueden dejar en blanco."""

    def __init__(self, repo: Repositorio | None):
        super().__init__()
        self.repo = repo
        self.setTitle("Tus formularios de Google")
        self.setSubTitle(
            "Pega aquí el enlace de «respuesta prerrellenada» de cada "
            "formulario: en el formulario, menú de tres puntos → «Obtener "
            "enlace prerrellenado». Si todavía no los tienes, déjalo en blanco "
            "y rellénalo luego en Correo → Plantillas de correo.")

        caja = QVBoxLayout(self)
        formulario = QFormLayout()
        self.campos: dict[str, QLineEdit] = {}
        for codigo, descripcion in FORMULARIOS:
            campo = QLineEdit()
            campo.setPlaceholderText("https://docs.google.com/forms/…")
            if repo is not None:
                plantilla = _plantilla(repo, codigo)
                campo.setText((plantilla or {}).get("URL_Form") or "")
            etiqueta_campo = QLabel(f"<b>{codigo.capitalize()}</b><br>"
                                    f"<small>{descripcion}</small>")
            etiqueta_campo.setTextFormat(Qt.RichText)
            formulario.addRow(etiqueta_campo, campo)
            self.campos[codigo] = campo
        caja.addLayout(formulario)
        caja.addStretch()

    def guardar(self) -> int:
        if self.repo is None:
            return 0
        guardadas = 0
        for codigo, campo in self.campos.items():
            url = campo.text().strip()
            plantilla = _plantilla(self.repo, codigo)
            if plantilla is None or not url:
                continue
            self.repo.actualizar("T_PLANTILLAS_MAIL", plantilla["ID_Plantilla"],
                                 {"URL_Form": url})
            guardadas += 1
        return guardadas


class _Negocio(QWizardPage):
    """Los textos que salen en los correos y en los PDF."""

    def __init__(self, cfg: config.Config):
        super().__init__()
        self.setTitle("Tus datos")
        self.setSubTitle("Esto es lo que sale en la cabecera de los correos y "
                         "en el pie de los informes.")
        caja = QVBoxLayout(self)
        formulario = QFormLayout()
        self.nombre = QLineEdit(cfg.negocio.nombre_comercial)
        self.lema = QLineEdit(cfg.negocio.lema)
        self.contacto = QLineEdit(cfg.negocio.contacto)
        self.horario = QLineEdit(cfg.negocio.horario_sala)
        self.horario.setPlaceholderText(
            "Lunes a sábado de 07:00 a 21:00 · Domingo de 07:00 a 14:00")
        formulario.addRow("Nombre comercial", self.nombre)
        formulario.addRow("Lema", self.lema)
        formulario.addRow("Contacto", self.contacto)
        formulario.addRow("Horario de sala", self.horario)
        caja.addLayout(formulario)
        caja.addStretch()


class Asistente(QWizard):
    """Las cuatro preguntas de la primera vez."""

    def __init__(self, cfg: config.Config, repo: Repositorio | None = None,
                 padre=None):
        super().__init__(padre)
        self.cfg = cfg
        self.repo = repo
        self.setWindowTitle(f"{cfg.negocio.nombre_comercial} — primera puesta en marcha")
        self.setWizardStyle(QWizard.ModernStyle)
        self.resize(640, 520)
        self.setButtonText(QWizard.NextButton, "Siguiente")
        self.setButtonText(QWizard.BackButton, "Atrás")
        self.setButtonText(QWizard.FinishButton, "Terminar")
        self.setButtonText(QWizard.CancelButton, "Dejarlo para luego")

        self.pagina_correo = _Correo(cfg)
        self.pagina_formularios = _Formularios(repo)
        self.pagina_negocio = _Negocio(cfg)
        self.addPage(_Bienvenida(cfg))
        self.addPage(self.pagina_correo)
        self.addPage(self.pagina_formularios)
        self.addPage(self.pagina_negocio)

        self.setOption(QWizard.HaveCustomButton1, True)
        self.setButtonText(QWizard.CustomButton1, "Probar la conexión")
        # Conectado al botón y no a customButtonClicked: esa señal entrega un
        # número entero y en PySide6 un entero no es igual a la constante del
        # botón, así que la comparación fallaba en silencio y el botón no hacía
        # nada.
        self.button(QWizard.CustomButton1).clicked.connect(self.pagina_correo.probar)
        self.currentIdChanged.connect(self._cambio_pagina)

    def _cambio_pagina(self, _=None) -> None:
        # El botón de probar solo tiene sentido en la página del correo.
        self.button(QWizard.CustomButton1).setVisible(
            self.currentPage() is self.pagina_correo)

    def accept(self) -> None:
        """Escribe los dos ficheros y guarda las URL en el libro."""
        try:
            ruta_env = escribir_env(self.pagina_correo.cuenta.text().strip(),
                                    self.pagina_correo.clave_limpia())
            escribir_config(self.cfg, self.pagina_correo.cuenta.text().strip(),
                            self.pagina_negocio.nombre.text().strip(),
                            self.pagina_negocio.lema.text().strip(),
                            self.pagina_negocio.contacto.text().strip(),
                            self.pagina_negocio.horario.text().strip())
            formularios = self.pagina_formularios.guardar()
        except Exception as error:
            QMessageBox.critical(self, "No se ha podido guardar", str(error))
            return

        # Comprobar que lo escrito se vuelve a encontrar. Decir «todo listo» y
        # que al siguiente arranque vuelva a salir esta ventana es lo peor que
        # puede hacer un asistente.
        config.releer_credenciales()
        if not config.credencial("GMAIL_APP_PASSWORD"):
            QMessageBox.critical(
                self, "Se ha guardado, pero no se vuelve a leer",
                f"He escrito el fichero en:\n{ruta_env}\n\n"
                "Pero al releerlo no encuentro la contraseña, así que esta "
                "ventana volvería a salir al abrir el programa.\n\n"
                "Suele ser que algo impida escribir en esa carpeta: el "
                "antivirus, o el «acceso controlado a carpetas» de Windows. "
                "Cuéntamelo con esta ruta delante.")
            return

        aviso = ""
        if not self.pagina_correo.probado:
            aviso = ("\n\nNo has llegado a probar la conexión. Si luego no sale "
                     "ningún correo, empieza por Correo → «Probar la conexión».")
        QMessageBox.information(
            self, "Todo listo",
            f"Cuenta guardada en:\n{ruta_env}\n\n"
            f"{formularios} formularios anotados.{aviso}\n\n"
            "Esta ventana ya no volverá a salir.")
        super().accept()


# ------------------------------------------------------------------- escritura

def escribir_env(cuenta: str, clave: str, ruta: Path | None = None) -> Path:
    """Guarda las credenciales. Sin marca de orden de bytes, en UTF-8 limpio."""
    ruta = ruta or config.asegurar_carpeta_datos() / ".env"
    contenido = (f"GMAIL_USUARIO={cuenta}\n"
                 f"GMAIL_APP_PASSWORD={clave}\n")
    ruta.write_text(contenido, encoding="utf-8", newline="\n")
    return ruta


def escribir_config(cfg: config.Config, remitente: str, nombre: str, lema: str,
                    contacto: str, horario: str,
                    ruta: Path | None = None) -> Path:
    """Reescribe config.toml con lo contestado, conservando lo demás.

    Se parte de config.ejemplo.toml para no perder los comentarios que explican
    cada apartado: el fichero lo va a leer una persona, no solo el programa.
    """
    ruta = ruta or config.asegurar_carpeta_datos() / "config.toml"
    modelo = config.RAIZ / "config.ejemplo.toml"
    if ruta.exists():
        texto = config._leer_texto(ruta)
    elif modelo.exists():
        texto = config._leer_texto(modelo)
    else:
        texto = ("[negocio]\n\n[datos]\n\n[correo]\n")

    cambios = {"nombre_comercial": nombre, "lema": lema, "contacto": contacto,
               "horario_sala": horario, "remitente": remitente}
    lineas = texto.splitlines()
    pendientes = dict(cambios)
    for indice, linea in enumerate(lineas):
        clave = linea.split("=", 1)[0].strip()
        if clave in pendientes:
            lineas[indice] = f'{clave:<16} = "{pendientes.pop(clave)}"'
    # Lo que no estuviera en el fichero se añade a su sección.
    for clave, valor in pendientes.items():
        seccion = "[correo]" if clave == "remitente" else "[negocio]"
        if seccion in lineas:
            lineas.insert(lineas.index(seccion) + 1, f'{clave:<16} = "{valor}"')
        else:
            lineas += [seccion, f'{clave:<16} = "{valor}"']

    ruta.write_text("\n".join(lineas) + "\n", encoding="utf-8", newline="\n")
    # Que lo escrito quede en memoria sin tener que rearrancar.
    cfg.negocio.nombre_comercial = nombre
    cfg.negocio.lema = lema
    cfg.negocio.contacto = contacto
    cfg.negocio.horario_sala = horario
    cfg.correo.remitente = remitente
    cfg.ruta_config = ruta
    return ruta


def _plantilla(repo: Repositorio, codigo: str) -> dict | None:
    for plantilla in repo.listar("T_PLANTILLAS_MAIL"):
        if plantilla.get("Codigo") == codigo:
            return plantilla
    return None
