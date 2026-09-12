"""Pruebas de la planificación: árbol, cargas, progresiones y asignaciones."""

import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zeu.datos import libro as ml, plantillas                      # noqa: E402
from zeu.datos.repositorio import Repositorio                      # noqa: E402
from zeu.nucleo import config                                      # noqa: E402
from zeu.nucleo.config import RAIZ                                 # noqa: E402
from zeu.servicios import informes                                 # noqa: E402
from zeu.servicios import programas as srv                         # noqa: E402
from zeu.servicios.importacion import importar_ejercicios          # noqa: E402


class Cargas(unittest.TestCase):
    def test_redondeo_a_carga_levantable(self):
        self.assertEqual(srv.redondear(77.3, 2.5), 75.0)
        self.assertEqual(srv.redondear(12.4, 2), 12.0)
        self.assertEqual(srv.redondear(43.2, 5), 40.0)

    def test_no_baja_del_peso_de_la_barra(self):
        self.assertEqual(srv.redondear(15, 2.5, minimo=20), 20.0)

    def test_sin_incremento_no_redondea(self):
        self.assertEqual(srv.redondear(77.3, None), 77.3)

    def test_las_repeticiones_en_reserva_bajan_el_porcentaje(self):
        self.assertEqual(srv.pct_por_reps(5, 0), 86.3)
        self.assertEqual(srv.pct_por_reps(5, 2), srv.pct_por_reps(7, 0))
        self.assertLess(srv.pct_por_reps(5, 3), srv.pct_por_reps(5, 0))

    def test_lee_el_primer_numero_del_rango(self):
        self.assertEqual(srv.primer_numero("8-10"), 8)
        self.assertEqual(srv.primer_numero("12"), 12)
        self.assertIsNone(srv.primer_numero("AMRAP"))

    def test_nota_de_progresion_legible(self):
        self.assertIn("2.5", srv.nota_progresion("LINEAL:+2.5"))
        self.assertEqual(srv.nota_progresion("NINGUNA"), "")


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
        importar_ejercicios(cls.repo, RAIZ / "datos_iniciales" / "ejercicios.csv")
        cls.creadas, cls.avisos = plantillas.crear(cls.repo)
        cls.cfg = config.Config()
        cls.cfg.datos.libro = cls.ruta

    @classmethod
    def tearDownClass(cls):
        cls.temporal.cleanup()

    def _usuario(self) -> str:
        return self.repo.insertar("T_USUARIOS", {
            "Nombre": "Prueba", "F_Nacimiento": date(1990, 1, 1), "Sexo": "M",
            "F_Alta": date.today(), "Estado": "ACTIVO"})


class Plantillas(Base):
    def test_se_crean_las_cuatro(self):
        self.assertEqual(len(self.creadas), 4)

    def test_todos_los_ejercicios_existen(self):
        self.assertEqual(self.avisos, [])

    def test_las_duraciones_cuadran(self):
        for macro in srv.raices(self.repo):
            self.assertEqual(srv.avisos_estructura(self.repo, macro["ID_Ciclo"]), [],
                             macro["Nombre"])

    def test_no_se_duplican_al_repetir(self):
        antes = len(self.repo.listar("T_CICLOS"))
        creadas, _ = plantillas.crear(self.repo)
        self.assertEqual(creadas, [])
        self.assertEqual(len(self.repo.listar("T_CICLOS")), antes)


