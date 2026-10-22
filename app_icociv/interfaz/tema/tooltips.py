"""Ajuste común de tooltips (ajuste de línea para ayudas largas).

Qt solo ajusta el texto de un tooltip cuando es texto enriquecido; una ayuda larga en texto plano se
muestra en una sola línea y puede ocupar media pantalla (más aún en pantalla dividida). Este filtro,
instalado una vez en la aplicación, convierte esas ayudas en un párrafo HTML antes de mostrarse, sin
cambiar su contenido.
"""

from __future__ import annotations

from html import escape

from PySide6.QtCore import QEvent, QObject
from PySide6.QtWidgets import QWidget

LARGO_AJUSTE = 60  # caracteres: por encima se muestra en párrafo con ajuste de línea
ANCHO_PX = 320


def como_parrafo(texto: str) -> str:
    """Texto plano → párrafo enriquecido que Qt ajusta en varias líneas (respeta saltos de línea)."""
    if not texto or texto.lstrip().startswith("<") or len(texto) <= LARGO_AJUSTE:
        return texto
    # Ancho fijo moderado (~320 px): Qt ajusta el texto enriquecido de forma muy estrecha por defecto.
    return f"<table width='{ANCHO_PX}'><tr><td>" + escape(texto).replace("\n", "<br>") + "</td></tr></table>"


class AjusteTooltips(QObject):
    def eventFilter(self, objeto, evento) -> bool:  # noqa: N802 - firma Qt
        if evento.type() == QEvent.Type.ToolTip and isinstance(objeto, QWidget):
            texto = objeto.toolTip()
            ajustado = como_parrafo(texto)
            if ajustado != texto:
                objeto.setToolTip(ajustado)
        return False
