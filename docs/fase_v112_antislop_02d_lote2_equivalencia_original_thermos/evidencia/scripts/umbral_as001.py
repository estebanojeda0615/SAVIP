"""Barrido del dominio de AS-001: ¿desde qué escala de la serie difieren la original y Anti-Slop?

Uso: python -I umbral_as001.py <raiz_app>
Misma serie base (tendencia_lineal_ruido del arnés) multiplicada por 10^k; consulta H=11. Imprime, por k, si
`ejecutar_proyeccion` lanza excepción (tipo) o devuelve resultado (proyeccion_generada, modelo, y_proj en hex).
"""
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path[:0] = [str(AQUI / "arnes"), sys.argv[1]]
import warnings  # noqa: E402
warnings.simplefilter("ignore")
import pandas as pd  # noqa: E402
from app_icociv.proyeccion import servicio_proyeccion as sp  # noqa: E402
from tests.fixtures.fase0 import generadores as gen  # noqa: E402

base = gen.ESCENARIOS_MOTOR["tendencia_lineal_ruido"]()
for k in (0, 50, 100, 140, 145, 148, 150, 151, 152, 153, 154, 155, 160, 200, 300):
    df = pd.DataFrame({"Periodo": gen._periodos(len(base)), "Indice": [v * 10.0 ** k for v in base]})
    anio, mes = gen.objetivo(df, 11)
    try:
        r = sp.ejecutar_proyeccion(df, anio, mes, 2020)
        y = r.get("y_proj")
        print(f"1e{k}\tRESULTADO\tgenerada={r.get('proyeccion_generada')}\tmodelo={r.get('modelo_codigo')}\t"
              f"y_proj={float(y).hex() if isinstance(y, float) else y}")
    except Exception as exc:
        print(f"1e{k}\tEXCEPCION\t{type(exc).__name__}: {str(exc)[:80]}")
