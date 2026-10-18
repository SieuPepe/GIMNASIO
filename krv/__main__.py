"""Punto de entrada de la aplicación Kevin Ruiz Valdenegro."""

from __future__ import annotations

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from .datos import libro as mod_libro
from .nucleo import config, log
from .ui import asistente, estilo
from .ui.principal import VentanaPrincipal


def main() -> int:
    log.configurar(config.RAIZ / "logs")
    registro = log.obtener("app")

    # La ventana de aviso tiene que existir antes que el primer error, así que
    # la aplicación de Qt se crea antes de leer nada.
    app = QApplication(sys.argv)
    try:
        cfg = config.cargar()
    except config.ConfigIlegible as error:
        registro.error("Configuración ilegible: %s", error.causa)
        QMessageBox.critical(None, "No se puede leer la configuración", str(error))
        return 1
    app.setApplicationName(cfg.negocio.nombre_comercial)
    if estilo.ICONO.exists():
        app.setWindowIcon(QIcon(str(estilo.ICONO)))
    app.setStyleSheet(estilo.HOJA)

    if not cfg.datos.libro.exists():
        QMessageBox.critical(
            None, "Falta el libro de datos",
            f"No se encuentra {cfg.datos.libro}.\n\n"
            "Créalo ejecutando:\n    python herramientas/crear_libro.py")
        return 1

    libro = mod_libro.Libro(cfg.datos.libro, cfg.datos.backups,
                            cfg.datos.copias_a_conservar)
    try:
        libro.cargar()
    except mod_libro.EsquemaDesactualizado as desfase:
        # El libro se creó con una versión anterior. No hay que rehacer nada:
        # se añade lo que falta conservando los datos, con copia previa.
        respuesta = QMessageBox.question(
            None, "El libro es de una versión anterior",
            f"Al libro le falta {desfase.resumen()} que esta versión necesita.\n\n"
            "Se pueden añadir sin tocar tus datos, y antes se hace una copia de "
            "seguridad.\n\n¿Actualizarlo ahora?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if respuesta != QMessageBox.Yes:
            return 1
        try:
            cambios = mod_libro.migrar(cfg.datos.libro, cfg.datos.backups)
            libro.cargar()
        except Exception as error:
            registro.exception("No se ha podido actualizar el libro")
            QMessageBox.critical(None, "No se ha podido actualizar", str(error))
            return 1
        registro.info("Libro actualizado: %s", ", ".join(cambios))
    except Exception as error:
        registro.exception("No se ha podido cargar el libro")
        QMessageBox.critical(None, "No se ha podido abrir el libro", str(error))
        return 1

    if mod_libro.esta_abierto_en_excel(cfg.datos.libro):
        QMessageBox.warning(
            None, "El libro está abierto en Excel",
            "Puedes consultar datos, pero no podrás guardar hasta que cierres Excel.\n\n"
            "Para mirar los datos mientras trabajas, abre una copia y no el original.")

    # La primera vez no hay cuenta de correo: se pregunta antes de abrir nada.
    if asistente.hace_falta():
        from .datos.repositorio import Repositorio
        paso = asistente.Asistente(cfg, Repositorio(libro))
        if paso.exec():
            try:
                libro.guardar()
            except Exception as error:
                registro.exception("No se ha podido guardar tras el asistente")
                QMessageBox.warning(None, "No se ha podido guardar", str(error))

    ventana = VentanaPrincipal(cfg, libro)
    ventana.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
