"""Definición del esquema del libro de datos.

Este módulo es la única fuente de verdad sobre qué hojas tiene el libro Excel,
qué columnas tiene cada una y de qué tipo son. El generador del libro, el
validador y el repositorio trabajan todos a partir de aquí.

Ver docs/02-modelo-datos.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Tipo(Enum):
    TEXTO = "texto"
    TEXTO_LARGO = "texto_largo"
    ENTERO = "entero"
    DECIMAL = "decimal"
    FECHA = "fecha"
    FECHA_HORA = "fecha_hora"
    BOOL = "bool"          # se guarda como SI / NO
    LISTA = "lista"        # valor de un conjunto cerrado
    REF = "ref"            # ID de otra tabla


@dataclass(frozen=True)
class Columna:
    nombre: str
    tipo: Tipo = Tipo.TEXTO
    obligatorio: bool = False
    opciones: tuple[str, ...] = ()
    ref: str | None = None          # nombre de la tabla referida
    ancho: int = 18
    ayuda: str = ""

    def __post_init__(self) -> None:
        if self.tipo is Tipo.LISTA and not self.opciones:
            raise ValueError(f"La columna {self.nombre} es LISTA y no tiene opciones")
        if self.tipo is Tipo.REF and not self.ref:
            raise ValueError(f"La columna {self.nombre} es REF y no indica tabla")


@dataclass(frozen=True)
class Tabla:
    nombre: str
    descripcion: str
    columnas: tuple[Columna, ...]
    prefijo: str | None = None      # prefijo del ID autogenerado; None = ID manual
    grupo: str = "Otros"

    @property
    def clave(self) -> str:
        """Nombre de la columna que hace de clave primaria (siempre la primera)."""
        return self.columnas[0].nombre

    @property
    def nombres_columnas(self) -> list[str]:
        return [c.nombre for c in self.columnas]

    def columna(self, nombre: str) -> Columna:
        for c in self.columnas:
            if c.nombre == nombre:
                return c
        raise KeyError(f"{self.nombre} no tiene columna {nombre}")


# --- Conjuntos de opciones reutilizados -------------------------------------

SEXO = ("H", "M")
SEXO_BAREMO = ("H", "M", "AMBOS")
LADO = ("NA", "DERECHO", "IZQUIERDO")
CAPACIDAD = (
    "FUERZA", "POTENCIA", "RESISTENCIA", "MOVILIDAD",
    "EQUILIBRIO", "COMPOSICION", "CONTROL_MOTOR",
)
TIPO_MEDIDA = ("CUANTITATIVA", "TECNICA", "MIXTA", "CUALITATIVA")
PATRON = (
    "EMPUJE_H", "EMPUJE_V", "TRACCION_H", "TRACCION_V", "DOMINANTE_RODILLA",
    "DOMINANTE_CADERA", "CORE", "LOCOMOCION", "MONOARTICULAR", "MOVILIDAD",
)
TIPO_CICLO = ("MACRO", "MESO", "MICRO")
ENFOQUE = ("ADAPTACION", "ACUMULACION", "INTENSIFICACION", "REALIZACION", "DESCARGA")
MODO_CARGA = ("PCT1RM", "RPE", "RIR", "KG", "PESO_CORPORAL", "TIEMPO")
BLOQUE = ("CALENTAMIENTO", "PRINCIPAL", "ACCESORIO", "CORE", "VUELTA_CALMA")
ESTADO_ENVIO = ("BORRADOR", "REVISADO", "ENVIADO", "ERROR", "CANCELADO")
CODIGO_MAIL = (
    "CONSENTIMIENTO", "BIENVENIDA", "CHECKIN_MITAD", "ENCUESTA_T14",
    "CIERRE_CICLO", "AGRADECIMIENTO", "RECORDATORIO",
)


# --- Definición de las tablas ------------------------------------------------

TABLAS: tuple[Tabla, ...] = (

    # ---------------------------------------------------------------- sistema
    Tabla(
        "T_CONFIG", "Parámetros editables sin recompilar", grupo="Sistema",
        columnas=(
            Columna("Clave", Tipo.TEXTO, obligatorio=True, ancho=32),
            Columna("Valor", Tipo.TEXTO, ancho=42),
            Columna("Descripcion", Tipo.TEXTO, ancho=60),
        ),
    ),
    Tabla(
        "T_CONTADORES", "Último número usado por cada prefijo de ID", grupo="Sistema",
        columnas=(
            Columna("Prefijo", Tipo.TEXTO, obligatorio=True, ancho=12),
            Columna("Ultimo_Valor", Tipo.ENTERO, obligatorio=True, ancho=14),
        ),
    ),
    Tabla(
        "T_LOG", "Auditoría de escrituras y errores", grupo="Sistema", prefijo="LOG",
        columnas=(
            Columna("ID_Log", Tipo.TEXTO, obligatorio=True, ancho=14),
            Columna("F_Hora", Tipo.FECHA_HORA, obligatorio=True, ancho=20),
            Columna("Nivel", Tipo.TEXTO, ancho=12),
            Columna("Modulo", Tipo.TEXTO, ancho=22),
            Columna("Mensaje", Tipo.TEXTO_LARGO, ancho=70),
        ),
    ),

    # --------------------------------------------------------------- usuarios
    Tabla(
        "T_USUARIOS", "Ficha básica del usuario", grupo="Usuarios", prefijo="USR",
        columnas=(
            Columna("ID_Usuario", Tipo.TEXTO, obligatorio=True, ancho=14),
            Columna("Nombre", Tipo.TEXTO, obligatorio=True, ancho=22),
            Columna("Apellidos", Tipo.TEXTO, ancho=28),
            Columna("F_Nacimiento", Tipo.FECHA, obligatorio=True, ancho=14,
                    ayuda="La edad se calcula, nunca se guarda"),
            Columna("Sexo", Tipo.LISTA, obligatorio=True, opciones=SEXO, ancho=8),
            Columna("Email", Tipo.TEXTO, ancho=30),
            Columna("Telefono", Tipo.TEXTO, ancho=16),
            Columna("F_Alta", Tipo.FECHA, obligatorio=True, ancho=14),
            Columna("Estado", Tipo.LISTA, obligatorio=True, ancho=12,
                    opciones=("ACTIVO", "INACTIVO", "BAJA")),
            Columna("Consentimiento_SN", Tipo.BOOL, ancho=18),
            Columna("F_Consentimiento", Tipo.FECHA, ancho=18),
            Columna("Origen_Consentimiento", Tipo.LISTA, ancho=22,
                    opciones=("FORM", "PRESENCIAL")),
            Columna("Acepta_Emails_SN", Tipo.BOOL, ancho=18),
            Columna("Notas", Tipo.TEXTO_LARGO, ancho=50),
        ),
    ),
    Tabla(
        "T_SALUD", "Cribado PAR-Q+ y antecedentes. Histórico: vale el más reciente",
        grupo="Usuarios", prefijo="SAL",
        columnas=(
            Columna("ID_Salud", Tipo.TEXTO, obligatorio=True, ancho=14),
            Columna("ID_Usuario", Tipo.REF, obligatorio=True, ref="T_USUARIOS", ancho=14),
            Columna("F_Registro", Tipo.FECHA, obligatorio=True, ancho=14),
            Columna("PARQ_1_SN", Tipo.BOOL, ancho=12, ayuda="Afección cardíaca o tensión alta"),
            Columna("PARQ_2_SN", Tipo.BOOL, ancho=12, ayuda="Dolor en el pecho"),
            Columna("PARQ_3_SN", Tipo.BOOL, ancho=12, ayuda="Mareos o pérdida de consciencia"),
            Columna("PARQ_4_SN", Tipo.BOOL, ancho=12, ayuda="Otra enfermedad crónica"),
            Columna("PARQ_5_SN", Tipo.BOOL, ancho=12, ayuda="Medicación crónica"),
            Columna("PARQ_6_SN", Tipo.BOOL, ancho=12, ayuda="Problema óseo, articular o muscular"),
            Columna("PARQ_7_SN", Tipo.BOOL, ancho=12, ayuda="Solo actividad supervisada"),
            Columna("Apto_SN", Tipo.BOOL, ancho=12),
            Columna("Requiere_Informe_Medico_SN", Tipo.BOOL, ancho=26),
            Columna("TA_Sistolica", Tipo.ENTERO, ancho=14),
            Columna("TA_Diastolica", Tipo.ENTERO, ancho=14),
            Columna("FC_Reposo", Tipo.ENTERO, ancho=12),
            Columna("Patologias", Tipo.TEXTO_LARGO, ancho=40),
            Columna("Medicacion", Tipo.TEXTO_LARGO, ancho=40),
            Columna("Lesiones_Historial", Tipo.TEXTO_LARGO, ancho=40),
            Columna("Contraindicaciones", Tipo.TEXTO_LARGO, ancho=40),
            Columna("Observaciones", Tipo.TEXTO_LARGO, ancho=40),
        ),
    ),
    Tabla(
        "T_OBJETIVOS", "Objetivos declarados. Histórico", grupo="Usuarios", prefijo="OBJ",
        columnas=(
            Columna("ID_Objetivo", Tipo.TEXTO, obligatorio=True, ancho=14),
            Columna("ID_Usuario", Tipo.REF, obligatorio=True, ref="T_USUARIOS", ancho=14),
            Columna("F_Registro", Tipo.FECHA, obligatorio=True, ancho=14),
            Columna("Tipo", Tipo.LISTA, obligatorio=True, ancho=20, opciones=(
                "PERDER_GRASA", "HIPERTROFIA", "FUERZA", "SALUD_GENERAL",
                "RENDIMIENTO", "REHABILITACION", "OTRO")),
            Columna("Descripcion", Tipo.TEXTO_LARGO, obligatorio=True, ancho=50),
            Columna("Prioridad", Tipo.ENTERO, ancho=12, ayuda="1 = principal"),
            Columna("Horizonte_Sem", Tipo.ENTERO, ancho=16),
            Columna("Metrica", Tipo.TEXTO, ancho=24),
            Columna("Valor_Objetivo", Tipo.DECIMAL, ancho=16),
            Columna("Estado", Tipo.LISTA, obligatorio=True, ancho=14,
                    opciones=("ACTIVO", "CUMPLIDO", "MODIFICADO", "DESCARTADO")),
        ),
    ),
    Tabla(
        "T_DISPONIBILIDAD", "Días, horario y material con que cuenta el usuario",
        grupo="Usuarios", prefijo="DIS",
        columnas=(
            Columna("ID_Disponibilidad", Tipo.TEXTO, obligatorio=True, ancho=18),
            Columna("ID_Usuario", Tipo.REF, obligatorio=True, ref="T_USUARIOS", ancho=14),
            Columna("F_Registro", Tipo.FECHA, obligatorio=True, ancho=14),
            Columna("Dias_Semana", Tipo.ENTERO, obligatorio=True, ancho=14),
            Columna("Dias_Preferidos", Tipo.TEXTO, ancho=28, ayuda="L,M,X,J,V,S,D"),
            Columna("Franja", Tipo.LISTA, ancho=14,
                    opciones=("MANANA", "MEDIODIA", "TARDE", "NOCHE", "VARIABLE")),
            Columna("Min_Sesion", Tipo.ENTERO, obligatorio=True, ancho=14),
            Columna("Lugar", Tipo.LISTA, ancho=14, opciones=("GIMNASIO", "CASA", "MIXTO")),
            Columna("Material_Disponible", Tipo.TEXTO_LARGO, ancho=45),
        ),
    ),

    # ------------------------------------------------------------- valoración
    Tabla(
        "T_PROTOCOLOS", "Plantillas de valoración: qué pruebas hace cada perfil",
        grupo="Valoracion", prefijo="PRO",
        columnas=(
            Columna("ID_Protocolo", Tipo.TEXTO, obligatorio=True, ancho=16),
            Columna("Nombre", Tipo.TEXTO, obligatorio=True, ancho=30),
            Columna("Descripcion", Tipo.TEXTO_LARGO, ancho=50),
            Columna("Perfil_Objetivo", Tipo.TEXTO, ancho=28),
            Columna("Edad_Min", Tipo.ENTERO, ancho=10),
            Columna("Edad_Max", Tipo.ENTERO, ancho=10),
            Columna("Sexo", Tipo.LISTA, ancho=10, opciones=SEXO_BAREMO),
            Columna("Duracion_Est_Min", Tipo.ENTERO, ancho=18),
            Columna("Material_Necesario", Tipo.TEXTO_LARGO, ancho=40),
            Columna("Es_Predeterminado_SN", Tipo.BOOL, ancho=20),
            Columna("Activo_SN", Tipo.BOOL, ancho=12),
        ),
    ),
    Tabla(
        "T_PROTOCOLO_DET", "Pruebas que incluye cada protocolo",
        grupo="Valoracion", prefijo="PRD",
        columnas=(
            Columna("ID_Linea", Tipo.TEXTO, obligatorio=True, ancho=14),
            Columna("ID_Protocolo", Tipo.REF, obligatorio=True, ref="T_PROTOCOLOS", ancho=16),
            Columna("ID_Test", Tipo.REF, obligatorio=True, ref="T_CAT_TESTS", ancho=22),
            Columna("Orden", Tipo.ENTERO, obligatorio=True, ancho=10),
            Columna("Obligatorio_SN", Tipo.BOOL, ancho=16),
            Columna("Notas_Protocolo", Tipo.TEXTO_LARGO, ancho=45),
        ),
    ),
    Tabla(
        "T_CAT_TESTS", "Catálogo de pruebas de valoración",
        grupo="Valoracion",
        columnas=(
            Columna("ID_Test", Tipo.TEXTO, obligatorio=True, ancho=22),
            Columna("Nombre", Tipo.TEXTO, obligatorio=True, ancho=34),
            Columna("Capacidad", Tipo.LISTA, obligatorio=True, opciones=CAPACIDAD, ancho=18),
            Columna("Tipo_Medida", Tipo.LISTA, obligatorio=True, opciones=TIPO_MEDIDA, ancho=16),
            Columna("Unidad", Tipo.TEXTO, ancho=14),
            Columna("Bilateral_SN", Tipo.BOOL, ancho=14),
            Columna("Mejor_Es", Tipo.LISTA, ancho=12, opciones=("ALTO", "BAJO")),
            Columna("Requiere_Esfuerzo_Maximo_SN", Tipo.BOOL, ancho=28),
            Columna("Tiene_Baremo_SN", Tipo.BOOL, ancho=18),
            Columna("Calculada_SN", Tipo.BOOL, ancho=14,
                    ayuda="Se deriva de otras pruebas; no se teclea"),
            Columna("Decimales", Tipo.ENTERO, ancho=12),
            Columna("Material", Tipo.TEXTO, ancho=30),
            Columna("Protocolo", Tipo.TEXTO_LARGO, ancho=70),
            Columna("Activo_SN", Tipo.BOOL, ancho=12),
        ),
    ),
    Tabla(
        "T_TEST_CRITERIOS", "Compensaciones observables de las pruebas técnicas",
        grupo="Valoracion",
        columnas=(
            Columna("ID_Criterio", Tipo.TEXTO, obligatorio=True, ancho=20),
            Columna("ID_Test", Tipo.REF, obligatorio=True, ref="T_CAT_TESTS", ancho=22),
            Columna("Descripcion", Tipo.TEXTO_LARGO, obligatorio=True, ancho=55),
            Columna("Orden", Tipo.ENTERO, ancho=10),
            Columna("Es_Dolor_SN", Tipo.BOOL, ancho=14,
                    ayuda="Si se marca, la puntuación técnica pasa a 0"),
        ),
    ),
    Tabla(
        "T_BAREMOS", "Tablas normativas por sexo y edad. Ver docs/11",
        grupo="Valoracion", prefijo="BAR",
        columnas=(
            Columna("ID_Baremo", Tipo.TEXTO, obligatorio=True, ancho=14),
            Columna("ID_Test", Tipo.REF, obligatorio=True, ref="T_CAT_TESTS", ancho=22),
            Columna("Sexo", Tipo.LISTA, obligatorio=True, opciones=SEXO_BAREMO, ancho=10),
            Columna("Edad_Min", Tipo.ENTERO, obligatorio=True, ancho=10),
            Columna("Edad_Max", Tipo.ENTERO, obligatorio=True, ancho=10),
            Columna("Valor_Min", Tipo.DECIMAL, obligatorio=True, ancho=12),
            Columna("Valor_Max", Tipo.DECIMAL, obligatorio=True, ancho=12),
            Columna("Categoria", Tipo.TEXTO, obligatorio=True, ancho=18),
            Columna("Puntuacion", Tipo.ENTERO, obligatorio=True, ancho=12),
            Columna("Fuente", Tipo.TEXTO, ancho=30),
            Columna("Solidez", Tipo.LISTA, ancho=12,
                    opciones=("ALTA", "MEDIA", "BAJA", "SIN_BAREMO")),
        ),
    ),
    Tabla(
        "T_VALORACIONES", "Cabecera de cada valoración física",
        grupo="Valoracion", prefijo="VAL",
        columnas=(
            Columna("ID_Valoracion", Tipo.TEXTO, obligatorio=True, ancho=16),
            Columna("ID_Usuario", Tipo.REF, obligatorio=True, ref="T_USUARIOS", ancho=14),
            Columna("ID_Protocolo", Tipo.REF, obligatorio=True, ref="T_PROTOCOLOS", ancho=16),
            Columna("Fecha", Tipo.FECHA, obligatorio=True, ancho=14),
            Columna("Tipo", Tipo.LISTA, obligatorio=True, ancho=16,
                    opciones=("INICIAL", "SEGUIMIENTO", "FINAL_CICLO")),
            Columna("Evaluador", Tipo.TEXTO, ancho=22),
            Columna("ID_Asignacion", Tipo.REF, ref="T_ASIGNACIONES", ancho=16),
            Columna("Bloqueo_Esfuerzo_Maximo_SN", Tipo.BOOL, ancho=26),
            Columna("Observaciones", Tipo.TEXTO_LARGO, ancho=50),
            Columna("Ruta_PDF", Tipo.TEXTO, ancho=40),
        ),
    ),
    Tabla(
        "T_VALORACION_DET", "Resultado de cada prueba. Formato largo",
        grupo="Valoracion", prefijo="VDT",
        columnas=(
            Columna("ID_Linea", Tipo.TEXTO, obligatorio=True, ancho=14),
            Columna("ID_Valoracion", Tipo.REF, obligatorio=True, ref="T_VALORACIONES", ancho=16),
            Columna("ID_Test", Tipo.REF, obligatorio=True, ref="T_CAT_TESTS", ancho=22),
            Columna("Lado", Tipo.LISTA, opciones=LADO, ancho=12),
            Columna("Valor", Tipo.DECIMAL, ancho=12),
            Columna("Valor_Tecnica", Tipo.ENTERO, ancho=14, ayuda="0-3"),
            Columna("Unidad", Tipo.TEXTO, ancho=12),
            Columna("Puntuacion", Tipo.ENTERO, ancho=12),
            Columna("Categoria", Tipo.TEXTO, ancho=18),
            Columna("Notas", Tipo.TEXTO_LARGO, ancho=40),
        ),
    ),
    Tabla(
        "T_VALORACION_CRITERIOS", "Compensaciones observadas en cada prueba técnica",
        grupo="Valoracion", prefijo="VCR",
        columnas=(
            Columna("ID_Linea", Tipo.TEXTO, obligatorio=True, ancho=14),
            Columna("ID_Valoracion", Tipo.REF, obligatorio=True, ref="T_VALORACIONES", ancho=16),
            Columna("ID_Test", Tipo.REF, obligatorio=True, ref="T_CAT_TESTS", ancho=22),
            Columna("ID_Criterio", Tipo.REF, obligatorio=True, ref="T_TEST_CRITERIOS", ancho=20),
            Columna("Lado", Tipo.LISTA, opciones=LADO, ancho=12),
            Columna("Observado_SN", Tipo.BOOL, ancho=14),
        ),
    ),
    Tabla(
        "T_CAPACIDADES", "Puntuación agregada por capacidad. Congelada por valoración",
        grupo="Valoracion", prefijo="CAP",
        columnas=(
            Columna("ID_Linea", Tipo.TEXTO, obligatorio=True, ancho=14),
            Columna("ID_Valoracion", Tipo.REF, obligatorio=True, ref="T_VALORACIONES", ancho=16),
            Columna("Capacidad", Tipo.LISTA, obligatorio=True, opciones=CAPACIDAD, ancho=18),
            Columna("Puntuacion", Tipo.ENTERO, ancho=12),
            Columna("N_Pruebas", Tipo.ENTERO, ancho=12,
                    ayuda="0 = el eje no se dibuja en el radar"),
        ),
    ),

    # ---------------------------------------------------------- entrenamiento
    Tabla(
        "T_EJERCICIOS", "Catálogo de ejercicios", grupo="Entrenamiento", prefijo="EJ",
        columnas=(
            Columna("ID_Ejercicio", Tipo.TEXTO, obligatorio=True, ancho=14),
            Columna("Nombre", Tipo.TEXTO, obligatorio=True, ancho=34),
            Columna("Patron", Tipo.LISTA, obligatorio=True, opciones=PATRON, ancho=20),
            Columna("Grupo_Principal", Tipo.TEXTO, obligatorio=True, ancho=20),
            Columna("Grupos_Secundarios", Tipo.TEXTO, ancho=28),
            Columna("Material", Tipo.TEXTO, ancho=24),
            Columna("Nivel", Tipo.ENTERO, ancho=10, ayuda="1 principiante - 3 avanzado"),
            Columna("Unilateral_SN", Tipo.BOOL, ancho=14),
            Columna("Es_Basico_SN", Tipo.BOOL, ancho=14),
            Columna("Incremento_Kg", Tipo.DECIMAL, ancho=16,
                    ayuda="Salto mínimo real de carga"),
            Columna("Video_URL", Tipo.TEXTO, ancho=40),
            Columna("Contraindicaciones", Tipo.TEXTO_LARGO, ancho=40),
            Columna("Activo_SN", Tipo.BOOL, ancho=12),
        ),
    ),
    Tabla(
        "T_CICLOS", "Árbol de ciclos: macro, meso y micro, con ID_Padre",
        grupo="Entrenamiento", prefijo="CIC",
        columnas=(
            Columna("ID_Ciclo", Tipo.TEXTO, obligatorio=True, ancho=14),
            Columna("Nombre", Tipo.TEXTO, obligatorio=True, ancho=34),
            Columna("Tipo", Tipo.LISTA, obligatorio=True, opciones=TIPO_CICLO, ancho=10),
            Columna("ID_Padre", Tipo.REF, ref="T_CICLOS", ancho=14),
            Columna("Orden", Tipo.ENTERO, ancho=10),
            Columna("Duracion_Sem", Tipo.ENTERO, obligatorio=True, ancho=14),
            Columna("Objetivo_Ciclo", Tipo.TEXTO, ancho=30),
            Columna("Enfoque", Tipo.LISTA, opciones=ENFOQUE, ancho=18),
            Columna("Es_Plantilla_SN", Tipo.BOOL, ancho=16),
            Columna("Origen", Tipo.LISTA, ancho=12, opciones=("MANUAL", "IA", "CLONADO")),
            Columna("ID_Origen", Tipo.TEXTO, ancho=14),
            Columna("Notas", Tipo.TEXTO_LARGO, ancho=45),
        ),
    ),
    Tabla(
        "T_SESIONES", "Sesiones de un microciclo", grupo="Entrenamiento", prefijo="SES",
        columnas=(
            Columna("ID_Sesion", Tipo.TEXTO, obligatorio=True, ancho=14),
            Columna("ID_Ciclo", Tipo.REF, obligatorio=True, ref="T_CICLOS", ancho=14),
            Columna("Num_Dia", Tipo.ENTERO, obligatorio=True, ancho=10),
            Columna("Nombre", Tipo.TEXTO, ancho=30),
            Columna("Tipo", Tipo.LISTA, ancho=18, opciones=(
                "FUERZA", "CARDIO", "MOVILIDAD", "MIXTA", "DESCANSO_ACTIVO")),
            Columna("Duracion_Est_Min", Tipo.ENTERO, ancho=18),
            Columna("Notas", Tipo.TEXTO_LARGO, ancho=45),
        ),
    ),
    Tabla(
        "T_SESION_DET", "Líneas de ejercicio de cada sesión",
        grupo="Entrenamiento", prefijo="LIN",
        columnas=(
            Columna("ID_Linea", Tipo.TEXTO, obligatorio=True, ancho=14),
            Columna("ID_Sesion", Tipo.REF, obligatorio=True, ref="T_SESIONES", ancho=14),
            Columna("Orden", Tipo.ENTERO, obligatorio=True, ancho=10),
            Columna("Bloque", Tipo.LISTA, obligatorio=True, opciones=BLOQUE, ancho=18),
            Columna("ID_Ejercicio", Tipo.REF, obligatorio=True, ref="T_EJERCICIOS", ancho=14),
            Columna("Grupo_Serie", Tipo.TEXTO, ancho=14, ayuda="Superseries y circuitos"),
            Columna("Series", Tipo.ENTERO, ancho=10),
            Columna("Reps", Tipo.TEXTO, ancho=12, ayuda='8, 8-10, AMRAP'),
            Columna("Modo_Carga", Tipo.LISTA, opciones=MODO_CARGA, ancho=16),
            Columna("Valor_Carga", Tipo.DECIMAL, ancho=14),
            Columna("Tempo", Tipo.TEXTO, ancho=12),
            Columna("Descanso_Seg", Tipo.ENTERO, ancho=14),
            Columna("Progresion", Tipo.TEXTO, ancho=22, ayuda="LINEAL:+2.5, PCT:70,75,80..."),
            Columna("Notas", Tipo.TEXTO_LARGO, ancho=40),
        ),
    ),
    Tabla(
        "T_1RM", "Repetición máxima por usuario y ejercicio. Histórico",
        grupo="Entrenamiento", prefijo="RM",
        columnas=(
            Columna("ID_Registro", Tipo.TEXTO, obligatorio=True, ancho=14),
            Columna("ID_Usuario", Tipo.REF, obligatorio=True, ref="T_USUARIOS", ancho=14),
            Columna("ID_Ejercicio", Tipo.REF, obligatorio=True, ref="T_EJERCICIOS", ancho=14),
            Columna("Fecha", Tipo.FECHA, obligatorio=True, ancho=14),
            Columna("Valor_1RM", Tipo.DECIMAL, obligatorio=True, ancho=12),
            Columna("Metodo", Tipo.LISTA, ancho=14,
                    opciones=("DIRECTO", "EPLEY", "BRZYCKI", "LOMBARDI")),
            Columna("Peso_Usado", Tipo.DECIMAL, ancho=14),
            Columna("Reps_Usadas", Tipo.ENTERO, ancho=14),
            Columna("Origen", Tipo.LISTA, ancho=14, opciones=("MANUAL", "VALORACION", "TEST")),
            Columna("Fiabilidad", Tipo.LISTA, ancho=12, opciones=("ALTA", "MEDIA", "BAJA")),
        ),
    ),
    Tabla(
        "T_ASIGNACIONES", "Macrociclo asignado a un usuario",
        grupo="Entrenamiento", prefijo="ASG",
        columnas=(
            Columna("ID_Asignacion", Tipo.TEXTO, obligatorio=True, ancho=16),
            Columna("ID_Usuario", Tipo.REF, obligatorio=True, ref="T_USUARIOS", ancho=14),
            Columna("ID_Ciclo", Tipo.REF, obligatorio=True, ref="T_CICLOS", ancho=14),
            Columna("F_Inicio", Tipo.FECHA, obligatorio=True, ancho=14),
            Columna("F_Fin_Prevista", Tipo.FECHA, obligatorio=True, ancho=16),
            Columna("Estado", Tipo.LISTA, obligatorio=True, ancho=16, opciones=(
                "PLANIFICADA", "EN_CURSO", "FINALIZADA", "INTERRUMPIDA")),
            Columna("ID_Asignacion_Anterior", Tipo.TEXTO, ancho=22),
            Columna("ID_Objetivo", Tipo.REF, ref="T_OBJETIVOS", ancho=14),
            Columna("Notas", Tipo.TEXTO_LARGO, ancho=45),
        ),
    ),
    Tabla(
        "T_ASIG_FASES", "Calendario de fases derivado, congelado al asignar",
        grupo="Entrenamiento", prefijo="AFA",
        columnas=(
            Columna("ID_Linea", Tipo.TEXTO, obligatorio=True, ancho=14),
            Columna("ID_Asignacion", Tipo.REF, obligatorio=True, ref="T_ASIGNACIONES", ancho=16),
            Columna("ID_Ciclo", Tipo.REF, obligatorio=True, ref="T_CICLOS", ancho=14),
            Columna("Nivel", Tipo.LISTA, obligatorio=True, opciones=TIPO_CICLO, ancho=10),
            Columna("F_Inicio", Tipo.FECHA, obligatorio=True, ancho=14),
            Columna("F_Fin", Tipo.FECHA, obligatorio=True, ancho=14),
            Columna("Estado", Tipo.TEXTO, ancho=16),
        ),
    ),

    # ---------------------------------------------------------- comunicación
    Tabla(
        "T_PLANTILLAS_MAIL", "Plantillas de correo con marcadores",
        grupo="Comunicacion", prefijo="PLM",
        columnas=(
            Columna("ID_Plantilla", Tipo.TEXTO, obligatorio=True, ancho=14),
            Columna("Codigo", Tipo.LISTA, obligatorio=True, opciones=CODIGO_MAIL, ancho=20),
            Columna("Asunto", Tipo.TEXTO, obligatorio=True, ancho=45),
            Columna("Cuerpo_HTML", Tipo.TEXTO_LARGO, ancho=70),
            Columna("Instruccion_IA", Tipo.TEXTO_LARGO, ancho=55),
            Columna("Requiere_Revision_SN", Tipo.BOOL, ancho=20),
            Columna("Permite_Modo_Vacaciones_SN", Tipo.BOOL, ancho=26),
            Columna("URL_Form", Tipo.TEXTO, ancho=45),
            Columna("Activo_SN", Tipo.BOOL, ancho=12),
        ),
    ),
    Tabla(
        "T_COLA_MAIL", "Bandeja de salida con estados. Nada sale sin pasar por aquí",
        grupo="Comunicacion", prefijo="ENV",
        columnas=(
            Columna("ID_Envio", Tipo.TEXTO, obligatorio=True, ancho=14),
            Columna("ID_Usuario", Tipo.REF, obligatorio=True, ref="T_USUARIOS", ancho=14),
            Columna("ID_Asignacion", Tipo.REF, ref="T_ASIGNACIONES", ancho=16),
            Columna("Codigo_Plantilla", Tipo.LISTA, obligatorio=True,
                    opciones=CODIGO_MAIL, ancho=20),
            Columna("F_Generado", Tipo.FECHA_HORA, obligatorio=True, ancho=20),
            Columna("F_Programada", Tipo.FECHA, ancho=16),
            Columna("Estado", Tipo.LISTA, obligatorio=True, opciones=ESTADO_ENVIO, ancho=14),
            Columna("Nota_Entrenador", Tipo.TEXTO_LARGO, ancho=50),
            Columna("Cuerpo_IA", Tipo.TEXTO_LARGO, ancho=60),
            Columna("Asunto_Final", Tipo.TEXTO, ancho=45),
            Columna("Cuerpo_Final", Tipo.TEXTO_LARGO, ancho=70),
            Columna("F_Envio", Tipo.FECHA_HORA, ancho=20),
            Columna("Aprobado_Por", Tipo.LISTA, ancho=20,
                    opciones=("ENTRENADOR", "MODO_VACACIONES")),
            Columna("Enlace_Form_Prefill", Tipo.TEXTO, ancho=55),
            Columna("F_Recordatorio", Tipo.FECHA, ancho=16),
            Columna("Respondido_SN", Tipo.BOOL, ancho=14),
            Columna("Quiere_Cita", Tipo.TEXTO, ancho=14),
            Columna("Error", Tipo.TEXTO_LARGO, ancho=45),
        ),
    ),
    Tabla(
        "T_RESPUESTAS", "Respuestas de los formularios. Formato largo",
        grupo="Comunicacion", prefijo="RES",
        columnas=(
            Columna("ID_Respuesta", Tipo.TEXTO, obligatorio=True, ancho=14),
            Columna("ID_Usuario", Tipo.REF, obligatorio=True, ref="T_USUARIOS", ancho=14),
            Columna("ID_Envio", Tipo.REF, ref="T_COLA_MAIL", ancho=14),
            Columna("F_Respuesta", Tipo.FECHA_HORA, obligatorio=True, ancho=20),
            Columna("Codigo_Pregunta", Tipo.TEXTO, obligatorio=True, ancho=22),
            Columna("Valor", Tipo.TEXTO_LARGO, ancho=55),
            Columna("Origen", Tipo.LISTA, ancho=12, opciones=("FORM", "MANUAL")),
        ),
    ),

    # -------------------------------------------------------------------- IA
    Tabla(
        "T_CONOCIMIENTO", "Criterio del entrenador que se inyecta a la IA",
        grupo="IA", prefijo="CON",
        columnas=(
            Columna("ID_Conocimiento", Tipo.TEXTO, obligatorio=True, ancho=18),
            Columna("Categoria", Tipo.TEXTO, obligatorio=True, ancho=24),
            Columna("Titulo", Tipo.TEXTO, obligatorio=True, ancho=40),
            Columna("Contenido", Tipo.TEXTO_LARGO, obligatorio=True, ancho=70),
            Columna("Tags", Tipo.TEXTO, ancho=34),
            Columna("Prioridad", Tipo.ENTERO, ancho=12),
            Columna("Origen", Tipo.LISTA, ancho=16, opciones=("MANUAL", "APRENDIZAJE")),
            Columna("F_Creacion", Tipo.FECHA, ancho=14),
            Columna("Activo_SN", Tipo.BOOL, ancho=12),
        ),
    ),
    Tabla(
        "T_REGLAS", "Restricciones. Las duras las bloquea el validador",
        grupo="IA", prefijo="REG",
        columnas=(
            Columna("ID_Regla", Tipo.TEXTO, obligatorio=True, ancho=14),
            Columna("Tipo", Tipo.LISTA, obligatorio=True, opciones=("DURA", "BLANDA"), ancho=12),
            Columna("Ambito", Tipo.TEXTO, ancho=24),
            Columna("Condicion", Tipo.TEXTO_LARGO, obligatorio=True, ancho=50),
            Columna("Accion", Tipo.TEXTO_LARGO, obligatorio=True, ancho=50),
            Columna("Prioridad", Tipo.ENTERO, ancho=12),
            Columna("Activo_SN", Tipo.BOOL, ancho=12),
        ),
    ),
    Tabla(
        "T_IA_LOG", "Trazabilidad de cada interacción con el modelo",
        grupo="IA", prefijo="IAL",
        columnas=(
            Columna("ID_Interaccion", Tipo.TEXTO, obligatorio=True, ancho=16),
            Columna("ID_Usuario", Tipo.REF, ref="T_USUARIOS", ancho=14),
            Columna("F_Hora", Tipo.FECHA_HORA, obligatorio=True, ancho=20),
            Columna("Proveedor", Tipo.TEXTO, ancho=16),
            Columna("Modelo", Tipo.TEXTO, ancho=26),
            Columna("Iteracion", Tipo.ENTERO, ancho=12),
            Columna("Feedback_Entrenador", Tipo.TEXTO_LARGO, ancho=55),
            Columna("ID_Ciclo_Generado", Tipo.TEXTO, ancho=18),
            Columna("Tokens", Tipo.ENTERO, ancho=12),
            Columna("Duracion_Seg", Tipo.DECIMAL, ancho=14),
            Columna("Estado", Tipo.TEXTO, ancho=16),
        ),
    ),
)


# --- Índices y comprobaciones ------------------------------------------------

POR_NOMBRE: dict[str, Tabla] = {t.nombre: t for t in TABLAS}


def tabla(nombre: str) -> Tabla:
    try:
        return POR_NOMBRE[nombre]
    except KeyError:
        raise KeyError(f"No existe la tabla {nombre}") from None


def _comprobar_coherencia() -> None:
    """Las referencias deben apuntar a tablas que existen y los prefijos ser únicos."""
    prefijos: dict[str, str] = {}
    for t in TABLAS:
        if t.prefijo:
            if t.prefijo in prefijos:
                raise ValueError(
                    f"Prefijo {t.prefijo} repetido en {t.nombre} y {prefijos[t.prefijo]}")
            prefijos[t.prefijo] = t.nombre
        for c in t.columnas:
            if c.tipo is Tipo.REF and c.ref not in POR_NOMBRE:
                raise ValueError(f"{t.nombre}.{c.nombre} referencia a {c.ref}, que no existe")


_comprobar_coherencia()