class Arbol(Base):
    def test_un_macro_tiene_varios_mesos_y_cada_meso_varios_micros(self):
        macro = next(c for c in srv.raices(self.repo) if "Hipertrofia" in c["Nombre"])
        mesos = srv.hijos(self.repo, macro["ID_Ciclo"])
        self.assertGreater(len(mesos), 1)
        self.assertTrue(any(len(srv.hijos(self.repo, m["ID_Ciclo"])) > 1 for m in mesos))

    def test_clonar_copia_el_arbol_entero(self):
        macro = next(c for c in srv.raices(self.repo) if "Fuerza" in c["Nombre"])
        original = srv.descendientes(self.repo, macro["ID_Ciclo"])
        lineas_antes = sum(
            len(srv.lineas(self.repo, s["ID_Sesion"]))
            for c in [macro] + original for s in srv.sesiones(self.repo, c["ID_Ciclo"]))

        nuevo = srv.clonar(self.repo, macro["ID_Ciclo"], "Copia de prueba")
        copiados = srv.descendientes(self.repo, nuevo)
        lineas_despues = sum(
            len(srv.lineas(self.repo, s["ID_Sesion"]))
            for c in copiados for s in srv.sesiones(self.repo, c["ID_Ciclo"]))

        self.assertEqual(len(copiados), len(original))
        self.assertEqual(lineas_despues, lineas_antes)
        self.assertEqual(self.repo.obtener("T_CICLOS", nuevo)["Origen"], "CLONADO")
        srv.borrar_ciclo(self.repo, nuevo)

    def test_borrar_se_lleva_todo_lo_que_cuelga(self):
        macro = next(c for c in srv.raices(self.repo) if "Salud" in c["Nombre"])
        copia = srv.clonar(self.repo, macro["ID_Ciclo"], "Para borrar")
        hijos = [c["ID_Ciclo"] for c in srv.descendientes(self.repo, copia)]
        srv.borrar_ciclo(self.repo, copia)
        self.assertFalse(self.repo.existe("T_CICLOS", copia))
        for identificador in hijos:
            self.assertFalse(self.repo.existe("T_CICLOS", identificador))

    def test_avisa_si_las_duraciones_no_cuadran(self):
        macro = self.repo.insertar("T_CICLOS", {
            "Nombre": "Descuadrado", "Tipo": "MACRO", "Duracion_Sem": 12, "Orden": 1})
        self.repo.insertar("T_CICLOS", {
            "Nombre": "Corto", "Tipo": "MESO", "ID_Padre": macro,
            "Duracion_Sem": 4, "Orden": 1})
        avisos = srv.avisos_estructura(self.repo, macro)
        self.assertTrue(any("12 semanas" in a for a in avisos))
        srv.borrar_ciclo(self.repo, macro)


class Asignaciones(Base):
    def setUp(self):
        self.uid = self._usuario()
        self.macro = next(c for c in srv.raices(self.repo) if "Hipertrofia" in c["Nombre"])

    def test_el_calendario_encadena_las_fases_sin_huecos(self):
        fases = srv.calendario(self.repo, self.macro["ID_Ciclo"], date(2026, 1, 5))
        micros = [f for f in fases if f.nivel == "MICRO"]
        for anterior, siguiente in zip(micros, micros[1:]):
            self.assertEqual((siguiente.inicio - anterior.fin).days, 1)

    def test_la_duracion_total_coincide_con_la_declarada(self):
        inicio = date(2026, 1, 5)
        fases = srv.calendario(self.repo, self.macro["ID_Ciclo"], inicio)
        fin = max(f.fin for f in fases)
        semanas = ((fin - inicio).days + 1) / 7
        self.assertEqual(semanas, self.macro["Duracion_Sem"])

    def test_asignar_congela_el_calendario(self):
        identificador = srv.asignar(self.repo, self.uid, self.macro["ID_Ciclo"],
                                    date(2026, 1, 5))
        fases = srv.fases_de(self.repo, identificador)
        self.assertTrue(fases)
        # Cambiar la plantilla después no debe mover el calendario ya asignado
        micro = next(f for f in fases if f["Nivel"] == "MICRO")
        self.repo.actualizar("T_CICLOS", micro["ID_Ciclo"], {"Duracion_Sem": 99})
        self.assertEqual(srv.fases_de(self.repo, identificador)[0]["F_Inicio"],
                         fases[0]["F_Inicio"])
        self.repo.actualizar("T_CICLOS", micro["ID_Ciclo"], {"Duracion_Sem": 4})

    def test_avisa_de_las_que_terminan_en_catorce_dias(self):
        identificador = srv.asignar(self.repo, self.uid, self.macro["ID_Ciclo"],
                                    date(2026, 1, 5))
        asignacion = self.repo.obtener("T_ASIGNACIONES", identificador)
        self.repo.actualizar("T_ASIGNACIONES", identificador, {"Estado": "EN_CURSO"})
        fin = asignacion["F_Fin_Prevista"]
        from datetime import timedelta
        avisos = srv.proximas_a_terminar(self.repo, 14, fin - timedelta(days=10))
        self.assertTrue(any(a.id_asignacion == identificador for a in avisos))
        lejos = srv.proximas_a_terminar(self.repo, 14, fin - timedelta(days=40))
        self.assertFalse(any(a.id_asignacion == identificador for a in lejos))

    def test_la_progresion_se_cuenta_dentro_del_microciclo(self):
        """PCT:80,82,85 son las tres semanas del micro, no las del plan entero."""
        identificador = srv.asignar(self.repo, self.uid, self.macro["ID_Ciclo"],
                                    date(2026, 1, 5))
        semanas = srv.semanas_de(self.repo, identificador)
        self.assertEqual(semanas[0].en_micro, 1)
        primera_del_segundo_micro = next(
            s for s in semanas if s.id_micro != semanas[0].id_micro)
        self.assertEqual(primera_del_segundo_micro.en_micro, 1)
        self.assertGreater(primera_del_segundo_micro.numero, 1)


