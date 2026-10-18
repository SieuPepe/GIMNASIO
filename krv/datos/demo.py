"""Usuario de demostración: uno solo, pero con todo lo que puede tener.

Sirve para dos cosas: ver el programa funcionando sin dar de alta a nadie real,
y tener un banco de pruebas estable cada vez que se cambia algo.

Los datos son inventados y el nombre lo dice. El correo es el de la propia
cuenta de envío, para que probar un correo de verdad sea escribirse a uno mismo
y nunca molestar a nadie.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from ..nucleo.config import Config, Correo
from ..servicios import cola as srv_cola
from ..servicios import programas as srv_programas
from ..servicios import valoracion as srv_valoracion
from .repositorio import Repositorio

NOMBRE = "Prueba"
APELLIDOS = "Demostración (datos de ejemplo)"

# Las pruebas del protocolo estándar, con un valor de partida y otro de la
# revisión posterior. La segunda tanda mejora casi todo, para que la comparación
# del informe tenga algo que enseñar.
#   id_test: (valor inicial, valor seguimiento)
PRUEBAS: dict[str, tuple[float, float]] = {
    "PESO": (71.4, 69.2),
    "ALTURA": (168.0, 168.0),
    "GRASA_PCT": (31.5, 28.9),
    "PERIM_CINTURA": (84.0, 79.5),
    "PERIM_CADERA": (102.0, 100.0),
    "PERIM_ABDOMEN": (88.0, 83.0),
    "STS_30": (14.0, 18.0),
    "PLANCHA_FRONTAL": (48.0, 72.0),
    "PLANCHA_INVERTIDA": (31.0, 45.0),
    "SORENSEN": (61.0, 88.0),
    "FLEXORES_TRONCO": (44.0, 63.0),
    "DEAD_HANG": (18.0, 31.0),
    "SALTO_VERTICAL": (22.0, 26.0),
    "ROCKPORT_TIEMPO": (15.8, 14.2),
    "ROCKPORT_FC": (148.0, 136.0),
    "SIT_AND_REACH": (1.0, 6.0),
}

# Las bilaterales llevan los dos lados. El brazo y el muslo derechos van algo
# por encima a propósito: así el informe tiene una asimetría real que señalar.
#   id_test: ((izq inicial, der inicial), (izq seguimiento, der seguimiento))
BILATERALES: dict[str, tuple[tuple[float, float], tuple[float, float]]] = {
    "PERIM_BRAZO": ((28.0, 29.0), (28.5, 29.2)),
    "PERIM_MUSLO": ((54.0, 56.5), (54.5, 56.0)),
    "DINAMOMETRIA": ((24.0, 29.5), (27.0, 31.0)),
    "PLANCHA_LATERAL": ((28.0, 36.0), (38.0, 42.0)),
    "SCRATCH": ((-4.0, 2.0), (-1.0, 3.0)),
    "DORSIFLEXION": ((8.5, 9.0), (9.5, 10.0)),
    "MONOPODAL": ((16.0, 24.0), (26.0, 29.0)),
}

# La fuerza se valora por técnica, de 0 a 3. El 1 de la zancada izquierda es
# deliberado: dispara el aviso de técnica y se ve para qué sirve.
TECNICA: dict[str, tuple[dict[str, int], dict[str, int]]] = {
    "SENTADILLA_TEC": ({"NA": 2}, {"NA": 3}),
    "ZANCADA_TEC": ({"IZQUIERDO": 1, "DERECHO": 2}, {"IZQUIERDO": 2, "DERECHO": 3}),
    "STEP_DOWN_TEC": ({"IZQUIERDO": 2, "DERECHO": 2}, {"IZQUIERDO": 3, "DERECHO": 3}),
}

UNO_RM = {
    "Sentadilla trasera con barra": (52.5, 60.0),
    "Press de banca con barra": (32.5, 37.5),
    "Peso muerto convencional": (65.0, 75.0),
    "Remo con barra": (35.0, 40.0),
}


@dataclass
class Resultado:
    id_usuario: str
    valoraciones: list[str]
    asignaciones: list[str]
    correos: int
    avisos: list[str]

    def resumen(self) -> str:
        return (f"usuario {self.id_usuario} · {len(self.valoraciones)} valoraciones · "
                f"{len(self.asignaciones)} asignaciones · {self.correos} correos")


def existe(repo: Repositorio) -> str | None:
    """El identificador del usuario de demostración, si ya está."""
    for usuario in repo.listar("T_USUARIOS"):
        if (usuario.get("Nombre") == NOMBRE
                and (usuario.get("Apellidos") or "").startswith("Demostración")):
            return usuario["ID_Usuario"]
    return None


def crear(repo: Repositorio, cfg: Config, hoy: date | None = None) -> Resultado:
    """Monta el usuario de demostración con todo lo que puede colgar de él."""
    hoy = hoy or date.today()
    avisos: list[str] = []

    id_usuario = _usuario(repo, cfg, hoy)
    _objetivos(repo, id_usuario, hoy)
    _salud(repo, id_usuario, hoy)
    _disponibilidad(repo, id_usuario, hoy)

    # Las asignaciones van antes que las marcas: así se sabe qué ejercicios
    # necesitan un 1RM para que la hoja salga con kilos de verdad.
    asignaciones = _asignaciones(repo, id_usuario, hoy, avisos)
    _marcas(repo, id_usuario, hoy, asignaciones, avisos)
    valoraciones = _valoraciones(repo, id_usuario, hoy, avisos)
    correos = _correos(repo, cfg, id_usuario, asignaciones, hoy)
    _respuestas(repo, id_usuario, hoy)

    return Resultado(id_usuario, valoraciones, asignaciones, correos, avisos)


# ------------------------------------------------------------------ las partes

def correo_de_pruebas(cfg: Config) -> str:
    """La dirección del usuario de ejemplo: la propia cuenta de envío.

    Si la configuración no tiene remitente —un config.toml a medio hacer, por
    ejemplo— se usa el de fábrica. Un usuario de demostración sin correo no
    sirve para enseñar la mitad del programa.
    """
    return cfg.correo.remitente.strip() or Correo().remitente


def _usuario(repo: Repositorio, cfg: Config, hoy: date) -> str:
    anterior = existe(repo)
    datos = {
        "Nombre": NOMBRE, "Apellidos": APELLIDOS,
        "F_Nacimiento": date(hoy.year - 42, 5, 17), "Sexo": "M",
        # El propio remitente: probar un correo es escribirse a uno mismo.
        "Email": correo_de_pruebas(cfg), "Telefono": "600 000 000",
        "F_Alta": hoy - timedelta(days=210), "Estado": "ACTIVO",
        "Consentimiento_SN": True, "F_Consentimiento": hoy - timedelta(days=210),
        "Origen_Consentimiento": "PRESENCIAL", "Acepta_Emails_SN": True,
        "Notas": "Usuario de ejemplo creado por el instalador. Se puede borrar "
                 "cuando ya no haga falta ver el programa funcionando.",
    }
    if anterior:
        repo.actualizar("T_USUARIOS", anterior, datos)
        return anterior
    return repo.insertar("T_USUARIOS", datos)


def _objetivos(repo: Repositorio, id_usuario: str, hoy: date) -> None:
    if _ya_tiene(repo, "T_OBJETIVOS", id_usuario):
        return
    for datos in (
        {"F_Registro": hoy - timedelta(days=210), "Tipo": "SALUD_GENERAL",
         "Descripcion": "Quitarme el dolor de espalda al final del día",
         "Prioridad": 1, "Horizonte_Sem": 16, "Estado": "CUMPLIDO"},
        {"F_Registro": hoy - timedelta(days=90), "Tipo": "FUERZA",
         "Descripcion": "Hacer una sentadilla con mi propio peso con buena técnica",
         "Prioridad": 1, "Horizonte_Sem": 20, "Metrica": "Sentadilla 1RM",
         "Valor_Objetivo": 70.0, "Estado": "ACTIVO"},
        {"F_Registro": hoy - timedelta(days=90), "Tipo": "PERDER_GRASA",
         "Descripcion": "Bajar algo de cintura sin pasar hambre",
         "Prioridad": 2, "Horizonte_Sem": 24, "Metrica": "Perímetro de cintura",
         "Valor_Objetivo": 78.0, "Estado": "ACTIVO"},
    ):
        repo.insertar("T_OBJETIVOS", {"ID_Usuario": id_usuario, **datos})


def _salud(repo: Repositorio, id_usuario: str, hoy: date) -> None:
    if _ya_tiene(repo, "T_SALUD", id_usuario):
        return
    comun = {"ID_Usuario": id_usuario, "Apto_SN": True,
             "Requiere_Informe_Medico_SN": False,
             "Lesiones_Historial": "Lumbalgia ocasional, sin episodios en el "
                                   "último año",
             "Contraindicaciones": "Evitar flexión lumbar cargada"}
    repo.insertar("T_SALUD", {
        **comun, "F_Registro": hoy - timedelta(days=210),
        "TA_Sistolica": 132, "TA_Diastolica": 85, "FC_Reposo": 74,
        "Patologias": "Ninguna conocida", "Medicacion": "Ninguna",
        "Observaciones": "Tensión en el límite alto. Repetir en tres meses."})
    repo.insertar("T_SALUD", {
        **comun, "F_Registro": hoy - timedelta(days=30),
        "TA_Sistolica": 124, "TA_Diastolica": 78, "FC_Reposo": 66,
        "Patologias": "Ninguna conocida", "Medicacion": "Ninguna",
        "Observaciones": "Mejor que en la revisión anterior."})


def _disponibilidad(repo: Repositorio, id_usuario: str, hoy: date) -> None:
    if _ya_tiene(repo, "T_DISPONIBILIDAD", id_usuario):
        return
    repo.insertar("T_DISPONIBILIDAD", {
        "ID_Usuario": id_usuario, "F_Registro": hoy - timedelta(days=210),
        "Dias_Semana": 2, "Dias_Preferidos": "Martes, jueves", "Franja": "TARDE",
        "Min_Sesion": 45, "Lugar": "GIMNASIO",
        "Material_Disponible": "Todo el de la sala"})
    repo.insertar("T_DISPONIBILIDAD", {
        "ID_Usuario": id_usuario, "F_Registro": hoy - timedelta(days=90),
        "Dias_Semana": 3, "Dias_Preferidos": "Lunes, miércoles, viernes",
        "Franja": "MANANA", "Min_Sesion": 60, "Lugar": "GIMNASIO",
        "Material_Disponible": "Todo el de la sala"})


# Un 1RM de partida plausible según con qué se hace el ejercicio.
POR_MATERIAL = {"BARRA": 40.0, "MANCUERNAS": 16.0, "MAQUINA": 35.0,
                "POLEA": 30.0, "KETTLEBELL": 20.0}


def _marcas(repo: Repositorio, id_usuario: str, hoy: date,
            asignaciones: list[str], avisos: list[str]) -> None:
    """Los 1RM. Sin ellos las cargas de la hoja salen «por determinar».

    Se registran los cuatro básicos con su histórico, y además los que pida el
    programa en curso, para que la hoja de entrenamiento salga con kilos de
    verdad. Se deja uno sin marca a propósito: así el aviso de «le falta una
    repetición máxima» se ve funcionando.
    """
    if _ya_tiene(repo, "T_1RM", id_usuario):
        return
    por_nombre = {e["Nombre"]: e["ID_Ejercicio"] for e in repo.listar("T_EJERCICIOS")}
    for nombre, (antes, ahora) in UNO_RM.items():
        id_ejercicio = por_nombre.get(nombre)
        if not id_ejercicio:
            avisos.append(f"No está el ejercicio «{nombre}»: me salto su 1RM")
            continue
        for fecha, valor, fiabilidad in (
                (hoy - timedelta(days=180), antes, "MEDIA"),
                (hoy - timedelta(days=25), ahora, "ALTA")):
            repo.insertar("T_1RM", {
                "ID_Usuario": id_usuario, "ID_Ejercicio": id_ejercicio,
                "Fecha": fecha, "Valor_1RM": valor, "Metodo": "EPLEY",
                "Peso_Usado": round(valor * 0.85, 1), "Reps_Usadas": 5,
                "Origen": "TEST", "Fiabilidad": fiabilidad})

    pendientes = sorted(_ejercicios_sin_marca(repo, id_usuario, asignaciones))
    for id_ejercicio in pendientes[:-1] if len(pendientes) > 1 else []:
        ejercicio = repo.obtener("T_EJERCICIOS", id_ejercicio) or {}
        valor = POR_MATERIAL.get(ejercicio.get("Material") or "", 25.0)
        repo.insertar("T_1RM", {
            "ID_Usuario": id_usuario, "ID_Ejercicio": id_ejercicio,
            "Fecha": hoy - timedelta(days=25), "Valor_1RM": valor,
            "Metodo": "EPLEY", "Peso_Usado": round(valor * 0.85, 1),
            "Reps_Usadas": 5, "Origen": "TEST", "Fiabilidad": "MEDIA"})


def _ejercicios_sin_marca(repo: Repositorio, id_usuario: str,
                          asignaciones: list[str]) -> set[str]:
    """Los ejercicios que el programa en curso necesita y aún no tienen 1RM."""
    con_marca = {m.get("ID_Ejercicio") for m in repo.listar(
        "T_1RM", lambda m: m.get("ID_Usuario") == id_usuario)}
    faltan: set[str] = set()
    for id_asignacion in asignaciones:
        asignacion = repo.obtener("T_ASIGNACIONES", id_asignacion) or {}
        if asignacion.get("Estado") != "EN_CURSO":
            continue
        for semana in srv_programas.semanas_de(repo, id_asignacion):
            for sesion in semana.sesiones:
                for linea in srv_programas.lineas(repo, sesion["ID_Sesion"]):
                    carga = srv_programas.resolver_carga(
                        repo, linea, id_usuario, semana.en_micro)
                    if carga.sin_1rm and linea.get("ID_Ejercicio") not in con_marca:
                        faltan.add(linea["ID_Ejercicio"])
    return faltan


def _valoraciones(repo: Repositorio, id_usuario: str, hoy: date,
                  avisos: list[str]) -> list[str]:
    """Dos valoraciones completas: la inicial y una de seguimiento mejor."""
    if _ya_tiene(repo, "T_VALORACIONES", id_usuario):
        return [v["ID_Valoracion"] for v in repo.listar(
            "T_VALORACIONES", lambda v: v.get("ID_Usuario") == id_usuario)]

    protocolo = _protocolo(repo)
    if protocolo is None:
        avisos.append("No hay protocolos cargados: no se crean valoraciones")
        return []
    pruebas_protocolo = {d["ID_Test"] for d in repo.listar(
        "T_PROTOCOLO_DET", lambda d: d.get("ID_Protocolo") == protocolo)}
    edad = 42
    hechas = []

    for indice, (fecha, tipo) in enumerate((
            (hoy - timedelta(days=200), "INICIAL"),
            (hoy - timedelta(days=20), "SEGUIMIENTO"))):
        id_valoracion = repo.insertar("T_VALORACIONES", {
            "ID_Usuario": id_usuario, "ID_Protocolo": protocolo, "Fecha": fecha,
            "Tipo": tipo, "Evaluador": "Kevin",
            "Observaciones": "Valoración de ejemplo." if indice == 0 else
                             "Mejora clara en tronco y equilibrio."})
        for id_test, valores in PRUEBAS.items():
            if id_test not in pruebas_protocolo:
                continue
            _linea(repo, id_valoracion, id_test, "NA", valores[indice], edad)
        for id_test, lados in BILATERALES.items():
            if id_test not in pruebas_protocolo:
                continue
            izquierdo, derecho = lados[indice]
            _linea(repo, id_valoracion, id_test, "IZQUIERDO", izquierdo, edad)
            _linea(repo, id_valoracion, id_test, "DERECHO", derecho, edad)
        for id_test, notas in TECNICA.items():
            if id_test not in pruebas_protocolo:
                continue
            for lado, nota in notas[indice].items():
                repo.insertar("T_VALORACION_DET", {
                    "ID_Valoracion": id_valoracion, "ID_Test": id_test,
                    "Lado": lado, "Valor_Tecnica": nota, "Unidad": "0-3",
                    "Puntuacion": nota * 25,
                    "Notas": "Valgo de rodilla en la bajada" if nota <= 1 else ""})
        hechas.append(id_valoracion)
    return hechas


def _linea(repo: Repositorio, id_valoracion: str, id_test: str, lado: str,
           valor: float, edad: int) -> None:
    """Una prueba medida, ya puntuada contra su tabla de referencia."""
    baremo = srv_valoracion.buscar_baremo(repo, id_test, float(valor), "M", edad)
    prueba = repo.obtener("T_CAT_TESTS", id_test) or {}
    repo.insertar("T_VALORACION_DET", {
        "ID_Valoracion": id_valoracion, "ID_Test": id_test, "Lado": lado,
        "Valor": float(valor), "Unidad": prueba.get("Unidad"),
        "Puntuacion": baremo.puntos if baremo else None,
        "Categoria": baremo.categoria if baremo else None})


def _asignaciones(repo: Repositorio, id_usuario: str, hoy: date,
                  avisos: list[str]) -> list[str]:
    """Una terminada y otra en curso que vence en 12 días.

    Lo de los 12 días es a propósito: así el panel de inicio arranca con el
    aviso de los 14 días encendido y se ve para qué sirve.
    """
    if _ya_tiene(repo, "T_ASIGNACIONES", id_usuario):
        return [a["ID_Asignacion"] for a in repo.listar(
            "T_ASIGNACIONES", lambda a: a.get("ID_Usuario") == id_usuario)]

    macros = [c for c in srv_programas.raices(repo)
              if srv_programas.hijos(repo, c["ID_Ciclo"])]
    if not macros:
        avisos.append("No hay programas con estructura: no se crean asignaciones")
        return []

    hechas = []
    pasado = macros[0]
    # El ciclo pasado empieza lo bastante atrás como para haber terminado ya.
    semanas = max(srv_programas.duracion_declarada(pasado), 4)
    identificador = srv_programas.asignar(
        repo, id_usuario, pasado["ID_Ciclo"], hoy - timedelta(weeks=semanas + 4),
        notas="Primer ciclo. Terminado.")
    repo.actualizar("T_ASIGNACIONES", identificador, {"Estado": "FINALIZADA"})
    hechas.append(identificador)

    actual = macros[1] if len(macros) > 1 else macros[0]
    fases = srv_programas.calendario(repo, actual["ID_Ciclo"], hoy)
    duracion = (max(f.fin for f in fases) - hoy).days if fases else 56
    inicio = hoy - timedelta(days=max(duracion - 12, 0))
    identificador = srv_programas.asignar(
        repo, id_usuario, actual["ID_Ciclo"], inicio,
        notas="Ciclo en curso. Termina pronto: el panel ya lo avisa.")
    repo.actualizar("T_ASIGNACIONES", identificador, {"Estado": "EN_CURSO"})
    hechas.append(identificador)
    return hechas


def _correos(repo: Repositorio, cfg: Config, id_usuario: str,
             asignaciones: list[str], hoy: date) -> int:
    """Borradores reales más un enviado y uno fallido, para ver los estados."""
    if _ya_tiene(repo, "T_COLA_MAIL", id_usuario):
        return len(repo.listar("T_COLA_MAIL",
                               lambda c: c.get("ID_Usuario") == id_usuario))
    srv_cola.generar_borradores(repo, cfg)
    if not _hay_borrador(repo, id_usuario):
        # Según cómo esté la configuración puede no salir ninguno, y entonces
        # la bandeja de la demostración no enseñaría el estado más importante.
        repo.insertar("T_COLA_MAIL", {
            "ID_Usuario": id_usuario, "Codigo_Plantilla": "ENCUESTA_T14",
            "F_Generado": hoy, "F_Programada": hoy, "Estado": "BORRADOR",
            "Asunto_Final": "¿Cómo ha ido este ciclo?",
            "Cuerpo_Final": "<p>Ejemplo de correo pendiente de tu revisión.</p>"})
    repo.insertar("T_COLA_MAIL", {
        "ID_Usuario": id_usuario, "Codigo_Plantilla": "BIENVENIDA",
        "F_Generado": hoy - timedelta(days=210),
        "F_Programada": hoy - timedelta(days=210), "Estado": "ENVIADO",
        "F_Envio": hoy - timedelta(days=210), "Aprobado_Por": "ENTRENADOR",
        "Asunto_Final": "Bienvenida", "Cuerpo_Final": "<p>Ejemplo ya enviado.</p>"})
    repo.insertar("T_COLA_MAIL", {
        "ID_Usuario": id_usuario, "Codigo_Plantilla": "RECORDATORIO",
        "F_Generado": hoy - timedelta(days=4),
        "F_Programada": hoy - timedelta(days=3), "Estado": "ERROR",
        "Asunto_Final": "Recordatorio",
        "Cuerpo_Final": "<p>Ejemplo que falló al enviarse.</p>",
        "Error": "Ejemplo: así se ve un envío que no ha salido."})
    return len(repo.listar("T_COLA_MAIL",
                           lambda c: c.get("ID_Usuario") == id_usuario))


def _respuestas(repo: Repositorio, id_usuario: str, hoy: date) -> None:
    """Una encuesta contestada, con molestia y cita: enciende dos avisos."""
    if _ya_tiene(repo, "T_RESPUESTAS", id_usuario):
        return
    for codigo, valor in (
            ("SATISFACCION", "8"),
            ("MOLESTIAS", "Algo de molestia en el hombro derecho al empujar"),
            ("QUIERE_CITA", "Sí, quiero que hablemos"),
            ("PROXIMO_CICLO", "Seguir con fuerza")):
        repo.insertar("T_RESPUESTAS", {
            "ID_Usuario": id_usuario, "F_Respuesta": hoy - timedelta(days=2),
            "Codigo_Pregunta": codigo, "Valor": valor, "Origen": "FORM",
            "Atendido_SN": False})


# ------------------------------------------------------------------- auxiliares

def _hay_borrador(repo: Repositorio, id_usuario: str) -> bool:
    return bool(repo.listar(
        "T_COLA_MAIL", lambda c: (c.get("ID_Usuario") == id_usuario
                                  and c.get("Estado") == "BORRADOR")))


def _ya_tiene(repo: Repositorio, tabla: str, id_usuario: str) -> bool:
    return bool(repo.listar(tabla, lambda f: f.get("ID_Usuario") == id_usuario))


def _protocolo(repo: Repositorio) -> str | None:
    protocolos = repo.listar("T_PROTOCOLOS")
    if not protocolos:
        return None
    predeterminado = [p for p in protocolos if p.get("Es_Predeterminado_SN")]
    return (predeterminado or protocolos)[0]["ID_Protocolo"]
