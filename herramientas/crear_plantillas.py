"""Crea las plantillas de macrociclo de partida.

    python herramientas/crear_plantillas.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zeu.datos import plantillas                     # noqa: E402
from zeu.datos.libro import abrir                    # noqa: E402
from zeu.datos.repositorio import Repositorio        # noqa: E402
from zeu.nucleo import config, log                   # noqa: E402


def main() -> int:
    cfg = config.cargar()
    log.configurar(config.RAIZ / "logs")
    if not cfg.datos.libro.exists():
        print(f"No existe el libro {cfg.datos.libro}.")
        return 1

    libro = abrir(cfg.datos.libro, cfg.datos.backups, cfg.datos.copias_a_conservar)
    repo = Repositorio(libro)
    if not repo.listar("T_EJERCICIOS"):
        print("El catálogo de ejercicios está vacío. Impórtalo primero:")
        print("    python herramientas/importar_ejercicios.py")
        return 1

    creadas, avisos = plantillas.crear(repo)
    for aviso in avisos:
        print(f"  aviso: {aviso}")
    if creadas:
        libro.guardar()
        for nombre in creadas:
            print(f"  creada: {nombre}")
        print(f"\n{len(creadas)} plantillas creadas.")
    else:
        print("Las plantillas ya existían. No se ha tocado nada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
