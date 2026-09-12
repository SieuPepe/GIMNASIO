"""Plantillas de correo de partida.

Los marcadores se sustituyen al montar el borrador. `Instruccion_IA` es lo que
se le dirá al modelo en la fase 7 para que personalice el texto; hasta entonces
se usa el cuerpo tal cual.
"""

from __future__ import annotations

from ..datos.repositorio import Repositorio

NOTA = ('{{#nota}}<div class="nota">{{nota_entrenador}}</div>{{/nota}}')

PLANTILLAS = [
    {
        "Codigo": "CONSENTIMIENTO",
        "Asunto": "{{nombre}}, necesitamos tu autorización para tus datos",
        "Requiere_Revision_SN": False,
        "Permite_Modo_Vacaciones_SN": True,
        "Instruccion_IA": ("Correo breve y cordial pidiendo la autorización de datos. "
                           "Sin jerga legal y sin alarmar. Máximo 100 palabras."),
        "Cuerpo_HTML": """
<p>Hola {{nombre}}:</p>
<p>Para preparar tu entrenamiento guardamos algunos datos tuyos: los de contacto y
los de tus mediciones físicas y de salud. Necesitamos que nos autorices a ello.</p>
<p>Es un momento: pulsa el botón y marca la casilla.</p>
<p><a class="boton" href="{{enlace_form}}">Dar mi autorización</a></p>
<p>Puedes retirarla cuando quieras escribiéndonos. Mientras no la tengamos, no te
enviaremos ningún otro correo.</p>
<p>Un saludo,<br/>{{entrenador}}</p>""",
    },
    {
        "Codigo": "BIENVENIDA",
        "Asunto": "{{nombre}}, ya tienes tu plan: {{programa}}",
        "Requiere_Revision_SN": True,
        "Permite_Modo_Vacaciones_SN": True,
        "Instruccion_IA": ("Correo de bienvenida al nuevo ciclo. Tono cercano y "
                           "motivador, sin prometer resultados. 120-150 palabras."),
        "Cuerpo_HTML": """
<p>Hola {{nombre}}:</p>
<p>Ya tienes preparado tu nuevo plan: <b>{{programa}}</b>, de {{semanas}} semanas,
del {{fecha_inicio}} al {{fecha_fin}}.</p>
<p>Lo hemos montado alrededor de lo que nos dijiste que querías conseguir:
«{{objetivo}}».</p>
""" + NOTA + """
<p>Te adjunto la hoja con las primeras semanas. Cualquier duda con un ejercicio,
pregúntame en la sala.</p>
<p>Nos vemos,<br/>{{entrenador}}</p>""",
    },
    {
        "Codigo": "CHECKIN_MITAD",
        "Asunto": "{{nombre}}, ¿cómo va el plan?",
        "Requiere_Revision_SN": True,
        "Permite_Modo_Vacaciones_SN": True,
        "Instruccion_IA": ("Una sola pregunta, muy breve. Máximo 60 palabras."),
        "Cuerpo_HTML": """
<p>Hola {{nombre}}:</p>
<p>Vas por la mitad de <b>{{programa}}</b>. Una sola pregunta, que tardas quince
segundos: <b>¿cómo te encuentras, del 1 al 10?</b></p>
<p><a class="boton" href="{{enlace_form}}">Responder</a></p>
""" + NOTA + """
<p>{{entrenador}}</p>""",
    },
    {
        "Codigo": "ENCUESTA_T14",
        "Asunto": "{{nombre}}, quedan dos semanas: cuéntame qué tal ha ido",
        "Requiere_Revision_SN": True,
        "Permite_Modo_Vacaciones_SN": False,
        "Instruccion_IA": (
            "Correo de cierre de ciclo y renovación. Empieza por lo que ha hecho el "
            "usuario, no por la petición. Integra con naturalidad la nota del "
            "entrenador. No inventes datos que no se dan. 150-200 palabras."),
        "Cuerpo_HTML": """
<p>Hola {{nombre}}:</p>
<p>En dos semanas terminas <b>{{programa}}</b>. Han sido {{semanas}} semanas desde
el {{fecha_inicio}}, y ya has completado {{fase_actual}}.</p>
""" + NOTA + """
<p>Antes de preparar el siguiente ciclo me viene muy bien saber cómo lo has vivido:
qué te ha funcionado, qué no, y si sigues buscando lo mismo que al empezar
(«{{objetivo}}»).</p>
<p>Son <b>dos minutos</b>, y lo que respondas se nota directamente en lo que viene
después.</p>
<p><a class="boton" href="{{enlace_form}}">Responder el cuestionario</a></p>
<p>Gracias,<br/>{{entrenador}}</p>""",
    },
    {
        "Codigo": "RECORDATORIO",
        "Asunto": "{{nombre}}, te quedan dos minutos de cuestionario",
        "Requiere_Revision_SN": True,
        "Permite_Modo_Vacaciones_SN": True,
        "Instruccion_IA": "Recordatorio muy breve y sin reproche. Máximo 70 palabras.",
        "Cuerpo_HTML": """
<p>Hola {{nombre}}:</p>
<p>Te escribí hace unos días sobre el final de <b>{{programa}}</b>. Si no te ha dado
tiempo, aquí tienes otra vez el enlace: son dos minutos y me ayuda mucho para
preparar tu siguiente ciclo.</p>
<p><a class="boton" href="{{enlace_form}}">Responder ahora</a></p>
<p>{{entrenador}}</p>""",
    },
    {
        "Codigo": "CIERRE_CICLO",
        "Asunto": "{{nombre}}, has terminado {{programa}}",
        "Requiere_Revision_SN": True,
        "Permite_Modo_Vacaciones_SN": False,
        "Instruccion_IA": ("Cierre del ciclo y propuesta del siguiente. Reconoce el "
                           "trabajo hecho. 120-160 palabras."),
        "Cuerpo_HTML": """
<p>Hola {{nombre}}:</p>
<p>Has terminado <b>{{programa}}</b>: {{semanas}} semanas, del {{fecha_inicio}} al
{{fecha_fin}}.</p>
""" + NOTA + """
<p>Con lo que me has contado ya estoy preparando el siguiente ciclo. Si quieres que
lo veamos juntos, pásate por la sala cuando esté yo: {{horario_sala}}.</p>
<p>Enhorabuena por el trabajo,<br/>{{entrenador}}</p>""",
    },
    {
        "Codigo": "AGRADECIMIENTO",
        "Asunto": "Recibido, {{nombre}}. Gracias",
        "Requiere_Revision_SN": False,
        "Permite_Modo_Vacaciones_SN": True,
        "Instruccion_IA": "Agradecimiento muy breve. Máximo 60 palabras.",
        "Cuerpo_HTML": """
<p>Hola {{nombre}}:</p>
<p>He recibido tus respuestas, gracias por dedicarles el rato. Ya estoy preparando
tu siguiente ciclo con ellas.</p>
{{#cita}}<p>Me dices que quieres que hablemos: pásate por la sala cuando esté yo,
{{horario_sala}}.</p>{{/cita}}
""" + NOTA + """
<p>{{entrenador}}</p>""",
    },
]


def crear(repo: Repositorio) -> list[str]:
    """Crea las plantillas que falten, sin tocar las que ya existan."""
    existentes = {p.get("Codigo") for p in repo.listar("T_PLANTILLAS_MAIL")}
    creadas = []
    for plantilla in PLANTILLAS:
        if plantilla["Codigo"] in existentes:
            continue
        datos = dict(plantilla)
        datos["Cuerpo_HTML"] = datos["Cuerpo_HTML"].strip()
        datos["Activo_SN"] = True
        datos["URL_Form"] = ""
        repo.insertar("T_PLANTILLAS_MAIL", datos)
        creadas.append(plantilla["Codigo"])
    return creadas
