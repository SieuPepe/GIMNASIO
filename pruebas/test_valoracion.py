"""Pruebas de la valoración física: fórmulas, baremos, hallazgos e informe."""

import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zeu.datos import libro as ml                                  # noqa: E402
from zeu.datos.repositorio import Repositorio                      # noqa: E402
from zeu.nucleo import config                                      # noqa: E402
from zeu.nucleo.config import RAIZ                                 # noqa: E402
from zeu.servicios import informes                                 # noqa: E402
from zeu.servicios import valoracion as srv                        # noqa: E402
from zeu.servicios.importacion import importar_valoracion          # noqa: E402

DATOS = RAIZ / "datos_iniciales"


class Formulas(unittest.TestCase):
    def test_imc(self):
        self.assertEqual(srv.imc(75, 178), 23.7)
        self.assertIsNone(srv.imc(None, 178))

    def test_indices(self):
        self.assertEqual(srv.indice(88, 100), 0.88)
        self.assertIsNone(srv.indice(88, 0))

    def test_rockport(self):
        """Kline: un adulto de mediana edad con marca razonable ronda los 40."""
        valor = srv.vo2max_rockport(75, 45, "H", 13.0, 140)
        self.assertTrue(35 < valor < 50, valor)
        self.assertGreater(srv.vo2max_rockport(75, 45, "H", 12.0, 130),
                           srv.vo2max_rockport(75, 45, "H", 14.0, 150))

    def test_cooper(self):
        self.assertAlmostEqual(srv.vo2max_cooper(2400), 42.4, places=1)
        self.assertEqual(srv.vo2max_cooper(0), None)

    def test_navette_baja_con_la_edad(self):
        self.assertGreater(srv.vo2max_navette(12, 20), srv.vo2max_navette(12, 50))

    def test_harvard_completo_y_corto(self):
        self.assertAlmostEqual(srv.harvard_indice(300, 50, 45, 40), 111.1, places=1)
        self.assertAlmostEqual(srv.harvard_indice(300, 50), 109.1, places=1)
        self.assertIsNone(srv.harvard_indice(None, 50))

    def test_1rm_y_su_fiabilidad(self):
        self.assertEqual(srv.estimar_1rm(100, 5), (116.7, "ALTA"))
        self.assertEqual(srv.estimar_1rm(100, 8)[1], "MEDIA")
        self.assertEqual(srv.estimar_1rm(60, 15)[1], "BAJA")
        self.assertGreater(srv.estimar_1rm(100, 5, "BRZYCKI")[0], 100)


class Hallazgos(unittest.TestCase):
    def test_asimetria_por_porcentaje(self):
        detalle = [{"ID_Test": "DINAMOMETRIA", "Lado": "DERECHO", "Valor": 50},
                   {"ID_Test": "DINAMOMETRIA", "Lado": "IZQUIERDO", "Valor": 40}]
        encontradas = srv.asimetrias(detalle)
        self.assertEqual(len(encontradas), 1)
        self.assertIn("20 %", encontradas[0].detalle)

    def test_diferencia_pequena_no_se_senala(self):
        detalle = [{"ID_Test": "DINAMOMETRIA", "Lado": "DERECHO", "Valor": 50},
                   {"ID_Test": "DINAMOMETRIA", "Lado": "IZQUIERDO", "Valor": 48}]
        self.assertEqual(srv.asimetrias(detalle), [])

    def test_escalas_con_negativos_se_comparan_en_su_unidad(self):
        """De -1 a -3 cm no es un 200 % de asimetría: son 2 cm."""
        cerca = [{"ID_Test": "SCRATCH", "Lado": "DERECHO", "Valor": -1},
                 {"ID_Test": "SCRATCH", "Lado": "IZQUIERDO", "Valor": -3}]
        self.assertEqual(srv.asimetrias(cerca), [])
        lejos = [{"ID_Test": "SCRATCH", "Lado": "DERECHO", "Valor": -2},
                 {"ID_Test": "SCRATCH", "Lado": "IZQUIERDO", "Valor": -9}]
        self.assertEqual(len(srv.asimetrias(lejos)), 1)

    def test_relacion_flexores_extensores(self):
        hallazgos = srv.relaciones_tronco({"SORENSEN": 80, "FLEXORES_TRONCO": 120})
        self.assertTrue(any("extensores lumbares" in h.detalle for h in hallazgos))
        self.assertEqual(srv.relaciones_tronco({"SORENSEN": 150, "FLEXORES_TRONCO": 120}), [])

    def test_asimetria_de_plancha_lateral(self):
        hallazgos = srv.relaciones_tronco(
            {"SORENSEN": 150, "PLANCHA_LATERAL_DERECHO": 90,
             "PLANCHA_LATERAL_IZQUIERDO": 60})
        self.assertTrue(any(h.tipo == "ASIMETRIA" for h in hallazgos))


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporal = tempfile.TemporaryDirectory()
        carpeta = Path(cls.temporal.name)
        cls.ruta = carpeta / "datos.xlsx"
        ml.crear(cls.ruta)
        cls.libro = ml.Libro(cls.ruta, carpeta / "backups")
        cls.libro.cargar()
        cls.repo = Repositorio(cls.libro)
        cls.resultados = importar_valoracion(cls.repo, DATOS)
        cls.cfg = config.Config()
        cls.cfg.datos.libro = cls.ruta

    @classmethod
    def tearDownClass(cls):
        cls.temporal.cleanup()


