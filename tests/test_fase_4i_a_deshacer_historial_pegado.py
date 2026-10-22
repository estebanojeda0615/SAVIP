"""Fase 4I-A V3: pegado numérico por tipo de campo, Deshacer/Rehacer, resaltado y doble historial.

Pruebas focalizadas con Qt real (portapapeles y Ctrl+V de QTest); sin motor estadístico.
"""
import os
from copy import deepcopy
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import Qt
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication, QLineEdit

from tests.test_fase_4i_tabla_editable import _ids, _widget_con_actividades
from tests.test_fase_4g_b_consulta_exportacion import borrador, formulario
from tests.test_slider_comparacion_historica_fase_4d import reales
from app_icociv.interfaz.widgets.proyecciones_icociv import WidgetProyeccionesICOCIV

APP = QApplication.instance()
SIN_MOTOR = "app_icociv.interfaz.widgets.proyecciones_icociv.calcular_actualizacion_icociv"


def _pegar(editor, texto):
    APP.clipboard().setText(texto)
    QTest.keyClick(editor, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
    APP.processEvents()


def _campo(control, texto):
    control.setFocus(); control.selectAll(); _pegar(control.lineEdit(), texto)


def test_B_ctrl_v_real_en_calculadora_P_A_y_cantidad():
    w = _widget_con_actividades(1); w.show(); w.activateWindow(); APP.processEvents()
    try:
        valores = deepcopy(w.valores); rechazos = QSignalSpy(w.precio_base.entradaRechazada)
        # Convenio V4: la coma agrupa miles y el punto es decimal («4.559» = 4.559).
        for texto, esperado in (("4,559", 4559), ("4.559", 4.559), ("4,55", 4.55), ("4,5590", 4.559), ("0,250", 0.25), ("1,250,000.50", 1250000.5)):
            _campo(w.precio_base, texto)
            assert w.precio_base.value() == esperado, (texto, w.precio_base.value())
        assert rechazos.count() == 0  # sin «Pegado ambiguo» ni otro aviso
        _campo(w.anticipo, "$ 1.250.000"); assert w.anticipo.value() == 1250000
        APP.clipboard().setText("1.250.000,50"); w.anticipo.selectAll(); w.anticipo.lineEdit().paste()  # ruta del menú «Pegar»
        assert w.anticipo.value() == 1250000.5
        for texto, esperado in (("1,25", 1.25), ("1,250.75", 1250.75), ("2,5000", 2.5)):
            _campo(w.cantidad, texto); assert w.cantidad.value() == esperado
        # Convenio V4 (sin decisión en línea): «1.250» = 1.25 y «1,250» = 1250 también en Cantidad.
        _campo(w.cantidad, "1.250"); assert w.cantidad.value() == 1.25
        _campo(w.cantidad, "1,250"); assert w.cantidad.value() == 1250
        # Varias celdas: aviso no modal y valor intacto.
        espia = QSignalSpy(w.cantidad.entradaRechazada)
        _campo(w.cantidad, "1\t2\r\n3\t4"); assert espia.count() == 1 and w.cantidad.value() == 1250
        assert w.valores == valores and w.pila_deshacer.count() == 0  # pegar en la calculadora no crea acciones de tabla
    finally:
        w.close()


def test_C_ctrl_v_real_en_editor_de_celda_y_deshacer_local():
    w = _widget_con_actividades(2); w.show(); w.activateWindow(); APP.processEvents()
    try:
        m = w.modelo_valores; t = w.tabla_valores
        def editar(clave, texto, confirmar=True):
            index = m.index(0, m.claves.index(clave)); t.setCurrentIndex(index); t.edit(index); APP.processEvents()
            editor = APP.focusWidget(); assert isinstance(editor, QLineEdit), editor
            editor.selectAll(); _pegar(editor, texto)
            if confirmar:
                QTest.keyClick(editor, Qt.Key.Key_Return); APP.processEvents()
            return editor
        editar("precio_base", "1,250,000.50"); assert w.valores[0]["precio_base"] == 1250000.5
        editar("anticipo", "1.250.000,50")  # A = P: inválido, aviso NO modal y sin cambio
        assert w.valores[0]["anticipo_amortizado"] == 0 and w.aviso_tabla.isVisibleTo(w)
        editar("precio_base", "2.500.000"); editar("anticipo", "1.250.000,50")
        assert (w.valores[0]["precio_base"], w.valores[0]["anticipo_amortizado"]) == (2500000, 1250000.5)
        editar("anticipo", "0"); editar("precio_base", "4,559"); assert w.valores[0]["precio_base"] == 4559
        # Ctrl+Z dentro del editor abierto deshace TEXTO, no el presupuesto.
        pila = w.pila_deshacer.count(); antes = list(w.valores)
        editor = editar("item", "Texto pegado", confirmar=False)
        QTest.keyClick(editor, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier); APP.processEvents()
        assert editor.text() != "Texto pegado" and w.pila_deshacer.count() == pila and all(a is b for a, b in zip(w.valores, antes))
        QTest.keyClick(editor, Qt.Key.Key_Escape); APP.processEvents()
        # Cantidad en celda con el convenio V4: «1.250» = 1.25, confirmada = una acción deshacible.
        editar("cantidad", "1.250")
        assert w.valores[0]["cantidad"] == 1.25 and w.pila_deshacer.count() == pila + 1
        # Pegado fuera de edición (Ctrl+V sobre la celda) y rango de varias celdas sin modal.
        index = m.index(1, m.claves.index("cantidad")); t.setCurrentIndex(index); t.setFocus()
        _pegar(t, "3,5"); assert w.valores[1]["cantidad"] == 3.5
        from PySide6.QtWidgets import QMessageBox, QToolTip
        with patch.object(QMessageBox, "information", side_effect=AssertionError("modal")), patch.object(QToolTip, "showText") as aviso:
            _pegar(t, "1\t2\n3\t4")
        assert aviso.called and w.valores[1]["cantidad"] == 3.5
    finally:
        w.close()


def test_D_deshacer_rehacer_botones_atajos_y_resaltado():
    w = _widget_con_actividades(4); w.show(); w.activateWindow(); APP.processEvents()
    try:
        ids = _ids(w); originales = deepcopy(w.valores)
        assert w.boton_deshacer.isVisibleTo(w) and w.boton_rehacer.isVisibleTo(w)
        assert not w.boton_deshacer.isEnabled() and not w.boton_rehacer.isEnabled()
        with patch(SIN_MOTOR, side_effect=AssertionError("No recalcular")):
            w.tabla_valores.verticalHeader().moveSection(3, 0)  # arrastre
            movido = [ids[3], *ids[:3]]
            assert _ids(w) == movido and w.boton_deshacer.isEnabled() and "mover «Actividad 4»" in w.boton_deshacer.toolTip()
            assert w._resaltado_id == ids[3] and w._temporizador_resaltado.isActive()
            w.boton_deshacer.click(); assert _ids(w) == ids and w.boton_rehacer.isEnabled() and w._resaltado_id == ids[3]
            w.boton_rehacer.click(); assert _ids(w) == movido
            w.tabla_valores.setFocus()
            QTest.keyClick(w.tabla_valores, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier); assert _ids(w) == ids
            QTest.keyClick(w.tabla_valores, Qt.Key.Key_Y, Qt.KeyboardModifier.ControlModifier); assert _ids(w) == movido
            QTest.keyClick(w.tabla_valores, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
            QTest.keyClick(w.tabla_valores, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)
            assert _ids(w) == movido
            # Menú: Mover abajo; resaltado transferido y temporizador reiniciado.
            assert w.mover_actividad(ids[0], 2) and w._resaltado_id == ids[0] and w.pila_deshacer.count() == 2
            # Clic en la tabla quita el resaltado.
            QTest.mouseClick(w.tabla_valores.viewport(), Qt.MouseButton.LeftButton, pos=w.tabla_valores.visualRect(w.modelo_valores.index(0, 2)).center())
            assert w._resaltado_id is None
        # Edición de celda: deshacer restaura el registro completo (mismo objeto) y la auditoría.
        m = w.modelo_valores; fila = next(i for i, r in enumerate(w._valores_visibles) if r["calculo_id"] == ids[1])
        previo = w.valores[[r["calculo_id"] for r in w.valores].index(ids[1])]; copia = deepcopy(previo)
        assert m.setData(m.index(fila, m.claves.index("cantidad")), "5", Qt.EditRole)
        nuevo = next(r for r in w.valores if r["calculo_id"] == ids[1])
        assert nuevo["cantidad"] == 5 and "editar Cantidad" in w.boton_deshacer.toolTip()
        with patch(SIN_MOTOR, side_effect=AssertionError("No recalcular")):
            w.pila_deshacer.undo()
            restaurado = next(r for r in w.valores if r["calculo_id"] == ids[1])
            assert restaurado is previo and restaurado == copia and w._resaltado_id == ids[1]
            w.pila_deshacer.redo(); assert next(r for r in w.valores if r["calculo_id"] == ids[1]) is nuevo
            w.pila_deshacer.undo()
        # Una acción nueva tras deshacer invalida la rama de rehacer.
        w.mover_actividad(ids[2], 0); assert not w.pila_deshacer.canRedo()
        # Cambios que no son comandos (filtro, tema) no entran en la pila.
        n = w.pila_deshacer.count(); w.solo_analisis_activo.setChecked(True); w.solo_analisis_activo.setChecked(False)
        assert w.pila_deshacer.count() == n
        # Cargar sesión reinicia la pila.
        w.restaurar_datos_sesion(deepcopy(w.datos_sesion())); assert w.pila_deshacer.count() == 0 and not w.boton_deshacer.isEnabled()
        assert sorted(r["calculo_id"] for r in w.valores) == sorted(r["calculo_id"] for r in originales)
    finally:
        w.close()


def test_E_dos_historiales_sincronizados_sin_tocar_calculadora():
    w = WidgetProyeccionesICOCIV(); w.restaurar_datos_sesion(reales()); w.show(); APP.processEvents()  # tres análisis reales
    try:
        sup_a, inf_a, sup_p, inf_p = w.selector_ambito, w.selector_ambito_inferior, w.selector_analisis_valores, w.selector_proyeccion_inferior
        textos = lambda c: [c.itemText(i) for i in range(c.count())]
        datos = lambda c: [c.itemData(i) for i in range(c.count())]
        borrador(w); antes = formulario(w); activo = w.analisis_activo_id
        assert datos(sup_a) == datos(inf_a) and textos(sup_a) == textos(inf_a) and inf_a.isVisibleTo(w) and sup_a.isVisibleTo(w)
        assert inf_a.count() > 2 and inf_p.count() > 2
        tipologia = w._ambitos[0]
        inf_a.setCurrentIndex(inf_a.findData(tipologia["clave"])); APP.processEvents()  # inferior → superior
        assert sup_a.currentData() == tipologia["clave"] and w._ambito_consulta["clave"] == tipologia["clave"]
        assert datos(sup_p) == datos(inf_p)
        sup_a.setCurrentIndex(0); APP.processEvents()  # superior → inferior
        assert inf_a.currentIndex() == 0 and w._ambito_consulta is None
        w.solo_analisis_activo.setChecked(True)
        espia = QSignalSpy(w.analisis_solicitado)
        inf_p.setCurrentIndex(1); APP.processEvents()
        assert sup_p.currentIndex() == 1 and w._proyeccion_consulta == inf_p.itemData(1) and espia.count() == 1
        assert w.lbl_filtro_inferior.text() == w.lbl_filtro_valores.text() and "de" in w.lbl_filtro_inferior.text()
        assert formulario(w) == antes and w.analisis_activo_id == activo  # la ventana activa al recibir la señal
        inf_p.setCurrentIndex(0); APP.processEvents()  # «Todas…» no activa nada
        assert sup_p.currentIndex() == 0 and espia.count() == 1 and formulario(w) == antes and w.analisis_activo_id == activo
        # Homónimos: cada ámbito conserva su clave única en ambos desplegables.
        assert len(set(datos(inf_a))) == inf_a.count()
        # «Sin análisis activo» sigue desactivando sin que el refresco lo reactive.
        w.desactivar_analisis(); APP.processEvents(); assert w.analisis_activo_id is None
        inf_a.setCurrentIndex(1); APP.processEvents(); assert w.analisis_activo_id is None
    finally:
        w.close()
