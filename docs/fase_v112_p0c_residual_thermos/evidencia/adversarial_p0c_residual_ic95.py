"""P0-C-R · prueba adversarial DIAGNÓSTICA (fuera del perfil esencial y de la recolección por defecto).

Comando canónico (03 §1), desde la raíz del repositorio, en PowerShell o bash:

    python -m pytest docs/fase_v112_p0c_residual_thermos/evidencia/adversarial_p0c_residual_ic95.py -p no:cacheprovider -q -rA

El nombre no empieza por `test_` y vive en `docs/`: `pytest --collect-only` no la recoge y `scripts/pruebas_fase0.py` no la
asigna a ningún perfil, de modo que no deja el CI en rojo ni necesita `skip`/`xfail`.

Tres grupos, que NO deben confundirse si algún día se promueve a `tests/`:

1. CONTRATO (`test_contrato_*`): lo que debería cumplirse tras una corrección. En la base `dfcaaa9`
   `test_contrato_sin_vector_individual_de_errores_oos` FALLA (vía A: el vector por ventana está publicado).
2. CARACTERIZACIÓN DEL NO-GO (`test_caracterizacion_no_go_*`): PASAN en la base y su PASS es la mala noticia. Con agregados
   que el contrato protege sale el IC95 interno sin leer el vector: EXACTO con el RMSE y su n (B1) y con el RMSE_h
   persistido en h=24 (B3); salvo un ULP con desviación y media (B2) o MAE y `estabilidad_error` (B4); salvo el redondeo
   a 3 decimales con el texto `interpretacion` (B5). El vector (A) y, sin `error_absoluto`, `z_modificado` con mediana y
   MAD (A') también lo reconstruyen. Documentan por qué retirar el vector no cierra P0-C. No deben promoverse como
   regresión: protegerían la vulnerabilidad.
3. DETECTOR Y ESCENARIO (`test_detector_*`, `test_escenario_*`): sensibilidad y casos borde, sin depender del motor salvo
   donde se indica. El detector es HEURÍSTICO (por nombre de clave; no mira cadenas de texto): un verde suyo no prueba
   irreconstruibilidad. El oráculo semántico es la caracterización, con las vías identificadas en esta fase (no se
   garantiza que sean todas).
"""
import math

import numpy as np
import pandas as pd
import pytest

from caso_ic95 import banda, entrada_ganadora, proyectar, sin_calendario, sp, vias

#: Nombres con los que un vector por ventana permite recuperar `sigma_h`: las columnas que producción ya considera
#: reconstructivas (`COLUMNAS_OOS_RECONSTRUCTIVAS`) más los alias en minúsculas que usan otras estructuras.
CLAVES_POR_VENTANA = {c.lower() for c in sp.COLUMNAS_OOS_RECONSTRUCTIVAS} | {
    "error_absoluto", "z_modificado", "real", "pronostico"}
AGREGADOS = ("rmse", "mae", "mase", "iteraciones", "sesgo_medio")
CASOS = ("n48_h6", "n72_h12", "n38_h24", "n72_h24")
#: Todos los escenarios de `caso_ic95` con banda interna finita (n30_h3 no la tiene).
CON_BANDA = ("n48_h6", "n72_h12", "n38_h24", "n60_h9", "n48_h24", "n72_h24")


def _numericos(valores) -> int:
    return sum(isinstance(v, (int, float, np.number)) and not isinstance(v, bool) and np.isfinite(v) for v in valores)


