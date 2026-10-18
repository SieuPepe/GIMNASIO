"""Deja el libro con un usuario de demostración que tiene de todo.

    python herramientas/crear_demo.py                 # sobre el libro configurado
    python herramientas/crear_demo.py --nuevo         # rehaciéndolo desde cero
    python herramientas/crear_demo.py --salida otro.xlsx --nuevo

Con --nuevo el libro se rehace: catálogo de ejercicios, valoración, plantillas,
programas y el usuario de ejemplo. Sin --nuevo solo añade lo que falte.

Antes de tocar nada hace una copia de seguridad, y no pisa un libro existente
sin que se lo pidan con --forzar.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from krv.datos import libro as ml, puesta_a_punto                   # noqa: E402
from krv.nucleo import config, log                                  # noqa: E402


def main() -> int:
    partes = argparse.ArgumentParser(description=__doc__)
    partes.add_argument("--salida", type=Path,
                        help="Libro donde escribir. Por defecto, el de config.toml")
    partes.add_argument("--nuevo", action="store_true",
                        help="Rehacer el libro desde cero")
    partes.add_argument("--forzar", action="store_true",
                        help="Permite pisar un libro que ya existe")
    partes.add_argument("--sin-demo", action="store_true",
                        help="Preparar el libro pero sin el usuario de ejemplo")
    opciones = partes.parse_args()

    cfg = config.cargar()
    log.configurar(config.CARPETA_DATOS / "logs")
    ruta = opciones.salida or cfg.datos.libro
    cfg.datos.libro = ruta

    if opciones.nuevo and ruta.exists() and not opciones.forzar:
        print(f"ERROR: {ruta} ya existe. Usa --forzar si quieres rehacerlo.")
        print("       (se hará una copia de seguridad antes de tocarlo)")
        return 1

    try:
        hecho = puesta_a_punto.preparar(
            cfg, ruta, con_demo=not opciones.sin_demo, rehacer=opciones.nuevo)
    except ml.LibroBloqueado as error:
        print(f"ERROR: {error}")
        return 1

    if hecho.copia:
        print(f"copia de seguridad  {hecho.copia.name}")
    print(f"preparado           {hecho.resumen()}")
    if hecho.demo:
        print(f"demostración        {hecho.demo.resumen()}")
    for aviso in hecho.avisos:
        print(f"  aviso: {aviso}")

    print(f"\nGuardado en {hecho.ruta}")
    print("Arranca con: python -m krv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
