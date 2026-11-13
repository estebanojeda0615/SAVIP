"""G4: ejecuta la sonda AS-004 con las seis definiciones 2D-1 sustituidas en memoria por stubs que fallan si se llaman
(sin editar archivos)
y compara su salida (claves de horizonte_info, columnas del CSV, fuente del encabezado) con la de la base.
Uso: python sonda_oculto.py <raiz_repo> <sonda_claves_as004.py> <sonda_base.json> <salida.json>
"""
import json
import runpy
import sys
from pathlib import Path

raiz, sonda, base_json, salida = sys.argv[1:]
sys.path.insert(0, str(Path(raiz).resolve()))
import app_icociv.proyeccion.servicio_proyeccion as sp  # noqa: E402

OBJ = ("determinar_horizonte_maximo_estadistico", "_serializar_evaluaciones_horizonte", "_item_horizonte_global",
       "_mayor_horizonte_con", "_ultimo_horizonte_por_clasificacion", "_evidencia_horizonte")
for n in OBJ:
    delattr(sp, n)
# Tras borrarlas, se sustituyen por stubs que FALLAN si alguien los llama (la sonda envuelve estos nombres con sus
# espías): cualquier llamada desde la ruta productiva aparecería como excepción y como diferencia.
def prohibida(nombre):
    def f(*a, **k):
        raise AssertionError(f"llamada a {nombre} con 2D-1 oculto")
    return f
for n in OBJ:
    setattr(sp, n, prohibida(n))
sys.argv = [sonda, raiz, salida]
runpy.run_path(sonda, run_name="__main__")
a = json.load(open(base_json, encoding="utf-8"))["escenarios"]
b = json.load(open(salida, encoding="utf-8"))["escenarios"]
dif = []
for esc in a:
    for campo in ("proyeccion_generada", "claves_historicas_presentes", "csv_columnas_historicas", "encabezado_ui_fuente"):
        if a[esc].get(campo) != b[esc].get(campo):
            dif.append((esc, campo))
print("escenarios", len(a), "diferencias", dif)