class DatosIniciales(Base):
    def test_se_importa_todo_sin_errores(self):
        for tabla, resultado in self.resultados.items():
            self.assertEqual(resultado.errores, [], tabla)
            self.assertGreater(resultado.altas, 0, tabla)

    def test_los_protocolos_solo_usan_pruebas_que_existen(self):
        pruebas = {t["ID_Test"] for t in self.repo.listar("T_CAT_TESTS")}
        for linea in self.repo.listar("T_PROTOCOLO_DET"):
            self.assertIn(linea["ID_Test"], pruebas)

    def test_las_pruebas_con_baremo_lo_tienen(self):
        con_baremo = {t["ID_Test"] for t in self.repo.listar("T_CAT_TESTS")
                      if t.get("Tiene_Baremo_SN")}
        baremadas = {b["ID_Test"] for b in self.repo.listar("T_BAREMOS")}
        self.assertEqual(con_baremo - baremadas, set())

    def test_las_pruebas_tecnicas_tienen_criterios(self):
        for prueba in self.repo.listar("T_CAT_TESTS",
                                       lambda t: t.get("Tipo_Medida") == "TECNICA"):
            criterios = self.repo.listar(
                "T_TEST_CRITERIOS", lambda c: c.get("ID_Test") == prueba["ID_Test"])
            self.assertTrue(criterios, prueba["ID_Test"])
            self.assertTrue(any(c.get("Es_Dolor_SN") for c in criterios),
                            f"{prueba['ID_Test']} no tiene criterio de dolor")


class Baremos(Base):
    def test_el_baremo_depende_del_sexo_y_la_edad(self):
        hombre = srv.buscar_baremo(self.repo, "VO2MAX", 44, "H", 25)
        mujer = srv.buscar_baremo(self.repo, "VO2MAX", 44, "M", 25)
        self.assertEqual(hombre.categoria, "BUENO")
        self.assertEqual(mujer.categoria, "SUPERIOR")

    def test_el_mismo_valor_puntua_mas_con_mas_edad(self):
        joven = srv.buscar_baremo(self.repo, "VO2MAX", 33, "H", 25)
        mayor = srv.buscar_baremo(self.repo, "VO2MAX", 33, "H", 65)
        self.assertLess(joven.puntos, mayor.puntos)

    def test_sin_baremo_no_se_inventa_categoria(self):
        vacio = srv.buscar_baremo(self.repo, "PLANCHA_INVERTIDA", 60, "H", 40)
        self.assertFalse(vacio.hay)
        self.assertIsNone(vacio.categoria)

    def test_la_tecnica_usa_la_escala_0_3(self):
        self.assertEqual(srv.buscar_baremo(self.repo, "SENTADILLA_TEC", 0, "H", 40).puntos, 0)
        self.assertEqual(srv.buscar_baremo(self.repo, "SENTADILLA_TEC", 3, "M", 70).puntos, 100)

    def test_el_punto_de_corte_de_dinapenia(self):
        """Por debajo de 27 kg en hombres, el baremo tiene que decir BAJO."""
        self.assertEqual(srv.buscar_baremo(self.repo, "DINAMOMETRIA", 25, "H", 45).categoria,
                         "BAJO")
        self.assertEqual(srv.buscar_baremo(self.repo, "DINAMOMETRIA", 14, "M", 45).categoria,
                         "BAJO")


