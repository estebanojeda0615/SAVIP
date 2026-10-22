"""Regresión de la presentación ICOCIV con Qt real y tablas sintéticas, sin pronósticos."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
from PySide6.QtCore import QEvent, QPoint, Qt
from PySide6.QtGui import QHelpEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QBoxLayout, QStyleOptionViewItem

from app_icociv.interfaz.animaciones import establecer_movimiento_reducido, establecer_sombras
from app_icociv.interfaz.tema import hoja_estilos
from app_icociv.interfaz.ventana_principal import VentanaPrincipal
from app_icociv.interfaz.widgets.proyecciones_icociv import COLUMNAS_PROYECCIONES, COLUMNAS_VALORES

_app = QApplication.instance() or QApplication([])
establecer_movimiento_reducido(True)
establecer_sombras(False)


def ventana_de_prueba() -> VentanaPrincipal:
    ventana = VentanaPrincipal()
    # Los dos grupos tienen hijos distintos; no se leen archivos ni anexos DANE.
    filas = []
    for i in range(2):
        filas.append({
            "Codigo_Grupos": f"G{i}", "Grupos_Obra": f"Grupo sintético {i}",
            "Cod_Subclases": f"S{i}", "Subclases": f"Subclase sintética {i}",
            "Cod_tip_obra": f"T{i}", "Tip_obra": f"Tipología sintética {i}",
            "cod_agreg_niv_obra_cap": f"C{i}", "Cap_const": f"Capítulo sintético {i}",
            "cod_agreg_nivel_obra_capitulo": f"C{i}", "Grupo_Costos": f"Costos sintéticos {i}",
            "Grupos_costos": f"Costos sintéticos {i}", "Insumos": f"Insumo sintético {i}",
        })
    ventana.controlador.tablas = {
        clave: pd.DataFrame(filas)
        for clave in ("T_16", "T_16_1", "T_16_2", "T_16_3", "T_16_6", "T_16_7", "T_16_8", "T_16_9", "T_16_10", "T_16_11", "T_16_12", "T_16_13")
    }
    ventana._llenar_combo(ventana.combo_grupo, ventana.controlador.opciones_grupo())
    ventana._actualizar_controles_habilitados(True)
    ventana._cambiar_seccion(1)
    ventana.show()
    _app.processEvents()
    return ventana


def test_jerarquia_y_casillas_conservan_senales_y_filtros() -> None:
    v = ventana_de_prueba()
    try:
        assert v.combo_nivel2.isHidden()
        v.combo_grupo.setCurrentIndex(1)
        assert v.lbl_nivel2.text() == "Subclase CPC" and not v.combo_nivel2.isHidden()
        assert not v.chk_t16_1.isHidden() and v.chk_t16_2.isHidden()

        QTest.mouseClick(v.chk_t16, Qt.MouseButton.LeftButton, pos=QPoint(10, v.chk_t16.height() // 2))
        assert v.lbl_nivel2.text() == "Grupo de costos" and v.chk_t16_1.isHidden()
        v.combo_nivel2.setCurrentIndex(1)
        assert v.lbl_nivel3.text() == "Insumo" and v.combo_nivel4.isHidden()

        v.chk_t16.setChecked(False)
        v.combo_nivel2.setCurrentIndex(1)
        assert v.lbl_nivel3.text() == "Tipología de obra" and not v.chk_t16_2.isHidden()
        v.chk_t16_1.setChecked(True)
        assert v.lbl_nivel3.text() == "Grupo de costos" and v.chk_t16_2.isHidden()
        v.combo_nivel3.setCurrentIndex(1)
        assert v.lbl_nivel4.text() == "Insumo"

        v.chk_t16_1.setChecked(False)
        v.combo_nivel3.setCurrentIndex(1)
        assert v.lbl_nivel4.text() == "Capítulo constructivo" and not v.chk_t16_3.isHidden()
        v.chk_t16_2.setChecked(True)
        assert v.lbl_nivel4.text() == "Grupo de costos" and v.chk_t16_3.isHidden()
        v.combo_nivel4.setCurrentIndex(1)
        assert v.lbl_nivel5.text() == "Insumo" and v.combo_nivel6.isHidden()

        v.chk_t16_2.setChecked(False)
        v.combo_nivel4.setCurrentIndex(1)
        assert v.combo_nivel5.isHidden()
        v.chk_t16_3.setChecked(True)
        assert v.lbl_nivel5.text() == "Grupo de costos"
        v.combo_nivel5.setCurrentIndex(1)
        assert v.lbl_nivel6.text() == "Insumo" and not v.combo_nivel6.isHidden()
        v.combo_nivel6.setCurrentIndex(1)

        v.combo_grupo.setCurrentIndex(2)
        assert v.combo_nivel2.currentData() is None
        assert v.combo_nivel3.isHidden() and v.combo_nivel6.isHidden()
        assert v.chk_t16_3.isHidden() and not v.chk_t16_3.isChecked()
        assert v.combo_nivel2.itemText(1) == "Subclase sintética 1"
    finally:
        v.close()


def test_boton_calcular_y_columnas_conservan_resultado_actual() -> None:
    v = ventana_de_prueba()
    w = v.widget_proyecciones
    try:
        w.contexto = {
            "proyeccion_generada": True, "indice_base": 100.0, "indice_proyectado": 110.0,
            "ruta_texto": "Datos sintéticos de prueba", "serie_final": "Ítem sintético",
            "periodo_base": "2026-12", "periodo_proyectado": "2027-06",
            "horizonte_solicitado": 6, "modelo": "Solo prueba de UI, sin pronóstico",
        }
        w._actualizar_estado_calculadora()
        w.item.setText("<Ítem & prueba>")
        w.unidad.setCurrentIndex(1)
        w.cantidad.setValue(2)
        w.precio_base.setValue(1000)
        w.anticipo.setValue(100)
        w.modalidad_importe.setCurrentIndex(w.modalidad_importe.findData('unitario'))
        QTest.mouseClick(w.boton_calcular, Qt.MouseButton.LeftButton)
        assert len(w.valores) == 1
        assert abs(w.valores[0]["valor_proyectado"] - 990.0) < 1e-9
        assert w.valores[0]["cantidad"] == 2
        assert list(w.modelo_valores._dataframe.columns) == [titulo for _, titulo in COLUMNAS_VALORES]

        w.proyecciones = [{"numero": 1, "item": "Ítem sintético"}]
        w._refrescar_tabla_proyecciones()
        assert w.modelo_proyecciones.columnCount() == len(COLUMNAS_PROYECCIONES) == 21
        assert w.modelo_valores.columnCount() == 17
        assert all(not w.tabla_valores.isColumnHidden(i) for i in range(17))
        option = QStyleOptionViewItem()
        index = w.modelo_valores.index(0, 6)
        w.tabla_valores.itemDelegate().initStyleOption(option, index)
        assert option.displayAlignment & Qt.AlignmentFlag.AlignRight
        assert index.data() == w.modelo_valores.data(index)
        item = w.modelo_valores.index(0, 3)
        evento = QHelpEvent(QEvent.Type.ToolTip, QPoint(0, 0), QPoint(0, 0))
        with patch("app_icociv.interfaz.widgets.proyecciones_icociv.QToolTip.showText") as tooltip:
            assert w.tabla_valores.itemDelegate().helpEvent(evento, w.tabla_valores, option, item)
            assert tooltip.call_args.args[1] == "<qt>&lt;Ítem &amp; prueba&gt;</qt>"
        assert item.data() == "<Ítem & prueba>"
    finally:
        v.close()


def test_layout_adaptable_y_temas_sin_cambiar_entrada() -> None:
    v = ventana_de_prueba()
    try:
        v.combo_grupo.setCurrentIndex(1)
        seleccion = v._seleccion_actual().copy()
        for ancho, alto in ((1100, 700), (1366, 768), (1920, 1080)):
            v.resize(ancho, alto)
            _app.processEvents()
            esperado = QBoxLayout.Direction.LeftToRight if v.widget_proyecciones.width() >= 856 else QBoxLayout.Direction.TopToBottom
            assert v.widget_proyecciones.fila_seleccion.direction() == esperado
            assert v.widget_proyecciones.fila_calculo.direction() == esperado
            assert v._seleccion_actual() == seleccion
        for tema in ("claro", "oscuro"):
            v.setStyleSheet(hoja_estilos(tema))
            _app.processEvents()
            assert v._seleccion_actual() == seleccion
        assert v.widget_proyecciones.cantidad.decimals() == 4
        assert v.widget_proyecciones.precio_base.decimals() == 4  # Fase 4I-A: P/A conservan hasta 4 decimales internos
    finally:
        v.close()


if __name__ == "__main__":
    for nombre, funcion in sorted(globals().copy().items()):
        if nombre.startswith("test_") and callable(funcion):
            funcion()
            print(f"OK {nombre}", flush=True)
