"""Pruebas del panel de alertas."""

import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zeu.datos import (libro as ml, plantillas, plantillas_correo,      # noqa: E402
                       semillas)
from zeu.datos.repositorio import Repositorio                           # noqa: E402
from zeu.nucleo import config                                           # noqa: E402
from zeu.nucleo.config import RAIZ                                      # noqa: E402
from zeu.nucleo.fechas import formatear_largo, plural                   # noqa: E402
from zeu.servicios import alertas as srv                                # noqa: E402
from zeu.servicios import programas as srv_programas                    # noqa: E402
from zeu.servicios.importacion import (importar_ejercicios,             # noqa: E402
                                       importar_valoracion)


class Formato(unittest.TestCase):
    def test_la_fecha_no_depende_del_idioma_del_sistema(self):
        self.assertEqual(formatear_largo(date(2026, 10, 18)),
                         "domingo, 18 de octubre de 2026")
        self.assertEqual(formatear_largo(None), "")

    def test_singular_y_plural(self):
        self.assertEqual(plural(1, "correo"), "1 correo")
        self.assertEqual(plural(0, "correo"), "0 correos")
        self.assertEqual(plural(1, "repetición máxima", "repeticiones máximas"),
                         "1 repetición máxima")


class Base(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        carpeta = Path(self.temporal.name)
        self.ruta = carpeta / "datos.xlsx"
        ml.crear(self.ruta)
        self.libro = ml.Libro(self.ruta, carpeta / "backups")
        self.libro.cargar()
        semillas.sembrar(self.libro)
        self.repo = Repositorio(self.libro)
        importar_ejercicios(self.repo, RAIZ / "datos_iniciales" / "ejercicios.csv")
        importar_valoracion(self.repo, RAIZ / "datos_iniciales")
        plantillas.crear(self.repo)
        plantillas_correo.crear(self.repo)
        for plantilla in self.repo.listar("T_PLANTILLAS_MAIL"):
            if "{{enlace_form}}" in (plantilla.get("Cuerpo_HTML") or ""):
                self.repo.actualizar("T_PLANTILLAS_MAIL", plantilla["ID_Plantilla"],
                                     {"URL_Form": "https://f/v?e={{id_usuario}}"})
        self.cfg = config.Config()
        self.cfg.datos.libro = self.ruta
        self.hoy = date(2026, 12, 20)

    def tearDown(self):
        self.temporal.cleanup()

    def _usuario(self, nombre="Marta", **extra) -> str:
        datos = {"Nombre": nombre, "F_Nacimiento": date(1990, 1, 1), "Sexo": "M",
                 "Email": f"{nombre.lower()}@ejemplo.com", "F_Alta": date(2026, 9, 1),
                 "Estado": "ACTIVO", "Consentimiento_SN": True}
        datos.update(extra)
        return self.repo.insertar("T_USUARIOS", datos)

    def _codigos(self, id_usuario: str | None = None) -> list[str]:
        return [a.codigo for a in srv.revisar(self.repo, self.cfg, self.hoy)
                if id_usuario is None or a.id_usuario == id_usuario]


class Estado(Base):
    """Las alertas de estado desaparecen solas cuando el estado cambia."""

    def test_sin_consentimiento(self):
        identificador = self._usuario(Consentimiento_SN=False)
        self.assertIn("SIN_CONSENTIMIENTO", self._codigos(identificador))
        self.repo.actualizar("T_USUARIOS", identificador,
                             {"Consentimiento_SN": True,
                              "F_Consentimiento": date(2026, 12, 1),
                              "Origen_Consentimiento": "FORM"})
        self.assertNotIn("SIN_CONSENTIMIENTO", self._codigos(identificador))

    def test_sin_programa_asignado(self):
        identificador = self._usuario()
        self.assertIn("SIN_PROGRAMA", self._codigos(identificador))
        macro = next(c for c in srv_programas.raices(self.repo)
                     if "Hipertrofia" in c["Nombre"])
        srv_programas.asignar(self.repo, identificador, macro["ID_Ciclo"],
                              date(2026, 12, 1))
        self.assertNotIn("SIN_PROGRAMA", self._codigos(identificador))

    def test_el_programa_que_vence_y_el_vencido(self):
        identificador = self._usuario()
        macro = next(c for c in srv_programas.raices(self.repo)
                     if "Hipertrofia" in c["Nombre"])
        asignacion = srv_programas.asignar(self.repo, identificador,
                                           macro["ID_Ciclo"], date(2026, 9, 7))
        self.repo.actualizar("T_ASIGNACIONES", asignacion, {"Estado": "EN_CURSO"})
        fin = self.repo.obtener("T_ASIGNACIONES", asignacion)["F_Fin_Prevista"]

        lejos = srv.revisar(self.repo, self.cfg, fin - timedelta(days=40))
        self.assertNotIn("PROGRAMA_VENCE", [a.codigo for a in lejos])

        cerca = srv.revisar(self.repo, self.cfg, fin - timedelta(days=7))
        vence = next(a for a in cerca if a.codigo == "PROGRAMA_VENCE")
        self.assertEqual(vence.gravedad, srv.AVISO)
        self.assertIn("7 días", vence.titulo)

        pasado = srv.revisar(self.repo, self.cfg, fin + timedelta(days=3))
        vencido = next(a for a in pasado if a.codigo == "PROGRAMA_VENCIDO")
        self.assertEqual(vencido.gravedad, srv.ALERTA)

    def test_cribado_que_exige_informe_medico(self):
        identificador = self._usuario()
        self.repo.insertar("T_SALUD", {
            "ID_Usuario": identificador, "F_Registro": date(2026, 9, 1),
            "PARQ_2_SN": True})
        self.assertIn("INFORME_MEDICO", self._codigos(identificador))
        salud = self.repo.listar("T_SALUD")[0]
        self.repo.actualizar("T_SALUD", salud["ID_Salud"],
                             {"Requiere_Informe_Medico_SN": True})
        self.assertNotIn("INFORME_MEDICO", self._codigos(identificador))

    def test_valoracion_caducada(self):
        identificador = self._usuario()
        self.repo.insertar("T_VALORACIONES", {
            "ID_Usuario": identificador, "ID_Protocolo": "PRO-EST",
            "Fecha": date(2026, 3, 1), "Tipo": "INICIAL"})
        codigos = self._codigos(identificador)
        self.assertIn("VALORACION_CADUCADA", codigos)
        self.assertNotIn("SIN_VALORACION", codigos)

    def test_valoracion_reciente_no_avisa(self):
        identificador = self._usuario()
        self.repo.insertar("T_VALORACIONES", {
            "ID_Usuario": identificador, "ID_Protocolo": "PRO-EST",
            "Fecha": date(2026, 12, 1), "Tipo": "INICIAL"})
        self.assertNotIn("VALORACION_CADUCADA", self._codigos(identificador))

    def test_falta_la_repeticion_maxima_del_ciclo_en_curso(self):
        identificador = self._usuario()
        macro = next(c for c in srv_programas.raices(self.repo)
                     if "Fuerza" in c["Nombre"])
        asignacion = srv_programas.asignar(self.repo, identificador,
                                           macro["ID_Ciclo"], date(2026, 12, 1))
        self.repo.actualizar("T_ASIGNACIONES", asignacion, {"Estado": "EN_CURSO"})
        self.assertIn("SIN_1RM", self._codigos(identificador))


class Hechos(Base):
    """Las de hecho puntual no se van solas: se marcan como atendidas."""

    def _responder(self, id_usuario, codigo, valor) -> str:
        return self.repo.insertar("T_RESPUESTAS", {
            "ID_Usuario": id_usuario, "F_Respuesta": datetime(2026, 12, 10, 9, 0),
            "Codigo_Pregunta": codigo, "Valor": valor, "Origen": "FORM"})

    def test_molestias_declaradas(self):
        identificador = self._usuario()
        respuesta = self._responder(identificador, "MOLESTIAS", "Leves, en el hombro")
        alerta = next(a for a in srv.revisar(self.repo, self.cfg, self.hoy)
                      if a.codigo == "MOLESTIAS")
        self.assertEqual(alerta.gravedad, srv.ALERTA)
        self.assertTrue(alerta.atendible)

        srv.marcar_atendida(self.repo, respuesta)
        self.assertNotIn("MOLESTIAS", self._codigos(identificador))

    def test_un_no_en_molestias_no_genera_alerta(self):
        identificador = self._usuario()
        self._responder(identificador, "MOLESTIAS", "Ninguna")
        self.assertNotIn("MOLESTIAS", self._codigos(identificador))

    def test_peticion_de_cita(self):
        identificador = self._usuario()
        self.cfg.negocio.horario_sala = "Lunes a sábado de 07:00 a 21:00"
        self._responder(identificador, "QUIERE_CITA", "Sí, llámame")
        alerta = next(a for a in srv.revisar(self.repo, self.cfg, self.hoy)
                      if a.codigo == "QUIERE_CITA")
        self.assertIn("07:00", alerta.detalle)

    def test_un_todavia_no_no_genera_alerta(self):
        identificador = self._usuario()
        self._responder(identificador, "QUIERE_CITA", "Todavía no")
        self.assertNotIn("QUIERE_CITA", self._codigos(identificador))


class Configuracion(Base):
    def test_avisa_si_la_plantilla_no_tiene_formulario(self):
        plantilla = next(p for p in self.repo.listar("T_PLANTILLAS_MAIL")
                         if p["Codigo"] == "ENCUESTA_T14")
        self.repo.actualizar("T_PLANTILLAS_MAIL", plantilla["ID_Plantilla"],
                             {"URL_Form": ""})
        alerta = next(a for a in srv.revisar(self.repo, self.cfg, self.hoy)
                      if a.codigo == "FORMULARIO_SIN_URL")
        self.assertEqual(alerta.gravedad, srv.ALERTA)

    def test_avisa_si_falta_el_catalogo(self):
        for ejercicio in list(self.repo.listar("T_EJERCICIOS")):
            self.repo.borrar("T_EJERCICIOS", ejercicio["ID_Ejercicio"], forzar=True)
        self.assertIn("VACIO_T_EJERCICIOS", self._codigos())


class Orden(Base):
    def test_lo_urgente_va_primero(self):
        self._usuario("Luis", Consentimiento_SN=False)      # ALERTA
        self._usuario("Ana")                                 # AVISO: sin programa
        alertas = srv.revisar(self.repo, self.cfg, self.hoy)
        gravedades = [srv.ORDEN_GRAVEDAD[a.gravedad] for a in alertas]
        self.assertEqual(gravedades, sorted(gravedades))

    def test_el_conteo_cuadra(self):
        self._usuario("Luis", Consentimiento_SN=False)
        alertas = srv.revisar(self.repo, self.cfg, self.hoy)
        conteo = srv.contar(alertas)
        self.assertEqual(sum(conteo.values()), len(alertas))

    def test_cada_alerta_sabe_adonde_lleva(self):
        self._usuario("Luis", Consentimiento_SN=False)
        for alerta in srv.revisar(self.repo, self.cfg, self.hoy):
            self.assertTrue(alerta.seccion, alerta.codigo)

    def test_el_resumen_en_texto(self):
        self._usuario("Luis", Consentimiento_SN=False)
        texto = srv.resumen(self.repo, self.cfg, self.hoy)
        self.assertIn("Requiere atención", texto)
        self.assertIn("Luis", texto)


if __name__ == "__main__":
    unittest.main()
