"""Dejar un libro listo para usar, desde cero.

Lo usan el instalador, la herramienta de línea de comandos y el propio
programa cuando arranca y no encuentra libro. Estaba escrito en tres sitios; es
el paso más delicado que hay, así que mejor en uno solo.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from ..nucleo.config import RAIZ, Config
from . import demo, libro as ml, plantillas, plantillas_correo, semillas
from .repositorio import Repositorio


@dataclass
class Preparacion:
    ruta: Path
    copia: Path | None = None
    ejercicios: int = 0
    pruebas: int = 0
    programas: int = 0
    plantillas_correo: int = 0
    demo: demo.Resultado | None = None
    avisos: list[str] = field(default_factory=list)

    def resumen(self) -> str:
        partes = [f"{self.ejercicios} ejercicios", f"{self.pruebas} pruebas",
                  f"{self.programas} programas",
                  f"{self.plantillas_correo} plantillas de correo"]
        if self.demo:
            partes.append("usuario de ejemplo")
        return ", ".join(partes)


def copia_de_seguridad(ruta: Path, motivo: str = "antes_de_instalar") -> Path | None:
    """Duplica el libro antes de tocarlo, con la fecha en el nombre."""
    if not ruta.exists():
        return None
    sello = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = ruta.with_name(f"{ruta.stem}_{motivo}_{sello}{ruta.suffix}")
    shutil.copy2(ruta, destino)
    return destino


def preparar(cfg: Config, ruta: Path | None = None, con_demo: bool = True,
             rehacer: bool = False) -> Preparacion:
    """Crea o completa el libro y le mete todo lo necesario para empezar.

    Con `rehacer` el libro se borra y se vuelve a hacer; sin él solo se añade lo
    que falte. En los dos casos, si había libro se hace copia antes.
    """
    ruta = Path(ruta or cfg.datos.libro)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    resultado = Preparacion(ruta=ruta)

    if ml.esta_abierto_en_excel(ruta):
        raise ml.LibroBloqueado(
            f"{ruta.name} está abierto en Excel. Ciérralo y vuelve a intentarlo.")

    resultado.copia = copia_de_seguridad(ruta)
    if rehacer:
        ruta.unlink(missing_ok=True)
    if not ruta.exists():
        ml.crear(ruta)

    libro = ml.abrir(ruta, cfg.datos.backups, cfg.datos.copias_a_conservar)
    repo = Repositorio(libro)
    iniciales = RAIZ / "datos_iniciales"

    semillas.sembrar(libro)
    if (iniciales / "ejercicios.csv").exists():
        from ..servicios.importacion import importar_ejercicios, importar_valoracion
        parcial = importar_ejercicios(repo, iniciales / "ejercicios.csv")
        resultado.ejercicios = parcial.altas + parcial.modificados
        resultado.avisos += parcial.errores[:5]
        for parcial in importar_valoracion(repo, iniciales).values():
            resultado.pruebas += parcial.altas + parcial.modificados
            resultado.avisos += parcial.errores[:3]
    else:
        resultado.avisos.append(
            f"No encuentro los datos iniciales en {iniciales}: el catálogo "
            "queda vacío")

    creados, _ = plantillas.crear(repo)
    resultado.programas = len(creados)
    resultado.plantillas_correo = len(plantillas_correo.crear(repo))

    if con_demo:
        resultado.demo = demo.crear(repo, cfg)
        resultado.avisos += resultado.demo.avisos

    libro.guardar()
    return resultado
