"""Punto de entrada del ejecutable.

PyInstaller lanza el fichero que se le indica como si fuera un script suelto, y
entonces `krv/__main__.py` no tiene paquete padre y sus imports relativos
fallan. Este lanzador importa el paquete de la forma normal y llama a su main.

Sin empaquetar no hace falta: ahí se usa `python -m krv`.
"""

import sys

from krv.__main__ import comprobar, main

if __name__ == "__main__":
    # --comprobar lo usa el guion de construcción nada más empaquetar.
    if "--comprobar" in sys.argv:
        raise SystemExit(comprobar())
    raise SystemExit(main())
