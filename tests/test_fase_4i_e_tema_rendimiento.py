"""Fase 4I-E: botón de tema visible en pantalla dividida y deserializador de snapshots equivalente al original."""
import os
import tarfile
import types
from copy import deepcopy
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import numpy as np
import pandas as pd
from PySide6.QtGui import QFontDatabase
from PySide6.QtTest import QTest

from tests.test_slider_comparacion_historica_fase_4d import APP, cargar, reales
from tests.test_proyecciones_redisenio_visual import ventana_de_prueba
from app_icociv.persistencia.historial_icociv import recuperar_resultado

ROOT = Path(__file__).resolve().parents[1]
for f in ("segoeui.ttf", "segoeuib.ttf", "seguisb.ttf", "seguisym.ttf"):
    QFontDatabase.addApplicationFont(str(Path("C:/Windows/Fonts") / f))
NOMBRE_LARGO = "anex-ICOCIV-IndicesCostosConstruccionInfraestructura-2026-agosto-revisado-final.xlsx"


def test_boton_de_tema_nunca_queda_vacio_en_pantalla_dividida():
    v = ventana_de_prueba(); v.show(); w = cargar(v)
    try:
        v.cabecera_app.establecer_estado_archivo(NOMBRE_LARGO, "cargado")
        b = v.boton_tema_toggle
        w.cantidad.setValue(7); w.precio_base.setValue(1234.5); borrador = w._datos_calculadora()
        for _ in range(2):
            for ancho in (1920, 1366, 1200, 1050, 950, 850, 683, 1920):
                v.resize(ancho, 800); QTest.qWait(150)
                # Switch de tema (pastilla sol/luna, sin texto): tamaño fijo y siempre dentro de la ventana.
                assert b.size() == b.sizeHint() and b.width() >= 40, (ancho, b.width(), b.sizeHint().width())
                assert b.isVisible() and b.mapTo(v, b.rect().topRight()).x() <= v.width()
                # El nombre del Excel se acorta con puntos suspensivos y conserva el nombre completo en el tooltip.
                e = v.cabecera_app.estado_archivo
                assert e.toolTip() == NOMBRE_LARGO and e.width() <= 320 and ("…" in e.text() or e.text() == NOMBRE_LARGO)
            # Alternar el tema en media pantalla: el botón refleja el tema y nada más cambia.
            v.resize(950, 800); QTest.qWait(150)
            tema = v.tema_actual; b.click(); QTest.qWait(150)
            assert v.tema_actual != tema and b.tema == v.tema_actual and b.isChecked() == (v.tema_actual == "oscuro")
            assert w._datos_calculadora() == borrador
    finally:
        v.close()


def _igual(a, b):
    if type(a) is not type(b):
        return False
    if isinstance(a, pd.DataFrame):
        return list(a.columns) == list(b.columns) and list(a.dtypes) == list(b.dtypes) and list(a.index) == list(b.index) and a.equals(b)
    if isinstance(a, np.ndarray):
        return a.dtype == b.dtype and np.array_equal(a, b, equal_nan=a.dtype.kind == "f")
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(_igual(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)):
        return len(a) == len(b) and all(_igual(x, y) for x, y in zip(a, b))
    if isinstance(a, float) and a != a:
        return b != b
    return a == b


def test_snapshots_identicos_al_deserializador_original():
    respaldo = ROOT / "docs/fase_4i_e/respaldo_inicio/fuentes_tests_inicio.tar"
    src = tarfile.open(respaldo).extractfile("app_icociv/persistencia/historial_icociv.py").read().decode()
    m = types.ModuleType("historial_original"); exec(src, m.__dict__)
    for a in reales()["historial_analisis"]:
        assert _igual(m.recuperar_resultado(deepcopy(a["resultado"])), recuperar_resultado(deepcopy(a["resultado"])))
    # Columnas repetidas y valores no finitos: camino original.
    from app_icociv.persistencia.historial_icociv import serializar_resultado
    for df in (pd.DataFrame([[1, 2.5], [3, float("nan")]], columns=["a", "a"]),
               pd.DataFrame({"Periodo": ["2026_1", "2026_2"], "Indice": [100.0, float("nan")], "n": [1, 2]})):
        s = serializar_resultado({"t": df, "x": [1, None, "z", float("inf")], "arr": np.array([1.5, np.nan])})
        resultados = []
        for funcion in (m.recuperar_resultado, recuperar_resultado):
            try:
                resultados.append(("ok", funcion(deepcopy(s))))
            except Exception as error:  # mismo comportamiento ante datos que el original no admite
                resultados.append(("error", type(error)))
        assert resultados[0][0] == resultados[1][0] and _igual(resultados[0][1], resultados[1][1])
