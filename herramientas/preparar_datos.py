"""Deja el libro listo para empezar: catálogo, valoración, plantillas y correos.

    python herramientas/preparar_datos.py

Es equivalente a lanzar en orden importar_ejercicios, importar_valoracion,
crear_plantillas y las plantillas de correo. No pisa nada de lo que ya exista.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zeu.datos import plantillas, plantillas_correo, semillas    # noqa: E402
from zeu.datos.libro import Libro                                # noqa: E402
from zeu.datos.repositorio import Repositorio                    # noqa: E402
from zeu.nucleo import config, log                               # noqa: E402
from zeu.servicios.importacion import (                          # noqa: E402
    importar_ejercicios, importar_valoracion)


def main() -> int:
    cfg = config.cargar()
    log.configurar(config.RAIZ / "logs")
    if not cfg.datos.libro.exists():
        print(f"No existe el libro {cfg.datos.libro}.")
        print("Créalo primero con: python herramientas/crear_libro.py")
        return 1

    libro = Libro(cfg.datos.libro, cfg.datos.backups, cfg.datos.copias_a_conservar)
    libro.cargar()
    repo = Repositorio(libro)
    datos = config.RAIZ / "datos_iniciales"
    codigo = 0

    nuevas = semillas.sembrar(libro)
    print(f"configuración      {nuevas} parámetros añadidos")

    resultado = importar_ejercicios(repo, datos / "ejercicios.csv")
    print(f"ejercicios         {resultado.resumen()}")
    codigo |= 1 if resultado.errores else 0

    for tabla, parcial in importar_valoracion(repo, datos).items():
        print(f"{tabla:<18} {parcial.resumen()}")
        codigo |= 1 if parcial.errores else 0

    creadas, avisos = plantillas.crear(repo)
    print(f"plantillas         {len(creadas)} macrociclos creados")
    for aviso in avisos:
        print(f"   aviso: {aviso}")

    correos = plantillas_correo.crear(repo)
    print(f"plantillas correo  {len(correos)} creadas")

    libro.guardar()
    print(f"\nLibro listo: {cfg.datos.libro}")
    if correos:
        print("\nPendiente: pega la URL del formulario de Google en cada plantilla de "
              "correo\n(hoja T_PLANTILLAS_MAIL, columna URL_Form), sustituyendo los "
              "valores por\n{{id_usuario}} y {{id_envio}}.")
    return codigo


if __name__ == "__main__":
    raise SystemExit(main())
