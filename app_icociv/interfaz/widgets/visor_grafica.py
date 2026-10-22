"""Visor interactivo de la gráfica de serie y proyección ICOCIV.

Agrega zoom (rueda del mouse y botones), desplazamiento (arrastre) y recálculo
dinámico de los ticks de ambos ejes. La interacción sólo modifica los límites de
los ejes y redibuja el lienzo: nunca vuelve a ejecutar la proyección ni ningún
cálculo estadístico.

El eje X es categórico (índices enteros 0..n-1 que representan periodos
mensuales), por eso se usa un localizador propio que traduce el rango visible a
índices de periodo. El eje Y usa el localizador automático de Matplotlib.
"""

from __future__ import annotations

import math

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.ticker import FuncFormatter, Locator, MaxNLocator
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QStyle,
    QVBoxLayout,
)


# Máximo de etiquetas simultáneas en el eje X para evitar superposición.
MAX_TICKS_X = 12
# Factor de zoom por muesca de rueda o pulsación de botón.
FACTOR_ZOOM = 1.25
# Amplitud mínima del eje X en índices de periodo (evita zoom infinito).
SPAN_MINIMO_X = 2.0
# Fracción mínima del rango original permitida en el eje Y.
FRACCION_MINIMA_Y = 0.005


class LocalizadorPeriodos(Locator):
    """Localizador de ticks para un eje X de periodos mensuales categóricos.

    Según el nivel de zoom escoge, en orden:
      1. todos los meses visibles (zoom alto);
      2. sólo inicios y finales de año (enero y diciembre);
      3. sólo inicios de año (enero);
      4. eneros espaciados, o un muestreo uniforme si no hay eneros.
    """

    def __init__(self, periodos: list[str], max_ticks: int = MAX_TICKS_X) -> None:
        self.periodos = list(periodos)
        self.max_ticks = max(2, int(max_ticks))
        self._meses = [_mes_de_periodo(p) for p in self.periodos]

    def __call__(self) -> list[float]:
        vmin, vmax = self.axis.get_view_interval()
        eje = self.axis.axes
        renderer = eje.figure._get_renderer()
        etiqueta = self.axis.get_major_ticks(1)[0].label1
        angulo = math.radians(etiqueta.get_rotation())
        seleccionados = []
        derecha = -math.inf
        for tick in self.tick_values(vmin, vmax):
            if not min(vmin, vmax) <= tick <= max(vmin, vmax):
                continue
            texto = self.axis.get_major_formatter()(tick)
            ancho, alto, _ = renderer.get_text_width_height_descent(texto, etiqueta.get_fontproperties(), False)
            mitad = (abs(ancho * math.cos(angulo)) + abs(alto * math.sin(angulo))) / 2
            x = eje.transData.transform((tick, 0))[0]
            if x - mitad >= derecha + 12:
                seleccionados.append(tick)
                derecha = x + mitad
        return seleccionados

    def tick_values(self, vmin: float, vmax: float) -> list[float]:
        total = len(self.periodos)
        if total == 0:
            return []
        if vmin > vmax:
            vmin, vmax = vmax, vmin
        inicio = max(0, int(math.floor(vmin)))
        fin = min(total - 1, int(math.ceil(vmax)))
        if fin < inicio:
            return []
        visibles = list(range(inicio, fin + 1))

        # 1. Zoom alto: cabe un tick por mes.
        if len(visibles) <= self.max_ticks:
            return [float(i) for i in visibles]

        # 2/3. Priorizar inicios y finales de año.
        for meses_clave in ((1, 12), (1,)):
            candidatos = [i for i in visibles if self._meses[i] in meses_clave]
            if candidatos and len(candidatos) <= self.max_ticks:
                return [float(i) for i in candidatos]

        # 4. Demasiados años visibles: espaciar los eneros.
        eneros = [i for i in visibles if self._meses[i] == 1]
        base = eneros or visibles
        paso = max(1, math.ceil(len(base) / self.max_ticks))
        return [float(i) for i in base[::paso]]


