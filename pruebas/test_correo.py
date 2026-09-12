"""Pruebas de la comunicación: plantillas, cola, salvaguardas y respuestas."""

import csv
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zeu.datos import (libro as ml, plantillas, plantillas_correo,     # noqa: E402
                       semillas)
from zeu.datos.repositorio import Repositorio                          # noqa: E402
from zeu.nucleo import config                                          # noqa: E402
from zeu.nucleo.config import RAIZ                                     # noqa: E402
from zeu.servicios import cola as srv                                  # noqa: E402
from zeu.servicios import correo as srv_correo                         # noqa: E402
from zeu.servicios import programas as srv_programas                   # noqa: E402
from zeu.servicios import respuestas as srv_respuestas                 # noqa: E402
from zeu.servicios.importacion import importar_ejercicios              # noqa: E402


class Plantillas(unittest.TestCase):
    def test_sustituye_marcadores(self):
        self.assertEqual(
            srv_correo.rellenar("Hola {{nombre}}", {"nombre": "Ana"}), "Hola Ana")

    def test_lo_desconocido_queda_vacio(self):
        self.assertEqual(srv_correo.rellenar("Hola {{x}}!", {}), "Hola !")

    def test_los_bloques_condicionales_desaparecen_enteros(self):
        plantilla = "A{{#nota}} nota: {{nota}}{{/nota}} B"
        self.assertEqual(srv_correo.rellenar(plantilla, {"nota": "vale"}),
                         "A nota: vale B")
        self.assertEqual(srv_correo.rellenar(plantilla, {}), "A B")

    def test_detecta_marcadores_sin_resolver(self):
        self.assertEqual(srv_correo.marcadores_sin_resolver("a {{uno}} b {{dos}}"),
                         ["dos", "uno"])

    def test_enlace_prerrellenado(self):
        url = "https://f/viewform?entry.1={{id_usuario}}&entry.2={{id_envio}}"
        enlace = srv_correo.enlace_prerrellenado(url, "USR-0042", "ENV-0311")
        self.assertIn("entry.1=USR-0042", enlace)
        self.assertIn("entry.2=ENV-0311", enlace)


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
        plantillas.crear(self.repo)
        plantillas_correo.crear(self.repo)
        self.cfg = config.Config()
        self.cfg.datos.libro = self.ruta
        self.cfg.negocio.horario_sala = "Lunes a sábado de 07:00 a 21:00"
        self.enviador = srv_correo.EnviadorSimulado()
        self.hoy = date(2026, 12, 20)

        for plantilla in self.repo.listar("T_PLANTILLAS_MAIL"):
            if "{{enlace_form}}" in (plantilla.get("Cuerpo_HTML") or ""):
                self.repo.actualizar("T_PLANTILLAS_MAIL", plantilla["ID_Plantilla"], {
                    "URL_Form": "https://f/viewform?e1={{id_usuario}}&e2={{id_envio}}"})

    def tearDown(self):
        self.temporal.cleanup()

    def _usuario(self, nombre="Marta", consentido=True, email="marta@ejemplo.com") -> str:
        return self.repo.insertar("T_USUARIOS", {
            "Nombre": nombre, "Apellidos": "Prueba", "F_Nacimiento": date(1990, 1, 1),
            "Sexo": "M", "Email": email, "F_Alta": date(2026, 9, 1), "Estado": "ACTIVO",
            "Consentimiento_SN": consentido,
            "F_Consentimiento": date(2026, 9, 1) if consentido else None,
            "Origen_Consentimiento": "FORM" if consentido else None})

    def _asignar(self, id_usuario, inicio=date(2026, 9, 7), estado="EN_CURSO") -> str:
        macro = next(c for c in srv_programas.raices(self.repo)
                     if "Hipertrofia" in c["Nombre"])
        identificador = srv_programas.asignar(self.repo, id_usuario,
                                              macro["ID_Ciclo"], inicio)
        self.repo.actualizar("T_ASIGNACIONES", identificador, {"Estado": estado})
        return identificador


