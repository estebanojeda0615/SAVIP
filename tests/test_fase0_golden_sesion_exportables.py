"""Fase 0 · Golden Master de sesiones y exportables sobre la ventana real (Qt offscreen) y un anexo sintético.

Un recorrido completo (tests/fixtures/fase0/captura_gui.py) se ejecuta una vez por módulo; cada prueba
compara una parte con golden/sesion_exportables.json: invariantes del flujo (motor no reejecutado,
guardado atómico, Ctrl+S, cancelación, error), sesión guardada, consultas H11→H23→H11, Excel de 5 hojas
con fórmulas, PDF y DOCX de la sesión, factor legado, y CSV/DOCX/PDF del informe de proyección."""

import json
import time
from copy import deepcopy

import pytest

from tests.fixtures.fase0 import captura as c
from tests.fixtures.fase0 import captura_gui as g

GOLDEN = c.leer_golden("sesion_exportables.json")


def _celdas(docx):
    return [c for tabla in docx["tablas"] for fila in tabla for c in fila]


@pytest.fixture(scope="module")
def recorrido(tmp_path_factory):
    carpeta = tmp_path_factory.mktemp("fase0_sesion")
    return carpeta, g.escenario(carpeta)


@pytest.mark.parametrize("seccion", ["invariantes", "consultas_serie1", "sesion", "excel_sesion", "pdf_sesion",
                                     "docx_sesion", "factor_legado", "informe_proyeccion"])
def test_golden_sesion_exportables(recorrido, seccion):
    assert c.diferencias(GOLDEN[seccion], recorrido[1][seccion], seccion) == []


def test_invariantes_del_flujo(recorrido):
    inv = recorrido[1]["invariantes"]
    assert (inv["serie1_h11_nuevos"], inv["serie2_h23_nuevos"], inv["motor_tras_dos_series"]) == (1, 1, 2)
    assert (inv["serie1_h23_reconsulta_nuevos"], inv["serie1_h11_reconsulta_nuevos"], inv["motor_tras_reconsultas"]) == (0, 0, 2)
    assert inv["valores_intactos_tras_reconsultas"] and inv["deshacer_restaura_orden"] and inv["rehacer_reaplica"]
    assert inv["guardar_como"] == [True, 1, True, True]
    assert inv["ctrl_s_misma_ruta"] == [0, True, True]  # sin diálogo, misma ruta, sin cambios pendientes
    assert inv["guardar_como_cancelado"] == [False, True, True]
    ok, intacto, aviso, archivos = inv["error_escritura"]
    assert (ok, intacto, aviso) == (False, True, True) and not [a for a in archivos if a.endswith(".tmp")]
    assert all(inv[k] for k in ("reabrir_valores_iguales", "reabrir_consultas_iguales", "reabrir_contexto_igual", "reabrir_analisis_activo"))


def test_excel_cinco_hojas_y_formulas_round_half_up(recorrido):
    excel = recorrido[1]["excel_sesion"]
    assert excel["hojas"] == g.HOJAS_EXCEL
    formulas = [v for _, v in excel["contenido"]["Valores proyectados"]["celdas"] if isinstance(v, str) and v.startswith("=")]
    assert any(f.startswith("=1+ROUND((") for f in formulas) and any(f.startswith("=ROUND((") for f in formulas)


def test_version_1_1_2_y_mae_no_presentado_como_intervalo(recorrido):
    datos = recorrido[1]
    textos = (datos["pdf_sesion"]["texto"] + datos["docx_sesion"]["parrafos"] + datos["informe_proyeccion"]["pdf"]["texto"]
              + datos["informe_proyeccion"]["docx"]["parrafos"])
    assert "1.1.2" in datos["pdf_sesion"]["texto"] and "1.1.2" in datos["informe_proyeccion"]["pdf"]["texto"]  # «Versión de SAVIP»
    assert "1.1.2" in _celdas(datos["docx_sesion"]) and "1.1.2" in _celdas(datos["informe_proyeccion"]["docx"])
    for linea in textos:
        if "MAE" in linea and "intervalo de confianza" in linea.lower():
            assert any(n in linea.lower() for n in ("no es", "no corresponde")), f"±MAE presentado como intervalo de confianza: {linea}"


def test_sesion_grande_determinista_abre_sin_motor(recorrido):
    """300 actividades derivadas de la sesión del recorrido (IDs deterministas): abre completa, sin motor."""
    from unittest.mock import patch
    from PySide6.QtWidgets import QFileDialog, QMessageBox
    from app_icociv.interfaz.controladores.controlador_principal import ControladorPrincipal
    from app_icociv.interfaz.ventana_principal import VentanaPrincipal
    from app_icociv.persistencia.gestor_sesiones import guardar_sesion

    carpeta = recorrido[0]
    datos = json.loads((carpeta / "sesion_fase0.json").read_text(encoding="utf-8"))
    base = datos["proyecciones_icociv"]["valores"]
    grandes = []
    for i in range(100):
        for r in base:
            copia = deepcopy(r); copia["calculo_id"] = f"{i:04d}{r['calculo_id'][4:]}"; copia["item"] = f"{r['item']} #{i:03d}"
            grandes.append(copia)
    datos["proyecciones_icociv"]["valores"] = grandes
    for analisis in datos["proyecciones_icociv"]["historial_analisis"]:  # la sesión valida estos vínculos al abrir
        analisis["registros_ids"] = [r["calculo_id"] for r in grandes if r.get("analisis_id") == analisis["id"]]
    ruta = guardar_sesion(carpeta / "sesion_grande.json", datos)
    v = VentanaPrincipal()
    try:
        g._cargar(v, carpeta / "anex-ICOCIV-sintetico-dic2026.xlsx")
        inicio = time.monotonic()
        with patch.object(QFileDialog, "getOpenFileName", return_value=(str(ruta), "")), \
             patch.object(ControladorPrincipal, "ejecutar_analisis", side_effect=AssertionError("motor")), \
             patch.object(QMessageBox, "warning", side_effect=AssertionError("aviso modal al abrir")), \
             patch.object(QMessageBox, "critical", side_effect=AssertionError("error modal al abrir")):
            v.abrir_sesion(); g._esperar(v, lambda: True)
        segundos = time.monotonic() - inicio
        w = v.widget_proyecciones
        assert len(w.valores) == 300 and w.modelo_valores.rowCount() == 300
        assert sum(r["valor_proyectado"] for r in w.valores) == pytest.approx(100 * sum(r["valor_proyectado"] for r in base), rel=1e-12)
        assert segundos < 120, f"abrir 300 actividades tardó {segundos:.1f} s"
    finally:
        with patch.object(v, "_decidir_cierre", return_value="descartar"):
            v.close()
