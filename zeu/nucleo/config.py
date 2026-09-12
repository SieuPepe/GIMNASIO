"""Configuración de la aplicación: config.toml y .env.

Los parámetros no sensibles viven en config.toml; las credenciales en .env,
que nunca entra en el repositorio. Todo el acceso a credenciales pasa por
`credencial()`, de modo que cambiar .env por el almacén de credenciales de
Windows sería tocar una sola función.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


@dataclass
class Negocio:
    nombre_comercial: str = "ZEU"
    lema: str = "Enjoy your process"
    horario_sala: str = ""
    contacto: str = ""


@dataclass
class Datos:
    libro: Path = RAIZ / "datos_zeu.xlsx"
    backups: Path = RAIZ / "backups"
    copias_a_conservar: int = 30


@dataclass
class Correo:
    remitente: str = ""
    smtp_host: str = "smtp.gmail.com"
    smtp_puerto: int = 465
    dias_aviso_previo: int = 14
    modo_vacaciones: bool = False
    caducidad_modo_vacaciones: str = ""
    tope_envios_dia: int = 20


@dataclass
class IA:
    url_ollama: str = "http://localhost:11434"
    modelo: str = "qwen2.5:7b-instruct"


@dataclass
class Config:
    negocio: Negocio = field(default_factory=Negocio)
    datos: Datos = field(default_factory=Datos)
    correo: Correo = field(default_factory=Correo)
    ia: IA = field(default_factory=IA)
    ruta_config: Path | None = None


def _aplicar(destino, valores: dict) -> None:
    """Copia al dataclass solo las claves que existen, respetando su tipo."""
    for clave, valor in valores.items():
        if not hasattr(destino, clave):
            continue
        actual = getattr(destino, clave)
        if isinstance(actual, Path):
            valor = Path(valor).expanduser()
        elif isinstance(actual, bool):
            valor = bool(valor)
        elif isinstance(actual, int) and not isinstance(valor, bool):
            valor = int(valor)
        setattr(destino, clave, valor)


def cargar(ruta: Path | None = None) -> Config:
    """Lee config.toml. Si no existe, devuelve la configuración por defecto."""
    cfg = Config()
    ruta = ruta or RAIZ / "config.toml"
    if ruta.exists():
        datos = tomllib.loads(ruta.read_text(encoding="utf-8"))
        for seccion in ("negocio", "datos", "correo", "ia"):
            if seccion in datos:
                _aplicar(getattr(cfg, seccion), datos[seccion])
        cfg.ruta_config = ruta
    return cfg


# --- Credenciales ------------------------------------------------------------

_ENV_CARGADO = False


def _cargar_env(ruta: Path | None = None) -> None:
    """Vuelca el .env en el entorno del proceso. No sobreescribe lo ya definido."""
    global _ENV_CARGADO
    ruta = ruta or RAIZ / ".env"
    if not ruta.exists():
        _ENV_CARGADO = True
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, _, valor = linea.partition("=")
        clave, valor = clave.strip(), valor.strip().strip('"').strip("'")
        os.environ.setdefault(clave, valor)
    _ENV_CARGADO = True


def credencial(nombre: str, obligatoria: bool = False) -> str:
    """Único punto de acceso a credenciales. Ver docs/03."""
    if not _ENV_CARGADO:
        _cargar_env()
    valor = os.environ.get(nombre, "")
    if obligatoria and not valor:
        raise RuntimeError(
            f"Falta la credencial {nombre}. Defínela en el fichero .env "
            f"(hay una plantilla en .env.ejemplo)."
        )
    return valor
