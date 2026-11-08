"""Nombres importados a nivel de módulo que no se usan en el archivo (AST). Compara base y HEAD para aislar los
huérfanos NUEVOS. Uso: python imports_huerfanos.py <raiz_base> <raiz_head> <archivo> [<archivo>...]"""
import ast
import sys
from pathlib import Path


def huerfanos(ruta: Path) -> set[str]:
    if not ruta.exists():
        return set()
    arbol = ast.parse(ruta.read_text(encoding="utf-8-sig"))
    importados = {}
    for n in arbol.body:
        if isinstance(n, ast.Import):
            for a in n.names:
                importados[(a.asname or a.name).split(".")[0]] = n.lineno
        elif isinstance(n, ast.ImportFrom) and n.module != "__future__":
            for a in n.names:
                importados[a.asname or a.name] = n.lineno
    usados = {x.id for x in ast.walk(arbol) if isinstance(x, ast.Name)} | \
             {x.value.id for x in ast.walk(arbol) if isinstance(x, ast.Attribute) and isinstance(x.value, ast.Name)}
    texto = ruta.read_text(encoding="utf-8-sig")
    return {k for k in importados if k not in usados and f"'{k}'" not in texto and f'"{k}"' not in texto}


base, head = Path(sys.argv[1]), Path(sys.argv[2])
for rel in sys.argv[3:]:
    b, h = huerfanos(base / rel), huerfanos(head / rel)
    print(f"{rel}: nuevos={sorted(h - b)} preexistentes={sorted(h & b)} resueltos={sorted(b - h)}")
