"""Paleta y hoja de estilos de Kevin Ruiz Valdenegro. Ver docs/12-marca.md"""

from __future__ import annotations

from pathlib import Path

from ..nucleo.config import RAIZ

# Tomados del logotipo: el marino es el del dibujo, y los demás son pasos del
# mismo tono elegidos para que cada uso llegue al contraste que necesita.
AZUL = "#15568F"
AZUL_OSCURO = "#06305A"
AZUL_CLARO = "#D7E3EF"
GRIS_FONDO = "#EEF1F4"
AZUL_MEDIO = "#2E6FA8"
GRIS_TEXTO = "#2B2B2B"
BLANCO = "#FFFFFF"

BUENO = "#5B9279"
MEDIO = "#C9A227"
BAJO = "#C1663F"
ALERTA = "#A33B3B"

MARCA = RAIZ / "assets" / "marca"
LOGO = MARCA / "kevin-logo.png"              # marino, para papel y fondos claros
LOGO_BLANCO = MARCA / "kevin-logo-blanco.png"  # para la barra lateral oscura
ISO = MARCA / "kevin-iso.png"
ICONO = MARCA / "kevin.ico"


def ruta_logo() -> Path | None:
    """El logotipo en su color, para documentos y fondos claros."""
    for candidato in (LOGO, ISO):
        if candidato.exists():
            return candidato
    return None


def ruta_logo_claro() -> Path | None:
    """La versión en blanco: sobre la barra lateral, el marino no se vería."""
    if LOGO_BLANCO.exists():
        return LOGO_BLANCO
    return ruta_logo()


HOJA = f"""
QWidget {{
    font-family: "Segoe UI", "Noto Sans", sans-serif;
    font-size: 13px;
    color: {GRIS_TEXTO};
}}
QMainWindow, QDialog {{ background: {BLANCO}; }}

#lateral {{ background: {AZUL_OSCURO}; }}
#lateral QPushButton {{
    background: transparent; border: none; color: #CBDAE8;
    text-align: left; padding: 11px 18px; font-size: 14px;
}}
#lateral QPushButton:hover {{ background: {AZUL}; color: white; }}
#lateral QPushButton:checked {{ background: {AZUL}; color: white; font-weight: bold; }}
#marca {{ color: white; font-size: 19px; font-weight: bold; padding: 18px 16px 0 16px; }}
#lema {{ color: #9FBBD4; font-size: 11px; padding: 0 18px 18px 18px; }}

#titulo {{ font-size: 21px; font-weight: bold; color: {AZUL_OSCURO}; }}
#subtitulo {{ color: #6C7A85; }}

QPushButton {{
    background: {AZUL}; color: white; border: none;
    padding: 7px 15px; border-radius: 3px;
}}
QPushButton:hover {{ background: {AZUL_OSCURO}; }}
QPushButton:disabled {{ background: #B9C6CE; }}
QPushButton[plano="true"] {{
    background: transparent; color: {AZUL}; border: 1px solid {AZUL};
}}
QPushButton[plano="true"]:hover {{ background: {AZUL_CLARO}; }}

QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit {{
    border: 1px solid #C3CDD4; border-radius: 3px; padding: 5px; background: white;
}}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus,
QTextEdit:focus, QPlainTextEdit:focus {{ border: 1px solid {AZUL}; }}

QTableWidget {{ gridline-color: #E2E8EC; selection-background-color: {AZUL_CLARO};
                selection-color: {GRIS_TEXTO}; }}
QHeaderView::section {{
    background: {AZUL}; color: white; padding: 6px; border: none; font-weight: bold;
}}
QGroupBox {{
    border: 1px solid #D5DDE3; border-radius: 4px; margin-top: 14px; padding-top: 10px;
}}
QGroupBox::title {{
    subcontrol-origin: margin; left: 10px; padding: 0 5px;
    color: {AZUL_OSCURO}; font-weight: bold;
}}
#aviso {{
    background: #FBF3E2; border-left: 4px solid {MEDIO};
    padding: 9px 12px; border-radius: 2px;
}}
#alerta {{
    background: #F8E9E9; border-left: 4px solid {ALERTA};
    padding: 9px 12px; border-radius: 2px;
}}
#correcto {{
    background: #EAF3EE; border-left: 4px solid {BUENO};
    padding: 9px 12px; border-radius: 2px;
}}
"""