class Disparadores(Base):
    def test_pide_consentimiento_a_quien_no_lo_tiene(self):
        self._usuario(consentido=False)
        codigos = [d.codigo for d in srv.detectar(self.repo, self.cfg, self.hoy)]
        self.assertIn("CONSENTIMIENTO", codigos)

    def test_no_lo_pide_dos_veces(self):
        self._usuario(consentido=False)
        srv.generar_borradores(self.repo, self.cfg, self.hoy)
        codigos = [d.codigo for d in srv.detectar(self.repo, self.cfg, self.hoy)]
        self.assertNotIn("CONSENTIMIENTO", codigos)

    def test_encuesta_a_catorce_dias_del_final(self):
        identificador = self._usuario()
        asignacion = self._asignar(identificador)
        fin = self.repo.obtener("T_ASIGNACIONES", asignacion)["F_Fin_Prevista"]
        lejos = [d.codigo for d in srv.detectar(self.repo, self.cfg,
                                                fin - timedelta(days=30))]
        cerca = [d.codigo for d in srv.detectar(self.repo, self.cfg,
                                                fin - timedelta(days=7))]
        self.assertNotIn("ENCUESTA_T14", lejos)
        self.assertIn("ENCUESTA_T14", cerca)

    def test_cierre_cuando_el_ciclo_ha_terminado(self):
        identificador = self._usuario()
        asignacion = self._asignar(identificador)
        fin = self.repo.obtener("T_ASIGNACIONES", asignacion)["F_Fin_Prevista"]
        codigos = [d.codigo for d in srv.detectar(self.repo, self.cfg,
                                                  fin + timedelta(days=2))]
        self.assertIn("CIERRE_CICLO", codigos)

    def test_sin_correo_no_se_genera_nada(self):
        self._usuario(email="")
        self._asignar(self.repo.listar("T_USUARIOS")[0]["ID_Usuario"])
        self.assertEqual(srv.detectar(self.repo, self.cfg, self.hoy), [])

    def test_recordatorio_solo_a_quien_no_responde(self):
        identificador = self._usuario()
        asignacion = self._asignar(identificador)
        envio = self.repo.insertar("T_COLA_MAIL", {
            "ID_Usuario": identificador, "ID_Asignacion": asignacion,
            "Codigo_Plantilla": "ENCUESTA_T14", "F_Generado": datetime.now(),
            "Estado": "ENVIADO",
            "F_Envio": datetime(2026, 12, 10, 9, 0), "Respondido_SN": False})
        codigos = [d.codigo for d in srv.detectar(self.repo, self.cfg, self.hoy)]
        self.assertIn("RECORDATORIO", codigos)
        self.repo.actualizar("T_COLA_MAIL", envio, {"Respondido_SN": True})
        codigos = [d.codigo for d in srv.detectar(self.repo, self.cfg, self.hoy)]
        self.assertNotIn("RECORDATORIO", codigos)


