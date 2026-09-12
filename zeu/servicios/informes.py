"""Informe de valoración física en PDF.

El entregable que el usuario se lleva en la mano. Ver docs/05, apartado
"El informe en PDF".
"""

from __future__ import annotations

import tempfile
from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                              # noqa: E402
from reportlab.lib import colors                             # noqa: E402
from reportlab.lib.enums import TA_CENTER                    # noqa: E402
from reportlab.lib.pagesizes import A4                       # noqa: E402
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # noqa: E402
from reportlab.lib.units import mm                           # noqa: E402
from reportlab.platypus import (                             # noqa: E402
    Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle)

from ..datos.repositorio import Repositorio
from ..nucleo.config import Config
from ..nucleo.fechas import formatear
from ..ui import estilo
from . import valoracion as srv

# Serie anterior y actual: el mismo azul en dos pasos (claro -> oscuro), que es
# como se codifica el mismo dato en dos momentos. Ambos pasan el 3:1 sobre papel
# blanco; además van con trazo distinto y con la tabla comparativa al lado, que
# es lo que hace que la identidad no dependa solo del color.
AZUL_ANTES = "#5E8CAE"
AZUL_AHORA = "#356283"

ETIQUETA_CAPACIDAD = {
    "COMPOSICION": "Composición\ncorporal", "FUERZA": "Fuerza",
    "CONTROL_MOTOR": "Control\nmotor", "POTENCIA": "Potencia",
    "RESISTENCIA": "Resistencia", "MOVILIDAD": "Movilidad",
    "EQUILIBRIO": "Equilibrio",
}


def _estilos() -> dict:
    base = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle("t", parent=base["Title"], fontSize=20, leading=24,
                                 textColor=colors.HexColor(estilo.AZUL_OSCURO),
                                 alignment=0, spaceAfter=2),
        "subtitulo": ParagraphStyle("s", parent=base["Normal"], fontSize=10.5,
                                    textColor=colors.HexColor("#6C7A85"), spaceAfter=10),
        "seccion": ParagraphStyle("h", parent=base["Heading2"], fontSize=12.5,
                                  textColor=colors.HexColor(estilo.AZUL_OSCURO),
                                  spaceBefore=12, spaceAfter=5),
        "texto": ParagraphStyle("p", parent=base["Normal"], fontSize=9.5, leading=13),
        "pie": ParagraphStyle("f", parent=base["Normal"], fontSize=8,
                              textColor=colors.HexColor("#9AA5AD"), alignment=TA_CENTER),
        "celda": ParagraphStyle("c", parent=base["Normal"], fontSize=8.5, leading=11),
    }


