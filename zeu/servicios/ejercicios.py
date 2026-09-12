"""Catálogo de ejercicios: vocabularios, filtrado y sustituciones.

El catálogo es la base sin la cual los programas serían texto libre: es lo que
permite equilibrar una sesión por patrón de movimiento, sustituir un ejercicio
por otro equivalente y filtrar por el material que el usuario tiene de verdad.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from ..datos.esquema import PATRON
from ..datos.repositorio import Repositorio

SEPARADOR = "|"

# Vocabulario de material. Se usa para filtrar el catálogo por lo que el usuario
# tiene disponible, así que conviene que no crezca sin control.
MATERIALES: tuple[str, ...] = (
    "PESO_CORPORAL", "BARRA", "DISCOS", "MANCUERNAS", "KETTLEBELL", "POLEA",
    "MAQUINA", "BANCO", "BANCO_LUMBAR", "RACK", "BARRA_DOMINADAS", "PARALELAS",
    "GOMA", "TRX", "CAJON", "COLCHONETA", "RODILLO", "BALON_MEDICINAL",
    "RUEDA_ABDOMINAL", "COMBA", "PALO", "TRINEO", "CINTA", "BICICLETA",
    "REMO_ERGOMETRO", "ELIPTICA",
)

GRUPOS: tuple[str, ...] = (
    "PECTORAL", "DORSAL", "TRAPECIO", "DELTOIDES", "BICEPS", "TRICEPS",
    "ANTEBRAZO", "CUADRICEPS", "ISQUIOSURALES", "GLUTEO", "ADUCTORES",
    "ABDUCTORES", "GEMELOS", "CORE", "ERECTORES", "CUERPO_COMPLETO",
    "CARDIOVASCULAR",
)

PATRONES = PATRON

# Patrones que se consideran equivalentes al buscar un sustituto.
EQUIVALENTES: dict[str, tuple[str, ...]] = {p: (p,) for p in PATRONES}

# Términos clínicos que se buscan a la vez en las contraindicaciones del
# ejercicio y en los antecedentes del usuario. Ver nota en `contraindicaciones`.
TERMINOS_CLINICOS: tuple[str, ...] = (
    "hombro", "glenohumeral", "subacromial", "esternoclavicular", "codo",
    "epicondilalgia", "muneca", "lumbar", "lumbalgia", "hernia", "discal",
    "rodilla", "femoropatelar", "menisco", "tobillo", "cadera", "aductores",
    "isquiosurales", "hipertension", "diastasis", "cervical",
)


def sin_tildes(texto: str) -> str:
    normalizado = unicodedata.normalize("NFD", str(texto or "").lower())
    return "".join(c for c in normalizado if unicodedata.category(c) != "Mn")


def lista(valor: str | None) -> tuple[str, ...]:
    """Convierte 'BARRA|DISCOS' en ('BARRA', 'DISCOS')."""
    if not valor:
        return ()
    return tuple(p.strip().upper() for p in str(valor).split(SEPARADOR) if p.strip())


def texto(valores) -> str:
    return SEPARADOR.join(v.strip().upper() for v in valores if v and v.strip())


def legible(valor: str | None) -> str:
    """'BARRA|DISCOS' -> 'barra, discos'. Presentación, no lógica."""
    return (valor or "").replace(SEPARADOR, ", ").replace("_", " ").lower()


def material_de(ejercicio: dict) -> set[str]:
    return set(lista(ejercicio.get("Material")))


def necesita_material(ejercicio: dict) -> set[str]:
    """Material realmente necesario: el peso corporal no cuenta como requisito."""
    return material_de(ejercicio) - {"PESO_CORPORAL"}


def hay_material(ejercicio: dict, disponible: set[str]) -> bool:
    """¿Se puede hacer con lo que el usuario tiene?"""
    requerido = necesita_material(ejercicio)
    if not requerido:
        return True
    disponible = {m.strip().upper() for m in disponible}
    return requerido.issubset(disponible)


@dataclass
class Contraindicacion:
    id_ejercicio: str
    nombre: str
    terminos: list[str]


def contraindicaciones(ejercicios: list[dict], antecedentes: str) -> list[Contraindicacion]:
    """Ejercicios a revisar según los antecedentes del usuario.

    Primera aproximación deliberadamente simple: se buscan términos clínicos
    presentes a la vez en las contraindicaciones del ejercicio y en el texto de
    salud del usuario. Cruzar texto libre nunca es fiable del todo, así que esto
    **señala para revisar, no bloquea**. El bloqueo de verdad vendrá de las
    reglas duras de T_REGLAS, que son explícitas.
    """
    texto_usuario = sin_tildes(antecedentes)
    if not texto_usuario.strip():
        return []
    presentes = [t for t in TERMINOS_CLINICOS if t in texto_usuario]
    if not presentes:
        return []

    encontrados: list[Contraindicacion] = []
    for ejercicio in ejercicios:
        contra = sin_tildes(ejercicio.get("Contraindicaciones"))
        if not contra.strip():
            continue
        coincidencias = [t for t in presentes if t in contra]
        if coincidencias:
            encontrados.append(Contraindicacion(
                ejercicio.get("ID_Ejercicio"), ejercicio.get("Nombre"), coincidencias))
    return encontrados


def activos(repo: Repositorio) -> list[dict]:
    return repo.listar("T_EJERCICIOS", lambda e: bool(e.get("Activo_SN")), orden="Nombre")


def filtrar(
    ejercicios: list[dict],
    patron: str | None = None,
    grupo: str | None = None,
    material: str | None = None,
    nivel_maximo: int | None = None,
    solo_basicos: bool = False,
    busqueda: str = "",
) -> list[dict]:
    """Filtro del listado y, más adelante, del catálogo que ve la IA."""
    texto_busqueda = sin_tildes(busqueda).strip()
    resultado = []
    for e in ejercicios:
        if patron and e.get("Patron") != patron:
            continue
        if grupo and grupo not in (
                (e.get("Grupo_Principal"),) + lista(e.get("Grupos_Secundarios"))):
            continue
        if material and material not in material_de(e):
            continue
        if nivel_maximo and int(e.get("Nivel") or 1) > nivel_maximo:
            continue
        if solo_basicos and not e.get("Es_Basico_SN"):
            continue
        if texto_busqueda and texto_busqueda not in sin_tildes(e.get("Nombre")):
            continue
        resultado.append(e)
    return resultado


def catalogo_disponible(
    repo: Repositorio,
    material: set[str] | None = None,
    nivel_maximo: int | None = None,
    antecedentes: str = "",
) -> list[dict]:
    """Los ejercicios que este usuario puede hacer de verdad.

    Es lo que en la fase 7 se le pasará a la IA como lista cerrada: si el
    catálogo va filtrado, el modelo no puede prescribir algo imposible.
    """
    candidatos = activos(repo)
    if material is not None:
        candidatos = [e for e in candidatos if hay_material(e, material)]
    if nivel_maximo:
        candidatos = [e for e in candidatos if int(e.get("Nivel") or 1) <= nivel_maximo]
    if antecedentes:
        excluidos = {c.id_ejercicio for c in contraindicaciones(candidatos, antecedentes)}
        candidatos = [e for e in candidatos if e.get("ID_Ejercicio") not in excluidos]
    return candidatos


def sustitutos(
    repo: Repositorio,
    id_ejercicio: str,
    material: set[str] | None = None,
    limite: int = 5,
) -> list[dict]:
    """Ejercicios equivalentes: mismo patrón, y se ordenan por parecido.

    Prioriza compartir grupo muscular principal y nivel similar. Es lo que
    resuelve el «no tengo barra» sin rehacer el programa.
    """
    original = repo.obtener("T_EJERCICIOS", id_ejercicio)
    if not original:
        return []
    patron = original.get("Patron")
    nivel = int(original.get("Nivel") or 1)
    grupo = original.get("Grupo_Principal")

    candidatos = [
        e for e in activos(repo)
        if e.get("ID_Ejercicio") != id_ejercicio
        and e.get("Patron") in EQUIVALENTES.get(patron, (patron,))
    ]
    if material is not None:
        candidatos = [e for e in candidatos if hay_material(e, material)]

    def parecido(e: dict) -> tuple:
        return (
            0 if e.get("Grupo_Principal") == grupo else 1,
            abs(int(e.get("Nivel") or 1) - nivel),
            0 if e.get("Es_Basico_SN") else 1,
            str(e.get("Nombre") or ""),
        )

    return sorted(candidatos, key=parecido)[:limite]


def volumen_por_grupo(repo: Repositorio, lineas: list[dict]) -> dict[str, float]:
    """Series semanales por grupo muscular. El secundario cuenta como media serie.

    Sirve para el control de volumen de docs/06 y para avisar de los desequilibrios
    groseros, tanto propios como de la IA.
    """
    conteo: dict[str, float] = {}
    for linea in lineas:
        ejercicio = repo.obtener("T_EJERCICIOS", linea.get("ID_Ejercicio"))
        if not ejercicio:
            continue
        series = float(linea.get("Series") or 0)
        principal = ejercicio.get("Grupo_Principal")
        if principal:
            conteo[principal] = conteo.get(principal, 0) + series
        for secundario in lista(ejercicio.get("Grupos_Secundarios")):
            conteo[secundario] = conteo.get(secundario, 0) + series / 2
    return conteo


def validar_vocabulario(ejercicio: dict) -> list[str]:
    """Comprueba material y grupos contra el vocabulario. Avisos, no bloqueos."""
    avisos: list[str] = []
    for material in material_de(ejercicio):
        if material not in MATERIALES:
            avisos.append(f"Material no reconocido: {material}")
    grupos = (ejercicio.get("Grupo_Principal"),) + lista(ejercicio.get("Grupos_Secundarios"))
    for grupo in grupos:
        if grupo and grupo not in GRUPOS:
            avisos.append(f"Grupo muscular no reconocido: {grupo}")
    return avisos


def patrones_sin_cobertura(ejercicios: list[dict]) -> list[str]:
    """Patrones de movimiento que no tiene cubiertos este conjunto de ejercicios.

    Al filtrar por el material de un usuario es fácil quedarse sin ninguna
    tracción vertical, por ejemplo, y montarle un plan desequilibrado sin darse
    cuenta. Esto lo dice antes de que pase.
    """
    presentes = {e.get("Patron") for e in ejercicios}
    esenciales = ("EMPUJE_H", "EMPUJE_V", "TRACCION_H", "TRACCION_V",
                  "DOMINANTE_RODILLA", "DOMINANTE_CADERA", "CORE")
    return [p for p in esenciales if p not in presentes]