class Montaje(Base):
    def test_el_cuerpo_lleva_los_datos_del_usuario(self):
        identificador = self._usuario()
        asignacion = self._asignar(identificador)
        self.repo.insertar("T_OBJETIVOS", {
            "ID_Usuario": identificador, "F_Registro": date(2026, 9, 1),
            "Tipo": "HIPERTROFIA", "Descripcion": "Ganar masa en tren superior",
            "Prioridad": 1, "Estado": "ACTIVO"})
        envio_id = self.repo.insertar("T_COLA_MAIL", {
            "ID_Usuario": identificador, "ID_Asignacion": asignacion,
            "Codigo_Plantilla": "ENCUESTA_T14", "F_Generado": datetime.now(),
            "Estado": "BORRADOR",
            "Nota_Entrenador": "Te veo mucho más suelta en la sentadilla"})
        asunto, html = srv.montar(self.repo, self.cfg,
                                  self.repo.obtener("T_COLA_MAIL", envio_id))
        self.assertIn("Marta", asunto)
        self.assertIn("Ganar masa en tren superior", html)
        self.assertIn("mucho más suelta", html)
        self.assertIn(identificador, html)      # el enlace lleva su identificador
        self.assertIn(envio_id, html)

    def test_sin_nota_no_queda_un_bloque_vacio(self):
        identificador = self._usuario()
        envio_id = self.repo.insertar("T_COLA_MAIL", {
            "ID_Usuario": identificador, "Codigo_Plantilla": "CONSENTIMIENTO",
            "F_Generado": datetime.now(), "Estado": "BORRADOR"})
        _, html = srv.montar(self.repo, self.cfg,
                             self.repo.obtener("T_COLA_MAIL", envio_id))
        self.assertNotIn('class="nota"', html)

    def test_las_comprobaciones_detectan_lo_que_delata_un_robot(self):
        identificador = self._usuario(email="")
        envio_id = self.repo.insertar("T_COLA_MAIL", {
            "ID_Usuario": identificador, "Codigo_Plantilla": "CONSENTIMIENTO",
            "F_Generado": datetime.now(), "Estado": "BORRADOR"})
        problemas = srv.comprobar(self.repo, self.cfg,
                                  self.repo.obtener("T_COLA_MAIL", envio_id))
        self.assertTrue(any("correo electrónico" in p for p in problemas))

    def test_avisa_si_falta_la_url_del_formulario(self):
        plantilla = next(p for p in self.repo.listar("T_PLANTILLAS_MAIL")
                         if p["Codigo"] == "ENCUESTA_T14")
        self.repo.actualizar("T_PLANTILLAS_MAIL", plantilla["ID_Plantilla"],
                             {"URL_Form": ""})
        identificador = self._usuario()
        asignacion = self._asignar(identificador)
        envio_id = self.repo.insertar("T_COLA_MAIL", {
            "ID_Usuario": identificador, "ID_Asignacion": asignacion,
            "Codigo_Plantilla": "ENCUESTA_T14", "F_Generado": datetime.now(),
            "Estado": "BORRADOR"})
        problemas = srv.comprobar(self.repo, self.cfg,
                                  self.repo.obtener("T_COLA_MAIL", envio_id))
        self.assertTrue(any("no tiene URL" in p for p in problemas))


