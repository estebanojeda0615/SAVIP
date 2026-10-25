"""Fase V1.1.2-01C: un mensaje largo se puede leer.

Con el texto en el área desplazable, QMessageBox se recalculaba y la caja se encogía a ~140×120 px
con una sola línea a la vista y sin ajuste de línea. Aquí se exige que se vean varias líneas enteras y que
los mensajes cortos no cambien.
"""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QLabel, QMessageBox, QScrollArea

from tests.test_v112_01_esqueleto_dialogos import _abrir, _ventana, _visible_en

LINEAS_VISIBLES = 5


def _mensaje(ventana, lineas):
    texto = "\n".join(f"• Análisis {i}: Pavimentos asfálticos / concreto · grupo sintético · 2027-07 · 11 meses"
                      for i in range(lineas))
    return QMessageBox(QMessageBox.Icon.Warning, "Actualizar análisis", texto, QMessageBox.StandardButton.Ok, ventana)


def _medir(caja):
    area = caja.findChild(QScrollArea, "savip_desplazamiento_mensaje")
    etiqueta = caja.findChild(QLabel, "qt_msgbox_label")
    vista = area.viewport() if area is not None else etiqueta
    return {"marco": caja.frameGeometry(), "pantalla": caja.screen().availableGeometry(), "area": area,
            "alto_visible": vista.height(), "ancho_visible": vista.width(), "linea": etiqueta.fontMetrics().lineSpacing(),
            "texto_entero": etiqueta.height() >= etiqueta.heightForWidth(etiqueta.width()),
            "sin_corte_horizontal": area is None or not area.horizontalScrollBar().isVisible(),
            "ok": _visible_en(caja.button(QMessageBox.StandardButton.Ok), caja)}


@pytest.mark.parametrize("ancho", [640, 1280])
@pytest.mark.parametrize("lineas", [20, 50, 200])
def test_mensaje_largo_muestra_varias_lineas(ancho, lineas):
    ventana = _ventana(ancho, 720)
    d = _abrir(_mensaje(ventana, lineas), _medir)
    assert d["area"] is not None and d["ok"]
    assert d["alto_visible"] >= LINEAS_VISIBLES * d["linea"], (d["alto_visible"], d["linea"])
    assert d["ancho_visible"] >= 200 and d["sin_corte_horizontal"], (d["ancho_visible"], d["sin_corte_horizontal"])
    assert d["pantalla"].contains(d["marco"])


@pytest.mark.parametrize("ancho", [640, 1280])
def test_mensaje_corto_sin_desplazamiento_y_entero(ancho):
    ventana = _ventana(ancho, 720)
    d = _abrir(_mensaje(ventana, 3), _medir)
    assert d["area"] is None and d["texto_entero"] and d["ok"]
    assert d["pantalla"].contains(d["marco"])
