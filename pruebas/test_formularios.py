"""Que los formularios que generamos los entienda nuestro propio importador.

El guion de Apps Script crea los formularios de Google con sus preguntas. El
importador reconoce cada respuesta por las palabras del enunciado. Son dos
ficheros que no se hablan entre sí, y si alguien reescribe una pregunta en uno
el otro deja de entenderla sin que nada falle: la respuesta llega y se tira.

    python -m unittest discover -s pruebas
"""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from krv.servicios.respuestas import _codigo_de, _columna_id   # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
GUION = RAIZ / "herramientas" / "formularios_google.gs"

# Lo que cada formulario tiene que acabar preguntando, pase lo que pase con la
# redacción. Si una de estas desaparece, el programa pierde una funcionalidad.
IMPRESCINDIBLES = {
    "crearConsentimiento": {"CONSENTIMIENTO"},
    "crearEncuesta": {"SENSACION", "MOLESTIAS", "DIFICULTAD", "ADHERENCIA",
                      "MOTIVO_FALTAS", "OBJETIVO", "PROXIMO_CICLO",
                      "QUIERE_CITA"},
    "crearCheckin": {"SENSACION", "MOLESTIAS", "QUIERE_CITA"},
}


def preguntas_de(funcion: str) -> list[str]:
    """Los enunciados de un formulario del guion, sin los saltos de página."""
    texto = GUION.read_text(encoding="utf-8")
    cuerpo = texto.split(f"function {funcion}", 1)[1].split("\nfunction ", 1)[0]
    # Un salto de página lleva título pero no genera columna en el CSV.
    cuerpo = re.sub(r"addPageBreakItem\(\)\s*\.setTitle\('[^']*'\)", "", cuerpo)
    return re.findall(r"setTitle\('([^']+)'", cuerpo)


class GuionDeFormularios(unittest.TestCase):
    def test_existe(self):
        self.assertTrue(GUION.exists())

    def test_todas_las_preguntas_se_reconocen(self):
        for funcion in IMPRESCINDIBLES:
            for pregunta in preguntas_de(funcion):
                with self.subTest(f"{funcion}: {pregunta[:40]}"):
                    self.assertTrue(
                        _codigo_de(pregunta) or _columna_id(pregunta),
                        "el importador no sabría qué hacer con esta respuesta")

    def test_cada_formulario_pregunta_lo_que_tiene_que_preguntar(self):
        for funcion, esperados in IMPRESCINDIBLES.items():
            codigos = {_codigo_de(p) for p in preguntas_de(funcion)}
            with self.subTest(funcion):
                self.assertEqual(esperados - codigos, set())

    def test_los_tres_llevan_la_identificacion(self):
        # Sin esto la respuesta llega sin saber de quién es y se descarta.
        texto = GUION.read_text(encoding="utf-8")
        for funcion in IMPRESCINDIBLES:
            cuerpo = texto.split(f"function {funcion}", 1)[1].split("\nfunction ", 1)[0]
            with self.subTest(funcion):
                self.assertIn("anadirOcultas(", cuerpo)

    def test_los_titulos_de_la_identificacion_se_reconocen(self):
        texto = GUION.read_text(encoding="utf-8")
        titulos = dict(re.findall(r"var (ID_\w+) = '([^']+)';", texto))
        self.assertEqual(_columna_id(titulos["ID_USUARIO"]), "ID_Usuario")
        self.assertEqual(_columna_id(titulos["ID_ENVIO"]), "ID_Envio")

    def test_el_enlace_devuelve_los_marcadores_a_su_sitio(self):
        # Google codifica las llaves al construir la dirección, y el programa
        # busca {{id_usuario}} tal cual.
        texto = GUION.read_text(encoding="utf-8")
        self.assertIn("%7B%7B", texto)
        self.assertIn("{{id_usuario}}", texto)
        self.assertIn("{{id_envio}}", texto)

    def test_la_identificacion_no_es_obligatoria(self):
        # Si lo fuera, quien abriera el formulario sin el enlace se atascaría.
        texto = GUION.read_text(encoding="utf-8")
        ocultas = texto.split("function anadirOcultas", 1)[1].split("\nfunction ", 1)[0]
        self.assertIn("setRequired(false)", ocultas)
        self.assertNotIn("setRequired(true)", ocultas)