def grafico_radar(actual: dict[str, tuple[int, int]],
                  anterior: dict[str, tuple[int, int]] | None,
                  destino: Path) -> Path | None:
    """Radar de capacidades. Solo se dibujan los ejes que se han medido."""
    ejes = [c for c in srv.CAPACIDADES if c in actual]
    if len(ejes) < 3:
        return None      # con menos de tres ejes un radar no dice nada

    import math
    angulos = [n / len(ejes) * 2 * math.pi for n in range(len(ejes))]
    angulos += angulos[:1]

    figura = plt.figure(figsize=(5.6, 5.0), dpi=200)
    ejes_polares = plt.subplot(111, polar=True)
    ejes_polares.set_theta_offset(math.pi / 2)
    ejes_polares.set_theta_direction(-1)
    ejes_polares.set_ylim(0, 100)
    ejes_polares.set_rgrids([25, 50, 75, 100], labels=["25", "50", "75", "100"],
                            angle=90, fontsize=7, color="#9AA5AD")
    ejes_polares.set_xticks(angulos[:-1])
    ejes_polares.set_xticklabels(
        [ETIQUETA_CAPACIDAD.get(c, c.capitalize()) for c in ejes],
        fontsize=9, color="#333333")
    ejes_polares.grid(color="#DCE3E8", linewidth=0.8)
    ejes_polares.spines["polar"].set_color("#DCE3E8")

    if anterior:
        valores = [anterior.get(c, (0, 0))[0] for c in ejes]
        if any(valores):
            valores += valores[:1]
            ejes_polares.plot(angulos, valores, linewidth=1.6, linestyle="--",
                              color=AZUL_ANTES, marker="o", markersize=4,
                              markerfacecolor="white", label="Valoración anterior")
            ejes_polares.fill(angulos, valores, color=AZUL_ANTES, alpha=0.08)

    valores = [actual[c][0] for c in ejes]
    valores += valores[:1]
    ejes_polares.plot(angulos, valores, linewidth=2.2, color=AZUL_AHORA,
                      marker="o", markersize=5, label="Esta valoración")
    ejes_polares.fill(angulos, valores, color=AZUL_AHORA, alpha=0.16)

    # Etiqueta directa del valor en cada eje: el número se lee aunque el color no.
    for angulo, valor in zip(angulos[:-1], valores[:-1]):
        ejes_polares.annotate(str(valor), (angulo, min(valor + 9, 103)),
                              ha="center", va="center", fontsize=8,
                              color="#333333", weight="bold")

    if anterior:
        ejes_polares.legend(loc="upper center", bbox_to_anchor=(0.5, -0.06),
                            ncol=2, frameon=False, fontsize=8.5)
    plt.tight_layout()
    figura.savefig(destino, bbox_inches="tight", facecolor="white")
    plt.close(figura)
    return destino


def _tabla(datos: list[list], anchos: list[float], cabecera: bool = True) -> Table:
    tabla = Table(datos, colWidths=anchos, repeatRows=1 if cabecera else 0)
    orden = [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, colors.HexColor("#E2E8EC")),
    ]
    if cabecera:
        orden += [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(estilo.AZUL)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]
    tabla.setStyle(TableStyle(orden))
    return tabla


def _color_puntos(puntos: int | None) -> colors.Color:
    if puntos is None:
        return colors.HexColor("#6C7A85")
    if puntos >= 85:
        return colors.HexColor(estilo.BUENO)
    if puntos >= 60:
        return colors.HexColor(estilo.MEDIO)
    return colors.HexColor(estilo.BAJO)