def vectores_por_ventana(objeto) -> list[str]:
    """Rutas públicas con >= 2 números bajo un nombre de error/observado/predicho por ventana.

    Recorre dicts, listas, tuplas, DataFrames (columnas y celdas anidadas) y Series (por su `name` y por su contenido),
    con protección de ciclos. Detecta listas de registros (`[{..., "error_absoluto": x}, ...]`), columnas, Series con
    nombre de error y claves de dict cuyo valor es una secuencia numérica (lista, tupla, array o Series).
    """
    hallados, vistos = [], set()

    def recorrer(nodo, ruta):
        if isinstance(nodo, (dict, list, tuple, pd.DataFrame, pd.Series, np.ndarray)):
            if id(nodo) in vistos:
                return
            vistos.add(id(nodo))
        if isinstance(nodo, dict):
            for clave, valor in nodo.items():
                if str(clave).lower() in CLAVES_POR_VENTANA and isinstance(valor, (list, tuple, np.ndarray, pd.Series)):
                    if _numericos(list(valor)) >= 2:
                        hallados.append(f"{ruta}.{clave}")
                recorrer(valor, f"{ruta}.{clave}")
        elif isinstance(nodo, (list, tuple)):
            registros = [x for x in nodo if isinstance(x, dict)]
            if len(registros) >= 2:
                for clave in {str(k) for x in registros for k in x}:
                    if clave.lower() in CLAVES_POR_VENTANA and _numericos([x.get(clave) for x in registros]) >= 2:
                        hallados.append(f"{ruta}[*].{clave}")
            for i, valor in enumerate(nodo):
                recorrer(valor, f"{ruta}[{i}]")
        elif isinstance(nodo, pd.Series):
            if str(nodo.name).lower() in CLAVES_POR_VENTANA and _numericos(nodo.tolist()) >= 2:
                hallados.append(f"{ruta}<Series {nodo.name}>")
            for valor in nodo.tolist():
                if isinstance(valor, (dict, list, pd.Series, pd.DataFrame)):
                    recorrer(valor, ruta)
        elif isinstance(nodo, pd.DataFrame):
            for columna in nodo.columns:
                if str(columna).lower() in CLAVES_POR_VENTANA:
                    if _numericos(pd.to_numeric(nodo[columna], errors="coerce").tolist()) >= 2:
                        hallados.append(f"{ruta}<{columna}>")
                for valor in nodo[columna].tolist():
                    if isinstance(valor, (dict, list, pd.Series, pd.DataFrame)):
                        recorrer(valor, f"{ruta}<{columna}>")

    recorrer(objeto, "resultado")
    return hallados


def _resumir(rutas):
    import re

    formas = sorted({re.sub(r"\.[a-z0-9_]+_h\d+\.", ".<modelo_h>.", r) for r in rutas})
    return f"{len(rutas)} rutas; formas: {formas}"


def _con_banda(caso):
    publico, interno, h = proyectar(caso)
    assert interno is not None, f"{caso}: el motor no construyó banda interna finita; elegir otro escenario."
    assert publico.get("ci95_lo") is None and publico.get("ci95_hi") is None, "El IC95 volvió a publicarse."
    assert sin_calendario(publico), f"{caso}: hay ajuste de calendario; la fórmula sin factor no aplica."
    return publico, interno, h


# 1. CONTRATO ---------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("caso", CASOS)
def test_contrato_sin_vector_individual_de_errores_oos(caso):
    publico, _, _ = proyectar(caso)
    rutas = vectores_por_ventana(publico)
    assert not rutas, f"Vector de errores OOS por ventana publicado (vía A, reconstruye el IC95): {_resumir(rutas)}"


@pytest.mark.parametrize("caso", CASOS)
def test_contrato_el_comparativo_conserva_los_agregados(caso):
    publico, _, h = proyectar(caso)
    metricas = entrada_ganadora(publico, h)["metricas"]
    assert [a for a in AGREGADOS if metricas.get(a) is None or not np.isfinite(float(metricas[a]))] == []


# 2. CARACTERIZACIÓN DEL NO-GO (su PASS demuestra la contradicción) ------------------------------------------------

