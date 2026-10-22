"""Fase 4I-J (ajuste K): «Aplicar fecha objetivo a análisis guardados» pide confirmación y, si se acepta,
actualiza TODAS las actividades afectadas con la trayectoria guardada (sin motor), en un solo paso de Deshacer."""

import json
import os
from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog, QFileDialog, QMessageBox, QPushButton

from tests.test_fase_4i_j_fecha_comun import APP, CAPTURAS, _calcular, _cargar
from tests.test_fase_4i_j_reutilizacion import _Contador, _anexo, _ejecutar
from app_icociv.interfaz.controladores.controlador_principal import ControladorPrincipal
from app_icociv.interfaz.ventana_principal import VentanaPrincipal
from app_icociv.interfaz.widgets.proyecciones_icociv import WidgetProyeccionesICOCIV
from app_icociv.servicios import fecha_objetivo as fo

CAPTURAS_K = CAPTURAS.parent.parent / "fase_4i_j_k" / "capturas"
CONSERVADOS = ("calculo_id", "analisis_id", "item", "unidad", "cantidad", "precio_base", "anticipo_amortizado",
               "i0_icociv", "periodo_base", "modalidad_importe", "nombre_componente", "tipo_componente")


def _canonico(w):
    return json.dumps(w.datos_sesion(), sort_keys=True, default=str)


def _aplicar(v, anio, mes, alcance="todas", respuesta=True):
    v.spin_anio.setValue(anio); v.spin_mes.setValue(mes)
    v.combo_alcance_fecha.setCurrentIndex(v.combo_alcance_fecha.findData(alcance))
    with patch.object(WidgetProyeccionesICOCIV, "_confirmar_actualizacion", return_value=respuesta) as dialogo:
        resultado = v.aplicar_fecha_objetivo()
    return resultado, dialogo


def _factor_vigente(i, i0):
    p = ((Decimal(repr(i)) / Decimal(repr(i0)) - 1) * 100).quantize(Decimal("0.01"), ROUND_HALF_UP)
    return float(1 + p / 100)


