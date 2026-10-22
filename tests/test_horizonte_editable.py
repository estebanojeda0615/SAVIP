"""Fase 2C-B: clics nativos en las flechas y sincronización existente 1..24."""

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests.test_numericos_icociv import _app, ventana_de_prueba
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest, QSignalSpy
from PySide6.QtWidgets import QStyle, QStyleOptionSpinBox
from app_icociv.interfaz.ventana_principal import VentanaPrincipal
from app_icociv.interfaz.controladores.trabajadores import TrabajadorFuncion


def ventana_horizonte():
    v = ventana_de_prueba()
    v.controlador.periodos = [f"2026_{i}" for i in range(1, 6)]
    v._ajustar_periodo_por_defecto(v.controlador.periodos)
    v.combo_grupo.setCurrentIndex(1)
    return v


def pulsar_flecha(v, aumentar):
    control = v.spin_horizonte_personalizado
    opcion = QStyleOptionSpinBox()
    control.initStyleOption(opcion)
    sub = QStyle.SubControl.SC_SpinBoxUp if aumentar else QStyle.SubControl.SC_SpinBoxDown
    rect = control.style().subControlRect(QStyle.ComplexControl.CC_SpinBox, opcion, sub, control)
    assert not rect.isEmpty()
    QTest.mouseClick(control, Qt.MouseButton.LeftButton, pos=rect.center())
    _app.processEvents()


def comprobar(v, meses, modo):
    total = 2026 * 12 + 4 + meses
    assert v.spin_horizonte_personalizado.value() == meses
    assert v.combo_horizonte.currentData() == modo
    assert (v.spin_anio.value(), v.spin_mes.value()) == (total // 12, total % 12 + 1)
    assert v._horizonte_solicitado() == meses
    assert f"{meses} mes(es)" in v.lbl_horizonte_recomendado.text()
    assert not v._sincronizando


def test_todos_los_predefinidos_flechas_y_retorno():
    v = ventana_horizonte()
    try:
        predefinidos = [v.combo_horizonte.itemData(i) for i in range(v.combo_horizonte.count()) if v.combo_horizonte.itemData(i) is not None]
        assert predefinidos == [1, 3, 6, 12, 18]
        for meses in predefinidos:
            v.combo_horizonte.setCurrentIndex(v.combo_horizonte.findData(meses))
            comprobar(v, meses, meses)
            assert v.spin_horizonte_personalizado.isEnabled()
            combo = QSignalSpy(v.combo_horizonte.currentIndexChanged)
            spin = QSignalSpy(v.spin_horizonte_personalizado.valueChanged)
            pulsar_flecha(v, True)
            comprobar(v, meses + 1, None)
            assert combo.count() == 1 and spin.count() == 1
            v.combo_horizonte.setCurrentIndex(v.combo_horizonte.findData(meses))
            comprobar(v, meses, meses)
            pulsar_flecha(v, False)
            comprobar(v, meses - 1, None) if meses > 1 else comprobar(v, 1, 1)
            v.combo_horizonte.setCurrentIndex(v.combo_horizonte.findData(meses))
            comprobar(v, meses, meses)
    finally:
        v.close()


def test_limites_1_24_y_sin_ciclos():
    v = ventana_horizonte()
    try:
        control = v.spin_horizonte_personalizado
        assert control.minimum() == 1 and control.maximum() == 24
        pulsar_flecha(v, False)
        comprobar(v, 1, 1)
        control.setValue(24)
        comprobar(v, 24, None)
        spin = QSignalSpy(control.valueChanged)
        with patch.object(v, "_alertar_horizonte_excedido") as aviso:
            pulsar_flecha(v, True)
            assert aviso.call_count == 1
        assert spin.count() == 0
        comprobar(v, 24, None)
        v._sincronizar_periodo_desde_horizonte()
        comprobar(v, 24, None)
        v._sincronizando = True
        v.combo_horizonte.setCurrentIndex(v.combo_horizonte.findData(12))
        control.setValue(12)
        assert v.combo_horizonte.currentData() == 12
        v._sincronizando = False
        v._sincronizar_periodo_desde_horizonte()
        comprobar(v, 12, 12)
    finally:
        v.close()


def test_bloqueos_legitimos_sin_archivo_sin_grupo_y_ocupado():
    vacia = VentanaPrincipal()
    try:
        vacia.combo_horizonte.setCurrentIndex(vacia.combo_horizonte.findData(None))
        assert not vacia.spin_horizonte_personalizado.isEnabled()
        vacia._establecer_ocupado(False)
        assert not vacia.spin_horizonte_personalizado.isEnabled()
    finally:
        vacia.close()
    v = ventana_horizonte()
    try:
        v.combo_grupo.setCurrentIndex(0)
        assert not v.spin_horizonte_personalizado.isEnabled()
        v.combo_horizonte.setCurrentIndex(v.combo_horizonte.findData(12))
        assert not v.spin_horizonte_personalizado.isEnabled()
        with patch("app_icociv.interfaz.ventana_principal.QMessageBox.warning") as advertencia:
            v.ejecutar_proyeccion()
            assert advertencia.call_count == 1 and v.trabajador is None
        v.combo_grupo.setCurrentIndex(1)
        assert v.spin_horizonte_personalizado.isEnabled()
        v._establecer_ocupado(True)
        assert not v.spin_horizonte_personalizado.isEnabled()
        v.combo_horizonte.setCurrentIndex(v.combo_horizonte.findData(18))
        assert not v.spin_horizonte_personalizado.isEnabled()
        v._establecer_ocupado(False)
        assert v.spin_horizonte_personalizado.isEnabled()
        comprobar(v, 18, 18)
        with patch.object(v, "trabajador") as trabajador:
            trabajador.isRunning.return_value = True
            v._establecer_ocupado(False)
            assert not v.spin_horizonte_personalizado.isEnabled()
            trabajador.isRunning.return_value = False
            v._establecer_ocupado(False)
            assert v.spin_horizonte_personalizado.isEnabled()
        v._establecer_ocupado(True)
        v.trabajador = TrabajadorFuncion(lambda: None)
        v.trabajador.finished.connect(lambda: v._establecer_ocupado(False))
        v.trabajador.start()
        for _ in range(300):
            QTest.qWait(10)
            if not v.trabajador.isRunning() and v.spin_horizonte_personalizado.isEnabled():
                break
        assert not v.trabajador.isRunning() and v.spin_horizonte_personalizado.isEnabled()
    finally:
        v.close()


def test_12_13_11_meses_ambos_temas():
    v = ventana_horizonte()
    try:
        for tema in ("claro", "oscuro"):
            v._aplicar_tema(tema, persistir=False)
            v.combo_horizonte.setCurrentIndex(v.combo_horizonte.findData(12))
            comprobar(v, 12, 12)
            pulsar_flecha(v, True)
            comprobar(v, 13, None)
            v.combo_horizonte.setCurrentIndex(v.combo_horizonte.findData(12))
            pulsar_flecha(v, False)
            comprobar(v, 11, None)
    finally:
        v.close()


if __name__ == "__main__":
    for nombre, funcion in sorted(globals().copy().items()):
        if nombre.startswith("test_") and callable(funcion):
            funcion()
            print("OK " + nombre, flush=True)
