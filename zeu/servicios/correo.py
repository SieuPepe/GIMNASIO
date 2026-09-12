"""Envío de correo y montaje de los cuerpos a partir de plantillas.

SMTP directo de Gmail con contraseña de aplicación. Ver docs/04.
"""

from __future__ import annotations

import re
import smtplib
import ssl
import time
from dataclasses import dataclass, field
from email.message import EmailMessage
from pathlib import Path

from ..nucleo import config, log

_log = log.obtener("servicios.correo")

MARCADOR = re.compile(r"\{\{\s*([a-z_0-9]+)\s*\}\}", re.IGNORECASE)
# Bloque condicional: {{#clave}}...{{/clave}} solo sale si la clave tiene valor.
SECCION = re.compile(r"\{\{#\s*([a-z_0-9]+)\s*\}\}(.*?)\{\{/\s*\1\s*\}\}",
                     re.IGNORECASE | re.DOTALL)

HOJA_ESTILO = """
body{font-family:Segoe UI,Helvetica,Arial,sans-serif;color:#333;line-height:1.55;
     font-size:15px;margin:0;padding:0;background:#F4F6F8}
.marco{max-width:620px;margin:0 auto;background:#fff}
.cabecera{background:#356283;color:#fff;padding:20px 26px}
.cabecera h1{margin:0;font-size:22px;letter-spacing:1px}
.cabecera p{margin:4px 0 0;font-size:12px;color:#A9C4D6;letter-spacing:2px;
            text-transform:uppercase}
.cuerpo{padding:24px 26px}
.nota{background:#D9E4EC;border-left:4px solid #4A7FA5;padding:12px 16px;margin:18px 0}
.boton{display:inline-block;background:#4A7FA5;color:#fff !important;text-decoration:none;
       padding:12px 26px;border-radius:4px;font-weight:bold;margin:18px 0}
.pie{padding:16px 26px;color:#8A959D;font-size:12px;border-top:1px solid #E2E8EC}
"""


def rellenar(plantilla: str, valores: dict[str, str]) -> str:
    """Sustituye {{marcador}} por su valor y resuelve los bloques condicionales.

    Lo que no se conoce se deja vacío: un párrafo entero que dependa de un dato
    ausente desaparece en lugar de quedarse a medias.
    """
    texto = plantilla or ""

    def seccion(coincidencia: re.Match) -> str:
        clave = coincidencia.group(1).lower()
        return coincidencia.group(2) if valores.get(clave) else ""
    texto = SECCION.sub(seccion, texto)

    def cambiar(coincidencia: re.Match) -> str:
        clave = coincidencia.group(1).lower()
        return str(valores.get(clave, "") or "")
    return MARCADOR.sub(cambiar, texto)


def marcadores_sin_resolver(texto: str) -> list[str]:
    """Un {{marcador}} sin sustituir en el correo delata al robot. Se comprueba."""
    return sorted({m.group(1) for m in MARCADOR.finditer(texto or "")})


def envolver(cuerpo_html: str, nombre_comercial: str, lema: str,
             pie: str = "") -> str:
    """Mete el cuerpo dentro de la plantilla visual de la marca."""
    return f"""<html><head><meta charset="utf-8"><style>{HOJA_ESTILO}</style></head>
<body><div class="marco">
  <div class="cabecera"><h1>{nombre_comercial}</h1><p>{lema}</p></div>
  <div class="cuerpo">{cuerpo_html}</div>
  <div class="pie">{pie or f'{nombre_comercial} · {lema}'}</div>
</div></body></html>"""


def enlace_prerrellenado(url: str, id_usuario: str, id_envio: str) -> str:
    """El enlace del formulario con los campos ocultos ya puestos.

    Se espera la URL de «respuesta prerrellenada» de Google Forms con
    {{id_usuario}} y {{id_envio}} en el lugar de los valores. Así el usuario no
    tiene que identificarse y cada respuesta queda atada a su envío.
    """
    return rellenar(url or "", {"id_usuario": id_usuario, "id_envio": id_envio})


# --- Envío -------------------------------------------------------------------

@dataclass
class Resultado:
    enviados: int = 0
    errores: list[tuple[str, str]] = field(default_factory=list)


class Enviador:
    """Interfaz de envío. La implementación real habla con Gmail."""

    def enviar(self, destinatario: str, asunto: str, html: str,
               adjuntos: list[Path] | None = None) -> None:
        raise NotImplementedError


class EnviadorSimulado(Enviador):
    """No envía nada: guarda lo que se le pide. Para pruebas y vista previa."""

    def __init__(self):
        self.enviados: list[dict] = []

    def enviar(self, destinatario, asunto, html, adjuntos=None) -> None:
        self.enviados.append({"para": destinatario, "asunto": asunto,
                              "html": html, "adjuntos": list(adjuntos or [])})


class EnviadorSMTP(Enviador):
    def __init__(self, cfg: config.Config, pausa_seg: float = 2.0):
        self.cfg = cfg
        self.pausa = pausa_seg
        self.remitente = (cfg.correo.remitente
                          or config.credencial("GMAIL_USUARIO", obligatoria=True))
        self.contrasena = config.credencial("GMAIL_APP_PASSWORD", obligatoria=True)

    def _mensaje(self, destinatario, asunto, html, adjuntos) -> EmailMessage:
        mensaje = EmailMessage()
        mensaje["From"] = f"{self.cfg.negocio.nombre_comercial} <{self.remitente}>"
        mensaje["To"] = destinatario
        mensaje["Subject"] = asunto
        mensaje.set_content(
            "Este mensaje se ve mejor en un cliente que admita formato HTML.")
        mensaje.add_alternative(html, subtype="html")
        for ruta in adjuntos or []:
            ruta = Path(ruta)
            if not ruta.exists():
                continue
            mensaje.add_attachment(ruta.read_bytes(), maintype="application",
                                   subtype="pdf", filename=ruta.name)
        return mensaje

    def enviar(self, destinatario, asunto, html, adjuntos=None) -> None:
        contexto = ssl.create_default_context()
        with smtplib.SMTP_SSL(self.cfg.correo.smtp_host,
                              self.cfg.correo.smtp_puerto, context=contexto) as servidor:
            servidor.login(self.remitente, self.contrasena)
            servidor.send_message(self._mensaje(destinatario, asunto, html, adjuntos))
        _log.info("Correo enviado a %s: %s", destinatario, asunto)
        # Espaciar los envíos en lote: una ráfaga parece un emisor masivo.
        if self.pausa:
            time.sleep(self.pausa)


def probar_conexion(cfg: config.Config) -> tuple[bool, str]:
    """Comprueba las credenciales sin enviar nada."""
    try:
        remitente = (cfg.correo.remitente
                     or config.credencial("GMAIL_USUARIO", obligatoria=True))
        contrasena = config.credencial("GMAIL_APP_PASSWORD", obligatoria=True)
    except RuntimeError as error:
        return False, str(error)
    try:
        contexto = ssl.create_default_context()
        with smtplib.SMTP_SSL(cfg.correo.smtp_host, cfg.correo.smtp_puerto,
                              context=contexto, timeout=15) as servidor:
            servidor.login(remitente, contrasena)
        return True, f"Conexión correcta con {remitente}"
    except smtplib.SMTPAuthenticationError:
        return False, ("Gmail rechaza las credenciales. Recuerda que hace falta una "
                       "contraseña de aplicación de 16 caracteres, no la contraseña "
                       "de la cuenta, y tener activada la verificación en dos pasos.")
    except Exception as error:
        return False, f"No se ha podido conectar: {error}"
