"""P0-C-R · prueba adversarial DIAGNÓSTICA (fuera del perfil esencial y de la recolección por defecto).

Ejecutar a mano, desde la raíz del repositorio:

    QT_QPA_PLATFORM=offscreen python -m pytest docs/fase_v112_p0c_residual_thermos/evidencia/adversarial_p0c_residual_ic95.py -p no:cacheprovider -q

El nombre no empieza por `test_` y vive en `docs/`: `pytest --collect-only` no la recoge y `scripts/pruebas_fase0.py` no la
asigna a ningún perfil. Así no deja el CI en rojo ni necesita `skip`/`xfail` para ocultar lo que demuestra.

Qué demuestra en la base `dfcaaa9` (resultado esperado y documentado en 03):

* `test_red_sin_vector_individual_de_errores_oos` FALLA: el objeto público lleva el vector de errores absolutos por ventana
  en `backtesting_comparativo.<modelo_h>.metricas.errores_extremos.observaciones[*].error_absoluto` (vía A).
* `test_via_b_*` PASAN, y eso es lo grave: con agregados que el contrato protege (RMSE y su `n`, o desviación y media del
  error) se reconstruye el IC95 interno EXACTO, sin leer el vector. Por eso retirar solo el vector no cierra P0-C.
* `test_comparativo_conserva_agregados` y los casos borde PASAN: no hay errores nuevos con historia insuficiente, entradas
  sin extremos ni estructuras con `None`.
"""
import math

import numpy as np
import pandas as pd
import pytest

import app_icociv.proyeccion.servicio_proyeccion as sp

#: Nombres con los que un vector por ventana permite recuperar `sigma_h` (ver `COLUMNAS_OOS_RECONSTRUCTIVAS`).
CLAVES_POR_VENTANA = {"error", "error_abs", "error_absoluto", "error_pct", "error_escalado_abs",
                      "escala_naive_insample", "observado", "predicho", "real", "pronostico"}
AGREGADOS = ("rmse", "mae", "mase", "iteraciones", "sesgo_medio")


def _serie(valores):
    return pd.DataFrame({"Periodo": [f"{2021 + i // 12}_{i % 12 + 1}" for i in range(len(valores))],
                         "Indice": [float(v) for v in valores]})


def _ondulada(n):
    return _serie([100.0 + 0.4 * i + 3.0 * math.sin(i * 0.7) for i in range(n)])


def _ruidosa(n, semilla=7):
    rng = np.random.default_rng(semilla)
    return _serie([120.0 + 0.6 * i + rng.normal(0.0, 2.5) for i in range(n)])


CASOS = {"n48_h6": (_ondulada(48), 6), "n72_h12": (_ruidosa(72), 12), "n38_h24": (_ondulada(38), 24),
         "n72_h24": (_ruidosa(72), 24)}
_CACHE: dict = {}


