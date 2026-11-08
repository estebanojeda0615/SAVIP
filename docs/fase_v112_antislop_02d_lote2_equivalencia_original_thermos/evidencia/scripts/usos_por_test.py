"""G1/G2: para cada archivo de pruebas, qué funciones test_* usan (directa o indirectamente vía helpers del mismo
archivo) los símbolos del par 2D-2, y qué importaciones de módulo los nombran. Análisis AST, solo lectura.
Uso: python usos_por_test.py <raiz>"""
import ast
import sys
from pathlib import Path

PAR = {"seleccionar_modelo_por_rmse_oos_global", "_errores_oos_por_par"}
raiz = Path(sys.argv[1])
for archivo in sorted(list((raiz / "tests").rglob("*.py")) + list((raiz / "pruebas").glob("*.py")) + list((raiz / "scripts").glob("*.py"))):
    texto = archivo.read_text(encoding="utf-8-sig")
    if not any(p in texto for p in PAR):
        continue
    arbol = ast.parse(texto)
    imports_modulo = []
    for nodo in arbol.body:
        if isinstance(nodo, ast.ImportFrom) and any(a.name in PAR for a in nodo.names):
            imports_modulo.append(f"L{nodo.lineno}: from {nodo.module} import {[a.name for a in nodo.names if a.name in PAR]}")
    funciones = {n.name: n for n in arbol.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}

    def nombres(n):
        out = set()
        for x in ast.walk(n):
            if isinstance(x, ast.Name):
                out.add(x.id)
            elif isinstance(x, ast.Attribute):
                out.add(x.attr)
            elif isinstance(x, ast.Constant) and isinstance(x.value, str) and x.value in PAR:
                out.add("str:" + x.value)
        return out

    directos = {f for f, n in funciones.items() if nombres(n) & PAR}
    cadenas = {f for f, n in funciones.items() if any(s.startswith("str:") for s in nombres(n))}
    cambio = True
    usa = set(directos)
    while cambio:
        cambio = False
        for f, n in funciones.items():
            if f not in usa and nombres(n) & usa:
                usa.add(f); cambio = True
    tests = [f for f in funciones if f.startswith("test_")]
    print(f"== {archivo.relative_to(raiz)}  tests={len(tests)}  usan_par={len([t for t in tests if t in usa])}")
    for i in imports_modulo:
        print("   import de módulo", i)
    for t in tests:
        marca = "USA" if t in usa else "no"
        extra = " (solo como cadena)" if t in cadenas and t not in directos - cadenas else ""
        print(f"   {marca:3} {t} L{funciones[t].lineno}{extra}")
    otros = sorted(f for f in usa if not f.startswith("test_"))
    if otros:
        print("   helpers que usan el par:", otros)
