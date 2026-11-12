"""G3 (solo lectura, AST): qué funciones test_* de tests/, pruebas/ y scripts/ nombran -directamente o vía
helpers del mismo archivo, incluidos métodos de clase- los símbolos 2D-1 (los 6 objetivo y los 2 compartidos)
y las funciones AS-004 del generador. Distingue uso como nombre/atributo y como cadena literal.

Uso: python usos_por_test_2d1.py <raiz>
"""
import ast
import sys
from pathlib import Path

OBJETIVO = {"determinar_horizonte_maximo_estadistico", "_serializar_evaluaciones_horizonte", "_item_horizonte_global",
            "_mayor_horizonte_con", "_ultimo_horizonte_por_clasificacion", "_evidencia_horizonte"}
COMPARTIDOS = {"_tipo_uso_horizonte", "_mayor_horizonte_permitido"}
AS004 = {"_lineas_factibilidad", "_lineas_horizontes", "_lineas_determinacion_horizonte"}
TODOS = OBJETIVO | COMPARTIDOS | AS004
raiz = Path(sys.argv[1])


def nombres(n):
    out = set()
    for x in ast.walk(n):
        if isinstance(x, ast.Name) and x.id in TODOS:
            out.add(x.id)
        elif isinstance(x, ast.Attribute) and x.attr in TODOS:
            out.add(x.attr)
        elif isinstance(x, ast.alias) and (x.asname or x.name) in TODOS:
            out.add(x.name)
        elif isinstance(x, ast.Constant) and isinstance(x.value, str):
            for s in TODOS:
                if s in x.value:
                    out.add("cadena:" + s)
    return out


def todos_nombres(n):
    return {x.id for x in ast.walk(n) if isinstance(x, ast.Name)} | {x.attr for x in ast.walk(n) if isinstance(x, ast.Attribute)}


archivos = sorted(list((raiz / "tests").rglob("*.py")) + list((raiz / "pruebas").glob("*.py")) + list((raiz / "scripts").glob("*.py")))
for archivo in archivos:
    texto = archivo.read_text(encoding="utf-8-sig")
    if not any(s in texto for s in TODOS):
        continue
    arbol = ast.parse(texto)
    funcs = {}
    for n in arbol.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs[n.name] = n
        elif isinstance(n, ast.ClassDef):
            for m in n.body:
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    funcs[f"{n.name}::{m.name}"] = m
    modulo = [f"L{n.lineno}:{sorted(nombres(n))}" for n in arbol.body
              if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and nombres(n)]
    propios = {f: nombres(n) for f, n in funcs.items()}
    cierre = {f: set(s) for f, s in propios.items()}
    cambio = True
    while cambio:
        cambio = False
        for f, n in funcs.items():
            for g in todos_nombres(n):
                for h in list(cierre):
                    if h.split("::")[-1] == g and h != f and not cierre[h] <= cierre[f]:
                        cierre[f] |= cierre[h]; cambio = True
    tests = [f for f in funcs if f.split("::")[-1].startswith("test_")]
    afect = [t for t in tests if cierre[t]]
    print(f"== {archivo.relative_to(raiz).as_posix()}  tests={len(tests)}  afectados={len(afect)}")
    for m in modulo:
        print("   nivel de módulo", m)
    for t in afect:
        print(f"   {t} L{funcs[t].lineno}-{funcs[t].end_lineno}: {sorted(cierre[t])}")
