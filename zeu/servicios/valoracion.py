"""Valoración física: baremos, puntuaciones, cálculos derivados y hallazgos.

Ver docs/05-valoracion-fisica.md y el anexo docs/11-anexo-baremos.md.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from ..datos.repositorio import Repositorio
from ..nucleo.fechas import edad as calcular_edad

CAPACIDADES = ("FUERZA", "POTENCIA", "RESISTENCIA", "MOVILIDAD",
               "EQUILIBRIO", "COMPOSICION", "CONTROL_MOTOR")

# La escala de técnica: 0 es dolor, y eso no es "una puntuación baja", es un alto.
TECNICA = {0: "Dolor durante el movimiento",
           1: "No completa el movimiento o compensaciones graves",
           2: "Completa con compensaciones leves, corregibles",
           3: "Ejecución correcta en todo el rango"}


# --- Baremos ----------------------------------------------------------------

@dataclass
class Puntuacion:
    categoria: str | None = None
    puntos: int | None = None
    solidez: str = ""
    fuente: str = ""

    @property
    def hay(self) -> bool:
        return self.puntos is not None



def buscar_baremo(repo: Repositorio, id_test: str, valor: float | None,
                  sexo: str | None, edad: int | None) -> Puntuacion:
    """Busca el tramo que corresponde a este valor, sexo y edad.

    Si no hay baremo para esa combinación devuelve una puntuación vacía: el valor
    se guarda y se muestra, pero no entra en el radar. Nunca se inventa categoría.
    """
    if valor is None:
        return Puntuacion()
    for fila in repo.listar("T_BAREMOS", lambda f: f.get("ID_Test") == id_test):
        if fila.get("Sexo") not in ("AMBOS", sexo):
            continue
        if edad is not None:
            if edad < (fila.get("Edad_Min") or 0) or edad > (fila.get("Edad_Max") or 120):
                continue
        minimo = fila.get("Valor_Min")
        maximo = fila.get("Valor_Max")
        if minimo is not None and valor < minimo:
            continue
        if maximo is not None and valor > maximo:
            continue
        return Puntuacion(fila.get("Categoria"), int(fila.get("Puntuacion") or 0),
                          fila.get("Solidez") or "", fila.get("Fuente") or "")
    return Puntuacion()


# --- Cálculos derivados ------------------------------------------------------

def imc(peso: float | None, altura_cm: float | None) -> float | None:
    if not peso or not altura_cm:
        return None
    return round(peso / (altura_cm / 100) ** 2, 1)


def indice(numerador: float | None, denominador: float | None) -> float | None:
    if not numerador or not denominador:
        return None
    return round(numerador / denominador, 2)


def vo2max_rockport(peso_kg, edad, sexo, tiempo_min, fc_final) -> float | None:
    """Ecuación de Kline. Una milla andando lo más rápido posible sin correr."""
    if not all((peso_kg, edad, tiempo_min, fc_final)):
        return None
    peso_lb = peso_kg * 2.2046
    resultado = (132.853 - 0.0769 * peso_lb - 0.3877 * edad
                 + 6.315 * (1 if sexo == "H" else 0)
                 - 3.2649 * tiempo_min - 0.1565 * fc_final)
    return round(max(resultado, 0), 1)


def vo2max_cooper(metros) -> float | None:
    if not metros:
        return None
    return round(max((metros - 504.9) / 44.73, 0), 1)


def vo2max_navette(velocidad_kmh, edad) -> float | None:
    if not velocidad_kmh or not edad:
        return None
    resultado = (31.025 + 3.238 * velocidad_kmh - 3.248 * edad
                 + 0.1536 * velocidad_kmh * edad)
    return round(max(resultado, 0), 1)


def harvard_indice(duracion_s, p1, p2=None, p3=None) -> float | None:
    """Índice de capacidad física. Con los tres pulsos usa la versión completa."""
    if not duracion_s or not p1:
        return None
    if p2 and p3:
        return round(duracion_s * 100 / (2 * (p1 + p2 + p3)), 1)
    return round(duracion_s * 100 / (5.5 * p1), 1)


FORMULAS_1RM = {
    "EPLEY": lambda w, r: w * (1 + r / 30),
    "BRZYCKI": lambda w, r: w * 36 / (37 - r) if r < 37 else None,
    "LOMBARDI": lambda w, r: w * (r ** 0.10),
}


def estimar_1rm(peso: float, repeticiones: int, metodo: str = "EPLEY") -> tuple[float, str]:
    """Devuelve (1RM estimado, fiabilidad). Por encima de 10 repeticiones se degrada."""
    formula = FORMULAS_1RM.get(metodo.upper(), FORMULAS_1RM["EPLEY"])
    valor = formula(peso, repeticiones)
    if valor is None:
        raise ValueError("Demasiadas repeticiones para esa fórmula")
    fiabilidad = "ALTA" if repeticiones <= 5 else ("MEDIA" if repeticiones <= 10 else "BAJA")
    return round(valor, 1), fiabilidad


def derivadas(valores: dict[str, float], sexo: str | None, edad: int | None) -> dict[str, float]:
    """Calcula de una vez todo lo que se deriva de otras pruebas."""
    resultado: dict[str, float] = {}
    peso, altura = valores.get("PESO"), valores.get("ALTURA")
    cintura, cadera = valores.get("PERIM_CINTURA"), valores.get("PERIM_CADERA")

    if (valor := imc(peso, altura)) is not None:
        resultado["IMC"] = valor
    if (valor := indice(cintura, cadera)) is not None:
        resultado["ICC"] = valor
    if (valor := indice(cintura, altura)) is not None:
        resultado["ICA"] = valor

    # Se usa la prueba de campo que se haya hecho, por orden de preferencia.
    vo2 = (vo2max_rockport(peso, edad, sexo,
                           valores.get("ROCKPORT_TIEMPO"), valores.get("ROCKPORT_FC"))
           or vo2max_cooper(valores.get("COOPER_DIST"))
           or vo2max_navette(valores.get("NAVETTE_VEL"), edad))
    if vo2:
        resultado["VO2MAX"] = vo2

    indice_harvard = harvard_indice(valores.get("HARVARD_DUR"), valores.get("HARVARD_P1"),
                                    valores.get("HARVARD_P2"), valores.get("HARVARD_P3"))
    if indice_harvard:
        resultado["HARVARD_IF"] = indice_harvard
    return resultado


# --- Hallazgos ---------------------------------------------------------------

@dataclass
class Hallazgo:
    tipo: str          # ASIMETRIA · RELACION · ALERTA
    titulo: str
    detalle: str
    gravedad: str = "AVISO"   # AVISO · ALERTA


# Pruebas cuya escala puede ser negativa o pasar por cero: ahí un porcentaje no
# significa nada (de -1 a -3 son "200 %"), así que se comparan en su unidad. Los
# umbrales son los del anexo 11.
UMBRAL_ABSOLUTO: dict[str, float] = {
    "SCRATCH": 5.0,          # cm entre dedos
    "SIT_AND_REACH": 3.0,    # cm
    "DORSIFLEXION": 1.5,     # cm, diferencia relevante tras un esguince
}


def asimetrias(detalle: list[dict], umbral_pct: float = 10.0) -> list[Hallazgo]:
    """Diferencias entre lados. Es el hallazgo más frecuente y el más accionable."""
    por_test: dict[str, dict[str, float]] = {}
    for linea in detalle:
        lado = linea.get("Lado")
        if lado not in ("DERECHO", "IZQUIERDO"):
            continue
        valor = linea.get("Valor")
        if valor is None:
            valor = linea.get("Valor_Tecnica")
        if valor is None:
            continue
        por_test.setdefault(linea["ID_Test"], {})[lado] = float(valor)

    encontradas: list[Hallazgo] = []
    for id_test, lados in por_test.items():
        if len(lados) < 2:
            continue
        derecho, izquierdo = lados["DERECHO"], lados["IZQUIERDO"]
        diferencia = abs(derecho - izquierdo)
        fuerte = "derecho" if derecho > izquierdo else "izquierdo"
        umbral_cm = UMBRAL_ABSOLUTO.get(id_test)

        if umbral_cm is not None:
            if diferencia < umbral_cm:
                continue
            texto = f"Diferencia de {diferencia:g} entre lados"
            grave = diferencia >= umbral_cm * 2
        else:
            mayor = max(abs(derecho), abs(izquierdo))
            if mayor == 0:
                continue
            porcentaje = diferencia / mayor * 100
            if porcentaje < umbral_pct:
                continue
            texto = f"Diferencia del {porcentaje:.0f} % entre lados"
            grave = porcentaje >= umbral_pct * 2

        encontradas.append(Hallazgo(
            "ASIMETRIA", id_test,
            f"{texto} ({derecho:g} frente a {izquierdo:g}); mejor el {fuerte}. "
            "Indicación de trabajo unilateral.",
            "ALERTA" if grave else "AVISO"))
    return encontradas


def relaciones_tronco(valores: dict[str, float]) -> list[Hallazgo]:
    """Relaciones de McGill. Es lo que de verdad interpreta las pruebas del tronco."""
    hallazgos: list[Hallazgo] = []
    sorensen = valores.get("SORENSEN")
    flexores = valores.get("FLEXORES_TRONCO")
    lateral = valores.get("PLANCHA_LATERAL")
    lateral_d = valores.get("PLANCHA_LATERAL_DERECHO")
    lateral_i = valores.get("PLANCHA_LATERAL_IZQUIERDO")

    if sorensen and flexores:
        razon = flexores / sorensen
        if razon > 1.0:
            hallazgos.append(Hallazgo(
                "RELACION", "Flexores / extensores",
                f"Relación {razon:.2f} (esperado menos de 1,00): los extensores "
                "lumbares están débiles respecto a los flexores. Es un factor de "
                "riesgo conocido de dolor lumbar.", "ALERTA"))
    if sorensen and (lateral or (lateral_d and lateral_i)):
        media = lateral or (lateral_d + lateral_i) / 2
        razon = media / sorensen
        if razon > 0.75:
            hallazgos.append(Hallazgo(
                "RELACION", "Plancha lateral / extensores",
                f"Relación {razon:.2f} (esperado menos de 0,75): desequilibrio del "
                "plano frontal.", "AVISO"))
    if lateral_d and lateral_i:
        razon = lateral_d / lateral_i
        if not 0.95 <= razon <= 1.05:
            hallazgos.append(Hallazgo(
                "ASIMETRIA", "Plancha lateral derecha / izquierda",
                f"Relación {razon:.2f} (esperado entre 0,95 y 1,05): asimetría "
                "relevante del tronco.", "ALERTA"))
    return hallazgos


def alertas_tecnica(repo: Repositorio, detalle: list[dict]) -> list[Hallazgo]:
    """Un 0 técnico es dolor: bloquea la prescripción de ese patrón."""
    hallazgos: list[Hallazgo] = []
    for linea in detalle:
        if linea.get("Valor_Tecnica") == 0:
            prueba = repo.obtener("T_CAT_TESTS", linea.get("ID_Test")) or {}
            lado = linea.get("Lado")
            sufijo = f" (lado {lado.lower()})" if lado in ("DERECHO", "IZQUIERDO") else ""
            hallazgos.append(Hallazgo(
                "ALERTA", prueba.get("Nombre") or linea.get("ID_Test"),
                f"Dolor durante el movimiento{sufijo}. No se prescribirá ese patrón "
                "hasta revisarlo.", "ALERTA"))
    return hallazgos


# --- Agregación por capacidad ------------------------------------------------

def capacidades(repo: Repositorio, detalle: list[dict]) -> dict[str, tuple[int, int]]:
    """Media de puntuaciones por capacidad: {capacidad: (puntuación, nº de pruebas)}.

    Solo se puntúa lo que se ha medido. Un protocolo reducido da un radar con
    menos ejes, no un radar con ceros: un cero falso es peor que un hueco.
    """
    acumulado: dict[str, list[int]] = {}
    for linea in detalle:
        if linea.get("Puntuacion") is None:
            continue
        prueba = repo.obtener("T_CAT_TESTS", linea.get("ID_Test"))
        if not prueba:
            continue
        acumulado.setdefault(prueba["Capacidad"], []).append(int(linea["Puntuacion"]))
    return {cap: (round(sum(v) / len(v)), len(v)) for cap, v in acumulado.items() if v}


def puntuacion_global(por_capacidad: dict[str, tuple[int, int]]) -> int | None:
    if not por_capacidad:
        return None
    puntos = [p for p, _ in por_capacidad.values()]
    return round(sum(puntos) / len(puntos))


# --- Valoración completa -----------------------------------------------------

@dataclass
class Resumen:
    valoracion: dict
    usuario: dict
    edad: int | None
    detalle: list[dict]
    valores: dict[str, float]
    por_capacidad: dict[str, tuple[int, int]]
    global_: int | None
    hallazgos: list[Hallazgo] = field(default_factory=list)
    puntos_fuertes: list[str] = field(default_factory=list)
    a_mejorar: list[str] = field(default_factory=list)


def resumir(repo: Repositorio, id_valoracion: str) -> Resumen:
    valoracion = repo.obtener("T_VALORACIONES", id_valoracion) or {}
    usuario = repo.obtener("T_USUARIOS", valoracion.get("ID_Usuario")) or {}
    nacimiento = usuario.get("F_Nacimiento")
    edad = calcular_edad(nacimiento, valoracion.get("Fecha")) if nacimiento else None

    detalle = repo.listar("T_VALORACION_DET",
                          lambda f: f.get("ID_Valoracion") == id_valoracion)
    valores: dict[str, float] = {}
    for linea in detalle:
        if linea.get("Valor") is None:
            continue
        clave = linea["ID_Test"]
        lado = linea.get("Lado")
        if lado in ("DERECHO", "IZQUIERDO"):
            valores[f"{clave}_{lado}"] = float(linea["Valor"])
            valores.setdefault(clave, float(linea["Valor"]))
        else:
            valores[clave] = float(linea["Valor"])

    por_capacidad = capacidades(repo, detalle)
    hallazgos = (alertas_tecnica(repo, detalle) + asimetrias(detalle)
                 + relaciones_tronco(valores))

    fuertes, flojos = [], []
    for linea in detalle:
        puntos = linea.get("Puntuacion")
        if puntos is None:
            continue
        prueba = repo.obtener("T_CAT_TESTS", linea.get("ID_Test")) or {}
        nombre = prueba.get("Nombre") or linea.get("ID_Test")
        if puntos >= 85:
            fuertes.append(nombre)
        elif puntos <= 35:
            flojos.append(nombre)

    return Resumen(
        valoracion=valoracion, usuario=usuario, edad=edad, detalle=detalle,
        valores=valores, por_capacidad=por_capacidad,
        global_=puntuacion_global(por_capacidad), hallazgos=hallazgos,
        puntos_fuertes=sorted(set(fuertes)), a_mejorar=sorted(set(flojos)))


def comparar(anterior: Resumen, actual: Resumen) -> list[dict]:
    """Diferencias entre dos valoraciones, solo de las pruebas presentes en ambas."""
    filas = []
    for clave, valor_actual in actual.valores.items():
        if "_DERECHO" in clave or "_IZQUIERDO" in clave:
            continue
        valor_anterior = anterior.valores.get(clave)
        if valor_anterior is None:
            continue
        filas.append({
            "ID_Test": clave,
            "antes": valor_anterior,
            "ahora": valor_actual,
            "diferencia": round(valor_actual - valor_anterior, 2),
        })
    return filas
