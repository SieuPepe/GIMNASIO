"""Actualiza el esquema de un libro creado con una versión anterior.

    python herramientas/migrar_libro.py [ruta.xlsx] [--revisar]

Añade las hojas y columnas que falten sin tocar los datos existentes, y hace
una copia de seguridad antes. Con --revisar solo dice qué haría.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zeu.datos import libro as mod_libro        # noqa: E402
from zeu.nucleo import config, log              # noqa: E402


def main() -> int:
    argumentos = [a for a in sys.argv[1:] if not a.startswith("--")]
    solo_revisar = "--revisar" in sys.argv
    cfg = config.cargar()
    log.configurar(config.RAIZ / "logs")
    ruta = Path(argumentos[0]) if argumentos else cfg.datos.libro

    if not ruta.exists():
        print(f"No existe el libro {ruta}.")
        return 1

    faltan = mod_libro.revisar(ruta)
    if not faltan:
        print(f"{ruta.name}: el esquema está al día, no hay nada que hacer.")
        return 0

    print(f"{ruta.name}: falta por añadir")
    for hoja, columnas in faltan.items():
        print(f"   {hoja}: {', '.join(columnas) if columnas else 'la hoja entera'}")
    if solo_revisar:
        print("\n(--revisar: no se ha tocado nada)")
        return 0

    try:
        cambios = mod_libro.migrar(ruta, cfg.datos.backups)
    except mod_libro.LibroBloqueado as error:
        print(f"\n{error}")
        return 1
    print(f"\n{len(cambios)} cambios aplicados. Copia previa en {cfg.datos.backups}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
