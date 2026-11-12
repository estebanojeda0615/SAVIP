"""AS-004 (diagnóstico, solo lectura): productores y consumidores de las claves que devuelve
`determinar_horizonte_maximo_estadistico`.

Uso: python mapa_claves_as004.py <raiz_repo> <grafo.json> <salida.csv>

- Claves: las del dict literal que devuelve esa función (AST).
- Productor: dict literal con la clave como llave, o asignación `x["clave"] = ...`.
- Consumidor: `x.get("clave"...)`, `x["clave"]` en lectura, o cadena igual a la clave en otro contexto
  (se marca como «cadena»; p. ej. listas de columnas o getattr).
- Receptor: el objeto sobre el que se lee (ast.unparse), para poder distinguir lecturas de `horizonte_info` de las de
  otros diccionarios con claves homónimas.
- Cada aparición se atribuye a la definición de nivel superior que la contiene y se cruza con el
  grafo de alcanzabilidad (grafo_as003.py): producción / scripts / tests.
Busca en app_icociv/**, aplicacion.py, tests/**, pruebas/** y scripts/**.
"""
import ast
import csv
import json
import sys
from pathlib import Path

raiz, grafo, salida = Path(sys.argv[1]), json.load(open(sys.argv[2], encoding="utf-8")), sys.argv[3]
SP = raiz / "app_icociv/proyeccion/servicio_proyeccion.py"
arbol_sp = ast.parse(SP.read_text(encoding="utf-8-sig"))
fn = next(n for n in arbol_sp.body if isinstance(n, ast.FunctionDef) and n.name == "determinar_horizonte_maximo_estadistico")
rets = [n for n in ast.walk(fn) if isinstance(n, ast.Return) and isinstance(n.value, ast.Dict)]
assert len(rets) == 1, "se esperaba un único return con dict literal"
ret = rets[0]
CLAVES = [k.value for k in ret.value.keys if isinstance(k, ast.Constant)]

archivos = sorted((raiz / "app_icociv").rglob("*.py")) + [raiz / "aplicacion.py"]
for d in ("tests", "pruebas", "scripts"):
    archivos += sorted((raiz / d).rglob("*.py"))


def modulo(p):
    return ".".join(p.relative_to(raiz).with_suffix("").parts)


filas = []
for p in archivos:
    rel = str(p.relative_to(raiz)).replace("\\", "/")
    arbol = ast.parse(p.read_text(encoding="utf-8-sig"))
    padres = {}
    for n in ast.walk(arbol):
        for h in ast.iter_child_nodes(n):
            padres[h] = n
    tops = {}
    for t in arbol.body:
        for n in ast.walk(t):
            tops[n] = t
    for n in ast.walk(arbol):
        if not (isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value in CLAVES):
            continue
        pa = padres.get(n)
        receptor = ""
        if isinstance(pa, ast.Subscript):
            receptor = ast.unparse(pa.value)
        elif isinstance(pa, ast.Call) and isinstance(pa.func, ast.Attribute):
            receptor = ast.unparse(pa.func.value)
        if isinstance(pa, ast.Dict) and n in pa.keys:
            rol = "productor:dict"
        elif isinstance(pa, ast.Subscript) and isinstance(pa.ctx, ast.Store):
            rol = "productor:asignacion"
        elif isinstance(pa, ast.Subscript):
            rol = "consumidor:subindice"
        elif isinstance(pa, ast.Call) and isinstance(pa.func, ast.Attribute) and pa.func.attr in ("get", "setdefault", "pop") and pa.args and pa.args[0] is n:
            rol = f"consumidor:.{pa.func.attr}"
        elif isinstance(pa, ast.Compare):
            rol = "consumidor:pertenencia"
        else:
            rol = "cadena"
        t = tops.get(n)
        nombre = getattr(t, "name", "<modulo>")
        if rel.startswith("app_icociv"):
            g = grafo.get(f"{modulo(p)}:{nombre}")
            alc = ("produccion" if g["produccion"] else ("scripts" if g["scripts"] else ("tests" if g["tests"] else "inalcanzable"))) if g else "nivel_modulo"
        else:
            alc = "produccion" if rel == "aplicacion.py" else rel.split("/")[0]
        filas.append([n.value, rel, n.lineno, nombre, rol, alc, receptor])

with open(salida, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["clave", "archivo", "linea", "definicion", "rol", "alcanzable_desde", "receptor"])
    w.writerows(sorted(filas))
print(len(CLAVES), "claves;", len(filas), "apariciones")
