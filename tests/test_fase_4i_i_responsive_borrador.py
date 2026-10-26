"""Fase 4I-I: calculadora ICOCIV y Empalme sin desplazamiento horizontal en media pantalla, sin perder entradas,
y borrador de Empalme conservado al guardar, cerrar y cambiar de sesión."""

import json
import os
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import SIGNAL
from PySide6.QtGui import QFontDatabase
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QFileDialog, QMessageBox, QScrollArea

from tests.test_slider_comparacion_historica_fase_4d import APP, cargar, reales
from tests.test_proyecciones_redisenio_visual import ventana_de_prueba
from tests.test_switch_tema_sesion_dane import MOTOR, _ventana_con_dane
from app_icociv.interfaz.ventana_principal import VentanaPrincipal
from tests.fixtures.sesiones import cargar as cargar_sesion_sintetica, ruta_temporal as ruta_sesion_sintetica  # Fase 1A (AS-007)

for _fuente in ("segoeui.ttf", "segoeuib.ttf", "seguisb.ttf", "seguisym.ttf"):
    QFontDatabase.addApplicationFont(str(Path("C:/Windows/Fonts") / _fuente))

SECUENCIA = (1920, 960, 850, 683, 1920, 683, 1020, 1920)


def _area(control):
    a = control.parent()
    while not isinstance(a, QScrollArea):
        a = a.parent()
    return a


def _visible_sin_horizontal(control):
    """El control cabe en el viewport de su área sin desplazamiento horizontal."""
    area = _area(control)
    derecha = control.mapTo(area.viewport(), control.rect().topRight()).x()
    return area.horizontalScrollBar().maximum() == 0 and 0 <= control.mapTo(area.viewport(), control.rect().topLeft()).x() and derecha <= area.viewport().width()


def _llenar_icociv(w):
    w.tipo_componente.setCurrentText("Capítulo"); w.nombre_componente.setText("Pavimento rígido MR-45")
    w.item.setText("Concreto hidráulico 4000 PSI"); w._item_editado = True; w.unidad.setCurrentIndex(3)
    w.cantidad.setValue(125.5); w.precio_base.setValue(423467.54); w.anticipo.setValue(15000)
    w.modalidad_importe.setCurrentIndex(w.modalidad_importe.findData("unitario"))
    w.observacion.setPlainText("Precio de referencia contractual.")


def _llenar_empalme(e):
    e.item.setText("Acero de refuerzo 60000 PSI"); e.codigo.setText("AC-60"); e.cantidad.setValue(2500)
    e.precio_base.setValue(5280.25); e.anticipo.setValue(120); e.observacion_item.setPlainText("Borrador sin registrar")
    e.modalidad_importe.setCurrentIndex(e.modalidad_importe.findData("total"))
    e.chk_acero.setChecked(True); e.p0.setValue(4100); e.ix.setValue(1.05); e.q.setValue(0.75)


def _calcular(w):
    with patch("app_icociv.interfaz.widgets.controles.confirmar_ingreso_presupuestal", return_value=True):
        w.boton_calcular.click()
    r = deepcopy(w.valores[-1])
    return {k: v for k, v in r.items() if k not in ("calculo_id", "fecha_calculo", "historial_ediciones", "numero_fila")}


def test_calculadora_icociv_una_columna_sin_perder_nada_y_mismo_calculo():
    referencia = ventana_de_prueba(); wr = cargar(referencia); referencia.resize(1920, 900); QTest.qWait(300)
    _llenar_icociv(wr); esperado = _calcular(wr); referencia.close()
    v = ventana_de_prueba(); w = cargar(v)
    try:
        v._cambiar_seccion(1); _llenar_icociv(w); w.precio_base.setFocus()
        borrador, pila = w._datos_calculadora(), w.pila_deshacer.count()
        ids = [id(x) for x, *_ in w._celdas_calculadora]
        conexiones = w.boton_calcular.receivers(SIGNAL("clicked(bool)"))
        claves = (w.tipo_componente, w.nombre_componente, w.item, w.unidad, w.cantidad, w.precio_base, w.anticipo,
                  w.modalidad_importe, w.observacion, w.boton_calcular, w.boton_limpiar, w.lbl_calculo_activo)
        for tema in ("claro", "oscuro"):
            v._aplicar_tema(tema, persistir=False)
            for ancho in SECUENCIA:
                v.resize(ancho, 900); QTest.qWait(450)
                for control in claves:
                    _area(control).ensureWidgetVisible(control, 0, 40); QTest.qWait(10)
                    assert _visible_sin_horizontal(control), (tema, ancho, control.metaObject().className())
                assert w._calculadora_una_columna == v._modo_compacto, (tema, ancho)  # media pantalla ⇒ una columna
                assert w._datos_calculadora() == borrador and w.pila_deshacer.count() == pila
                assert w.modalidad_importe.currentData() == "unitario" and w.precio_base.hasFocus()
        assert [id(x) for x, *_ in w._celdas_calculadora] == ids and w.boton_calcular.receivers(SIGNAL("clicked(bool)")) == conexiones
        v.resize(683, 900); QTest.qWait(450)
        assert _calcular(w) == esperado  # mismo resultado económico calculado en media pantalla
    finally:
        v.close()


