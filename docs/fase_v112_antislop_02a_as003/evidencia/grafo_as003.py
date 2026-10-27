"""Fase 2A (AS-003): grafo de referencias conservador entre definiciones de nivel superior.

Uso: python grafo_as003.py <raiz_del_repo> <salida.json>

Nodos: funciones y clases de nivel superior de app_icociv/** (una clase incluye todos sus métodos).
Aristas (conservadoras, sobreestiman el uso):
  - nombre usado (ast.Name) resuelto en el propio módulo o por `from X import a [as b]`, en cualquier nivel;
  - atributo `alias.a` cuando `alias` es un módulo importado de app_icociv;
  - cualquier atributo `.a` o cadena literal igual al nombre de una definición de app_icociv (getattr, patch,
    tablas de despacho, conexiones Qt por nombre): se enlaza con TODAS las definiciones de ese nombre.
  - Las cadenas "ruta.py::nombre" (fichas de criterios.py) NO son aristas: se registran como citas documentales (D).
Raíces:
  - producción: sentencias de nivel de módulo de aplicacion.py y de cada módulo de app_icociv (no def/class);
  - scripts: pruebas/*.py y scripts/*.py completos (contratos S);
  - tests: tests/**/*.py completos (solo T).
Salida: por definición, si es alcanzable desde producción, desde scripts y desde tests, y quién la referencia.
"""
import ast
import json
import sys
from collections import defaultdict
from pathlib import Path

raiz = Path(sys.argv[1])


def modulo_de(ruta: Path) -> str:
    return ".".join(ruta.relative_to(raiz).with_suffix("").parts)


archivos_app = sorted(p for p in (raiz / "app_icociv").rglob("*.py"))
defs = {}  # "mod:nombre" -> (ruta, ini, fin, tipo)
por_nombre = defaultdict(set)
documentales = defaultdict(set)  # clave -> módulos que la citan como ubicación documental
arboles = {}
for p in archivos_app:
    arbol = ast.parse(p.read_text(encoding="utf-8-sig"))
    mod = modulo_de(p)
    arboles[mod] = (p, arbol)
    for n in arbol.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            clave = f"{mod}:{n.name}"
            defs[clave] = (str(p.relative_to(raiz)).replace("\\", "/"), n.lineno, n.end_lineno,
                           "class" if isinstance(n, ast.ClassDef) else "def")
            por_nombre[n.name].add(clave)
modulos_app = set(arboles)


def resolver(mod_actual: str, nodo: ast.AST) -> set[str]:
    """Referencias de un subárbol a definiciones de app_icociv."""
    alias_nombre = {}   # nombre local -> clave
    alias_modulo = {}   # nombre local -> módulo
    for n in ast.walk(nodo):
        if isinstance(n, ast.ImportFrom) and n.module:
            base = n.module
            if n.level:
                partes = mod_actual.split(".")[: -n.level]
                base = ".".join(partes + ([n.module] if n.module else []))
            for a in n.names:
                local = a.asname or a.name
                if f"{base}:{a.name}" in defs:
                    alias_nombre[local] = f"{base}:{a.name}"
                elif f"{base}.{a.name}" in modulos_app:
                    alias_modulo[local] = f"{base}.{a.name}"
        elif isinstance(n, ast.Import):
            for a in n.names:
                if a.name in modulos_app:
                    alias_modulo[a.asname or a.name] = a.name
    refs = set()
    for n in ast.walk(nodo):
        if isinstance(n, ast.Name):
            if n.id in alias_nombre:
                refs.add(alias_nombre[n.id])
            elif f"{mod_actual}:{n.id}" in defs:
                refs.add(f"{mod_actual}:{n.id}")
        elif isinstance(n, ast.Attribute):
            if isinstance(n.value, ast.Name) and n.value.id in alias_modulo and f"{alias_modulo[n.value.id]}:{n.attr}" in defs:
                refs.add(f"{alias_modulo[n.value.id]}:{n.attr}")
            else:
                refs |= por_nombre.get(n.attr, set())
        elif isinstance(n, ast.Constant) and isinstance(n.value, str):
            if n.value in por_nombre:  # getattr/patch/despacho por nombre exacto
                refs |= por_nombre[n.value]
            elif "::" in n.value:  # ubicación documental "ruta.py::nombre" (criterios.py): contrato D, no llamada
                for k in por_nombre.get(n.value.split("::")[-1].strip(), ()):
                    documentales[k].add(mod_actual)
    return refs


def alias_de_modulo(mod: str, arbol: ast.Module) -> ast.Module:
    """Imports de nivel de módulo, para resolver nombres dentro de las definiciones."""
    return ast.Module(body=[n for n in arbol.body if isinstance(n, (ast.Import, ast.ImportFrom))], type_ignores=[])


aristas = defaultdict(set)
raices_prod = set()
for mod, (p, arbol) in arboles.items():
    imports = [n for n in arbol.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    for n in arbol.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            sub = ast.Module(body=imports + [n], type_ignores=[])
            aristas[f"{mod}:{n.name}"] |= resolver(mod, sub) - {f"{mod}:{n.name}"}
        elif not isinstance(n, (ast.Import, ast.ImportFrom)):
            raices_prod |= resolver(mod, ast.Module(body=imports + [n], type_ignores=[]))


def raices_de(rutas) -> dict[str, set[str]]:
    salida = defaultdict(set)
    for p in rutas:
        try:
            arbol = ast.parse(p.read_text(encoding="utf-8-sig"))
        except SyntaxError:
            continue
        for r in resolver(modulo_de(p), arbol):
            salida[r].add(str(p.relative_to(raiz)).replace("\\", "/"))
    return salida


ap = raices_de([raiz / "aplicacion.py"])
raices_prod |= set(ap)
scripts = raices_de(sorted((raiz / "pruebas").glob("*.py")) + sorted((raiz / "scripts").glob("*.py")))
tests = raices_de(sorted((raiz / "tests").rglob("*.py")))


def cierre(semillas: set[str]) -> set[str]:
    vistos, pila = set(), list(semillas)
    while pila:
        x = pila.pop()
        if x in vistos:
            continue
        vistos.add(x)
        pila.extend(aristas.get(x, ()))
    return vistos


prod = cierre(raices_prod)
scr = cierre(set(scripts))
tst = cierre(set(tests))
inversas = defaultdict(set)
for a, bs in aristas.items():
    for b in bs:
        inversas[b].add(a)

salida = {}
for clave, (ruta, ini, fin, tipo) in defs.items():
    salida[clave] = {
        "archivo": ruta, "ini": ini, "fin": fin, "lineas": fin - ini + 1, "tipo": tipo,
        "produccion": clave in prod, "scripts": clave in scr, "tests": clave in tst,
        "referenciado_por": sorted(inversas.get(clave, ())),
        "scripts_directos": sorted(scripts.get(clave, ())),
        "tests_directos": sorted(tests.get(clave, ())),
        "citas_documentales": sorted(documentales.get(clave, ())),
    }
Path(sys.argv[2]).write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")
no_prod = {k: v for k, v in salida.items() if not v["produccion"]}
print(f"definiciones: {len(salida)}; alcanzables desde producción: {len(prod & set(defs))}; no alcanzables: {len(no_prod)}")
por_archivo = defaultdict(lambda: [0, 0])
for k, v in no_prod.items():
    por_archivo[v["archivo"]][0] += 1
    por_archivo[v["archivo"]][1] += v["lineas"]
for a, (n, l) in sorted(por_archivo.items(), key=lambda x: -x[1][1]):
    print(f"  {a}: {n} definiciones, {l} líneas")
