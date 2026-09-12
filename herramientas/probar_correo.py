"""Comprueba la configuración de correo sin enviar nada a nadie.

    python herramientas/probar_correo.py            # solo comprueba la conexión
    python herramientas/probar_correo.py --enviar   # además se manda un correo a ti mismo
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zeu.nucleo import config, log                  # noqa: E402
from zeu.servicios import correo as srv             # noqa: E402


def _oculta(valor: str) -> str:
    """Enseña lo justo para reconocerla sin dejarla escrita en pantalla."""
    if not valor:
        return "(vacía)"
    limpio = valor.replace(" ", "")
    return f"{limpio[:2]}{'·' * (len(limpio) - 4)}{limpio[-2:]}  ({len(limpio)} caracteres)"


def main() -> int:
    cfg = config.cargar()
    log.configurar(config.RAIZ / "logs")
    enviar = "--enviar" in sys.argv

    ruta_env = config.RAIZ / ".env"
    print(f"Fichero .env       {'encontrado' if ruta_env.exists() else 'NO EXISTE en ' + str(ruta_env)}")
    if not ruta_env.exists():
        print("\nCópialo de la plantilla y rellénalo:")
        print("    Copy-Item .env.ejemplo .env")
        return 1

    usuario = cfg.correo.remitente or config.credencial("GMAIL_USUARIO")
    contrasena = config.credencial("GMAIL_APP_PASSWORD")
    print(f"Remitente          {usuario or '(vacío)'}")
    print(f"Contraseña         {_oculta(contrasena)}")
    print(f"Servidor           {cfg.correo.smtp_host}:{cfg.correo.smtp_puerto}")

    if not usuario or not contrasena:
        print("\nFalta GMAIL_USUARIO o GMAIL_APP_PASSWORD en el .env.")
        return 1
    if len(contrasena.replace(" ", "")) != 16:
        print("\nAviso: una contraseña de aplicación de Google tiene 16 caracteres. "
              "Si has puesto la contraseña de tu cuenta, Google la rechazará.")

    print("\nConectando…")
    correcto, mensaje = srv.probar_conexion(cfg)
    print(("OK   " if correcto else "ERROR") + f"  {mensaje}")
    if not correcto:
        return 1

    if enviar:
        print("\nEnviándote un correo de prueba a ti mismo…")
        html = srv.envolver(
            "<p>Si lees esto, el correo de ZEU funciona.</p>"
            "<p>Este mensaje lo ha enviado <code>herramientas/probar_correo.py</code>.</p>",
            cfg.negocio.nombre_comercial, cfg.negocio.lema)
        try:
            srv.EnviadorSMTP(cfg, pausa_seg=0).enviar(
                usuario, f"[PRUEBA] {cfg.negocio.nombre_comercial}", html)
        except Exception as error:
            print(f"ERROR  No se ha podido enviar: {error}")
            return 1
        print(f"OK     Enviado a {usuario}. Revisa la bandeja de entrada.")
    else:
        print("\n(Con --enviar además te mandas un correo de prueba a ti mismo.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
