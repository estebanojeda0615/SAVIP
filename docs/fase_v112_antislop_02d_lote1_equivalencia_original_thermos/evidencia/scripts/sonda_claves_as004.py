"""AS-004 (diagnóstico dinámico, solo lectura): qué claves históricas de `horizonte_info` existen en
resultados reales de `ejecutar_proyeccion`, qué escribe el CSV reproducible en sus columnas, qué
mensaje usa el encabezado de la interfaz y si se invoca alguna función 2D-1 (espías pasivos: cuentan
y delegan, no alteran argumentos ni retornos).

Escenarios: 7 series × h ∈ {1, 12, 18, 24}, más una «sesión heredada» (dato antiguo inyectado, ver HEREDADO).
Uso: python sonda_claves_as004.py <raiz_repo> <salida.json>
"""
import ast
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

raiz = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(raiz))
import app_icociv.proyeccion.servicio_proyeccion as sp  # noqa: E402
from app_icociv.reportes import generador_reportes as gr  # noqa: E402
from app_icociv.interfaz import presentacion_resultados as pr  # noqa: E402

OBJ = ["determinar_horizonte_maximo_estadistico", "_serializar_evaluaciones_horizonte", "_item_horizonte_global",
       "_mayor_horizonte_con", "_ultimo_horizonte_por_clasificacion", "_evidencia_horizonte",
       "_tipo_uso_horizonte", "_mayor_horizonte_permitido"]
llamadas = {n: 0 for n in OBJ}


def espia(nombre, f):
    def envoltura(*a, **k):
        llamadas[nombre] += 1
        return f(*a, **k)
    return envoltura


# Lote 2D-1: tras el retiro, las seis definiciones ya no existen; se espían solo las presentes y se registran ausentes.
AUSENTES = [n for n in OBJ if not hasattr(sp, n)]
for n in OBJ:
    if n not in AUSENTES:
        setattr(sp, n, espia(n, getattr(sp, n)))

# Las claves se extraen de la fuente que aún contiene la función (SONDA_FUENTE_CLAVES, por defecto la propia raíz).
import os  # noqa: E402
FUENTE_CLAVES = Path(os.environ.get("SONDA_FUENTE_CLAVES", str(raiz))).resolve()
arbol = ast.parse((FUENTE_CLAVES / "app_icociv/proyeccion/servicio_proyeccion.py").read_text(encoding="utf-8-sig"))
fn = next(n for n in arbol.body if isinstance(n, ast.FunctionDef) and n.name == "determinar_horizonte_maximo_estadistico")
rets = [n for n in ast.walk(fn) if isinstance(n, ast.Return) and isinstance(n.value, ast.Dict)]
assert len(rets) == 1, "se esperaba un único return con dict literal"
ret = rets[0]
CLAVES = [k.value for k in ret.value.keys if isinstance(k, ast.Constant)]
COLS_CSV = ["accion_global", "razon_parada_horizontes", "horizonte_maximo_evaluado",
            "horizonte_maximo_permitido_como_escenario", "horizonte_maximo_admisible",
            "base_horizonte_maximo_recomendado", "base_horizonte_maximo_escenario",
            "advertencia_metodologica_horizontes", "horizonte_maximo_evaluable_por_datos",
            "limite_operativo_auditoria", "horizonte_solicitado_cubierto", "mensaje_no_recomendables",
            "horizontes_evaluados", "horizonte_maximo_recomendado", "horizonte_maximo_con_cautela",
            "horizonte_maximo_escenario", "primer_horizonte_no_viable"]


def periodos(n):
    return [f"{2021 + i // 12}_{i % 12 + 1}" for i in range(n)]


def serie(valores):
    return pd.DataFrame({"Periodo": periodos(len(valores)), "Indice": valores})


fx = raiz / "tests/fixtures/horizonte_dinamico"
estable = [100.0 + 0.25 * i + 0.02 * np.sin(i / 4.0) for i in range(120)]
ESCENARIOS = {
    "fixture_serie_drift": pd.read_csv(fx / "serie_drift.csv"),
    "fixture_serie_holt": pd.read_csv(fx / "serie_holt.csv"),
    "estable_120": serie(estable),
    "historia_insuficiente_20": serie(estable[:20]),
    "sin_valores_validos": serie([float("nan")] * 30),
    "valor_negativo": serie(estable[:59] + [-5.0]),
    "valor_cero": serie(estable[:59] + [0.0]),
}


HORIZONTES = (1, 12, 18, 24)

