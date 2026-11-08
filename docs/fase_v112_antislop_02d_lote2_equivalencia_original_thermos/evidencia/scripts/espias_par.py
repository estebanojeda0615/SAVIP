"""G1: espías (wraps=, sin sustituir nada) sobre el par 2D-2 mientras corre la ruta productiva completa.

Uso: python -I espias_par.py <raiz_app>
Escenarios: los 35 del motor del oráculo (5 series × 7 horizontes), los 6 de los fixtures horizonte_dinamico,
informe CSV/DOCX/PDF de una proyección y el recorrido GUI real de Fase 0 (sesión y exportables).
Imprime el número de llamadas a cada símbolo del par y al selector vigente.
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

AQUI = Path(r"C:\Pruebas SAVIP\L2\oraculo")
raiz = Path(sys.argv[1])
sys.path[:0] = [str(AQUI / "arnes"), str(raiz)]
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import warnings  # noqa: E402
warnings.simplefilter("ignore")
import pandas as pd  # noqa: E402
from app_icociv.proyeccion import servicio_proyeccion as sp  # noqa: E402
from tests.fixtures.fase0 import generadores as gen  # noqa: E402

PAR = ("seleccionar_modelo_por_rmse_oos_global", "_errores_oos_por_par")
espias = {n: patch.object(sp, n, wraps=getattr(sp, n)) for n in PAR}
vigente = patch.object(sp, "_seleccionar_modelo_rectangular", wraps=sp._seleccionar_modelo_rectangular)
activos = {n: p.start() for n, p in espias.items()}
v = vigente.start()
casos = 0
try:
    for nombre in gen.ESCENARIOS_MOTOR:
        df = gen.serie(nombre)
        for h in (1, 6, 11, 12, 17, 23, 24):
            sp.ejecutar_proyeccion(df, *gen.objetivo(df, h), 2020); casos += 1
    fix = AQUI / "arnes" / "tests" / "fixtures" / "horizonte_dinamico"
    for archivo in ("serie_drift.csv", "serie_holt.csv"):
        df = pd.read_csv(fix / archivo, dtype={"Periodo": str})[["Periodo", "Indice"]]
        for h in (1, 12, 24):
            sp.ejecutar_proyeccion(df, *gen.objetivo(df, h), 2020); casos += 1
    from tests.fixtures.fase0 import captura_gui as g
    with tempfile.TemporaryDirectory(prefix="espias_gui_") as tmp:
        g.escenario(Path(tmp)); casos += 1  # incluye informe_proyeccion (CSV/DOCX/PDF) y exportables de sesión
finally:
    llamadas = {n: m.call_count for n, m in activos.items()}
    for p in espias.values():
        p.stop()
    vigente.stop()
print(f"raiz={raiz}")
print(f"escenarios={casos} (35 motor + 6 fixtures + recorrido GUI con informe y exportables)")
for n, c in llamadas.items():
    print(f"llamadas {n}: {c}")
print(f"llamadas _seleccionar_modelo_rectangular (vigente): {v.call_count}")