def test_empalme_media_pantalla_sin_barra_horizontal_y_estado_invariable():
    v = ventana_de_prueba(); cargar(v); e = v.widget_empalme
    try:
        v._cambiar_seccion(2); _llenar_empalme(e); estado = e._estado_formulario()
        for tema in ("claro", "oscuro"):
            v._aplicar_tema(tema, persistir=False)
            for ancho in SECUENCIA:
                v.resize(ancho, 900); QTest.qWait(450)
                for control in (e.item, e.cantidad, e.precio_base, e.anticipo, e.modalidad_importe, e.q, e.p0, e.ix,
                                e.fecha_final_mes, e.boton_calcular, e.observacion_item):
                    _area(control).ensureWidgetVisible(control, 0, 40); QTest.qWait(10)
                    assert _visible_sin_horizontal(control), (tema, ancho, control.metaObject().className())
                assert e._estado_formulario() == estado and not e.calculos
    finally:
        v.close()


def _guardar(v, destino):
    with patch.object(v, "_solicitar_usuario", return_value="QA"), \
         patch.object(QFileDialog, "getSaveFileName", return_value=(str(destino), "")):
        return v.guardar_rapido(como=True)


def _abrir(v, ruta, decision="descartar"):
    with patch.object(QFileDialog, "getOpenFileName", return_value=(str(ruta), "")), \
         patch.object(v, "_decidir_cierre", return_value=decision), patch(MOTOR, side_effect=AssertionError("motor")):
        v.abrir_sesion()
        while v._operacion_sesion:
            APP.processEvents()


def test_borrador_empalme_se_guarda_cierra_y_reabre_literal(tmp_path):
    v = _ventana_con_dane(); e = v.widget_empalme
    try:
        assert not v._hay_trabajo()
        _llenar_empalme(e)
        assert e.tiene_borrador() and v._hay_trabajo() and v._firma_trabajo() != v._firma_guardada  # solo Empalme ⇒ hay trabajo
        literal = e._estado_formulario()
        # Fallo de escritura: nada se pierde.
        with patch("app_icociv.interfaz.ventana_principal.guardar_sesion", side_effect=PermissionError("Acceso denegado")), \
             patch.object(QMessageBox, "warning"):
            assert not _guardar(v, tmp_path / "x.json")
        assert e._estado_formulario() == literal
        ruta = tmp_path / "con_borrador.json"
        assert _guardar(v, ruta)
        guardado = json.loads(ruta.read_text(encoding="utf-8"))["empalme_iccp_icociv"]
        assert guardado["calculos"] == [] and guardado["borrador_formulario"]["q"] == 0.75  # no se registró nada
        assert guardado["borrador_formulario"]["item"] == "Acero de refuerzo 60000 PSI"
        # «Abrir otra sesión» con el borrador presente: Cancelar lo conserva.
        _abrir(v, ruta, decision="cancelar")
        assert e._estado_formulario() == literal
        # Cerrar sin guardar ⇒ nueva sesión vacía; reabrir ⇒ borrador literal, sin cálculos registrados.
        with patch.object(v, "_decidir_cierre", return_value="descartar"):
            assert v.cerrar_sesion()
        assert not e.tiene_borrador() and e.item.text() == "" and not v._hay_trabajo()
        _abrir(v, ruta)
        assert e._estado_formulario() == literal and not e.calculos and e.tiene_borrador()
        assert v._firma_trabajo() == v._firma_guardada  # recién abierta: sin cambios pendientes
        # «Guardar y cerrar» escribe el borrador (con un cambio) y solo después limpia.
        e.q.setValue(0.8)
        with patch.object(v, "_decidir_cierre", return_value="guardar"):
            assert v.cerrar_sesion()
        assert json.loads(ruta.read_text(encoding="utf-8"))["empalme_iccp_icociv"]["borrador_formulario"]["q"] == 0.8
        assert not e.tiene_borrador()
        # JSON anterior sin el campo nuevo: abre igual y sin borrador (sin contaminación del proyecto previo).
        antiguo = tmp_path / "antiguo.json"
        antiguo.write_text(json.dumps({"usuario": "QA", "archivo_excel": "", "proyecciones_icociv": reales()}, ensure_ascii=False), encoding="utf-8")
        _abrir(v, antiguo)
        assert v.ruta_sesion_actual == antiguo and not e.tiene_borrador() and e.item.text() == ""
    finally:
        v.close()


def test_aviso_sesion_guardada_no_falla_al_destruir_la_ventana():
    v = VentanaPrincipal(); v.show()
    v.notificaciones.mostrar("Sesión guardada", "x", "exito", permanencia=200)
    v.close(); v.deleteLater(); QTest.qWait(600)  # antes: «Internal C++ object (Notificacion) already deleted»


def test_edicion_de_fila_empalme_en_curso_se_reabre_en_edicion(tmp_path):
    from tests.test_historial_empalme_fase_4b import abrir as abrir_4b, guardar as guardar_4b
    datos = cargar_sesion_sintetica('FASE_4B_FIXTURE_DATOS')
    p = tmp_path / "anterior.json"; p.write_text(json.dumps(datos), encoding="utf-8")
    v = VentanaPrincipal(); w = v.widget_empalme
    try:
        abrir_4b(v, p)
        w.tabla.selectRow(0); w.editar_seleccionado(); w.cantidad.setValue(w.cantidad.value() + 7)
        literal, calculo = w._estado_formulario(), w.calculos[0]["calculo_id"]
        guardar_4b(v, tmp_path / "en_edicion.json")
        otra = VentanaPrincipal(); e = otra.widget_empalme
        try:
            abrir_4b(otra, tmp_path / "en_edicion.json")
            assert e.indice_edicion == 0 and e.calculos[0]["calculo_id"] == calculo and e.calculos == w.calculos
            assert e.boton_calcular.text() == "Actualizar cálculo" and e._estado_formulario() == literal
        finally:
            otra.close()
    finally:
        v.close()
