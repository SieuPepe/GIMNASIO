"""Carga el catálogo de ejercicios en el libro de datos.

    python herramientas/importar_ejercicios.py [ruta.csv] [--actualizar]

Sin --actualizar solo da de alta los que faltan; con --actualizar, además
sobreescribe los que ya existen con lo que diga el fichero.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zeu.datos.libro import abrir                          # noqa: E402
from zeu.datos.repositorio import Repositorio              # noqa: E402
from zeu.nucleo import config, log                         # noqa: E402
from zeu.servicios.importacion import importar_ejercicios  # noqa: E402

POR_DEFECTO = config.RAIZ / "datos_iniciales" / "ejercicios.csv"


def main() -> int:
    argumentos = [a for a in sys.argv[1:] if not a.startswith("--")]
    actualizar = "--actualizar" in sys.argv
    cfg = config.cargar()
    log.configurar(config.RAIZ / "logs")

    ruta_csv = Path(argumentos[0]) if argumentos else POR_DEFECTO
    if not ruta_csv.exists():
        print(f"No se encuentra el fichero {ruta_csv}")
        return 1
    if not cfg.datos.libro.exists():
        print(f"No existe el libro {cfg.datos.libro}. Créalo con herramientas/crear_libro.py")
        return 1

    libro = abrir(cfg.datos.libro, cfg.datos.backups, cfg.datos.copias_a_conservar)
    resultado = importar_ejercicios(Repositorio(libro), ruta_csv, actualizar=actualizar)

    for aviso in resultado.avisos:
        print(f"  aviso: {aviso}")
    for error in resultado.errores:
        print(f"  ERROR: {error}")

    if resultado.altas or resultado.modificados:
        libro.guardar()
    print(f"\n{ruta_csv.name}: {resultado.resumen()}")
    if not actualizar and resultado.sin_cambios:
        print("Los existentes no se han tocado. Usa --actualizar si quieres sobreescribirlos.")
    return 1 if resultado.errores else 0


if __name__ == "__main__":
    raise SystemExit(main())
