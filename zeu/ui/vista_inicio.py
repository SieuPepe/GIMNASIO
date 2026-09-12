"""Panel de inicio: el estado de la cartera de un vistazo."""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget

from ..datos.repositorio import Repositorio
from ..servicios import usuarios as srv
from . import estilo
from .comunes import etiqueta


def _tarjeta(numero: str, texto: str, color: str) -> QFrame:
    marco = QFrame()
    marco.setStyleSheet(
        f"QFrame {{ background: white; border: 1px solid #DCE3E8;"
        f" border-top: 3px solid {color}; border-radius: 4px; }}")
    caja = QVBoxLayout(marco)
    caja.setContentsMargins(16, 12, 16, 12)
    grande = QLabel(numero)
    grande.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {color}; border: none;")
    pequeno = QLabel(texto)
    pequeno.setStyleSheet("color: #6C7A85; border: none;")
    pequeno.setWordWrap(True)
    caja.addWidget(grande)
    caja.addWidget(pequeno)
    return marco


class VistaInicio(QWidget):
    def __init__(self, repo: Repositorio, padre=None):
        super().__init__(padre)
        self.repo = repo
        self.raiz = QVBoxLayout(self)
        self.raiz.setContentsMargins(24, 20, 24, 20)
        self.raiz.addWidget(etiqueta("Panel de inicio", "titulo"))
        self.subtitulo = etiqueta("", "subtitulo")
        self.raiz.addWidget(self.subtitulo)
        self.rejilla = QGridLayout()
        self.rejilla.setSpacing(12)
        self.raiz.addLayout(self.rejilla)
        self.pendientes = etiqueta("", "aviso", ajustar=True)
        self.raiz.addWidget(self.pendientes)
        self.proximo = etiqueta("", "subtitulo", ajustar=True)
        self.raiz.addWidget(self.proximo)
        self.raiz.addStretch()
        self.refrescar()

    def refrescar(self) -> None:
        usuarios = self.repo.listar("T_USUARIOS")
        activos = [u for u in usuarios if u.get("Estado") == "ACTIVO"]
        sin_consentimiento = [u for u in activos if not u.get("Consentimiento_SN")]
        sin_cribado = [u for u in activos if srv.salud_vigente(self.repo, u["ID_Usuario"]) is None]
        requieren_informe = [
            u for u in activos
            if (s := srv.salud_vigente(self.repo, u["ID_Usuario"]))
            and srv.evaluar_cribado(s).requiere_informe
        ]

        while self.rejilla.count():
            elemento = self.rejilla.takeAt(0)
            anterior = elemento.widget()
            if anterior is not None:
                # setParent(None) lo quita de la vista ya; con deleteLater() solo
                # se destruye al volver al bucle de eventos y se queda pintado.
                anterior.setParent(None)
                anterior.deleteLater()
        ejercicios = [e for e in self.repo.listar("T_EJERCICIOS") if e.get("Activo_SN")]
        tarjetas = [
            (str(len(activos)), "usuarios activos", estilo.AZUL),
            (str(len(ejercicios)), "ejercicios en el catálogo",
             estilo.AZUL if ejercicios else estilo.BAJO),
            (str(len(sin_consentimiento)), "sin consentimiento registrado",
             estilo.BAJO if sin_consentimiento else estilo.BUENO),
            (str(len(sin_cribado)), "sin cribado de salud",
             estilo.BAJO if sin_cribado else estilo.BUENO),
            (str(len(requieren_informe)), "requieren informe médico",
             estilo.ALERTA if requieren_informe else estilo.BUENO),
        ]
        for columna, (numero, texto, color) in enumerate(tarjetas):
            self.rejilla.addWidget(_tarjeta(numero, texto, color), 0, columna)

        self.subtitulo.setText(
            f"{len(usuarios)} usuarios en total, {len(activos)} activos")

        lineas: list[str] = []
        if sin_consentimiento:
            lineas.append("Sin consentimiento: " + ", ".join(
                f"{u.get('Nombre')} {u.get('Apellidos') or ''}".strip()
                for u in sin_consentimiento[:6]) +
                (" …" if len(sin_consentimiento) > 6 else ""))
        if requieren_informe:
            lineas.append("Requieren informe médico antes de esfuerzo máximo: " + ", ".join(
                f"{u.get('Nombre')} {u.get('Apellidos') or ''}".strip()
                for u in requieren_informe[:6]))
        if not ejercicios:
            lineas.append("El catálogo de ejercicios está vacío: impórtalo desde "
                          "«Ejercicios → Importar desde CSV…» antes de crear programas.")
        self.pendientes.setText("\n".join(lineas) if lineas else "")
        self.pendientes.setVisible(bool(lineas))

        self.proximo.setText(
            "En construcción: el panel se completará con los programas que vencen en "
            "menos de 14 días, las valoraciones caducadas y los correos pendientes de "
            "revisar, según vayan entrando las fases 3 a 6.")
