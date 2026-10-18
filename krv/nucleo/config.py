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
    nombre_comercial: str = "Kevin Ruiz Valdenegro"
    lema: str = "Movimiento es vida"
    horario_sala: str = ""
    contacto: str = "Kevin Ruiz Valdenegro · 644 300 765 · movimientoesvida.krv@gmail.com"


@dataclass
class Datos:
    libro: Path = RAIZ / "datos_krv.xlsx"
    backups: Path = RAIZ / "backups"
    copias_a_conservar: int = 30


@dataclass
class Correo:
    remitente: str = "movimientoesvida.krv@gmail.com"
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


class ConfigIlegible(Exception):
    """config.toml existe pero no se puede entender."""

    def __init__(self, ruta: Path, causa: Exception):
        self.ruta = ruta
        self.causa = causa
        super().__init__(
            f"No se entiende el fichero de configuración:\n{ruta}\n\n"
            f"{causa}\n\n"
            "Cada línea tiene que ser  clave = \"valor\"  y las secciones van "
            "entre corchetes, como [negocio].\n\n"
            "Si no sabes qué ha pasado, la salida más rápida es renombrar ese "
            "fichero: el programa arrancará con los valores de fábrica y podrás "
            "rehacerlo a partir de config.ejemplo.toml.")


def _leer_texto(ruta: Path) -> str:
    """Lee un fichero de texto del usuario sin atragantarse con Windows.

    «utf-8-sig» quita la marca invisible del principio que dejan el Bloc de
    notas y varios comandos de PowerShell. Sin eso, el fichero falla en la
    línea 1, columna 1, con un error que no dice nada.
    """
    try:
        return ruta.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return ruta.read_text(encoding="utf-16")


def cargar(ruta: Path | None = None) -> Config:
    """Lee config.toml. Si no existe, devuelve la configuración por defecto."""
    cfg = Config()
    ruta = ruta or RAIZ / "config.toml"
    if ruta.exists():
        try:
            datos = tomllib.loads(_leer_texto(ruta))
        except (tomllib.TOMLDecodeError, UnicodeDecodeError) as error:
            raise ConfigIlegible(ruta, error) from error
        for seccion in ("negocio", "datos", "correo", "ia"):
            if seccion in datos:
                _aplicar(getattr(cfg, seccion), datos[seccion])
        cfg.ruta_config = ruta
    return cfg


# --- Credenciales ------------------------------------------------------------

_ENV_CARGADO = False
_ENV_ORIGEN: Path | None = None       # de qué fichero se leyó, para poder decirlo
_ENV_CLAVES: tuple[str, ...] = ()     # qué claves traía, para poder decirlo

# El Bloc de notas de Windows añade «.txt» si no se elige «Todos los archivos»,
# y es el tropiezo más habitual al crear el .env. Se acepta ese nombre también,
# en vez de dejar al usuario delante de un error que no explica nada.
NOMBRES_ENV = (".env", ".env.txt")


def ruta_env() -> Path | None:
    """El fichero de credenciales que se va a usar, si existe alguno."""
    for nombre in NOMBRES_ENV:
        candidato = RAIZ / nombre
        if candidato.exists():
            return candidato
    return None


def _cargar_env(ruta: Path | None = None) -> None:
    """Vuelca el .env en el entorno del proceso. No sobreescribe lo ya definido."""
    global _ENV_CARGADO, _ENV_ORIGEN, _ENV_CLAVES
    ruta = ruta or ruta_env()
    _ENV_CARGADO = True
    _ENV_ORIGEN = ruta
    _ENV_CLAVES = ()
    if ruta is None or not ruta.exists():
        return
    # «utf-8-sig» quita la marca invisible que el Bloc de notas puede poner al
    # principio del fichero. Sin esto, la primera clave se lee con tres bytes
    # pegados delante y es como si no estuviera: justo la que falla.
    contenido = _leer_texto(ruta)
    leidas = []
    for linea in contenido.splitlines():
        linea = linea.strip().lstrip("\ufeff")
        if linea.lower().startswith("export "):
            linea = linea[len("export "):].strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, _, valor = linea.partition("=")
        clave = clave.strip().lstrip("\ufeff")
        valor = valor.strip().strip('"').strip("'")
        if not clave:
            continue
        leidas.append(clave)
        if os.environ.get(clave):
            continue          # lo que ya venga del entorno manda
        os.environ[clave] = valor
    _ENV_CLAVES = tuple(leidas)


def diagnostico_env() -> str:
    """Explica dónde se ha buscado el .env y qué se ha encontrado.

    Un «falta la credencial» cuando el fichero está escrito no dice nada útil.
    Esto dice el camino exacto y lo que se ha leído, que es lo que permite ver
    que el fichero se llama «.env.txt» o que está en otra carpeta.
    """
    if _ENV_ORIGEN is None:
        return (f"No se encuentra ningún fichero de credenciales. Tiene que "
                f"llamarse exactamente «.env» y estar en:\n{RAIZ}\n\n"
                "Ojo: el Bloc de notas le añade «.txt» al guardar si no eliges "
                "«Todos los archivos» en el tipo de archivo. Si el tuyo se llama "
                "«.env.txt», renómbralo (aunque así también lo lee).")
    if not _ENV_CLAVES:
        return (f"El fichero {_ENV_ORIGEN} existe pero no se ha podido leer "
                "ninguna línea con el formato CLAVE=valor.")
    return (f"Se ha leído {_ENV_ORIGEN} y contiene: "
            f"{', '.join(_ENV_CLAVES)}.")


def credencial(nombre: str, obligatoria: bool = False) -> str:
    """Único punto de acceso a credenciales. Ver docs/03."""
    if not _ENV_CARGADO:
        _cargar_env()
    valor = os.environ.get(nombre, "")
    if obligatoria and not valor:
        raise RuntimeError(
            f"Falta la credencial {nombre}.\n\n{diagnostico_env()}\n\n"
            "Hay una plantilla en .env.ejemplo."
        )
    return valor
