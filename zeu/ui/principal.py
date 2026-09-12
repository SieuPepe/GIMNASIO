"""Ventana principal: navegación lateral y ciclo de guardado."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QButtonGroup, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton,
    QStackedWidget, QVBoxLayout, QWidget,
)

from ..datos.libro import Libro
from ..datos.repositorio import Repositorio
from ..nucleo.config import Config
from . import estilo
from .comunes import avisar_error
from .vista_ejercicios import VistaEjercicios
from .vista_inicio import VistaInicio
from .vista_asignaciones import VistaAsignaciones
from .vista_correo import VistaCorreo
from .vista_programas import VistaProgramas
from .vista_valoraciones import VistaValoraciones
from .vista_usuarios import VistaUsuarios

# Secciones previstas. Las que no tienen vista aún quedan desactivadas, para que
# se vea hacia dónde va la aplicación.
PENDIENTES: list[tuple[str, str]] = []


class VentanaPrincipal(QMainWindow):
    def __init__(self, cfg: Config, libro: Libro):
        super().__init__()
        self.cfg = cfg
        self.libro = libro
        self.repo = Repositorio(libro)
        self.setWindowTitle(f"{cfg.negocio.nombre_comercial} — Gestión de entrenamiento")
        self.resize(1180, 760)
        self._construir()

    def _construir(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        disposicion = QHBoxLayout(central)
        disposicion.setContentsMargins(0, 0, 0, 0)
        disposicion.setSpacing(0)

        lateral = QWidget()
        lateral.setObjectName("lateral")
        lateral.setFixedWidth(235)
        caja = QVBoxLayout(lateral)
        caja.setContentsMargins(0, 0, 0, 0)
        caja.setSpacing(0)

        logo = estilo.ruta_logo()
        if logo:
            imagen = QLabel()
            imagen.setPixmap(QPixmap(str(logo)).scaledToWidth(
                170, Qt.SmoothTransformation))
            imagen.setContentsMargins(18, 18, 18, 8)
            caja.addWidget(imagen)
        else:
            marca = QLabel(self.cfg.negocio.nombre_comercial)
            marca.setObjectName("marca")
            caja.addWidget(marca)
        lema = QLabel(self.cfg.negocio.lema)
        lema.setObjectName("lema")
        caja.addWidget(lema)

        self.paginas = QStackedWidget()
        self.vista_inicio = VistaInicio(self.repo)
        self.vista_usuarios = VistaUsuarios(self.repo, self.guardar)
        self.vista_ejercicios = VistaEjercicios(self.repo, self.guardar)
        self.vista_valoraciones = VistaValoraciones(self.repo, self.cfg, self.guardar)
        self.vista_programas = VistaProgramas(self.repo, self.guardar)
        self.vista_asignaciones = VistaAsignaciones(self.repo, self.cfg, self.guardar)
        self.vista_correo = VistaCorreo(self.repo, self.cfg, self.guardar)
        self.paginas.addWidget(self.vista_inicio)
        self.paginas.addWidget(self.vista_usuarios)
        self.paginas.addWidget(self.vista_ejercicios)
        self.paginas.addWidget(self.vista_valoraciones)
        self.paginas.addWidget(self.vista_programas)
        self.paginas.addWidget(self.vista_asignaciones)
        self.paginas.addWidget(self.vista_correo)

        grupo = QButtonGroup(self)
        grupo.setExclusive(True)
        for indice, texto in enumerate(
                ("Inicio", "Usuarios", "Ejercicios", "Valoraciones",
                 "Programas", "Asignaciones", "Correo")):
            boton = QPushButton(texto)
            boton.setCheckable(True)
            boton.clicked.connect(lambda _=False, i=indice: self._ir(i))
            grupo.addButton(boton)
            caja.addWidget(boton)
            if indice == 0:
                boton.setChecked(True)

        for texto, fase in PENDIENTES:
            boton = QPushButton(f"{texto}   ·  {fase}")
            boton.setEnabled(False)
            caja.addWidget(boton)

        caja.addStretch()
        disposicion.addWidget(lateral)
        disposicion.addWidget(self.paginas, 1)

        self.statusBar().showMessage(f"Libro de datos: {self.libro.ruta}")

    def _ir(self, indice: int) -> None:
        if indice == 0:
            self.vista_inicio.refrescar()
        self.paginas.setCurrentIndex(indice)

    def guardar(self) -> bool:
        """Escribe el libro tras cada cambio. Devuelve si ha ido bien."""
        try:
            self.libro.guardar()
        except Exception as error:
            avisar_error(self, "No se ha podido guardar en el libro", error)
            return False
        self.statusBar().showMessage(f"Guardado en {self.libro.ruta}", 4000)
        self.vista_inicio.refrescar()
        return True
