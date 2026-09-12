"""Genera el libro de datos vacío con todas sus hojas.

    python herramientas/crear_libro.py [ruta] [--sobreescribir]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zeu.datos import libro as mod_libro       # noqa: E402
from zeu.datos import semillas                 # noqa: E402
from zeu.nucleo import config, log             # noqa: E402


def main() -> int:
    argumentos = [a for a in sys.argv[1:] if not a.startswith("--")]
    sobreescribir = "--sobreescribir" in sys.argv
    cfg = config.cargar()
    log.configurar(config.RAIZ / "logs")
    ruta = Path(argumentos[0]) if argumentos else cfg.datos.libro

    if ruta.exists() and not sobreescribir:
        print(f"Ya existe {ruta}.")
        print("Usa --sobreescribir si de verdad quieres reemplazarlo (se hará copia antes).")
        return 1

    if ruta.exists():
        destino = mod_libro.Libro(ruta, cfg.datos.backups, cfg.datos.copias_a_conservar)
        copia = destino._copia_seguridad()
        print(f"Copia de seguridad previa: {copia}")

    mod_libro.crear(ruta, sobreescribir=sobreescribir)
    libro = mod_libro.abrir(ruta, cfg.datos.backups, cfg.datos.copias_a_conservar)
    semillas.sembrar(libro)
    libro.guardar(forzar=True)
    print(f"Libro creado: {ruta}")
    print(f"  {len(mod_libro.TABLAS)} hojas + _ESQUEMA")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
