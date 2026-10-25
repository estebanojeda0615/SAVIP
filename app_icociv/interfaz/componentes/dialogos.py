"""Ventanas emergentes que no se salen de SAVIP (Fase V1.1.2-01).

Causa del defecto: los diálogos se dimensionaban sin mirar la ventana de SAVIP.
* `QMessageBox` calcula su ancho a partir del MONITOR (hasta ~500 px de texto más el icono).
* Varios `QDialog` fijan tamaños de escritorio: 1060×420 la confirmación de fechas, 760×660 el
  informe (mínimo 620×520), 900×640 el visor de gráfica y 760×640 las explicaciones.
Qt los centra sobre la ventana dueña. Con SAVIP en Snap 1/2 o 1/3, a 1366×768 o simplemente
reducida, el diálogo quedaba más ancho que la ventana y sobresalía de ella; si la ventana estaba
junto al borde del monitor, sobresalía también del monitor.

Corrección central: un filtro de eventos de la aplicación (mismo patrón que `AjusteTooltips`)
intercepta el primer `Show` de cada diálogo de SAVIP. Deja que Qt calcule su tamaño (`showEvent`)
y, ANTES de que Windows muestre la ventana:
1. limita su tamaño al área visible de la ventana de SAVIP (∩ área útil de su monitor), o al
   monitor si el contenido mínimo del diálogo no cabe físicamente en la ventana;
2. activa el ajuste de línea de los mensajes y, si el texto sigue sin caber, lo pone en un área
   desplazable. Los botones quedan siempre fuera del área desplazable, a la vista;
3. lo centra sobre la ventana dueña y lo encierra en esa área.
No cambia textos, botones, botón predeterminado ni el resultado de ningún diálogo. Los selectores
de archivos nativos de Windows no son diálogos Qt y no se tocan.
"""

from __future__ import annotations

from PySide6.QtCore import QEvent, QMargins, QObject, QRect, QSize
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QApplication,
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFontDialog,
    QFrame,
    QLabel,
    QMessageBox,
    QScrollArea,
    QWidget,
)

MARGEN = 12  # separación mínima entre el diálogo y el borde del área permitida
ANCHO_MINIMO_MENSAJE = 260
LINEAS_LEGIBLES = 6  # líneas de texto que el área desplazable deja siempre a la vista
_EXCLUIDOS = (QFileDialog, QColorDialog, QFontDialog)