class Envio(Base):
    def _borrador(self, id_usuario, codigo="BIENVENIDA", asignacion=None) -> str:
        return self.repo.insertar("T_COLA_MAIL", {
            "ID_Usuario": id_usuario, "ID_Asignacion": asignacion,
            "Codigo_Plantilla": codigo, "F_Generado": datetime.now(),
            "F_Programada": self.hoy, "Estado": "BORRADOR"})

    def test_sin_consentimiento_solo_sale_la_peticion_de_consentimiento(self):
        identificador = self._usuario(consentido=False)
        asignacion = self._asignar(identificador)
        bienvenida = self._borrador(identificador, "BIENVENIDA", asignacion)
        consentimiento = self._borrador(identificador, "CONSENTIMIENTO")

        resultado = srv.enviar(self.repo, self.cfg, self.enviador,
                               [bienvenida, consentimiento])
        self.assertEqual(resultado.enviados, [consentimiento])
        self.assertTrue(any("consentimiento" in motivo
                            for _, motivo in resultado.omitidos))

    def test_una_celda_en_blanco_no_significa_que_no_quiera_correos(self):
        identificador = self.repo.insertar("T_USUARIOS", {
            "Nombre": "Sin", "F_Nacimiento": date(1990, 1, 1), "Sexo": "H",
            "Email": "sin@ejemplo.com", "F_Alta": date.today(), "Estado": "ACTIVO",
            "Consentimiento_SN": True})
        resultado = srv.enviar(self.repo, self.cfg, self.enviador,
                               [self._borrador(identificador, "CONSENTIMIENTO")])
        self.assertEqual(len(resultado.enviados), 1)

    def test_se_respeta_la_negativa_explicita(self):
        identificador = self._usuario()
        self.repo.actualizar("T_USUARIOS", identificador, {"Acepta_Emails_SN": False})
        resultado = srv.enviar(self.repo, self.cfg, self.enviador,
                               [self._borrador(identificador, "CONSENTIMIENTO")])
        self.assertEqual(resultado.enviados, [])

    def test_el_envio_queda_registrado(self):
        identificador = self._usuario()
        envio_id = self._borrador(identificador, "CONSENTIMIENTO")
        srv.enviar(self.repo, self.cfg, self.enviador, [envio_id])
        envio = self.repo.obtener("T_COLA_MAIL", envio_id)
        self.assertEqual(envio["Estado"], "ENVIADO")
        self.assertEqual(envio["Aprobado_Por"], "ENTRENADOR")
        self.assertTrue(envio["Cuerpo_Final"])
        self.assertEqual(len(self.enviador.enviados), 1)

    def test_lo_que_no_esta_listo_no_se_pierde_de_la_bandeja(self):
        """Faltar una URL no es un fallo de envío: el borrador sigue ahí."""
        plantilla = next(p for p in self.repo.listar("T_PLANTILLAS_MAIL")
                         if p["Codigo"] == "CONSENTIMIENTO")
        self.repo.actualizar("T_PLANTILLAS_MAIL", plantilla["ID_Plantilla"],
                             {"URL_Form": ""})
        identificador = self._usuario(consentido=False)
        envio_id = self._borrador(identificador, "CONSENTIMIENTO")

        resultado = srv.enviar(self.repo, self.cfg, self.enviador, [envio_id])
        self.assertEqual(resultado.enviados, [])
        envio = self.repo.obtener("T_COLA_MAIL", envio_id)
        self.assertEqual(envio["Estado"], "BORRADOR")      # sigue donde estaba
        self.assertIn("formulario", envio["Error"])        # con el motivo anotado
        self.assertIn(envio_id, [e["ID_Envio"] for e in srv.pendientes(self.repo)])

        # Arreglada la causa, se envía sin rehacer nada
        self.repo.actualizar("T_PLANTILLAS_MAIL", plantilla["ID_Plantilla"],
                             {"URL_Form": "https://f/v?e1={{id_usuario}}"})
        self.assertEqual(srv.enviar(self.repo, self.cfg, self.enviador,
                                    [envio_id]).enviados, [envio_id])

    def test_un_correo_en_error_sigue_a_la_vista(self):
        class Roto(srv_correo.Enviador):
            def enviar(self, *_args, **_kwargs):
                raise RuntimeError("servidor caído")

        identificador = self._usuario()
        envio_id = self._borrador(identificador, "CONSENTIMIENTO")
        srv.enviar(self.repo, self.cfg, Roto(), [envio_id])
        self.assertIn(envio_id, [e["ID_Envio"] for e in srv.pendientes(self.repo)])

    def test_un_fallo_de_envio_deja_el_correo_en_error(self):
        class Roto(srv_correo.Enviador):
            def enviar(self, *_args, **_kwargs):
                raise RuntimeError("servidor caído")

        identificador = self._usuario()
        envio_id = self._borrador(identificador, "CONSENTIMIENTO")
        resultado = srv.enviar(self.repo, self.cfg, Roto(), [envio_id])
        self.assertEqual(resultado.fallidos[0][0], envio_id)
        self.assertEqual(self.repo.obtener("T_COLA_MAIL", envio_id)["Estado"], "ERROR")


