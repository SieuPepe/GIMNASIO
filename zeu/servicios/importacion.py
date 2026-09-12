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


def importar_ejercicios(repo: Repositorio, ruta: Path, actualizar: bool = False) -> Resultado:
    resultado = Resultado()
    columnas = buscar_tabla("T_EJERCICIOS").nombres_columnas

    for numero, fila in enumerate(leer_csv(ruta), start=2):
        nombre = fila.get("Nombre")
        if not nombre:
            continue
        datos = {c: fila.get(c) for c in columnas if c in fila}
        resultado.avisos.extend(
            f"Línea {numero} ({nombre}): {aviso}"
            for aviso in srv_ejercicios.validar_vocabulario(datos))

        identificador = (datos.get("ID_Ejercicio") or "").strip()
        existente = repo.obtener("T_EJERCICIOS", identificador) if identificador else None
        # Sin ID en el fichero, el nombre hace de clave natural para no duplicar.
        if existente is None and not identificador:
            existente = next(
                (e for e in repo.listar("T_EJERCICIOS")
                 if srv_ejercicios.sin_tildes(e.get("Nombre")) ==
                 srv_ejercicios.sin_tildes(nombre)), None)

        try:
            if existente is None:
                repo.insertar("T_EJERCICIOS", datos)
                resultado.altas += 1
            elif actualizar:
                clave = existente["ID_Ejercicio"]
                antes = dict(existente)
                repo.actualizar("T_EJERCICIOS", clave, datos)
                if antes == repo.obtener("T_EJERCICIOS", clave):
                    resultado.sin_cambios += 1
                else:
                    resultado.modificados += 1
            else:
                resultado.sin_cambios += 1
        except ErrorValidacion as error:
            resultado.errores.append(f"Línea {numero} ({nombre}): {'; '.join(error.errores)}")
    return resultado
