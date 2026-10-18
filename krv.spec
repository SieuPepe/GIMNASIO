# -*- mode: python ; coding: utf-8 -*-
"""Empaquetado con PyInstaller.

    pyinstaller krv.spec --noconfirm

Sale una carpeta `dist/KevinRuizValdenegro` con el ejecutable y todo lo que
necesita. Se empaqueta en carpeta y no en un solo fichero a propósito: arranca
mucho más rápido, el antivirus se queja bastante menos y actualizar es
reemplazar ficheros.

Lo que viaja dentro son solo los recursos de lectura —logotipos, datos
iniciales y la plantilla de configuración—. Los datos del usuario viven en su
carpeta de Documentos; ver krv/nucleo/config.py.
"""

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

RAIZ = Path(SPECPATH)
ICONO = RAIZ / "assets" / "marca" / "kevin.ico"

recursos = [
    (str(RAIZ / "datos_iniciales"), "datos_iniciales"),
    (str(RAIZ / "assets" / "marca"), "assets/marca"),
    (str(RAIZ / "config.ejemplo.toml"), "."),
    (str(RAIZ / ".env.ejemplo"), "."),
]

# openpyxl y reportlab cargan cosas por nombre, así que el análisis automático
# no siempre las ve.
ocultos = (collect_submodules("openpyxl")
           + collect_submodules("reportlab.graphics.barcode")
           + ["PySide6.QtPrintSupport"])

# Lo que no se usa y pesa: fuera. Sin esto el paquete se va a más del doble.
sobra = [
    "tkinter", "unittest", "pydoc", "doctest", "pdb",
    "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtQuick",
    "PySide6.QtQml", "PySide6.Qt3DCore", "PySide6.QtMultimedia",
    "PySide6.QtNetworkAuth", "PySide6.QtCharts", "PySide6.QtDataVisualization",
    "PySide6.QtBluetooth", "PySide6.QtPositioning", "PySide6.QtSensors",
    "PySide6.QtSerialPort", "PySide6.QtTest", "PySide6.QtDesigner",
    "scipy", "pandas", "IPython", "pytest",
]

analisis = Analysis(
    [str(RAIZ / "arrancar.py")],
    pathex=[str(RAIZ)],
    binaries=[],
    datas=recursos,
    hiddenimports=ocultos,
    hookspath=[],
    runtime_hooks=[],
    excludes=sobra,
    noarchive=False,
)

pyz = PYZ(analisis.pure)

exe = EXE(
    pyz,
    analisis.scripts,
    [],
    exclude_binaries=True,
    name="KevinRuizValdenegro",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    # Sin consola: es una aplicación de ventanas, no un programa de terminal.
    console=False,
    icon=str(ICONO) if ICONO.exists() else None,
)

coleccion = COLLECT(
    exe,
    analisis.binaries,
    analisis.datas,
    strip=False,
    upx=False,
    name="KevinRuizValdenegro",
)
