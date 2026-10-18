"""Pruebas del manual y de la ayuda de ventana.

Lo que se vigila aquí es sobre todo que el texto y la interfaz no se separen:
una página que apunta a una sección que ya no existe, o un recorrido que señala
un widget que alguien ha renombrado, son fallos que no se ven hasta que el
usuario pulsa. Estas pruebas los cazan antes.

    python -m unittest discover -s pruebas
"""

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from krv.ui import ayuda as may                                         # noqa: E402
from krv.ui.ayuda_contenido import (AYUDAS, CAPITULOS, PAGINAS,         # noqa: E402
                                    entrada, titulo_de)
from krv.ui.principal import SECCIONES                                  # noqa: E402
from krv.ui.recorrido import GUIONES, RECORRIDOS                        # noqa: E402

# Las ventanas que tienen que llevar su propia página de ayuda. Si se añade una
# ventana al programa, esta lista es lo que obliga a documentarla.
VENTANAS_ESPERADAS = {
    "inicio", "usuarios", "ejercicios", "valoraciones", "programas",
    "asignaciones", "correo", "manual_ayuda",
    "ficha_usuario", "objetivos", "salud", "disponibilidad",
    "ficha_ejercicio", "sustitutos", "valoracion", "criterios",
    "ciclo", "sesion", "linea", "asignar", "imprimir", "plantillas",
}


class Contenido(unittest.TestCase):
    def test_todas_las_ventanas_tienen_ayuda(self):
        self.assertEqual(VENTANAS_ESPERADAS - set(AYUDAS), set())

    def test_no_hay_ayudas_sin_ventana(self):
        self.assertEqual(set(AYUDAS) - VENTANAS_ESPERADAS, set())

    def test_cada_ayuda_describe_sus_controles(self):
        for clave, ayuda in AYUDAS.items():
            with self.subTest(clave):
                self.assertTrue(ayuda.controles, "sin un solo control explicado")
                self.assertTrue(ayuda.para_que.strip())
                self.assertTrue(ayuda.donde.strip())

    def test_los_capitulos_apuntan_a_algo(self):
        for capitulo in CAPITULOS:
            for clave in capitulo.entradas:
                with self.subTest(f"{capitulo.titulo} / {clave}"):
                    self.assertIsNotNone(entrada(clave))

    def test_no_queda_nada_fuera_del_indice(self):
        indexadas = {c for cap in CAPITULOS for c in cap.entradas}
        self.assertEqual((set(AYUDAS) | set(PAGINAS)) - indexadas, set())

    def test_ver_tambien_no_lleva_a_ninguna_parte(self):
        for clave, ayuda in AYUDAS.items():
            for destino in ayuda.ver_tambien:
                with self.subTest(f"{clave} -> {destino}"):
                    self.assertIsNotNone(entrada(destino))

    def test_las_secciones_existen_de_verdad(self):
        for clave in list(AYUDAS) + list(PAGINAS):
            objeto = entrada(clave)
            if objeto.seccion:
                with self.subTest(clave):
                    self.assertIn(objeto.seccion, SECCIONES)

    def test_los_recorridos_citados_existen(self):
        for clave in list(AYUDAS) + list(PAGINAS):
            objeto = entrada(clave)
            if objeto.recorrido:
                with self.subTest(clave):
                    self.assertIn(objeto.recorrido, RECORRIDOS)

    def test_el_html_sale_completo(self):
        for clave in AYUDAS:
            with self.subTest(clave):
                html = may.a_html(clave)
                self.assertIn(titulo_de(clave), html)
                self.assertGreater(len(html), 500)

    def test_el_html_de_exportacion_no_lleva_enlaces_de_programa(self):
        # El manual guardado se lee fuera de la aplicación: un «abrir esta
        # ventana» ahí no haría nada y solo confundiría.
        for clave in AYUDAS:
            with self.subTest(clave):
                html = may.a_html(clave, con_acciones=False)
                self.assertNotIn(f"{may.ESQUEMA_SECCION}:", html)
                self.assertNotIn(f"{may.ESQUEMA_RECORRIDO}:", html)