@pytest.mark.parametrize("caso", CON_BANDA)
@pytest.mark.parametrize("via", ["A (vector error_absoluto)", "B1 (rmse+iteraciones)"])
def test_caracterizacion_no_go_cada_via_reconstruye_el_ic95_exacto(caso, via):
    """A (vector) y B1 (el RMSE publicado, que ES sigma): igualdad exacta, sin tolerancia, en los 6 escenarios."""
    publico, interno, h = _con_banda(caso)
    sigma, n = vias(publico, h)[via]
    assert banda(publico, sigma, n) == interno


@pytest.mark.parametrize("caso", CON_BANDA)
@pytest.mark.parametrize("via", ["A' (z_modificado+mediana+MAD)", "B2 (desviacion ddof1+media)",
                                 "B4 (mae+estabilidad_error)"])
def test_caracterizacion_no_go_via_algebraica_reconstruye_el_ic95_salvo_un_ulp(caso, via):
    """A', B2 y B4 son identidades exactas, pero reordenan la aritmética de coma flotante: la sigma puede diferir de la
    interna en el último dígito. Hoy la banda coincide bit a bit salvo B2 en n48_h24 (2,8e-14, ~2e-16 relativo).
    Tolerancia declarada: `rel_tol=1e-15` (unos cinco ULP)."""
    publico, interno, h = _con_banda(caso)
    sigma, n = vias(publico, h)[via]
    lo, hi = banda(publico, sigma, n)
    assert math.isclose(lo, interno[0], rel_tol=1e-15, abs_tol=0.0)
    assert math.isclose(hi, interno[1], rel_tol=1e-15, abs_tol=0.0)


@pytest.mark.parametrize("caso", ["n38_h24", "n72_h24"])
def test_caracterizacion_no_go_el_rmse_h_persistido_reconstruye_el_ic95_exacto_en_h24(caso):
    """En h=24 la muestra rectangular W* coincide con la del intervalo: `tabla_horizontes` (y CSV y sesión) bastan."""
    publico, interno, h = _con_banda(caso)
    sigma, n = vias(publico, h)["B3 (RMSE_h rectangular+W)"]
    assert banda(publico, sigma, n) == interno


@pytest.mark.parametrize("caso", CON_BANDA)
def test_caracterizacion_no_go_el_texto_interpretacion_da_el_ic95_salvo_el_redondeo_a_3_decimales(caso):
    """B5: `interpretacion` publica «RMSE=x.xxx». El redondeo a 3 decimales acota |sigma_texto − sigma| <= 5e-4, luego
    |límite − interno| <= c(n)·5e-4. La cota se deduce del formato, no es una tolerancia elegida."""
    publico, interno, h = _con_banda(caso)
    sigma, n = vias(publico, h)["B5 (texto interpretacion, 3 decimales)"]
    cota = sp._multiplicador_intervalo(sp.NIVEL_NOMINAL_95, n) * 5e-4 * (1 + 1e-9)
    lo, hi = banda(publico, sigma, n)
    assert abs(lo - interno[0]) <= cota and abs(hi - interno[1]) <= cota


def test_caracterizacion_no_go_retirar_solo_el_vector_no_cierra_p0c():
    """La «corrección parcial»: sin `observaciones` el contrato del vector pasaría, pero B1 sigue dando el IC95 exacto."""
    publico, interno, h = _con_banda("n48_h6")
    parcial = {k: v for k, v in publico.items() if k != "backtesting_comparativo"}
    parcial["backtesting_comparativo"] = {
        clave: {**e, "metricas": {**(e.get("metricas") or {}), "errores_extremos": {
            k: v for k, v in ((e.get("metricas") or {}).get("errores_extremos") or {}).items() if k != "observaciones"}}}
        for clave, e in publico["backtesting_comparativo"].items()}
    assert vectores_por_ventana(parcial) == []
    sigma, n = vias(parcial, h)["B1 (rmse+iteraciones)"]
    assert banda(parcial, sigma, n) == interno


