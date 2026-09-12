"""Registro de actividad: a fichero rotado por día y a consola."""

from __future__ import annotations

import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

_CONFIGURADO = False


def configurar(carpeta: Path) -> None:
    global _CONFIGURADO
    if _CONFIGURADO:
        return
    carpeta.mkdir(parents=True, exist_ok=True)
    formato = logging.Formatter(
        "%(asctime)s  %(levelname)-7s  %(name)-22s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    fichero = TimedRotatingFileHandler(
        carpeta / "zeu.log", when="midnight", backupCount=30, encoding="utf-8"
    )
    fichero.setFormatter(formato)
    consola = logging.StreamHandler()
    consola.setFormatter(formato)

    raiz = logging.getLogger("zeu")
    raiz.setLevel(logging.INFO)
    raiz.addHandler(fichero)
    raiz.addHandler(consola)
    _CONFIGURADO = True


def obtener(nombre: str) -> logging.Logger:
    return logging.getLogger(f"zeu.{nombre}")