def _ejecutar(caso):
    """Resultado público e IC95 interno (capturado antes de que `_retirar_intervalo_de_publicacion` lo vacíe)."""
    if caso not in _CACHE:
        df, h = CASOS[caso]
        anio, mes = map(int, df.iloc[-1]["Periodo"].split("_")[:2])
        total = anio * 12 + mes - 1 + h
        interno = {}
        original = sp._retirar_intervalo_de_publicacion

        def espia(resultado, *a, **k):
            interno.update(lo=resultado.get("ci95_lo"), hi=resultado.get("ci95_hi"))
            return original(resultado, *a, **k)

        sp._retirar_intervalo_de_publicacion = espia
        try:
            publico = sp.ejecutar_proyeccion(df, total // 12, total % 12 + 1, 2021)
        finally:
            sp._retirar_intervalo_de_publicacion = original
        _CACHE[caso] = (publico, interno, h)
    return _CACHE[caso]


def vectores_por_ventana(objeto) -> list[str]:
    """Rutas públicas con >= 2 números bajo un nombre de error/observado/predicho por ventana.

    Recorre dicts, listas, tuplas, DataFrames, Series y arrays con protección de ciclos. Detecta listas de registros
    (`[{..., "error_absoluto": x}, ...]`), columnas de DataFrame y claves cuyo valor ya es una secuencia numérica.
    """
    hallados, vistos = [], set()

    def numeros(valores):
        return sum(isinstance(v, (int, float, np.number)) and not isinstance(v, bool) and np.isfinite(v)
                   for v in valores)

    def recorrer(nodo, ruta):
        if isinstance(nodo, (dict, list, tuple, pd.DataFrame, pd.Series, np.ndarray)):
            if id(nodo) in vistos:
                return
            vistos.add(id(nodo))
        if isinstance(nodo, dict):
            for clave, valor in nodo.items():
                if str(clave).lower() in CLAVES_POR_VENTANA and isinstance(valor, (list, tuple, np.ndarray, pd.Series)):
                    if numeros(list(valor)) >= 2:
                        hallados.append(f"{ruta}.{clave}")
                recorrer(valor, f"{ruta}.{clave}")
        elif isinstance(nodo, (list, tuple)):
            registros = [x for x in nodo if isinstance(x, dict)]
            if len(registros) >= 2:
                for clave in {str(k) for x in registros for k in x}:
                    if clave.lower() in CLAVES_POR_VENTANA and numeros([x.get(clave) for x in registros]) >= 2:
                        hallados.append(f"{ruta}[*].{clave}")
            for i, valor in enumerate(nodo):
                recorrer(valor, f"{ruta}[{i}]")
        elif isinstance(nodo, pd.DataFrame):
            for columna in nodo.columns:
                if str(columna).lower() in CLAVES_POR_VENTANA:
                    if len(pd.to_numeric(nodo[columna], errors="coerce").dropna()) >= 2:
                        hallados.append(f"{ruta}<{columna}>")
                for valor in nodo[columna].tolist():
                    if isinstance(valor, (dict, list)):
                        recorrer(valor, f"{ruta}<{columna}>")

    recorrer(objeto, "resultado")
    return hallados


def _resumir(rutas):
    import re
    genericas = sorted({re.sub(r"\.[a-z0-9_]+_h\d+\.", ".<modelo_h>.", r) for r in rutas})
    return f"{len(rutas)} rutas; formas: {genericas}"


@pytest.mark.parametrize("caso", sorted(CASOS))
def test_red_sin_vector_individual_de_errores_oos(caso):
    publico, _, _ = _ejecutar(caso)
    rutas = vectores_por_ventana(publico)
    assert not rutas, f"Vector de errores OOS por ventana publicado (vía A, reconstruye el IC95): {_resumir(rutas)}"


@pytest.mark.parametrize("caso", sorted(CASOS))
def test_comparativo_conserva_agregados(caso):
    publico, _, h = _ejecutar(caso)
    entrada = publico["backtesting_comparativo"][f"{publico['modelo_codigo']}_h{h}"]
    metricas = entrada["metricas"]
    assert all(metricas.get(a) is not None for a in AGREGADOS), [a for a in AGREGADOS if metricas.get(a) is None]
    assert len(publico["backtesting_comparativo"]) > 0


def _banda(publico, sigma, n):
    c = sp._multiplicador_intervalo(sp.NIVEL_NOMINAL_95, int(n))
    y = float(publico["y_proj"])
    return y - c * sigma, y + c * sigma


@pytest.mark.parametrize("caso", sorted(CASOS))
def test_via_b_el_rmse_del_comparativo_reconstruye_el_ic95_exacto(caso):
    """Comprobación INDEPENDIENTE de la vía B: no lee `observaciones`. Igualdad exacta, sin tolerancia."""
    publico, interno, h = _ejecutar(caso)
    metricas = publico["backtesting_comparativo"][f"{publico['modelo_codigo']}_h{h}"]["metricas"]
    assert interno["lo"] is not None and publico.get("ci95_lo") is None  # existe banda interna y no se publica
    assert _banda(publico, float(metricas["rmse"]), metricas["iteraciones"]) == (interno["lo"], interno["hi"])


@pytest.mark.parametrize("caso", ["n38_h24", "n72_h24"])
def test_via_b_el_rmse_h_persistido_reconstruye_el_ic95_exacto_en_h24(caso):
    """En H=24 la muestra rectangular W* es la misma que la del intervalo: `tabla_horizontes` (y CSV y sesión) bastan."""
    publico, interno, h = _ejecutar(caso)
    fila = next(f for f in publico["horizonte_info"]["tabla_horizontes"] if int(f["horizonte"]) == h)
    assert _banda(publico, float(fila["rmse"]), fila["W"]) == (interno["lo"], interno["hi"])


def test_historia_insuficiente_no_rompe_el_recorrido():
    df = _ruidosa(30)
    anio, mes = map(int, df.iloc[-1]["Periodo"].split("_")[:2])
    total = anio * 12 + mes - 1 + 3
    publico = sp.ejecutar_proyeccion(df, total // 12, total % 12 + 1, 2021)
    assert publico.get("proyeccion_generada") is False
    assert vectores_por_ventana(publico) == []


def test_el_recorrido_tolera_none_y_estructuras_faltantes():
    sintetico = {"backtesting_comparativo": {"a_h1": None, "b_h1": {"metricas": None},
                                             "c_h1": {"metricas": {"errores_extremos": {"observaciones": []}}},
                                             "d_h1": {"metricas": {"errores_extremos": {"observaciones": None}}}}}
    assert vectores_por_ventana(sintetico) == []


def test_entradas_sin_extremos_siguen_publicando_el_vector():
    """Un candidato sin observaciones extremas (`cantidad == 0`) publica igualmente el vector completo."""
    publico, _, _ = _ejecutar("n48_h6")
    sin_extremos = [k for k, e in publico["backtesting_comparativo"].items()
                    if (e.get("metricas") or {}).get("errores_extremos", {}).get("cantidad") == 0]
    assert sin_extremos, "El caso ya no tiene candidatos sin extremos: elegir otro."
    entrada = publico["backtesting_comparativo"][sin_extremos[0]]
    assert len(entrada["metricas"]["errores_extremos"]["observaciones"]) == entrada["iteraciones"]
