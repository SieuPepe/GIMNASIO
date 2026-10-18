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
        # Se simula el modo empaquetado sin tener que empaquetar. No se mira a
        # qué carpeta concreta va —eso lo decide Windows y cambia de un equipo
        # a otro— sino que salga de Documentos y no de dentro del programa.
        import importlib
        from unittest import mock
        with mock.patch.object(sys, "frozen", True, create=True), \
             mock.patch.object(sys, "_MEIPASS", str(RAIZ), create=True):
            recargado = importlib.reload(config)
            carpeta = recargado.CARPETA_DATOS
            documentos = recargado.carpeta_documentos()
            esta_empaquetado = recargado.empaquetado()
            raiz = recargado.RAIZ
            libro = recargado.Config().datos.libro
        importlib.reload(config)      # ya sin el parche puesto

        self.assertTrue(esta_empaquetado)
        self.assertEqual(raiz, RAIZ)
        self.assertNotEqual(carpeta, raiz)
        self.assertEqual(carpeta, documentos / config.NOMBRE_CARPETA)
        self.assertEqual(libro.parent, carpeta)

    def test_resolver_la_ruta_no_crea_carpetas(self):
        # Importar un módulo no debería dejar carpetas sueltas por el disco.
        import importlib
        import tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory() as temporal:
            inventada = Path(temporal) / "no_deberia_existir"
            with mock.patch.dict("os.environ", {"KRV_DATOS": str(inventada)}):
                recargado = importlib.reload(config)
                self.assertEqual(recargado.CARPETA_DATOS, inventada)
                self.assertFalse(inventada.exists())
                # Y cuando de verdad se va a escribir, se crea.
                self.assertTrue(recargado.asegurar_carpeta_datos().exists())
            importlib.reload(config)

    def test_la_carpeta_de_datos_se_puede_llevar_a_otro_sitio(self):
        # Para quien quiera el libro en una unidad de red, por ejemplo.
        import importlib
        import tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory() as temporal:
            with mock.patch.dict("os.environ", {"KRV_DATOS": temporal}):
                recargado = importlib.reload(config)
                self.assertEqual(recargado.CARPETA_DATOS, Path(temporal))
                self.assertEqual(recargado.Config().datos.libro.parent,
                                 Path(temporal))
            importlib.reload(config)

    def test_la_carpeta_de_documentos_es_una_carpeta_de_verdad(self):
        documentos = config.carpeta_documentos()
        self.assertTrue(documentos.is_absolute())
        self.assertTrue(documentos.exists())


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


class CodigoLimpio(unittest.TestCase):
    """Avisos del propio Python que es facil dejar pasar.

    Una ruta de Windows dentro de una cadena normal («Documentos\\Kevin...»)
    deja un aviso de secuencia de escape invalida que ensucia cada arranque y
    que en alguna version futura de Python pasara a ser un error.
    """

    def test_ningun_fichero_deja_avisos_al_compilar(self):
        import warnings
        problemas = []
        for fichero in sorted(RAIZ.rglob("*.py")):
            if any(p in fichero.parts for p in (".venv", "__pycache__", "build",
                                                "dist")):
                continue
            with warnings.catch_warnings(record=True) as avisos:
                warnings.simplefilter("always")
                compile(fichero.read_text(encoding="utf-8"), str(fichero), "exec")
            for aviso in avisos:
                problemas.append(
                    f"{fichero.relative_to(RAIZ)}:{aviso.lineno}: {aviso.message}")
        self.assertEqual(problemas, [])


class GuionesDePowerShell(unittest.TestCase):
    """Lo que rompió el guion en Windows y no se veía aquí.

    Windows PowerShell 5, con ErrorActionPreference en «Stop», convierte en
    error propio todo lo que un programa escriba por la salida de errores,
    aunque termine bien. unittest, pip y PyInstaller la usan para sus mensajes
    normales, así que el guion se paraba en seco en cuanto cualquiera hablaba.
    La solución es llamarlos siempre a través de `Ejecuta`.
    """

    GUIONES = ("instalar.ps1", "construir.ps1")

    def test_los_dos_guiones_llevan_el_ayudante(self):
        for nombre in self.GUIONES:
            with self.subTest(nombre):
                texto = (RAIZ / nombre).read_text(encoding="utf-8")
                self.assertIn("function Ejecuta", texto)

    def test_no_queda_ninguna_llamada_externa_sin_proteger(self):
        # Un «& $algo» suelto es justo lo que reventaba.
        suelta = re.compile(r'^\s*&\s*\$(?!null)', re.MULTILINE)
        for nombre in self.GUIONES:
            with self.subTest(nombre):
                texto = (RAIZ / nombre).read_text(encoding="utf-8")
                dentro_de_ejecuta = texto.split("function Ejecuta", 1)[1]
                fin = dentro_de_ejecuta.index("\n}")
                resto = (texto.split("function Ejecuta", 1)[0]
                         + dentro_de_ejecuta[fin:])
                self.assertEqual(suelta.findall(resto), [],
                                 "hay llamadas externas fuera de Ejecuta")

    def test_nadie_usa_el_truco_de_tragarse_los_errores(self):
        # «2>$null» no basta en PowerShell 5: el error salta igual.
        for nombre in self.GUIONES:
            with self.subTest(nombre):
                texto = (RAIZ / nombre).read_text(encoding="utf-8")
                self.assertNotIn("2>$null", texto)

    def test_construir_pasa_las_pruebas_antes_de_empaquetar(self):
        texto = (RAIZ / "construir.ps1").read_text(encoding="utf-8")
        orden_pruebas = texto.index("unittest")
        orden_paquete = texto.index("PyInstaller', (Join-Path")
        self.assertLess(orden_pruebas, orden_paquete,
                        "empaquetar algo roto es perder media hora")

    def test_hay_pruebas_del_propio_instalador(self):
        prueba = RAIZ / "pruebas" / "test_instalador.ps1"
        self.assertTrue(prueba.exists())
        texto = prueba.read_text(encoding="utf-8")
        for funcion in ("Ejecuta", "Copia-Libro", "Excel-Abierto", "Ruta-Libro"):
            with self.subTest(funcion):
                self.assertIn(funcion, texto)


if __name__ == "__main__":
    unittest.main()
