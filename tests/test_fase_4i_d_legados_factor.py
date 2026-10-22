"""Fase 4I-D: conversión por lote de registros con el factor anterior y celdas numéricas puras.

Datos SINTÉTICOS que reproducen los factores de las capturas del usuario (1.027413, 1.023369, 1.030601,
1.023640); el motor estadístico queda bloqueado en todas las pruebas.
"""
import json
import os
import re
from copy import deepcopy
from decimal import Decimal
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox
from openpyxl import load_workbook

from tests.test_slider_comparacion_historica_fase_4d import APP, sintetico
from app_icociv.interfaz.widgets.proyecciones_icociv import WidgetProyeccionesICOCIV
from app_icociv.servicios.actualizacion_icociv import CRITERIO_FACTOR, es_factor_legado, factor_aplicado
from app_icociv.utilidades.importes_presupuestales import desglose_presupuestal

MOTOR = "app_icociv.interfaz.controladores.controlador_principal.ControladorPrincipal.ejecutar_analisis"
# (I proyectado con I0 = 100, P, A, Cantidad, modalidad, factor esperado, % esperado)
CASOS = ((102.7413, 100000, 0, 1, "unitario", 1.0274, 2.74), (102.3369, 150000, 50000, 3, "unitario", 1.0234, 2.34),
         (103.0601, 150000, 50000, 3, "total", 1.0306, 3.06), (102.3640, 84500, 4500, 2.5, "unitario", 1.0236, 2.36),
         (101.995, 1000000, 0, 1, "total", 1.02, 2.0), (97.255, 100000, 0, 1, "unitario", 0.9725, -2.75))


def _legado(r):
    """Registro tal como lo guardaba SAVIP antes de la regla: factor I/I0 sin redondear."""
    r = {k: v for k, v in r.items() if k not in ("criterio_factor", "factor_icociv_indices")}
    f = r["i_icociv"] / r["i0_icociv"]; base = r["base_ajustable"]
    r.update(factor_icociv=f, r_total=base * (f - 1), diferencia_absoluta=base * (f - 1), valor_proyectado=base + base * (f - 1),
             diferencia_porcentual=(base * (f - 1) / base) * 100, historial_ediciones=[])
    return r


def sesion_legada():
    w = sintetico(); w.valores.clear(); w._refrescar_tabla_valores()
    for i, (indice, p, a, q, modo, *_rest) in enumerate(CASOS):
        w.contexto["indice_proyectado"] = indice; w._formulario_guardado = None
        w.item.setText(f"Actividad {i + 1}"); w._item_editado = True; w.unidad.setCurrentIndex(1)
        w.modalidad_importe.setCurrentIndex(w.modalidad_importe.findData(modo))
        w.cantidad.setValue(q); w.precio_base.setValue(p); w.anticipo.setValue(a)
        with patch("app_icociv.interfaz.widgets.controles.confirmar_ingreso_presupuestal", return_value=True):
            w.boton_calcular.click()
    datos = deepcopy(w.datos_sesion()); datos["valores"] = [_legado(r) for r in datos["valores"]]
    w.close()
    nuevo = WidgetProyeccionesICOCIV(); nuevo.restaurar_datos_sesion(datos)  # abrir NO convierte nada
    return nuevo, datos


def _celda(w, fila, clave):
    m = w.modelo_valores
    return m.data(m.index(fila, m.claves.index(clave)))


def test_1_antes_legados_intactos_celdas_numericas_y_aviso():
    w, datos = sesion_legada()
    try:
        assert w.valores == datos["valores"] and all(es_factor_legado(r) for r in w.valores)
        assert [_celda(w, i, "factor") for i in range(4)] == ["1.027413", "1.023369", "1.030601", "1.023640"]
        assert [_celda(w, i, "diferencia") for i in range(4)] == ["2.74", "2.34", "3.06", "2.36"]
        for i in range(len(CASOS)):
            assert re.fullmatch(r"-?[\d,]+(\.\d+)?", _celda(w, i, "factor"))  # solo números, sin «histórico»
        assert w.aviso_legados.isVisibleTo(w) and "6 actividades usan el factor anterior" in w.lbl_legados.text()
    finally:
        w.close()


def test_2_cancelar_y_fallo_no_cambian_nada():
    w, datos = sesion_legada()
    try:
        with patch(MOTOR, side_effect=AssertionError("motor")):
            with patch.object(WidgetProyeccionesICOCIV, "_confirmar_actualizacion", return_value=False):
                assert not w.actualizar_legados_lote()
            assert w.valores == datos["valores"] and w.pila_deshacer.count() == 0
            w.valores[2]["i0_icociv"] = None  # una fila sin índice fiable → nada se aplica (atómica)
            with patch.object(QMessageBox, "warning") as aviso, patch.object(WidgetProyeccionesICOCIV, "_confirmar_actualizacion") as pregunta:
                assert not w.actualizar_legados_lote()
            assert aviso.called and "Actividad 3" in aviso.call_args[0][2] and not pregunta.called
            w.valores[2]["i0_icociv"] = datos["valores"][2]["i0_icociv"]
            assert w.valores == datos["valores"]
    finally:
        w.close()


