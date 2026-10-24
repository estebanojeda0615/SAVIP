"""Indicador de trabajo en curso, superpuesto al área de contenido.

Las operaciones largas ya se ejecutan en un hilo (`TrabajadorFuncion`), de modo que la ventana nunca
se congela; este velo cubre solo el área de trabajo (la navegación lateral y la cabecera quedan a la
vista) y bloquea sus clics para impedir dobles ejecuciones.

Fase V1.1.2-01: el velo tiene dos aspectos.

* **Esqueleto** (``esqueleto="anexo" | "resultados" | "sesion"``): cuando la operación prepara
  contenido nuevo, el área muestra la silueta de ese contenido y una franja superior con la etapa.
  El contenido anterior queda oculto: no se presenta información desactualizada como nueva.
* **Panel** (sin esqueleto): para operaciones que no cambian lo que se ve (exportar un informe), un
  cuadro compacto con la etapa sobre el contenido atenuado.

En ambos, la barra es indeterminada salvo que el llamador informe avance medido con
`establecer_progreso`. Se retiró el «progreso visual estimado» (Fases 4I-B/4I-C), que simulaba un
porcentaje sin medirlo.

Fase V1.1.2-01B (sesiones): con ``inmediato=True`` la franja se ve desde el primer instante, sobre el
contenido intacto (fondo transparente que igualmente bloquea los clics); el esqueleto pedido sustituye
al contenido solo si la operación supera los 0,4 s. `pintar_ahora()` lleva ese estado a la pantalla antes
de un tramo síncrono del hilo de la interfaz, durante el cual ningún temporizador tendría turno.
"""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QElapsedTimer, QEasingCurve, QPropertyAnimation, Qt, QTimer
from PySide6.QtWidgets import QFrame, QGraphicsOpacityEffect, QHBoxLayout, QVBoxLayout, QWidget

from app_icociv.interfaz.animaciones.microinteracciones import aplicar_elevacion
from app_icociv.interfaz.animaciones.transiciones import movimiento_reducido
from app_icociv.interfaz.componentes.esqueleto import VARIANTES, EsqueletoContenido, FranjaProgreso
from app_icociv.interfaz.tema import tokens

INTERVALO_ANIMACION = 33  # ms (~30 fps); solo mientras el velo es visible
CICLO_BRILLO = 1.6  # s por pasada del brillo del esqueleto
CICLO_FRANJA = 1.4  # s por pasada del segmento indeterminado


