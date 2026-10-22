"""Tooltips legibles (claro/oscuro) y modo compacto para pantalla dividida. Pruebas focalizadas Qt (offscreen)."""
import json
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QEvent, QPoint
from PySide6.QtGui import QFontDatabase, QHelpEvent, QPalette
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QScrollArea, QToolTip

from tests.test_slider_comparacion_historica_fase_4d import APP, cargar
from tests.test_proyecciones_redisenio_visual import ventana_de_prueba
from app_icociv.interfaz.tema.colores import paleta

for f in ("segoeui.ttf", "segoeuib.ttf", "seguisb.ttf"):
    QFontDatabase.addApplicationFont(str(Path("C:/Windows/Fonts") / f))


def _tip(objetivo, punto):
    QToolTip.hideText(); APP.processEvents()
    QApplication.sendEvent(objetivo, QHelpEvent(QEvent.Type.ToolTip, punto, objetivo.mapToGlobal(punto))); QTest.qWait(120)
    return next((w for w in QApplication.topLevelWidgets() if w.metaObject().className() == "QTipLabel" and w.isVisible()), None)


def test_tooltips_claros_en_tema_claro_suaves_en_oscuro_y_breves():
    v = ventana_de_prueba(); v.resize(1366, 768); v.show(); w = cargar(v)
    try:
        for tema in ("claro", "oscuro", "claro"):  # alternar sin reiniciar
            v._aplicar_tema(tema, persistir=False); v._cambiar_seccion(1); QTest.qWait(300)
            c = paleta(tema)
            assert QApplication.palette().color(QPalette.ToolTipBase).name().upper() == c["tooltip_fondo"]
            tip = _tip(w.precio_base, QPoint(20, 10))
            assert tip is not None
            fondo = tip.grab().toImage().pixelColor(4, tip.height() // 2).name().upper()
            assert fondo == c["tooltip_fondo"], (tema, fondo)
            if tema == "claro":
                assert QApplication.palette().color(QPalette.ToolTipBase).lightness() > 220  # nunca casi negro
            assert tip.width() <= 380  # ayuda larga con ajuste de línea, no una franja de media pantalla
        t = w.tabla_valores; m = w.modelo_valores
        indice = m.index(0, m.claves.index("factor")); t.scrollTo(indice); APP.processEvents()
        tip = _tip(t.viewport(), t.visualRect(indice).center())
        assert tip is not None and "ID:" not in tip.text() and "Análisis:" in tip.text()
        # El valor de la celda no cambia por la ayuda.
        assert m.data(indice) == f"{w.valores[0]['factor_icociv']:.6f}" or m.data(indice).replace(".", "").isdigit()
    finally:
        QToolTip.hideText(); v.close()


def test_tooltip_de_importe_breve_con_modalidad_declarada():
    from tests.test_fase_4i_d_legados_factor import sesion_legada
    w, _ = sesion_legada()
    try:
        m = w.modelo_valores
        texto = m.data(m.index(0, m.claves.index("valor_unitario")), 3)  # Qt.ToolTipRole
        assert texto.startswith("Importe declarado: $") and "Modalidad: Unitario" in texto and len(texto) < 70
    finally:
        w.close()


def _desborde(v):
    area = [a for a in v.tabs_principales.currentWidget().findChildren(QScrollArea) if a.isVisible()][0]
    return area.horizontalScrollBar().maximum()


def test_pantalla_dividida_ancho_estrecho_ancho_sin_perder_estado():
    v = ventana_de_prueba(); v.show(); w = cargar(v)
    try:
        assert v.minimumWidth() <= 683  # Snap al 50 % de 1366 y de 1920
        v.resize(1920, 1000); QTest.qWait(300); v._cambiar_seccion(1); QTest.qWait(300)
        w.item.setText("Borrador"); w._item_editado = True; w.cantidad.setValue(3); w.precio_base.setValue(123456.5); w.anticipo.setValue(1000)
        w.modalidad_importe.setCurrentIndex(w.modalidad_importe.findData("total"))
        w.selector_proyeccion_inferior.setCurrentIndex(2); APP.processEvents()
        estado = lambda: (json.dumps(w._datos_calculadora(), sort_keys=True, default=str), w._proyeccion_consulta,
                          w.selector_analisis_valores.currentIndex(), w.selector_proyeccion_inferior.currentIndex(),
                          w.solo_analisis_activo.isChecked(), [r["calculo_id"] for r in w.valores], w.analisis_activo_id)
        antes = estado(); aprobado = w.fila_calculo.direction()
        for _ in range(3):
            v.resize(960, 900); QTest.qWait(250)
            assert v.navegacion.esta_contraida() and w.fila_calculo.direction().name == "TopToBottom"
            assert _desborde(v) == 0 and estado() == antes
            v.resize(1920, 1000); QTest.qWait(250)
            assert not v.navegacion.esta_contraida() and w.fila_calculo.direction() == aprobado and estado() == antes
        # Navegación contraída a mano: ampliar no la expande sola.
        v.navegacion.establecer_contraccion(True); v.resize(960, 900); QTest.qWait(250); v.resize(1920, 1000); QTest.qWait(250)
        assert v.navegacion.esta_contraida()
        v.navegacion.establecer_contraccion(False)
        # Ancho intermedio dentro de la histéresis: no alterna en cada píxel.
        v.resize(1150, 900); QTest.qWait(250); assert v._modo_compacto
        v.resize(1220, 900); QTest.qWait(250); assert v._modo_compacto  # entre 1180 y 1260 conserva el modo
        v.resize(1300, 900); QTest.qWait(250); assert not v._modo_compacto
    finally:
        v.close()
