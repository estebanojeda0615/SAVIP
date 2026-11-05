"""Seleccion por RMSE fuera de muestra global (C-SEL-001, 08-08-2026).

Cierra H-9, la ultima heuristica decisoria del producto.

QUE SE RETIRA. Hasta esta fecha el modelo lo elegia
`_modelo_trayectoria_consistente`: promedio del RMSE relativo al mejor de cada
horizonte, **ponderado con peso 1/h**. El peso no tenia fuente -su justificacion
era operativa, «la evidencia de corto plazo es mas confiable y mas usada»- y
cambiaba el modelo entregado. Medido sobre las diez series del anexo de mayo de
2026, la regla nueva y la vieja discrepan en **una**.

QUE ENTRA.

    RMSE_global(m) = sqrt( SUM_{(t,h) in S} e(m,t,h)^2 / |S| )
    m* = argmin_m RMSE_global(m)

con ``S`` la muestra comun: los pares (objetivo, horizonte) en los que **todos**
los candidatos tienen error finito. Sin parametros libres, sin umbrales, sin
imputacion y sin minimos de tamano.

PONDERACION IMPLICITA, DECLARADA. Cada observacion pesa igual, pero los
horizontes largos aportan errores mayores: sobre el anexo, h=18 pone el 2,6 % de
las observaciones y hasta el 8,8 % de la suma de cuadrados. El peso lo pone la
magnitud medida, no una constante elegida. Es la direccion contraria a 1/h y hay
que saberlo al leer el resultado.

Ejecucion:
    python tests/test_seleccion_rmse_global.py
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from app_icociv.proyeccion import servicio_proyeccion as sp  # noqa: E402


# Lote 2D-2: retiradas las 13 pruebas que ejercitaban el selector heredado `seleccionar_modelo_por_rmse_oos_global`
# (eliminado). Sus propiedades las fija sobre el selector vigente tests/test_fase1a_selector_rectangular.py; la
# correspondencia caso a caso está en docs/fase_v112_antislop_02d_lote2_equivalencia_original_thermos/
# 03_G2_MATRIZ_PRUEBAS_Y_CRITERIO_CSEL001.md.


# ======================================================================
# 4. Lo que la regla NO consulta
# ======================================================================
def test_la_regla_no_consulta_umbrales_ni_identidad():
    # Fase 2B y lote 2D-2: se inspecciona el selector que usa la ruta productiva; los heredados se retiraron.
    fuente = inspect.getsource(sp._seleccionar_modelo_rectangular)
    for prohibido in ("UMBRAL_", "TOLERANCIA_", "MIN_ERRORES", "COBERTURA_IC95",
                      "es_benchmark", "MODELOS_BENCHMARK", "estado"):
        assert prohibido not in fuente, prohibido


# `test_no_queda_el_peso_1_h_en_la_ruta_de_seleccion` RETIRADA en la Fase 2B (AS-003): inspeccionaba
# la fuente de `_modelo_consistente_desde_comparativo`, retirada. La ausencia de peso 1/h en el
# selector vigente la prueban `p_pesos_uniformes_por_horizonte` y el mutante `peso_1_h` de
# tests/test_fase1a_selector_rectangular.py.


def test_la_regla_retirada_ya_no_se_invoca_en_la_ruta_productiva():
    """`_modelo_trayectoria_consistente` se retiro en la Fase 2B (AS-003): ni definicion ni llamadas."""
    fuente_modulo = inspect.getsource(sp)
    llamadas = fuente_modulo.count("_modelo_trayectoria_consistente(")
    assert llamadas == 0, (
        f"no debe quedar ninguna llamada ({llamadas})"
    )
    assert not hasattr(sp, "_modelo_trayectoria_consistente")


def _ejecutar() -> int:
    fallos = 0
    for nombre, prueba in sorted(globals().items()):
        if nombre.startswith("test_") and callable(prueba):
            try:
                prueba()
                print(f"  OK   {nombre}")
            except AssertionError as exc:
                fallos += 1
                print(f"  FALLA {nombre}: {exc}")
    print(f"\n{'todas las pruebas pasan' if not fallos else f'{fallos} fallidas'}")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(_ejecutar())
