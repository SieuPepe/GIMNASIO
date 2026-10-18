"""Pruebas del instalador: datos de demostración y primera configuración.

Lo que se vigila es que la instalación desde cero deje el programa enseñando
todo lo que sabe hacer, y que el asistente escriba unos ficheros que después se
puedan releer.

    python -m unittest discover -s pruebas
"""

import os
import shutil
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from krv.datos import demo, libro as ml, plantillas, plantillas_correo, semillas  # noqa: E402
from krv.datos.repositorio import Repositorio                      # noqa: E402
from krv.nucleo import config                                      # noqa: E402
from krv.servicios import alertas, programas as srv_programas      # noqa: E402
from krv.servicios import valoracion as srv_valoracion             # noqa: E402
from krv.servicios.importacion import (importar_ejercicios,        # noqa: E402
                                       importar_valoracion)


class UsuarioDeDemostracion(unittest.TestCase):
    """Un solo usuario, pero con todo lo que puede colgar de uno."""

    @classmethod
    def setUpClass(cls):
        cls.temporal = tempfile.TemporaryDirectory()
        base = Path(cls.temporal.name)
        ruta = base / "datos_krv.xlsx"
        ml.crear(ruta)
        # Sin tocar el config.toml de quien ejecute las pruebas: si el suyo
        # trae el remitente vacío, media demostración se queda sin correo.
        cls.cfg = config.Config()
        cls.cfg.datos.libro = ruta
        cls.cfg.datos.backups = base / "bk"
        cls.libro = ml.Libro(ruta, cls.cfg.datos.backups)
        cls.libro.cargar()
        semillas.sembrar(cls.libro)
        cls.repo = Repositorio(cls.libro)
        iniciales = config.RAIZ / "datos_iniciales"
        importar_ejercicios(cls.repo, iniciales / "ejercicios.csv")
        importar_valoracion(cls.repo, iniciales)
        plantillas.crear(cls.repo)
        plantillas_correo.crear(cls.repo)
        cls.hoy = date(2026, 10, 18)
        cls.resultado = demo.crear(cls.repo, cls.cfg, hoy=cls.hoy)

    @classmethod
    def tearDownClass(cls):
        cls.temporal.cleanup()

    def test_se_crea_sin_avisos(self):
        self.assertEqual(self.resultado.avisos, [])

    def test_el_usuario_se_ve_que_es_de_ejemplo(self):
        usuario = self.repo.obtener("T_USUARIOS", self.resultado.id_usuario)
        self.assertEqual(usuario["Nombre"], demo.NOMBRE)
        self.assertIn("ejemplo", usuario["Apellidos"].lower() + usuario["Notas"].lower())

    def test_el_correo_es_el_de_la_cuenta_de_envio(self):
        # Probar un correo tiene que ser escribirse a uno mismo, nunca a nadie.
        usuario = self.repo.obtener("T_USUARIOS", self.resultado.id_usuario)
        self.assertEqual(usuario["Email"], demo.correo_de_pruebas(self.cfg))
        self.assertTrue(usuario["Email"], "el usuario de ejemplo necesita correo")

    def test_el_correo_sale_aunque_el_config_no_tenga_remitente(self):
        # Le pasó a un config.toml a medio hacer: el usuario de ejemplo se
        # quedaba sin correo y la mitad del programa no se podía enseñar.
        vacio = config.Config()
        vacio.correo.remitente = ""
        self.assertTrue(demo.correo_de_pruebas(vacio))
        self.assertIn("@", demo.correo_de_pruebas(vacio))

    def test_puede_recibir_correos(self):
        usuario = self.repo.obtener("T_USUARIOS", self.resultado.id_usuario)
        self.assertTrue(usuario["Consentimiento_SN"])
        self.assertTrue(usuario["Acepta_Emails_SN"])

    def test_tiene_de_todo(self):
        esperado = {"T_OBJETIVOS": 3, "T_SALUD": 2, "T_DISPONIBILIDAD": 2,
                    "T_VALORACIONES": 2, "T_ASIGNACIONES": 2}
        for tabla, cuantos in esperado.items():
            with self.subTest(tabla):
                filas = self.repo.listar(
                    tabla, lambda f: f.get("ID_Usuario") == self.resultado.id_usuario)
                self.assertEqual(len(filas), cuantos)

    def test_el_historico_tiene_mas_de_un_registro(self):
        # Salud y disponibilidad se acumulan: hay que poder verlo.
        for tabla in ("T_SALUD", "T_DISPONIBILIDAD"):
            with self.subTest(tabla):
                filas = self.repo.listar(
                    tabla, lambda f: f.get("ID_Usuario") == self.resultado.id_usuario)
                fechas = {f["F_Registro"] for f in filas}
                self.assertGreater(len(fechas), 1)

    def test_las_dos_valoraciones_estan_completas(self):
        for id_valoracion in self.resultado.valoraciones:
            with self.subTest(id_valoracion):
                detalle = self.repo.listar(
                    "T_VALORACION_DET",
                    lambda d: d.get("ID_Valoracion") == id_valoracion)
                self.assertGreater(len(detalle), 25)

    def test_la_segunda_valoracion_va_mejor_que_la_primera(self):
        primera, segunda = [srv_valoracion.resumir(self.repo, v)
                            for v in self.resultado.valoraciones]
        self.assertIsNotNone(primera.global_)
        self.assertGreater(segunda.global_, primera.global_)

    def test_hay_asimetrias_que_ensenar(self):
        resumen = srv_valoracion.resumir(self.repo, self.resultado.valoraciones[0])
        self.assertTrue(resumen.hallazgos, "sin hallazgos no se ve para qué sirven")

    def test_la_fuerza_se_valora_por_tecnica(self):
        detalle = self.repo.listar(
            "T_VALORACION_DET",
            lambda d: d.get("ID_Valoracion") == self.resultado.valoraciones[0])
        tecnicas = [d for d in detalle if d.get("Valor_Tecnica") is not None]
        self.assertTrue(tecnicas)
        self.assertTrue(any(d["Valor_Tecnica"] <= 1 for d in tecnicas),
                        "hace falta una técnica baja para ver saltar el aviso")

    def test_una_asignacion_terminada_y_otra_en_curso(self):
        estados = sorted(self.repo.obtener("T_ASIGNACIONES", a)["Estado"]
                         for a in self.resultado.asignaciones)
        self.assertEqual(estados, ["EN_CURSO", "FINALIZADA"])

    def test_la_asignacion_en_curso_vence_dentro_del_aviso(self):
        # Para que el panel de inicio arranque con el aviso de los 14 días.
        en_curso = [self.repo.obtener("T_ASIGNACIONES", a)
                    for a in self.resultado.asignaciones]
        actual = next(a for a in en_curso if a["Estado"] == "EN_CURSO")
        quedan = (actual["F_Fin_Prevista"] - self.hoy).days
        self.assertGreater(quedan, 0)
        self.assertLessEqual(quedan, self.cfg.correo.dias_aviso_previo)

    def test_la_bandeja_ensena_los_tres_estados(self):
        estados = {c["Estado"] for c in self.repo.listar(
            "T_COLA_MAIL",
            lambda c: c.get("ID_Usuario") == self.resultado.id_usuario)}
        for estado in ("BORRADOR", "ENVIADO", "ERROR"):
            self.assertIn(estado, estados)

    def test_el_panel_de_inicio_tiene_avisos(self):
        avisos = alertas.revisar(self.repo, self.cfg, hoy=self.hoy)
        self.assertTrue(avisos, "el panel vacío no enseña nada")
        titulos = " ".join(a.titulo + a.detalle for a in avisos)
        self.assertIn("días de programa", titulos)

    def test_la_hoja_de_entrenamiento_sale_con_kilos(self):
        # Si no hubiera 1RM, saldría «por determinar» y no se vería la gracia.
        actual = next(a for a in self.resultado.asignaciones
                      if self.repo.obtener("T_ASIGNACIONES", a)["Estado"] == "EN_CURSO")
        asignacion = self.repo.obtener("T_ASIGNACIONES", actual)
        semanas = srv_programas.semanas_de(self.repo, actual)
        self.assertTrue(semanas)
        con_kilos = 0
        for semana in semanas[:1]:
            for sesion in semana.sesiones:
                for linea in srv_programas.lineas(self.repo, sesion["ID_Sesion"]):
                    carga = srv_programas.resolver_carga(
                        self.repo, linea, asignacion["ID_Usuario"], semana.en_micro)
                    con_kilos += 0 if carga.sin_1rm else 1
        self.assertGreater(con_kilos, 0)

    def test_volver_a_crearlo_no_duplica_nada(self):
        antes = len(self.repo.listar("T_USUARIOS"))
        objetivos = len(self.repo.listar("T_OBJETIVOS"))
        demo.crear(self.repo, self.cfg, hoy=self.hoy)
        self.assertEqual(len(self.repo.listar("T_USUARIOS")), antes)
        self.assertEqual(len(self.repo.listar("T_OBJETIVOS")), objetivos)