class Recorridos(unittest.TestCase):
    def test_cada_recorrido_tiene_pasos_con_texto(self):
        for guion in GUIONES:
            with self.subTest(guion.clave):
                self.assertTrue(guion.pasos)
                self.assertTrue(guion.resumen.strip())
                for paso in guion.pasos:
                    self.assertTrue(paso.titulo.strip())
                    self.assertGreater(len(paso.texto), 40, "explicación demasiado corta")

    def test_el_primer_paso_lleva_a_una_seccion(self):
        # Si el recorrido no empieza llevando a su ventana, el primer paso se
        # pinta sobre la que hubiera abierta y no se entiende nada.
        for guion in GUIONES:
            with self.subTest(guion.clave):
                self.assertIn(guion.pasos[0].seccion, SECCIONES)

    def test_las_secciones_de_los_pasos_existen(self):
        for guion in GUIONES:
            for paso in guion.pasos:
                if paso.seccion:
                    with self.subTest(f"{guion.clave} / {paso.titulo}"):
                        self.assertIn(paso.seccion, SECCIONES)


class ObjetivosDeLosRecorridos(unittest.TestCase):
    """Esta es la prueba que de verdad protege los recorridos.

    Cada paso señala un widget por su ruta de atributos. Si alguien renombra un
    botón, la ruta deja de resolver y el paso se queda sin nada que destacar.
    Aquí se monta la ventana real y se comprueba una por una.
    """

    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        from krv.datos import libro as ml, plantillas, plantillas_correo, semillas
        from krv.datos.repositorio import Repositorio
        from krv.nucleo import config
        from krv.ui.principal import VentanaPrincipal
        import tempfile

        cls.temporal = tempfile.TemporaryDirectory()
        base = Path(cls.temporal.name)
        ruta = base / "datos_krv.xlsx"
        ml.crear(ruta)
        cls.cfg = config.cargar()
        cls.cfg.datos.libro = ruta
        cls.cfg.datos.backups = base / "backups"
        cls.libro = ml.Libro(ruta, cls.cfg.datos.backups)
        cls.libro.cargar()
        semillas.sembrar(cls.libro)
        repo = Repositorio(cls.libro)
        plantillas.crear(repo)
        plantillas_correo.crear(repo)
        cls.libro.guardar()

        cls.app = QApplication.instance() or QApplication([])
        cls.ventana = VentanaPrincipal(cls.cfg, cls.libro)
        cls.ventana.resize(1180, 760)
        cls.ventana.show()

    @classmethod
    def tearDownClass(cls):
        cls.ventana.close()
        cls.temporal.cleanup()

    def test_cada_paso_encuentra_su_widget(self):
        from PySide6.QtWidgets import QWidget
        from krv.ui.recorrido import Recorrido, _Grupo

        for guion in GUIONES:
            guia = Recorrido(self.ventana, guion)
            try:
                for numero, paso in enumerate(guion.pasos, start=1):
                    with self.subTest(f"{guion.clave} paso {numero}: {paso.titulo}"):
                        guia.indice = numero - 1
                        guia._pintar_paso()
                        self.app.processEvents()
                        if paso.objetivo:
                            self.assertIsNotNone(
                                guia._objetivo,
                                f"«{paso.objetivo}» no existe en la ventana")
                            self.assertIsInstance(guia._objetivo, (QWidget, _Grupo))
                            self.assertIsNotNone(
                                guia._hueco(),
                                f"«{paso.objetivo}» no tiene sitio en pantalla")
            finally:
                guia.terminar()

    def test_el_boton_de_ayuda_esta_en_todas_las_vistas(self):
        vistas = ("vista_inicio", "vista_usuarios", "vista_ejercicios",
                  "vista_valoraciones", "vista_programas", "vista_asignaciones",
                  "vista_correo", "vista_manual")
        for nombre in vistas:
            with self.subTest(nombre):
                vista = getattr(self.ventana, nombre)
                self.assertTrue(hasattr(vista, "btn_ayuda"),
                                "esta ventana no tiene botón «?»")

    def test_el_manual_ensena_todas_sus_paginas(self):
        manual = self.ventana.vista_manual
        for capitulo in CAPITULOS:
            for clave in capitulo.entradas:
                with self.subTest(clave):
                    manual.mostrar(clave)
                    self.assertGreater(len(manual.texto.toPlainText()), 100)

    def test_el_buscador_del_manual_encuentra_y_descarta(self):
        manual = self.ventana.vista_manual
        manual.busqueda.setText("consentimiento")
        visibles = self._visibles(manual)
        self.assertIn("Concepto: consentimiento y correo", visibles)
        manual.busqueda.setText("xyzzy")
        self.assertEqual(self._visibles(manual), [])
        manual.busqueda.setText("")
        self.assertGreater(len(self._visibles(manual)), 30)

    def test_el_buscador_no_distingue_acentos(self):
        manual = self.ventana.vista_manual
        manual.busqueda.setText("valoracion")
        self.assertTrue(self._visibles(manual))
        manual.busqueda.setText("")

    @staticmethod
    def _visibles(manual) -> list[str]:
        nombres = []
        arbol = manual.arbol
        for i in range(arbol.topLevelItemCount()):
            padre = arbol.topLevelItem(i)
            for j in range(padre.childCount()):
                hijo = padre.child(j)
                if not hijo.isHidden() and not padre.isHidden():
                    nombres.append(hijo.text(0))
        return nombres