#: Sesión heredada: `horizonte_info` con claves del subsistema antiguo, como el que guardaría una versión que sí
#: ejecutara `determinar_*`. Se inyecta en un resultado vigente sin `resultado_horizonte_solicitado` ni `explicacion`
#: para observar las lecturas de respaldo (dato, no código: no llama a ninguna función 2D-1).
HEREDADO = {"horizonte_maximo_recomendado": 12, "horizonte_maximo_con_cautela": 9, "horizonte_maximo_escenario": 18,
            "horizonte_maximo_permitido_como_escenario": 18, "horizonte_maximo_admisible": 18,
            "horizonte_maximo_evaluado": 20, "primer_horizonte_no_viable": 19, "horizontes_evaluados": [1, 2, 3],
            "mensaje_no_recomendables": "HEREDADO-no-recomendables", "mensaje_ui": "HEREDADO-mensaje-ui",
            "razon_parada": "HEREDADO-parada", "base_horizonte_maximo_recomendado": "HEREDADO-base",
            "advertencia_metodologica_horizontes": "HEREDADO-advertencia", "horizonte_solicitado_cubierto": True,
            "base_horizonte_maximo_escenario": "HEREDADO-base-escenario", "horizonte_maximo_evaluable_por_datos": 21,
            "horizonte_maximo_busqueda_configurado": 22}


def anio_mes_objetivo(df, h=12):
    ultimo = str(df["Periodo"].iloc[-1]).replace("-", "_").split("_")
    t = int(ultimo[0]) * 12 + int(ultimo[1]) - 1 + h
    return t // 12, t % 12 + 1


salida = {"raiz": str(raiz), "definiciones_ausentes": AUSENTES, "claves_determinar": CLAVES, "claves_heredadas_inyectadas": sorted(HEREDADO), "escenarios": {}}
def casos():
    for nombre, df in ESCENARIOS.items():
        for h in HORIZONTES:
            yield f"{nombre}|h{h}", df, h
    yield "sesion_heredada|h12", ESCENARIOS["estable_120"], 12


for nombre, df, h in casos():
    for n in llamadas:
        llamadas[n] = 0
    anio, mes = anio_mes_objetivo(df, h)
    try:
        res = sp.ejecutar_proyeccion(df, anio, mes, 2021)
    except Exception as e:  # se registra; no se oculta
        salida["escenarios"][nombre] = {"excepcion": f"{type(e).__name__}: {e}"}
        continue
    if nombre.startswith("sesion_heredada"):
        res = dict(res)
        res["horizonte_info"] = {**HEREDADO}
        res["analisis_horizontes_completo"] = res["horizonte_info"]
        res.pop("resultado_horizonte_solicitado", None)
        res["explicacion"] = ""
    info = res.get("horizonte_info") or {}
    presentes = {k: info[k] for k in CLAVES if k in info}
    csv = gr.construir_dataframe_reproducibilidad(df, res)
    # Se OBSERVA el encabezado real (no se reimplementa su orden de respaldo): qué texto candidato aparece en el HTML.
    from html import escape
    html = pr._encabezado(res, bool(res.get("proyeccion_generada")))
    candidatos = {"resultado_horizonte_solicitado.razon_principal": pr._resultado_solicitado(res).get("razon_principal"),
                  "explicacion": res.get("explicacion"), "horizonte_info.mensaje_ui": info.get("mensaje_ui"),
                  "texto fijo": "Análisis ejecutado."}
    # `_encabezado` puede recortar el texto: se compara por prefijo (60 caracteres escapados).
    fuente = next((k for k, v in candidatos.items() if v and escape(str(v))[:60] in html), "ninguno de los candidatos")
    salida["escenarios"][nombre] = {
        "proyeccion_generada": bool(res.get("proyeccion_generada")),
        "llamadas_espias": dict(llamadas),
        "claves_historicas_presentes": {k: (v if isinstance(v, (int, float, str, bool)) or v is None else type(v).__name__ + f"[{len(v)}]") for k, v in presentes.items()},
        # Valores distintos de cada columna histórica en TODAS las filas del CSV (no solo la primera).
        "csv_columnas_historicas": {c: ("; ".join(sorted({str(v) for v in csv[c].tolist()})) if c in csv.columns
                                        else "<columna ausente>") for c in COLS_CSV},
        "encabezado_ui_fuente": fuente,
        "analisis_es_horizonte_info": res.get("analisis_horizontes_completo") is res.get("horizonte_info"),
    }
json.dump(salida, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
for n, d in salida["escenarios"].items():
    if "excepcion" in d:
        print(n, d["excepcion"]); continue
    print(n, "gen=", d["proyeccion_generada"], "llamadas=", sum(d["llamadas_espias"].values()), "n_claves_hist=", len(d["claves_historicas_presentes"]), "enc=", d["encabezado_ui_fuente"])
