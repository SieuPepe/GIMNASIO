"""Plantillas de macrociclo de partida.

No hay planificaciones propias de las que partir, así que se entregan cuatro
estructuras tipo. Se crean como plantillas editables: la idea es clonarlas y
adaptarlas, no usarlas tal cual.

Las líneas se escriben con el NOMBRE del ejercicio y se resuelven contra el
catálogo, de modo que si un ejercicio no existe la plantilla lo dice en vez de
crear una referencia rota.
"""

from __future__ import annotations

from ..datos.repositorio import Repositorio
from ..servicios import ejercicios as srv_ejercicios

# (bloque, ejercicio, series, reps, modo, valor, descanso, progresion)
L = tuple

CALENT = [
    ("CALENTAMIENTO", "Bicicleta estática", 1, "5-8 min", "TIEMPO", 480, 0, ""),
    ("CALENTAMIENTO", "Gato-camello", 2, "8", "PESO_CORPORAL", None, 30, ""),
    ("CALENTAMIENTO", "Bird dog", 2, "8", "PESO_CORPORAL", None, 30, ""),
]
VUELTA = [("VUELTA_CALMA", "Estiramiento de isquiosurales tumbado", 2, "30 s",
           "TIEMPO", 30, 20, "")]

PLANTILLAS = [
    {
        "nombre": "Principiante · adaptación 12 semanas",
        "objetivo": "Aprender los patrones básicos y crear el hábito",
        "notas": "Tres días por semana. Cargas conservadoras y foco en técnica.",
        "mesos": [
            {"nombre": "Adaptación anatómica", "enfoque": "ADAPTACION", "semanas": 4,
             "micros": [
                {"nombre": "Aprendizaje de patrones", "semanas": 4, "sesiones": [
                    {"dia": 1, "nombre": "Cuerpo completo A", "tipo": "FUERZA", "lineas": CALENT + [
                        ("PRINCIPAL", "Sentadilla goblet", 3, "10", "RIR", 3, 90, "DOBLE_PROGRESION"),
                        ("PRINCIPAL", "Press de banca con mancuernas", 3, "10", "RIR", 3, 90, "DOBLE_PROGRESION"),
                        ("PRINCIPAL", "Remo con mancuerna a una mano", 3, "10", "RIR", 3, 90, "DOBLE_PROGRESION"),
                        ("CORE", "Plancha frontal", 3, "20-30 s", "TIEMPO", 25, 45, ""),
                    ] + VUELTA},
                    {"dia": 2, "nombre": "Cuerpo completo B", "tipo": "FUERZA", "lineas": CALENT + [
                        ("PRINCIPAL", "Peso muerto rumano", 3, "10", "RIR", 3, 90, "DOBLE_PROGRESION"),
                        ("PRINCIPAL", "Press de hombro con mancuernas", 3, "10", "RIR", 3, 90, "DOBLE_PROGRESION"),
                        ("PRINCIPAL", "Jalón al pecho en polea", 3, "10", "RIR", 3, 90, "DOBLE_PROGRESION"),
                        ("ACCESORIO", "Puente de glúteo", 3, "12", "PESO_CORPORAL", None, 60, ""),
                        ("CORE", "Dead bug", 3, "8", "PESO_CORPORAL", None, 45, ""),
                    ] + VUELTA},
                    {"dia": 3, "nombre": "Cuerpo completo C", "tipo": "MIXTA", "lineas": CALENT + [
                        ("PRINCIPAL", "Prensa de piernas 45 grados", 3, "12", "RIR", 3, 90, "DOBLE_PROGRESION"),
                        ("PRINCIPAL", "Remo en polea baja", 3, "12", "RIR", 3, 90, "DOBLE_PROGRESION"),
                        ("ACCESORIO", "Zancada estática", 2, "10", "PESO_CORPORAL", None, 60, ""),
                        ("PRINCIPAL", "Caminata rápida", 1, "15 min", "TIEMPO", 900, 0, ""),
                    ] + VUELTA},
                ]}]},
            {"nombre": "Primera acumulación", "enfoque": "ACUMULACION", "semanas": 5,
             "micros": [
                {"nombre": "Volumen progresivo", "semanas": 4, "sesiones": [
                    {"dia": 1, "nombre": "Tren inferior", "tipo": "FUERZA", "lineas": CALENT + [
                        ("PRINCIPAL", "Sentadilla goblet", 4, "8", "RIR", 2, 120, "LINEAL:+2"),
                        ("PRINCIPAL", "Peso muerto rumano", 3, "10", "RIR", 2, 120, "LINEAL:+2.5"),
                        ("ACCESORIO", "Subida al cajón", 3, "10", "RIR", 2, 75, ""),
                        ("CORE", "Plancha lateral", 3, "20 s", "TIEMPO", 20, 45, ""),
                    ] + VUELTA},
                    {"dia": 2, "nombre": "Tren superior", "tipo": "FUERZA", "lineas": CALENT + [
                        ("PRINCIPAL", "Press de banca con mancuernas", 4, "8", "RIR", 2, 120, "LINEAL:+2"),
                        ("PRINCIPAL", "Remo con mancuerna a una mano", 4, "8", "RIR", 2, 120, "LINEAL:+2"),
                        ("ACCESORIO", "Press de hombro con mancuernas", 3, "10", "RIR", 2, 75, ""),
                        ("ACCESORIO", "Curl de bíceps con mancuernas", 2, "12", "RIR", 2, 60, ""),
                    ] + VUELTA},
                    {"dia": 3, "nombre": "Mixta", "tipo": "MIXTA", "lineas": CALENT + [
                        ("PRINCIPAL", "Prensa de piernas 45 grados", 3, "12", "RIR", 2, 90, "LINEAL:+5"),
                        ("PRINCIPAL", "Jalón al pecho en polea", 3, "12", "RIR", 2, 90, "LINEAL:+2.5"),
                        ("PRINCIPAL", "Bicicleta estática", 1, "20 min", "TIEMPO", 1200, 0, ""),
                    ] + VUELTA},
                ]},
                {"nombre": "Descarga", "semanas": 1, "sesiones": [
                    {"dia": 1, "nombre": "Descarga cuerpo completo", "tipo": "MIXTA", "lineas": CALENT + [
                        ("PRINCIPAL", "Sentadilla goblet", 2, "8", "RIR", 4, 90, "DESCARGA:60"),
                        ("PRINCIPAL", "Press de banca con mancuernas", 2, "8", "RIR", 4, 90, "DESCARGA:60"),
                        ("PRINCIPAL", "Remo en polea baja", 2, "8", "RIR", 4, 90, "DESCARGA:60"),
                    ] + VUELTA},
                ]}]},
            {"nombre": "Consolidación", "enfoque": "INTENSIFICACION", "semanas": 3,
             "micros": [
                {"nombre": "Carga moderada", "semanas": 3, "sesiones": [
                    {"dia": 1, "nombre": "Tren inferior", "tipo": "FUERZA", "lineas": CALENT + [
                        ("PRINCIPAL", "Sentadilla trasera con barra", 4, "6", "PCT1RM", 75, 150, "PCT:72,75,78"),
                        ("PRINCIPAL", "Peso muerto rumano", 3, "8", "PCT1RM", 70, 120, "PCT:68,70,73"),
                        ("ACCESORIO", "Zancada caminando", 3, "10", "RIR", 2, 90, ""),
                    ] + VUELTA},
                    {"dia": 2, "nombre": "Tren superior", "tipo": "FUERZA", "lineas": CALENT + [
                        ("PRINCIPAL", "Press de banca con barra", 4, "6", "PCT1RM", 75, 150, "PCT:72,75,78"),
                        ("PRINCIPAL", "Remo con barra", 4, "8", "PCT1RM", 70, 120, "PCT:68,70,73"),
                        ("ACCESORIO", "Elevaciones laterales", 3, "12", "RIR", 2, 60, ""),
                    ] + VUELTA},
                    {"dia": 3, "nombre": "Mixta", "tipo": "MIXTA", "lineas": CALENT + [
                        ("PRINCIPAL", "Prensa de piernas 45 grados", 3, "10", "RIR", 2, 90, ""),
                        ("PRINCIPAL", "Dominada asistida con goma", 3, "6", "PESO_CORPORAL", None, 120, ""),
                        ("PRINCIPAL", "Caminata rápida", 1, "25 min", "TIEMPO", 1500, 0, ""),
                    ] + VUELTA},
                ]}]},
        ],
    },
    {
        "nombre": "Hipertrofia 16 semanas",
        "objetivo": "Ganar masa muscular con volumen progresivo",
        "notas": "Cuatro días por semana, torso-pierna. Requiere base previa.",
        "mesos": [
            {"nombre": "Acumulación I", "enfoque": "ACUMULACION", "semanas": 5,
             "micros": [
                {"nombre": "Volumen medio", "semanas": 4, "sesiones": [
                    {"dia": 1, "nombre": "Torso empuje", "tipo": "FUERZA", "lineas": CALENT + [
                        ("PRINCIPAL", "Press de banca con barra", 4, "8-10", "RIR", 2, 120, "DOBLE_PROGRESION"),
                        ("PRINCIPAL", "Press de hombro con mancuernas", 4, "10", "RIR", 2, 90, "DOBLE_PROGRESION"),
                        ("ACCESORIO", "Press inclinado con mancuernas", 3, "12", "RIR", 2, 75, ""),
                        ("ACCESORIO", "Elevaciones laterales", 4, "15", "RIR", 1, 45, ""),
                        ("ACCESORIO", "Extensión de tríceps en polea", 3, "12", "RIR", 2, 60, ""),
                    ] + VUELTA},
                    {"dia": 2, "nombre": "Pierna", "tipo": "FUERZA", "lineas": CALENT + [
                        ("PRINCIPAL", "Sentadilla trasera con barra", 4, "8", "RIR", 2, 150, "DOBLE_PROGRESION"),
                        ("PRINCIPAL", "Peso muerto rumano", 4, "10", "RIR", 2, 120, "DOBLE_PROGRESION"),
                        ("ACCESORIO", "Prensa de piernas 45 grados", 3, "12", "RIR", 2, 90, ""),
                        ("ACCESORIO", "Curl femoral tumbado", 3, "12", "RIR", 2, 60, ""),
                        ("ACCESORIO", "Elevación de gemelos de pie", 4, "15", "RIR", 1, 45, ""),
                    ] + VUELTA},
                    {"dia": 3, "nombre": "Torso tracción", "tipo": "FUERZA", "lineas": CALENT + [
                        ("PRINCIPAL", "Dominada con agarre prono", 4, "6-8", "PESO_CORPORAL", None, 150, "DOBLE_PROGRESION"),
                        ("PRINCIPAL", "Remo con barra", 4, "8-10", "RIR", 2, 120, "DOBLE_PROGRESION"),
                        ("ACCESORIO", "Remo en polea baja", 3, "12", "RIR", 2, 75, ""),
                        ("ACCESORIO", "Face pull", 3, "15", "RIR", 2, 45, ""),
                        ("ACCESORIO", "Curl de bíceps con barra", 3, "12", "RIR", 2, 60, ""),
                    ] + VUELTA},
                    {"dia": 4, "nombre": "Pierna y core", "tipo": "FUERZA", "lineas": CALENT + [
                        ("PRINCIPAL", "Hip thrust con barra", 4, "10", "RIR", 2, 120, "DOBLE_PROGRESION"),
                        ("PRINCIPAL", "Sentadilla búlgara", 3, "10", "RIR", 2, 90, ""),
                        ("ACCESORIO", "Extensión de cuádriceps en máquina", 3, "15", "RIR", 1, 60, ""),
                        ("CORE", "Plancha lateral", 3, "30 s", "TIEMPO", 30, 45, ""),
                        ("CORE", "Crunch en polea alta", 3, "15", "RIR", 2, 45, ""),
                    ] + VUELTA},
                ]},
                {"nombre": "Descarga", "semanas": 1, "sesiones": [
                    {"dia": 1, "nombre": "Descarga torso", "tipo": "FUERZA", "lineas": CALENT + [
                        ("PRINCIPAL", "Press de banca con barra", 3, "8", "PCT1RM", 60, 120, "DESCARGA:60"),
                        ("PRINCIPAL", "Remo con barra", 3, "8", "PCT1RM", 60, 120, "DESCARGA:60"),
                    ] + VUELTA},
                    {"dia": 2, "nombre": "Descarga pierna", "tipo": "FUERZA", "lineas": CALENT + [
                        ("PRINCIPAL", "Sentadilla trasera con barra", 3, "8", "PCT1RM", 60, 120, "DESCARGA:60"),
                        ("PRINCIPAL", "Peso muerto rumano", 3, "8", "PCT1RM", 60, 120, "DESCARGA:60"),
                    ] + VUELTA},
                ]}]},
            {"nombre": "Acumulación II", "enfoque": "ACUMULACION", "semanas": 5,
             "micros": [
                {"nombre": "Volumen alto", "semanas": 4, "sesiones": [
                    {"dia": 1, "nombre": "Torso empuje", "tipo": "FUERZA", "lineas": CALENT + [
                        ("PRINCIPAL", "Press de banca inclinado con barra", 5, "8", "RIR", 1, 120, "LINEAL:+2.5"),
                        ("PRINCIPAL", "Press militar sentado con barra", 4, "8", "RIR", 1, 120, "LINEAL:+2.5"),
                        ("ACCESORIO", "Cruce de poleas", 3, "15", "RIR", 1, 60, ""),
                        ("ACCESORIO", "Fondos en paralelas", 3, "10", "PESO_CORPORAL", None, 90, ""),
                    ] + VUELTA},
                    {"dia": 2, "nombre": "Pierna", "tipo": "FUERZA", "lineas": CALENT + [
                        ("PRINCIPAL", "Sentadilla frontal con barra", 4, "8", "RIR", 1, 150, "LINEAL:+2.5"),
                        ("PRINCIPAL", "Peso muerto convencional", 3, "6", "PCT1RM", 75, 180, "PCT:72,75,78,80"),
                        ("ACCESORIO", "Zancada caminando", 3, "12", "RIR", 2, 90, ""),
                        ("ACCESORIO", "Curl femoral sentado", 4, "12", "RIR", 1, 60, ""),
                    ] + VUELTA},
                    {"dia": 3, "nombre": "Torso tracción", "tipo": "FUERZA", "lineas": CALENT + [
                        ("PRINCIPAL", "Dominada con agarre prono", 5, "6", "PESO_CORPORAL", None, 150, ""),
                        ("PRINCIPAL", "Remo Pendlay", 4, "8", "RIR", 1, 120, "LINEAL:+2.5"),
                        ("ACCESORIO", "Jalón con agarre neutro", 3, "12", "RIR", 1, 75, ""),
                        ("ACCESORIO", "Curl martillo", 3, "12", "RIR", 1, 60, ""),
                    ] + VUELTA},
                    {"dia": 4, "nombre": "Pierna y core", "tipo": "FUERZA", "lineas": CALENT + [
                        ("PRINCIPAL", "Hip thrust con barra", 4, "8", "RIR", 1, 120, "LINEAL:+5"),
                        ("ACCESORIO", "Prensa de piernas 45 grados", 4, "15", "RIR", 1, 90, ""),
                        ("CORE", "Rueda abdominal", 3, "10", "PESO_CORPORAL", None, 60, ""),
                        ("CORE", "Plancha frontal", 3, "45 s", "TIEMPO", 45, 45, ""),
                    ] + VUELTA},
                ]},
                {"nombre": "Descarga", "semanas": 1, "sesiones": [
                    {"dia": 1, "nombre": "Descarga general", "tipo": "MIXTA", "lineas": CALENT + [
                        ("PRINCIPAL", "Press de banca con barra", 3, "8", "PCT1RM", 60, 120, "DESCARGA:60"),
                        ("PRINCIPAL", "Sentadilla trasera con barra", 3, "8", "PCT1RM", 60, 120, "DESCARGA:60"),
                    ] + VUELTA},
                ]}]},
            {"nombre": "Intensificación", "enfoque": "INTENSIFICACION", "semanas": 6,
             "micros": [
                {"nombre": "Carga alta, volumen medio", "semanas": 5, "sesiones": [
                    {"dia": 1, "nombre": "Torso pesado", "tipo": "FUERZA", "lineas": CALENT + [
                        ("PRINCIPAL", "Press de banca con barra", 5, "5", "PCT1RM", 82, 180, "PCT:80,82,85,87,80"),
                        ("PRINCIPAL", "Remo con barra", 4, "6", "PCT1RM", 78, 150, "PCT:76,78,80,82,76"),
                        ("ACCESORIO", "Press de hombro con mancuernas", 3, "10", "RIR", 2, 90, ""),
                    ] + VUELTA},
                    {"dia": 2, "nombre": "Pierna pesada", "tipo": "FUERZA", "lineas": CALENT + [
                        ("PRINCIPAL", "Sentadilla trasera con barra", 5, "5", "PCT1RM", 82, 180, "PCT:80,82,85,87,80"),
                        ("PRINCIPAL", "Peso muerto convencional", 3, "4", "PCT1RM", 85, 210, "PCT:82,85,87,90,82"),
                        ("ACCESORIO", "Curl femoral tumbado", 3, "12", "RIR", 2, 60, ""),
                    ] + VUELTA},
                    {"dia": 3, "nombre": "Complementaria", "tipo": "MIXTA", "lineas": CALENT + [
                        ("PRINCIPAL", "Dominada con agarre prono", 4, "5", "PESO_CORPORAL", None, 150, ""),
                        ("ACCESORIO", "Sentadilla búlgara", 3, "10", "RIR", 2, 90, ""),
                        ("CORE", "Pallof press", 3, "10", "RIR", 2, 45, ""),
                    ] + VUELTA},
                ]},
                {"nombre": "Descarga final", "semanas": 1, "sesiones": [
                    {"dia": 1, "nombre": "Descarga", "tipo": "MIXTA", "lineas": CALENT + [
                        ("PRINCIPAL", "Sentadilla goblet", 2, "8", "RIR", 4, 90, ""),
                        ("PRINCIPAL", "Remo en polea baja", 2, "10", "RIR", 4, 90, ""),
                    ] + VUELTA},
                ]}]},
        ],
    },
    {
        "nombre": "Fuerza 16 semanas",
        "objetivo": "Subir la fuerza máxima en los básicos",
        "notas": "Tres días. Progresión por porcentajes del 1RM: exige tenerlos medidos.",
        "mesos": [
            {"nombre": "Base de fuerza", "enfoque": "ACUMULACION", "semanas": 6,
             "micros": [
                {"nombre": "Técnica y volumen", "semanas": 5, "sesiones": [
                    {"dia": 1, "nombre": "Sentadilla", "tipo": "FUERZA", "lineas": CALENT + [
                        ("PRINCIPAL", "Sentadilla trasera con barra", 5, "5", "PCT1RM", 72, 180, "PCT:70,72,75,77,80"),
                        ("ACCESORIO", "Peso muerto rumano", 3, "8", "PCT1RM", 65, 120, ""),
                        ("CORE", "Plancha frontal", 3, "45 s", "TIEMPO", 45, 45, ""),
                    ] + VUELTA},
                    {"dia": 2, "nombre": "Press", "tipo": "FUERZA", "lineas": CALENT + [
                        ("PRINCIPAL", "Press de banca con barra", 5, "5", "PCT1RM", 72, 180, "PCT:70,72,75,77,80"),
                        ("ACCESORIO", "Press militar sentado con barra", 3, "8", "PCT1RM", 65, 120, ""),
                        ("ACCESORIO", "Remo con barra", 4, "8", "RIR", 2, 120, ""),
                    ] + VUELTA},
                    {"dia": 3, "nombre": "Peso muerto", "tipo": "FUERZA", "lineas": CALENT + [
                        ("PRINCIPAL", "Peso muerto convencional", 5, "5", "PCT1RM", 72, 210, "PCT:70,72,75,77,80"),
                        ("ACCESORIO", "Dominada con agarre prono", 4, "6", "PESO_CORPORAL", None, 120, ""),
                        ("CORE", "Extensión lumbar en banco", 3, "12", "PESO_CORPORAL", None, 60, ""),
                    ] + VUELTA},
                ]},
                {"nombre": "Descarga", "semanas": 1, "sesiones": [
                    {"dia": 1, "nombre": "Descarga", "tipo": "FUERZA", "lineas": CALENT + [
                        ("PRINCIPAL", "Sentadilla trasera con barra", 3, "5", "PCT1RM", 60, 150, "DESCARGA:60"),
                        ("PRINCIPAL", "Press de banca con barra", 3, "5", "PCT1RM", 60, 150, "DESCARGA:60"),
                    ] + VUELTA},
                ]}]},
            {"nombre": "Intensificación", "enfoque": "INTENSIFICACION", "semanas": 6,
             "micros": [
                {"nombre": "Series pesadas", "semanas": 5, "sesiones": [
                    {"dia": 1, "nombre": "Sentadilla pesada", "tipo": "FUERZA", "lineas": CALENT + [
                        ("PRINCIPAL", "Sentadilla trasera con barra", 5, "3", "PCT1RM", 85, 210, "PCT:82,85,87,90,80"),
                        ("ACCESORIO", "Sentadilla frontal con barra", 3, "5", "PCT1RM", 70, 150, ""),
                    ] + VUELTA},
                    {"dia": 2, "nombre": "Press pesado", "tipo": "FUERZA", "lineas": CALENT + [
                        ("PRINCIPAL", "Press de banca con barra", 5, "3", "PCT1RM", 85, 210, "PCT:82,85,87,90,80"),
                        ("ACCESORIO", "Press militar con barra de pie", 4, "5", "PCT1RM", 70, 150, ""),
                        ("ACCESORIO", "Remo Pendlay", 4, "6", "RIR", 2, 120, ""),
                    ] + VUELTA},
                    {"dia": 3, "nombre": "Peso muerto pesado", "tipo": "FUERZA", "lineas": CALENT + [
                        ("PRINCIPAL", "Peso muerto convencional", 4, "3", "PCT1RM", 87, 240, "PCT:85,87,90,92,82"),
                        ("ACCESORIO", "Dominada con agarre prono", 4, "5", "PESO_CORPORAL", None, 150, ""),
                    ] + VUELTA},
                ]},
                {"nombre": "Descarga", "semanas": 1, "sesiones": [
                    {"dia": 1, "nombre": "Descarga", "tipo": "FUERZA", "lineas": CALENT + [
                        ("PRINCIPAL", "Sentadilla trasera con barra", 3, "3", "PCT1RM", 65, 150, "DESCARGA:60"),
                    ] + VUELTA},
                ]}]},
            {"nombre": "Realización", "enfoque": "REALIZACION", "semanas": 4,
             "micros": [
                {"nombre": "Puesta a punto", "semanas": 3, "sesiones": [
                    {"dia": 1, "nombre": "Singles y dobles", "tipo": "FUERZA", "lineas": CALENT + [
                        ("PRINCIPAL", "Sentadilla trasera con barra", 4, "2", "PCT1RM", 90, 240, "PCT:88,90,93"),
                        ("PRINCIPAL", "Press de banca con barra", 4, "2", "PCT1RM", 90, 240, "PCT:88,90,93"),
                    ] + VUELTA},
                    {"dia": 2, "nombre": "Peso muerto", "tipo": "FUERZA", "lineas": CALENT + [
                        ("PRINCIPAL", "Peso muerto convencional", 3, "2", "PCT1RM", 90, 240, "PCT:88,90,93"),
                        ("ACCESORIO", "Remo con barra", 3, "6", "RIR", 3, 120, ""),
                    ] + VUELTA},
                ]},
                {"nombre": "Test de 1RM", "semanas": 1, "sesiones": [
                    {"dia": 1, "nombre": "Test", "tipo": "FUERZA", "lineas": CALENT + [
                        ("PRINCIPAL", "Sentadilla trasera con barra", 1, "1", "PCT1RM", 100, 300, ""),
                        ("PRINCIPAL", "Press de banca con barra", 1, "1", "PCT1RM", 100, 300, ""),
                        ("PRINCIPAL", "Peso muerto convencional", 1, "1", "PCT1RM", 100, 300, ""),
                    ]},
                ]}]},
        ],
    },
    {
        "nombre": "Salud general 12 semanas",
        "objetivo": "Mejorar condición física general y hábitos",
        "notas": "Dos o tres días. Pensado para población adulta poco entrenada.",
        "mesos": [
            {"nombre": "Puesta en marcha", "enfoque": "ADAPTACION", "semanas": 6,
             "micros": [
                {"nombre": "Base", "semanas": 6, "sesiones": [
                    {"dia": 1, "nombre": "Fuerza suave", "tipo": "MIXTA", "lineas": CALENT + [
                        ("PRINCIPAL", "Sentadilla sin carga", 3, "10", "PESO_CORPORAL", None, 60, ""),
                        ("PRINCIPAL", "Press de pecho en máquina", 3, "12", "RIR", 3, 75, "DOBLE_PROGRESION"),
                        ("PRINCIPAL", "Remo en máquina", 3, "12", "RIR", 3, 75, "DOBLE_PROGRESION"),
                        ("ACCESORIO", "Puente de glúteo", 3, "12", "PESO_CORPORAL", None, 45, ""),
                        ("PRINCIPAL", "Caminata rápida", 1, "20 min", "TIEMPO", 1200, 0, ""),
                    ] + VUELTA},
                    {"dia": 2, "nombre": "Movilidad y equilibrio", "tipo": "MOVILIDAD", "lineas": CALENT + [
                        ("PRINCIPAL", "Movilidad de cadera 90/90", 3, "8", "PESO_CORPORAL", None, 30, ""),
                        ("PRINCIPAL", "Deslizamientos en pared", 3, "10", "PESO_CORPORAL", None, 30, ""),
                        ("PRINCIPAL", "Movilidad de tobillo rodilla a pared", 3, "10", "PESO_CORPORAL", None, 30, ""),
                        ("ACCESORIO", "Bicicleta estática", 1, "15 min", "TIEMPO", 900, 0, ""),
                    ] + VUELTA},
                ]}]},
            {"nombre": "Progresión", "enfoque": "ACUMULACION", "semanas": 6,
             "micros": [
                {"nombre": "Carga progresiva", "semanas": 6, "sesiones": [
                    {"dia": 1, "nombre": "Fuerza A", "tipo": "FUERZA", "lineas": CALENT + [
                        ("PRINCIPAL", "Sentadilla goblet", 3, "10", "RIR", 3, 90, "DOBLE_PROGRESION"),
                        ("PRINCIPAL", "Press de banca con mancuernas", 3, "10", "RIR", 3, 90, "DOBLE_PROGRESION"),
                        ("PRINCIPAL", "Jalón al pecho en polea", 3, "12", "RIR", 3, 90, "DOBLE_PROGRESION"),
                        ("CORE", "Plancha frontal", 3, "30 s", "TIEMPO", 30, 45, ""),
                    ] + VUELTA},
                    {"dia": 2, "nombre": "Fuerza B", "tipo": "FUERZA", "lineas": CALENT + [
                        ("PRINCIPAL", "Peso muerto rumano", 3, "10", "RIR", 3, 90, "DOBLE_PROGRESION"),
                        ("PRINCIPAL", "Press de hombro con mancuernas", 3, "10", "RIR", 3, 90, ""),
                        ("PRINCIPAL", "Remo con mancuerna a una mano", 3, "12", "RIR", 3, 90, ""),
                        ("CORE", "Bird dog", 3, "8", "PESO_CORPORAL", None, 45, ""),
                    ] + VUELTA},
                    {"dia": 3, "nombre": "Cardio", "tipo": "CARDIO", "lineas": CALENT + [
                        ("PRINCIPAL", "Caminata rápida", 1, "30 min", "TIEMPO", 1800, 0, ""),
                    ] + VUELTA},
                ]}]},
        ],
    },
]