class Adjuntos(Base):
    def test_la_bienvenida_lleva_la_hoja_de_entrenamiento(self):
        """El cuerpo dice «te adjunto la hoja»: tiene que ir de verdad."""
        identificador = self._usuario()
        asignacion = self._asignar(identificador)
        envio_id = self.repo.insertar("T_COLA_MAIL", {
            "ID_Usuario": identificador, "ID_Asignacion": asignacion,
            "Codigo_Plantilla": "BIENVENIDA", "F_Generado": datetime.now(),
            "Estado": "BORRADOR"})
        resultado = srv.enviar(self.repo, self.cfg, self.enviador, [envio_id])
        self.assertEqual(resultado.enviados, [envio_id])
        adjuntos = self.enviador.enviados[0]["adjuntos"]
        self.assertEqual(len(adjuntos), 1)
        self.assertTrue(adjuntos[0].exists())
        self.assertGreater(adjuntos[0].stat().st_size, 5_000)

    def test_los_demas_correos_no_llevan_adjunto(self):
        identificador = self._usuario()
        envio_id = self.repo.insertar("T_COLA_MAIL", {
            "ID_Usuario": identificador, "Codigo_Plantilla": "CONSENTIMIENTO",
            "F_Generado": datetime.now(), "Estado": "BORRADOR"})
        srv.enviar(self.repo, self.cfg, self.enviador, [envio_id])
        self.assertEqual(self.enviador.enviados[0]["adjuntos"], [])

    def test_se_adjunta_el_primer_microciclo(self):
        identificador = self._usuario()
        asignacion = self._asignar(identificador)
        semanas = srv_programas.semanas_de(self.repo, asignacion)
        primeras = [s for s in semanas if s.id_micro == semanas[0].id_micro]
        envio = {"Codigo_Plantilla": "BIENVENIDA", "ID_Asignacion": asignacion}
        ruta = srv.adjuntos_para(self.repo, self.cfg, envio)[0]
        self.assertIn(f"s{primeras[0].numero:02d}", ruta.name)


