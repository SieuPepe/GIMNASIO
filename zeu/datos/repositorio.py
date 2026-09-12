"""Acceso a las tablas del libro: altas, bajas, modificaciones y validación.

Es la única capa que conoce la estructura del almacén. La interfaz y los
servicios trabajan con diccionarios ya validados, nunca con celdas.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Callable, Iterable

from ..nucleo import log
from ..nucleo.fechas import a_fecha
from .esquema import Tabla, Tipo, tabla as buscar_tabla
from .libro import Libro

_log = log.obtener("datos.repositorio")


class ErrorValidacion(Exception):
    def __init__(self, errores: list[str]):
        self.errores = errores
        super().__init__("; ".join(errores))


class Repositorio:
    def __init__(self, libro: Libro):
        self.libro = libro

    # -- identificadores --
    def siguiente_id(self, nombre_tabla: str) -> str:
        t = buscar_tabla(nombre_tabla)
        if not t.prefijo:
            raise ValueError(f"{nombre_tabla} usa identificadores manuales")
        contadores = self.libro.filas.setdefault("T_CONTADORES", [])
        fila = next((f for f in contadores if f.get("Prefijo") == t.prefijo), None)
        if fila is None:
            fila = {"Prefijo": t.prefijo, "Ultimo_Valor": 0}
            contadores.append(fila)
        # Nunca se reutilizan números: partimos del mayor entre el contador y lo
        # que haya en la tabla, por si alguien editó el Excel a mano.
        maximo = fila["Ultimo_Valor"] or 0
        for registro in self.libro.filas.get(nombre_tabla, []):
            valor = str(registro.get(t.clave) or "")
            if valor.startswith(t.prefijo + "-"):
                sufijo = valor.split("-", 1)[1]
                if sufijo.isdigit():
                    maximo = max(maximo, int(sufijo))
        fila["Ultimo_Valor"] = maximo + 1
        return f"{t.prefijo}-{maximo + 1:04d}"

    # -- consulta --
    def listar(
        self,
        nombre_tabla: str,
        filtro: Callable[[dict], bool] | None = None,
        orden: str | None = None,
        descendente: bool = False,
    ) -> list[dict]:
        filas = list(self.libro.filas.get(nombre_tabla, []))
        if filtro:
            filas = [f for f in filas if filtro(f)]
        if orden:
            filas.sort(key=lambda f: (f.get(orden) is None, _clave_orden(f.get(orden))),
                       reverse=descendente)
        return filas

    def obtener(self, nombre_tabla: str, identificador: str) -> dict | None:
        clave = buscar_tabla(nombre_tabla).clave
        for fila in self.libro.filas.get(nombre_tabla, []):
            if fila.get(clave) == identificador:
                return fila
        return None

    def existe(self, nombre_tabla: str, identificador: str) -> bool:
        return self.obtener(nombre_tabla, identificador) is not None

    # -- validación --
    def validar(self, nombre_tabla: str, datos: dict, identificador: str | None = None) -> list[str]:
        t = buscar_tabla(nombre_tabla)
        errores: list[str] = []
        for columna in t.columnas:
            valor = datos.get(columna.nombre)
            vacio = valor is None or (isinstance(valor, str) and not valor.strip())

            if columna.obligatorio and vacio and columna.nombre != t.clave:
                errores.append(f"«{columna.nombre}» es obligatorio")
                continue
            if vacio:
                continue

            if columna.tipo is Tipo.LISTA and str(valor) not in columna.opciones:
                errores.append(
                    f"«{columna.nombre}»: {valor!r} no es un valor válido "
                    f"({', '.join(columna.opciones)})")
            elif columna.tipo is Tipo.REF and not self.existe(columna.ref, str(valor)):
                errores.append(f"«{columna.nombre}»: no existe {valor} en {columna.ref}")
            elif columna.tipo in (Tipo.ENTERO, Tipo.DECIMAL):
                try:
                    float(valor)
                except (TypeError, ValueError):
                    errores.append(f"«{columna.nombre}» debe ser un número")
            elif columna.tipo in (Tipo.FECHA, Tipo.FECHA_HORA):
                try:
                    a_fecha(valor)
                except ValueError:
                    errores.append(f"«{columna.nombre}» no es una fecha válida")

        if identificador is None:
            nuevo = datos.get(t.clave)
            if nuevo and self.existe(nombre_tabla, str(nuevo)):
                errores.append(f"Ya existe un registro con {t.clave} = {nuevo}")
        return errores

    # -- escritura --
    def insertar(self, nombre_tabla: str, datos: dict) -> str:
        t = buscar_tabla(nombre_tabla)
        registro = {c.nombre: datos.get(c.nombre) for c in t.columnas}
        # Se valida antes de pedir el identificador: un alta rechazada no debe
        # consumir un número de la serie.
        errores = self.validar(nombre_tabla, registro)
        if not t.prefijo and not registro.get(t.clave):
            errores.append(f"«{t.clave}» es obligatorio")
        if errores:
            raise ErrorValidacion(errores)
        if t.prefijo and not registro.get(t.clave):
            registro[t.clave] = self.siguiente_id(nombre_tabla)
        self.libro.filas.setdefault(nombre_tabla, []).append(_normalizar(registro, t))
        _log.info("Alta en %s: %s", nombre_tabla, registro[t.clave])
        return str(registro[t.clave])

    def actualizar(self, nombre_tabla: str, identificador: str, datos: dict) -> None:
        t = buscar_tabla(nombre_tabla)
        actual = self.obtener(nombre_tabla, identificador)
        if actual is None:
            raise KeyError(f"No existe {identificador} en {nombre_tabla}")
        propuesto = dict(actual)
        propuesto.update({c.nombre: datos[c.nombre] for c in t.columnas if c.nombre in datos})
        propuesto[t.clave] = identificador
        errores = self.validar(nombre_tabla, propuesto, identificador=identificador)
        if errores:
            raise ErrorValidacion(errores)
        actual.update(_normalizar(propuesto, t))
        _log.info("Modificación en %s: %s", nombre_tabla, identificador)

    def dependencias(self, nombre_tabla: str, identificador: str) -> list[str]:
        """Qué registros de otras tablas apuntan a este. Integridad referencial."""
        from .esquema import TABLAS
        encontradas: list[str] = []
        for otra in TABLAS:
            for columna in otra.columnas:
                if columna.tipo is Tipo.REF and columna.ref == nombre_tabla:
                    cuantos = sum(
                        1 for f in self.libro.filas.get(otra.nombre, [])
                        if f.get(columna.nombre) == identificador
                    )
                    if cuantos:
                        encontradas.append(f"{otra.nombre}.{columna.nombre} ({cuantos})")
        return encontradas

    def borrar(self, nombre_tabla: str, identificador: str, forzar: bool = False) -> None:
        t = buscar_tabla(nombre_tabla)
        dependen = self.dependencias(nombre_tabla, identificador)
        if dependen and not forzar:
            raise ErrorValidacion(
                [f"No se puede borrar: hay registros que lo usan en {', '.join(dependen)}"])
        filas = self.libro.filas.get(nombre_tabla, [])
        self.libro.filas[nombre_tabla] = [f for f in filas if f.get(t.clave) != identificador]
        _log.info("Baja en %s: %s", nombre_tabla, identificador)

    # -- configuración --
    def config(self, clave: str, por_defecto: str = "") -> str:
        for fila in self.libro.filas.get("T_CONFIG", []):
            if fila.get("Clave") == clave:
                return str(fila.get("Valor") or por_defecto)
        return por_defecto


def _clave_orden(valor: Any):
    if valor is None:
        return ""
    if isinstance(valor, (int, float, date, datetime)):
        return valor
    return str(valor).lower()


def _normalizar(registro: dict, t: Tabla) -> dict:
    """Deja los tipos como corresponde antes de guardar en memoria."""
    limpio: dict = {}
    for columna in t.columnas:
        valor = registro.get(columna.nombre)
        if valor is None or (isinstance(valor, str) and not valor.strip()):
            limpio[columna.nombre] = None
        elif columna.tipo is Tipo.FECHA:
            limpio[columna.nombre] = a_fecha(valor)
        elif columna.tipo is Tipo.ENTERO:
            limpio[columna.nombre] = int(float(valor))
        elif columna.tipo is Tipo.DECIMAL:
            limpio[columna.nombre] = float(valor)
        elif columna.tipo is Tipo.BOOL:
            limpio[columna.nombre] = (
                valor if isinstance(valor, bool)
                else str(valor).strip().upper() in ("SI", "SÍ", "S", "1", "TRUE"))
        elif isinstance(valor, str):
            limpio[columna.nombre] = valor.strip()
        else:
            limpio[columna.nombre] = valor
    return limpio