class VeloCarga(QFrame):
    """Superposición con la etapa en curso y, si procede, el esqueleto del contenido esperado."""

    def __init__(self, contenedor: QWidget, tema: str | None = "claro") -> None:
        super().__init__(contenedor)
        self.setObjectName("velo_carga")
        self.setProperty("modo", "panel")
        self._contenedor = contenedor
        self._al_cancelar: Callable[[], None] | None = None
        # Sin esto el velo no bloquearía los clics sobre los controles de abajo.
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.franja = FranjaProgreso(tema=tema)
        self.etiqueta = self.franja.etiqueta
        self.boton_cancelar = self.franja.boton_cancelar
        self.boton_cancelar.clicked.connect(self._cancelar)
        self.esqueleto = EsqueletoContenido(tema=tema)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        # Aspecto «panel»: cuadro centrado que se estrecha con la ventana.
        self.panel = QFrame()
        self.panel.setObjectName("panel_carga")
        self.panel.setMaximumWidth(520)
        self._layout_panel = QVBoxLayout(self.panel)
        self._layout_panel.setContentsMargins(tokens.ESPACIO_2, tokens.ESPACIO_3, tokens.ESPACIO_2, tokens.ESPACIO_3)
        self._fila_panel = QHBoxLayout()
        self._fila_panel.setContentsMargins(tokens.ESPACIO_5, 0, tokens.ESPACIO_5, 0)
        self._fila_panel.addStretch(1); self._fila_panel.addWidget(self.panel, 4); self._fila_panel.addStretch(1)
        aplicar_elevacion(self.panel, tokens.ELEVACION_3, tema)

        self._animacion = QTimer(self)
        self._animacion.setInterval(INTERVALO_ANIMACION)
        self._animacion.timeout.connect(self._avanzar)
        self._activo = False
        # Fase 4I-B: demora propia. El velo bloquea clics desde el inicio, pero solo se hace
        # perceptible tras ~0,4 s: las tareas breves no producen un destello.
        self._aparicion = QTimer(self)
        self._aparicion.setSingleShot(True)
        self._aparicion.setInterval(400)
        self._aparicion.timeout.connect(self._aparecer)
        self._reloj = QElapsedTimer()
        self._pendiente: str | None = None  # esqueleto que espera los 0,4 s tras una franja inmediata
        # Un único fundido reutilizable: los ayudantes genéricos de transiciones crean una animación
        # nueva por llamada que queda viva como hija del widget (acumulaba 2 por cada carga).
        self._fundido = QPropertyAnimation(self)
        self._fundido.setPropertyName(b"opacity")
        self._fundido.setDuration(tokens.DURACION_RAPIDA)
        self._fundido.finished.connect(self._fin_fundido)
        self._hacia = 1.0
        self._montar(None)
        self.hide()

    # -------------------------------------------------------------- aspecto
    def _montar(self, esqueleto: str | None, solo_franja: bool = False) -> None:
        """Coloca la franja en el panel centrado, sola arriba (`solo_franja`) o sobre el esqueleto."""
        while self._layout.count():
            self._layout.takeAt(0)
        self._layout_panel.removeWidget(self.franja)
        if solo_franja:
            self.setProperty("modo", "franja")
            self.panel.hide(); self.esqueleto.hide()
            self._layout.addWidget(self.franja); self._layout.addStretch(1)
        elif esqueleto is None:
            self.setProperty("modo", "panel")
            self.esqueleto.hide()
            self._layout_panel.addWidget(self.franja)
            self._layout.addStretch(1); self._layout.addLayout(self._fila_panel); self._layout.addStretch(1)
            self.panel.show()
        else:
            self.setProperty("modo", "esqueleto")
            self.panel.hide()
            self.esqueleto.establecer_variante(esqueleto)
            self._layout.addWidget(self.franja); self._layout.addWidget(self.esqueleto, 1)
            self.esqueleto.show()
        self.franja.show()
        self.style().unpolish(self); self.style().polish(self)

    def actualizar_tema(self, tema: str | None) -> None:
        aplicar_elevacion(self.panel, tokens.ELEVACION_3, tema)
        self.franja.actualizar_tema(tema)
        self.esqueleto.actualizar_tema(tema)

    # -------------------------------------------------------------- ciclo
    def mostrar(
        self,
        mensaje: str = "Procesando…",
        detalle: str = "",
        al_cancelar: Callable[[], None] | None = None,
        esqueleto: str | None = None,
        inmediato: bool = False,
    ) -> None:
        # `detalle` se acepta por compatibilidad con los llamadores, pero no se muestra (Fase 4I-C).
        esqueleto = esqueleto if esqueleto in VARIANTES else None
        self._pendiente = esqueleto if inmediato else None
        self._montar(esqueleto, solo_franja=inmediato)
        self.franja.establecer_progreso(None)
        self.franja.establecer_texto(mensaje)
        self._activo = True
        self._al_cancelar = al_cancelar
        self.boton_cancelar.setEnabled(True)
        self.boton_cancelar.setVisible(al_cancelar is not None)
        self.setGeometry(self._contenedor.rect())
        self.raise_()
        self.setAccessibleName(f"Procesando: {mensaje}")
        self._fundido.stop()  # una salida en curso no debe actuar sobre esta operación
        self._reloj.start()
        if inmediato:  # Fase 01B: la franja se ve ya; solo el esqueleto espera el umbral
            self.setGraphicsEffect(None)
            self.show()
            if not movimiento_reducido():
                self._animacion.start()
            if self._pendiente:
                self._aparicion.start()
            return
        efecto = QGraphicsOpacityEffect(self); efecto.setOpacity(0.0); self.setGraphicsEffect(efecto)
        self.show()
        self._aparicion.start()

    def _aparecer(self) -> None:
        if not self._activo:
            return
        if self.property("modo") == "franja":  # franja ya visible: el esqueleto entra sin fundido
            self._montar(self._pendiente)
            return
        if not movimiento_reducido():
            self._animacion.start()
        self._fundir(1.0)

    def _fundir(self, hacia: float) -> None:
        """Entrada (1.0) o salida (0.0) con el fundido reutilizable; inmediata con movimiento reducido."""
        self._hacia = hacia
        self._fundido.stop()
        if movimiento_reducido():
            self._fin_fundido()
            return
        efecto = self.graphicsEffect()
        if not isinstance(efecto, QGraphicsOpacityEffect):
            efecto = QGraphicsOpacityEffect(self); efecto.setOpacity(1.0 - hacia); self.setGraphicsEffect(efecto)
        self._fundido.setTargetObject(efecto)
        self._fundido.setStartValue(efecto.opacity()); self._fundido.setEndValue(hacia)
        self._fundido.setEasingCurve(QEasingCurve.Type.OutCubic if hacia else QEasingCurve.Type.InCubic)
        self._fundido.start()

    def _fin_fundido(self) -> None:
        # El efecto se retira al terminar: mantenerlo penaliza el repintado del esqueleto animado.
        if self._hacia >= 1.0:
            self.setGraphicsEffect(None)
        elif not self._activo:  # no oculta un velo que otra operación haya vuelto a mostrar
            self.hide(); self.setGraphicsEffect(None)

    def _avanzar(self) -> None:
        paso = INTERVALO_ANIMACION / 1000
        self.franja.avanzar(paso / CICLO_FRANJA)
        if self.esqueleto.isVisible():
            self.esqueleto.avanzar(paso / CICLO_BRILLO)

    def pintar_ahora(self, largo: bool = False) -> None:
        """Antes de un tramo síncrono del hilo de la interfaz: aplica la aparición si ya venció su plazo
        —o si el llamador sabe que el tramo será `largo`— sin fundido (no habría bucle que lo animara) y
        pinta el estado en pantalla en este momento."""
        if not self._activo:
            return
        if self._aparicion.isActive() and (largo or self._reloj.elapsed() >= self._aparicion.interval()):
            self._aparicion.stop()
            if self.property("modo") == "franja":
                self._montar(self._pendiente)
            else:
                self._fundido.stop(); self.setGraphicsEffect(None)
                if not movimiento_reducido():
                    self._animacion.start()
        self._layout.activate()
        self.repaint()

    def actualizar_mensaje(self, mensaje: str, detalle: str = "") -> None:
        """Nueva etapa REAL de la misma operación (solo el título; `detalle` no se muestra)."""
        self.franja.establecer_texto(mensaje)
        self.setAccessibleName(f"Procesando: {mensaje}")

    def establecer_progreso(self, valor: int | None, maximo: int = 100) -> None:
        """Progreso MEDIDO por el llamador; `None` vuelve al indicador indeterminado."""
        self.franja.establecer_progreso(valor, maximo)

    def ocultar(self, exito: bool = True) -> None:
        """Retira el velo ante éxito, error o cancelación. Con progreso medido y éxito, la barra se
        completa durante el desvanecimiento; nunca se simula un 100 %. Idempotente."""
        if not self._activo:
            return
        self._activo = False
        self._animacion.stop()
        self._al_cancelar = None
        if self._aparicion.isActive():
            self._aparicion.stop()
            if self.property("modo") != "franja":  # tarea breve: nunca llegó a verse; se retira sin animación
                self.hide(); self.setGraphicsEffect(None)
                return
        if exito and not self.franja.indeterminada:
            self.franja.establecer_progreso(self.franja.maximo, self.franja.maximo)
        self._fundir(0.0)

    @property
    def activo(self) -> bool:
        return self._activo

    def animacion_activa(self) -> bool:
        """True si queda algún temporizador del velo en marcha (para comprobar la limpieza)."""
        return self._animacion.isActive() or self._aparicion.isActive()

    def reposicionar(self) -> None:
        if self.isVisible():
            self.setGeometry(self._contenedor.rect())

    def _cancelar(self) -> None:
        if self._al_cancelar is not None:
            self.boton_cancelar.setEnabled(False)
            self.franja.establecer_texto("Cancelando…")
            self._al_cancelar()


__all__ = ["VeloCarga"]
