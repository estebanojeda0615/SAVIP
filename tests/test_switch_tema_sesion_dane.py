"""Switch claro/oscuro tipo pastilla y apertura de sesiones con Excel DANE obligatorio (corte igual o posterior)."""

import json
import os
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QFileDialog, QMessageBox

from tests.test_slider_comparacion_historica_fase_4d import APP, reales
from tests.test_proyecciones_redisenio_visual import ventana_de_prueba
from app_icociv.interfaz.ventana_principal import TEXTO_SIN_DANE, VentanaPrincipal, corte_requerido_sesion

ROOT = Path(__file__).resolve().parents[1]
ANEXO = ROOT / "docs/fase_4d_slider/fixtures/ANEXO_SINTETICO.xlsx"  # periodos 2024-01 … 2026-12
MOTOR = "app_icociv.interfaz.controladores.controlador_principal.ControladorPrincipal.ejecutar_analisis"
NOMBRE_LARGO = "anex-ICOCIV-IndicesCostosConstruccionInfraestructura-2026-agosto-revisado-final.xlsx"


def _ventana_con_dane(hasta=None):
    v = VentanaPrincipal(); v.resize(1366, 800); v.show()
    v._archivo_cargado(v.controlador.cargar_archivo(str(ANEXO)))
    if hasta:  # un anexo más antiguo es el mismo anexo con menos periodos publicados
        v.controlador.periodos = v.controlador.periodos[:v.controlador.periodos.index(hasta) + 1]
    APP.processEvents()
    return v


def _sesion(tmp_path, **extra):
    datos = {"usuario": "QA", "archivo_excel": "C:/ruta/que/no/existe/anexo_original.xlsx", "proyecciones_icociv": reales(), **extra}
    ruta = tmp_path / "sesion.json"; ruta.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    return ruta, datos


def _abrir(v, ruta):
    with patch.object(QFileDialog, "getOpenFileName", return_value=(str(ruta), "")) as dialogo, \
         patch.object(QMessageBox, "warning") as aviso, patch(MOTOR, side_effect=AssertionError("motor")), \
         patch.object(VentanaPrincipal, "_cargar_archivo", side_effect=AssertionError("no debe abrir el Excel de la sesión")):
        v.abrir_sesion()
        while v._operacion_sesion: APP.processEvents()
    return dialogo, aviso


def test_switch_tema_pastilla_alterna_y_no_se_recorta():
    v = ventana_de_prueba(); v.show()
    try:
        v.cabecera_app.establecer_estado_archivo(NOMBRE_LARGO, "cargado")
        s = v.boton_tema_toggle
        assert s.text() == "" and s.isCheckable()
        borrador = v.widget_proyecciones._datos_calculadora()
        for ancho in (1920, 1366, 1050, 960, 850, 683, 640, 1920):
            v.resize(ancho, 800); QTest.qWait(120)
            assert s.isVisible() and s.size() == s.sizeHint(), (ancho, s.size())
            assert s.mapTo(v, s.rect().topRight()).x() <= v.width(), ancho
            e = v.cabecera_app.estado_archivo
            assert e.toolTip() == NOMBRE_LARGO and e.width() <= 320 and "…" in e.text()
            tema = v.tema_actual; s.click(); QTest.qWait(60)
            assert v.tema_actual != tema and s.isChecked() == (v.tema_actual == "oscuro") and s.tema == v.tema_actual
            assert v.accion_modo_oscuro.isChecked() == s.isChecked()
            assert ("oscuro" if s.isChecked() else "claro") in s.toolTip().lower()
        v.accion_modo_oscuro.trigger(); assert s.isChecked() == (v.tema_actual == "oscuro")  # Vista › Modo oscuro sigue
        assert v.widget_proyecciones._datos_calculadora() == borrador
    finally:
        v.close()


def test_sin_dane_no_se_abre_sesion(tmp_path):
    v = VentanaPrincipal(); ruta, _ = _sesion(tmp_path)
    try:
        dialogo, aviso = _abrir(v, ruta)
        assert not dialogo.called and aviso.call_args[0][2] == TEXTO_SIN_DANE
        assert not v.widget_proyecciones.historial and v.sesion_pendiente is None
    finally:
        v.close()


def test_dane_igual_abre_sin_recalcular_ni_alterar(tmp_path):
    v = _ventana_con_dane(); ruta, datos = _sesion(tmp_path)
    try:
        assert corte_requerido_sesion(datos) == "2026-12" and v._corte_dane_cargado() == "2026-12"
        dialogo, aviso = _abrir(v, ruta)
        assert dialogo.called and not aviso.called
        w = v.widget_proyecciones
        assert [a["id"] for a in w.historial] == [a["id"] for a in datos["proyecciones_icociv"]["historial_analisis"]]
        assert w.valores == datos["proyecciones_icociv"]["valores"] and v.controlador.ruta_archivo == ANEXO
        guardado = deepcopy(w.datos_sesion()); guardado.pop("comparacion_historica", None)
        esperado = deepcopy(datos["proyecciones_icociv"]); esperado.pop("comparacion_historica", None)
        assert guardado["historial_analisis"] == esperado["historial_analisis"]
    finally:
        v.close()


def test_dane_posterior_abre_y_dane_antiguo_no(tmp_path):
    ruta, datos = _sesion(tmp_path, corte_dane="2026-08")
    v = _ventana_con_dane()  # 2026-12 ≥ 2026-08
    try:
        _, aviso = _abrir(v, ruta)
        assert not aviso.called and v.widget_proyecciones.historial
    finally:
        v.close()
    v = _ventana_con_dane(hasta="2026_7")  # 2026-07 < 2026-08
    try:
        _, aviso = _abrir(v, ruta)
        assert aviso.call_args[0][2] == ("La sesión requiere un archivo ICOCIV con fecha base 2026-08 o posterior. El archivo "
                                         "actualmente cargado corresponde a 2026-07. Cargue un archivo compatible para continuar.")
        assert not v.widget_proyecciones.historial and v.sesion_pendiente is None
    finally:
        v.close()


def test_guardar_registra_corte_dane(tmp_path):
    v = _ventana_con_dane(); ruta, _ = _sesion(tmp_path)
    try:
        _abrir(v, ruta)
        salida = tmp_path / "guardada.json"
        with patch.object(v, "_solicitar_usuario", return_value="QA"), \
             patch.object(QFileDialog, "getSaveFileName", return_value=(str(salida), "")):
            v.guardar_sesion_actual(como=True)
        assert json.loads(salida.read_text(encoding="utf-8"))["corte_dane"] == "2026-12"
    finally:
        v.close()
