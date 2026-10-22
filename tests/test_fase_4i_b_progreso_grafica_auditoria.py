"""Fase 4I-B: progreso visual estimado, «Ver gráfica» sin salir de Proyecciones y barra de acciones única.

Pruebas focalizadas Qt (offscreen) con datos SINTÉTICOS; el motor estadístico queda bloqueado.
"""
import json
import os
from copy import deepcopy
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QScrollArea, QWidget

from tests.test_slider_comparacion_historica_fase_4d import APP, cargar
from tests.test_proyecciones_redisenio_visual import ventana_de_prueba
from app_icociv.interfaz.componentes import VeloCarga
from app_icociv.interfaz.componentes.carga import ESCALA, progreso_estimado
from app_icociv.interfaz.animaciones.transiciones import establecer_movimiento_reducido
from app_icociv.interfaz.widgets.visor_grafica import VisorGraficaDialog
from app_icociv.persistencia.historial_icociv import recuperar_resultado

MOTOR = "app_icociv.interfaz.controladores.controlador_principal.ControladorPrincipal.ejecutar_analisis"


class _Visor(VisorGraficaDialog):
    """Mismo visor; sin bucle modal en offscreen. Registra la figura abierta."""
    abiertos = []

    def exec(self):
        _Visor.abiertos.append(self)
        return 0


# ---------------------------------------------------------------- progreso
def test_P_curva_estimada_por_fases():
    assert progreso_estimado(0) == 0
    serie = [progreso_estimado(t / 10) for t in range(0, 600)]
    assert all(b >= a for a, b in zip(serie, serie[1:]))  # monótona
    assert 40 < progreso_estimado(1.5) < 85 and abs(progreso_estimado(4.0) - 85) < 1e-9
    assert progreso_estimado(4.2) == 85 == progreso_estimado(4.44)  # pausa visible en ~85 %
    assert 85 < progreso_estimado(10) < progreso_estimado(60) < 94  # lenta, sin llegar a 100
    assert progreso_estimado(3600) < 94.0001


def _velo():
    base = QWidget(); base.resize(500, 300); base.show()
    return base, VeloCarga(base)


def test_P1_P4_avanza_pausa_y_solo_completa_con_exito_real():
    establecer_movimiento_reducido(False)
    base, velo = _velo()
    try:
        velo.mostrar("Ejecutando proyección…")
        QTest.qWait(1200); temprano = velo.barra.value()
        assert 0 < temprano < 0.85 * ESCALA and velo.barra.maximum() == ESCALA
        QTest.qWait(3150); assert abs(velo.barra.value() - 0.85 * ESCALA) <= 5  # ~85 % y en pausa
        QTest.qWait(2500); tardio = velo.barra.value()
        assert 0.85 * ESCALA < tardio < 0.95 * ESCALA and velo.barra.value() < ESCALA  # sigue sin 100 %
        from PySide6.QtWidgets import QLabel
        assert [l.text() for l in velo.findChildren(QLabel) if l.isVisible()] == [velo.etiqueta.text()]  # Fase 4I-C: solo título y barra
        velo.ocultar(exito=True)
        assert velo.barra.value() == ESCALA  # 100 % solo al terminar de verdad
        QTest.qWait(300); assert not velo.isVisible() and not velo._animacion.isActive()
        velo.ocultar(exito=True)  # idempotente (p. ej. error + finished)
    finally:
        base.close()


def test_P2_P3_tarea_breve_sin_destello_y_error_sin_exito_falso():
    establecer_movimiento_reducido(False)
    base, velo = _velo()
    try:
        velo.mostrar("Cargando…"); QTest.qWait(150)
        assert velo.graphicsEffect().opacity() == 0.0  # < 400 ms: aún imperceptible
        velo.ocultar(); QTest.qWait(300); assert not velo.isVisible()
        velo.mostrar("Ejecutando…"); QTest.qWait(900); valor = velo.barra.value()
        velo.ocultar(exito=False)
        assert velo.barra.value() == valor < ESCALA  # error: no salta a 100 %
        QTest.qWait(300); assert not velo.isVisible() and not velo._animacion.isActive()
        velo.mostrar("Exportando…"); velo.establecer_progreso(40, 100)  # progreso MEDIDO: sin rótulo de estimado
        QTest.qWait(200); assert velo.barra.value() == 40
        velo.ocultar()
    finally:
        base.close()


def test_P3_ventana_error_real_retira_velo_sin_completar():
    v = ventana_de_prueba(); v.show()
    try:
        v._establecer_ocupado(True, "Ejecutando proyección…"); QTest.qWait(700)
        with patch.object(v, "notificaciones", None), patch("app_icociv.interfaz.ventana_principal.QMessageBox.critical"):
            v._mostrar_error("fallo simulado")
        assert v.velo_carga.barra.value() < ESCALA
        v._establecer_ocupado(False)  # «finished» posterior: no cambia nada
        QTest.qWait(300); assert not v.velo_carga.isVisible() and v.boton_cargar.isEnabled()
    finally:
        v.close()


