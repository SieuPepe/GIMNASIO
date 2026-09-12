"""Importación de las respuestas de Google Forms y lo que se hace con ellas.

Las respuestas no se quedan en un informe: vuelven al sistema y modifican el
siguiente plan. Ver docs/08, apartado «Aprovechamiento de las respuestas».
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from ..datos.repositorio import Repositorio
from ..nucleo import log
from ..nucleo.config import Config
from ..nucleo.fechas import a_fecha
from . import ejercicios as srv_ejercicios
from .importacion import leer_csv

_log = log.obtener("servicios.respuestas")

# Palabras que identifican cada pregunta en la cabecera del CSV de Google Forms.
# Así no hace falta que los títulos coincidan al carácter con los de docs/08.
# El orden importa: se comprueban de más específica a más general, porque
# "¿quieres que hablemos para preparar tu próximo ciclo?" contiene las dos.
CLAVES = {
    "SENSACION": ("como te sientes", "fisicamente", "sensacion"),
    "ENERGIA": ("energia",),
    "SUENO": ("descansando", "duermes", "sueno"),
    "MOLESTIAS": ("molestias", "dolores"),
    "GUSTA_MAS": ("mas te ha gustado", "gusta mas"),
    "GUSTA_MENOS": ("menos te ha gustado", "gusta menos"),
    "DIFICULTAD": ("dificultad",),
    "CLARIDAD": ("claros", "claridad"),
    "ADHERENCIA": ("porcentaje de las sesiones", "sesiones has podido", "adherencia"),
    "MOTIVO_FALTAS": ("saltado sesiones", "motivo"),
    "PREFERENCIA_HORARIA": ("duracion de sesion", "franja", "dias te encaja"),
    "QUIERE_CITA": ("hablemos", "quieres que te llame", "cita con"),
    "PROXIMO_CICLO": ("te gustaria trabajar", "te gustaria probar", "proximo ciclo"),
    "OBJETIVO": ("objetivo",),
    "CONSENTIMIENTO": ("autorizo", "autorizacion", "consentimiento"),
}
COLUMNAS_ID = {"ID_Usuario": ("id_usuario", "idusuario", "usuario_id"),
               "ID_Envio": ("id_envio", "idenvio", "envio_id")}
AFIRMATIVOS = ("si", "sí", "autorizo", "si, llamame", "si, por correo", "true", "1")


def _codigo_de(cabecera: str) -> str | None:
    texto = srv_ejercicios.sin_tildes(cabecera)
    for codigo, palabras in CLAVES.items():
        if any(palabra in texto for palabra in palabras):
            return codigo
    return None


def _columna_id(cabecera: str) -> str | None:
    texto = srv_ejercicios.sin_tildes(cabecera).replace(" ", "_")
    for campo, variantes in COLUMNAS_ID.items():
        if any(v in texto for v in variantes):
            return campo
    return None


def _es_afirmativo(valor) -> bool:
    return srv_ejercicios.sin_tildes(valor).strip() in AFIRMATIVOS


@dataclass
class ResultadoRespuestas:
    filas: int = 0
    respuestas: int = 0
    sin_identificar: int = 0
    acciones: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)

    def resumen(self) -> str:
        partes = [f"{self.filas} filas leídas", f"{self.respuestas} respuestas nuevas"]
        if self.sin_identificar:
            partes.append(f"{self.sin_identificar} sin identificar")
        return ", ".join(partes)


def importar(repo: Repositorio, cfg: Config, ruta: Path,
             aplicar_acciones: bool = True) -> ResultadoRespuestas:
    """Lee el CSV de respuestas de Google Forms y lo vuelca al libro."""
    resultado = ResultadoRespuestas()
    filas = leer_csv(ruta)
    if not filas:
        return resultado

    cabeceras = list(filas[0].keys())
    mapa_id = {c: _columna_id(c) for c in cabeceras if _columna_id(c)}
    mapa_preguntas: dict[str, str] = {}
    for cabecera in cabeceras:
        if cabecera in mapa_id:
            continue
        codigo = _codigo_de(cabecera)
        if not codigo:
            continue
        if codigo in mapa_preguntas.values():
            resultado.avisos.append(
                f"Dos columnas apuntan a «{codigo}»; se usa la primera: "
                f"«{cabecera}» se ignora")
            continue
        mapa_preguntas[cabecera] = codigo
    sin_reconocer = [c for c in cabeceras
                     if c not in mapa_id and c not in mapa_preguntas
                     and "marca temporal" not in srv_ejercicios.sin_tildes(c)
                     and "timestamp" not in srv_ejercicios.sin_tildes(c)]
    if sin_reconocer:
        resultado.avisos.append(
            "Columnas que no se han reconocido y no se importan: "
            + ", ".join(sin_reconocer[:6]))

    for fila in filas:
        resultado.filas += 1
        id_usuario = next((fila[c].strip() for c, campo in mapa_id.items()
                           if campo == "ID_Usuario" and fila.get(c)), "")
        id_envio = next((fila[c].strip() for c, campo in mapa_id.items()
                         if campo == "ID_Envio" and fila.get(c)), "")
        if not repo.existe("T_USUARIOS", id_usuario):
            resultado.sin_identificar += 1
            continue
        if id_envio and not repo.existe("T_COLA_MAIL", id_envio):
            id_envio = ""

        marca = next((fila[c] for c in cabeceras
                      if "marca temporal" in srv_ejercicios.sin_tildes(c)
                      or "timestamp" in srv_ejercicios.sin_tildes(c)), "")
        try:
            fecha = a_fecha(marca.split(" ")[0]) if marca else date.today()
        except ValueError:
            fecha = date.today()

        ya_registradas = {
            r.get("Codigo_Pregunta") for r in repo.listar(
                "T_RESPUESTAS",
                lambda r: (r.get("ID_Usuario") == id_usuario
                           and r.get("ID_Envio") == (id_envio or None)))}

        valores: dict[str, str] = {}
        for columna, codigo in mapa_preguntas.items():
            valor = (fila.get(columna) or "").strip()
            if not valor:
                continue
            valores[codigo] = valor
            if codigo in ya_registradas:
                continue
            repo.insertar("T_RESPUESTAS", {
                "ID_Usuario": id_usuario, "ID_Envio": id_envio or None,
                "F_Respuesta": datetime.combine(fecha, datetime.min.time()),
                "Codigo_Pregunta": codigo, "Valor": valor, "Origen": "FORM"})
            resultado.respuestas += 1

        if id_envio:
            repo.actualizar("T_COLA_MAIL", id_envio, {"Respondido_SN": True})
        if aplicar_acciones:
            resultado.acciones.extend(
                _acciones(repo, cfg, id_usuario, id_envio, valores, fecha))
    return resultado


def _acciones(repo: Repositorio, cfg: Config, id_usuario: str, id_envio: str,
              valores: dict[str, str], fecha: date) -> list[str]:
    """Lo que cada respuesta cambia en el sistema."""
    from . import cola as srv_cola

    hechas: list[str] = []
    usuario = repo.obtener("T_USUARIOS", id_usuario) or {}
    nombre = usuario.get("Nombre") or id_usuario

    if "CONSENTIMIENTO" in valores and _es_afirmativo(valores["CONSENTIMIENTO"]):
        if not usuario.get("Consentimiento_SN"):
            repo.actualizar("T_USUARIOS", id_usuario, {
                "Consentimiento_SN": True, "F_Consentimiento": fecha,
                "Origen_Consentimiento": "FORM"})
            hechas.append(f"{nombre}: consentimiento registrado con fecha "
                          f"{fecha:%d/%m/%Y}")

    if "MOLESTIAS" in valores and not srv_ejercicios.sin_tildes(
            valores["MOLESTIAS"]).startswith("no"):
        hechas.append(f"{nombre}: declara molestias «{valores['MOLESTIAS'][:60]}». "
                      "Revisar antes del siguiente ciclo")

    if "OBJETIVO" in valores and "cambio" in srv_ejercicios.sin_tildes(valores["OBJETIVO"]):
        anterior = next(iter(repo.listar(
            "T_OBJETIVOS", lambda o: (o.get("ID_Usuario") == id_usuario
                                      and o.get("Estado") == "ACTIVO"))), None)
        if anterior:
            repo.actualizar("T_OBJETIVOS", anterior["ID_Objetivo"],
                            {"Estado": "MODIFICADO"})
        repo.insertar("T_OBJETIVOS", {
            "ID_Usuario": id_usuario, "F_Registro": fecha, "Tipo": "OTRO",
            "Descripcion": valores["OBJETIVO"], "Prioridad": 1, "Estado": "ACTIVO"})
        hechas.append(f"{nombre}: objetivo actualizado a «{valores['OBJETIVO'][:50]}»")

    quiere_cita = "QUIERE_CITA" in valores and _es_afirmativo(valores["QUIERE_CITA"])
    if quiere_cita:
        hechas.append(f"{nombre}: quiere hablar contigo. Indícale el horario de sala")

    # Cerrar el bucle: el silencio tras responder es lo que hace que a la
    # siguiente no respondan.
    if valores and not srv_cola._ya_hay(repo, "AGRADECIMIENTO", id_usuario, None):
        envio = repo.obtener("T_COLA_MAIL", id_envio) if id_envio else None
        repo.insertar("T_COLA_MAIL", {
            "ID_Usuario": id_usuario,
            "ID_Asignacion": (envio or {}).get("ID_Asignacion"),
            "Codigo_Plantilla": "AGRADECIMIENTO",
            "F_Generado": datetime.now(), "F_Programada": date.today(),
            "Estado": "BORRADOR",
            "Nota_Entrenador": "",
            "Quiere_Cita": "SI" if quiere_cita else ""})
        hechas.append(f"{nombre}: generado el correo de agradecimiento")
    return hechas


def resumen_usuario(repo: Repositorio, id_usuario: str) -> dict[str, str]:
    """Últimas respuestas de un usuario, una por pregunta."""
    ultimas: dict[str, str] = {}
    for respuesta in repo.listar("T_RESPUESTAS",
                                 lambda r: r.get("ID_Usuario") == id_usuario,
                                 orden="F_Respuesta"):
        ultimas[respuesta["Codigo_Pregunta"]] = respuesta.get("Valor") or ""
    return ultimas
