"""Deja el libro con un usuario de demostración que tiene de todo.

    python herramientas/crear_demo.py                 # sobre el libro configurado
    python herramientas/crear_demo.py --salida demo.xlsx --nuevo

Con --nuevo crea el libro desde cero y lo llena: catálogo de ejercicios,
valoración, plantillas, programas y el usuario de ejemplo. Sin --nuevo trabaja
sobre el libro que diga config.toml y solo añade lo que falte.

Nunca pisa un libro que ya exista sin que se lo pidan con --forzar, y antes de
tocar nada hace una copia de seguridad.
"""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from krv.datos import demo, libro as ml, plantillas, plantillas_correo, semillas  # noqa: E402
from krv.datos.repositorio import Repositorio                       # noqa: E402
from krv.nucleo import config, log                                  # noqa: E402
from krv.servicios.importacion import (importar_ejercicios,         # noqa: E402
                                       importar_valoracion)


def copia_de_seguridad(ruta: Path) -> Path | None:
    """Duplica el libro antes de tocarlo. Sin esto no se escribe nada."""
    if not ruta.exists():
        return None
    sello = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = ruta.with_name(f"{ruta.stem}_antes_de_demo_{sello}{ruta.suffix}")
    shutil.copy2(ruta, destino)
    return destino


def main() -> int:
    partes = argparse.ArgumentParser(description=__doc__)
    partes.add_argument("--salida", type=Path,
                        help="Libro donde escribir. Por defecto, el de config.toml")
    partes.add_argument("--nuevo", action="store_true",
                        help="Crear el libro desde cero y cargar todos los datos")
    partes.add_argument("--forzar", action="store_true",
                        help="Permite pisar un libro que ya existe (hace copia antes)")
    opciones = partes.parse_args()

    cfg = config.cargar()
    log.configurar(config.RAIZ / "logs")
    ruta = opciones.salida or cfg.datos.libro
    cfg.datos.libro = ruta

    if ml.esta_abierto_en_excel(ruta):
        print(f"ERROR: {ruta} está abierto en Excel. Ciérralo y repite.")
        return 1

    if opciones.nuevo:
        if ruta.exists() and not opciones.forzar:
            print(f"ERROR: {ruta} ya existe. Usa --forzar si quieres rehacerlo.")
            print("       (se hará una copia de seguridad antes de tocarlo)")
            return 1
        copia = copia_de_seguridad(ruta)
        if copia:
            print(f"copia de seguridad  {copia.name}")
        ruta.unlink(missing_ok=True)
        ml.crear(ruta)
        print(f"libro creado        {ruta}")
    elif not ruta.exists():
        print(f"ERROR: no existe {ruta}. Usa --nuevo para crearlo.")
        return 1
    else:
        copia = copia_de_seguridad(ruta)
        print(f"copia de seguridad  {copia.name}")

    libro = ml.abrir(ruta, cfg.datos.backups, cfg.datos.copias_a_conservar)
    repo = Repositorio(libro)
    iniciales = config.RAIZ / "datos_iniciales"

    semillas.sembrar(libro)
    resultado = importar_ejercicios(repo, iniciales / "ejercicios.csv")
    print(f"ejercicios          {resultado.resumen()}")
    for tabla, parcial in importar_valoracion(repo, iniciales).items():
        print(f"  {tabla:20} {parcial.resumen()}")
    creadas, existentes = plantillas.crear(repo)
    print(f"programas           {len(creadas)} nuevos, {len(existentes)} ya estaban")
    print(f"plantillas correo   {len(plantillas_correo.crear(repo))} creadas")

    hecho = demo.crear(repo, cfg)
    print(f"demostración        {hecho.resumen()}")
    for aviso in hecho.avisos:
        print(f"  aviso: {aviso}")

    libro.guardar()
    print(f"\nGuardado en {ruta}")
    print("Arranca con: python -m krv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
