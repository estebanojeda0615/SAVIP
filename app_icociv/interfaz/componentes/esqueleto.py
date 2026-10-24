"""Esqueletos de carga (Skeleton Loaders) y franja de progreso de SAVIP (Fase V1.1.2-01).

Mientras una operación larga prepara contenido, el área de trabajo muestra la silueta de lo que va
a aparecer (tarjetas, gráfica, tablas, filtros) en lugar de un velo anónimo. Encima, una franja
dice la etapa REAL en curso. La barra solo se llena cuando el llamador mide el avance
(`establecer_progreso`); si no, es un indicador indeterminado. No se inventan porcentajes.

Todo se pinta en dos widgets con un único temporizador del velo: no hay un widget ni una animación
por fila. Con `movimiento_reducido()` el temporizador no se inicia y el esqueleto queda estático.
"""

from __future__ import annotations

import math

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QWidget

from app_icociv.interfaz.tema import tokens
from app_icociv.interfaz.tema.colores import normalizar_tema, paleta

#: Variantes: la geometría de cada una imita el contenido real que se está preparando.
VARIANTES = ("anexo", "resultados", "sesion")


def bloques(variante: str, ancho: float, alto: float) -> tuple[list[QRectF], list[QRectF]]:
    """Tarjetas y barras de la variante para un área de `ancho`×`alto` (función pura, se prueba sola).

    Las tarjetas nunca salen del área; las barras siempre quedan dentro de su tarjeta.
    """
    m, g = 14.0, 12.0  # mismos márgenes y separación que el panel principal
    tarjetas: list[QRectF] = []
    barras: list[QRectF] = []
    ancho_util = max(0.0, ancho - 2 * m)

    def tarjeta(x, y, w, h) -> QRectF:
        r = QRectF(x, y, max(0.0, w), max(0.0, min(h, alto - m - y)))
        if r.height() > 24 and r.width() > 24:
            tarjetas.append(r)
        return r

    def barra(t: QRectF, fx, fy, fw, h) -> None:
        r = QRectF(t.x() + 16 + fx * (t.width() - 32), t.y() + fy, max(8.0, fw * (t.width() - 32)), h)
        if r.bottom() <= t.bottom() - 10 and r.right() <= t.right() - 12:
            barras.append(r)

    def tabla(t: QRectF, columnas: tuple[float, ...], inicio: float = 18) -> None:
        y = t.y() + inicio
        x = 0.0
        for fw in columnas:  # cabecera
            barra(t, x, y - t.y(), fw * 0.7, 10); x += fw
        y += 30
        fila = 0
        while y + 12 <= t.bottom() - 12:
            x = 0.0
            for i, fw in enumerate(columnas):
                variacion = 0.55 + 0.35 * ((fila * 7 + i * 3) % 5) / 4
                barra(t, x, y - t.y(), fw * variacion, 9); x += fw
            y += 28; fila += 1

    y = m
    if variante == "anexo":
        # Filtros jerárquicos (grupo, subgrupo, capítulo, serie) y la tabla de la serie.
        filtros = tarjeta(m, y, ancho_util, 96)
        n = 4 if ancho_util >= 760 else 2
        paso = 1 / n
        for i in range(n):
            barra(filtros, i * paso, 16, paso * 0.45, 10)
            barra(filtros, i * paso, 38, paso * 0.88, 30)
        y += 96 + g
        tabla(tarjeta(m, y, ancho_util, alto - y - m), (0.18, 0.34, 0.16, 0.16, 0.16))
    elif variante == "sesion":
        # Resumen de la sesión (tarjetas) y el historial de análisis.
        n = 3 if ancho_util >= 640 else 2
        w = (ancho_util - g * (n - 1)) / n
        for i in range(n):
            t = tarjeta(m + i * (w + g), y, w, 84)
            barra(t, 0, 16, 0.5, 10); barra(t, 0, 36, 0.7, 20); barra(t, 0, 64, 0.35, 8)
        y += 84 + g
        lista = tarjeta(m, y, ancho_util, alto - y - m)
        barra(lista, 0, 18, 0.3, 12)
        fila_y = 54.0
        while lista.y() + fila_y + 30 <= lista.bottom() - 12:
            barra(lista, 0, fila_y, 0.04, 24); barra(lista, 0.07, fila_y + 2, 0.5, 10); barra(lista, 0.07, fila_y + 17, 0.3, 8)
            fila_y += 44
    else:  # "resultados": cabecera, indicadores (KPI), gráfica y tabla
        cab = tarjeta(m, y, ancho_util, 64)
        barra(cab, 0, 16, 0.34, 14); barra(cab, 0, 40, 0.22, 9)
        y += 64 + g
        n = 4 if ancho_util >= 900 else 2
        w = (ancho_util - g * (n - 1)) / n
        for i in range(n):
            t = tarjeta(m + i * (w + g), y, w, tokens.TARJETA_KPI_MIN_ALTURA)
            barra(t, 0, 14, 0.45, 9); barra(t, 0, 33, 0.6, 20); barra(t, 0, 62, 0.35, 8)
        y += tokens.TARJETA_KPI_MIN_ALTURA + g
        resto = alto - y - m
        if ancho_util >= 900:
            wg = ancho_util * 0.58
            grafica = tarjeta(m, y, wg, resto)
            tabla(tarjeta(m + wg + g, y, ancho_util - wg - g, resto), (0.3, 0.35, 0.35))
        else:
            grafica = tarjeta(m, y, ancho_util, resto * 0.55)
            tabla(tarjeta(m, y + resto * 0.55 + g, ancho_util, resto * 0.45 - g), (0.3, 0.35, 0.35))
        barra(grafica, 0, 16, 0.3, 12)
        area = QRectF(grafica.x() + 16, grafica.y() + 44, grafica.width() - 32, grafica.height() - 60)
        if area.height() > 30:
            barras.append(area)
    return tarjetas, barras


