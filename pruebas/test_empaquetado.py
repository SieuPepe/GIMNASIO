"""Pruebas del empaquetado y del instalador de Windows.

No se puede compilar aquí ni el ejecutable de Windows ni el instalador, pero sí
se puede comprobar lo que más se rompe al mover ficheros de sitio: que el
.spec y el .iss sigan apuntando a cosas que existen, y que el reparto entre
recursos y datos del usuario sea el correcto.

    python -m unittest discover -s pruebas
"""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from krv.nucleo import config                                      # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
SPEC = RAIZ / "krv.spec"
ISS = RAIZ / "instalador" / "krv.iss"


class RepartoDeCarpetas(unittest.TestCase):
    """Los recursos van dentro del programa; lo del usuario, fuera.

    Si esto se mezcla, el programa instalado intenta escribir en «Archivos de
    programa» y Windows no le deja.
    """

    def test_sin_empaquetar_todo_esta_en_el_proyecto(self):
        self.assertFalse(config.empaquetado())
        self.assertEqual(config.RAIZ, config.CARPETA_DATOS)
        self.assertEqual(config.RAIZ, RAIZ)

    def test_los_recursos_estan_donde_dice_la_raiz(self):
        for relativa in ("datos_iniciales/ejercicios.csv",
                         "assets/marca/kevin.ico",
                         "config.ejemplo.toml"):
            with self.subTest(relativa):
                self.assertTrue((config.RAIZ / relativa).exists())

    def test_el_libro_cuelga_de_la_carpeta_de_datos(self):
        cfg = config.Config()
        self.assertEqual(cfg.datos.libro.parent, config.CARPETA_DATOS)
        self.assertEqual(cfg.datos.backups.parent, config.CARPETA_DATOS)

    def test_empaquetado_los_datos_no_van_dentro_del_programa(self):
        # Se simula el modo empaquetado sin tener que empaquetar, y con un
        # «home» de mentira para no dejar carpetas sueltas por ahí.
        import importlib
        import tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory() as casa:
            documentos = Path(casa) / "Documents"
            documentos.mkdir()
            try:
                with mock.patch.object(sys, "frozen", True, create=True), \
                     mock.patch.object(sys, "_MEIPASS", str(RAIZ), create=True), \
                     mock.patch.object(Path, "home", staticmethod(lambda: Path(casa))):
                    recargado = importlib.reload(config)
                    self.assertTrue(recargado.empaquetado())
                    self.assertEqual(recargado.RAIZ, RAIZ)
                    self.assertNotEqual(recargado.CARPETA_DATOS, recargado.RAIZ)
                    self.assertEqual(recargado.CARPETA_DATOS,
                                     documentos / recargado.NOMBRE_CARPETA)
                    self.assertTrue(recargado.CARPETA_DATOS.exists())
                    # Y el libro por defecto cae ahí, no en el programa.
                    self.assertEqual(recargado.Config().datos.libro.parent,
                                     recargado.CARPETA_DATOS)
            finally:
                # El parche ya no está puesto: esta recarga deja el módulo bien.
                importlib.reload(config)


class Spec(unittest.TestCase):
    """El .spec de PyInstaller."""

    @classmethod
    def setUpClass(cls):
        cls.texto = SPEC.read_text(encoding="utf-8")

    def test_existe(self):
        self.assertTrue(SPEC.exists())

    def test_arranca_por_el_lanzador_y_no_por_el_modulo(self):
        # Lanzar krv/__main__.py directamente rompe sus imports relativos.
        self.assertIn('"arrancar.py"', self.texto)
        self.assertNotIn('"__main__.py"', self.texto)
        self.assertTrue((RAIZ / "arrancar.py").exists())

    def test_empaqueta_los_recursos_que_el_programa_busca(self):
        for recurso in ("datos_iniciales", "assets", "config.ejemplo.toml"):
            with self.subTest(recurso):
                self.assertIn(recurso, self.texto)

    def test_no_empaqueta_los_datos_del_usuario(self):
        # El libro y las credenciales son del usuario: no viajan en el programa.
        for prohibido in ("datos_krv.xlsx", '".env"', "config.toml\""):
            with self.subTest(prohibido):
                self.assertNotIn(prohibido, self.texto)

    def test_sale_sin_consola(self):
        self.assertIn("console=False", self.texto)

    def test_lleva_el_icono(self):
        self.assertIn("kevin.ico", self.texto)
        self.assertTrue((RAIZ / "assets" / "marca" / "kevin.ico").exists())


