"""P0-C-R, GATE 0 §2.2: inventario de superficies públicas con capacidad reconstructiva del IC95.

Uso (desde la raíz, Qt offscreen):  python docs/fase_v112_p0c_residual_thermos/evidencia/inventario_superficies.py

Caso n=48, h=6 (B-A1). Para cada superficie se busca el par (sigma, n) que reproduce EXACTAMENTE el IC95 interno:
sigma_ref = `backtesting_comparativo[<ganador>_h6].metricas.rmse` (31 errores) y la muestra rectangular W*=13.
"""
import json
import math
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import app_icociv.proyeccion.servicio_proyeccion as sp  # noqa: E402


def ondulada(n):
    return pd.DataFrame({"Periodo": [f"{2021 + i // 12}_{i % 12 + 1}" for i in range(n)],
                         "Indice": [100.0 + 0.4 * i + 3.0 * math.sin(i * 0.7) for i in range(n)]})


def recorrer(nodo, ruta, vistos, salida):
    """Rutas numéricas con nombre de agregado de error, en dicts, listas, DataFrames y Series (con protección de ciclos)."""
    if isinstance(nodo, (dict, list, tuple, pd.DataFrame, pd.Series, np.ndarray)):
        if id(nodo) in vistos:
            return
        vistos.add(id(nodo))
    if isinstance(nodo, dict):
        for k, v in nodo.items():
            recorrer(v, f"{ruta}.{k}", vistos, salida)
    elif isinstance(nodo, (list, tuple)):
        for i, v in enumerate(nodo):
            recorrer(v, f"{ruta}[{i}]", vistos, salida)
    elif isinstance(nodo, pd.DataFrame):
        for c in nodo.columns:
            for i, v in enumerate(nodo[c].tolist()):
                recorrer(v, f"{ruta}<{c}>[{i}]", vistos, salida)
    elif isinstance(nodo, pd.Series):
        for i, v in enumerate(nodo.tolist()):
            recorrer(v, f"{ruta}[{i}]", vistos, salida)
    elif isinstance(nodo, (int, float, np.floating, np.integer)) and not isinstance(nodo, bool):
        salida.append((ruta, float(nodo)))


def main():
    df = ondulada(48)
    anio, mes = map(int, df.iloc[-1]["Periodo"].split("_")[:2])
    total = anio * 12 + mes - 1 + 6
    r = sp.ejecutar_proyeccion(df, total // 12, total % 12 + 1, 2021)
    clave = f"{r['modelo_codigo']}_h6"
    sigma_ref = r["backtesting_comparativo"][clave]["metricas"]["rmse"]
    rect = r["backtesting"]["metricas"]["rmse"]
    print(f"sigma del IC95 (= rmse de {clave}, n=31): {sigma_ref!r}   rmse rectangular (W*=13): {rect!r}")
    print(f"ajuste_calendario: { {k: v for k, v in (r.get('ajuste_calendario') or {}).items() if not isinstance(v, (dict, list))} }")

    # 1. Objeto público: dónde aparece EXACTAMENTE sigma_ref, y cuántas entradas del comparativo publican rmse e iteraciones.
    numeros = []
    recorrer(r, "r", set(), numeros)
    exactas = sorted({ruta for ruta, v in numeros if v == sigma_ref})
    print(f"\n[objeto] rutas con valor == sigma del IC95: {len(exactas)}")
    for ruta in exactas:
        print("   ", ruta)
    comp = r["backtesting_comparativo"]
    con_rmse = sum(1 for e in comp.values() if (e.get("metricas") or {}).get("rmse") is not None)
    con_obs = sum(1 for e in comp.values() if ((e.get("metricas") or {}).get("errores_extremos") or {}).get("observaciones"))
    n_obs = sorted({len(((e.get("metricas") or {}).get("errores_extremos") or {}).get("observaciones") or [])
                    for e in comp.values()})
    print(f"[objeto] backtesting_comparativo: {len(comp)} entradas; con metricas.rmse: {con_rmse}; "
          f"con observaciones no vacías: {con_obs}; tamaños de observaciones: {n_obs[:6]}…{n_obs[-3:]}")

    # 2. Sesión JSON
    from app_icociv.interfaz.controladores.controlador_principal import ControladorPrincipal
    ses = ControladorPrincipal._proyeccion_serializable(r)
    texto = json.dumps(ses, default=str)
    print(f"\n[sesión] contiene backtesting_comparativo: {'backtesting_comparativo' in ses}; "
          f"sigma del IC95 aparece: {repr(sigma_ref) in texto or str(sigma_ref) in texto}; "
          f"rmse rectangular aparece: {repr(rect) in texto}; 'error_absoluto' aparece: {'error_absoluto' in texto}")

    # 3. CSV de reproducibilidad
    from app_icociv.reportes.generador_reportes import generar_csv_reproducibilidad
    with TemporaryDirectory() as tmp:
        ruta = generar_csv_reproducibilidad(Path(tmp) / "r.csv", df, r, [{"nivel": "Serie", "valor": "x"}])
        csv = pd.read_csv(ruta, encoding="utf-8-sig")
    cols = [c for c in csv.columns if any(t in c for t in ("rmse", "iteraciones", "desviacion", "error_medio", "mae"))]
    print(f"\n[CSV] columnas de agregados: {cols}")
    fila6 = csv[csv.get("horizonte", pd.Series(dtype=float)) == 6] if "horizonte" in csv.columns else csv.tail(1)
    for c in cols:
        valores = fila6[c].tolist() if c in fila6 else []
        print(f"   {c} (h=6): {valores[:3]}")

    # 4. Tabla de horizontes publicada
    tabla = (r.get("horizonte_info") or {}).get("tabla_horizontes")
    if isinstance(tabla, pd.DataFrame):
        print(f"\n[tabla_horizontes] columnas: {list(tabla.columns)}")
        print(tabla.head(7).to_string(max_cols=12))
    elif isinstance(tabla, list) and tabla:
        print(f"\n[tabla_horizontes] lista de {len(tabla)}; claves fila: {sorted(tabla[0])}")
        print(f"   fila h=6: { {k: v for k, v in (tabla[5] if len(tabla) > 5 else tabla[-1]).items()} }")


if __name__ == "__main__":
    main()