class SeparadorDelCsv(unittest.TestCase):
    """Los nuestros van con punto y coma; los de Google Forms, con coma.

    Estaba fijo en punto y coma, así que un CSV de Google se leía como una sola
    columna gigante: no se importaba nada y tampoco daba error.
    """

    def test_reconoce_los_dos(self):
        from krv.servicios.importacion import delimitador_de
        self.assertEqual(delimitador_de("ID;Nombre;Fecha"), ";")
        self.assertEqual(delimitador_de("Marca temporal,ID_Usuario,¿Cómo vas?"), ",")

    def test_sin_separador_se_queda_con_el_nuestro(self):
        from krv.servicios.importacion import delimitador_de
        self.assertEqual(delimitador_de("UnaSolaColumna"), ";")

    def test_gana_el_que_mas_aparece(self):
        # Una cabecera con comas dentro del texto de las preguntas.
        from krv.servicios.importacion import delimitador_de
        self.assertEqual(
            delimitador_de("Marca temporal,¿Cómo te sientes, ahora?,ID_Usuario"),
            ",")
        self.assertEqual(delimitador_de("Nombre;Notas, varias;Fecha"), ";")

    def test_un_csv_de_google_se_importa(self):
        import csv
        import tempfile
        from pathlib import Path as Ruta
        from krv.servicios.importacion import leer_csv
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Ruta(carpeta) / "respuestas.csv"
            with ruta.open("w", encoding="utf-8", newline="") as fichero:
                escritor = csv.writer(fichero)           # coma, como Google
                escritor.writerow(["Marca temporal", "ID_Usuario",
                                   "¿Has tenido molestias o dolores?"])
                escritor.writerow(["18/10/2026 9:30", "USR-0001", "No"])
            filas = leer_csv(ruta)
        self.assertEqual(len(filas), 1)
        self.assertEqual(filas[0]["ID_Usuario"], "USR-0001")

    def test_los_datos_iniciales_siguen_leyendose(self):
        from krv.nucleo.config import RAIZ
        from krv.servicios.importacion import leer_csv
        filas = leer_csv(RAIZ / "datos_iniciales" / "ejercicios.csv")
        self.assertGreater(len(filas), 100)
        self.assertIn("Nombre", filas[0])


