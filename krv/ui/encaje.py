"""Que ninguna ventana se salga de la pantalla.

El programa se escribe en un monitor grande y luego se usa en un portátil, o en
una pantalla con el escalado de Windows al 125 %. Entonces una ventana pensada
para 760 píxeles de alto ya no cabe, Qt la centra igualmente y la barra de
título se queda por encima del borde: no hay forma de moverla ni de cerrarla
con el ratón.

Esto se engancha una sola vez a la aplicación y vigila todas las ventanas que
se abren, también las que se añadan en el futuro.
"""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QRect, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication, QWidget

# Un respiro contra el borde, para que no quede pegada.
MARGEN = 16
# Por debajo de esto una ventana ya no se puede usar; mejor dejarla asomar.
MINIMO = 320


def pantalla_de(ventana: QWidget):
    """La pantalla donde está la ventana, o la principal si aún no lo sabe."""
    return (ventana.screen()
            or (ventana.parent().screen() if ventana.parent() else None)
            or QGuiApplication.primaryScreen())


def encajar(ventana: QWidget, disponible: QRect | None = None) -> bool:
    """Encoge y recoloca la ventana hasta que quepa entera. Dice si la tocó.

    `disponible` permite pasar otro rectángulo en vez del de la pantalla, que
    es lo que hace falta para poder probar esto con pantallas pequeñas sin
    tener una.
    """
    if disponible is None:
        pantalla = pantalla_de(ventana)
        if pantalla is None:
            return False
        disponible = pantalla.availableGeometry()
    marco = ventana.frameGeometry()
    if marco.isEmpty():
        return False
    tocada = False

    # El marco (barra de título y bordes) no cuenta como tamaño del contenido,
    # así que hay que descontarlo antes de redimensionar.
    extra_ancho = max(marco.width() - ventana.width(), 0)
    extra_alto = max(marco.height() - ventana.height(), 0)
    tope_ancho = disponible.width() - MARGEN * 2 - extra_ancho
    tope_alto = disponible.height() - MARGEN * 2 - extra_alto

    ancho = min(ventana.width(), max(tope_ancho, MINIMO))
    alto = min(ventana.height(), max(tope_alto, MINIMO))
    if (ancho, alto) != (ventana.width(), ventana.height()):
        # Un mínimo mayor que la pantalla impediría encogerla.
        ventana.setMinimumSize(min(ventana.minimumWidth(), ancho),
                               min(ventana.minimumHeight(), alto))
        ventana.resize(ancho, alto)
        marco = ventana.frameGeometry()
        tocada = True

    # Ahora que cabe, que esté dentro. Se mueve el marco, pero move() coloca el
    # contenido: la diferencia entre los dos es lo que hay que compensar.
    destino_x = min(max(marco.x(), disponible.x() + MARGEN),
                    disponible.right() - marco.width() + 1 - MARGEN)
    destino_y = min(max(marco.y(), disponible.y() + MARGEN),
                    disponible.bottom() - marco.height() + 1 - MARGEN)
    destino_x = max(destino_x, disponible.x())
    destino_y = max(destino_y, disponible.y())
    if (destino_x, destino_y) != (marco.x(), marco.y()):
        ventana.move(destino_x + (ventana.x() - marco.x()),
                     destino_y + (ventana.y() - marco.y()))
        tocada = True
    return tocada


class _Vigilante(QObject):
    """Encaja cada ventana justo después de que se muestre.

    Se espera un ciclo del bucle de eventos: en el momento del «show» el
    contenido todavía no ha terminado de colocarse y el tamaño definitivo aún
    no se conoce.
    """

    def eventFilter(self, objeto, evento) -> bool:
        if (evento.type() == QEvent.Show and isinstance(objeto, QWidget)
                and objeto.isWindow()):
            QTimer.singleShot(0, lambda: _encajar_si_sigue_viva(objeto))
        return False


def _encajar_si_sigue_viva(ventana: QWidget) -> None:
    try:
        if ventana.isVisible():
            encajar(ventana)
    except RuntimeError:
        pass        # se cerró entre medias y Qt ya la ha destruido


_vigilante: _Vigilante | None = None


def instalar(app: QApplication | None = None) -> None:
    """Engancha la vigilancia a la aplicación. Se puede llamar más de una vez."""
    global _vigilante
    if _vigilante is not None:
        return
    app = app or QApplication.instance()
    if app is None:
        return
    _vigilante = _Vigilante(app)
    app.installEventFilter(_vigilante)
