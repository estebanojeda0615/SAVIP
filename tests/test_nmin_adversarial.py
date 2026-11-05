"""Pruebas adversariales del primer origen derivado (microauditoria P0-E, 12-08-2026).

QUE FIJA ESTE ARCHIVO. La sesion anterior cerro P0-E con
`N0 = max_m N_min(m) = 6`, justificando cada `N_min` por conteo de parametros:
«un parametro esta identificado cuando el numero de ecuaciones supera al de
incognitas». La microauditoria midio ese supuesto y **lo refuto** para los dos
modelos que fijan el maximo.

Estas pruebas NO afirman que N0=6 sea correcto. Hacen lo contrario: **dejan
clavado lo que se midio**, para que nadie vuelva a apoyarse en el conteo de
parametros sin volver a medir. Un test verde no sustituye a una fuente.

Ejecucion:
    python tests/test_nmin_adversarial.py
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import numpy as np

from app_icociv.estadistica import criterios as CR
from app_icociv.estadistica import modelos_interpretables as MI
from app_icociv.proyeccion import servicio_proyeccion as SP
from app_icociv.validacion import backtesting as BT

TOL = 1e-6


def _serie_tendencia(n: int, semilla: int = 0) -> tuple[np.ndarray, np.ndarray]:
    g = np.random.default_rng(semilla)
    t = np.arange(1.0, n + 1.0)
    return t, 100.0 + 1.2 * t + g.normal(0, 0.6, n)


# --- 1 y 2: Holt en su N_min declarado NO estima todos sus parametros --------

def test_holt_amortiguado_en_n6_deja_parametros_en_la_frontera() -> None:
    """HALLAZGO, no aspiracion: en n=6 alpha y beta* caen en la cota inferior.

    Con cinco parametros nominales, dos de ellos no proceden de los datos sino
    del borde del dominio admisible. Holt colapsa a una recta fija. Si algun dia
    esta prueba falla porque la solucion pasa a ser interior, hay que revisar
    `P0E_MICROAUDITORIA_HOLT.md`: cambiaria la base del veredicto.
    """
    en_frontera = 0
    for semilla in range(8):
        _, y = _serie_tendencia(6, semilla)
        MI._MEMORIA_HOLT.clear()
        alpha, beta, _phi, _l0, _b0 = MI.estimar_parametros_holt(y, amortiguado=True)
        if abs(alpha - MI.HOLT_ALPHA_MIN) < TOL and abs(beta - MI.HOLT_BETA_MIN) < TOL:
            en_frontera += 1
    assert en_frontera == 8, (
        f"alpha y beta* interiores en {8 - en_frontera}/8 casos; el hallazgo de la "
        "microauditoria era 8/8 en la frontera"
    )


def test_holt_lineal_en_n5_deja_parametros_en_la_frontera() -> None:
    en_frontera = 0
    for semilla in range(8):
        _, y = _serie_tendencia(5, semilla)
        MI._MEMORIA_HOLT.clear()
        alpha, beta, _phi, _l0, _b0 = MI.estimar_parametros_holt(y, amortiguado=False)
        if abs(alpha - MI.HOLT_ALPHA_MIN) < TOL and abs(beta - MI.HOLT_BETA_MIN) < TOL:
            en_frontera += 1
    assert en_frontera == 8, f"solo {en_frontera}/8 en la frontera"


def test_holt_en_n6_no_interpola() -> None:
    """La objecion por interpolacion NO se sostiene: el SSE no se anula."""
    for semilla in range(5):
        _, y = _serie_tendencia(6, semilla)
        MI._MEMORIA_HOLT.clear()
        a, b, phi, _, _ = MI.estimar_parametros_holt(y, amortiguado=True)
        sse, _, _ = MI._holt_sse_con_estados_optimos(y, a, b, phi)
        assert sse / (6 * float(np.var(y, ddof=1))) > 1e-4, "el SSE se anula: interpolacion"


# --- 3, 4 y 5: el resto del catalogo en su N_min declarado ------------------

def test_huber_y_regresiones_ajustan_por_debajo_de_su_nmin_declarado() -> None:
    """El N_min de Huber y de las regresiones no es una barrera real.

    Se declararon 4 y 3 por el conteo `k+1`. Medido: ajustan y predicen desde 2.
    No decide -no son el maximo- pero la ficha describe una restriccion que no
    existe.
    """
    for nombre in ("huber", "lineal", "logaritmico", "exponencial_log_lineal"):
        t, y = _serie_tendencia(2)
        modelo = MI.ajustar_modelo_interpretable(nombre, t, y)
        assert np.isfinite(float(modelo["predict"]([8.0])[0])), nombre


def test_variacion_respeta_exactamente_su_nmin() -> None:
    """Los unicos dos modelos cuyo minimo declarado coincide con el impuesto."""
    for nombre in ("variacion_lineal", "log_variacion"):
        t, y = _serie_tendencia(3)
        try:
            MI.ajustar_modelo_interpretable(nombre, t, y)
            raise AssertionError(f"{nombre} ajusto con n=3; su minimo declarado es 4")
        except ValueError:
            pass
        t, y = _serie_tendencia(4)
        MI.ajustar_modelo_interpretable(nombre, t, y)


def test_naive_declara_un_minimo_inalcanzable() -> None:
    """`OBSERVACIONES_MINIMAS_MODELO['naive'] = 1` no lo admite el codigo."""
    assert MI.OBSERVACIONES_MINIMAS_MODELO["naive"] == 1
    t, y = _serie_tendencia(1)
    try:
        MI.ajustar_modelo_interpretable("naive", t, y)
        raise AssertionError("naive ajusto con n=1; la puerta global exige 2")
    except ValueError:
        pass


# --- 7 y 8: invariantes que SI se sostienen (el 6 se retiró en el lote 2D-2) ---

# Lote 2D-2: retirado `test_muestra_comun_intacta_desde_el_primer_origen`, que medía la muestra común con el
# extractor heredado `_errores_oos_por_par` (eliminado). La muestra rectangular completa W*×24 de la ruta productiva
# la fija test_fase1a_selector_rectangular.py::test_la_ruta_productiva_usa_el_selector_rectangular_y_ningun_selector_retirado
# (pares comunes = pares esperados = W*×24, 21 candidatos); los orígenes del rectángulo, test_metodologia_n0_12_h24.py::
# test_c_rectangulo_n65_da_w_estrella_30_y_mismos_origenes_por_h.


def test_anti_leakage_y_pares_por_horizonte() -> None:
    import pandas as pd

    n = 40
    n0 = MI.observaciones_minimas_catalogo(SP._catalogo_activo())
    periodos = [f"{2021 + i // 12}_{i % 12 + 1}" for i in range(n)]
    _, y = _serie_tendencia(n, 6)
    serie = pd.DataFrame({"Periodo": periodos, "Indice": y})
    for h in (1, 5):
        r = BT.ejecutar_backtesting(serie, horizonte=h, modelo="lineal")
        assert r["iteraciones"] == n - n0 - h + 1
        pred = r["predicciones"]
        for obs, t_obj in zip(pred["Observaciones_entrenamiento"], pred["t"]):
            assert int(obs) <= int(t_obj) - h + 1, "fuga: el entrenamiento alcanza al objetivo"


# --- 9 y 10: no reaparecen los literales; P0-A/B/D intactos -----------------

def test_no_reaparecen_18_ni_060() -> None:
    for nombre in ("MIN_OBS_WF_INICIAL", "PROPORCION_ENTRENAMIENTO_WF"):
        assert not hasattr(CR, nombre), nombre
    for modulo in (BT, SP):
        fuente = inspect.getsource(modulo)
        assert "PROPORCION_ENTRENAMIENTO_WF" not in fuente
        assert "MIN_OBS_WF_INICIAL" not in fuente


def p0d_en_el_selector_vigente() -> None:
    """P0-D sobre el selector que usa la ruta productiva, con las propiedades canónicas de Fase 1A."""
    from tests.test_fase1a_selector_rectangular import (
        SELECTOR,
        p_empate_primer_candidato_del_banco,
        p_invariante_al_orden_de_entrada,
        p_sse_exacto_decide_una_ulp,
    )
    for propiedad in (p_sse_exacto_decide_una_ulp, p_invariante_al_orden_de_entrada, p_empate_primer_candidato_del_banco):
        assert propiedad(SELECTOR), propiedad.__name__


def test_p0a_p0b_p0d_intactos() -> None:
    """P0-A, P0-B y P0-D siguen cerrados. P0-D, por comportamiento sobre el selector vigente."""
    assert "seleccionar_modelo_por_evidencia(" not in inspect.getsource(SP)
    assert SP.MODELOS_PARAMETRO_SIN_SUSTENTO == {"promedio_movil", "variacion_reciente"}
    p0d_en_el_selector_vigente()


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
            except Exception as exc:  # noqa: BLE001
                fallos += 1
                print(f"  ERROR {nombre}: {type(exc).__name__}: {exc}")
    print(f"\n{'todas las pruebas pasan' if not fallos else f'{fallos} fallidas'}")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(_ejecutar())