def _mes_de_periodo(periodo: str) -> int:
    """Extrae el mes de una etiqueta 'AAAA-MM'; 0 si no es reconocible."""
    partes = str(periodo).replace("_", "-").split("-")
    if len(partes) >= 2 and partes[1].isdigit():
        return int(partes[1])
    return 0


def configurar_ejes_dinamicos(eje, etiquetas: list[str]) -> None:
    """Instala localizadores/formateadores que se recalculan al hacer zoom.

    Sustituye los ticks fijos por un localizador dinámico: Matplotlib vuelve a
    consultar el localizador en cada redibujado con el rango visible actual, de
    modo que los ticks se ajustan solos al nivel de zoom.
    """
    eje.xaxis.set_major_locator(LocalizadorPeriodos(etiquetas))
    eje.xaxis.set_major_formatter(FuncFormatter(_formatear_periodo(etiquetas)))
    # El eje Y conserva el localizador automático: al reducir el rango visible
    # genera divisiones más finas y al ampliarlo vuelve a divisiones amplias.
    eje.yaxis.set_major_locator(MaxNLocator(nbins="auto", min_n_ticks=3))
    # La rotación se fija en el eje (no en las etiquetas) para que sobreviva a
    # cada recálculo de ticks.
    eje.tick_params(axis="x", labelrotation=30)


def _formatear_periodo(etiquetas: list[str]):
    """Devuelve un formateador índice -> 'AAAA-MM'."""

    def formato(valor: float, _posicion: int) -> str:
        indice = int(round(valor))
        if 0 <= indice < len(etiquetas):
            return etiquetas[indice]
        return ""

    return formato


MESES = ("Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre",
         "Octubre", "Noviembre", "Diciembre")
# Fase 4I-C: rótulo mostrado por curva (las demás conservan su nombre real de leyenda).
TIPOS_CURVA = {"Serie observada": "Histórico observado", "Proyección": "Proyección (estimación puntual)"}
PRIORIDAD_CURVA = {"Serie observada": 0, "Proyección": 1}
UMBRAL_CLIC_PX = 12  # a 100 dpi; se escala con el dpi de la figura


def mes_legible(periodo: str) -> str:
    """'2027-07' / '2027_7' → 'Julio de 2027'; si no se reconoce, devuelve el texto tal cual."""
    partes = str(periodo).replace("_", "-").split("-")
    if len(partes) >= 2 and partes[0].isdigit() and partes[1].isdigit() and 1 <= int(partes[1]) <= 12:
        return f"{MESES[int(partes[1]) - 1]} de {partes[0]}"
    return str(periodo)


def texto_punto_proyectado(periodo: str, valor: float, detalle: dict) -> str:
    """Fase 4I-P: etiqueta de un punto proyectado con su H, I(h) y la referencia I(h) ± MAE(h).

    MAE(h) es el error absoluto medio histórico (fuera de muestra) de ESE horizonte en la ejecución que originó
    la trayectoria; la referencia no es un intervalo de confianza ni tiene cobertura garantizada.
    """
    iso = str(periodo).replace("_", "-")
    partes = iso.split("-")
    iso = f"{int(partes[0]):04d}-{int(partes[1]):02d}" if len(partes) >= 2 and all(p.isdigit() for p in partes[:2]) else iso
    lineas = [f"{mes_legible(periodo)} ({iso}) · H={detalle['horizonte']}",
              f"{TIPOS_CURVA['Proyección']} · I(h): {valor:,.3f}"]
    mae = detalle.get("mae")
    if mae is None:
        lineas.append("MAE histórico por horizonte no disponible")
    else:
        lineas += [f"MAE histórico H{detalle['horizonte']}: {mae:,.3f}",
                   f"Referencia ±MAE: {detalle['inferior']:,.3f} a {detalle['superior']:,.3f}",
                   "(error histórico; no es intervalo de confianza)"]
    return "\n".join(lineas)