def geometria_dialogo(tamano: QSize, minimo: QSize, marco_ventana: QRect | None, util_monitor: QRect,
                      bordes: QMargins) -> tuple[QRect, str]:
    """Rectángulo de CLIENTE del diálogo y ámbito («ventana» o «monitor»). Función pura.

    `marco_ventana` es el marco (frameGeometry) de la ventana dueña en coordenadas globales;
    `bordes`, el marco nativo estimado del diálogo (barra de título y bordes).
    """
    def cliente_max(area: QRect) -> QSize:
        return QSize(area.width() - bordes.left() - bordes.right() - 2 * MARGEN,
                     area.height() - bordes.top() - bordes.bottom() - 2 * MARGEN)

    zona, ambito = util_monitor, "monitor"
    if marco_ventana is not None and marco_ventana.intersects(util_monitor):
        visible = marco_ventana.intersected(util_monitor)
        limite = cliente_max(visible)
        if minimo.width() <= limite.width() and minimo.height() <= limite.height():
            zona, ambito = visible, "ventana"
    limite = cliente_max(zona)
    ancho = max(minimo.width(), min(tamano.width(), limite.width()))
    alto = max(minimo.height(), min(tamano.height(), limite.height()))
    ancho_marco = ancho + bordes.left() + bordes.right()
    alto_marco = alto + bordes.top() + bordes.bottom()
    centro = (marco_ventana if marco_ventana is not None else zona).center()
    x = _encajar(centro.x() - ancho_marco // 2, ancho_marco, zona.left(), zona.width())
    y = _encajar(centro.y() - alto_marco // 2, alto_marco, zona.top(), zona.height())
    return QRect(x + bordes.left(), y + bordes.top(), ancho, alto), ambito


def _encajar(posicion: int, largo: int, inicio: int, disponible: int) -> int:
    """Mantiene [posicion, posicion+largo] dentro de [inicio, inicio+disponible] (con margen si cabe)."""
    if largo + 2 * MARGEN <= disponible:
        return min(max(posicion, inicio + MARGEN), inicio + disponible - MARGEN - largo)
    if largo <= disponible:
        return inicio + (disponible - largo) // 2
    return inicio  # más grande que el área: se ancla al inicio para que título y contenido queden a la vista


def _ventana_duena(dialogo: QDialog) -> QWidget | None:
    padre = dialogo.parentWidget()
    ventana = padre.window() if padre is not None else QApplication.activeWindow()
    if ventana is None or ventana is dialogo or not ventana.isVisible():
        return None
    return ventana


def _bordes(ventana: QWidget | None) -> QMargins:
    """Marco nativo estimado: el de la ventana dueña (misma decoración de Windows)."""
    if ventana is None:
        return QMargins(0, 0, 0, 0)
    marco, cliente = ventana.frameGeometry(), ventana.geometry()
    return QMargins(max(0, cliente.left() - marco.left()), max(0, cliente.top() - marco.top()),
                    max(0, marco.right() - cliente.right()), max(0, marco.bottom() - cliente.bottom()))


def _minimo_caja(caja: QMessageBox) -> QSize:
    botones = caja.findChild(QDialogButtonBox)
    m = caja.layout().contentsMargins() if caja.layout() else QMargins()
    ancho_botones = (botones.sizeHint().width() if botones is not None else 0) + m.left() + m.right()
    return QSize(max(ANCHO_MINIMO_MENSAJE, ancho_botones), 120)


def _ajuste_de_linea(caja: QMessageBox) -> None:
    for nombre in ("qt_msgbox_label", "qt_msgbox_informativelabel"):
        etiqueta = caja.findChild(QLabel, nombre)
        if etiqueta is not None:
            etiqueta.setWordWrap(True)


def _minimo_lectura(caja: QMessageBox, minimo: QSize) -> QSize:
    """Mínimo con el texto desplazable: botones y márgenes más `LINEAS_LEGIBLES` líneas de texto a la vista."""
    etiqueta = caja.findChild(QLabel, "qt_msgbox_label")
    botones = caja.findChild(QDialogButtonBox)
    rejilla = caja.layout()
    if etiqueta is None or rejilla is None:
        return minimo
    m = rejilla.contentsMargins()
    alto = (m.top() + m.bottom() + max(rejilla.verticalSpacing(), 0)
            + (botones.sizeHint().height() if botones is not None else 0)
            + LINEAS_LEGIBLES * etiqueta.fontMetrics().lineSpacing() + 2 * etiqueta.margin())
    return QSize(minimo.width(), max(minimo.height(), alto))


def _texto_desplazable(caja: QMessageBox) -> None:
    """Pone el texto principal en un área desplazable (los botones siguen fuera de ella)."""
    etiqueta = caja.findChild(QLabel, "qt_msgbox_label")
    rejilla = caja.layout()
    if etiqueta is None or rejilla is None or caja.findChild(QScrollArea, "savip_desplazamiento_mensaje"):
        return
    indice = rejilla.indexOf(etiqueta)
    if indice < 0:
        return
    fila, columna, filas, columnas = rejilla.getItemPosition(indice)
    rejilla.removeWidget(etiqueta)
    area = QScrollArea(caja)
    area.setObjectName("savip_desplazamiento_mensaje")
    area.setWidgetResizable(True)
    area.setFrameShape(QFrame.Shape.NoFrame)
    area.setWidget(etiqueta)
    rejilla.addWidget(area, fila, columna, filas, columnas)


def ajustar_dialogo(dialogo: QDialog) -> str:
    """Dimensiona y coloca `dialogo` (ya calculado por Qt, aún sin mostrarse). Devuelve el ámbito."""
    ventana = _ventana_duena(dialogo)
    pantalla = (ventana.screen() if ventana is not None else None) or dialogo.screen() or QGuiApplication.primaryScreen()
    util = pantalla.availableGeometry()
    bordes = _bordes(ventana)
    marco = ventana.frameGeometry() if ventana is not None else None
    if isinstance(dialogo, QMessageBox):
        minimo = _minimo_caja(dialogo)
        lectura = dialogo.property("savip_tamano_lectura")
        if lectura is not None:
            # Con el texto ya desplazable, QMessageBox se recalcula al mínimo del área (una sola línea a la
            # vista, sin ajuste de línea): se reaplican el ajuste y el tamaño de lectura decididos al activarlo.
            _ajuste_de_linea(dialogo)
            destino, ambito = geometria_dialogo(lectura, _minimo_lectura(dialogo, minimo), marco, util, bordes)
            dialogo.setFixedSize(destino.size())
        else:
            destino, ambito = geometria_dialogo(dialogo.size(), minimo, marco, util, bordes)
            if destino.width() < dialogo.width() or destino.height() < dialogo.height():
                _ajuste_de_linea(dialogo)
                rejilla = dialogo.layout()
                rejilla.activate()
                alto = rejilla.totalHeightForWidth(destino.width()) if rejilla.hasHeightForWidth() else dialogo.height()
                if alto > destino.height():
                    _texto_desplazable(dialogo)
                    alto = destino.height()
                    minimo = _minimo_lectura(dialogo, minimo)
                destino, ambito = geometria_dialogo(QSize(destino.width(), max(alto, minimo.height())), minimo, marco, util, bordes)
                if dialogo.findChild(QScrollArea, "savip_desplazamiento_mensaje") is not None:
                    dialogo.setProperty("savip_tamano_lectura", destino.size())
                dialogo.setFixedSize(destino.size())
    else:
        disposicion = dialogo.layout()
        minimo = disposicion.minimumSize() if disposicion is not None else dialogo.minimumSizeHint()
        minimo = minimo.expandedTo(QSize(120, 80))
        destino, ambito = geometria_dialogo(dialogo.size(), minimo, marco, util, bordes)
        explicito = dialogo.minimumSize()
        dialogo.setMinimumSize(min(explicito.width(), max(minimo.width(), destino.width())),
                               min(explicito.height(), max(minimo.height(), destino.height())))
        dialogo.resize(destino.size())
    dialogo.move(destino.left() - bordes.left(), destino.top() - bordes.top())
    dialogo.setProperty("savip_ambito_dialogo", ambito)
    return ambito


class AjusteDialogos(QObject):
    """Filtro de la aplicación que aplica `ajustar_dialogo` al mostrarse cada diálogo Qt."""

    def eventFilter(self, objeto, evento):  # noqa: N802 - firma Qt
        tipo = evento.type()
        mostrar = tipo == QEvent.Type.Show and isinstance(objeto, QDialog) and objeto.isWindow()
        # QMessageBox recalcula su tamaño (a partir del monitor) en cada LayoutRequest, también el que
        # provoca activar el ajuste de línea: se deja actuar a Qt y se vuelve a acotar.
        recalcular = (tipo == QEvent.Type.LayoutRequest and isinstance(objeto, QMessageBox)
                      and objeto.isVisible() and objeto.property("savip_ambito_dialogo") is not None)
        if ((mostrar or recalcular) and not isinstance(objeto, _EXCLUIDOS)
                and not objeto.property("savip_ajustando")):
            objeto.setProperty("savip_ajustando", True)
            try:
                objeto.event(evento)  # showEvent propio (QMessageBox calcula aquí su tamaño)
                ajustar_dialogo(objeto)
            finally:
                objeto.setProperty("savip_ajustando", False)
            return True
        return False


def instalar_ajuste_dialogos(aplicacion: QApplication | None = None) -> AjusteDialogos:
    """Instala el filtro una sola vez por aplicación (varias ventanas lo comparten)."""
    aplicacion = aplicacion or QApplication.instance()
    existente = getattr(aplicacion, "_savip_ajuste_dialogos", None)
    if existente is None:
        existente = AjusteDialogos(aplicacion)
        aplicacion.installEventFilter(existente)
        aplicacion._savip_ajuste_dialogos = existente
    return existente


__all__ = ["AjusteDialogos", "ajustar_dialogo", "geometria_dialogo", "instalar_ajuste_dialogos"]
