"""Localiza en qué difiere un objeto de código empaquetado del compilado desde una fuente (diagnóstico).
Uso: python diff_codigo.py <pyz_dir> <raiz_fuente> <modulo>"""
import marshal
import sys
import types
from pathlib import Path


def recorrer(a, b, ruta, salida):
    for attr in ("co_code", "co_consts", "co_names", "co_varnames", "co_firstlineno", "co_linetable",
                 "co_exceptiontable", "co_flags", "co_argcount", "co_kwonlyargcount", "co_qualname"):
        x, y = getattr(a, attr), getattr(b, attr)
        if attr == "co_consts":
            if len(x) != len(y):
                salida.append(f"{ruta}.co_consts: longitud {len(x)} != {len(y)}")
            for i, (cx, cy) in enumerate(zip(x, y)):
                if isinstance(cx, types.CodeType) and isinstance(cy, types.CodeType):
                    recorrer(cx, cy, f"{ruta}/{cx.co_name}", salida)
                elif cx != cy or type(cx) is not type(cy):
                    salida.append(f"{ruta}.co_consts[{i}]: {repr(cx)[:120]} != {repr(cy)[:120]}")
        elif x != y:
            salida.append(f"{ruta}.{attr}: {repr(x)[:100]} != {repr(y)[:100]}")


pyz, raiz, mod = sys.argv[1:4]
c = marshal.loads((Path(pyz) / "pyz" / f"{mod}.code").read_bytes())
rel = Path(*mod.split("."))
f = Path(raiz) / rel / "__init__.py" if (Path(raiz) / rel).is_dir() else Path(raiz) / rel.with_suffix(".py")
p = compile(f.read_bytes(), c.co_filename, "exec", dont_inherit=True, optimize=0)
out = []
recorrer(c, p, mod, out)
print(f"{mod}: {len(out)} diferencias (empaquetado != fuente)")
print("\n".join(out[:15]))