class EsqueletoContenido(QWidget):
    """Silueta del contenido esperado. Se pinta entera en `paintEvent`; `fase` mueve el brillo."""

    def __init__(self, parent: QWidget | None = None, tema: str | None = "claro") -> None:
        super().__init__(parent)
        self.setObjectName("esqueleto_contenido")
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAccessibleName("Contenido en preparación")
        self.variante = "resultados"
        self.fase = 0.0
        self.actualizar_tema(tema)

    def actualizar_tema(self, tema: str | None) -> None:
        self._tema = normalizar_tema(tema)
        self.update()

    def establecer_variante(self, variante: str) -> None:
        self.variante = variante if variante in VARIANTES else "resultados"
        self.update()

    def avanzar(self, paso: float) -> None:
        self.fase = (self.fase + paso) % 1.0
        self.update()

    def paintEvent(self, _evento) -> None:  # noqa: N802 - firma Qt
        c = paleta(self._tema)
        oscuro = self._tema == "oscuro"
        tarjetas, barras = bloques(self.variante, self.width(), self.height())
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor(c["borde"]), tokens.GROSOR_BORDE))
        p.setBrush(QColor(c["superficie"]))
        for t in tarjetas:
            p.drawRoundedRect(t, tokens.RADIO_MEDIO, tokens.RADIO_MEDIO)
        base = QColor(c["superficie_3"])
        ruta = QPainterPath()
        for b in barras:
            ruta.addRoundedRect(b, 4, 4)
        p.setPen(Qt.PenStyle.NoPen)
        p.fillPath(ruta, base)
        # Brillo (shimmer): una banda diagonal suave que recorre el área de izquierda a derecha.
        brillo = base.lighter(125 if oscuro else 106)
        ancho = max(1.0, float(self.width()))
        centro = -0.25 * ancho + self.fase * 1.5 * ancho
        gradiente = QLinearGradient(centro - 0.18 * ancho, 0, centro + 0.18 * ancho, ancho * 0.08)
        transparente = QColor(brillo); transparente.setAlpha(0)
        gradiente.setColorAt(0.0, transparente); gradiente.setColorAt(0.5, brillo); gradiente.setColorAt(1.0, transparente)
        p.fillPath(ruta, gradiente)
        p.end()


class FranjaProgreso(QFrame):
    """Etapa en curso y barra fina: medida (determinada) o indeterminada honesta."""

    def __init__(self, parent: QWidget | None = None, tema: str | None = "claro") -> None:
        super().__init__(parent)
        self.setObjectName("franja_progreso")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(tokens.ESPACIO_5, tokens.ESPACIO_3, tokens.ESPACIO_5, tokens.ESPACIO_3 + 4)
        layout.setSpacing(tokens.ESPACIO_3)
        self.etiqueta = QLabel("Procesando…")
        self.etiqueta.setObjectName("texto_carga")
        self.etiqueta.setWordWrap(True)
        self.etiqueta.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.etiqueta, 1)
        self.boton_cancelar = QPushButton("Cancelar")
        self.boton_cancelar.setObjectName("boton_secundario")
        self.boton_cancelar.setVisible(False)
        layout.addWidget(self.boton_cancelar, 0, Qt.AlignmentFlag.AlignVCenter)
        self.indeterminada = True
        self.valor = 0
        self.maximo = 100
        self.fase = 0.0
        self.actualizar_tema(tema)
        self._anunciar()

    def actualizar_tema(self, tema: str | None) -> None:
        self._tema = normalizar_tema(tema)
        self.update()

    def establecer_texto(self, texto: str) -> None:
        self.etiqueta.setText(texto)
        self._anunciar()

    def establecer_progreso(self, valor: int | None, maximo: int = 100) -> None:
        """Avance MEDIDO por el llamador; `None` vuelve al modo indeterminado."""
        if valor is None:
            self.indeterminada = True
        else:
            self.indeterminada = False
            self.maximo = max(1, int(maximo))
            self.valor = max(0, min(int(valor), self.maximo))
        self._anunciar()
        self.update()

    def porcentaje(self) -> float | None:
        """Porcentaje medido, o `None` si el avance no se puede medir (indeterminado)."""
        return None if self.indeterminada else 100.0 * self.valor / self.maximo

    def avanzar(self, paso: float) -> None:
        self.fase = (self.fase + paso) % 1.0
        if self.indeterminada:
            self.update()

    def _anunciar(self) -> None:
        estado = "avance no medible" if self.indeterminada else f"{self.porcentaje():.0f} %"
        self.setAccessibleName(f"{self.etiqueta.text()} ({estado})")

    def paintEvent(self, evento) -> None:  # noqa: N802 - firma Qt
        super().paintEvent(evento)
        c = paleta(self._tema)
        p = QPainter(self)
        alto = 4
        pista = QRectF(0, self.height() - alto, self.width(), alto)
        p.fillRect(pista, QColor(c["superficie_3"]))
        relleno = QColor(c["principal"])
        if self.indeterminada:
            # Segmento que entra y sale; nunca representa una fracción del trabajo.
            ancho = self.width() * 0.28
            t = 0.5 - 0.5 * math.cos(math.pi * self.fase)  # suavizado
            x = -ancho + t * (self.width() + ancho)
            p.fillRect(QRectF(x, pista.y(), ancho, alto).intersected(pista), relleno)
        else:
            p.fillRect(QRectF(0, pista.y(), self.width() * self.valor / self.maximo, alto), relleno)
        p.end()


__all__ = ["EsqueletoContenido", "FranjaProgreso", "VARIANTES", "bloques"]
