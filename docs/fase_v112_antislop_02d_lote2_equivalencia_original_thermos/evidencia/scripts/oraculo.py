"""Oráculo neutral de equivalencia (2D-2, G0/G4). Externo a todos los árboles comparados; no copia lógica estadística.

Uso:  python -I oraculo.py <raiz_app> <salida.json> [--sin-gui]
      python -I oraculo.py --comparar <a.json> <b.json>

- `app_icociv` y `aplicacion` se importan de <raiz_app> (se verifica la ruta real del módulo).
- El arnés de captura (`tests/fixtures/fase0`: generadores, captura, captura_gui) se importa de ./arnes, copia literal
  del de 5478958; es el mismo para todas las raíces, así que las entradas son idénticas.
- Números: cada float se guarda como float.hex (distingue 1 ULP, -0.0, nan e inf); enteros, textos, None y booleanos
  con su tipo. Las listas conservan su orden. Solo se ordenan claves de diccionario.
- Sección GUI: usa el recorrido real de Fase 0 sobre la ventana (Qt offscreen). Ese arnés normaliza, en textos de
  PDF/DOCX/Excel/sesión, rutas temporales, fechas-hora e identificadores aleatorios (captura.normalizar_texto y
  captura_gui.reemplazos_ids) y convierte flotantes no finitos en None (json_estable). Es la única normalización.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import tempfile
import traceback
from pathlib import Path

AQUI = Path(__file__).resolve().parent
HORIZONTES_MOTOR = (1, 6, 11, 12, 17, 23, 24)
RELOJ = ("timestamp", "fecha_calculo", "fecha_hora", "generado_en")


def canon(x):
    """Forma canónica exacta y tipada."""
    if hasattr(x, "columns") and hasattr(x, "dtypes"):  # DataFrame
        return {"__df__": [str(c) for c in x.columns], "dtypes": [str(t) for t in x.dtypes],
                "index": canon(list(x.index)), "filas": canon(x.astype(object).values.tolist())}
    if hasattr(x, "index") and hasattr(x, "dtype") and hasattr(x, "to_dict"):  # Series
        return {"__serie__": canon(list(x.index)), "dtype": str(x.dtype), "valores": canon(x.astype(object).tolist())}
    if isinstance(x, dict):
        return {str(k): canon(v) for k, v in x.items() if not any(r in str(k).lower() for r in RELOJ)}
    if isinstance(x, (list, tuple)):
        return [canon(v) for v in x]
    if isinstance(x, (set, frozenset)):
        return {"__set__": sorted(json.dumps(canon(v), sort_keys=True) for v in x)}
    if isinstance(x, bool) or x is None or isinstance(x, str):
        return x
    if isinstance(x, int):
        return {"i": str(x)}
    if isinstance(x, float):
        return {"f": x.hex()}
    if hasattr(x, "item") and not isinstance(x, (bytes, bytearray)):
        try:
            v = x.item()
            return {"np": type(x).__name__, "v": canon(v)}
        except (ValueError, AttributeError):
            pass
    if hasattr(x, "tolist"):
        return {"arr": canon(x.tolist())}
    import re
    return {"repr": re.sub(r" at 0x[0-9A-Fa-f]+", "", repr(x))}


def protegido(fn, *a, **k):
    try:
        return {"ok": canon(fn(*a, **k))}
    except Exception as exc:  # se registra como resultado: un rechazo distinto también es una diferencia
        return {"excepcion": type(exc).__name__, "mensaje": str(exc)}


def series_extra(gen, np, pd):
    """Entradas sintéticas deterministas (semilla explícita). Son datos, no lógica."""
    def df(valores):
        return pd.DataFrame({"Periodo": gen._periodos(len(valores)), "Indice": [float(v) for v in valores]})
    r = lambda s: np.random.default_rng(s)  # noqa: E731
    base = gen.ESCENARIOS_MOTOR["tendencia_lineal_ruido"]()
    g = r(21); volatil = list(100.0 + np.cumsum(g.normal(0.2, 3.0, 72)))
    g = r(22); nivel = [100.0 + 0.2 * i + g.normal(0, 0.5) + (30.0 if i >= 36 else 0.0) for i in range(72)]
    g = r(23); casi = [100.0 + 1e-6 * g.normal() for _ in range(48)]
    g = r(24); larga = [100.0 + 0.4 * i + 3.0 * math.sin(2 * math.pi * i / 12) + g.normal(0, 0.6) for i in range(120)]
    g = r(25); minima = [100.0 + 0.5 * i + g.normal(0, 1.0) for i in range(36)]
    return {
        "volatil_72_s21": (df(volatil), (1, 12, 24)),
        "escala_x1e6": (df([v * 1e6 for v in base]), (1, 12, 24)),
        "escala_x1e-3": (df([v * 1e-3 for v in base]), (1, 12, 24)),
        "cambio_nivel_72_s22": (df(nivel), (1, 12, 24)),
        "casi_constante_48_s23": (df(casi), (1, 12, 24)),
        "larga_120_s24": (df(larga), (1, 12, 24)),
        "minima_36_s25": (df(minima), (1, 12, 24)),
        "extremo_finito_x1e150": (df([v * 1e150 for v in base]), (11,)),
    }


def capturar(raiz: Path, con_gui: bool) -> dict:
    sys.path[:0] = [str(AQUI / "arnes"), str(raiz)]
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from unittest.mock import patch

    import numpy as np
    import pandas as pd

    import app_icociv
    from app_icociv.proyeccion import servicio_proyeccion as sp
    from tests.fixtures.fase0 import captura, generadores as gen

    origen_app = Path(app_icociv.__file__).resolve()
    origen_arnes = Path(gen.__file__).resolve()
    assert raiz.resolve() in origen_app.parents, origen_app
    assert (AQUI / "arnes").resolve() in origen_arnes.parents, origen_arnes

    def proyeccion(df, h):
        anio, mes = gen.objetivo(df, h)
        with patch.object(sp, "_seleccionar_modelo_rectangular", wraps=sp._seleccionar_modelo_rectangular) as espia:
            try:
                r = sp.ejecutar_proyeccion(df, anio, mes, 2020)
            except Exception as exc:
                return {"excepcion": type(exc).__name__, "mensaje": str(exc),
                        "traza_final": traceback.format_exc().strip().splitlines()[-3:]}
        if not espia.call_count:
            return {"llamadas_selector": 0, "claves": sorted(map(str, r)), "resultado": canon(r)}
        matriz, modelos = espia.call_args.args
        datos = matriz["datos"]
        comunes = sorted(set.intersection(*(set(datos[m]) for m in modelos)))
        return {"llamadas_selector": espia.call_count, "candidatos": list(modelos), "w_estrella": canon(matriz.get("w_estrella")),
                "horizontes_matriz": canon(matriz.get("horizontes")), "pares_comunes": [list(p) for p in comunes],
                "sse_exacto": {m: str(sp._sse_exacto([datos[m][p][0] for p in comunes])) for m in modelos},
                "claves": sorted(map(str, r)), "resultado": canon(r)}

    salida = {"motor": {}, "series_extra": {}, "fixtures_horizonte_dinamico": {}}
    for nombre in gen.ESCENARIOS_MOTOR:
        df = gen.serie(nombre)
        for h in HORIZONTES_MOTOR:
            salida["motor"][f"{nombre}|h{h}"] = proyeccion(df, h)
    for nombre, (df, hs) in series_extra(gen, np, pd).items():
        for h in hs:
            salida["series_extra"][f"{nombre}|h{h}"] = proyeccion(df, h)
    fix = AQUI / "arnes" / "tests" / "fixtures" / "horizonte_dinamico"
    for archivo in ("serie_drift.csv", "serie_holt.csv"):
        df = pd.read_csv(fix / archivo, dtype={"Periodo": str})[["Periodo", "Indice"]]
        for h in (1, 12, 24):
            salida["fixtures_horizonte_dinamico"][f"{archivo}|h{h}"] = proyeccion(df, h)
    salida["rechazos"] = protegido(captura.capturar_rechazos)
    salida["economico_empalme"] = protegido(captura.capturar_economico)
    if con_gui:
        from tests.fixtures.fase0 import captura_gui as g
        with tempfile.TemporaryDirectory(prefix="oraculo_gui_") as tmp:
            salida["gui_sesion_exportables"] = protegido(g.escenario, Path(tmp))
    return salida


def resumen_hash(datos: dict) -> dict:
    h = lambda o: hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False).encode()).hexdigest()  # noqa: E731
    return {"total": h(datos), **{k: h(v) for k, v in datos.items()}}


def diferencias(a, b, ruta="$", out=None, limite=200):
    out = [] if out is None else out
    if len(out) >= limite:
        return out
    if type(a) is not type(b):
        out.append(f"{ruta}: tipo {type(a).__name__} != {type(b).__name__}")
    elif isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append(f"{ruta}.{k}: solo en {'B' if k not in a else 'A'}")
            else:
                diferencias(a[k], b[k], f"{ruta}.{k}", out, limite)
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append(f"{ruta}: longitud {len(a)} != {len(b)}")
        for i, (x, y) in enumerate(zip(a, b)):
            diferencias(x, y, f"{ruta}[{i}]", out, limite)
    elif a != b:
        out.append(f"{ruta}: {str(a)[:160]!r} != {str(b)[:160]!r}")
    return out


if __name__ == "__main__":
    if sys.argv[1] == "--comparar":
        A = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
        B = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
        for seccion in sorted(set(A["datos"]) | set(B["datos"])):
            d = diferencias(A["datos"].get(seccion), B["datos"].get(seccion), seccion)
            n = len(A["datos"].get(seccion) or {}) if isinstance(A["datos"].get(seccion), dict) else 1
            print(f"{seccion}: casos={n} diferencias={len(d)}{' (truncado a 200)' if len(d) >= 200 else ''}")
            for linea in d[:40]:
                print("   ", linea)
        print("hash A:", A["hash"]["total"], "\nhash B:", B["hash"]["total"],
              "\nIGUALES" if A["hash"]["total"] == B["hash"]["total"] else "\nDISTINTOS")
        sys.exit(0)
    raiz, destino = Path(sys.argv[1]), Path(sys.argv[2])
    datos = capturar(raiz, "--sin-gui" not in sys.argv)
    meta = {"raiz": str(raiz), "fuente_git": (raiz / ".fuente_git.txt").read_text(encoding="utf-8").strip()
            if (raiz / ".fuente_git.txt").exists() else None, "python": sys.version}
    destino.write_text(json.dumps({"meta": meta, "hash": resumen_hash(datos), "datos": datos}, ensure_ascii=False,
                                  sort_keys=True, indent=0), encoding="utf-8", newline="\n")
    print(json.dumps(resumen_hash(datos), indent=1))
