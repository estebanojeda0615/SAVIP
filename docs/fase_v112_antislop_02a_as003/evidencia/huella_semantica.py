"""Fase 2A (AS-003): huella semántica del motor y la economía, para comparar antes/después de cada lote.

Uso (desde la raíz de una copia del repositorio):
    python huella_semantica.py capturar <salida.json>
    python huella_semantica.py comparar <antes.json> <despues.json>

Captura, para los 5 escenarios sintéticos del Golden Master del motor y los horizontes consultados 1, 11, 23 y 24:
  - el resultado COMPLETO de `ejecutar_proyeccion` (todas las claves públicas y anidadas: modelo, segundo,
    RMSErect, pares, W*, trayectoria de 24 meses, tabla por horizonte con MAE(h), backtesting, factibilidad...),
    sin los campos de reloj;
  - el SSE exacto (Fraction como texto) y el RMSErect de los 21 candidatos sobre la muestra común;
  - la economía, el empalme y los rechazos de `tests/fixtures/fase0/captura.py`.
La comparación es EXACTA (sin tolerancia): debe ejecutarse en el mismo equipo y entorno.
"""
import json
import re
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path.cwd()))
from app_icociv.proyeccion import servicio_proyeccion as sp  # noqa: E402
from tests.fixtures.fase0 import captura, generadores as gen  # noqa: E402

HORIZONTES = (1, 11, 23, 24)
RELOJ = ("timestamp", "fecha_calculo", "fecha_hora", "generado_en")


def sin_reloj(x):
    if isinstance(x, dict):
        return {k: sin_reloj(v) for k, v in x.items() if not any(r in str(k).lower() for r in RELOJ)}
    if isinstance(x, list):
        return [sin_reloj(v) for v in x]
    return x


def a_json(x):
    """Serialización estable de cualquier objeto del resultado (DataFrames como registros)."""
    if hasattr(x, "to_dict") and hasattr(x, "columns"):
        return {"__dataframe__": list(map(str, x.columns)), "filas": a_json(x.astype(object).to_dict("records"))}
    if hasattr(x, "to_dict") and hasattr(x, "index"):
        return {"__serie__": a_json(x.astype(object).to_dict())}
    if isinstance(x, dict):
        return {str(k): a_json(v) for k, v in x.items()}
    if isinstance(x, (list, tuple, set)):
        return [a_json(v) for v in x]
    if hasattr(x, "item") and not isinstance(x, (str, bytes)):
        try:
            return a_json(x.item())
        except (ValueError, AttributeError):
            pass
    if hasattr(x, "tolist"):
        return a_json(x.tolist())
    if isinstance(x, float):
        return repr(x)  # exacto, incluye nan/inf
    if isinstance(x, (str, int, bool)) or x is None:
        return x
    return re.sub(r" at 0x[0-9A-Fa-f]+", "", repr(x))  # funciones/objetos: sin dirección de memoria


def capturar() -> dict:
    salida = {"motor": {}, "economico": captura.capturar_economico(), "rechazos": captura.capturar_rechazos()}
    for nombre in gen.ESCENARIOS_MOTOR:
        df = gen.serie(nombre)
        for h in HORIZONTES:
            anio, mes = gen.objetivo(df, h)
            with patch.object(sp, "_seleccionar_modelo_rectangular", wraps=sp._seleccionar_modelo_rectangular) as espia:
                r = sp.ejecutar_proyeccion(df, anio, mes, 2020)
            matriz, modelos = espia.call_args.args
            datos = matriz["datos"]
            comunes = sorted(set.intersection(*(set(datos[m]) for m in modelos)))
            sse = {m: str(sp._sse_exacto([datos[m][p][0] for p in comunes])) for m in modelos}
            salida["motor"][f"{nombre}|h{h}"] = {
                "llamadas_selector": espia.call_count,
                "candidatos": list(modelos),
                "pares_comunes": [list(p) for p in comunes],
                "sse_exacto": sse,
                "claves_publicas": sorted(map(str, r)),
                "resultado": sin_reloj(a_json(r)),
            }
    return salida


def diferencias(a, b, ruta="$", salida=None):
    salida = [] if salida is None else salida
    if type(a) is not type(b):
        salida.append(f"{ruta}: tipo {type(a).__name__} != {type(b).__name__}")
    elif isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                salida.append(f"{ruta}.{k}: {'falta antes' if k not in a else 'falta después'}")
            else:
                diferencias(a[k], b[k], f"{ruta}.{k}", salida)
    elif isinstance(a, list):
        if len(a) != len(b):
            salida.append(f"{ruta}: longitud {len(a)} != {len(b)}")
        for i, (x, y) in enumerate(zip(a, b)):
            diferencias(x, y, f"{ruta}[{i}]", salida)
    elif a != b:
        salida.append(f"{ruta}: {a!r} != {b!r}")
    return salida


if __name__ == "__main__":
    if sys.argv[1] == "capturar":
        datos = capturar()
        Path(sys.argv[2]).write_text(json.dumps(datos, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
        print(f"capturados {len(datos['motor'])} casos de motor, economía y rechazos -> {sys.argv[2]}")
    else:
        a = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
        b = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
        dif = diferencias(a, b)
        print(f"casos de motor: {len(a['motor'])} / {len(b['motor'])}; diferencias exactas: {len(dif)}")
        for linea in dif[:50]:
            print("  ", linea)
        sys.exit(1 if dif else 0)