class ValoracionCompleta(Base):
    def setUp(self):
        self.uid = self.repo.insertar("T_USUARIOS", {
            "Nombre": "Prueba", "F_Nacimiento": date(1980, 1, 1), "Sexo": "H",
            "F_Alta": date.today(), "Estado": "ACTIVO"})
        self.vid = self.repo.insertar("T_VALORACIONES", {
            "ID_Usuario": self.uid, "ID_Protocolo": "PRO-EST",
            "Fecha": date(2026, 9, 1), "Tipo": "INICIAL"})

    def _medir(self, id_test, valor=None, lado="NA", tecnica=None):
        bruto = tecnica if tecnica is not None else valor
        puntos = srv.buscar_baremo(self.repo, id_test, bruto, "H", 46)
        self.repo.insertar("T_VALORACION_DET", {
            "ID_Valoracion": self.vid, "ID_Test": id_test, "Lado": lado,
            "Valor": valor, "Valor_Tecnica": tecnica,
            "Puntuacion": puntos.puntos, "Categoria": puntos.categoria})

    def test_solo_se_puntuan_las_capacidades_medidas(self):
        self._medir("DINAMOMETRIA", 48, "DERECHO")
        self._medir("SIT_AND_REACH", 5)
        resumen = srv.resumir(self.repo, self.vid)
        self.assertIn("FUERZA", resumen.por_capacidad)
        self.assertIn("MOVILIDAD", resumen.por_capacidad)
        self.assertNotIn("POTENCIA", resumen.por_capacidad)   # hueco, no cero

    def test_un_cero_tecnico_es_una_alerta(self):
        self._medir("SENTADILLA_TEC", tecnica=0)
        resumen = srv.resumir(self.repo, self.vid)
        alertas = [h for h in resumen.hallazgos if h.gravedad == "ALERTA"]
        self.assertTrue(alertas)
        self.assertIn("Dolor", alertas[0].detalle)

    def test_la_comparativa_solo_incluye_lo_medido_en_ambas(self):
        self._medir("PESO", 90)
        self._medir("SIT_AND_REACH", 2)
        otra = self.repo.insertar("T_VALORACIONES", {
            "ID_Usuario": self.uid, "ID_Protocolo": "PRO-EST",
            "Fecha": date(2026, 12, 1), "Tipo": "SEGUIMIENTO"})
        for id_test, valor in (("PESO", 85), ("DINAMOMETRIA", 50)):
            self.repo.insertar("T_VALORACION_DET", {
                "ID_Valoracion": otra, "ID_Test": id_test, "Lado": "NA", "Valor": valor})
        comparacion = srv.comparar(srv.resumir(self.repo, self.vid),
                                   srv.resumir(self.repo, otra))
        self.assertEqual([c["ID_Test"] for c in comparacion], ["PESO"])
        self.assertEqual(comparacion[0]["diferencia"], -5)

    def test_se_genera_el_informe_en_pdf(self):
        for id_test, valor in (("PESO", 88), ("ALTURA", 178), ("DINAMOMETRIA", 46),
                               ("SIT_AND_REACH", 3), ("MONOPODAL", 14),
                               ("PLANCHA_FRONTAL", 70)):
            self._medir(id_test, valor)
        self._medir("SENTADILLA_TEC", tecnica=2)
        with tempfile.TemporaryDirectory() as carpeta:
            destino = Path(carpeta) / "informe.pdf"
            informes.generar(self.repo, self.cfg, self.vid, destino)
            self.assertTrue(destino.exists())
            self.assertGreater(destino.stat().st_size, 20_000)

    def test_el_radar_necesita_al_menos_tres_ejes(self):
        with tempfile.TemporaryDirectory() as carpeta:
            destino = Path(carpeta) / "radar.png"
            self.assertIsNone(informes.grafico_radar(
                {"FUERZA": (60, 1), "MOVILIDAD": (70, 1)}, None, destino))
            self.assertIsNotNone(informes.grafico_radar(
                {"FUERZA": (60, 1), "MOVILIDAD": (70, 1), "EQUILIBRIO": (55, 1)},
                None, destino))


if __name__ == "__main__":
    unittest.main()
