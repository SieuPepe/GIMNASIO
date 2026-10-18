"""Que ninguna ventana se salga de la pantalla.

El programa se escribe en un monitor grande y se usa en un portátil, o con el
escalado de Windows al 125 %. Entonces una ventana de 760 píxeles de alto ya no
cabe: Qt la centra igual y la barra de título queda por encima del borde, sin
forma de moverla ni de cerrarla con el ratón.

    python -m unittest discover -s pruebas
"""

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QRect                                # noqa: E402
from PySide6.QtWidgets import (                                 # noqa: E402
    QApplication, QDialog, QDialogButtonBox, QLabel, QVBoxLayout,
)

from krv.ui import encaje                                       # noqa: E402

# Un portátil de 1366x768 con el escalado al 125 %, menos la barra de tareas.
PORTATIL = QRect(0, 0, 1092, 574)
# Y uno aún más justo, por si acaso.
PEQUENA = QRect(0, 0, 800, 480)


class VentanasQueNoCaben(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _ventana(self, ancho, alto, x=None, y=None, minimo=None):
        dialogo = QDialog()
        caja = QVBoxLayout(dialogo)
        caja.addWidget(QLabel("contenido"))
        caja.addWidget(QDialogButtonBox(QDialogButtonBox.Ok))
        if minimo:
            dialogo.setMinimumSize(*minimo)
        dialogo.resize(ancho, alto)
        dialogo.show()
        if x is not None:
            dialogo.move(x, y)
        self.app.processEvents()
        self.addCleanup(dialogo.close)
        return dialogo

    def _cabe(self, dialogo, disponible):
        encaje.encajar(dialogo, disponible)
        self.app.processEvents()
        return disponible.contains(dialogo.frameGeometry())

    def test_una_ventana_que_ya_cabe_no_se_toca(self):
        dialogo = self._ventana(400, 300, 100, 100)
        antes = dialogo.geometry()
        self.assertFalse(encaje.encajar(dialogo, PORTATIL))
        self.assertEqual(dialogo.geometry(), antes)

    def test_una_ventana_mas_alta_que_la_pantalla(self):
        # El caso de la valoración: 760 de alto en una pantalla de 574.
        self.assertTrue(self._cabe(self._ventana(1020, 760), PORTATIL))

    def test_una_ventana_mas_ancha_que_la_pantalla(self):
        self.assertTrue(self._cabe(self._ventana(1600, 300), PORTATIL))

    def test_la_ventana_principal_en_un_portatil(self):
        self.assertTrue(self._cabe(self._ventana(1180, 760), PORTATIL))

    def test_el_borde_de_arriba_es_el_que_importa(self):
        # Es lo que se ve: la barra de título por encima del borde superior.
        dialogo = self._ventana(400, 300, 100, -250)
        self.assertTrue(self._cabe(dialogo, PORTATIL))
        self.assertGreaterEqual(dialogo.frameGeometry().y(), PORTATIL.y())

    def test_tambien_los_otros_tres_bordes(self):
        for nombre, (x, y) in (("izquierda", (-300, 100)),
                               ("derecha", (2000, 100)),
                               ("abajo", (100, 2000))):
            with self.subTest(nombre):
                self.assertTrue(self._cabe(self._ventana(400, 300, x, y), PORTATIL))

    def test_un_minimo_mayor_que_la_pantalla_no_lo_impide(self):
        # Varios diálogos fijan un ancho mínimo; si fuera mayor que la pantalla
        # Qt se negaría a encogerlos.
        dialogo = self._ventana(900, 900, None, None, minimo=(900, 900))
        self.assertTrue(self._cabe(dialogo, PEQUENA))

    def test_en_una_pantalla_minuscula_sigue_siendo_usable(self):
        dialogo = self._ventana(1180, 760)
        encaje.encajar(dialogo, PEQUENA)
        self.app.processEvents()
        self.assertGreaterEqual(dialogo.width(), 300)
        self.assertGreaterEqual(dialogo.height(), 300)

    def test_los_botones_siguen_dentro_al_encoger(self):
        # De nada sirve que la ventana quepa si los botones se quedan fuera.
        dialogo = self._ventana(1020, 760)
        encaje.encajar(dialogo, PORTATIL)
        self.app.processEvents()
        for botonera in dialogo.findChildren(QDialogButtonBox):
            self.assertLessEqual(botonera.geometry().bottom(), dialogo.height())


class VentanasDeVerdad(unittest.TestCase):
    """Las ventanas del programa, con sus tamaños reales."""

    @classmethod
    def setUpClass(cls):
        import tempfile
        from krv.datos import libro as ml, plantillas, plantillas_correo, semillas
        from krv.datos.repositorio import Repositorio
        from krv.nucleo import config

        cls.app = QApplication.instance() or QApplication([])
        cls.temporal = tempfile.TemporaryDirectory()
        base = Path(cls.temporal.name)
        ruta = base / "datos.xlsx"
        ml.crear(ruta)
        cls.cfg = config.Config()
        cls.cfg.datos.libro = ruta
        cls.cfg.datos.backups = base / "bk"
        cls.libro = ml.Libro(ruta, cls.cfg.datos.backups)
        cls.libro.cargar()
        semillas.sembrar(cls.libro)
        cls.repo = Repositorio(cls.libro)
        plantillas.crear(cls.repo)
        plantillas_correo.crear(cls.repo)

    @classmethod
    def tearDownClass(cls):
        cls.temporal.cleanup()

    def test_la_ventana_principal_cabe_en_un_portatil(self):
        from krv.ui.principal import VentanaPrincipal
        ventana = VentanaPrincipal(self.cfg, self.libro)
        ventana.show()
        self.app.processEvents()
        try:
            encaje.encajar(ventana, PORTATIL)
            self.app.processEvents()
            self.assertTrue(PORTATIL.contains(ventana.frameGeometry()))
        finally:
            ventana.close()

    def test_los_dialogos_grandes_caben(self):
        from krv.ui.asistente import Asistente
        from krv.ui.ayuda import PanelAyuda
        from krv.ui.ficha_usuario import FichaUsuario
        for nombre, construir in (
                ("FichaUsuario", lambda: FichaUsuario(self.repo)),
                ("Asistente", lambda: Asistente(self.cfg, self.repo)),
                ("PanelAyuda", lambda: PanelAyuda("linea"))):
            with self.subTest(nombre):
                dialogo = construir()
                dialogo.show()
                self.app.processEvents()
                try:
                    encaje.encajar(dialogo, PORTATIL)
                    self.app.processEvents()
                    self.assertTrue(PORTATIL.contains(dialogo.frameGeometry()),
                                    f"{nombre} se sale: {dialogo.frameGeometry()}")
                finally:
                    dialogo.close()


class Vigilancia(unittest.TestCase):
    def test_se_engancha_a_la_aplicacion(self):
        app = QApplication.instance() or QApplication([])
        encaje.instalar(app)
        self.assertIsNotNone(encaje._vigilante)
        encaje.instalar(app)        # llamarlo dos veces no debe duplicarlo

    def test_el_arranque_la_instala(self):
        texto = (Path(__file__).resolve().parents[1] / "krv" / "__main__.py").read_text(
            encoding="utf-8")
        self.assertIn("encaje.instalar(app)", texto)


if __name__ == "__main__":
    unittest.main()
