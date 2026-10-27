"""Fase 2A (AS-003): retira definiciones de nivel superior por nombre exacto, usando los límites del AST.

Uso: python retirar_definiciones.py <archivo.py> <nombre> [<nombre> ...]

Borra cada `def` (con sus decoradores) desde su primera línea hasta `end_lineno`, más las líneas en blanco que
la siguen, de modo que se conserve el espaciado de dos líneas entre definiciones. Falla si un nombre no existe,
aparece más de una vez o no es de nivel superior. No toca nada más del archivo.
"""
import ast
import sys
from pathlib import Path

ruta = Path(sys.argv[1])
nombres = sys.argv[2:]
texto = ruta.read_text(encoding="utf-8-sig")
bom = ruta.read_bytes().startswith(b"\xef\xbb\xbf")
fin_linea = "\r\n" if "\r\n" in texto else "\n"
lineas = texto.splitlines(keepends=True)
arbol = ast.parse(texto)
rangos = []
for nombre in nombres:
    nodos = [n for n in arbol.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == nombre]
    assert len(nodos) == 1, f"{nombre}: {len(nodos)} definiciones de nivel superior"
    n = nodos[0]
    ini = min([n.lineno] + [d.lineno for d in n.decorator_list]) - 1
    fin = n.end_lineno
    while fin < len(lineas) and not lineas[fin].strip():
        fin += 1
    rangos.append((ini, fin, nombre))
for ini, fin, nombre in sorted(rangos, reverse=True):
    print(f"retirada {nombre}: líneas {ini + 1}-{fin} ({fin - ini})")
    del lineas[ini:fin]
nuevo = "".join(lineas)
if nuevo.endswith(fin_linea * 2):  # la definición retirada era la última: sin líneas en blanco al final
    nuevo = nuevo.rstrip() + fin_linea
ast.parse(nuevo)
ruta.write_bytes((b"\xef\xbb\xbf" if bom else b"") + nuevo.encode("utf-8"))
