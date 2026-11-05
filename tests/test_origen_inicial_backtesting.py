"""Origen inicial del backtesting derivado de la estimabilidad (P0-E, 12-08-2026).

QUE SE RETIRA. Hasta esta fecha el primer origen era

    N0 = max( 8, min( max(18, floor(0,60 n)), n-1 ) )

tres literales sin fuente -18, 0,60 y 8- que decidian cuantos origenes existen,
cuantos pares OOS produce cada horizonte, el RMSE global y por tanto **el modelo
que la aplicacion entrega**. La tabla de criterios los publicaba ademas
atribuidos a «Hyndman y Athanasopoulos», atribucion que no resiste la
verificacion: FPP3 5.10, el procedimiento que SAVIP aplica, no da ninguna
proporcion, y la unica del libro -5.8- es 20 % de PRUEBA para una particion
unica, es decir 80 % de entrenamiento, no 60 %.

QUE ENTRA.

    N0 = max sobre los candidatos que compiten de su minimo IDENTIFICABLE

con el minimo de cada modelo DERIVADO de su propia formulacion: un parametro
esta identificado cuando el numero de ecuaciones supera al de incognitas. El
binding es Holt amortiguado -alpha, beta*, phi, l0, b0-, que con cinco errores
de un paso puede anular el SSE con parametros no unicos: la sexta observacion es
la primera que los identifica.

POR QUE EL MAXIMO. `C-SEL-001` compara sobre la muestra comun. Un candidato que
no es estimable en los primeros origenes encoge esa muestra para todos y la
comparacion pasa a decidirse sobre el subconjunto que fija el modelo mas fragil.
El maximo es la condicion de comparabilidad, no una precaucion.

POR QUE EL MINIMO ADMISIBLE. Las fuentes acotan 6 <= N0 <= n-H pero no eligen
dentro del rango. Todo N0 = 6 + delta introduce un delta sin procedencia que
decide el modelo entregado, y REQ 5 y REQ 8 lo prohiben.

LIMITACION DECLARADA. FPP3 5.10 excluye las primeras observaciones «since it is
not possible to obtain a reliable forecast based on a small training set», pero
no operacionaliza «pequeno» y esta remediacion tampoco. Lo que cambia es que el
problema deja de estar oculto en una constante y pasa a estar medido.

Ejecucion:
    python tests/test_origen_inicial_backtesting.py
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import numpy as np
import pandas as pd

from app_icociv.estadistica import criterios as CR
from app_icociv.estadistica import modelos_interpretables as MI
from app_icociv.proyeccion import servicio_proyeccion as SP
from app_icociv.validacion import backtesting as BT

N_SERIE = 65


def _serie(n: int = N_SERIE) -> pd.DataFrame:
    """Serie mensual determinista con tendencia y estacionalidad suave."""
    periodos = []
    anio, mes = 2021, 1
    for _ in range(n):
        periodos.append(f"{anio}_{mes:02d}")
        mes += 1
        if mes == 13:
            anio, mes = anio + 1, 1
    t = np.arange(n, dtype=float)
    indice = 100.0 + 0.8 * t + 1.5 * np.sin(t / 6.0)
    return pd.DataFrame({"Periodo": periodos, "Indice": indice})


# --- 1 y 2: los literales sin fuente ya no existen como decisores -----------

def test_no_existe_literal_18_ni_060_en_criterios() -> None:
    for nombre in ("MIN_OBS_WF_INICIAL", "PROPORCION_ENTRENAMIENTO_WF"):
        assert not hasattr(CR, nombre), (
            f"{nombre} sigue definida: era un literal sin fuente que decidia el primer origen"
        )


def test_ningun_modulo_reintroduce_los_literales() -> None:
    for modulo in (BT, SP):
        fuente = inspect.getsource(modulo)
        assert "PROPORCION_ENTRENAMIENTO_WF" not in fuente, f"{modulo.__name__} reintroduce 0,60"
        assert "MIN_OBS_WF_INICIAL" not in fuente, f"{modulo.__name__} reintroduce 18"


# --- 3: el primer origen se deriva del metodo adoptado ----------------------

def test_minimos_por_modelo_declarados_y_derivados() -> None:
    tabla = MI.OBSERVACIONES_MINIMAS_MODELO
    for nombre in MI.MODELOS_INTERPRETABLES:
        assert nombre in tabla, f"{nombre} no declara su minimo de observaciones"
        assert tabla[nombre] >= 1
    assert tabla["holt_amortiguado"] == 6, "Holt amortiguado tiene 5 parametros: identifica desde 6"
    assert tabla["holt_lineal"] == 5, "Holt lineal tiene 4 parametros: identifica desde 5"
    assert tabla["naive"] == 1, "Naive no estima ningun parametro"


def test_origen_inicial_es_el_maximo_del_catalogo() -> None:
    activos = tuple(m for m in MI.MODELOS_INTERPRETABLES if m not in SP.MODELOS_PARAMETRO_SIN_SUSTENTO)
    esperado = max(MI.OBSERVACIONES_MINIMAS_MODELO[m] for m in activos)
    assert MI.observaciones_minimas_catalogo(activos) == esperado
    assert BT._entrenamiento_inicial(N_SERIE, None, activos) == esperado, (
        "el primer origen debe ser el maximo de los minimos, no una proporcion"
    )


def test_origen_inicial_no_depende_de_la_longitud_de_la_serie() -> None:
    """La regla retirada crecia con n; la derivada no: el minimo es del MODELO."""
    valores = {BT._entrenamiento_inicial(n, None, None) for n in (40, 65, 120, 400)}
    assert len(valores) == 1, f"el primer origen sigue dependiendo de n: {valores}"


def test_techo_derivado_por_disponibilidad() -> None:
    """N0 <= n-1: sin observacion posterior no existe ningun par (t,h)."""
    assert BT._entrenamiento_inicial(4, None, None) == 3


def test_una_sola_definicion_del_primer_origen() -> None:
    """La copia de servicio_proyeccion debe coincidir con la de backtesting."""
    for n in (12, 20, 40, 65, 120):
        rejilla = SP._limites_auditoria_horizontes(n)[0]
        assert rejilla == BT._entrenamiento_inicial(n, None, None), (
            f"n={n}: la rejilla usa un primer origen distinto al del backtesting"
        )


# --- 4: todos los candidatos se estiman en el primer origen -----------------

def test_todos_los_candidatos_estimables_en_el_primer_origen() -> None:
    activos = tuple(m for m in MI.MODELOS_INTERPRETABLES if m not in SP.MODELOS_PARAMETRO_SIN_SUSTENTO)
    n0 = MI.observaciones_minimas_catalogo(activos)
    serie = _serie()
    t = np.arange(n0, dtype=float)
    y = serie["Indice"].to_numpy(dtype=float)[:n0]
    for nombre in activos:
        MI.ajustar_modelo_interpretable(nombre, t, y)  # no debe levantar excepcion


# --- 5: un solo origen para todos los modelos -------------------------------

def test_mismo_origen_inicial_para_todos_los_modelos() -> None:
    activos = tuple(m for m in MI.MODELOS_INTERPRETABLES if m not in SP.MODELOS_PARAMETRO_SIN_SUSTENTO)
    resultados = BT.ejecutar_backtesting_comparativo(_serie(), modelos=activos, horizontes=(1, 3))
    origenes = {
        r["entrenamiento_inicial"] for r in resultados.values() if r.get("ejecutado")
    }
    assert len(origenes) == 1, f"hay origenes distintos por modelo: {origenes}"


# --- 6: los pares por horizonte coinciden con la derivacion -----------------

def test_pares_por_horizonte_coinciden_con_la_derivacion() -> None:
    activos = tuple(m for m in MI.MODELOS_INTERPRETABLES if m not in SP.MODELOS_PARAMETRO_SIN_SUSTENTO)
    n0 = MI.observaciones_minimas_catalogo(activos)
    for h in (1, 3, 12):
        r = BT.ejecutar_backtesting(_serie(), horizonte=h, modelo="naive")
        assert r["iteraciones"] == N_SERIE - n0 - h + 1, (
            f"h={h}: {r['iteraciones']} pares, derivacion n - N0 - h + 1 = {N_SERIE - n0 - h + 1}"
        )


# --- 7 y 8: sin fuga y ventana expansiva ------------------------------------

def test_sin_fuga_el_entrenamiento_es_anterior_al_objetivo() -> None:
    h = 6
    r = BT.ejecutar_backtesting(_serie(), horizonte=h, modelo="lineal")
    pred = r["predicciones"]
    for obs, t_obj in zip(pred["Observaciones_entrenamiento"], pred["t"]):
        assert int(obs) <= int(t_obj) - h + 1, "el entrenamiento alcanza o supera al objetivo"


def test_ventana_expansiva_conservada() -> None:
    r = BT.ejecutar_backtesting(_serie(), horizonte=1, modelo="lineal")
    obs = list(r["predicciones"]["Observaciones_entrenamiento"])
    assert obs == sorted(obs) and obs[-1] - obs[0] == len(obs) - 1, (
        "la ventana dejo de ser expansiva de paso 1"
    )


# --- 9, 10 y 11: P0-A, P0-B y P0-D no reabren -------------------------------

def test_p0a_el_selector_de_respaldo_sigue_retirado() -> None:
    fuente = inspect.getsource(SP)
    assert "seleccionar_modelo_por_evidencia(" not in fuente, "P0-A reabierto"


def test_p0b_el_catalogo_sigue_gobernado_por_estimabilidad() -> None:
    assert SP.MODELOS_PARAMETRO_SIN_SUSTENTO == {"promedio_movil", "variacion_reciente"}
    # Solo el CUERPO: la cadena de documentacion nombra los literales retirados
    # justamente para dejar constancia de que lo estan.
    cuerpo = inspect.getsource(SP._modelos_para_analisis)
    cuerpo = cuerpo.split('"""')[-1]
    for literal in ("MIN_OBS_NIVEL_2", "MIN_OBS_HUBER", "0.035", "0.05"):
        assert literal not in cuerpo, f"P0-B reabierto: reaparece {literal}"


