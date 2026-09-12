"""Utilidades de fecha compartidas."""

from __future__ import annotations

from datetime import date, datetime


def edad(nacimiento: date, referencia: date | None = None) -> int:
    """Edad en años cumplidos. La edad se calcula, nunca se guarda."""
    ref = referencia or date.today()
    return ref.year - nacimiento.year - (
        (ref.month, ref.day) < (nacimiento.month, nacimiento.day)
    )


def a_fecha(valor) -> date | None:
    """Convierte a date lo que venga de Excel, de la interfaz o de texto."""
    if valor is None or valor == "":
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    texto = str(valor).strip()
    for formato in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    raise ValueError(f"No se reconoce la fecha: {valor!r}")


def formatear(valor: date | None) -> str:
    return valor.strftime("%d/%m/%Y") if valor else ""
