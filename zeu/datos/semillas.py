"""Datos iniciales del libro recién creado.

De momento solo los parámetros de T_CONFIG. El catálogo de ejercicios, los
protocolos de valoración y los baremos del anexo 11 se cargarán en sus fases
correspondientes.
"""

from __future__ import annotations

from .libro import Libro

CONFIG_INICIAL: list[tuple[str, str, str]] = [
    ("dias_aviso_previo", "14",
     "Días antes del fin del programa en que se genera la encuesta"),
    ("dias_recordatorio", "5",
     "Días tras el envío para recordar a quien no ha respondido"),
    ("meses_caducidad_valoracion", "4",
     "A partir de aquí, el panel avisa de que toca revaloración"),
    ("formula_1rm", "EPLEY",
     "Fórmula por defecto para estimar la repetición máxima"),
    ("copias_a_conservar", "30",
     "Número de copias de seguridad que se guardan"),
    ("umbral_asimetria_pct", "10",
     "Diferencia porcentual entre lados a partir de la cual se marca asimetría"),
    ("checkin_mitad_activo", "NO",
     "Enviar el correo de una sola pregunta a mitad de ciclo"),
    ("modo_vacaciones", "NO",
     "Los borradores se envían solos, sin revisión"),
    ("caducidad_modo_vacaciones", "",
     "Fecha en que el modo vacaciones se desactiva solo (AAAA-MM-DD)"),
    ("tope_envios_dia", "20",
     "Máximo de correos que pueden salir en un día"),
]


def sembrar(libro: Libro) -> int:
    """Rellena T_CONFIG con los valores que falten. No pisa los existentes."""
    filas = libro.filas.setdefault("T_CONFIG", [])
    existentes = {f.get("Clave") for f in filas}
    nuevas = 0
    for clave, valor, descripcion in CONFIG_INICIAL:
        if clave not in existentes:
            filas.append({"Clave": clave, "Valor": valor, "Descripcion": descripcion})
            nuevas += 1
    return nuevas