# Lote 2D-2: retirado `test_p0d_la_regla_de_seleccion_no_cambia` (y sus auxiliares _P0D_ULP_*, _p0d_banco,
# _p0d_lista), que probaba el selector heredado ya eliminado. Sus cuatro propiedades (muestra común, una ULP,
# orden de entrada, desempate) las fijan sobre el selector vigente tests/test_fase1a_selector_rectangular.py
# y tests/test_nmin_adversarial.py::p0d_en_el_selector_vigente.


# --- 12: determinismo -------------------------------------------------------

def test_determinismo() -> None:
    a = BT.ejecutar_backtesting(_serie(), horizonte=3, modelo="holt_amortiguado")
    b = BT.ejecutar_backtesting(_serie(), horizonte=3, modelo="holt_amortiguado")
    assert a["entrenamiento_inicial"] == b["entrenamiento_inicial"]
    assert list(a["predicciones"]["Predicho"]) == list(b["predicciones"]["Predicho"])


# --- 13: la tabla de criterios no publica una atribucion falsa --------------

def test_criterio_publicado_sin_atribucion_falsa() -> None:
    criterio = next(c for c in CR.CRITERIOS_ESTADISTICOS if c.id == "C-WF-002")
    assert "0.60" not in criterio.valor and "18" not in criterio.valor, (
        "la tabla sigue publicando la formula retirada"
    )
    assert "Hyndman" not in criterio.fuente, (
        "FPP3 no sustenta max(18, 0,60n): 5.10 no da proporcion y 5.8 da 20 % de prueba"
    )


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
