"""P0-D: el ganador no puede depender del redondeo del RMSE (D4, D11-D13 tras el lote 2D-2).

La revision independiente reabrio P0-D porque

    hypot(e_1,...,e_n) / sqrt(n)   y   sqrt(sum(e_i**2) / n)

son algebraicamente iguales pero **no redondean igual**. Medido: con dos
candidatos que difieren en una ULP en un solo error, la forma directa distingue
cual es menor y `hypot` devuelve **el mismo flotante para los dos**, creando un
empate que matematicamente no existe. Con el desempate por orden de aparicion,
ese empate artificial hace ganar al primer candidato del banco en lugar de al de
menor error real.

La solucion NO es una tolerancia. Es una derivacion: como la raiz cuadrada es
estrictamente creciente y el factor 1/n es comun a todos los candidatos sobre la
misma muestra comun,

    argmin RMSE = argmin MSE = argmin SSE

de modo que la decision puede tomarse sobre la suma de cuadrados calculada de
forma EXACTA. Cada flotante IEEE-754 es un racional con denominador potencia de
dos, y `float.as_integer_ratio()` lo entrega sin perdida.

Ejecucion directa, sin pytest:

    python tests/test_p0d_rmse_orden_exacto.py
"""
from __future__ import annotations

import inspect
import re
import struct
import sys
import traceback
from fractions import Fraction
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from app_icociv.proyeccion.servicio_proyeccion import (  # noqa: E402
    _seleccionar_modelo_rectangular,
    _sse_exacto,
)

# Lote 2D-2: retiradas D1-D3 y D5-D10, que ejercitaban el selector heredado `seleccionar_modelo_por_rmse_oos_global`
# (eliminado). Sus propiedades las fija sobre el selector vigente tests/test_fase1a_selector_rectangular.py; detalle en
# docs/fase_v112_antislop_02d_lote2_equivalencia_original_thermos/03_G2_MATRIZ_PRUEBAS_Y_CRITERIO_CSEL001.md.
# Quedan D4 y D13 sobre `_sse_exacto` y D11-D12 sobre el selector vigente.


def test_d4_permutar_la_muestra_comun_no_cambia_nada() -> None:
    """D4. El SSE exacto es invariante al orden de iteracion de S_common."""
    generador = np.random.default_rng(11)
    valores = [float(x) for x in generador.uniform(-4, 4, 40)]
    referencia = _sse_exacto(valores)
    for _ in range(50):
        permutado = list(valores)
        generador.shuffle(permutado)
        assert _sse_exacto(permutado) == referencia


def _lineas_ejecutables(funcion) -> str:
    """Codigo de la funcion sin comentarios ni docstring.

    Buscar cadenas sobre la fuente completa da falsos positivos: los docstrings de
    estas dos funciones **describen** las reglas retiradas -la ponderacion 1/h y la
    prohibicion de `isclose`- precisamente para dejar constancia de que no estan.
    Lo que hay que inspeccionar es lo que se ejecuta.
    """
    fuente = inspect.getsource(funcion)
    sin_docstring = re.sub(r'"""(?:.|\n)*?"""', "", fuente)
    return "\n".join(
        linea.split("#", 1)[0]
        for linea in sin_docstring.splitlines()
        if linea.strip() and not linea.strip().startswith("#")
    )


def test_d11_los_pesos_siguen_siendo_uniformes() -> None:
    """D11. Ninguna ponderacion por horizonte ni por antiguedad."""
    ejecutable = _lineas_ejecutables(_seleccionar_modelo_rectangular).lower()
    for sospechoso in ("1/h", "1 / h", "peso", "ponder"):
        assert sospechoso not in ejecutable, sospechoso
    # Dos errores iguales en horizontes distintos pesan lo mismo.
    assert _sse_exacto([2.0, 0.0]) == _sse_exacto([0.0, 2.0])


def test_d12_la_decision_no_usa_ninguna_tolerancia() -> None:
    """D12. Sin epsilon, sin isclose, sin redondeo en la ruta de decision."""
    for funcion in (_seleccionar_modelo_rectangular, _sse_exacto):
        ejecutable = _lineas_ejecutables(funcion)
        for prohibido in ("isclose", "epsilon", "EPS", "round(", "tolerancia",
                          "atol", "rtol", "Decimal"):
            assert prohibido not in ejecutable, (funcion.__name__, prohibido)


def test_d13_el_acumulador_entero_coincide_con_fraction_puro() -> None:
    """El atajo de rendimiento debe dar EXACTAMENTE lo mismo que Fraction."""
    generador = np.random.default_rng(3)
    for _ in range(200):
        valores = [float(x) for x in generador.uniform(-1e6, 1e6, 7)]
        referencia = sum((Fraction(v) ** 2 for v in valores), Fraction(0))
        assert _sse_exacto(valores) == referencia
    # Y con magnitudes extremas.
    extremos = [1e-300, 1e300, -1e150, 0.0]
    assert _sse_exacto(extremos) == sum((Fraction(v) ** 2 for v in extremos), Fraction(0))


def _ejecutar() -> int:
    pruebas = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    fallos = 0
    for prueba in pruebas:
        try:
            prueba()
            print(f"  OK    {prueba.__name__}")
        except Exception:
            fallos += 1
            print(f"  FALLA {prueba.__name__}")
            traceback.print_exc()
    print(f"\n{len(pruebas) - fallos}/{len(pruebas)} aprobadas")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(_ejecutar())