class AsistenteDePrimeraVez(unittest.TestCase):
    """Escribe .env y config.toml, y lo escrito se tiene que poder releer."""

    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.base = Path(self.temporal.name)
        shutil.copy(config.RAIZ / "config.ejemplo.toml",
                    self.base / "config.ejemplo.toml")

    def tearDown(self):
        self.temporal.cleanup()

    def test_el_env_sale_sin_marca_invisible(self):
        from krv.ui import asistente
        ruta = asistente.escribir_env("a@b.com", "clave", self.base / ".env")
        crudo = ruta.read_bytes()
        self.assertFalse(crudo.startswith(b"\xef\xbb\xbf"),
                         "el .env no debe llevar marca de orden de bytes")
        self.assertNotIn(b"\r\n", crudo)
        self.assertIn(b"GMAIL_USUARIO=a@b.com", crudo)

    def test_el_env_quita_los_espacios_de_la_contrasena(self):
        # Google la enseña en grupos de cuatro: se pega tal cual muchas veces.
        from krv.ui import asistente
        ruta = asistente.escribir_env("a@b.com", "abcd efgh ijkl mnop".replace(" ", ""),
                                      self.base / ".env")
        self.assertIn("GMAIL_APP_PASSWORD=abcdefghijklmnop", ruta.read_text())

    def test_el_config_escrito_se_relee(self):
        from krv.ui import asistente
        cfg = config.Config()
        ruta = asistente.escribir_config(
            cfg, "yo@gmail.com", "Mi Nombre", "Mi lema", "Contacto",
            "Lunes a viernes", ruta=self.base / "config.toml")
        leido = config.cargar(ruta)
        self.assertEqual(leido.negocio.nombre_comercial, "Mi Nombre")
        self.assertEqual(leido.negocio.lema, "Mi lema")
        self.assertEqual(leido.negocio.horario_sala, "Lunes a viernes")
        self.assertEqual(leido.correo.remitente, "yo@gmail.com")

    def test_el_config_conserva_lo_que_no_se_pregunta(self):
        from krv.ui import asistente
        destino = self.base / "config.toml"
        shutil.copy(self.base / "config.ejemplo.toml", destino)
        original = config.cargar(destino)
        asistente.escribir_config(config.Config(), "yo@gmail.com", "N", "L", "C",
                                  "H", ruta=destino)
        leido = config.cargar(destino)
        self.assertEqual(leido.correo.dias_aviso_previo,
                         original.correo.dias_aviso_previo)
        self.assertEqual(leido.datos.copias_a_conservar,
                         original.datos.copias_a_conservar)

    def test_el_config_mantiene_los_comentarios(self):
        # El fichero lo lee una persona: los comentarios explican cada apartado.
        from krv.ui import asistente
        destino = self.base / "config.toml"
        shutil.copy(self.base / "config.ejemplo.toml", destino)
        asistente.escribir_config(config.Config(), "yo@gmail.com", "N", "L", "C",
                                  "H", ruta=destino)
        self.assertIn("#", destino.read_text(encoding="utf-8"))

    def test_hace_falta_cuando_no_hay_credencial(self):
        import importlib
        from krv.nucleo import config as modulo
        from krv.ui import asistente
        recargado = importlib.reload(modulo)
        recargado.CARPETA_DATOS = self.base
        os.environ.pop("GMAIL_APP_PASSWORD", None)
        importlib.reload(asistente)
        try:
            self.assertTrue(asistente.hace_falta())
        finally:
            importlib.reload(modulo)
            importlib.reload(asistente)


if __name__ == "__main__":
    unittest.main()
