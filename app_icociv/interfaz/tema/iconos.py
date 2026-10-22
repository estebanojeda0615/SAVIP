"""Iconos lineales de SAVIP: un solo SVG por icono, recoloreado según el texto del control y su estado."""

from __future__ import annotations

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QPainter, QPalette, QPixmap
from PySide6.QtSvg import QSvgRenderer

from app_icociv.config.rutas import ruta_recurso

_TRAZO_BASE = "#AEB9C6"  # color con el que se dibujan los SVG de recursos


def icono_lineal(nombre: str, color: str, color_deshabilitado: str | None = None, lado: int = 40) -> QIcon:
    """``nombre`` sin extensión (p. ej. «accion_cargar»); ``color`` en hex. Devuelve un QIcon nítido."""
    svg = ruta_recurso(f"app_icociv/interfaz/recursos/{nombre}.svg").read_text(encoding="utf-8")
    icono = QIcon()
    for modo, tinta in ((QIcon.Mode.Normal, color), (QIcon.Mode.Disabled, color_deshabilitado or color)):
        imagen = QPixmap(lado, lado); imagen.fill(Qt.GlobalColor.transparent)
        pintor = QPainter(imagen)
        QSvgRenderer(QByteArray(svg.replace(_TRAZO_BASE, tinta).encode())).render(pintor)
        pintor.end()
        icono.addPixmap(imagen, modo)
    return icono


def icono_para(widget, nombre: str) -> QIcon:
    """Icono teñido con el color de texto vigente del widget (sigue el tema y el estilo del botón)."""
    paleta = widget.palette()
    return icono_lineal(nombre, paleta.color(QPalette.ColorGroup.Active, QPalette.ColorRole.ButtonText).name(),
                        paleta.color(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText).name())