# ---------------------------------------------------------------- gráfica en el mismo módulo
def _estado(v, w):
    return (v.tabs_principales.currentIndex(), json.dumps(w._datos_calculadora(), sort_keys=True, default=str),
            deepcopy(w.valores), w._ambito_consulta, w._proyeccion_consulta, w.analisis_activo_id,
            w.selector_ambito.currentIndex(), w.selector_proyeccion_inferior.currentIndex(), w.solo_analisis_activo.isChecked(),
            [i.row() for i in w.tabla_valores.selectionModel().selectedRows()],
            [a.verticalScrollBar().value() for a in w.findChildren(QScrollArea)])


def test_G1_G5_ver_grafica_sobre_proyecciones_por_analisis_id():
    v = ventana_de_prueba(); v.resize(1366, 768); v.show(); w = cargar(v); APP.processEvents()
    try:
        v._cambiar_seccion(1); APP.processEvents()
        w.item.setText("Borrador"); w._item_editado = True; w.cantidad.setValue(9)
        w._seleccionar_fila_valores(1)
        with patch(MOTOR, side_effect=AssertionError("motor")), \
             patch("app_icociv.interfaz.ventana_principal.VisorGraficaDialog", _Visor):
            w.selector_proyeccion_inferior.setCurrentIndex(0); APP.processEvents()
            assert not w.boton_grafica_inferior.isEnabled() and not w.boton_grafica_superior.isEnabled()  # G4
            for combo, boton, indice in ((w.selector_proyeccion_inferior, w.boton_grafica_inferior, 1),
                                         (w.selector_analisis_valores, w.boton_grafica_superior, 2)):
                combo.setCurrentIndex(indice); APP.processEvents()
                identificador = combo.itemData(indice); antes = _estado(v, w); _Visor.abiertos.clear()
                boton.click(); APP.processEvents()
                assert _estado(v, w) == antes and antes[0] == 1  # G1/G3: sigue en Proyecciones, mismo scroll y estado
                visor = _Visor.abiertos[0]
                esperado = recuperar_resultado(next(a for a in w.historial if a["id"] == identificador)["resultado"])
                linea = visor.eje.get_lines()[0]
                assert list(linea.get_ydata())[-1] == esperado["serie_df"]["Indice"].iloc[-1]  # G5: snapshot por ID
            # G2: proyección distinta de la activa → no cambia el análisis activo ni la sección.
            activo = w.analisis_activo_id; otro = next(a["id"] for a in w.historial if a["id"] != activo)
            antes = _estado(v, w); w.grafica_solicitada.emit(otro); APP.processEvents()
            assert _estado(v, w) == antes
    finally:
        v.close()


# ---------------------------------------------------------------- distribución
def test_U1_U2_acciones_en_una_fila_y_botones_compactos():
    v = ventana_de_prueba(); v.resize(1366, 768); v.show(); w = cargar(v); v._cambiar_seccion(1); APP.processEvents()
    try:
        y = lambda b: b.mapTo(w, b.rect().center()).y()
        x = lambda b: b.mapTo(w, b.rect().topLeft()).x()
        assert abs(y(w.boton_deshacer) - y(w.boton_grafica_inferior)) <= 2  # misma fila
        assert x(w.boton_deshacer) < x(w.boton_rehacer) < x(w.boton_grafica_inferior)
        assert x(w.boton_rehacer) - x(w.boton_deshacer) < 200  # Deshacer/Rehacer juntos a la izquierda
        tabla = w.tabla_valores.mapTo(w, w.tabla_valores.rect().topLeft()).y()
        assert 0 < tabla - w.boton_grafica_inferior.mapTo(w, w.boton_grafica_inferior.rect().bottomLeft()).y() < 24
        # Superior: botón en la fila del rótulo «Proyección guardada», encima del combo (sin fila extra).
        assert y(w.boton_grafica_superior) < w.selector_analisis_valores.mapTo(w, w.selector_analisis_valores.rect().topLeft()).y()
        for b in (w.boton_deshacer, w.boton_rehacer, w.boton_grafica_inferior, w.boton_grafica_superior):
            assert b.height() <= 34, (b.text(), b.height())
        for b in (v.boton_popup_grafica, w.barra.boton_exportar):
            assert b.sizeHint().height() <= 42, (b.text(), b.sizeHint().height())  # auditoría: antes ~56 px
    finally:
        v.close()