def test_3_conversion_por_lote_coherente_deshacible_y_persistente(tmp_path):
    w, datos = sesion_legada()
    originales = list(w.valores)
    try:
        with patch(MOTOR, side_effect=AssertionError("motor")), \
             patch.object(WidgetProyeccionesICOCIV, "_confirmar_actualizacion", return_value=True) as pregunta:
            assert w.actualizar_legados_lote()
        assert pregunta.call_count == 1 and len(pregunta.call_args[0][0]) == 6 and (f"{pregunta.call_args[0][0][0][0]['factor_icociv']:.6f}", pregunta.call_args[0][0][0][1]["factor_icociv"]) == ("1.027413", 1.0274)
        assert w.pila_deshacer.count() == 1 and not w.aviso_legados.isVisibleTo(w)
        for i, (r, antes, (indice, p, a, q, modo, f_esp, p_esp)) in enumerate(zip(w.valores, originales, CASOS)):
            assert r["criterio_factor"] == CRITERIO_FACTOR and (r["factor_icociv"], r["diferencia_porcentual"]) == (f_esp, p_esp)
            assert (r["i0_icociv"], r["i_icociv"], r["calculo_id"], r["analisis_id"]) == (antes["i0_icociv"], antes["i_icociv"], antes["calculo_id"], antes["analisis_id"])
            base = Decimal(repr(p - a)); F = Decimal(repr(f_esp))
            assert r["valor_proyectado"] == float(base * F) and r["r_total"] == float(base * (F - 1))
            d = desglose_presupuestal(r, r["valor_proyectado"])
            if modo == "unitario":
                assert (d["base_unitaria"], d["valor_unitario"]) == (p - a, float(base * F)) and d["valor_total"] == float(base * F) * q
            else:
                assert (d["base_total"], d["valor_total"]) == (p - a, float(base * F)) and d["valor_unitario"] == float(base * F) / q
            assert _celda(w, i, "factor") == f"{f_esp:.4f}" and _celda(w, i, "diferencia") == f"{p_esp:.2f}"
            archivo = r["historial_ediciones"][-1]
            assert archivo["antes"]["factor_icociv"] == antes["factor_icociv"] and archivo["antes"]["valor_proyectado"] == antes["valor_proyectado"]
        assert w.valores[0]["valor_proyectado"] == 102740.0 and w.valores[0]["r_total"] == 2740.0  # caso del prompt
        # Deshacer restaura los seis originales de una vez; Rehacer vuelve a aplicar.
        w.pila_deshacer.undo(); assert all(a is b for a, b in zip(w.valores, originales))
        w.pila_deshacer.redo(); assert not any(es_factor_legado(r) for r in w.valores)
        # Guardar y reabrir: sin factor anterior y sin conversión repetida.
        otro = WidgetProyeccionesICOCIV(); otro.restaurar_datos_sesion(deepcopy(w.datos_sesion()))
        try:
            assert otro.valores == w.valores and not otro.aviso_legados.isVisibleTo(otro) and not otro.actualizar_legados_lote()
        finally:
            otro.close()
        # Excel: fórmulas del factor aplicado, celdas numéricas, cinco hojas.
        w._generar_excel(str(tmp_path / "x.xlsx")); libro = load_workbook(tmp_path / "x.xlsx"); ws = libro["Valores proyectados"]
        columnas, _ = w.plan_excel_valores(); n = {k: i for i, (k, _) in enumerate(columnas, 1)}
        assert len(libro.sheetnames) == 5
        for fila in range(3, 3 + len(CASOS)):
            assert ws.cell(fila, n["factor"]).value.startswith("=1+ROUND(") and ws.cell(fila, n["factor"]).number_format == "0.0000"
        libro.close()
        # PDF/Word (mismo modelo de informe): factor solo numérico y metodología homogénea.
        from app_icociv.reportes.sesion_modulos import construir_proyecciones
        informe = construir_proyecciones(w)
        tablas = [b for s in informe.secciones for b in s.bloques if getattr(b, "encabezados", None) and "Factor" in b.encabezados]
        factores = [fila[b.encabezados.index("Factor")] for b in tablas for fila in b.filas]
        assert factores[:4] == ["1.0274", "1.0234", "1.0306", "1.0236"] and all(re.fullmatch(r"-?[\d,]+\.\d+", f) for f in factores)
        assert "Todos los registros siguen la regla vigente" in json.dumps([getattr(b, "texto", "") for s in informe.secciones for b in s.bloques], ensure_ascii=False)
    finally:
        w.close()


def test_4_exportar_con_reglas_mixtas_avisa_y_permite_cancelar():
    w, _ = sesion_legada()
    textos = []
    try:
        with patch.object(QMessageBox, "exec", return_value=0), \
             patch.object(QMessageBox, "setText", side_effect=lambda *a: textos.append(a[-1])):
            assert not w._confirmar_avisos_alcance(w.alcance_exportacion("sesion"))  # cerrar = cancelar
        assert any("6 actividades usan el factor anterior" in t for t in textos)
        from app_icociv.reportes.sesion_modulos import construir_proyecciones
        texto = json.dumps([getattr(b, "texto", "") for s in construir_proyecciones(w).secciones for b in s.bloques], ensure_ascii=False)
        assert "no siguen la regla vigente" in texto and "(histórico)" not in texto
    finally:
        w.close()


def test_5_edicion_posterior_y_descriptiva():
    w, _ = sesion_legada()
    try:
        m = w.modelo_valores; col = m.claves.index
        assert m.setData(m.index(1, col("item")), "Solo el nombre", Qt.EditRole)
        assert es_factor_legado(w.valores[1])  # editar el nombre no recalcula ni convierte
        with patch.object(WidgetProyeccionesICOCIV, "_confirmar_actualizacion", return_value=True):
            w.actualizar_legados_lote()
        assert m.setData(m.index(0, col("precio_base")), "200,000", Qt.EditRole)
        r = w.valores[0]; p, f = factor_aplicado(r["i_icociv"], r["i0_icociv"])
        assert r["criterio_factor"] == CRITERIO_FACTOR and r["factor_icociv"] == 1.0274 and r["valor_proyectado"] == 205480.0
    finally:
        w.close()
