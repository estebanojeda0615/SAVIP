"""Indicador de trabajo en curso, superpuesto al área de contenido.

Las operaciones largas ya se ejecutan en un hilo (`TrabajadorFuncion`), de modo
que la ventana nunca se congela; lo que faltaba era decírselo al usuario. Este
velo cubre solo el área de contenido, deja visible la cabecera y describe la
etapa en curso en lugar de mostrar un giro anónimo.
"""

from __future__ import annotations

import math
from typing import Callable

from PySide6.QtCore import QElapsedTimer, Qt, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app_icociv.interfaz.animaciones.microinteracciones import aplicar_elevacion
from app_icociv.interfaz.animaciones.transiciones import (
    desvanecer_entrada,
    desvanecer_salida,
)
from app_icociv.interfaz.tema import tokens


ESCALA = 1000  # resolución de la barra (0–1000 ↔ 0–100 %)
DURACION_FASE_RAPIDA = 4.0  # s hasta ~85 %
PAUSA = 0.45  # s detenida en 85 %


def progreso_estimado(segundos: float) -> float:
    """Porcentaje VISUAL estimado (no mide el trabajo): ease-out hasta 85 % en 4 s, pausa breve y
    avance lento y asintótico hacia 94 %, sin alcanzar 100 % hasta que el trabajo termina."""
    if segundos <= 0:
        return 0.0
    if segundos < DURACION_FASE_RAPIDA:
        return 85 * (1 - (1 - segundos / DURACION_FASE_RAPIDA) ** 3)
    if segundos < DURACION_FASE_RAPIDA + PAUSA:
        return 85.0
    return 94 - 9 * math.exp(-(segundos - DURACION_FASE_RAPIDA - PAUSA) / 8)


class VeloCarga(QFrame):
    """Superposición con mensaje de etapa y barra de progreso indeterminada."""

    def __init__(self, contenedor: QWidget, tema: str | None = "claro") -> None:
        super().__init__(contenedor)
        self.setObjectName("velo_carga")
        self._contenedor = contenedor
        self._al_cancelar: Callable[[], None] | None = None
        # Sin esto el velo no bloquearía los clics sobre los controles de abajo.
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch(1)

        fila = QHBoxLayout()
        fila.addStretch(1)

        self.panel = QFrame()
        self.panel.setObjectName("panel_carga")
        self.panel.setMinimumWidth(320)
        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(
            tokens.ESPACIO_6, tokens.ESPACIO_5, tokens.ESPACIO_6, tokens.ESPACIO_5
        )
        panel_layout.setSpacing(tokens.ESPACIO_3)

        self.etiqueta = QLabel("Procesando…")
        self.etiqueta.setObjectName("texto_carga")
        self.etiqueta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        panel_layout.addWidget(self.etiqueta)

        self.barra = QProgressBar()
        self.barra.setTextVisible(False)
        self.barra.setRange(0, ESCALA)
        self.barra.setAccessibleName("Progreso visual estimado")
        panel_layout.addWidget(self.barra)
        # Fase 4I-C: el cuadro muestra SOLO título y barra (sin porcentaje ni textos accesorios);
        # la barra sigue siendo progreso visual estimado y su nombre accesible lo declara.

        self.boton_cancelar = QPushButton("Cancelar")
        self.boton_cancelar.setObjectName("boton_secundario")
        self.boton_cancelar.setVisible(False)
        self.boton_cancelar.clicked.connect(self._cancelar)
        panel_layout.addWidget(self.boton_cancelar, 0, Qt.AlignmentFlag.AlignCenter)

        self._reloj = QElapsedTimer()
        self._activo = False
        self._real = False  # True si el llamador informa progreso medido
        self._animacion = QTimer(self)
        self._animacion.setInterval(40)
        self._animacion.timeout.connect(self._avanzar)
        # Fase 4I-B: demora propia (antes `retardo` de desvanecer_entrada, que podía cruzarse con
        # la salida de una tarea breve y dejar el velo visible).
        self._aparicion = QTimer(self)
        self._aparicion.setSingleShot(True)
        self._aparicion.setInterval(400)
        self._aparicion.timeout.connect(lambda: desvanecer_entrada(self, duracion=tokens.DURACION_RAPIDA))

        aplicar_elevacion(self.panel, tokens.ELEVACION_3, tema)
        fila.addWidget(self.panel)
        fila.addStretch(1)
        layout.addLayout(fila)
        layout.addStretch(1)
        self.hide()

    def actualizar_tema(self, tema: str | None) -> None:
        aplicar_elevacion(self.panel, tokens.ELEVACION_3, tema)

    def mostrar(
        self,
        mensaje: str = "Procesando…",
        detalle: str = "",
        al_cancelar: Callable[[], None] | None = None,
    ) -> None:
        # `detalle` se acepta por compatibilidad con los llamadores, pero ya no se muestra (Fase 4I-C).
        self.etiqueta.setText(mensaje)
        self._reloj.start()
        self._activo = True;self._real = False
        self.barra.setRange(0, ESCALA);self.barra.setValue(0)
        self._animacion.start()
        self._al_cancelar = al_cancelar
        self.boton_cancelar.setVisible(al_cancelar is not None)
        self.setGeometry(self._contenedor.rect())
        self.raise_()
        # Lectores de pantalla: se anuncia el cambio de estado.
        self.setAccessibleName(f"Procesando: {mensaje}")
        # El velo bloquea clics desde el inicio (evita dobles ejecuciones), pero se hace
        # perceptible tras ~0,4 s: las tareas breves no producen un destello.
        efecto = QGraphicsOpacityEffect(self);efecto.setOpacity(0.0);self.setGraphicsEffect(efecto)
        self.show()
        self._aparicion.start()

    def _avanzar(self) -> None:
        if not self._real:
            # Monótona: nunca retrocede ni llega al 100 % antes de ocultar(exito=True).
            self.barra.setValue(max(self.barra.value(), round(progreso_estimado(self._reloj.elapsed() / 1000) * ESCALA / 100)))

    def actualizar_mensaje(self, mensaje: str, detalle: str = "") -> None:
        self.etiqueta.setText(mensaje)  # solo el título; `detalle` no se muestra (Fase 4I-C)

    def establecer_progreso(self, valor: int | None, maximo: int = 100) -> None:
        """Progreso MEDIDO por el llamador; `None` vuelve al progreso visual estimado."""
        if valor is None:
            self._real = False
            self.barra.setRange(0, ESCALA)
            return
        self._real = True
        self.barra.setRange(0, int(maximo))
        self.barra.setValue(int(valor))

    def ocultar(self, exito: bool = True) -> None:
        """Retira el velo. Con éxito real la barra pasa a 100 % durante el desvanecimiento;
        ante error o cancelación se retira sin completarse. Idempotente."""
        if not self._activo:
            return
        self._activo = False
        self._animacion.stop()
        self._al_cancelar = None
        if self._aparicion.isActive():  # tarea breve: nunca llegó a verse; se retira sin animación
            self._aparicion.stop();self.hide();self.setGraphicsEffect(None)
            return
        if exito and not self._real:
            self.barra.setValue(ESCALA)
        desvanecer_salida(self, duracion=tokens.DURACION_RAPIDA)

    def reposicionar(self) -> None:
        if self.isVisible():
            self.setGeometry(self._contenedor.rect())

    def _cancelar(self) -> None:
        if self._al_cancelar is not None:
            self.boton_cancelar.setEnabled(False)
            self.etiqueta.setText("Cancelando…")
            self._al_cancelar()


__all__ = ["VeloCarga"]
