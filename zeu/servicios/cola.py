"""Bandeja de salida: detección de disparadores, borradores y envío.

Nada sale a ciegas: la aplicación genera borradores y el entrenador los revisa,
añade su impresión personal y aprueba. El modo vacaciones salta la revisión,
con salvaguardas. Ver docs/04.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

from ..datos.repositorio import Repositorio
from ..nucleo import log
from ..nucleo.config import Config
from ..nucleo.fechas import formatear
from . import correo as srv_correo
from . import programas as srv_programas
from . import usuarios as srv_usuarios

_log = log.obtener("servicios.cola")

# ERROR también está abierto: un correo que no ha salido tiene que seguir a la
# vista para poder arreglar la causa y reintentarlo, no desaparecer.
ESTADOS_ABIERTOS = ("BORRADOR", "REVISADO", "ERROR")


# --- Contexto del correo -----------------------------------------------------

def contexto(repo: Repositorio, cfg: Config, id_usuario: str,
             id_asignacion: str | None = None,
             nota: str = "", extra: dict | None = None) -> dict:
    """Todo lo que puede sustituirse en una plantilla para este usuario."""
    usuario = repo.obtener("T_USUARIOS", id_usuario) or {}
    objetivo = srv_usuarios.objetivo_activo(repo, id_usuario) or {}
    datos = {
        "nombre": usuario.get("Nombre") or "",
        "nombre_completo": " ".join(
            x for x in (usuario.get("Nombre"), usuario.get("Apellidos")) if x),
        "email": usuario.get("Email") or "",
        "objetivo": objetivo.get("Descripcion") or "",
        "entrenador": cfg.negocio.contacto or cfg.negocio.nombre_comercial,
        "gimnasio": cfg.negocio.nombre_comercial,
        "lema": cfg.negocio.lema,
        "horario_sala": cfg.negocio.horario_sala,
        "nota": nota, "nota_entrenador": nota,
    }
    if id_asignacion:
        asignacion = repo.obtener("T_ASIGNACIONES", id_asignacion) or {}
        ciclo = repo.obtener("T_CICLOS", asignacion.get("ID_Ciclo")) or {}
        fase = srv_programas.fase_actual(repo, id_asignacion)
        micro = repo.obtener("T_CICLOS", fase.get("ID_Ciclo")) if fase else None
        datos.update({
            "programa": ciclo.get("Nombre") or "",
            "semanas": str(ciclo.get("Duracion_Sem") or ""),
            "fecha_inicio": formatear(asignacion.get("F_Inicio")),
            "fecha_fin": formatear(asignacion.get("F_Fin_Prevista")),
            "fase_actual": micro.get("Nombre") if micro else "",
            "dias_restantes": str(srv_programas.dias_para_fin(asignacion) or ""),
        })
    datos.update(extra or {})
    return datos


def montar(repo: Repositorio, cfg: Config, envio: dict) -> tuple[str, str]:
    """Devuelve (asunto, cuerpo HTML completo) listo para ver o enviar."""
    plantilla = next(
        (p for p in repo.listar("T_PLANTILLAS_MAIL")
         if p.get("Codigo") == envio.get("Codigo_Plantilla")), None)
    if not plantilla:
        raise ValueError(f"No hay plantilla para {envio.get('Codigo_Plantilla')}")

    valores = contexto(repo, cfg, envio["ID_Usuario"], envio.get("ID_Asignacion"),
                       nota=envio.get("Nota_Entrenador") or "")
    valores["enlace_form"] = srv_correo.enlace_prerrellenado(
        plantilla.get("URL_Form") or "", envio["ID_Usuario"], envio["ID_Envio"])
    valores["cita"] = envio.get("Quiere_Cita") or ""

    asunto = srv_correo.rellenar(plantilla.get("Asunto") or "", valores)
    # El cuerpo redactado por la IA, cuando lo haya (fase 7), manda sobre la
    # plantilla; hasta entonces se usa la plantilla tal cual.
    base = envio.get("Cuerpo_IA") or plantilla.get("Cuerpo_HTML") or ""
    cuerpo = srv_correo.rellenar(base, valores)
    html = srv_correo.envolver(cuerpo, cfg.negocio.nombre_comercial, cfg.negocio.lema,
                               cfg.negocio.contacto)
    return asunto, html


def comprobar(repo: Repositorio, cfg: Config, envio: dict) -> list[str]:
    """Los tres fallos que delatan un correo automático, antes de enviarlo."""
    problemas: list[str] = []
    usuario = repo.obtener("T_USUARIOS", envio.get("ID_Usuario")) or {}
    asunto, html = montar(repo, cfg, envio)

    if not usuario.get("Email"):
        problemas.append("El usuario no tiene correo electrónico")
    if usuario.get("Nombre") and usuario["Nombre"] not in html:
        problemas.append("El nombre del usuario no aparece en el cuerpo")
    pendientes = (srv_correo.marcadores_sin_resolver(html)
                  + srv_correo.marcadores_sin_resolver(asunto))
    if pendientes:
        problemas.append("Marcadores sin sustituir: " + ", ".join(pendientes))

    plantilla = next((p for p in repo.listar("T_PLANTILLAS_MAIL")
                      if p.get("Codigo") == envio.get("Codigo_Plantilla")), None)
    if plantilla and "{{enlace_form}}" in (plantilla.get("Cuerpo_HTML") or ""):
        if not (plantilla.get("URL_Form") or "").strip():
            problemas.append(
                f"La plantilla {plantilla['Codigo']} lleva un botón a un "
                "formulario y no tiene URL. Pégala en «Plantillas de correo»")
        elif envio["ID_Usuario"] not in html:
            problemas.append("El enlace del formulario no lleva el identificador")
    return problemas


# --- Disparadores ------------------------------------------------------------

@dataclass
class Disparador:
    codigo: str
    id_usuario: str
    id_asignacion: str | None
    motivo: str
    programada: date


def _ya_hay(repo: Repositorio, codigo: str, id_usuario: str,
            id_asignacion: str | None) -> bool:
    for envio in repo.listar("T_COLA_MAIL"):
        if (envio.get("Codigo_Plantilla") == codigo
                and envio.get("ID_Usuario") == id_usuario
                and envio.get("ID_Asignacion") == id_asignacion
                and envio.get("Estado") != "CANCELADO"):
            return True
    return False


def detectar(repo: Repositorio, cfg: Config, hoy: date | None = None) -> list[Disparador]:
    """Recorre usuarios y asignaciones buscando lo que toca enviar."""
    hoy = hoy or date.today()
    dias_aviso = int(repo.config("dias_aviso_previo", str(cfg.correo.dias_aviso_previo)))
    dias_recordatorio = int(repo.config("dias_recordatorio", "5"))
    checkin = repo.config("checkin_mitad_activo", "NO").upper() in ("SI", "SÍ", "1")
    encontrados: list[Disparador] = []

    for usuario in repo.listar("T_USUARIOS", lambda u: u.get("Estado") == "ACTIVO"):
        identificador = usuario["ID_Usuario"]
        if (not usuario.get("Consentimiento_SN") and usuario.get("Email")
                and not _ya_hay(repo, "CONSENTIMIENTO", identificador, None)):
            encontrados.append(Disparador(
                "CONSENTIMIENTO", identificador, None,
                "sin consentimiento registrado", hoy))

    for asignacion in repo.listar("T_ASIGNACIONES"):
        identificador = asignacion["ID_Asignacion"]
        id_usuario = asignacion.get("ID_Usuario")
        usuario = repo.obtener("T_USUARIOS", id_usuario) or {}
        if usuario.get("Estado") != "ACTIVO" or not usuario.get("Email"):
            continue
        estado = asignacion.get("Estado")
        inicio, fin = asignacion.get("F_Inicio"), asignacion.get("F_Fin_Prevista")
        if not inicio or not fin:
            continue
        dias = (fin - hoy).days

        if estado in ("PLANIFICADA", "EN_CURSO") and not _ya_hay(
                repo, "BIENVENIDA", id_usuario, identificador):
            encontrados.append(Disparador("BIENVENIDA", id_usuario, identificador,
                                          "programa recién asignado", inicio))

        if checkin and estado == "EN_CURSO":
            mitad = inicio + (fin - inicio) / 2
            if hoy >= mitad and not _ya_hay(repo, "CHECKIN_MITAD", id_usuario, identificador):
                encontrados.append(Disparador("CHECKIN_MITAD", id_usuario, identificador,
                                              "mitad del ciclo", mitad))

        if estado == "EN_CURSO" and 0 <= dias <= dias_aviso and not _ya_hay(
                repo, "ENCUESTA_T14", id_usuario, identificador):
            encontrados.append(Disparador(
                "ENCUESTA_T14", id_usuario, identificador,
                f"quedan {dias} días", fin - timedelta(days=dias_aviso)))

        if estado in ("EN_CURSO", "FINALIZADA") and dias < 0 and not _ya_hay(
                repo, "CIERRE_CICLO", id_usuario, identificador):
            encontrados.append(Disparador("CIERRE_CICLO", id_usuario, identificador,
                                          "el ciclo ha terminado", fin))

    # Recordatorio a quien recibió la encuesta y no ha respondido
    for envio in repo.listar("T_COLA_MAIL", lambda e: (
            e.get("Codigo_Plantilla") == "ENCUESTA_T14"
            and e.get("Estado") == "ENVIADO" and not e.get("Respondido_SN"))):
        enviado = envio.get("F_Envio")
        fecha = enviado.date() if isinstance(enviado, datetime) else enviado
        if not fecha or (hoy - fecha).days < dias_recordatorio:
            continue
        if _ya_hay(repo, "RECORDATORIO", envio["ID_Usuario"], envio.get("ID_Asignacion")):
            continue
        encontrados.append(Disparador(
            "RECORDATORIO", envio["ID_Usuario"], envio.get("ID_Asignacion"),
            f"sin responder desde hace {(hoy - fecha).days} días", hoy))

    return encontrados


def generar_borradores(repo: Repositorio, cfg: Config,
                       hoy: date | None = None) -> list[str]:
    """Crea en la cola un borrador por cada disparador pendiente."""
    creados = []
    for disparador in detectar(repo, cfg, hoy):
        identificador = repo.insertar("T_COLA_MAIL", {
            "ID_Usuario": disparador.id_usuario,
            "ID_Asignacion": disparador.id_asignacion,
            "Codigo_Plantilla": disparador.codigo,
            "F_Generado": datetime.now(),
            "F_Programada": disparador.programada,
            "Estado": "BORRADOR",
        })
        creados.append(identificador)
        _log.info("Borrador %s (%s) para %s", identificador, disparador.codigo,
                  disparador.id_usuario)
    return creados


def pendientes(repo: Repositorio) -> list[dict]:
    return repo.listar("T_COLA_MAIL", lambda e: e.get("Estado") in ESTADOS_ABIERTOS,
                       orden="F_Programada")


def con_retraso(repo: Repositorio, hoy: date | None = None) -> list[dict]:
    hoy = hoy or date.today()
    return [e for e in pendientes(repo)
            if e.get("F_Programada") and e["F_Programada"] < hoy]


# --- Adjuntos ----------------------------------------------------------------

# Plantillas cuyo texto promete un documento. Si el correo lo dice, tiene que ir.
CON_ADJUNTO = ("BIENVENIDA",)


def adjuntos_para(repo: Repositorio, cfg: Config, envio: dict) -> list[Path]:
    """Los documentos que acompañan a este correo, generados al vuelo."""
    if envio.get("Codigo_Plantilla") not in CON_ADJUNTO:
        return []
    id_asignacion = envio.get("ID_Asignacion")
    if not id_asignacion:
        return []

    from . import informes

    semanas = srv_programas.semanas_de(repo, id_asignacion)
    if not semanas:
        return []
    # «Las primeras semanas» es el primer microciclo entero, que es lo que el
    # usuario va a hacer ahora; como mucho seis, para que no sea un tocho.
    primero = semanas[0].id_micro
    del_primer_micro = [s.numero for s in semanas if s.id_micro == primero]
    return [informes.generar_programa(repo, cfg, id_asignacion,
                                      desde=del_primer_micro[0],
                                      hasta=min(del_primer_micro[-1],
                                                del_primer_micro[0] + 5))]


# --- Envío -------------------------------------------------------------------

@dataclass
class ResultadoEnvio:
    enviados: list[str]
    fallidos: list[tuple[str, str]]
    omitidos: list[tuple[str, str]]


def enviar(repo: Repositorio, cfg: Config, enviador: srv_correo.Enviador,
           identificadores: list[str], aprobado_por: str = "ENTRENADOR",
           adjuntos: dict[str, list[Path]] | None = None) -> ResultadoEnvio:
    """Envía los borradores indicados y anota el resultado en la cola."""
    resultado = ResultadoEnvio([], [], [])
    for identificador in identificadores:
        envio = repo.obtener("T_COLA_MAIL", identificador)
        if not envio or envio.get("Estado") == "ENVIADO":
            resultado.omitidos.append((identificador, "ya enviado o inexistente"))
            continue
        usuario = repo.obtener("T_USUARIOS", envio.get("ID_Usuario")) or {}

        # Requisito legal, no configurable: sin consentimiento no sale nada que
        # no sea la propia petición de consentimiento.
        if (not usuario.get("Consentimiento_SN")
                and envio.get("Codigo_Plantilla") != "CONSENTIMIENTO"):
            resultado.omitidos.append((identificador, "sin consentimiento registrado"))
            continue
        # Solo bloquea una negativa explícita: una celda en blanco en el Excel
        # no puede significar "no quiere correos", o no saldría ninguno.
        if usuario.get("Acepta_Emails_SN") is False:
            resultado.omitidos.append((identificador, "ha pedido no recibir correos"))
            continue

        problemas = comprobar(repo, cfg, envio)
        if problemas:
            # Que falte configurar algo no es un fallo de envío: el correo no
            # estaba listo. Se deja como estaba, con el motivo anotado, para
            # arreglar la causa y volver a darle sin rehacer nada.
            repo.actualizar("T_COLA_MAIL", identificador,
                            {"Error": "; ".join(problemas)})
            resultado.fallidos.append((identificador, "; ".join(problemas)))
            continue

        asunto, html = montar(repo, cfg, envio)
        try:
            documentos = (adjuntos or {}).get(identificador)
            if documentos is None:
                documentos = adjuntos_para(repo, cfg, envio)
        except Exception as error:
            # El cuerpo promete la hoja de entrenamiento: mejor no enviar un
            # correo que dice «te adjunto» sin adjuntar nada.
            motivo = f"no se ha podido generar el documento adjunto: {error}"
            repo.actualizar("T_COLA_MAIL", identificador, {"Error": motivo})
            resultado.fallidos.append((identificador, motivo))
            continue
        try:
            enviador.enviar(usuario["Email"], asunto, html, documentos)
        except Exception as error:
            repo.actualizar("T_COLA_MAIL", identificador,
                            {"Estado": "ERROR", "Error": str(error)})
            resultado.fallidos.append((identificador, str(error)))
            continue

        repo.actualizar("T_COLA_MAIL", identificador, {
            "Estado": "ENVIADO", "F_Envio": datetime.now(),
            "Asunto_Final": asunto, "Cuerpo_Final": html,
            "Aprobado_Por": aprobado_por, "Error": ""})
        resultado.enviados.append(identificador)
    return resultado


# --- Modo vacaciones ---------------------------------------------------------

@dataclass
class EstadoVacaciones:
    activo: bool
    caducidad: date | None
    motivo: str = ""


def estado_vacaciones(repo: Repositorio, hoy: date | None = None) -> EstadoVacaciones:
    """Activo solo si está marcado y la fecha de caducidad no ha pasado.

    El riesgo no es activarlo, es olvidarse de desactivarlo, así que caduca solo.
    """
    hoy = hoy or date.today()
    activo = repo.config("modo_vacaciones", "NO").upper() in ("SI", "SÍ", "1")
    texto = repo.config("caducidad_modo_vacaciones", "").strip()
    caducidad = None
    if texto:
        try:
            from ..nucleo.fechas import a_fecha
            caducidad = a_fecha(texto)
        except ValueError:
            caducidad = None
    if not activo:
        return EstadoVacaciones(False, caducidad)
    if caducidad is None:
        return EstadoVacaciones(False, None,
                                "activado sin fecha de caducidad: no se aplica")
    if caducidad < hoy:
        return EstadoVacaciones(False, caducidad,
                                f"caducó el {formatear(caducidad)}")
    return EstadoVacaciones(True, caducidad)


def enviar_en_vacaciones(repo: Repositorio, cfg: Config,
                         enviador: srv_correo.Enviador,
                         hoy: date | None = None) -> ResultadoEnvio:
    """Envío sin revisión, con todas las salvaguardas de docs/04."""
    hoy = hoy or date.today()
    estado = estado_vacaciones(repo, hoy)
    if not estado.activo:
        return ResultadoEnvio([], [], [("-", estado.motivo or "modo vacaciones apagado")])

    tope = int(repo.config("tope_envios_dia", str(cfg.correo.tope_envios_dia)))
    enviados_hoy = sum(
        1 for e in repo.listar("T_COLA_MAIL", lambda e: e.get("Estado") == "ENVIADO")
        if isinstance(e.get("F_Envio"), datetime) and e["F_Envio"].date() == hoy)

    aptas = {p["Codigo"] for p in repo.listar("T_PLANTILLAS_MAIL")
             if p.get("Permite_Modo_Vacaciones_SN")}
    elegidos, omitidos = [], []
    for envio in pendientes(repo):
        if envio.get("F_Programada") and envio["F_Programada"] > hoy:
            continue
        if envio.get("Estado") == "ERROR":
            # Sin nadie delante, reintentar a ciegas lo que ya falló solo
            # repetiría el error todos los días.
            omitidos.append((envio["ID_Envio"],
                             "quedó en error: necesita que lo revises"))
            continue
        if envio.get("Codigo_Plantilla") not in aptas:
            omitidos.append((envio["ID_Envio"],
                             "su plantilla exige revisión: espera a la vuelta"))
            continue
        if enviados_hoy + len(elegidos) >= tope:
            omitidos.append((envio["ID_Envio"], f"tope diario de {tope} alcanzado"))
            continue
        elegidos.append(envio["ID_Envio"])

    resultado = enviar(repo, cfg, enviador, elegidos, aprobado_por="MODO_VACACIONES")
    resultado.omitidos.extend(omitidos)
    return resultado


def resumen_diario(repo: Repositorio, hoy: date | None = None) -> str:
    """Lo que ha salido hoy sin supervisión, para no volver a ciegas."""
    hoy = hoy or date.today()
    salidos = [e for e in repo.listar("T_COLA_MAIL",
                                      lambda e: e.get("Aprobado_Por") == "MODO_VACACIONES")
               if isinstance(e.get("F_Envio"), datetime) and e["F_Envio"].date() == hoy]
    if not salidos:
        return "Hoy no ha salido ningún correo automático."
    lineas = [f"{len(salidos)} correos enviados hoy en modo vacaciones:"]
    for envio in salidos:
        usuario = repo.obtener("T_USUARIOS", envio.get("ID_Usuario")) or {}
        lineas.append(f"  · {envio.get('Codigo_Plantilla')} → "
                      f"{usuario.get('Nombre')} {usuario.get('Apellidos') or ''}".rstrip())
    return "\n".join(lineas)
