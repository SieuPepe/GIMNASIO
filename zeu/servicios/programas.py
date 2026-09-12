"""Planificación: árbol de ciclos, cargas, progresiones y asignaciones.

Ver docs/02 (el árbol se resuelve con ID_Padre) y docs/06 (en el plan no se
guardan kilos, se guarda la intención).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from ..datos.repositorio import Repositorio

NIVELES = ("MACRO", "MESO", "MICRO")
HIJO_DE = {"MACRO": "MESO", "MESO": "MICRO"}

# Porcentaje del 1RM que corresponde a hacer N repeticiones hasta el fallo.
# Con repeticiones en reserva se suman: 5 repeticiones a RIR 2 equivalen a 7.
PCT_POR_REPS = {1: 100.0, 2: 95.5, 3: 92.2, 4: 89.2, 5: 86.3, 6: 83.7,
                7: 81.1, 8: 78.6, 9: 76.2, 10: 74.0, 11: 71.7, 12: 69.4}


# --- Árbol -------------------------------------------------------------------

def hijos(repo: Repositorio, id_padre: str | None, tipo: str | None = None) -> list[dict]:
    return repo.listar(
        "T_CICLOS",
        lambda c: (c.get("ID_Padre") == id_padre
                   and (tipo is None or c.get("Tipo") == tipo)),
        orden="Orden")


def raices(repo: Repositorio, solo_plantillas: bool = False) -> list[dict]:
    return repo.listar(
        "T_CICLOS",
        lambda c: (c.get("Tipo") == "MACRO" and not c.get("ID_Padre")
                   and (not solo_plantillas or c.get("Es_Plantilla_SN"))),
        orden="Nombre")


def descendientes(repo: Repositorio, id_ciclo: str) -> list[dict]:
    """Todos los ciclos por debajo de este, en orden de recorrido."""
    resultado: list[dict] = []
    for hijo in hijos(repo, id_ciclo):
        resultado.append(hijo)
        resultado.extend(descendientes(repo, hijo["ID_Ciclo"]))
    return resultado


def duracion_declarada(ciclo: dict) -> int:
    return int(ciclo.get("Duracion_Sem") or 0)


def duracion_hijos(repo: Repositorio, id_ciclo: str) -> int:
    return sum(duracion_declarada(h) for h in hijos(repo, id_ciclo))


def avisos_estructura(repo: Repositorio, id_ciclo: str) -> list[str]:
    """La suma de los hijos debería cuadrar con el padre. Avisa, no bloquea."""
    avisos: list[str] = []
    for ciclo in [repo.obtener("T_CICLOS", id_ciclo)] + descendientes(repo, id_ciclo):
        if not ciclo:
            continue
        sus_hijos = hijos(repo, ciclo["ID_Ciclo"])
        if not sus_hijos:
            if ciclo["Tipo"] == "MICRO" and not sesiones(repo, ciclo["ID_Ciclo"]):
                avisos.append(f"«{ciclo['Nombre']}» no tiene ninguna sesión")
            continue
        suma = sum(duracion_declarada(h) for h in sus_hijos)
        if suma != duracion_declarada(ciclo):
            avisos.append(
                f"«{ciclo['Nombre']}» declara {duracion_declarada(ciclo)} semanas "
                f"y sus {len(sus_hijos)} hijos suman {suma}")
    return avisos


def sesiones(repo: Repositorio, id_ciclo: str) -> list[dict]:
    return repo.listar("T_SESIONES", lambda s: s.get("ID_Ciclo") == id_ciclo,
                       orden="Num_Dia")


def lineas(repo: Repositorio, id_sesion: str) -> list[dict]:
    return repo.listar("T_SESION_DET", lambda l: l.get("ID_Sesion") == id_sesion,
                       orden="Orden")


def clonar(repo: Repositorio, id_ciclo: str, nuevo_nombre: str | None = None,
           id_padre: str | None = "", es_plantilla: bool | None = None) -> str:
    """Duplica un ciclo entero con sus sesiones y ejercicios.

    Es lo que ahorra el 90 % del tiempo de crear una planificación: se parte de
    una que ya funciona y se adapta.
    """
    original = repo.obtener("T_CICLOS", id_ciclo)
    if not original:
        raise KeyError(id_ciclo)
    copia = {c: original.get(c) for c in original}
    copia.pop("ID_Ciclo", None)
    copia["Nombre"] = nuevo_nombre or f"{original['Nombre']} (copia)"
    copia["Origen"] = "CLONADO"
    copia["ID_Origen"] = id_ciclo
    if id_padre != "":
        copia["ID_Padre"] = id_padre
    if es_plantilla is not None:
        copia["Es_Plantilla_SN"] = es_plantilla
    nuevo = repo.insertar("T_CICLOS", copia)

    for sesion in sesiones(repo, id_ciclo):
        datos = {c: sesion.get(c) for c in sesion}
        datos.pop("ID_Sesion", None)
        datos["ID_Ciclo"] = nuevo
        id_sesion = repo.insertar("T_SESIONES", datos)
        for linea in lineas(repo, sesion["ID_Sesion"]):
            fila = {c: linea.get(c) for c in linea}
            fila.pop("ID_Linea", None)
            fila["ID_Sesion"] = id_sesion
            repo.insertar("T_SESION_DET", fila)

    for hijo in hijos(repo, id_ciclo):
        clonar(repo, hijo["ID_Ciclo"], hijo["Nombre"], id_padre=nuevo,
               es_plantilla=es_plantilla)
    return nuevo


def borrar_ciclo(repo: Repositorio, id_ciclo: str) -> None:
    """Borra el ciclo con todo lo que cuelga de él."""
    for hijo in hijos(repo, id_ciclo):
        borrar_ciclo(repo, hijo["ID_Ciclo"])
    for sesion in sesiones(repo, id_ciclo):
        for linea in lineas(repo, sesion["ID_Sesion"]):
            repo.borrar("T_SESION_DET", linea["ID_Linea"], forzar=True)
        repo.borrar("T_SESIONES", sesion["ID_Sesion"], forzar=True)
    repo.borrar("T_CICLOS", id_ciclo)


# --- Cargas ------------------------------------------------------------------

def rm_vigente(repo: Repositorio, id_usuario: str, id_ejercicio: str) -> dict | None:
    registros = repo.listar(
        "T_1RM",
        lambda r: (r.get("ID_Usuario") == id_usuario
                   and r.get("ID_Ejercicio") == id_ejercicio),
        orden="Fecha", descendente=True)
    return registros[0] if registros else None


def pct_por_reps(reps: int, rir: float = 0) -> float | None:
    """Porcentaje del 1RM equivalente a N repeticiones con esas en reserva."""
    efectivas = int(round(reps + rir))
    if efectivas < 1:
        return None
    return PCT_POR_REPS.get(min(efectivas, 12))


def redondear(kilos: float, incremento: float | None, minimo: float = 0) -> float:
    """A la carga levantable más cercana por debajo. Nadie pone 77,3 kg."""
    if not incremento:
        return round(kilos, 1)
    valor = int(kilos / incremento) * incremento
    if minimo and valor < minimo:
        return round(minimo, 2)
    return round(valor, 2)


def primer_numero(texto) -> int | None:
    """De '8-10' saca 8; de 'AMRAP' no saca nada."""
    if texto is None:
        return None
    digitos = ""
    for caracter in str(texto):
        if caracter.isdigit():
            digitos += caracter
        elif digitos:
            break
    return int(digitos) if digitos else None


@dataclass
class Carga:
    texto: str                 # lo que se imprime en la casilla "Carga"
    kilos: float | None = None
    nota: str = ""
    sin_1rm: bool = False


def _pct_de_la_semana(progresion: str | None, semana: int, base: float | None) -> float | None:
    """Aplica la pauta de progresión al porcentaje base."""
    if not progresion or not progresion.strip():
        return base
    pauta = progresion.strip().upper()
    if pauta.startswith("PCT:"):
        valores = [float(v) for v in pauta[4:].split(",") if v.strip()]
        return valores[min(semana - 1, len(valores) - 1)] if valores else base
    if pauta.startswith("DESCARGA:") and base is not None:
        return base * float(pauta.split(":")[1]) / 100
    return base


def resolver_carga(repo: Repositorio, linea: dict, id_usuario: str | None,
                   semana: int = 1) -> Carga:
    """Traduce la intención de la línea a la carga concreta de esa semana."""
    modo = (linea.get("Modo_Carga") or "").upper()
    valor = linea.get("Valor_Carga")
    progresion = (linea.get("Progresion") or "").strip().upper()
    ejercicio = repo.obtener("T_EJERCICIOS", linea.get("ID_Ejercicio")) or {}
    incremento = ejercicio.get("Incremento_Kg")
    minimo = 20.0 if "BARRA" in (ejercicio.get("Material") or "") else 0.0

    if modo == "PESO_CORPORAL":
        return Carga("peso corporal")
    if modo == "TIEMPO":
        if not valor:
            return Carga("por tiempo")
        # Por encima de dos minutos, en minutos: "480 s" no se lee de un vistazo.
        return Carga(f"{valor / 60:g} min" if valor >= 120 else f"{valor:g} s")
    if modo == "KG":
        kilos = float(valor or 0)
        if progresion.startswith("LINEAL:"):
            kilos += float(progresion.split(":")[1]) * (semana - 1)
        kilos = redondear(kilos, incremento, minimo)
        return Carga(f"{kilos:g} kg", kilos)

    # Modos que dependen del 1RM
    porcentaje = None
    if modo == "PCT1RM":
        porcentaje = _pct_de_la_semana(progresion, semana, float(valor or 0))
    elif modo in ("RPE", "RIR"):
        reps = primer_numero(linea.get("Reps"))
        if reps:
            rir = float(valor or 0) if modo == "RIR" else max(0.0, 10 - float(valor or 10))
            porcentaje = pct_por_reps(reps, rir)

    etiqueta = (f"{porcentaje:g} % 1RM" if modo == "PCT1RM" and porcentaje
                else (f"RIR {valor:g}" if modo == "RIR" else f"RPE {valor:g}"))

    if not id_usuario or porcentaje is None:
        return Carga(etiqueta)

    registro = rm_vigente(repo, id_usuario, linea.get("ID_Ejercicio"))
    if not registro:
        # Nunca se inventa un número: se dice que falta y se lista en alertas.
        return Carga(f"{etiqueta} → por determinar",
                     nota="sin 1RM registrado", sin_1rm=True)

    kilos = redondear(float(registro["Valor_1RM"]) * porcentaje / 100, incremento, minimo)
    if progresion.startswith("LINEAL:"):
        kilos = redondear(kilos + float(progresion.split(":")[1]) * (semana - 1),
                          incremento, minimo)
    return Carga(f"{etiqueta} → {kilos:g} kg", kilos)


def nota_progresion(progresion: str | None) -> str:
    pauta = (progresion or "").strip().upper()
    if not pauta or pauta == "NINGUNA":
        return ""
    if pauta.startswith("LINEAL:"):
        return f"sube {pauta.split(':')[1]} kg por semana"
    if pauta.startswith("PCT:"):
        return "porcentaje por semana: " + pauta[4:].replace(",", " · ")
    if pauta.startswith("DESCARGA:"):
        return f"descarga al {pauta.split(':')[1]} %"
    if pauta == "DOBLE_PROGRESION":
        return "sube repeticiones hasta el techo del rango; al llegar, sube carga"
    if pauta.startswith("AUTORREGULADA"):
        return "ajusta la carga para mantener el RIR objetivo"
    return pauta.lower()


# --- Asignaciones ------------------------------------------------------------

@dataclass
class Fase:
    id_ciclo: str
    nombre: str
    nivel: str
    inicio: date
    fin: date
    semanas: int


def calendario(repo: Repositorio, id_macro: str, inicio: date) -> list[Fase]:
    """Fechas de cada fase a partir de las duraciones declaradas.

    Se calcula al asignar y se guarda: así, cambiar la plantilla después no
    altera el calendario de quien ya la está haciendo, y el aviso de los 14 días
    tiene una fecha firme contra la que comparar.
    """
    fases: list[Fase] = []

    def recorrer(id_ciclo: str, desde: date) -> date:
        ciclo = repo.obtener("T_CICLOS", id_ciclo)
        if not ciclo:
            return desde
        semanas = duracion_declarada(ciclo)
        sus_hijos = hijos(repo, id_ciclo)
        if sus_hijos:
            cursor = desde
            for hijo in sus_hijos:
                cursor = recorrer(hijo["ID_Ciclo"], cursor)
            fin = cursor - timedelta(days=1)
        else:
            fin = desde + timedelta(weeks=max(semanas, 1)) - timedelta(days=1)
        fases.append(Fase(id_ciclo, ciclo["Nombre"], ciclo["Tipo"], desde, fin,
                          max((fin - desde).days + 1, 7) // 7))
        return fin + timedelta(days=1)

    recorrer(id_macro, inicio)
    return sorted(fases, key=lambda f: (f.inicio, NIVELES.index(f.nivel)))


def asignar(repo: Repositorio, id_usuario: str, id_macro: str, inicio: date,
            id_objetivo: str | None = None, notas: str = "") -> str:
    """Asigna un macrociclo y congela su calendario de fases."""
    fases = calendario(repo, id_macro, inicio)
    if not fases:
        raise ValueError("El ciclo no tiene estructura que asignar")
    fin = max(f.fin for f in fases)
    id_asignacion = repo.insertar("T_ASIGNACIONES", {
        "ID_Usuario": id_usuario, "ID_Ciclo": id_macro, "F_Inicio": inicio,
        "F_Fin_Prevista": fin,
        "Estado": "EN_CURSO" if inicio <= date.today() else "PLANIFICADA",
        "ID_Objetivo": id_objetivo, "Notas": notas})
    for fase in fases:
        repo.insertar("T_ASIG_FASES", {
            "ID_Asignacion": id_asignacion, "ID_Ciclo": fase.id_ciclo,
            "Nivel": fase.nivel, "F_Inicio": fase.inicio, "F_Fin": fase.fin,
            "Estado": "PENDIENTE"})
    return id_asignacion


def fases_de(repo: Repositorio, id_asignacion: str) -> list[dict]:
    return repo.listar("T_ASIG_FASES",
                       lambda f: f.get("ID_Asignacion") == id_asignacion,
                       orden="F_Inicio")


def fase_actual(repo: Repositorio, id_asignacion: str,
                referencia: date | None = None) -> dict | None:
    hoy = referencia or date.today()
    candidatas = [f for f in fases_de(repo, id_asignacion)
                  if f.get("Nivel") == "MICRO"
                  and f.get("F_Inicio") <= hoy <= f.get("F_Fin")]
    return candidatas[0] if candidatas else None


def dias_para_fin(asignacion: dict, referencia: date | None = None) -> int | None:
    fin = asignacion.get("F_Fin_Prevista")
    if not fin:
        return None
    return (fin - (referencia or date.today())).days


def asignacion_vigente(repo: Repositorio, id_usuario: str) -> dict | None:
    activas = repo.listar(
        "T_ASIGNACIONES",
        lambda a: (a.get("ID_Usuario") == id_usuario
                   and a.get("Estado") in ("EN_CURSO", "PLANIFICADA")),
        orden="F_Inicio", descendente=True)
    return activas[0] if activas else None


@dataclass
class Aviso:
    id_asignacion: str
    id_usuario: str
    nombre: str
    dias: int
    texto: str


def proximas_a_terminar(repo: Repositorio, dias_aviso: int = 14,
                        referencia: date | None = None) -> list[Aviso]:
    """Asignaciones a las que les quedan menos de N días. Dispara la encuesta."""
    encontradas: list[Aviso] = []
    for asignacion in repo.listar("T_ASIGNACIONES",
                                  lambda a: a.get("Estado") == "EN_CURSO"):
        dias = dias_para_fin(asignacion, referencia)
        if dias is None or dias > dias_aviso:
            continue
        usuario = repo.obtener("T_USUARIOS", asignacion.get("ID_Usuario")) or {}
        nombre = " ".join(x for x in (usuario.get("Nombre"),
                                      usuario.get("Apellidos")) if x)
        encontradas.append(Aviso(
            asignacion["ID_Asignacion"], asignacion.get("ID_Usuario"), nombre, dias,
            f"termina en {dias} días" if dias >= 0 else f"terminó hace {-dias} días"))
    return sorted(encontradas, key=lambda a: a.dias)


@dataclass
class Semana:
    numero: int          # semana del plan completo, la que ve el usuario
    en_micro: int        # semana dentro de su microciclo, la que usa la progresión
    id_micro: str
    nombre_micro: str
    inicio: date | None
    sesiones: list[dict] = field(default_factory=list)


def semanas_de(repo: Repositorio, id_asignacion: str) -> list[Semana]:
    """Desglose semana a semana de una asignación, con sus sesiones."""
    resultado: list[Semana] = []
    numero = 0
    for fase in fases_de(repo, id_asignacion):
        if fase.get("Nivel") != "MICRO":
            continue
        ciclo = repo.obtener("T_CICLOS", fase.get("ID_Ciclo")) or {}
        for repeticion in range(max(duracion_declarada(ciclo), 1)):
            numero += 1
            inicio = fase.get("F_Inicio")
            # La progresión se cuenta dentro del microciclo, no desde el principio
            # del plan: "PCT:80,82,85" son sus tres semanas, no las semanas 1 a 3
            # de un macrociclo de dieciséis.
            resultado.append(Semana(
                numero, repeticion + 1, fase["ID_Ciclo"], ciclo.get("Nombre", ""),
                inicio + timedelta(weeks=repeticion) if inicio else None,
                sesiones(repo, fase["ID_Ciclo"])))
    return resultado