def generar(repo: Repositorio, cfg: Config, id_valoracion: str,
            destino: Path | None = None) -> Path:
    resumen = srv.resumir(repo, id_valoracion)
    usuario = resumen.usuario
    estilos = _estilos()
    nombre = " ".join(x for x in (usuario.get("Nombre"), usuario.get("Apellidos")) if x)

    anteriores = [
        v for v in repo.listar(
            "T_VALORACIONES",
            lambda v: (v.get("ID_Usuario") == usuario.get("ID_Usuario")
                       and v.get("ID_Valoracion") != id_valoracion
                       and v.get("ID_Protocolo") == resumen.valoracion.get("ID_Protocolo")),
            orden="Fecha", descendente=True)
        if v.get("Fecha") and resumen.valoracion.get("Fecha")
        and v["Fecha"] < resumen.valoracion["Fecha"]]
    anterior = srv.resumir(repo, anteriores[0]["ID_Valoracion"]) if anteriores else None

    if destino is None:
        carpeta = Path(cfg.datos.libro).parent / "salidas" / "valoraciones"
        carpeta.mkdir(parents=True, exist_ok=True)
        destino = carpeta / (
            f"valoracion_{usuario.get('ID_Usuario')}_"
            f"{resumen.valoracion.get('Fecha', date.today()):%Y%m%d}.pdf")
    destino.parent.mkdir(parents=True, exist_ok=True)

    documento = SimpleDocTemplate(
        str(destino), pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title=f"Valoración física — {nombre}",
        author=cfg.negocio.nombre_comercial)
    partes = []

    # -- cabecera --
    logo = estilo.ruta_logo()
    protocolo = repo.obtener("T_PROTOCOLOS", resumen.valoracion.get("ID_Protocolo")) or {}
    encabezado = [[
        Paragraph(f"<b>{cfg.negocio.nombre_comercial}</b>", estilos["titulo"]),
        Paragraph(f"{cfg.negocio.lema}<br/>{formatear(resumen.valoracion.get('Fecha'))}",
                  estilos["subtitulo"]),
    ]]
    if logo and logo.exists():
        encabezado[0][0] = Image(str(logo), width=34 * mm, height=16 * mm, kind="proportional")
    tabla_encabezado = Table(encabezado, colWidths=[100 * mm, 74 * mm])
    tabla_encabezado.setStyle(TableStyle([("ALIGN", (1, 0), (1, 0), "RIGHT"),
                                          ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    partes += [tabla_encabezado, Spacer(1, 6)]

    partes.append(Paragraph("Informe de valoración física", estilos["titulo"]))
    partes.append(Paragraph(
        f"{nombre} · {resumen.edad} años · "
        f"{'Hombre' if usuario.get('Sexo') == 'H' else 'Mujer'} · "
        f"Protocolo: {protocolo.get('Nombre', '')}", estilos["subtitulo"]))

    # -- resumen y radar --
    partes.append(Paragraph("Resumen", estilos["seccion"]))
    with tempfile.TemporaryDirectory() as temporal:
        grafico = grafico_radar(resumen.por_capacidad,
                                anterior.por_capacidad if anterior else None,
                                Path(temporal) / "radar.png")
        filas_capacidad = [["Capacidad", "Puntuación", "Pruebas"]]
        for capacidad in srv.CAPACIDADES:
            if capacidad not in resumen.por_capacidad:
                continue
            puntos, cuantas = resumen.por_capacidad[capacidad]
            filas_capacidad.append([
                ETIQUETA_CAPACIDAD.get(capacidad, capacidad).replace("\n", " "),
                f"{puntos}/100", str(cuantas)])
        if resumen.global_ is not None:
            filas_capacidad.append(["Global", f"{resumen.global_}/100", ""])
        tabla_capacidad = _tabla(filas_capacidad, [42 * mm, 22 * mm, 16 * mm])
        tabla_capacidad.setStyle(TableStyle([
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("LINEABOVE", (0, -1), (-1, -1), 0.8, colors.HexColor(estilo.AZUL)),
        ]))

        if grafico:
            bloque = Table([[Image(str(grafico), width=96 * mm, height=86 * mm,
                                   kind="proportional"), tabla_capacidad]],
                           colWidths=[96 * mm, 82 * mm])
            bloque.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
            partes.append(bloque)
        else:
            partes.append(tabla_capacidad)
            partes.append(Paragraph(
                "Se han medido menos de tres capacidades, así que no se dibuja el "
                "radar: con dos ejes no aporta nada.", estilos["texto"]))

        # -- hallazgos --
        if resumen.hallazgos:
            partes.append(Paragraph("Hallazgos", estilos["seccion"]))
            filas = [["", "Hallazgo", "Detalle"]]
            for hallazgo in resumen.hallazgos:
                marca = "!" if hallazgo.gravedad == "ALERTA" else "·"
                filas.append([marca, Paragraph(f"<b>{hallazgo.titulo}</b>", estilos["celda"]),
                              Paragraph(hallazgo.detalle, estilos["celda"])])
            tabla = _tabla(filas, [6 * mm, 45 * mm, 123 * mm])
            for n, hallazgo in enumerate(resumen.hallazgos, start=1):
                if hallazgo.gravedad == "ALERTA":
                    tabla.setStyle(TableStyle([
                        ("TEXTCOLOR", (0, n), (0, n), colors.HexColor(estilo.ALERTA)),
                        ("FONTNAME", (0, n), (0, n), "Helvetica-Bold")]))
            partes.append(tabla)

        # -- comparativa --
        if anterior:
            comparacion = srv.comparar(anterior, resumen)
            if comparacion:
                partes.append(Paragraph(
                    f"Comparativa con la valoración de "
                    f"{formatear(anterior.valoracion.get('Fecha'))}", estilos["seccion"]))
                filas = [["Prueba", "Antes", "Ahora", "Diferencia"]]
                for linea in comparacion:
                    prueba = repo.obtener("T_CAT_TESTS", linea["ID_Test"]) or {}
                    signo = "+" if linea["diferencia"] > 0 else ""
                    filas.append([
                        Paragraph(prueba.get("Nombre") or linea["ID_Test"], estilos["celda"]),
                        f"{linea['antes']:g}", f"{linea['ahora']:g}",
                        f"{signo}{linea['diferencia']:g} {prueba.get('Unidad') or ''}"])
                partes.append(_tabla(filas, [80 * mm, 25 * mm, 25 * mm, 44 * mm]))

        # -- detalle --
        partes.append(Spacer(1, 8))
        partes.append(Paragraph("Detalle por prueba", estilos["seccion"]))
        por_capacidad: dict[str, list[dict]] = {}
        for linea in resumen.detalle:
            prueba = repo.obtener("T_CAT_TESTS", linea.get("ID_Test"))
            if prueba:
                por_capacidad.setdefault(prueba["Capacidad"], []).append((linea, prueba))

        for capacidad in srv.CAPACIDADES:
            if capacidad not in por_capacidad:
                continue
            partes.append(Paragraph(
                ETIQUETA_CAPACIDAD.get(capacidad, capacidad).replace("\n", " "),
                estilos["texto"]))
            filas = [["Prueba", "Lado", "Valor", "Categoría", "Puntos"]]
            for linea, prueba in por_capacidad[capacidad]:
                valor = linea.get("Valor")
                if linea.get("Valor_Tecnica") is not None:
                    texto_valor = f"{int(linea['Valor_Tecnica'])}/3"
                elif valor is not None:
                    texto_valor = f"{valor:g} {prueba.get('Unidad') or ''}".strip()
                else:
                    texto_valor = "—"
                lado = linea.get("Lado")
                filas.append([
                    Paragraph(prueba.get("Nombre"), estilos["celda"]),
                    {"DERECHO": "Dcho", "IZQUIERDO": "Izdo"}.get(lado, ""),
                    texto_valor,
                    (linea.get("Categoria") or "sin baremo").replace("_", " ").lower(),
                    str(linea.get("Puntuacion") or "—")])
            tabla = _tabla(filas, [66 * mm, 14 * mm, 30 * mm, 44 * mm, 20 * mm])
            for n, (linea, _) in enumerate(por_capacidad[capacidad], start=1):
                tabla.setStyle(TableStyle([
                    ("TEXTCOLOR", (4, n), (4, n), _color_puntos(linea.get("Puntuacion"))),
                    ("FONTNAME", (4, n), (4, n), "Helvetica-Bold")]))
            partes += [tabla, Spacer(1, 7)]

        # -- lectura --
        if resumen.puntos_fuertes or resumen.a_mejorar:
            partes.append(Paragraph("Lectura de los resultados", estilos["seccion"]))
            if resumen.puntos_fuertes:
                partes.append(Paragraph(
                    "<b>Puntos fuertes:</b> " + ", ".join(resumen.puntos_fuertes),
                    estilos["texto"]))
            if resumen.a_mejorar:
                partes.append(Paragraph(
                    "<b>Áreas de mejora:</b> " + ", ".join(resumen.a_mejorar),
                    estilos["texto"]))
            partes.append(Spacer(1, 4))

        if resumen.valoracion.get("Observaciones"):
            partes.append(Paragraph("Conclusión del entrenador", estilos["seccion"]))
            partes.append(Paragraph(resumen.valoracion["Observaciones"], estilos["texto"]))

        partes.append(Spacer(1, 10))
        partes.append(Paragraph(
            "Los valores de referencia son orientativos y dependen del protocolo de "
            "medición. Este informe no sustituye a una valoración médica.",
            estilos["pie"]))

        def pie(lienzo, _documento):
            lienzo.saveState()
            lienzo.setFont("Helvetica", 7.5)
            lienzo.setFillColor(colors.HexColor("#9AA5AD"))
            lienzo.drawString(18 * mm, 10 * mm,
                              f"{cfg.negocio.nombre_comercial} · {cfg.negocio.lema}")
            lienzo.drawRightString(A4[0] - 18 * mm, 10 * mm,
                                   f"{nombre} · página {lienzo.getPageNumber()}")
            lienzo.restoreState()

        documento.build(partes, onFirstPage=pie, onLaterPages=pie)
    return destino


# --- Programa de entrenamiento ----------------------------------------------

def _cabecera_marca(cfg: Config, estilos: dict, derecha: str) -> Table:
    logo = estilo.ruta_logo()
    izquierda = (Image(str(logo), width=34 * mm, height=16 * mm, kind="proportional")
                 if logo and logo.exists()
                 else Paragraph(f"<b>{cfg.negocio.nombre_comercial}</b>", estilos["titulo"]))
    tabla = Table([[izquierda, Paragraph(derecha, estilos["subtitulo"])]],
                  colWidths=[100 * mm, 74 * mm])
    tabla.setStyle(TableStyle([("ALIGN", (1, 0), (1, 0), "RIGHT"),
                               ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    return tabla


def generar_programa(repo: Repositorio, cfg: Config, id_asignacion: str,
                     desde: int = 1, hasta: int | None = None,
                     destino: Path | None = None) -> Path:
    """Hoja de entrenamiento del usuario, con las cargas ya resueltas en kilos."""
    from . import programas as srv_prog

    asignacion = repo.obtener("T_ASIGNACIONES", id_asignacion)
    if not asignacion:
        raise KeyError(id_asignacion)
    usuario = repo.obtener("T_USUARIOS", asignacion["ID_Usuario"]) or {}
    macro = repo.obtener("T_CICLOS", asignacion["ID_Ciclo"]) or {}
    nombre = " ".join(x for x in (usuario.get("Nombre"), usuario.get("Apellidos")) if x)
    estilos = _estilos()

    semanas = srv_prog.semanas_de(repo, id_asignacion)
    hasta = hasta or len(semanas)
    elegidas = [s for s in semanas if desde <= s.numero <= hasta]

    if destino is None:
        carpeta = Path(cfg.datos.libro).parent / "salidas" / "programas"
        destino = carpeta / (f"programa_{usuario.get('ID_Usuario')}_"
                             f"s{desde:02d}-s{hasta:02d}.pdf")
    destino.parent.mkdir(parents=True, exist_ok=True)

    documento = SimpleDocTemplate(
        str(destino), pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=14 * mm, bottomMargin=16 * mm,
        title=f"Programa de entrenamiento — {nombre}",
        author=cfg.negocio.nombre_comercial)
    partes = [
        _cabecera_marca(cfg, estilos,
                        f"{cfg.negocio.lema}<br/>{formatear(asignacion.get('F_Inicio'))} "
                        f"– {formatear(asignacion.get('F_Fin_Prevista'))}"),
        Spacer(1, 4),
        Paragraph("Programa de entrenamiento", estilos["titulo"]),
        Paragraph(f"{nombre} · {macro.get('Nombre', '')}"
                  + (f" · {macro.get('Objetivo_Ciclo')}" if macro.get("Objetivo_Ciclo") else ""),
                  estilos["subtitulo"]),
    ]

    # -- calendario del plan --
    partes.append(Paragraph("Plan completo", estilos["seccion"]))
    filas = [["Fase", "Nivel", "Desde", "Hasta", "Semanas"]]
    for fase in srv_prog.fases_de(repo, id_asignacion):
        ciclo = repo.obtener("T_CICLOS", fase.get("ID_Ciclo")) or {}
        if fase.get("Nivel") == "MACRO":
            continue
        sangria = "" if fase.get("Nivel") == "MESO" else "     "
        inicio, fin = fase.get("F_Inicio"), fase.get("F_Fin")
        filas.append([
            Paragraph(f"{sangria}{ciclo.get('Nombre', '')}", estilos["celda"]),
            (fase.get("Nivel") or "").capitalize(),
            formatear(inicio), formatear(fin),
            str(((fin - inicio).days + 1) // 7) if inicio and fin else ""])
    partes.append(_tabla(filas, [78 * mm, 20 * mm, 25 * mm, 25 * mm, 22 * mm]))

    # -- semanas --
    sin_1rm: set[str] = set()
    for semana in elegidas:
        partes.append(Paragraph(
            f"Semana {semana.numero} · {semana.nombre_micro}"
            + (f" · desde el {formatear(semana.inicio)}" if semana.inicio else ""),
            estilos["seccion"]))
        if not semana.sesiones:
            partes.append(Paragraph("Sin sesiones definidas en este microciclo.",
                                    estilos["texto"]))
            continue
        for sesion in semana.sesiones:
            partes.append(Paragraph(
                f"<b>Día {sesion.get('Num_Dia')} · {sesion.get('Nombre') or ''}</b>"
                + (f"  ({sesion.get('Tipo', '').lower()})" if sesion.get("Tipo") else ""),
                estilos["texto"]))
            filas = [["Bloque", "Ejercicio", "Series", "Reps", "Carga", "Desc.", "Notas"]]
            for linea in srv_prog.lineas(repo, sesion["ID_Sesion"]):
                ejercicio = repo.obtener("T_EJERCICIOS", linea.get("ID_Ejercicio")) or {}
                carga = srv_prog.resolver_carga(
                    repo, linea, asignacion.get("ID_Usuario"), semana.en_micro)
                if carga.sin_1rm:
                    sin_1rm.add(ejercicio.get("Nombre") or linea.get("ID_Ejercicio"))
                nota = " · ".join(x for x in (
                    linea.get("Notas") or "", srv_prog.nota_progresion(linea.get("Progresion")),
                    f"tempo {linea['Tempo']}" if linea.get("Tempo") else "") if x)
                descanso = linea.get("Descanso_Seg")
                filas.append([
                    (linea.get("Bloque") or "").replace("_", " ").capitalize(),
                    Paragraph(ejercicio.get("Nombre") or "", estilos["celda"]),
                    str(linea.get("Series") or ""), str(linea.get("Reps") or ""),
                    Paragraph(f"<b>{carga.texto}</b>", estilos["celda"]),
                    f"{int(descanso)}s" if descanso else "",
                    Paragraph(nota, estilos["celda"])])
            partes.append(_tabla(
                filas, [22 * mm, 45 * mm, 13 * mm, 16 * mm, 34 * mm, 13 * mm, 37 * mm]))
            partes.append(Spacer(1, 5))

    if sin_1rm:
        partes.append(Spacer(1, 4))
        partes.append(Paragraph(
            "<b>Pendiente de medir:</b> " + ", ".join(sorted(sin_1rm)) +
            ". Sin la repetición máxima no se puede calcular el peso, así que esas "
            "casillas salen «por determinar».", estilos["texto"]))

    partes.append(Spacer(1, 8))
    partes.append(Paragraph(
        "Anota debajo de cada sesión lo que hayas hecho de verdad: repeticiones, "
        "kilos y sensaciones. Esa información es la que permite ajustar el plan.",
        estilos["pie"]))

    def pie(lienzo, _documento):
        lienzo.saveState()
        lienzo.setFont("Helvetica", 7.5)
        lienzo.setFillColor(colors.HexColor("#9AA5AD"))
        lienzo.drawString(15 * mm, 10 * mm,
                          f"{cfg.negocio.nombre_comercial} · {cfg.negocio.lema}")
        lienzo.drawRightString(A4[0] - 15 * mm, 10 * mm,
                               f"{nombre} · página {lienzo.getPageNumber()}")
        lienzo.restoreState()

    documento.build(partes, onFirstPage=pie, onLaterPages=pie)
    return destino