class VisorGraficaDialog(QDialog):
    """Ventana emergente con la gráfica y controles de zoom/desplazamiento."""

    def __init__(self, parent, figura, titulo: str, hoja_estilo: str = "", subtitulo: str = "") -> None:
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setModal(True)
        self.resize(900, 640)
        self.setMinimumSize(560, 420)
        if hoja_estilo:
            self.setStyleSheet(hoja_estilo)

        self.figura = figura
        figura.set_layout_engine("tight")
        self.eje = figura.axes[0] if figura.axes else None
        self.canvas = FigureCanvas(figura)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.canvas.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.canvas.setCursor(Qt.CursorShape.OpenHandCursor)

        # Límites originales: sirven de tope al alejar y al desplazarse.
        self._limites_base = self._leer_limites()
        self._panorama_activo = False
        self._inicio_clic = None
        self._anotacion = None  # Fase 4I-C: una sola etiqueta de dato, reutilizada

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        if subtitulo:
            etiqueta = QLabel(subtitulo)
            etiqueta.setWordWrap(True)
            etiqueta.setObjectName("ruta_dashboard")
            layout.addWidget(etiqueta)

        layout.addWidget(self.canvas, 1)

        controles = QHBoxLayout()
        ayuda = QLabel("Rueda del mouse: zoom · Arrastrar: desplazar")
        ayuda.setObjectName("ruta_dashboard")
        controles.addWidget(ayuda)
        controles.addStretch()
        self.boton_alejar = self._boton_zoom("−", "Alejar (Zoom Out)", self.alejar)
        self.boton_acercar = self._boton_zoom("+", "Acercar (Zoom In)", self.acercar)
        self.boton_restablecer = self._boton_zoom("⟲", "Restablecer vista completa", self.restablecer_vista)
        for boton in (self.boton_alejar, self.boton_acercar, self.boton_restablecer):
            controles.addWidget(boton)
        boton_cerrar = QPushButton("Cerrar")
        boton_cerrar.setObjectName("boton_cerrar_dialogo")
        boton_cerrar.clicked.connect(self.accept)
        controles.addWidget(boton_cerrar)
        layout.addLayout(controles)

        # Eventos nativos de Matplotlib (sin librerías externas).
        self._conexiones = [
            self.canvas.mpl_connect("scroll_event", self._al_desplazar_rueda),
            self.canvas.mpl_connect("button_press_event", self._al_presionar),
            self.canvas.mpl_connect("motion_notify_event", self._al_mover),
            self.canvas.mpl_connect("button_release_event", self._al_soltar),
        ]

    # ------------------------------------------------------------ controles
    @staticmethod
    def _boton_zoom(texto: str, ayuda: str, accion) -> QPushButton:
        boton = QPushButton(texto)
        boton.setObjectName("boton_zoom")
        boton.setToolTip(ayuda)
        boton.setAccessibleName(ayuda)
        if texto == "⟲":
            boton.setText("")
            boton.setIcon(boton.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        boton.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        boton.clicked.connect(accion)
        return boton

    def acercar(self) -> None:
        """Zoom in centrado en la vista actual (mismo efecto que la rueda)."""
        self._aplicar_zoom(1.0 / FACTOR_ZOOM)

    def alejar(self) -> None:
        """Zoom out centrado en la vista actual (mismo efecto que la rueda)."""
        self._aplicar_zoom(FACTOR_ZOOM)

    def restablecer_vista(self) -> None:
        """Vuelve a los límites originales calculados al dibujar la serie."""
        if self.eje is None or self._limites_base is None:
            return
        (x0, x1), (y0, y1) = self._limites_base
        self.eje.set_xlim(x0, x1)
        self.eje.set_ylim(y0, y1)
        self.canvas.draw_idle()

    # -------------------------------------------------------------- eventos
    def _al_desplazar_rueda(self, evento) -> None:
        """Zoom respecto al cursor: hacia adelante acerca, hacia atrás aleja."""
        if self.eje is None or evento.inaxes is not self.eje:
            return
        pasos = evento.step if evento.step else (1 if evento.button == "up" else -1)
        escala = FACTOR_ZOOM ** (-pasos)
        self._aplicar_zoom(escala, evento.xdata, evento.ydata)

    def _al_presionar(self, evento) -> None:
        """Inicia el desplazamiento con el botón izquierdo o el central."""
        if self.eje is None or evento.inaxes is not self.eje:
            return
        if evento.button not in (1, 2):
            return
        # start_pan/drag_pan/end_pan son la API nativa que usa la barra de
        # navegación de Matplotlib; maneja correctamente la transformación.
        self._inicio_clic = (evento.x, evento.y) if evento.button == 1 else None
        self.eje.start_pan(evento.x, evento.y, evento.button)
        self._panorama_activo = True
        self.canvas.setCursor(Qt.CursorShape.ClosedHandCursor)

    def _al_mover(self, evento) -> None:
        if not self._panorama_activo or self.eje is None:
            return
        self.eje.drag_pan(1, evento.key, evento.x, evento.y)
        self._ajustar_a_limites()
        self.canvas.draw_idle()

    def _al_soltar(self, evento) -> None:
        if not self._panorama_activo or self.eje is None:
            return
        self.eje.end_pan()
        self._panorama_activo = False
        self.canvas.setCursor(Qt.CursorShape.OpenHandCursor)
        # Un clic sin arrastre (< 4 px) consulta el dato; arrastrar sigue desplazando la vista.
        if self._inicio_clic is not None and getattr(evento, "x", None) is not None and math.hypot(evento.x - self._inicio_clic[0], evento.y - self._inicio_clic[1]) < 4:
            self.inspeccionar(evento.x, evento.y)
        self._inicio_clic = None

    # ------------------------------------------------------ inspección de datos
    def punto_mas_cercano(self, x_px: float, y_px: float):
        """Punto REAL dibujado más cercano al clic (en píxeles) o ``None``.

        Devuelve (curva, periodo, valor, x, y). Solo considera vértices de las curvas con leyenda
        (no interpola meses) y exige un umbral en píxeles escalado por dpi.
        """
        if self.eje is None:
            return None
        localizador = self.eje.xaxis.get_major_locator()
        periodos = getattr(localizador, "periodos", None) or []
        umbral = UMBRAL_CLIC_PX * self.figura.dpi / 100
        candidatos = []
        for linea in self.eje.get_lines():
            nombre = linea.get_label()
            if not nombre or nombre.startswith("_") or not linea.get_visible():
                continue
            for x, y in zip(linea.get_xdata(), linea.get_ydata()):
                try:
                    x, y = float(x), float(y)
                except (TypeError, ValueError):
                    continue
                if not (math.isfinite(x) and math.isfinite(y)) or abs(x - round(x)) > 1e-9 or not 0 <= round(x) < len(periodos):
                    continue
                px, py = self.eje.transData.transform((x, y))
                distancia = math.hypot(px - x_px, py - y_px)
                if distancia <= umbral:
                    prioridad = PRIORIDAD_CURVA.get(nombre, 2)
                    # Los datos (observado/proyección) prevalecen sobre curvas auxiliares como el ajuste.
                    candidatos.append((prioridad >= 2, round(distancia), prioridad, distancia, nombre, periodos[round(x)], y, x))
        if not candidatos:
            return None
        *_, nombre, periodo, valor, x = min(candidatos)
        return nombre, periodo, valor, x, valor

    def inspeccionar(self, x_px: float, y_px: float) -> bool:
        """Muestra/mueve la etiqueta del punto; un clic en zona vacía la oculta. No recalcula nada."""
        punto = self.punto_mas_cercano(x_px, y_px)
        if punto is None:
            self.ocultar_anotacion()
            return False
        nombre, periodo, valor, x, y = punto
        texto = f"{mes_legible(periodo)}\n{TIPOS_CURVA.get(nombre, nombre)} · ICOCIV: {valor:,.3f}"
        detalle = (getattr(self.figura, "savip_detalle_proyeccion", None) or {}).get(int(round(x))) if nombre == "Proyección" else None
        if detalle:
            texto = texto_punto_proyectado(periodo, valor, detalle)
        oscuro = sum(self.figura.get_facecolor()[:3]) / 3 < 0.5
        fondo, borde, letra = ("#2B3644", "#566477", "#E7ECF2") if oscuro else ("#F5F7FA", "#C3CCD6", "#1E2A36")
        if self._anotacion is None:
            self._anotacion = self.eje.annotate(
                "", (0, 0), xytext=(16, 16), textcoords="offset points", fontsize=9, zorder=10,
                bbox={"boxstyle": "round,pad=0.45,rounding_size=0.3", "linewidth": 0.8},
                arrowprops={"arrowstyle": "-", "linewidth": 0.8, "shrinkA": 0, "shrinkB": 5})
        a = self._anotacion
        # Se coloca hacia dentro del lienzo para no salirse ni tapar el marcador.
        caja = self.eje.get_window_extent()
        px, py = self.eje.transData.transform((x, y))
        derecha, arriba = px > (caja.x0 + caja.x1) / 2, py > (caja.y0 + caja.y1) / 2
        a.xy = (x, y)
        a.set_text(texto)
        a.set_position((-16 if derecha else 16, -16 if arriba else 16))
        a.set_ha("right" if derecha else "left");a.set_va("top" if arriba else "bottom")
        a.set_color(letra);a.get_bbox_patch().set_facecolor(fondo);a.get_bbox_patch().set_edgecolor(borde)
        a.arrow_patch.set_color(borde)
        a.set_visible(True)
        self.canvas.draw_idle()
        return True

    def ocultar_anotacion(self) -> None:
        if self._anotacion is not None and self._anotacion.get_visible():
            self._anotacion.set_visible(False)
            self.canvas.draw_idle()

    def keyPressEvent(self, evento) -> None:  # noqa: N802 - firma Qt
        # Esc retira primero la etiqueta; con la etiqueta oculta, Esc cierra el visor como siempre.
        if evento.key() == Qt.Key.Key_Escape and self._anotacion is not None and self._anotacion.get_visible():
            self.ocultar_anotacion();evento.accept();return
        super().keyPressEvent(evento)

    # --------------------------------------------------------------- zoom
    def _aplicar_zoom(self, escala: float, x_centro=None, y_centro=None) -> None:
        """Escala los límites alrededor de un punto y redibuja.

        ``escala`` < 1 acerca y ``escala`` > 1 aleja. Si no se indica un punto,
        se usa el centro de la vista actual (caso de los botones).
        """
        if self.eje is None:
            return
        x0, x1 = self.eje.get_xlim()
        y0, y1 = self.eje.get_ylim()
        if x_centro is None:
            x_centro = (x0 + x1) / 2.0
        if y_centro is None:
            y_centro = (y0 + y1) / 2.0

        nuevo_x = (x_centro - (x_centro - x0) * escala, x_centro + (x1 - x_centro) * escala)
        nuevo_y = (y_centro - (y_centro - y0) * escala, y_centro + (y1 - y_centro) * escala)
        self.eje.set_xlim(*self._acotar(nuevo_x, self._limites_base[0], SPAN_MINIMO_X))
        self.eje.set_ylim(*self._acotar(nuevo_y, self._limites_base[1], None))
        self.canvas.draw_idle()

    def _ajustar_a_limites(self) -> None:
        """Impide que el desplazamiento salga del rango de datos."""
        self.eje.set_xlim(*self._acotar(self.eje.get_xlim(), self._limites_base[0], SPAN_MINIMO_X))
        self.eje.set_ylim(*self._acotar(self.eje.get_ylim(), self._limites_base[1], None))

    @staticmethod
    def _acotar(rango, base, span_minimo) -> tuple[float, float]:
        """Recorta un rango para que quepa dentro del rango base."""
        lo, hi = float(rango[0]), float(rango[1])
        base_lo, base_hi = float(base[0]), float(base[1])
        span_base = base_hi - base_lo
        if span_base <= 0:
            return base_lo, base_hi
        minimo = span_minimo if span_minimo is not None else span_base * FRACCION_MINIMA_Y

        span = hi - lo
        if span >= span_base:  # no alejar más allá de los datos
            return base_lo, base_hi
        if span < minimo:  # no acercar indefinidamente
            centro = (lo + hi) / 2.0
            lo, hi = centro - minimo / 2.0, centro + minimo / 2.0
        if lo < base_lo:
            hi += base_lo - lo
            lo = base_lo
        if hi > base_hi:
            lo -= hi - base_hi
            hi = base_hi
        return max(lo, base_lo), min(hi, base_hi)

    def _leer_limites(self):
        if self.eje is None:
            return ((0.0, 1.0), (0.0, 1.0))
        return (tuple(self.eje.get_xlim()), tuple(self.eje.get_ylim()))


if __name__ == "__main__":
    # Comprobación del localizador dinámico en distintos niveles de zoom.
    periodos = [f"{2021 + i // 12:04d}-{i % 12 + 1:02d}" for i in range(61)]
    localizador = LocalizadorPeriodos(periodos)

    # Zoom alto (8 meses visibles): un tick por mes.
    ticks = localizador.tick_values(10, 17)
    assert ticks == [float(i) for i in range(10, 18)], ticks

    # Zoom medio (2 años): inicios y finales de año.
    ticks = [int(t) for t in localizador.tick_values(0, 24)]
    assert all(_mes_de_periodo(periodos[i]) in (1, 12) for i in ticks), ticks
    assert len(ticks) <= MAX_TICKS_X

    # Vista completa (61 meses): inicios y finales de año, sin superposición.
    ticks = [int(t) for t in localizador.tick_values(0, 60)]
    assert all(_mes_de_periodo(periodos[i]) in (1, 12) for i in ticks), ticks
    assert len(ticks) <= MAX_TICKS_X, ticks

    # 8 años: enero+diciembre ya no cabe, se conservan sólo los eneros.
    ocho = [f"{2010 + i // 12:04d}-{i % 12 + 1:02d}" for i in range(12 * 8)]
    ticks = [int(t) for t in LocalizadorPeriodos(ocho).tick_values(0, len(ocho) - 1)]
    assert all(_mes_de_periodo(ocho[i]) == 1 for i in ticks), ticks
    assert len(ticks) <= MAX_TICKS_X, ticks

    # Rango muy amplio: se espacian los eneros sin exceder el máximo.
    largos = [f"{2000 + i // 12:04d}-{i % 12 + 1:02d}" for i in range(12 * 40)]
    ticks = LocalizadorPeriodos(largos).tick_values(0, len(largos) - 1)
    assert len(ticks) <= MAX_TICKS_X, len(ticks)

    # Fuera de rango y rangos invertidos no rompen.
    assert localizador.tick_values(-50, -10) == []
    assert localizador.tick_values(30, 20) == localizador.tick_values(20, 30)

    # Acotado: no aleja más allá de los datos ni acerca sin límite.
    assert VisorGraficaDialog._acotar((-5.0, 100.0), (0.0, 60.0), 2.0) == (0.0, 60.0)
    lo, hi = VisorGraficaDialog._acotar((10.0, 10.2), (0.0, 60.0), 2.0)
    assert math.isclose(hi - lo, 2.0), (lo, hi)
    lo, hi = VisorGraficaDialog._acotar((-3.0, 7.0), (0.0, 60.0), 2.0)
    assert (lo, hi) == (0.0, 10.0), (lo, hi)
    print("OK visor_grafica")