if __name__ == "__main__":
    unittest.main()


class FiltrosYControles(unittest.TestCase):
    """El filtro múltiple, los desplegables buscables y el aviso de orden."""

    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def test_el_desplegable_multiple_arranca_con_lo_marcado(self):
        from krv.ui.comunes import DesplegableMultiple
        combo = DesplegableMultiple(
            [("A", "Uno"), ("B", "Dos"), ("C", "Tres")], marcadas=["A", "C"])
        self.assertEqual(combo.marcadas(), ["A", "C"])
        self.assertEqual(combo.lineEdit().text(), "Uno, Tres")

    def test_el_desplegable_multiple_resume_los_extremos(self):
        from krv.ui.comunes import DesplegableMultiple
        combo = DesplegableMultiple([("A", "Uno"), ("B", "Dos")], marcadas=[],
                                    texto_vacio="Nada", texto_todas="Todo")
        self.assertEqual(combo.lineEdit().text(), "Nada")
        combo.marcar(["A", "B"])
        self.assertEqual(combo.lineEdit().text(), "Todo")

    def test_el_desplegable_multiple_avisa_de_los_cambios(self):
        from krv.ui.comunes import DesplegableMultiple
        combo = DesplegableMultiple([("A", "Uno"), ("B", "Dos")], marcadas=["A"])
        avisos = []
        combo.cambiado.connect(lambda: avisos.append(combo.marcadas()))
        combo.marcar(["B"])
        self.assertEqual(avisos, [["B"]])

    def test_el_filtro_de_asignaciones_arranca_en_lo_que_esta_vivo(self):
        from krv.ui.vista_asignaciones import ESTADOS, ESTADOS_POR_DEFECTO
        self.assertEqual(ESTADOS_POR_DEFECTO, ["PLANIFICADA", "EN_CURSO"])
        # Y los cuatro estados del filtro son los que admite el libro.
        from krv.datos.esquema import TABLAS
        columna = next(c for t in TABLAS if t.nombre == "T_ASIGNACIONES"
                       for c in t.columnas if c.nombre == "Estado")
        self.assertEqual([c for c, _ in ESTADOS], list(columna.opciones))

    def test_los_desplegables_buscables_no_admiten_texto_nuevo(self):
        from PySide6.QtWidgets import QComboBox
        from krv.ui.comunes import hacer_buscable
        combo = hacer_buscable(QComboBox())
        combo.addItem("Sentadilla trasera con barra", "EJ-1")
        self.assertTrue(combo.isEditable())
        self.assertEqual(combo.insertPolicy(), QComboBox.NoInsert)
        combo.setCurrentText("algo que no existe")
        combo.lineEdit().editingFinished.emit()
        self.assertEqual(combo.count(), 1)

    def test_el_buscable_filtra_por_cualquier_parte_del_nombre(self):
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QComboBox
        from krv.ui.comunes import hacer_buscable
        combo = hacer_buscable(QComboBox())
        for texto in ("Press de banca con barra", "Sentadilla trasera con barra",
                      "Remo con mancuerna"):
            combo.addItem(texto, texto)
        completador = combo.completer()
        self.assertEqual(completador.filterMode(), Qt.MatchContains)
        self.assertEqual(completador.caseSensitivity(), Qt.CaseInsensitive)
        completador.setCompletionPrefix("banca")
        self.assertEqual(completador.completionCount(), 1)
        completador.setCompletionPrefix("BARRA")
        self.assertEqual(completador.completionCount(), 2)


