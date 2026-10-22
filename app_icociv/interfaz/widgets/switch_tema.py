"""Interruptor claro/oscuro tipo pastilla: perilla y un icono lineal (sol o luna), sin texto."""

from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QAbstractButton, QSizePolicy

from app_icociv.interfaz.tema.colores import paleta
from app_icociv.interfaz.tema.iconos import icono_lineal

ANCHO, ALTO, MARGEN, LADO_ICONO = 56, 28, 3, 16


class SwitchTema(QAbstractButton):
    """Marcado = oscuro. Claro: perilla a la izquierda y sol a la derecha; oscuro: luna a la izquierda y perilla a la derecha."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.tema = "claro"
        self._iconos: dict[str, object] = {}

    def establecer_tema(self, tema: str) -> None:
        self.tema = tema
        self._iconos.clear()
        self.update()

    def sizeHint(self) -> QSize:  # noqa: N802 - firma Qt
        return QSize(ANCHO + 2 * MARGEN, ALTO + 2 * MARGEN)

    minimumSizeHint = sizeHint

    def paintEvent(self, _evento) -> None:  # noqa: N802 - firma Qt
        p = paleta(self.tema)
        oscuro = self.isChecked()
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        pista = QRectF(MARGEN, (self.height() - ALTO) / 2, ANCHO, ALTO)
        borde = p["foco"] if self.hasFocus() else p["borde_control"] if self.underMouse() else p["borde"]
        pintor.setPen(QPen(QColor(borde), 1.5 if self.hasFocus() else 1))
        pintor.setBrush(QColor(p["campo"] if oscuro else p["fondo_secundario"]))
        pintor.drawRoundedRect(pista, ALTO / 2, ALTO / 2)
        lado = ALTO - 2 * MARGEN
        x_perilla = pista.right() - MARGEN - lado if oscuro else pista.left() + MARGEN
        pintor.setPen(QPen(QColor(p["borde"]), 1))
        pintor.setBrush(QColor(p["superficie_3"] if oscuro else p["superficie"]))
        pintor.drawEllipse(QRectF(x_perilla, pista.top() + MARGEN, lado, lado))
        nombre = "tema_luna" if oscuro else "tema_sol"
        if nombre not in self._iconos:
            self._iconos[nombre] = icono_lineal(nombre, p["texto_secundario"]).pixmap(LADO_ICONO * 2, LADO_ICONO * 2)
        centro_x = pista.left() + MARGEN + lado / 2 if oscuro else pista.right() - MARGEN - lado / 2
        pintor.drawPixmap(QRectF(centro_x - LADO_ICONO / 2, pista.center().y() - LADO_ICONO / 2, LADO_ICONO, LADO_ICONO).toRect(),
                          self._iconos[nombre])
        pintor.end()