class ModoVacaciones(Base):
    def _activar(self, caducidad: str) -> None:
        for fila in self.repo.libro.filas["T_CONFIG"]:
            if fila["Clave"] == "modo_vacaciones":
                fila["Valor"] = "SI"
            if fila["Clave"] == "caducidad_modo_vacaciones":
                fila["Valor"] = caducidad

    def test_sin_caducidad_no_se_aplica(self):
        self._activar("")
        estado = srv.estado_vacaciones(self.repo, self.hoy)
        self.assertFalse(estado.activo)
        self.assertIn("caducidad", estado.motivo)

    def test_caducado_se_apaga_solo(self):
        self._activar("2026-01-01")
        estado = srv.estado_vacaciones(self.repo, self.hoy)
        self.assertFalse(estado.activo)
        self.assertIn("caducó", estado.motivo)

    def test_las_plantillas_delicadas_no_salen_solas(self):
        self._activar("2027-01-15")
        identificador = self._usuario()
        asignacion = self._asignar(identificador)
        self.repo.insertar("T_COLA_MAIL", {
            "ID_Usuario": identificador, "ID_Asignacion": asignacion,
            "Codigo_Plantilla": "ENCUESTA_T14", "F_Generado": datetime.now(),
            "F_Programada": self.hoy, "Estado": "BORRADOR"})
        resultado = srv.enviar_en_vacaciones(self.repo, self.cfg,
                                             self.enviador, self.hoy)
        self.assertEqual(resultado.enviados, [])
        self.assertTrue(any("revisión" in m for _, m in resultado.omitidos))

    def test_respeta_el_tope_diario(self):
        self._activar("2027-01-15")
        for fila in self.repo.libro.filas["T_CONFIG"]:
            if fila["Clave"] == "tope_envios_dia":
                fila["Valor"] = "2"
        for n in range(4):
            identificador = self._usuario(nombre=f"U{n}", email=f"u{n}@ejemplo.com")
            self.repo.insertar("T_COLA_MAIL", {
                "ID_Usuario": identificador, "Codigo_Plantilla": "CONSENTIMIENTO",
                "F_Generado": datetime.now(), "F_Programada": self.hoy,
                "Estado": "BORRADOR"})
        resultado = srv.enviar_en_vacaciones(self.repo, self.cfg,
                                             self.enviador, self.hoy)
        self.assertEqual(len(resultado.enviados), 2)
        self.assertTrue(any("tope" in m for _, m in resultado.omitidos))

    def test_no_reintenta_solo_lo_que_ya_fallo(self):
        """Sin nadie delante, reintentar a ciegas repetiría el error a diario."""
        class Roto(srv_correo.Enviador):
            def enviar(self, *_args, **_kwargs):
                raise RuntimeError("servidor caído")

        self._activar("2027-01-15")
        identificador = self._usuario()
        envio_id = self.repo.insertar("T_COLA_MAIL", {
            "ID_Usuario": identificador, "Codigo_Plantilla": "CONSENTIMIENTO",
            "F_Generado": datetime.now(), "F_Programada": self.hoy,
            "Estado": "BORRADOR"})
        srv.enviar(self.repo, self.cfg, Roto(), [envio_id])
        resultado = srv.enviar_en_vacaciones(self.repo, self.cfg,
                                             self.enviador, self.hoy)
        self.assertEqual(resultado.enviados, [])
        self.assertTrue(any("revises" in m for _, m in resultado.omitidos))

    def test_queda_constancia_de_lo_que_salio_sin_supervision(self):
        self._activar("2027-01-15")
        identificador = self._usuario()
        self.repo.insertar("T_COLA_MAIL", {
            "ID_Usuario": identificador, "Codigo_Plantilla": "CONSENTIMIENTO",
            "F_Generado": datetime.now(), "F_Programada": self.hoy,
            "Estado": "BORRADOR"})
        srv.enviar_en_vacaciones(self.repo, self.cfg, self.enviador, self.hoy)
        enviado = next(e for e in self.repo.listar("T_COLA_MAIL")
                       if e.get("Estado") == "ENVIADO")
        self.assertEqual(enviado["Aprobado_Por"], "MODO_VACACIONES")
        self.assertIn("modo vacaciones", srv.resumen_diario(self.repo, date.today()))


