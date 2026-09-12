"""Paleta y hoja de estilos de ZEU. Ver docs/12-marca.md"""

from __future__ import annotations

from pathlib import Path

from ..nucleo.config import RAIZ

AZUL = "#4A7FA5"
AZUL_OSCURO = "#356283"
AZUL_CLARO = "#D9E4EC"
GRIS_FONDO = "#E2E2E2"
GRIS_TEXTO = "#333333"
BLANCO = "#FFFFFF"

BUENO = "#5B9279"
MEDIO = "#C9A227"
BAJO = "#C1663F"
ALERTA = "#A33B3B"

LOGO = RAIZ / "assets" / "marca" / "zeu-logo.png"
ISO = RAIZ / "assets" / "marca" / "zeu-iso.png"


def ruta_logo() -> Path | None:
    for candidato in (ISO, LOGO):
        if candidato.exists():
            return candidato
    return None


HOJA = f"""
QWidget {{
    font-family: "Segoe UI", "Noto Sans", sans-serif;
    font-size: 13px;
    color: {GRIS_TEXTO};
}}
QMainWindow, QDialog {{ background: {BLANCO}; }}

#lateral {{ background: {AZUL_OSCURO}; }}
#lateral QPushButton {{
    background: transparent; border: none; color: #DCE7EF;
    text-align: left; padding: 11px 18px; font-size: 14px;
}}
#lateral QPushButton:hover {{ background: {AZUL}; color: white; }}
#lateral QPushButton:checked {{ background: {AZUL}; color: white; font-weight: bold; }}
#marca {{ color: white; font-size: 26px; font-weight: bold; padding: 18px 18px 0 18px; }}
#lema {{ color: #A9C4D6; font-size: 11px; padding: 0 18px 18px 18px; }}

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
