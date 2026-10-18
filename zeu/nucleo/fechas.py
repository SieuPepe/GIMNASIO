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


DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre")


def formatear_largo(valor: date | None) -> str:
    """«lunes, 18 de octubre de 2026», sin depender del idioma del sistema."""
    if not valor:
        return ""
    return (f"{DIAS[valor.weekday()]}, {valor.day} de "
            f"{MESES[valor.month - 1]} de {valor.year}")


def plural(cantidad: int, singular: str, plural_: str | None = None) -> str:
    """«1 correo» / «3 correos», sin el «1 correos» que delata al programa."""
    return f"{cantidad} {singular if cantidad == 1 else (plural_ or singular + 's')}"