class Respuestas(Base):
    def _csv(self, filas: list[list], cabeceras: list[str]) -> Path:
        ruta = Path(self.temporal.name) / "respuestas.csv"
        with open(ruta, "w", encoding="utf-8-sig", newline="") as fichero:
            escritor = csv.writer(fichero, delimiter=";")
            escritor.writerow(cabeceras)
            escritor.writerows(filas)
        return ruta

    def test_reconoce_las_preguntas_por_su_texto(self):
        self.assertEqual(
            srv_respuestas._codigo_de("¿Cómo te sientes físicamente ahora mismo?"),
            "SENSACION")
        self.assertEqual(
            srv_respuestas._codigo_de("¿Quieres que hablemos para preparar tu "
                                      "próximo ciclo?"), "QUIERE_CITA")
        self.assertEqual(
            srv_respuestas._codigo_de("¿Qué te gustaría trabajar en el próximo ciclo?"),
            "PROXIMO_CICLO")

    def test_importa_y_marca_el_envio_como_respondido(self):
        identificador = self._usuario()
        asignacion = self._asignar(identificador)
        envio_id = self.repo.insertar("T_COLA_MAIL", {
            "ID_Usuario": identificador, "ID_Asignacion": asignacion,
            "Codigo_Plantilla": "ENCUESTA_T14", "F_Generado": datetime.now(),
            "Estado": "ENVIADO", "F_Envio": datetime(2026, 12, 10, 9, 0)})
        ruta = self._csv(
            [["21/12/2026 10:32", identificador, envio_id, "8", "No"]],
            ["Marca temporal", "ID_Usuario", "ID_Envio",
             "¿Cómo te sientes físicamente?", "¿Has tenido molestias o dolores?"])
        resultado = srv_respuestas.importar(self.repo, self.cfg, ruta)
        self.assertEqual(resultado.respuestas, 2)
        self.assertTrue(self.repo.obtener("T_COLA_MAIL", envio_id)["Respondido_SN"])

    def test_una_respuesta_de_usuario_desconocido_no_se_cuela(self):
        ruta = self._csv([["21/12/2026", "USR-9999", "", "8"]],
                         ["Marca temporal", "ID_Usuario", "ID_Envio",
                          "¿Cómo te sientes físicamente?"])
        resultado = srv_respuestas.importar(self.repo, self.cfg, ruta)
        self.assertEqual(resultado.sin_identificar, 1)
        self.assertEqual(resultado.respuestas, 0)

    def test_el_consentimiento_queda_registrado_con_fecha(self):
        identificador = self._usuario(consentido=False)
        ruta = self._csv([["21/12/2026 10:00", identificador, "", "Autorizo"]],
                         ["Marca temporal", "ID_Usuario", "ID_Envio",
                          "Autorizo el tratamiento de mis datos"])
        srv_respuestas.importar(self.repo, self.cfg, ruta)
        usuario = self.repo.obtener("T_USUARIOS", identificador)
        self.assertTrue(usuario["Consentimiento_SN"])
        self.assertEqual(usuario["F_Consentimiento"], date(2026, 12, 21))
        self.assertEqual(usuario["Origen_Consentimiento"], "FORM")

    def test_cambiar_de_objetivo_crea_uno_nuevo_y_archiva_el_anterior(self):
        identificador = self._usuario()
        anterior = self.repo.insertar("T_OBJETIVOS", {
            "ID_Usuario": identificador, "F_Registro": date(2026, 9, 1),
            "Tipo": "HIPERTROFIA", "Descripcion": "Ganar masa", "Prioridad": 1,
            "Estado": "ACTIVO"})
        ruta = self._csv(
            [["21/12/2026", identificador, "", "Lo cambio: quiero ganar fuerza"]],
            ["Marca temporal", "ID_Usuario", "ID_Envio", "¿Mantienes tu objetivo?"])
        srv_respuestas.importar(self.repo, self.cfg, ruta)
        self.assertEqual(self.repo.obtener("T_OBJETIVOS", anterior)["Estado"],
                         "MODIFICADO")
        activos = self.repo.listar(
            "T_OBJETIVOS", lambda o: (o.get("ID_Usuario") == identificador
                                      and o.get("Estado") == "ACTIVO"))
        self.assertEqual(len(activos), 1)
        self.assertIn("fuerza", activos[0]["Descripcion"])

    def test_responder_genera_el_correo_de_agradecimiento(self):
        identificador = self._usuario()
        ruta = self._csv([["21/12/2026", identificador, "", "9"]],
                         ["Marca temporal", "ID_Usuario", "ID_Envio",
                          "¿Cómo te sientes físicamente?"])
        srv_respuestas.importar(self.repo, self.cfg, ruta)
        codigos = [e["Codigo_Plantilla"] for e in srv.pendientes(self.repo)]
        self.assertIn("AGRADECIMIENTO", codigos)

    def test_no_duplica_al_importar_dos_veces(self):
        identificador = self._usuario()
        ruta = self._csv([["21/12/2026", identificador, "", "9"]],
                         ["Marca temporal", "ID_Usuario", "ID_Envio",
                          "¿Cómo te sientes físicamente?"])
        srv_respuestas.importar(self.repo, self.cfg, ruta)
        segunda = srv_respuestas.importar(self.repo, self.cfg, ruta)
        self.assertEqual(segunda.respuestas, 0)
        self.assertEqual(len(self.repo.listar("T_RESPUESTAS")), 1)


if __name__ == "__main__":
    unittest.main()
