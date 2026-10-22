"""Fase 4I-H: el estado DANE de la cabecera nunca muestra la leyenda fija recortada («Sin arch… cargado»)."""

import os
import shutil
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QFontDatabase
from PySide6.QtTest import QTest

from tests.test_slider_comparacion_historica_fase_4d import APP
from tests.test_switch_tema_sesion_dane import ANEXO
from app_icociv.interfaz.ventana_principal import VentanaPrincipal

for _fuente in ("segoeui.ttf", "segoeuib.ttf", "seguisb.ttf", "seguisym.ttf"):  # misma fuente que en Windows
    QFontDatabase.addApplicationFont(str(Path("C:/Windows/Fonts") / _fuente))

ANCHOS = (1920, 1366, 1200, 960, 850, 683, 640)
SECUENCIA = (1920, 683, 960, 1920)


def _geometria_ok(v):
    e, s = v.cabecera_app.estado_archivo, v.boton_tema_toggle
    derecha_estado = e.mapTo(v, e.rect().topRight()).x()
    return derecha_estado < s.mapTo(v, s.rect().topLeft()).x() and s.mapTo(v, s.rect().topRight()).x() <= v.width()


def test_sin_dane_leyenda_completa_o_corta_nunca_recortada():
    v = VentanaPrincipal(); v.show()
    try:
        e = v.cabecera_app.estado_archivo
        for tema in ("claro", "oscuro"):
            v._aplicar_tema(tema, persistir=False)
            for ancho in (*ANCHOS, *SECUENCIA, *SECUENCIA):  # sin reiniciar: se reexpande al ampliar
                v.resize(ancho, 800); QTest.qWait(450)  # la barra lateral termina de contraerse/expandirse
                texto = e.text()
                assert texto in ("Sin archivo cargado", "Sin archivo") or (texto == "" and not e.pixmap().isNull()), (tema, ancho, texto)
                assert "…" not in texto and "..." not in texto
                assert e.fontMetrics().horizontalAdvance(texto) <= e.contentsRect().width()  # cabe de verdad
                assert e.toolTip() == "Sin archivo DANE cargado" == e.accessibleName()
                assert _geometria_ok(v), (tema, ancho)
                # La leyenda completa cabe en todos los anchos admitidos (mínimo de ventana 640 px).
                assert texto == "Sin archivo cargado", (tema, ancho, texto, e.width())
            # Switch intacto: alterna el tema sin tocar el estado
            tema_antes = v.tema_actual; v.boton_tema_toggle.click(); QTest.qWait(80)
            assert v.tema_actual != tema_antes and e.text() in ("Sin archivo cargado", "Sin archivo")
    finally:
        v.close()


def test_ultimo_recurso_icono_con_tooltip():
    v = VentanaPrincipal(); v.show()
    try:
        e = v.cabecera_app.estado_archivo
        e.setFixedWidth(40); QTest.qWait(50)  # más estrecho de lo que el diseño permite
        assert e.text() == "" and not e.pixmap().isNull() and e.toolTip() == "Sin archivo DANE cargado"
        e.setMinimumWidth(0); e.setMaximumWidth(16777215); v.resize(1920, 800); QTest.qWait(80)
        assert e.text() == "Sin archivo cargado"
    finally:
        v.close()


def test_dane_cargado_nombre_legible_que_se_reexpande(tmp_path):
    v = VentanaPrincipal(); v.show()
    try:
        e = v.cabecera_app.estado_archivo
        for nombre in ("anex-ICOCIV-ago2026.xlsx", "anex-ICOCIV-IndicesCostosConstruccionInfraestructura-revisado-ago2026.xlsx"):
            v.cabecera_app.establecer_estado_archivo(nombre, "cargado")
            for tema in ("claro", "oscuro"):
                v._aplicar_tema(tema, persistir=False)
                for ancho in (*ANCHOS, *SECUENCIA):
                    v.resize(ancho, 800); QTest.qWait(450)  # la barra lateral termina de contraerse/expandirse
                    assert e.toolTip() == nombre and e.width() <= 320 and _geometria_ok(v)
                    assert e.fontMetrics().horizontalAdvance(e.text()) <= e.contentsRect().width()
                    assert e.text() == nombre or ("…" in e.text() and e.text().endswith(".xlsx") and len(e.text()) >= 14), e.text()
                v.resize(1920, 800); QTest.qWait(80)
                if len(nombre) < 30:
                    assert e.text() == nombre  # el nombre corto completo vuelve al ampliar
    finally:
        v.close()


def test_indicador_sigue_al_dane_activo_al_cerrar_y_cambiar(tmp_path):
    v = VentanaPrincipal(); v.show()
    try:
        e = v.cabecera_app.estado_archivo
        v._archivo_cargado(v.controlador.cargar_archivo(str(ANEXO))); QTest.qWait(50)
        assert e.toolTip() == ANEXO.name and e.text() == ANEXO.name
        v.widget_proyecciones.nombre_proyecto.setText("trabajo")
        with patch.object(v, "_decidir_cierre", return_value="descartar"):
            assert v.cerrar_sesion()
        assert e.toolTip() == ANEXO.name  # cerrar la sesión no descarga el DANE
        otro = tmp_path / "anex-ICOCIV-sep2026.xlsx"; shutil.copy(ANEXO, otro)
        v._archivo_cargado(v.controlador.cargar_archivo(str(otro))); QTest.qWait(50)
        assert e.toolTip() == otro.name and e.text() == otro.name
    finally:
        v.close()