def test_caracterizacion_no_go_retirar_solo_error_absoluto_no_basta():
    """Sin la clave `error_absoluto`, `z_modificado` con la mediana y el MAD publicados devuelve el vector |e| (A')."""
    publico, interno, h = _con_banda("n48_h6")
    entrada = entrada_ganadora(publico, h)
    extremos = entrada["metricas"]["errores_extremos"]
    entrada_sin_ea = {**entrada, "metricas": {**entrada["metricas"], "errores_extremos": {
        **extremos, "observaciones": [{k: v for k, v in o.items() if k != "error_absoluto"}
                                      for o in extremos["observaciones"]]}}}
    sin_ea = {**publico, "backtesting_comparativo": {
        **publico["backtesting_comparativo"], f"{publico['modelo_codigo']}_h{h}": entrada_sin_ea}}
    assert all("error_absoluto" not in o for o in entrada_sin_ea["metricas"]["errores_extremos"]["observaciones"])
    sigma, n = vias(sin_ea, h)["A' (z_modificado+mediana+MAD)"]
    assert banda(sin_ea, sigma, n) == interno


# 3. DETECTOR Y ESCENARIO --------------------------------------------------------------------------------------------

@pytest.mark.parametrize("objeto, esperado", [
    ({"diagnostico": [{"origen": i, "Error": 0.1 * i} for i in range(5)]}, ["resultado.diagnostico[*].Error"]),
    ({"bt": {"predicciones": pd.DataFrame({"Origen": [1, 2], "Predicho": [1.0, 2.0]})}}, ["resultado.bt.predicciones<Predicho>"]),
    ({"extremos": {"error_absoluto": [0.5, 0.7, 0.9]}}, ["resultado.extremos.error_absoluto"]),
    ({"extremos": {"error_absoluto": np.array([0.5, 0.7])}}, ["resultado.extremos.error_absoluto"]),
    ({"x": [pd.Series([1.0, 2.0], name="Error")]}, ["resultado.x[0]<Series Error>"]),
    ({"anidado": {"t": pd.DataFrame({"Origen": [1, 2], "Observado": [1.0, 2.0]})}}, ["resultado.anidado.t<Observado>"]),
    ({"obs": [{"posicion": i, "z_modificado": 0.1 * i} for i in range(3)]}, ["resultado.obs[*].z_modificado"]),
    ({"solo_uno": [{"error_absoluto": 0.3}]}, []),
    ({"c": {"a_h1": None, "b_h1": {"metricas": None}, "c_h1": {"metricas": {"errores_extremos": {"observaciones": []}}},
            "d_h1": {"metricas": {"errores_extremos": {"observaciones": None}}}}}, []),
], ids=["registros_Error", "columna_Predicho", "lista_error_absoluto", "array_error_absoluto", "series_Error",
        "dataframe_anidado", "registros_z_modificado", "un_solo_registro", "none_y_vacios"])
def test_detector_sensibilidad(objeto, esperado):
    assert vectores_por_ventana(objeto) == esperado


def test_escenario_historia_insuficiente_sin_banda_ni_vectores():
    publico, interno, _ = proyectar("n30_h3")
    assert publico.get("proyeccion_generada") is False and interno is None
    assert vectores_por_ventana(publico) == []


def test_escenario_entradas_sin_extremos_publican_el_vector_completo():
    """Un candidato sin observaciones extremas (`cantidad == 0`) publica igualmente un registro por ventana."""
    publico, _, _ = proyectar("n48_h6")
    sin_extremos = [e for e in publico["backtesting_comparativo"].values()
                    if ((e.get("metricas") or {}).get("errores_extremos") or {}).get("calculable")
                    and e["metricas"]["errores_extremos"].get("cantidad") == 0]
    assert sin_extremos, "El escenario ya no tiene candidatos sin extremos: elegir otro."
    entrada = sin_extremos[0]
    assert len(entrada["metricas"]["errores_extremos"]["observaciones"]) == entrada["metricas"]["iteraciones"]