class CargasConUsuario(Base):
    def setUp(self):
        self.uid = self._usuario()
        self.sentadilla = next(e for e in self.repo.listar("T_EJERCICIOS")
                               if e["Nombre"] == "Sentadilla trasera con barra")

    def _linea(self, **extra) -> dict:
        linea = {"ID_Ejercicio": self.sentadilla["ID_Ejercicio"], "Series": 5,
                 "Reps": "5", "Modo_Carga": "PCT1RM", "Valor_Carga": 80}
        linea.update(extra)
        return linea

    def test_sin_1rm_no_se_inventa_un_numero(self):
        carga = srv.resolver_carga(self.repo, self._linea(), self.uid)
        self.assertTrue(carga.sin_1rm)
        self.assertIn("por determinar", carga.texto)
        self.assertIsNone(carga.kilos)

    def test_con_1rm_calcula_y_redondea(self):
        self.repo.insertar("T_1RM", {
            "ID_Usuario": self.uid, "ID_Ejercicio": self.sentadilla["ID_Ejercicio"],
            "Fecha": date.today(), "Valor_1RM": 100, "Metodo": "EPLEY"})
        carga = srv.resolver_carga(self.repo, self._linea(), self.uid)
        self.assertEqual(carga.kilos, 80.0)
        self.assertFalse(carga.sin_1rm)

    def test_al_actualizar_el_1rm_cambia_la_carga(self):
        self.repo.insertar("T_1RM", {
            "ID_Usuario": self.uid, "ID_Ejercicio": self.sentadilla["ID_Ejercicio"],
            "Fecha": date(2026, 1, 1), "Valor_1RM": 100, "Metodo": "EPLEY"})
        self.repo.insertar("T_1RM", {
            "ID_Usuario": self.uid, "ID_Ejercicio": self.sentadilla["ID_Ejercicio"],
            "Fecha": date(2026, 6, 1), "Valor_1RM": 120, "Metodo": "EPLEY"})
        self.assertEqual(srv.resolver_carga(self.repo, self._linea(), self.uid).kilos, 95.0)

    def test_la_progresion_por_porcentajes_cambia_cada_semana(self):
        self.repo.insertar("T_1RM", {
            "ID_Usuario": self.uid, "ID_Ejercicio": self.sentadilla["ID_Ejercicio"],
            "Fecha": date.today(), "Valor_1RM": 100, "Metodo": "EPLEY"})
        linea = self._linea(Progresion="PCT:70,75,80")
        kilos = [srv.resolver_carga(self.repo, linea, self.uid, s).kilos for s in (1, 2, 3)]
        self.assertEqual(kilos, [70.0, 75.0, 80.0])
        # Más allá del último valor se mantiene el último, no se dispara
        self.assertEqual(srv.resolver_carga(self.repo, linea, self.uid, 9).kilos, 80.0)

    def test_la_descarga_baja_la_carga(self):
        self.repo.insertar("T_1RM", {
            "ID_Usuario": self.uid, "ID_Ejercicio": self.sentadilla["ID_Ejercicio"],
            "Fecha": date.today(), "Valor_1RM": 100, "Metodo": "EPLEY"})
        normal = srv.resolver_carga(self.repo, self._linea(), self.uid).kilos
        descarga = srv.resolver_carga(
            self.repo, self._linea(Progresion="DESCARGA:60"), self.uid).kilos
        self.assertLess(descarga, normal)

    def test_el_peso_corporal_no_necesita_1rm(self):
        carga = srv.resolver_carga(self.repo, self._linea(Modo_Carga="PESO_CORPORAL"),
                                   self.uid)
        self.assertEqual(carga.texto, "peso corporal")
        self.assertFalse(carga.sin_1rm)

    def test_el_tiempo_largo_se_expresa_en_minutos(self):
        carga = srv.resolver_carga(
            self.repo, self._linea(Modo_Carga="TIEMPO", Valor_Carga=480), self.uid)
        self.assertEqual(carga.texto, "8 min")

    def test_se_genera_la_hoja_de_entrenamiento(self):
        macro = next(c for c in srv.raices(self.repo) if "Principiante" in c["Nombre"])
        identificador = srv.asignar(self.repo, self.uid, macro["ID_Ciclo"], date(2026, 3, 2))
        with tempfile.TemporaryDirectory() as carpeta:
            destino = Path(carpeta) / "programa.pdf"
            informes.generar_programa(self.repo, self.cfg, identificador,
                                      desde=1, hasta=2, destino=destino)
            self.assertTrue(destino.exists())
            self.assertGreater(destino.stat().st_size, 5_000)


if __name__ == "__main__":
    unittest.main()
