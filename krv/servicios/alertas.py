"""Lo que requiere atención, reunido en un sitio.

Dos clases de alerta, que se comportan distinto:

- Las de **estado** (falta el consentimiento, no hay programa asignado)
  desaparecen solas en cuanto el estado cambia.
- Las de **hecho puntual** (ha declarado molestias, ha pedido cita) no pueden
  irse solas, porque el hecho ya ocurrió: se marcan como atendidas desde el
  panel.

Ver docs/09, fase 6.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from ..datos.repositorio import Repositorio
from ..nucleo.config import Config
from ..nucleo.fechas import formatear, plural
from . import cola as srv_cola
from . import programas as srv_programas
from . import respuestas as srv_respuestas
from . import usuarios as srv_usuarios

ALERTA, AVISO, INFO = "ALERTA", "AVISO", "INFO"
ORDEN_GRAVEDAD = {ALERTA: 0, AVISO: 1, INFO: 2}

USUARIOS, PROGRAMAS, VALORACION, CORREO, CONFIGURACION = (
    "Usuarios", "Programas", "Valoración", "Correo", "Configuración")


@dataclass
class Alerta:
    codigo: str
    gravedad: str
    grupo: str
    titulo: str
    detalle: str = ""
    id_usuario: str | None = None
    seccion: str | None = None        # a qué pantalla lleva al pulsarla
    orden: int = 0                    # desempate dentro de la misma gravedad
    id_respuesta: str | None = None   # si se puede marcar como atendida

    @property
    def atendible(self) -> bool:
        return self.id_respuesta is not None


def _nombre(usuario: dict) -> str:
    return " ".join(x for x in (usuario.get("Nombre"), usuario.get("Apellidos")) if x)


# --- Comprobaciones ----------------------------------------------------------

def _programas(repo: Repositorio, cfg: Config, hoy: date) -> list[Alerta]:
    dias_aviso = int(repo.config("dias_aviso_previo", str(cfg.correo.dias_aviso_previo)))
    encontradas: list[Alerta] = []

    for asignacion in repo.listar("T_ASIGNACIONES",
                                  lambda a: a.get("Estado") == "EN_CURSO"):
        dias = srv_programas.dias_para_fin(asignacion, hoy)
        if dias is None or dias > dias_aviso:
            continue
        usuario = repo.obtener("T_USUARIOS", asignacion.get("ID_Usuario")) or {}
        ciclo = repo.obtener("T_CICLOS", asignacion.get("ID_Ciclo")) or {}
        vencido = dias < 0
        encontradas.append(Alerta(
            "PROGRAMA_VENCIDO" if vencido else "PROGRAMA_VENCE",
            ALERTA if vencido else AVISO, PROGRAMAS,
            f"{_nombre(usuario)}: "
            + (f"su programa terminó hace {plural(-dias, 'día', 'días')}" if vencido
               else f"le quedan {plural(dias, 'día', 'días')} de programa"),
            f"«{ciclo.get('Nombre', '')}», hasta el "
            f"{formatear(asignacion.get('F_Fin_Prevista'))}",
            usuario.get("ID_Usuario"), "asignaciones", dias))

    activos = repo.listar("T_USUARIOS", lambda u: u.get("Estado") == "ACTIVO")
    for usuario in activos:
        if srv_programas.asignacion_vigente(repo, usuario["ID_Usuario"]):
            continue
        encontradas.append(Alerta(
            "SIN_PROGRAMA", AVISO, PROGRAMAS,
            f"{_nombre(usuario)} no tiene programa asignado",
            "Está activo pero sin planificación en curso",
            usuario["ID_Usuario"], "asignaciones", 100))

    # Cargas sin resolver en lo que está entrenando ahora mismo
    for asignacion in repo.listar("T_ASIGNACIONES",
                                  lambda a: a.get("Estado") == "EN_CURSO"):
        faltan = _sin_1rm(repo, asignacion, hoy)
        if not faltan:
            continue
        usuario = repo.obtener("T_USUARIOS", asignacion.get("ID_Usuario")) or {}
        encontradas.append(Alerta(
            "SIN_1RM", AVISO, PROGRAMAS,
            f"{_nombre(usuario)}: falta "
            + plural(len(faltan), "repetición máxima", "repeticiones máximas"),
            "Sin ellas la hoja sale «por determinar» en: "
            + ", ".join(sorted(faltan)[:4]),
            usuario.get("ID_Usuario"), "asignaciones", 50))
    return encontradas


def _sin_1rm(repo: Repositorio, asignacion: dict, hoy: date) -> set[str]:
    """Ejercicios del microciclo en curso sin repetición máxima registrada."""
    fase = srv_programas.fase_actual(repo, asignacion["ID_Asignacion"], hoy)
    semanas = srv_programas.semanas_de(repo, asignacion["ID_Asignacion"])
    if fase:
        semanas = [s for s in semanas if s.id_micro == fase.get("ID_Ciclo")]
    semanas = semanas[:1]
    faltan: set[str] = set()
    for semana in semanas:
        for sesion in semana.sesiones:
            for linea in srv_programas.lineas(repo, sesion["ID_Sesion"]):
                carga = srv_programas.resolver_carga(
                    repo, linea, asignacion.get("ID_Usuario"), semana.en_micro)
                if carga.sin_1rm:
                    ejercicio = repo.obtener(
                        "T_EJERCICIOS", linea.get("ID_Ejercicio")) or {}
                    faltan.add(ejercicio.get("Nombre") or "?")
    return faltan


def _usuarios(repo: Repositorio, cfg: Config, hoy: date) -> list[Alerta]:
    encontradas: list[Alerta] = []
    for usuario in repo.listar("T_USUARIOS", lambda u: u.get("Estado") == "ACTIVO"):
        identificador = usuario["ID_Usuario"]
        if not usuario.get("Consentimiento_SN"):
            encontradas.append(Alerta(
                "SIN_CONSENTIMIENTO", ALERTA, USUARIOS,
                f"{_nombre(usuario)} no tiene consentimiento registrado",
                "Hasta que lo dé, no se le puede enviar ningún correo salvo la "
                "propia petición",
                identificador, "usuarios", 10))
        if not usuario.get("Email"):
            encontradas.append(Alerta(
                "SIN_CORREO", AVISO, USUARIOS,
                f"{_nombre(usuario)} no tiene correo electrónico",
                "No podrá recibir la hoja de entrenamiento ni los cuestionarios",
                identificador, "usuarios", 60))

        salud = srv_usuarios.salud_vigente(repo, identificador)
        if salud is None:
            encontradas.append(Alerta(
                "SIN_CRIBADO", AVISO, VALORACION,
                f"{_nombre(usuario)} no tiene cribado de salud",
                "Conviene hacerle el PAR-Q+ antes de cualquier prueba de esfuerzo",
                identificador, "usuarios", 30))
        else:
            cribado = srv_usuarios.evaluar_cribado(salud)
            if cribado.requiere_informe and not salud.get("Requiere_Informe_Medico_SN"):
                encontradas.append(Alerta(
                    "INFORME_MEDICO", ALERTA, VALORACION,
                    f"{_nombre(usuario)}: el cribado exige informe médico",
                    "; ".join(cribado.motivos),
                    identificador, "usuarios", 5))
    return encontradas


def _valoraciones(repo: Repositorio, cfg: Config, hoy: date) -> list[Alerta]:
    meses = int(repo.config("meses_caducidad_valoracion", "4"))
    encontradas: list[Alerta] = []
    for usuario in repo.listar("T_USUARIOS", lambda u: u.get("Estado") == "ACTIVO"):
        identificador = usuario["ID_Usuario"]
        suyas = repo.listar("T_VALORACIONES",
                            lambda v: v.get("ID_Usuario") == identificador,
                            orden="Fecha", descendente=True)
        if not suyas:
            encontradas.append(Alerta(
                "SIN_VALORACION", AVISO, VALORACION,
                f"{_nombre(usuario)} no tiene ninguna valoración",
                "Sin valoración, el programa es una suposición",
                identificador, "valoraciones", 40))
            continue
        ultima = suyas[0].get("Fecha")
        if not ultima:
            continue
        transcurridos = (hoy - ultima).days
        if transcurridos > meses * 30:
            encontradas.append(Alerta(
                "VALORACION_CADUCADA", AVISO, VALORACION,
                f"{_nombre(usuario)}: la valoración tiene "
                + plural(transcurridos // 30, "mes", "meses"),
                f"La última es del {formatear(ultima)}. Toca revalorar",
                identificador, "valoraciones", 45))
    return encontradas


def _correo(repo: Repositorio, cfg: Config, hoy: date) -> list[Alerta]:
    encontradas: list[Alerta] = []
    pendientes = srv_cola.pendientes(repo)
    retrasados = srv_cola.con_retraso(repo, hoy)
    con_error = [e for e in pendientes if e.get("Estado") == "ERROR"]

    if retrasados:
        encontradas.append(Alerta(
            "CORREO_RETRASADO", ALERTA, CORREO,
            plural(len(retrasados), "correo con retraso", "correos con retraso"),
            "Debían haber salido ya. Están esperando revisión en la bandeja",
            None, "correo", 15))
    sin_retraso = len(pendientes) - len(retrasados) - len(con_error)
    if sin_retraso > 0:
        encontradas.append(Alerta(
            "CORREO_PENDIENTE", AVISO, CORREO,
            plural(sin_retraso, "correo pendiente de revisar",
                   "correos pendientes de revisar"),
            "Añádeles tu impresión y apruébalos",
            None, "correo", 70))
    for envio in con_error:
        usuario = repo.obtener("T_USUARIOS", envio.get("ID_Usuario")) or {}
        encontradas.append(Alerta(
            "CORREO_ERROR", ALERTA, CORREO,
            f"No ha salido el correo de {_nombre(usuario)}",
            envio.get("Error") or "Error sin detallar",
            envio.get("ID_Usuario"), "correo", 12))

    dias_recordatorio = int(repo.config("dias_recordatorio", "5"))
    for envio in repo.listar("T_COLA_MAIL", lambda e: (
            e.get("Codigo_Plantilla") == "ENCUESTA_T14"
            and e.get("Estado") == "ENVIADO" and not e.get("Respondido_SN"))):
        enviado = envio.get("F_Envio")
        fecha = enviado.date() if hasattr(enviado, "date") else enviado
        if not fecha or (hoy - fecha).days < dias_recordatorio * 2:
            continue
        usuario = repo.obtener("T_USUARIOS", envio.get("ID_Usuario")) or {}
        encontradas.append(Alerta(
            "ENCUESTA_SIN_RESPUESTA", AVISO, CORREO,
            f"{_nombre(usuario)} no ha respondido al cuestionario",
            "Se le envió hace " + plural((hoy - fecha).days, "día", "días"),
            envio.get("ID_Usuario"), "correo", 65))

    estado = srv_cola.estado_vacaciones(repo, hoy)
    if estado.activo:
        encontradas.append(Alerta(
            "MODO_VACACIONES", INFO, CORREO,
            f"Modo vacaciones activo hasta el {formatear(estado.caducidad)}",
            "Los correos aptos salen solos, sin revisión", None, "correo", 0))
    elif estado.motivo:
        encontradas.append(Alerta(
            "MODO_VACACIONES_INACTIVO", AVISO, CORREO,
            f"Modo vacaciones: {estado.motivo}",
            "Está marcado pero no se aplica", None, "correo", 80))
    return encontradas


def _respuestas(repo: Repositorio, cfg: Config, hoy: date) -> list[Alerta]:
    """Hechos que el usuario ha contado y hay que atender."""
    encontradas: list[Alerta] = []
    for respuesta in repo.listar("T_RESPUESTAS",
                                 lambda r: not r.get("Atendido_SN"),
                                 orden="F_Respuesta", descendente=True):
        codigo = respuesta.get("Codigo_Pregunta")
        valor = respuesta.get("Valor") or ""
        usuario = repo.obtener("T_USUARIOS", respuesta.get("ID_Usuario")) or {}
        if codigo == "MOLESTIAS" and not srv_respuestas._es_negativo(valor):
            encontradas.append(Alerta(
                "MOLESTIAS", ALERTA, USUARIOS,
                f"{_nombre(usuario)} ha declarado molestias",
                f"«{valor[:90]}»",
                respuesta.get("ID_Usuario"), "usuarios", 1,
                respuesta["ID_Respuesta"]))
        elif codigo == "QUIERE_CITA" and srv_respuestas._es_afirmativo(valor):
            encontradas.append(Alerta(
                "QUIERE_CITA", AVISO, USUARIOS,
                f"{_nombre(usuario)} quiere hablar contigo",
                f"Indícale el horario de sala: {cfg.negocio.horario_sala}"
                if cfg.negocio.horario_sala else "Indícale cuándo estás en sala",
                respuesta.get("ID_Usuario"), "usuarios", 20,
                respuesta["ID_Respuesta"]))
    return encontradas


def _configuracion(repo: Repositorio, cfg: Config, hoy: date) -> list[Alerta]:
    encontradas: list[Alerta] = []
    comprobaciones = [
        ("T_EJERCICIOS", "El catálogo de ejercicios está vacío",
         "Impórtalo con herramientas/preparar_datos.py", "ejercicios"),
        ("T_PROTOCOLOS", "No hay protocolos de valoración",
         "Sin ellos no se puede valorar a nadie", "valoraciones"),
        ("T_CICLOS", "No hay ningún programa creado",
         "Crea uno o carga las plantillas de partida", "programas"),
        ("T_PLANTILLAS_MAIL", "No hay plantillas de correo",
         "Sin ellas no se puede enviar nada", "correo"),
    ]
    for tabla, titulo, detalle, seccion in comprobaciones:
        if not repo.listar(tabla):
            encontradas.append(Alerta(
                f"VACIO_{tabla}", ALERTA, CONFIGURACION, titulo, detalle,
                None, seccion, 0))

    for plantilla in repo.listar("T_PLANTILLAS_MAIL", lambda p: p.get("Activo_SN")):
        if "{{enlace_form}}" not in (plantilla.get("Cuerpo_HTML") or ""):
            continue
        if (plantilla.get("URL_Form") or "").strip():
            continue
        encontradas.append(Alerta(
            "FORMULARIO_SIN_URL", ALERTA, CONFIGURACION,
            f"La plantilla «{plantilla.get('Codigo')}» no tiene formulario",
            "Lleva un botón a un formulario de Google y falta su URL: "
            "esos correos no se pueden enviar",
            None, "correo", 8))
    return encontradas


# --- Entrada pública ---------------------------------------------------------

def revisar(repo: Repositorio, cfg: Config, hoy: date | None = None) -> list[Alerta]:
    """Todas las alertas, de la más urgente a la menos."""
    hoy = hoy or date.today()
    encontradas: list[Alerta] = []
    for comprobacion in (_configuracion, _respuestas, _usuarios,
                         _valoraciones, _programas, _correo):
        encontradas.extend(comprobacion(repo, cfg, hoy))
    return sorted(encontradas,
                  key=lambda a: (ORDEN_GRAVEDAD.get(a.gravedad, 9), a.orden, a.titulo))


def contar(alertas: list[Alerta]) -> dict[str, int]:
    conteo = {ALERTA: 0, AVISO: 0, INFO: 0}
    for alerta in alertas:
        conteo[alerta.gravedad] = conteo.get(alerta.gravedad, 0) + 1
    return conteo


def marcar_atendida(repo: Repositorio, id_respuesta: str) -> None:
    repo.actualizar("T_RESPUESTAS", id_respuesta, {"Atendido_SN": True})


def resumen(repo: Repositorio, cfg: Config, hoy: date | None = None) -> str:
    """Las alertas en texto, para un correo o para el registro."""
    alertas = revisar(repo, cfg, hoy)
    if not alertas:
        return "Nada pendiente."
    lineas = []
    for gravedad, etiqueta in ((ALERTA, "Requiere atención"), (AVISO, "Conviene mirar")):
        suyas = [a for a in alertas if a.gravedad == gravedad]
        if not suyas:
            continue
        lineas.append(f"{etiqueta} ({len(suyas)}):")
        lineas.extend(f"  · {a.titulo}" for a in suyas)
    return "\n".join(lineas)