class Instalador(unittest.TestCase):
    """El guion de Inno Setup."""

    @classmethod
    def setUpClass(cls):
        cls.texto = ISS.read_text(encoding="utf-8")

    def test_existe(self):
        self.assertTrue(ISS.exists())

    def test_tiene_las_secciones_imprescindibles(self):
        for seccion in ("[Setup]", "[Files]", "[Icons]", "[Code]", "[Languages]"):
            with self.subTest(seccion):
                self.assertIn(seccion, self.texto)

    def test_los_ficheros_a_los_que_apunta_existen(self):
        # Las rutas del .iss son relativas a su propia carpeta.
        for linea in self.texto.splitlines():
            encontrado = re.search(r'(?:Source|SetupIconFile)[:=]\s*"?([^";]+)"?',
                                   linea)
            if not encontrado:
                continue
            ruta = encontrado.group(1).strip().replace("\\", "/")
            ruta = ruta.split("*")[0]
            destino = (ISS.parent / ruta).resolve()
            if "dist/" in ruta:
                continue        # lo crea PyInstaller justo antes
            with self.subTest(ruta):
                self.assertTrue(destino.exists(), f"no existe {destino}")

    def test_toda_variable_usada_esta_definida(self):
        definidas = set(re.findall(r'#define\s+(\w+)', self.texto))
        usadas = set(re.findall(r'\{#(\w+)\}', self.texto))
        self.assertEqual(usadas - definidas, set())

    def test_instala_sin_pedir_administrador(self):
        # Con UAC de por medio la instalacion falla mas y asusta mas.
        self.assertIn("PrivilegesRequired=lowest", self.texto)

    def test_guarda_copia_del_libro_antes_de_nada(self):
        self.assertIn("CopiaDeSeguridad", self.texto)
        self.assertIn("CopiaHecha := CopiaDeSeguridad()", self.texto)

    def test_se_planta_si_el_libro_esta_abierto_en_excel(self):
        self.assertIn("~$datos_krv.xlsx", self.texto)

    def test_la_instalacion_desde_cero_no_borra_el_libro_lo_aparta(self):
        # Borrar es irreversible; renombrar deja el fichero ahi por si acaso.
        self.assertIn("RenameFile(RutaLibro()", self.texto)
        self.assertNotIn("DeleteFile(RutaLibro()", self.texto)

    def test_el_desinstalador_no_toca_los_datos(self):
        self.assertNotIn("[UninstallDelete]", self.texto)
        self.assertIn("Tus datos NO se borran", self.texto)

    def test_las_dos_opciones_estan_en_la_pagina(self):
        self.assertIn("Instalacion desde cero", self.texto)
        self.assertIn("Actualizar la version", self.texto)

    def test_el_nombre_de_la_carpeta_coincide_con_el_del_programa(self):
        # Si no, el instalador haria la copia en un sitio y el programa leeria
        # de otro.
        definido = re.search(r'#define\s+CarpetaDatos\s+"([^"]+)"', self.texto)
        self.assertIsNotNone(definido)
        self.assertEqual(definido.group(1), config.NOMBRE_CARPETA)

    def test_el_ejecutable_coincide_con_el_que_produce_el_spec(self):
        definido = re.search(r'#define\s+Ejecutable\s+"([^"]+)"', self.texto)
        nombre = definido.group(1).replace(".exe", "")
        self.assertIn(f'name="{nombre}"', SPEC.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
