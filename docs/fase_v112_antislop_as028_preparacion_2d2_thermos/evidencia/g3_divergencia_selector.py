"""AS-028 G3: ¿coincide el selector heredado (todos los pares del backtesting comparativo, float)
con el modelo productivo (W*x24, SSE exacta, 21 candidatos)? Solo lectura; no parchea nada."""
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, sys.argv[1])
from app_icociv.proyeccion import servicio_proyeccion as sp
from app_icociv.validacion.backtesting import ejecutar_backtesting_comparativo
from tests.fixtures.fase0 import generadores as gen

def periodos(n):
    return [f"{2021 + i // 12}_{i % 12 + 1}" for i in range(n)]

casos = {"script_L296 (61 obs, anio_base 2021)": (pd.DataFrame({"Periodo": periodos(61), "Indice": [100.0 + 0.45 * i + 1.8 * np.sin(i / 3.0) for i in range(61)]}), (2026, 4), 2021)}
for nombre in ("tendencia_lineal_ruido", "estacional", "exponencial", "paseo_aleatorio", "lineal_exacta_empate"):
    s = gen.serie(nombre)
    casos[nombre] = (s, gen.objetivo(s, 11), 2020)
H = tuple(range(1, 25))
dif = 0
for nombre, (serie, (anio, mes), base) in casos.items():
    r = sp.ejecutar_proyeccion(serie, anio, mes, base)
    viejo = sp.seleccionar_modelo_por_rmse_oos_global(ejecutar_backtesting_comparativo(serie, horizontes=H, anio_base=base), H)
    igual = viejo == r["modelo_codigo"]
    dif += not igual
    print(f"{nombre:40} productivo={r['modelo_codigo']:28} heredado={viejo!s:28} {'IGUAL' if igual else 'DISTINTO'}")
print(f"casos={len(casos)} distintos={dif}")
