"""P0-C-R · utilidades compartidas por los diagnósticos de esta carpeta (una sola fuente de verdad del caso).

Fija Qt en modo offscreen y pone la raíz del repositorio en `sys.path`, de modo que los scripts y la prueba funcionan con
`python <script>` o con `python -m pytest <archivo>` desde la raíz, en PowerShell o en bash.

Depende de dos nombres privados de producción, a propósito: `_retirar_intervalo_de_publicacion` (para capturar el IC95
interno antes de que se vacíe) y `_multiplicador_intervalo` (el `c(n)` exacto que usa el motor). Si cambian, estos
diagnósticos fallan con `AttributeError`: es la señal de que el análisis de 01 debe repetirse.
"""
import math
import os
import sys
from functools import cache
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import app_icociv.proyeccion.servicio_proyeccion as sp  # noqa: E402


def serie(valores, anio=2021):
    return pd.DataFrame({"Periodo": [f"{anio + i // 12}_{i % 12 + 1}" for i in range(len(valores))],
                         "Indice": [float(v) for v in valores]})


def ondulada(n):
    return serie([100.0 + 0.4 * i + 3.0 * math.sin(i * 0.7) for i in range(n)])


def ruidosa(n, semilla=7):
    rng = np.random.default_rng(semilla)
    return serie([120.0 + 0.6 * i + rng.normal(0.0, 2.5) for i in range(n)])


def estacional(n, semilla=3):
    rng = np.random.default_rng(semilla)
    return serie([100.0 + 0.3 * i + 6.0 * math.cos(2 * math.pi * i / 12) + rng.normal(0.0, 0.8) for i in range(n)])


#: Escenarios del GATE 0: nombre -> (generador, n, h). Se generan bajo demanda (la caché es por nombre).
ESCENARIOS = {
    "n48_h6": (ondulada, 48, 6),     # caso B-A1
    "n72_h12": (ruidosa, 72, 12),    # errores no triviales
    "n38_h24": (ondulada, 38, 24),   # pocos pares: 3 errores en el paso 24
    "n60_h9": (estacional, 60, 9),
    "n48_h24": (ondulada, 48, 24),   # H máximo: la muestra rectangular W* coincide con la del intervalo
    "n72_h24": (ruidosa, 72, 24),
    "n30_h3": (ruidosa, 30, 3),      # historia insuficiente: no hay proyección
}


@cache
def proyectar(nombre):
    """`(publico, interno, h)`: resultado real de `ejecutar_proyeccion` y el IC95 interno capturado antes de vaciarlo.

    `interno` es `(lo, hi)` o `None` si el motor no construyó banda finita. El espía se restaura siempre.
    """
    generador, n, h = ESCENARIOS[nombre]
    df = generador(n)
    anio, mes = map(int, df.iloc[-1]["Periodo"].split("_")[:2])
    total = anio * 12 + mes - 1 + h
    capturado = {}
    original = sp._retirar_intervalo_de_publicacion

    def espia(resultado, *a, **k):
        capturado.update(lo=resultado.get("ci95_lo"), hi=resultado.get("ci95_hi"))
        return original(resultado, *a, **k)

    sp._retirar_intervalo_de_publicacion = espia
    try:
        publico = sp.ejecutar_proyeccion(df, total // 12, total % 12 + 1, 2021)
    finally:
        sp._retirar_intervalo_de_publicacion = original
    lo, hi = capturado.get("lo"), capturado.get("hi")
    finito = all(v is not None and math.isfinite(v) for v in (lo, hi))
    return publico, ((lo, hi) if finito else None), h


def banda(publico, sigma, n):
    """IC95 con la fórmula productiva `y ± c(n)·sigma` (factor de calendario 1: se comprueba en `sin_calendario`)."""
    c = sp._multiplicador_intervalo(sp.NIVEL_NOMINAL_95, int(n))
    y = float(publico["y_proj"])
    return y - c * float(sigma), y + c * float(sigma)


def sin_calendario(publico):
    """Los escenarios no aplican ajuste de calendario; si alguno lo hiciera, la fórmula sin factor no valdría."""
    return not (publico.get("ajuste_calendario") or {}).get("ajuste_calendario_aplicado")


def entrada_ganadora(publico, h):
    return publico["backtesting_comparativo"][f"{publico['modelo_codigo']}_h{h}"]


def _rms(valores):
    v = np.asarray(valores, float)
    v = v[np.isfinite(v)]
    return (float(np.sqrt(np.mean(v ** 2))) if len(v) else float("nan")), len(v)


def vias(publico, h):
    """`{vía: (sigma, n)}` para las reconstrucciones de 01.

    A y A' leen datos por ventana; B1–B4, solo agregados. `n` es `metricas.iteraciones` salvo en A/A', donde es el número
    de registros. (`iteraciones` cuenta también predicciones no finitas; `errores_extremos.n`, también publicado, da el n
    finito. En los escenarios de esta carpeta coinciden.)
    """
    met = entrada_ganadora(publico, h)["metricas"]
    n = int(met["iteraciones"])
    extremos = met.get("errores_extremos") or {}
    obs = extremos.get("observaciones") or []
    # A': el vector |e| sale de z_modificado sin `error_absoluto`: |e| = mediana + z·MAD/factor (metricas.py:73).
    mediana, mad, factor = (extremos.get(k) for k in ("mediana_error_absoluto", "mad_error_absoluto", "factor"))
    desde_z = [mediana + o["z_modificado"] * mad / factor for o in obs] if obs and mad else []
    mae, estabilidad = float(met["mae"]), float(met["estabilidad_error"])
    fila = next(f for f in publico["horizonte_info"]["tabla_horizontes"] if int(f["horizonte"]) == h)
    return {
        "A (vector error_absoluto)": _rms([o["error_absoluto"] for o in obs if "error_absoluto" in o]),
        "A' (z_modificado+mediana+MAD)": _rms(desde_z),
        "B1 (rmse+iteraciones)": (float(met["rmse"]), n),
        "B2 (desviacion ddof1+media)": (
            math.sqrt(float(met["error_medio"]) ** 2 + float(met["desviacion_error"]) ** 2 * (n - 1) / n), n),
        # B4: estabilidad = std(|e|, ddof=1)/mean(|e|) y mae = mean(|e|)  =>  sigma² = mae²·(1 + estabilidad²·(n−1)/n)
        "B4 (mae+estabilidad_error)": (mae * math.sqrt(1 + estabilidad ** 2 * (n - 1) / n), n),
        "B3 (RMSE_h rectangular+W)": (float(fila["rmse"]), int(fila["W"])),
    }
