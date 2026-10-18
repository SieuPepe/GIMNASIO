"""Punto de entrada de la aplicación Kevin Ruiz Valdenegro."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from .datos import libro as mod_libro
from .nucleo import config, log
from .ui import asistente, estilo
from .ui.principal import VentanaPrincipal


def comprobar() -> int:
    """Arranca todo sin enseñar nada, para ver si el paquete está completo.

    Lo llama el guion de construcción nada más empaquetar. Un módulo que falte
    dentro del ejecutable no se nota al construir: se nota cuando alguien abre
    el programa, y para entonces ya está instalado en otro ordenador. Esto
    recorre el mismo camino que el arranque de verdad —las ventanas, el libro,
    los PDF y los gráficos— y devuelve 1 si algo falta.
    """
    import os
    import tempfile
    import traceback

    # En Windows hay escritorio y la ventana se construye sin llegar a
    # enseñarse. Sin escritorio —un servidor, o esta comprobación lanzada desde
    # una consola remota— hay que decirle a Qt que dibuje en el vacío.
    if (not sys.platform.startswith("win")
            and not os.environ.get("DISPLAY")
            and not os.environ.get("WAYLAND_DISPLAY")):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    pasos = []
    try:
        # Las bibliotecas pesadas, por su nombre, para que el error diga cuál.
        pasos.append("matplotlib")
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot                                  # noqa: F401
        pasos.append("reportlab")
        import reportlab.pdfgen.canvas                            # noqa: F401
        pasos.append("openpyxl")
        import openpyxl                                           # noqa: F401

        pasos.append("módulos de la aplicación")
        from .datos import puesta_a_punto
        from .datos.repositorio import Repositorio
        from .servicios import informes
        from .ui.asistente import Asistente                       # noqa: F401
        from .ui.vista_manual import VistaManual                  # noqa: F401

        pasos.append("recursos empaquetados")
        for relativa in ("datos_iniciales/ejercicios.csv",
                         "assets/marca/kevin.ico", "config.ejemplo.toml"):
            if not (config.RAIZ / relativa).exists():
                print(f"FALTA el recurso {relativa} en {config.RAIZ}")
                return 1

        app = QApplication.instance() or QApplication(sys.argv)
        app.setStyleSheet(estilo.HOJA)

        with tempfile.TemporaryDirectory() as temporal:
            cfg = config.Config()
            cfg.datos.libro = Path(temporal) / "comprobacion.xlsx"
            cfg.datos.backups = Path(temporal) / "copias"

            pasos.append("crear el libro")
            puesta_a_punto.preparar(cfg, con_demo=False)
            libro = mod_libro.abrir(cfg.datos.libro, cfg.datos.backups)

            pasos.append("construir la ventana")
            ventana = VentanaPrincipal(cfg, libro)
            ventana.vista_manual.mostrar("instalar")

            pasos.append("dibujar un gráfico")
            radar = informes.grafico_radar(
                {"FUERZA": (70, 100), "RESISTENCIA": (55, 100),
                 "MOVILIDAD": (60, 100), "EQUILIBRIO": (80, 100)},
                None, Path(temporal) / "radar.png")
            if radar is None or not radar.exists():
                print("FALLA: no se ha podido dibujar el gráfico")
                return 1

            pasos.append("cerrar")
            ventana.close()
            Repositorio(libro)
    except Exception:
        print(f"FALLA en el paso: {pasos[-1] if pasos else 'arranque'}")
        traceback.print_exc()
        return 1

    print(f"Comprobación correcta: {len(pasos)} pasos, recursos en {config.RAIZ}")
    return 0


def main() -> int:
    log.configurar(config.CARPETA_DATOS / "logs")
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
        # Instalado como programa no hay consola a la que mandar a nadie: si no
        # hay libro, se ofrece crearlo aquí mismo.
        respuesta = QMessageBox.question(
            None, "Todavía no hay libro de datos",
            f"No se encuentra:\n{cfg.datos.libro}\n\n"
            "Puedo crearlo ahora con el catálogo de ejercicios, las pruebas de "
            "valoración, las plantillas y un usuario de ejemplo para que veas "
            "cómo funciona todo.\n\n¿Lo creo?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if respuesta != QMessageBox.Yes:
            return 1
        from .datos import puesta_a_punto
        try:
            hecho = puesta_a_punto.preparar(cfg, con_demo=True)
        except Exception as error:
            registro.exception("No se ha podido crear el libro")
            QMessageBox.critical(None, "No se ha podido crear el libro", str(error))
            return 1
        registro.info("Libro creado: %s", hecho.resumen())
        QMessageBox.information(
            None, "Libro creado",
            f"Listo:\n{hecho.ruta}\n\n{hecho.resumen()}.\n\n"
            "Dentro tienes al usuario «Prueba Demostración» con programas, "
            "valoraciones y correos, para ver el programa funcionando. Se puede "
            "borrar cuando ya no haga falta.")

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
