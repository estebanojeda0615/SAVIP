"""Procedencia: compara el bytecode de app_icociv empaquetado en SAVIP.exe con el compilado desde una fuente Git.

Uso: python procedencia_bytecode.py <pyz_dir_extraido> <raiz_fuente> <salida.txt>

Para cada módulo `app_icociv.*` del PYZ:
  - se carga el código marshal empaquetado (no se ejecuta);
  - se compila la fuente correspondiente con el MISMO co_filename que trae el empaquetado y optimize=0;
  - se comparan ambos objetos de código de forma estructural y recursiva (bytecode, constantes con su tipo,
    nombres, variables, números de línea, tabla de líneas y de excepciones, flags, aridad, stacksize y los
    objetos de código anidados). No se usa marshal.dumps porque sus bytes dependen de banderas de referencia
    e internado que varían entre procesos sin cambiar el código.
Además informa los módulos de la fuente que no están en el PYZ y viceversa.
"""
import marshal
import sys
import types
from pathlib import Path


ATRIBUTOS = ("co_code", "co_names", "co_varnames", "co_freevars", "co_cellvars", "co_name", "co_qualname",
             "co_firstlineno", "co_linetable", "co_exceptiontable", "co_flags", "co_argcount",
             "co_posonlyargcount", "co_kwonlyargcount", "co_nlocals", "co_stacksize")


def canon_const(k):
    """Constante canónica con su tipo. Los frozenset se ordenan: su repr depende del hash aleatorio del proceso."""
    if isinstance(k, types.CodeType):
        return canon(k)
    if isinstance(k, frozenset):
        return ("frozenset", tuple(sorted(repr(canon_const(e)) for e in k)))
    if isinstance(k, tuple):
        return ("tuple", tuple(canon_const(e) for e in k))
    if isinstance(k, float):
        return ("float", k.hex())
    return (type(k).__name__, repr(k))


def canon(c):
    """Forma canónica de un objeto de código, sin co_filename."""
    return tuple(getattr(c, a) for a in ATRIBUTOS) + (tuple(canon_const(k) for k in c.co_consts),)


def main(pyz_dir: str, raiz: str, salida: str):
    pyz = Path(pyz_dir) / "pyz"
    raiz = Path(raiz)
    lineas, iguales, distintos, faltan = [], 0, [], []
    empaquetados = sorted(p.stem for p in pyz.glob("app_icociv*.code"))
    for mod in empaquetados:
        crudo = (pyz / f"{mod}.code").read_bytes()
        codigo = marshal.loads(crudo)
        rel = Path(*mod.split("."))
        fuente = raiz / rel / "__init__.py" if (raiz / rel).is_dir() else raiz / rel.with_suffix(".py")
        if not fuente.is_file():
            faltan.append(mod)
            lineas.append(f"FALTA_EN_FUENTE\t{mod}")
            continue
        propio = compile(fuente.read_bytes(), codigo.co_filename, "exec", dont_inherit=True, optimize=0)
        if canon(propio) == canon(codigo):
            iguales += 1
            lineas.append(f"IGUAL\t{mod}")
        else:
            distintos.append(mod)
            lineas.append(f"DISTINTO\t{mod}")
    en_fuente = sorted(
        ".".join(p.relative_to(raiz).with_suffix("").parts).removesuffix(".__init__")
        for p in (raiz / "app_icociv").rglob("*.py")
    )
    solo_fuente = sorted(set(en_fuente) - set(empaquetados))
    resumen = (f"fuente={raiz}\nmodulos_empaquetados={len(empaquetados)} iguales={iguales} "
               f"distintos={len(distintos)} sin_fuente={len(faltan)} solo_en_fuente={len(solo_fuente)}\n"
               f"distintos: {distintos}\nsin_fuente: {faltan}\nsolo_en_fuente: {solo_fuente}\n")
    Path(salida).write_text(resumen + "\n".join(lineas) + "\n", encoding="utf-8", newline="\n")
    print(resumen)


if __name__ == "__main__":
    main(*sys.argv[1:4])
