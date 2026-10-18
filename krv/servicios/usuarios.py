"""Lógica de negocio de usuarios: altas, cribado PAR-Q+ y datos derivados."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from ..datos.repositorio import Repositorio
from ..nucleo.fechas import edad as calcular_edad

# Qué significa cada pregunta del PAR-Q+. Ver docs/11 §1.1
PARQ = {
    "PARQ_1_SN": "Afección cardíaca o tensión arterial alta diagnosticada",
    "PARQ_2_SN": "Dolor en el pecho en reposo o con actividad",
    "PARQ_3_SN": "Mareos con pérdida de equilibrio o pérdida de consciencia",
    "PARQ_4_SN": "Otra enfermedad crónica diagnosticada",
    "PARQ_5_SN": "Medicación prescrita para una enfermedad crónica",
    "PARQ_6_SN": "Problema óseo, articular o muscular que pueda empeorar",
    "PARQ_7_SN": "Indicación médica de hacer solo actividad supervisada",
}

# Preguntas que, por sí solas, exigen informe médico antes de esfuerzo máximo.
PARQ_CRITICAS = ("PARQ_1_SN", "PARQ_2_SN", "PARQ_3_SN", "PARQ_7_SN")


@dataclass
class Cribado:
    apto: bool
    requiere_informe: bool
    bloquea_esfuerzo_maximo: bool
    motivos: list[str]


def clasificar_tension(sistolica: int | None, diastolica: int | None) -> tuple[str, int]:
    """Clasificación europea. Devuelve (categoría, grado). Ver docs/11 §1.2"""
    if not sistolica or not diastolica:
        return ("SIN_DATO", 0)
    s, d = int(sistolica), int(diastolica)
    if s >= 180 or d >= 110:
        return ("HIPERTENSION_GRADO_3", 3)
    if s >= 160 or d >= 100:
        return ("HIPERTENSION_GRADO_2", 2)
    if s >= 140 or d >= 90:
        return ("HIPERTENSION_GRADO_1", 1)
    if s >= 130 or d >= 85:
        return ("NORMAL_ALTA", 0)
    if s >= 120 or d >= 80:
        return ("NORMAL", 0)
    return ("OPTIMA", 0)


def evaluar_cribado(salud: dict) -> Cribado:
    """Aplica el criterio de docs/05: cualquier 'sí' relevante bloquea."""
    motivos: list[str] = []
    criticas = False
    for clave, texto in PARQ.items():
        if salud.get(clave):
            motivos.append(texto)
            if clave in PARQ_CRITICAS:
                criticas = True

    categoria, grado = clasificar_tension(salud.get("TA_Sistolica"), salud.get("TA_Diastolica"))
    if grado >= 1:
        motivos.append(f"Tensión arterial: {categoria.replace('_', ' ').lower()}")

    fc = salud.get("FC_Reposo")
    if fc and (int(fc) < 50 or int(fc) > 100):
        motivos.append(f"Frecuencia cardíaca en reposo fuera de rango ({fc} lpm)")

    requiere_informe = criticas or grado >= 1
    apto = not motivos
    return Cribado(
        apto=apto,
        requiere_informe=requiere_informe,
        bloquea_esfuerzo_maximo=bool(motivos),
        motivos=motivos,
    )


def salud_vigente(repo: Repositorio, id_usuario: str) -> dict | None:
    """La ficha de salud más reciente del usuario."""
    fichas = repo.listar("T_SALUD", lambda f: f.get("ID_Usuario") == id_usuario,
                         orden="F_Registro", descendente=True)
    return fichas[0] if fichas else None


def objetivo_activo(repo: Repositorio, id_usuario: str) -> dict | None:
    objetivos = repo.listar(
        "T_OBJETIVOS",
        lambda f: f.get("ID_Usuario") == id_usuario and f.get("Estado") == "ACTIVO",
        orden="Prioridad")
    return objetivos[0] if objetivos else None


def disponibilidad_vigente(repo: Repositorio, id_usuario: str) -> dict | None:
    filas = repo.listar("T_DISPONIBILIDAD", lambda f: f.get("ID_Usuario") == id_usuario,
                        orden="F_Registro", descendente=True)
    return filas[0] if filas else None


def alta(repo: Repositorio, datos: dict) -> str:
    """Alta de usuario con los valores por defecto que corresponden."""
    datos = dict(datos)
    datos.setdefault("F_Alta", date.today())
    datos.setdefault("Estado", "ACTIVO")
    datos.setdefault("Consentimiento_SN", False)
    datos.setdefault("Acepta_Emails_SN", True)
    return repo.insertar("T_USUARIOS", datos)


def resumen(repo: Repositorio, usuario: dict) -> dict:
    """Datos derivados que necesita el listado, calculados de una vez."""
    id_usuario = usuario.get("ID_Usuario")
    salud = salud_vigente(repo, id_usuario)
    objetivo = objetivo_activo(repo, id_usuario)
    cribado = evaluar_cribado(salud) if salud else None
    nacimiento = usuario.get("F_Nacimiento")
    return {
        "id": id_usuario,
        "nombre_completo": " ".join(
            x for x in (usuario.get("Nombre"), usuario.get("Apellidos")) if x),
        "edad": calcular_edad(nacimiento) if nacimiento else None,
        "sexo": usuario.get("Sexo") or "",
        "email": usuario.get("Email") or "",
        "estado": usuario.get("Estado") or "",
        "consentimiento": bool(usuario.get("Consentimiento_SN")),
        "objetivo": (objetivo or {}).get("Descripcion") or "",
        "tiene_salud": salud is not None,
        "cribado": cribado,
    }


def avisos(repo: Repositorio, usuario: dict) -> list[str]:
    """Lo que hay que resolver de este usuario. Alimenta el panel de inicio."""
    pendientes: list[str] = []
    id_usuario = usuario.get("ID_Usuario")
    if not usuario.get("Consentimiento_SN"):
        pendientes.append("Sin consentimiento de datos registrado")
    if not usuario.get("Email"):
        pendientes.append("Sin correo electrónico: no podrá recibir cuestionarios")
    salud = salud_vigente(repo, id_usuario)
    if salud is None:
        pendientes.append("Sin cribado de salud (PAR-Q+)")
    else:
        cribado = evaluar_cribado(salud)
        if cribado.requiere_informe and not salud.get("Requiere_Informe_Medico_SN"):
            pendientes.append("El cribado exige informe médico y no está marcado")
    if objetivo_activo(repo, id_usuario) is None:
        pendientes.append("Sin objetivo activo")
    if disponibilidad_vigente(repo, id_usuario) is None:
        pendientes.append("Sin disponibilidad registrada")
    return pendientes