def test_aceptar_cancelar_deshacer_individual_bloqueo_y_persistencia(tmp_path):
    anexo = _anexo(tmp_path / "anex-ICOCIV-oct2026.xlsx")
    v = VentanaPrincipal(); v.resize(1366, 900); v.show(); w = v.widget_proyecciones
    motor = _Contador()
    try:
        with patch.object(ControladorPrincipal, "ejecutar_analisis", motor.metodo):
            _cargar(v, anexo)
            assert _ejecutar(v, 1, 9) == 1
            for i in range(6):
                _calcular(w, f"A{i + 1}")
            assert _ejecutar(v, 2, 9) == 1
            for i in range(5):
                _calcular(w, f"B{i + 1}")
            a, b = w.historial
            assert len(w.valores) == 11 and {r["periodo_proyectado"] for r in w.valores} == {"2027-07"} and motor.n == 2

            # Cancelar: sesión idéntica, sin Deshacer nuevo, sin fecha común (la confirmación antecede a todo).
            antes, pila = _canonico(w), w.pila_deshacer.count()
            hecho, dialogo = _aplicar(v, 2027, 9, respuesta=False)
            assert not hecho and dialogo.call_count == 1 and _canonico(w) == antes and w.pila_deshacer.count() == pila
            assert w.fecha_objetivo_presupuesto == ""
            kw = dialogo.call_args.kwargs
            assert kw["titulo"] == "Actualizar fecha objetivo del presupuesto" and kw["boton"] == "Aceptar y actualizar" and kw["con_fechas"]
            assert "Se actualizarán 11 actividades al periodo 2027-09" in kw["introduccion"] and "No se realizará un nuevo análisis" in kw["introduccion"]
            assert len(dialogo.call_args[0][0]) == 11

            # Aceptar: las 11 actividades pasan a 2027-09 con el punto guardado de SU análisis, sin motor.
            originales = deepcopy(w.valores)
            hecho, _ = _aplicar(v, 2027, 9)
            assert hecho and motor.n == 2 and w.pila_deshacer.count() == pila + 1 and w.fecha_objetivo_presupuesto == "2027-09"
            tray = {a["id"]: fo.trayectoria(a), b["id"]: fo.trayectoria(b)}
            for viejo, nuevo in zip(originales, w.valores):
                assert all(nuevo.get(k) == viejo.get(k) for k in CONSERVADOS)  # I0, P, A, cantidad, modalidad, vínculos
                assert (nuevo["periodo_proyectado"], nuevo["horizonte"], nuevo["i_icociv"]) == ("2027-09", 11, tray[viejo["analisis_id"]][10])
                assert nuevo["factor_icociv"] == _factor_vigente(nuevo["i_icociv"], nuevo["i0_icociv"])
                assert nuevo["historial_ediciones"][-1]["antes"]["i_icociv"] == viejo["i_icociv"]
                assert "sin ejecutar el motor" in nuevo["historial_ediciones"][-1]["motivo"]
            m = w.modelo_valores  # la tabla inferior ya muestra el índice nuevo
            columna = m.claves.index("i_icociv")
            assert all(m.data(m.index(f, columna)) not in (None, "") for f in range(m.rowCount())) and m.rowCount() == 11
            assert "sep-2027" in v.lbl_fecha_presupuesto.text() and w.actividades_en_otra_fecha() == 0
            actualizados = deepcopy(w.valores)
            # Misma fecha otra vez: sin ventana ni Deshacer nuevo.
            hecho, dialogo = _aplicar(v, 2027, 9)
            assert hecho and not dialogo.called and w.pila_deshacer.count() == pila + 1 and "ya corresponden" in w.aviso_tabla.text()

            # Deshacer una vez restaura TODO; Rehacer lo reaplica.
            w.pila_deshacer.undo(); APP.processEvents()
            assert w.valores == originales and w.fecha_objetivo_presupuesto == "" and "consulta_horizonte" not in a
            assert w.contexto["periodo_proyectado"] == "2027-07"
            w.pila_deshacer.redo(); APP.processEvents()
            assert w.valores == actualizados and w.fecha_objetivo_presupuesto == "2027-09"

            # Solo el análisis seleccionado (B → 2027-11): cambian solo sus 5 actividades; aviso integrado.
            v._activar_analisis(b["id"], conservar_formulario=True)
            hecho, dialogo = _aplicar(v, 2027, 11, "individual")
            assert hecho and "Atención" in dialogo.call_args.kwargs["introduccion"] and len(dialogo.call_args[0][0]) == 5
            assert [r["periodo_proyectado"] for r in w.valores] == ["2027-09"] * 6 + ["2027-11"] * 5
            assert w.valores[:6] == actualizados[:6] and w.excepciones_fecha[-1]["analisis_id"] == b["id"]
            assert "jul-2027" not in fo.advertencia_fechas(w.valores, w.fecha_objetivo_presupuesto)
            assert "sep-2027 (6 actividades) y nov-2027 (5 actividades)" in fo.advertencia_fechas(w.valores, w.fecha_objetivo_presupuesto)
            w.pila_deshacer.undo()

            # Bloqueos sin cambios parciales: fuera de 24 meses y actividad sin análisis vinculado.
            antes = _canonico(w)
            # (Los controles Año/Mes ya impiden pasar de 24 meses; se comprueba la regla en la propia operación.)
            with patch.object(QMessageBox, "warning") as aviso,                  patch.object(WidgetProyeccionesICOCIV, "_confirmar_actualizacion", side_effect=AssertionError("sin ventana")):
                hecho = w.aplicar_fecha_objetivo("2028-12")
            assert not hecho and "máximo es 24" in aviso.call_args[0][2] and _canonico(w) == antes
            w.valores[3]["analisis_id"] = None
            with patch.object(QMessageBox, "warning") as aviso:
                hecho, dialogo = _aplicar(v, 2027, 12)
            assert not hecho and not dialogo.called and "no tiene un análisis vinculado" in aviso.call_args[0][2]
            w.valores[3]["analisis_id"] = a["id"]; assert _canonico(w) == antes
            assert motor.n == 2  # cero llamadas al motor en todo el ajuste

            # Guardar y reabrir: fechas y valores actualizados, sin motor.
            ruta = tmp_path / "presupuesto.json"
            with patch.object(v, "_solicitar_usuario", return_value="QA"), patch.object(QFileDialog, "getSaveFileName", return_value=(str(ruta), "")):
                assert v.guardar_sesion_actual(como=True)
            otra = VentanaPrincipal()
            try:
                _cargar(otra, anexo)
                with patch.object(QFileDialog, "getOpenFileName", return_value=(str(ruta), "")):
                    otra.abrir_sesion()
                    while otra._operacion_sesion:
                        APP.processEvents()
                assert otra.widget_proyecciones.valores == w.valores and otra.widget_proyecciones.fecha_objetivo_presupuesto == "2027-09"
            finally:
                otra.close()
            assert motor.n == 2

            # Ventana real: Esc no cambia nada; capturas en claro y oscuro a media pantalla.
            CAPTURAS_K.mkdir(parents=True, exist_ok=True)
            for tema in ("claro", "oscuro"):
                v._aplicar_tema(tema, persistir=False); v.resize(960, 900); QTest.qWait(300)
                antes, visto = _canonico(w), {}

                def capturar(tema=tema):
                    d = next((x for x in QApplication.topLevelWidgets() if isinstance(x, QDialog) and x.isVisible()), None)
                    if d is None:
                        QTimer.singleShot(100, capturar); return
                    visto.update(titulo=d.windowTitle(), botones=sorted(b.text() for b in d.findChildren(QPushButton)))
                    d.grab().save(str(CAPTURAS_K / f"confirmacion_fecha_{tema}.png"))
                    QTest.keyClick(d, Qt.Key.Key_Escape)
                QTimer.singleShot(200, capturar)
                v.spin_anio.setValue(2027); v.spin_mes.setValue(12)
                v.combo_alcance_fecha.setCurrentIndex(0)
                assert not v.aplicar_fecha_objetivo() and _canonico(w) == antes
                assert visto["titulo"] == "Actualizar fecha objetivo del presupuesto" and visto["botones"] == ["Aceptar y actualizar", "Cancelar"]
    finally:
        v.close()