class ColumnasQueApuntanALoMismo(unittest.TestCase):
    """Una pregunta con detalle ocupa dos columnas y es una sola respuesta.

    «¿Has tenido molestias?» y «cuéntame dónde» son la misma respuesta partida
    en dos. Antes se guardaba la primera y la segunda se tiraba, así que el
    aviso del panel salía sin el detalle, que es justo lo que hace falta leer.
    """

    def setUp(self):
        import tempfile
        from datetime import date
        from krv.datos import libro as ml, plantillas_correo, semillas
        from krv.datos.repositorio import Repositorio
        from krv.nucleo import config

        self.temporal = tempfile.TemporaryDirectory()
        base = Path(self.temporal.name)
        ruta = base / "datos.xlsx"
        ml.crear(ruta)
        self.cfg = config.Config()
        self.cfg.datos.libro = ruta
        self.cfg.datos.backups = base / "bk"
        self.libro = ml.Libro(ruta, self.cfg.datos.backups)
        self.libro.cargar()
        semillas.sembrar(self.libro)
        self.repo = Repositorio(self.libro)
        plantillas_correo.crear(self.repo)
        self.usuario = self.repo.insertar("T_USUARIOS", {
            "Nombre": "Ana", "F_Nacimiento": date(1990, 3, 2), "Sexo": "M",
            "Email": "ana@ejemplo.com", "F_Alta": date(2026, 1, 1),
            "Estado": "ACTIVO"})
        self.base = base

    def tearDown(self):
        self.temporal.cleanup()

    def _importar(self, cabeceras, valores):
        from krv.servicios import respuestas
        import csv
        ruta = self.base / "respuestas.csv"
        with ruta.open("w", encoding="utf-8", newline="") as fichero:
            escritor = csv.writer(fichero)
            escritor.writerow(cabeceras)
            escritor.writerow(valores)
        return respuestas.importar(self.repo, self.cfg, ruta)

    def _valor(self, codigo):
        filas = self.repo.listar(
            "T_RESPUESTAS", lambda r: r.get("Codigo_Pregunta") == codigo)
        return filas[0]["Valor"] if filas else None

    def test_las_dos_columnas_acaban_en_una_respuesta(self):
        self._importar(
            ["ID_Usuario", "¿Has tenido molestias o dolores?",
             "Si has marcado molestias, cuéntame dónde"],
            [self.usuario, "Sí", "En el hombro derecho al empujar"])
        guardadas = self.repo.listar(
            "T_RESPUESTAS", lambda r: r.get("Codigo_Pregunta") == "MOLESTIAS")
        self.assertEqual(len(guardadas), 1, "debería ser una sola respuesta")
        self.assertIn("Sí", guardadas[0]["Valor"])
        self.assertIn("hombro", guardadas[0]["Valor"],
                      "el detalle es lo que de verdad hay que leer")

    def test_el_aviso_de_molestias_lleva_el_detalle(self):
        resultado = self._importar(
            ["ID_Usuario", "¿Has tenido molestias o dolores?",
             "Si has marcado molestias, cuéntame dónde"],
            [self.usuario, "Sí", "En el hombro derecho"])
        self.assertTrue(any("hombro" in a for a in resultado.acciones),
                        f"acciones: {resultado.acciones}")

    def test_el_objetivo_nuevo_queda_escrito(self):
        # «Lo cambio» a secas no sirve de descripción de un objetivo.
        self._importar(
            ["ID_Usuario", "¿Mantienes el objetivo con el que empezaste?",
             "Si lo cambias, ¿cuál es ahora tu objetivo?"],
            [self.usuario, "Lo cambio", "Quiero ganar fuerza en el tren inferior"])
        objetivos = self.repo.listar(
            "T_OBJETIVOS", lambda o: o.get("Estado") == "ACTIVO")
        self.assertEqual(len(objetivos), 1)
        self.assertIn("fuerza", objetivos[0]["Descripcion"])

    def test_una_sola_columna_sigue_funcionando(self):
        self._importar(["ID_Usuario", "¿Has tenido molestias o dolores?"],
                       [self.usuario, "No"])
        self.assertEqual(self._valor("MOLESTIAS"), "No")

    def test_el_orden_lo_marca_el_formulario(self):
        # La columna de la izquierda va primera: es la pregunta, no el detalle.
        self._importar(
            ["ID_Usuario", "¿Qué duración de sesión te encaja mejor?",
             "¿Qué días te encaja mejor entrenar?", "¿Y en qué franja horaria?"],
            [self.usuario, "60 minutos", "Lunes y miércoles", "Tarde"])
        valor = self._valor("PREFERENCIA_HORARIA")
        self.assertTrue(valor.startswith("60 minutos"), valor)
        self.assertIn("Tarde", valor)

    def test_las_vacias_no_ensucian(self):
        self._importar(
            ["ID_Usuario", "¿Has tenido molestias o dolores?",
             "Si has marcado molestias, cuéntame dónde"],
            [self.usuario, "No", ""])
        self.assertEqual(self._valor("MOLESTIAS"), "No")


if __name__ == "__main__":
    unittest.main()