class AvisoDeOrdenRepetido(unittest.TestCase):
    """El diálogo de ciclo no debe dejar guardar un orden ya ocupado."""

    @classmethod
    def setUpClass(cls):
        import tempfile
        from PySide6.QtWidgets import QApplication
        from krv.datos import libro as ml, semillas
        from krv.datos.repositorio import Repositorio
        from krv.servicios import programas as srv

        cls.app = QApplication.instance() or QApplication([])
        cls.temporal = tempfile.TemporaryDirectory()
        base = Path(cls.temporal.name)
        ruta = base / "datos_krv.xlsx"
        ml.crear(ruta)
        cls.libro = ml.Libro(ruta, base / "bk")
        cls.libro.cargar()
        semillas.sembrar(cls.libro)
        cls.repo = Repositorio(cls.libro)
        cls.srv = srv
        cls.macro = cls.repo.insertar("T_CICLOS", {
            "Nombre": "Macro", "Tipo": "MACRO", "Orden": 1, "Duracion_Sem": 8,
            "Origen": "MANUAL"})
        cls.meso = cls.repo.insertar("T_CICLOS", {
            "Nombre": "Acumulación", "Tipo": "MESO", "ID_Padre": cls.macro,
            "Orden": 1, "Duracion_Sem": 4, "Origen": "MANUAL"})

    @classmethod
    def tearDownClass(cls):
        cls.temporal.cleanup()

    def test_el_orden_solo_admite_enteros(self):
        from PySide6.QtWidgets import QSpinBox
        from krv.ui.dialogos_programa import DialogoCiclo
        dialogo = DialogoCiclo(self.repo, tipo="MESO", id_padre=self.macro)
        # QSpinBox es de enteros; un QDoubleSpinBox admitiría decimales.
        self.assertIsInstance(dialogo.orden, QSpinBox)
        self.assertNotIsInstance(dialogo.orden, type(None))
        self.assertEqual(dialogo.orden.minimum(), 1)

    def test_el_orden_propuesto_es_el_primero_libre(self):
        from krv.ui.dialogos_programa import DialogoCiclo
        dialogo = DialogoCiclo(self.repo, tipo="MESO", id_padre=self.macro)
        self.assertEqual(dialogo.orden.value(),
                         self.srv.siguiente_orden(self.repo, self.macro))

    def test_no_guarda_un_orden_ocupado(self):
        from unittest import mock
        from krv.ui.dialogos_programa import DialogoCiclo
        dialogo = DialogoCiclo(self.repo, tipo="MESO", id_padre=self.macro)
        dialogo.nombre.setText("Intensificación")
        dialogo.orden.setValue(1)                      # el que ya tiene el otro
        antes = len(self.srv.hijos(self.repo, self.macro))
        with mock.patch("krv.ui.dialogos_programa.QMessageBox.warning") as aviso:
            dialogo._guardar()
        self.assertTrue(aviso.called, "debería avisar de que el orden está cogido")
        self.assertIn("Acumulación", str(aviso.call_args))
        self.assertEqual(len(self.srv.hijos(self.repo, self.macro)), antes,
                         "no debería haber guardado nada")

    def test_guarda_cuando_el_orden_esta_libre(self):
        from krv.ui.dialogos_programa import DialogoCiclo
        dialogo = DialogoCiclo(self.repo, tipo="MESO", id_padre=self.macro)
        dialogo.nombre.setText("Realización")
        dialogo.orden.setValue(7)
        antes = len(self.srv.hijos(self.repo, self.macro))
        dialogo._guardar()
        self.assertEqual(len(self.srv.hijos(self.repo, self.macro)), antes + 1)
        self.assertEqual(self.srv.ordenes_repetidos(self.repo, self.macro), set())

    def test_editar_sin_tocar_el_orden_no_se_queja(self):
        from krv.ui.dialogos_programa import DialogoCiclo
        dialogo = DialogoCiclo(self.repo, id_ciclo=self.meso, padre=None)
        dialogo.nombre.setText("Acumulación (revisada)")
        dialogo._guardar()
        self.assertEqual(
            self.repo.obtener("T_CICLOS", self.meso)["Nombre"],
            "Acumulación (revisada)")
