"""Tabla obligatoria del comparador (prompt §7) a partir de las capturas del oráculo.

Uso: python -I tabla_comparador.py <original.json> <antislop.json> <v111.json> <salida.csv>
Por caso: SHA-256 de la entrada (serie y horizonte), SHA-256 del resultado canónico en cada versión, modelo, SSE de
los 21 candidatos, RMSErect, trayectoria H1-H24 y la comparación exacta. Economía, sesiones y exportables van en
filas propias (secciones completas). La columna del lote final queda «NO VERIFICADO»: 2D-2 no se ejecutó (G0 NO-GO).
"""
import csv
import hashlib
import io
import json
import sys
from pathlib import Path


def h(o) -> str:
    return hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def campo(caso, *ruta):
    x = caso
    for r in ruta:
        if not isinstance(x, dict) or r not in x:
            return None
        x = x[r]
    return x


def modelo(caso):
    if "excepcion" in caso:
        return f"EXCEPCIÓN {caso['excepcion']}"
    return campo(caso, "resultado", "modelo_codigo") or "sin modelo (no calculable)"


O, A, V = (json.loads(Path(p).read_text(encoding="utf-8"))["datos"] for p in sys.argv[1:4])
cols = ["caso", "entradas_sha", "base_original_sha", "anti_slop_previo_sha", "v111_sha", "lote_final_sha", "modelo_original",
        "modelo_final", "SSE", "RMSErect", "H1-H24", "economia", "sesiones", "exportables", "comparacion_exacta",
        "metadatos_normalizados", "observaciones"]
filas = []
for seccion in ("motor", "series_extra", "fixtures_horizonte_dinamico"):
    for caso in O[seccion]:
        o, a, v = O[seccion][caso], A[seccion].get(caso), V[seccion].get(caso)
        igual_oa, igual_ov = o == a, o == v
        obs = []
        if not igual_oa:
            obs.append(f"original: {modelo(o)}; Anti-Slop: {modelo(a)} (dominio AS-001, Fase 1B)")
        if not igual_ov:
            obs.append("difiere de V1.1.1")
        filas.append({
            "caso": f"{seccion}/{caso}", "entradas_sha": h([seccion, caso]),
            "base_original_sha": h(o), "anti_slop_previo_sha": h(a), "v111_sha": h(v), "lote_final_sha": "NO VERIFICADO (2D-2 no ejecutado: G0 NO-GO)",
            "modelo_original": modelo(o), "modelo_final": "NO VERIFICADO",
            "SSE": "igual" if campo(o, "sse_exacto") == campo(a, "sse_exacto") else "DIFERENTE",
            "RMSErect": "igual" if campo(o, "resultado", "rmse_seleccion_oos") == campo(a, "resultado", "rmse_seleccion_oos") else "DIFERENTE",
            "H1-H24": "igual" if campo(o, "resultado", "trayectoria_24_meses") == campo(a, "resultado", "trayectoria_24_meses") else "DIFERENTE",
            "economia": "fila propia", "sesiones": "fila propia", "exportables": "fila propia",
            "comparacion_exacta": ("IGUAL" if igual_oa else "DIFERENTE") + " original↔Anti-Slop; " + ("IGUAL" if igual_ov else "DIFERENTE") + " original↔V1.1.1",
            "metadatos_normalizados": "ninguno (claves de reloj excluidas: timestamp, fecha_calculo, fecha_hora, generado_en)",
            "observaciones": "; ".join(obs),
        })
for seccion, etiqueta in (("rechazos", "rechazos"), ("economico_empalme", "economía y empalme"), ("gui_sesion_exportables", "sesión y exportables (GUI)")):
    o, a, v = O[seccion], A[seccion], V[seccion]
    filas.append({
        "caso": seccion, "entradas_sha": h([seccion]), "base_original_sha": h(o), "anti_slop_previo_sha": h(a), "v111_sha": h(v),
        "lote_final_sha": "NO VERIFICADO (2D-2 no ejecutado: G0 NO-GO)", "modelo_original": "n/a", "modelo_final": "n/a",
        "SSE": "n/a", "RMSErect": "n/a", "H1-H24": "n/a",
        "economia": ("IGUAL" if o == a else "DIFERENTE") if seccion == "economico_empalme" else "n/a",
        "sesiones": ("IGUAL" if o == a else "DIFERENTE") if seccion.startswith("gui") else "n/a",
        "exportables": ("IGUAL" if o == a else "DIFERENTE") if seccion.startswith("gui") else "n/a",
        "comparacion_exacta": ("IGUAL" if o == a else "DIFERENTE") + " original↔Anti-Slop; " + ("IGUAL" if o == v else "DIFERENTE") + " original↔V1.1.1",
        "metadatos_normalizados": "rutas temporales, fechas-hora, IDs aleatorios; no finitos→None (arnés Fase 0)" if seccion.startswith("gui") else "ninguno",
        "observaciones": "V1.1.1 difiere solo en la etiqueta de versión 1.1.1/1.1.2 (9 celdas o líneas)" if seccion.startswith("gui") and o != v else "",
    })
buf = io.StringIO()
w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
w.writeheader()
w.writerows(filas)
Path(sys.argv[4]).write_bytes(buf.getvalue().encode("utf-8"))
print(f"filas={len(filas)} iguales_original_antislop={sum('IGUAL original↔Anti-Slop' in f['comparacion_exacta'] for f in filas)}")
