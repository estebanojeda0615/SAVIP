"""Lote 2D-1 (G4.2): retira por AST, de servicio_proyeccion.py, EXACTAMENTE las seis definiciones autorizadas.

Para cada definición borra desde su primera línea hasta su `end_lineno` más las dos líneas en blanco separadoras (se
exige que lo sean). Después verifica que:
  - el nuevo módulo tiene las mismas definiciones de nivel superior menos las seis, en el mismo orden;
  - cada definición conservada y cada sentencia de nivel de módulo es idéntica en `ast.dump` (sin posiciones);
  - los dos auxiliares compartidos (_tipo_uso_horizonte, _mayor_horizonte_permitido) siguen presentes e idénticos;
  - ningún nombre importado queda sin uso por el retiro (comparación de nombres usados antes/después).
Uso: python retirar_2d1.py <ruta servicio_proyeccion.py>   (reescribe el archivo solo si todas las comprobaciones pasan)
"""
import ast
import sys

SEIS = ["determinar_horizonte_maximo_estadistico", "_serializar_evaluaciones_horizonte", "_item_horizonte_global",
        "_mayor_horizonte_con", "_ultimo_horizonte_por_clasificacion", "_evidencia_horizonte"]
COMPARTIDOS = ["_tipo_uso_horizonte", "_mayor_horizonte_permitido"]
ruta = sys.argv[1]
src = open(ruta, encoding="utf-8").read()
L = src.split("\n")
arbol = ast.parse(src)
tops = {n.name: n for n in arbol.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
assert all(n in tops for n in SEIS + COMPARTIDOS)
borrar = set()
total_def = 0
for n in SEIS:
    f = tops[n]
    ini = min([f.lineno] + [d.lineno for d in f.decorator_list])
    total_def += f.end_lineno - ini + 1
    for extra in (f.end_lineno + 1, f.end_lineno + 2):
        assert L[extra - 1] == "", (n, extra)
    borrar.update(range(ini, f.end_lineno + 3))
nuevo = "\n".join(l for i, l in enumerate(L, 1) if i not in borrar)
arbol2 = ast.parse(nuevo)


def firma(nodos):
    return [(getattr(n, "name", type(n).__name__), ast.dump(n, include_attributes=False)) for n in nodos]


antes = [x for x in firma(arbol.body) if x[0] not in SEIS]
despues = firma(arbol2.body)
assert antes == despues, "cambió alguna definición o sentencia ajena a las seis"
tops2 = {n.name for n in arbol2.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
assert not (set(SEIS) & tops2) and set(COMPARTIDOS) <= tops2


def usados(a):
    return {n.id for n in ast.walk(a) if isinstance(n, ast.Name)} | {n.attr for n in ast.walk(a) if isinstance(n, ast.Attribute)}


importados = set()
for n in arbol.body:
    if isinstance(n, (ast.Import, ast.ImportFrom)):
        importados |= {(a.asname or a.name).split(".")[0] for a in n.names}
huerfanos = sorted(i for i in importados if i in usados(arbol) and i not in usados(arbol2))
assert not huerfanos, f"imports que quedarían sin uso: {huerfanos}"
open(ruta, "w", encoding="utf-8", newline="\n").write(nuevo)
print(f"retiradas {len(SEIS)} definiciones: {total_def} líneas de definición; {len(borrar)} líneas en total "
      f"(con separadores); definiciones de nivel superior {len(tops)} -> {len(tops2)}; compartidos presentes; "
      f"resto idéntico en AST; imports huérfanos: ninguno")
