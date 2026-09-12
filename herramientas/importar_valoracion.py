"""Carga las pruebas, criterios, baremos y protocolos de la valoración física.

    python herramientas/importar_valoracion.py [carpeta] [--actualizar]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zeu.datos.libro import Libro                            # noqa: E402
from zeu.datos.repositorio import Repositorio                # noqa: E402
from zeu.nucleo import config, log                           # noqa: E402
from zeu.servicios.importacion import importar_valoracion    # noqa: E402


def main() -> int:
    argumentos = [a for a in sys.argv[1:] if not a.startswith("--")]
    actualizar = "--actualizar" in sys.argv
    cfg = config.cargar()
    log.configurar(config.RAIZ / "logs")
    carpeta = Path(argumentos[0]) if argumentos else config.RAIZ / "datos_iniciales"

    if not cfg.datos.libro.exists():
        print(f"No existe el libro {cfg.datos.libro}.")
        return 1

    libro = Libro(cfg.datos.libro, cfg.datos.backups, cfg.datos.copias_a_conservar)
    libro.cargar()
    resultados = importar_valoracion(Repositorio(libro), carpeta, actualizar=actualizar)

    hubo_cambios = False
    codigo = 0
    for tabla, resultado in resultados.items():
        print(f"{tabla:<24} {resultado.resumen()}")
        for error in resultado.errores[:5]:
            print(f"   ERROR: {error}")
            codigo = 1
        hubo_cambios |= bool(resultado.altas or resultado.modificados)
    if hubo_cambios:
        libro.guardar()
        print("\nLibro actualizado.")
    return codigo


if __name__ == "__main__":
    raise SystemExit(main())