def crear(repo: Repositorio) -> tuple[list[str], list[str]]:
    """Crea las plantillas que falten. Devuelve (creadas, avisos)."""
    por_nombre = {
        srv_ejercicios.sin_tildes(e["Nombre"]): e["ID_Ejercicio"]
        for e in repo.listar("T_EJERCICIOS")}
    existentes = {c["Nombre"] for c in repo.listar("T_CICLOS")}
    creadas, avisos = [], []

    for plantilla in PLANTILLAS:
        if plantilla["nombre"] in existentes:
            continue
        semanas = sum(m["semanas"] for m in plantilla["mesos"])
        id_macro = repo.insertar("T_CICLOS", {
            "Nombre": plantilla["nombre"], "Tipo": "MACRO", "Orden": 1,
            "Duracion_Sem": semanas, "Objetivo_Ciclo": plantilla["objetivo"],
            "Es_Plantilla_SN": True, "Origen": "MANUAL", "Notas": plantilla["notas"]})

        for orden_meso, meso in enumerate(plantilla["mesos"], start=1):
            id_meso = repo.insertar("T_CICLOS", {
                "Nombre": meso["nombre"], "Tipo": "MESO", "ID_Padre": id_macro,
                "Orden": orden_meso, "Duracion_Sem": meso["semanas"],
                "Enfoque": meso["enfoque"], "Es_Plantilla_SN": True, "Origen": "MANUAL"})

            for orden_micro, micro in enumerate(meso["micros"], start=1):
                id_micro = repo.insertar("T_CICLOS", {
                    "Nombre": micro["nombre"], "Tipo": "MICRO", "ID_Padre": id_meso,
                    "Orden": orden_micro, "Duracion_Sem": micro["semanas"],
                    "Es_Plantilla_SN": True, "Origen": "MANUAL"})

                for sesion in micro["sesiones"]:
                    id_sesion = repo.insertar("T_SESIONES", {
                        "ID_Ciclo": id_micro, "Num_Dia": sesion["dia"],
                        "Nombre": sesion["nombre"], "Tipo": sesion["tipo"]})
                    orden = 0
                    for (bloque, nombre, series, reps, modo, valor,
                         descanso, progresion) in sesion["lineas"]:
                        id_ejercicio = por_nombre.get(srv_ejercicios.sin_tildes(nombre))
                        if not id_ejercicio:
                            avisos.append(
                                f"«{plantilla['nombre']}» → {sesion['nombre']}: "
                                f"no existe el ejercicio «{nombre}», línea omitida")
                            continue
                        orden += 1
                        repo.insertar("T_SESION_DET", {
                            "ID_Sesion": id_sesion, "Orden": orden, "Bloque": bloque,
                            "ID_Ejercicio": id_ejercicio, "Series": series, "Reps": reps,
                            "Modo_Carga": modo, "Valor_Carga": valor,
                            "Descanso_Seg": descanso, "Progresion": progresion})
        creadas.append(plantilla["nombre"])
    return creadas, avisos
