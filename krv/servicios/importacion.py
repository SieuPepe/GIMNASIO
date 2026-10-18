"""Importación del catálogo de ejercicios desde CSV.

El fichero usa punto y coma como separador y la barra vertical para los campos
con varios valores, que es lo que abre bien Excel en español sin tocar nada.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

from ..datos.esquema import tabla as buscar_tabla
from ..datos.repositorio import ErrorValidacion, Repositorio
from . import ejercicios as srv_ejercicios


@dataclass
class Resultado:
    altas: int = 0
    modificados: int = 0
    sin_cambios: int = 0
    errores: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)

    @property
    def procesados(self) -> int:
        return self.altas + self.modificados + self.sin_cambios

    def resumen(self) -> str:
        partes = [f"{self.altas} altas", f"{self.modificados} modificados",
                  f"{self.sin_cambios} sin cambios"]
        if self.errores:
            partes.append(f"{len(self.errores)} con error")
        if self.avisos:
            partes.append(f"{len(self.avisos)} avisos")
        return ", ".join(partes)


def leer_csv(ruta: Path) -> list[dict]:
    with open(ruta, encoding="utf-8-sig", newline="") as fichero:
        return [
            {clave.strip(): (valor or "").strip() for clave, valor in fila.items() if clave}
            for fila in csv.DictReader(fichero, delimiter=";")
        ]


def importar_tabla(
    repo: Repositorio,
    ruta: Path,
    nombre_tabla: str,
    actualizar: bool = False,
    clave_natural: str | None = None,
    etiqueta: str = "Nombre",
    validador=None,
) -> Resultado:
    """Importa un CSV en una tabla del libro.

    `clave_natural` permite reconocer una fila que ya existe aunque el fichero no
    traiga identificador: así reimportar no duplica. `validador` recibe la fila y
    devuelve avisos (no bloquean).
    """
    resultado = Resultado()
    tabla = buscar_tabla(nombre_tabla)
    columnas = tabla.nombres_columnas
    clave = tabla.clave

    for numero, fila in enumerate(leer_csv(ruta), start=2):
        if not any((fila.get(c) or "").strip() for c in columnas):
            continue
        datos = {c: fila.get(c) for c in columnas if c in fila}
        nombre = fila.get(etiqueta) or datos.get(clave) or f"línea {numero}"
        if validador:
            resultado.avisos.extend(
                f"Línea {numero} ({nombre}): {aviso}" for aviso in validador(datos))

        identificador = (datos.get(clave) or "").strip()
        existente = repo.obtener(nombre_tabla, identificador) if identificador else None
        if existente is None and not identificador and clave_natural:
            valor = srv_ejercicios.sin_tildes(fila.get(clave_natural))
            existente = next(
                (r for r in repo.listar(nombre_tabla)
                 if srv_ejercicios.sin_tildes(r.get(clave_natural)) == valor), None)

        try:
            if existente is None:
                repo.insertar(nombre_tabla, datos)
                resultado.altas += 1
            elif actualizar:
                identificador = existente[clave]
                antes = dict(existente)
                repo.actualizar(nombre_tabla, identificador, datos)
                if antes == repo.obtener(nombre_tabla, identificador):
                    resultado.sin_cambios += 1
                else:
                    resultado.modificados += 1
            else:
                resultado.sin_cambios += 1
        except ErrorValidacion as error:
            resultado.errores.append(f"Línea {numero} ({nombre}): {'; '.join(error.errores)}")
    return resultado


def importar_ejercicios(repo: Repositorio, ruta: Path, actualizar: bool = False) -> Resultado:
    return importar_tabla(
        repo, ruta, "T_EJERCICIOS", actualizar=actualizar,
        clave_natural="Nombre", validador=srv_ejercicios.validar_vocabulario)


# Ficheros de la valoración física, en el orden en que deben cargarse: los
# baremos y el detalle de protocolo referencian pruebas que han de existir antes.
VALORACION: tuple[tuple[str, str, str], ...] = (
    ("tests.csv", "T_CAT_TESTS", "Nombre"),
    ("criterios.csv", "T_TEST_CRITERIOS", "Descripcion"),
    ("baremos.csv", "T_BAREMOS", "ID_Test"),
    ("protocolos.csv", "T_PROTOCOLOS", "Nombre"),
    ("protocolo_det.csv", "T_PROTOCOLO_DET", "ID_Test"),
)


def importar_valoracion(repo: Repositorio, carpeta: Path,
                        actualizar: bool = False) -> dict[str, Resultado]:
    """Carga de una vez las pruebas, criterios, baremos y protocolos."""
    resultados: dict[str, Resultado] = {}
    for fichero, tabla, etiqueta in VALORACION:
        ruta = carpeta / fichero
        if not ruta.exists():
            continue
        resultados[tabla] = importar_tabla(
            repo, ruta, tabla, actualizar=actualizar, etiqueta=etiqueta)
    return resultados
