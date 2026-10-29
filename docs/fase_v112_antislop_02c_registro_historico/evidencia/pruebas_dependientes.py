"""Fase 2C (AS-003): pruebas que dependen de las definiciones heredadas, por función de prueba y tipo de uso.

Uso: python pruebas_dependientes.py <raiz_del_repo> <grafo.json> <collect.txt> <salida.json>

- Heredadas: definiciones de servicio_proyeccion.py, modelos_interpretables.py y validacion_series.py NO alcanzables
  desde producción según el grafo de grafo_as003.py (Fase 2A).
- Por cada función de prueba (test_* de nivel superior o en clase) se reúnen las referencias de su cuerpo y, de forma
  transitiva, las de los helpers y fixtures del mismo archivo que usa. Tipos de uso:
    llamada   el nombre se llama: f(...), mod.f(...)
    patch     patch.object(mod, "f") o patch("...f")
    inspect   inspect.getsource(f) / getsource(mod.f)
    cadena    el nombre aparece en una cadena literal (p. ej. aserciones sobre el texto de la fuente)
    import    solo se importa (o se lista) sin usarse de otra forma
- Los ids se expanden con la salida de `pytest --collect-only -q` (parametrizaciones incluidas).
- Archivos de estilo script (sin funciones test_*, no recolectados por pytest): cada función pública de nivel superior
  se registra como comprobación «no recolectada».
- Homónimos: los nombres genéricos (_numero, _ratio, _fmt, _mejor_por) solo cuentan si el archivo importa el módulo
  heredado que los define (p. ej. tests/test_fase_4i_p2 usa otro `_numero`, de reportes.sesion_modulos).
"""
import ast
import importlib.util
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

raiz, grafo, collect, salida = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4])
g = json.load(open(grafo, encoding="utf-8"))
ALCANCE = ("servicio_proyeccion.py", "modelos_interpretables.py", "validacion_series.py")
heredadas = {k.split(":")[1] for k, v in g.items() if v["archivo"].endswith(ALCANCE) and not v["produccion"]}
spec = importlib.util.spec_from_file_location("pf", raiz / "scripts" / "pruebas_fase0.py")
pf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pf)
esenciales = set(pf.ESENCIALES)
deseleccionadas = set(getattr(pf, "GUI_NODOS", ()))


def usos_directos(nodo):
    """{nombre heredado: {tipos}} y nombres locales llamados/usados (para la transitividad)."""
    usos = defaultdict(set)
    locales = set()
    dentro_inspect = set()
    for n in ast.walk(nodo):
        if isinstance(n, ast.Call):
            f = n.func
            nombre_f = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else None)
            if nombre_f == "getsource":
                for a in n.args:
                    for m in ast.walk(a):
                        dentro_inspect.add(id(m))
                        nm = m.attr if isinstance(m, ast.Attribute) else (m.id if isinstance(m, ast.Name) else None)
                        if nm in heredadas:
                            usos[nm].add("inspect")
            if nombre_f in ("object", "patch") or (isinstance(f, ast.Attribute) and f.attr == "object"):
                for a in n.args:
                    if isinstance(a, ast.Constant) and isinstance(a.value, str):
                        nm = a.value.split(".")[-1]
                        if nm in heredadas:
                            usos[nm].add("patch")
            if nombre_f in heredadas and id(n.func) not in dentro_inspect:
                usos[nombre_f].add("llamada")
    for n in ast.walk(nodo):
        if isinstance(n, ast.Name):
            locales.add(n.id)
            if n.id in heredadas and not usos.get(n.id):
                usos[n.id].add("import")
        elif isinstance(n, ast.Attribute):
            locales.add(n.attr)
            if n.attr in heredadas and not usos.get(n.attr):
                usos[n.attr].add("import")
        elif isinstance(n, ast.Constant) and isinstance(n.value, str):
            for h in heredadas:
                if re.search(r"\b%s\b" % re.escape(h), n.value) and "patch" not in usos.get(h, set()):
                    usos[h].add("cadena")
        elif isinstance(n, ast.arg):
            locales.add(n.arg)
    return usos, locales


