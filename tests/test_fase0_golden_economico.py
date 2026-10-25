"""Fase 0 · Golden Master de las reglas económicas: porcentaje y factor ROUND_HALF_UP, Base = P − A, R,
valor proyectado, rechazos de entradas inválidas, factor legado y empalme ICCP→ICOCIV (datos ICCP
internos del repositorio + índices ICOCIV sintéticos). Esperados en golden/economico.json."""

import pytest

from tests.fixtures.fase0 import captura as c

GOLDEN = c.leer_golden("economico.json")
OBTENIDO = c.capturar_economico()


@pytest.mark.parametrize("seccion", ["factores", "importes", "rechazos", "factor_legado", "empalme"])
def test_golden_economico(seccion):
    assert c.diferencias(GOLDEN[seccion], OBTENIDO[seccion], seccion) == []


def test_factor_es_exacto_en_decimal():
    """p y F se comparan como texto Decimal: sin tolerancia (la regla es exacta)."""
    assert [(f["p"], f["F"]) for f in OBTENIDO["factores"]] == [(f["p"], f["F"]) for f in GOLDEN["factores"]]
