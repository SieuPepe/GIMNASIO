"""Pruebas del catálogo de ejercicios y su importación."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zeu.datos import libro as ml                               # noqa: E402
from zeu.datos.repositorio import Repositorio                   # noqa: E402
from zeu.nucleo.config import RAIZ                              # noqa: E402
from zeu.servicios import ejercicios as srv                     # noqa: E402
from zeu.servicios.importacion import importar_ejercicios       # noqa: E402

CSV = RAIZ / "datos_iniciales" / "ejercicios.csv"


class Vocabulario(unittest.TestCase):
    def test_lista_y_texto_son_inversos(self):
        self.assertEqual(srv.lista("BARRA|DISCOS"), ("BARRA", "DISCOS"))
        self.assertEqual(srv.texto(["barra", "discos"]), "BARRA|DISCOS")
        self.assertEqual(srv.lista(None), ())

    def test_sin_tildes(self):
        self.assertEqual(srv.sin_tildes("Elevación de Gemelos"), "elevacion de gemelos")

    def test_material_disponible(self):
        barra = {"Material": "BARRA|DISCOS|RACK"}
        self.assertTrue(srv.hay_material(barra, {"BARRA", "DISCOS", "RACK", "BANCO"}))
        self.assertFalse(srv.hay_material(barra, {"BARRA", "DISCOS"}))

    def test_el_peso_corporal_no_es_un_requisito(self):
        self.assertTrue(srv.hay_material({"Material": "PESO_CORPORAL"}, set()))
        self.assertTrue(srv.hay_material(
            {"Material": "MANCUERNAS|PESO_CORPORAL"}, {"MANCUERNAS"}))


class CatalogoInicial(unittest.TestCase):
    """El fichero que se entrega tiene que estar impecable: es la base de todo."""

    @classmethod
    def setUpClass(cls):
        cls.temporal = tempfile.TemporaryDirectory()
        carpeta = Path(cls.temporal.name)
        cls.ruta = carpeta / "datos.xlsx"
        ml.crear(cls.ruta)
        cls.libro = ml.Libro(cls.ruta, carpeta / "backups")
        cls.libro.cargar()
        cls.repo = Repositorio(cls.libro)
        cls.resultado = importar_ejercicios(cls.repo, CSV)

    @classmethod
    def tearDownClass(cls):
        cls.temporal.cleanup()

    def test_se_importa_entero_y_sin_errores(self):
        self.assertEqual(self.resultado.errores, [])
        self.assertGreaterEqual(self.resultado.altas, 120)

    def test_sin_avisos_de_vocabulario(self):
        self.assertEqual(self.resultado.avisos, [])

    def test_no_hay_nombres_repetidos(self):
        nombres = [srv.sin_tildes(e["Nombre"]) for e in self.repo.listar("T_EJERCICIOS")]
        self.assertEqual(len(nombres), len(set(nombres)))

    def test_cubre_todos_los_patrones_esenciales(self):
        self.assertEqual(srv.patrones_sin_cobertura(srv.activos(self.repo)), [])

    def test_los_ejercicios_con_carga_externa_declaran_incremento(self):
        """Sin incremento no se puede redondear la carga a algo levantable.

        Un ejercicio lleva carga externa si usa un medio que se carga en kilos y
        no declara PESO_CORPORAL: una dominada se hace en una barra fija, pero la
        resistencia es el propio cuerpo y no hay kilos que redondear.
        """
        cargables = {"BARRA", "MANCUERNAS", "MAQUINA", "POLEA", "KETTLEBELL"}
        sin_incremento = [
            e["Nombre"] for e in srv.activos(self.repo)
            if srv.necesita_material(e) & cargables
            and "PESO_CORPORAL" not in srv.material_de(e)
            and not e.get("Incremento_Kg")
        ]
        self.assertEqual(sin_incremento, [])

    def test_el_peso_corporal_esta_bien_declarado(self):
        """Las planchas y las dominadas tienen que poder hacerse sin carga."""
        for nombre in ("Plancha frontal", "Dominada con agarre prono",
                       "Remo invertido", "Fondos en banco"):
            ejercicio = next(e for e in srv.activos(self.repo) if e["Nombre"] == nombre)
            self.assertIn("PESO_CORPORAL", srv.material_de(ejercicio), nombre)

    def test_importar_dos_veces_no_duplica(self):
        antes = len(self.repo.listar("T_EJERCICIOS"))
        segunda = importar_ejercicios(self.repo, CSV)
        self.assertEqual(segunda.altas, 0)
        self.assertEqual(len(self.repo.listar("T_EJERCICIOS")), antes)

    def test_sustitutos_comparten_patron(self):
        sentadilla = next(e for e in srv.activos(self.repo)
                          if e["Nombre"] == "Sentadilla trasera con barra")
        encontrados = srv.sustitutos(self.repo, sentadilla["ID_Ejercicio"])
        self.assertTrue(encontrados)
        for e in encontrados:
            self.assertEqual(e["Patron"], "DOMINANTE_RODILLA")
            self.assertNotEqual(e["ID_Ejercicio"], sentadilla["ID_Ejercicio"])

    def test_sustitutos_respetan_el_material(self):
        sentadilla = next(e for e in srv.activos(self.repo)
                          if e["Nombre"] == "Sentadilla trasera con barra")
        casa = {"MANCUERNAS", "BANCO", "CAJON", "PESO_CORPORAL"}
        for e in srv.sustitutos(self.repo, sentadilla["ID_Ejercicio"], material=casa):
            self.assertTrue(srv.hay_material(e, casa), e["Nombre"])

    def test_catalogo_filtrado_por_material_de_casa(self):
        casa = {"MANCUERNAS", "COLCHONETA", "BANCO", "GOMA", "PESO_CORPORAL"}
        disponible = srv.catalogo_disponible(self.repo, material=casa)
        self.assertTrue(0 < len(disponible) < len(srv.activos(self.repo)))
        for e in disponible:
            self.assertTrue(srv.hay_material(e, casa), e["Nombre"])

    def test_detecta_patrones_sin_cobertura(self):
        """Solo con mancuernas no hay tracción vertical: hay que avisarlo."""
        solo_mancuernas = srv.catalogo_disponible(
            self.repo, material={"MANCUERNAS", "PESO_CORPORAL"})
        self.assertIn("TRACCION_V", srv.patrones_sin_cobertura(solo_mancuernas))

    def test_contraindicaciones_senalan_lo_que_toca(self):
        encontradas = srv.contraindicaciones(
            srv.activos(self.repo), "Hernia discal L5-S1 sintomática")
        nombres = {c.nombre for c in encontradas}
        self.assertIn("Peso muerto convencional", nombres)
        self.assertNotIn("Curl de bíceps con mancuernas", nombres)

    def test_sin_antecedentes_no_senala_nada(self):
        self.assertEqual(srv.contraindicaciones(srv.activos(self.repo), ""), [])

    def test_volumen_por_grupo_reparte_los_secundarios(self):
        press = next(e for e in srv.activos(self.repo)
                     if e["Nombre"] == "Press de banca con barra")
        volumen = srv.volumen_por_grupo(
            self.repo, [{"ID_Ejercicio": press["ID_Ejercicio"], "Series": 4}])
        self.assertEqual(volumen["PECTORAL"], 4)
        self.assertEqual(volumen["TRICEPS"], 2)


if __name__ == "__main__":
    unittest.main()