GENERICOS = {"_numero": "modelos_interpretables", "_ratio": "modelos_interpretables", "_fmt": "modelos_interpretables",
             "_mejor_por": "modelos_interpretables"}
resultado = []
for archivo in sorted((raiz / "tests").rglob("*.py")):
    rel = str(archivo.relative_to(raiz)).replace("\\", "/")
    texto = archivo.read_text(encoding="utf-8-sig")
    arbol = ast.parse(texto)
    ayudantes = {}
    pruebas = []
    for n in arbol.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if n.name.startswith("test_"):
                pruebas.append(n)
            else:
                ayudantes[n.name] = n
        elif isinstance(n, ast.ClassDef):
            for m in n.body:
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and m.name.startswith("test_"):
                    pruebas.append(m)
        elif isinstance(n, ast.Assign):  # tablas a nivel de módulo (p. ej. listas de propiedades/mutantes)
            for t in n.targets:
                if isinstance(t, ast.Name):
                    ayudantes[t.id] = n
    estilo_script = not pruebas
    if estilo_script:
        pruebas = [n for nombre, n in list(ayudantes.items())
                   if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and not nombre.startswith("_")]
    cache = {}

    def usos_de(nombre, visitados=()):
        if nombre in cache:
            return cache[nombre]
        u, loc = usos_directos(ayudantes[nombre])
        total = defaultdict(set, {k: set(v) for k, v in u.items()})
        for l in loc:
            if l in ayudantes and l not in visitados and l != nombre:
                for k, v in usos_de(l, visitados + (nombre,)).items():
                    total[k] |= v
        cache[nombre] = total
        return total

    for p in pruebas:
        u, loc = usos_directos(p)
        total = defaultdict(set, {k: set(v) for k, v in u.items()})
        for l in loc:
            if l in ayudantes:
                for k, v in usos_de(l).items():
                    total[k] |= v
        for nombre, modulo in GENERICOS.items():
            if nombre in total and modulo not in texto:
                del total[nombre]
        if total:
            resultado.append({"archivo": rel, "prueba": p.name, "linea": p.lineno, "esencial": rel in esenciales,
                              "recolectada": not estilo_script,
                              "usos": {k: sorted(v) for k, v in sorted(total.items())}})

ids = [l.strip() for l in collect.read_text(encoding="utf-8").splitlines() if "::" in l]
for r in resultado:
    pref = f"{r['archivo']}::{r['prueba']}"
    if not r["recolectada"]:
        r["ids"] = [pref + " (no recolectada por pytest)"]
        r["deseleccionada_en_esenciales"] = False
        continue
    r["ids"] = [i for i in ids if i == pref or i.startswith(pref + "[") or re.fullmatch(re.escape(r["archivo"]) + r"::\w+::" + re.escape(r["prueba"]) + r"(\[.*\])?", i)]
    r["deseleccionada_en_esenciales"] = any(i in deseleccionadas for i in r["ids"])
salida.write_text(json.dumps({"heredadas": sorted(heredadas), "pruebas": resultado}, ensure_ascii=False, indent=1),
                  encoding="utf-8")
ess = [r for r in resultado if r["esencial"]]
print(f"heredadas: {len(heredadas)}; funciones de prueba dependientes: {len(resultado)} "
      f"({len(ess)} esenciales); ids: {sum(len(r['ids']) for r in resultado)} "
      f"({sum(len(r['ids']) for r in ess)} esenciales)")
por_archivo = defaultdict(lambda: [0, 0, False])
for r in resultado:
    por_archivo[r["archivo"]][0] += 1
    por_archivo[r["archivo"]][1] += len(r["ids"])
    por_archivo[r["archivo"]][2] = r["esencial"]
for a, (n, i, e) in sorted(por_archivo.items()):
    print(f"  {'ESENCIAL ' if e else 'historica'} {a}: {n} funciones, {i} ids")
