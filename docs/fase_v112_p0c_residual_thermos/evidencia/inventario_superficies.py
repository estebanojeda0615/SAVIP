"""P0-C-R, GATE 0 §2.2: dónde aparece públicamente la `sigma_h` exacta del IC95 y qué publica cada superficie persistida.

Uso, desde la raíz del repositorio:  python docs/fase_v112_p0c_residual_thermos/evidencia/inventario_superficies.py

Caso n48_h6. No reconstruye bandas (eso lo hace `diagnostico_vias_a_b.py`): localiza en el objeto todas las rutas cuyo
valor es exactamente `sigma_h` (= `metricas.rmse` de la entrada ganadora) y lista los agregados de la sesión JSON, el CSV
de reproducibilidad y la tabla de horizontes.
"""
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

from caso_ic95 import ESCENARIOS, entrada_ganadora, proyectar


def numeros(nodo, ruta="r", vistos=None):
    """Pares (ruta, valor) de todos los números del árbol (dicts, listas, DataFrames, Series), con protección de ciclos."""
    vistos = vistos if vistos is not None else set()
    if isinstance(nodo, (dict, list, tuple, pd.DataFrame, pd.Series, np.ndarray)):
        if id(nodo) in vistos:
            return
        vistos.add(id(nodo))
    if isinstance(nodo, dict):
        for k, v in nodo.items():
            yield from numeros(v, f"{ruta}.{k}", vistos)
    elif isinstance(nodo, (list, tuple, pd.Series, np.ndarray)):
        for i, v in enumerate(list(nodo)):
            yield from numeros(v, f"{ruta}[{i}]", vistos)
    elif isinstance(nodo, pd.DataFrame):
        for c in nodo.columns:
            yield from numeros(nodo[c], f"{ruta}<{c}>", vistos)
    elif isinstance(nodo, (int, float, np.number)) and not isinstance(nodo, bool):
        yield ruta, float(nodo)


def main():
    publico, _, h = proyectar("n48_h6")
    df = ESCENARIOS["n48_h6"][0](ESCENARIOS["n48_h6"][1])
    entrada = entrada_ganadora(publico, h)
    sigma, n = entrada["metricas"]["rmse"], entrada["metricas"]["iteraciones"]
    fila = next(f for f in publico["horizonte_info"]["tabla_horizontes"] if int(f["horizonte"]) == h)
    print(f"sigma_h del IC95 = metricas.rmse de la entrada ganadora: {sigma!r} (n={n}); "
          f"RMSE_h rectangular: {fila['rmse']!r} (W={fila['W']})")

    exactas = sorted({ruta for ruta, v in numeros(publico) if v == sigma})
    print(f"\n[objeto] rutas con valor == sigma_h: {exactas}")
    comp = publico["backtesting_comparativo"]
    tamanos = sorted({len(((e.get("metricas") or {}).get("errores_extremos") or {}).get("observaciones") or [])
                      for e in comp.values()})
    print(f"[objeto] backtesting_comparativo: {len(comp)} entradas; con metricas.rmse: "
          f"{sum((e.get('metricas') or {}).get('rmse') is not None for e in comp.values())}; "
          f"tamaños de observaciones: min={tamanos[0]} max={tamanos[-1]}")

    from app_icociv.interfaz.controladores.controlador_principal import ControladorPrincipal
    texto = json.dumps(ControladorPrincipal._proyeccion_serializable(publico), default=str)
    print(f"\n[sesión] backtesting_comparativo: {'backtesting_comparativo' in texto}; sigma_h: {repr(sigma) in texto}; "
          f"RMSE_h rectangular: {repr(fila['rmse']) in texto}; 'error_absoluto': {'error_absoluto' in texto}")

    from app_icociv.reportes.generador_reportes import generar_csv_reproducibilidad
    with TemporaryDirectory() as tmp:
        csv = pd.read_csv(generar_csv_reproducibilidad(Path(tmp) / "r.csv", df, publico, [{"nivel": "Serie", "valor": "x"}]),
                          encoding="utf-8-sig")
    numeros_csv = set(csv.select_dtypes("number").to_numpy().ravel())
    rmse_csv = pd.to_numeric(csv["rmse_horizonte"], errors="coerce").dropna()
    mas_cercano = float(rmse_csv.iloc[(rmse_csv - fila["rmse"]).abs().argmin()])
    print(f"\n[CSV] RMSE_h de h={h} en `rmse_horizonte`: {mas_cercano!r} (texto con redondeo; "
          f"|dif| con el objeto = {abs(mas_cercano - fila['rmse']):.1e}); "
          f"W={fila['W']} en `iteraciones_backtesting_horizonte`: {fila['W'] in set(csv['iteraciones_backtesting_horizonte'])}; "
          f"sigma_h aparece: {sigma in numeros_csv}")

    print(f"\n[tabla_horizontes] fila h={h}: {fila}")


if __name__ == "__main__":
    main()
