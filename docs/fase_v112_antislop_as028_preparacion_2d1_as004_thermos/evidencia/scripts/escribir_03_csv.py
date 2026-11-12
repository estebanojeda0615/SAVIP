"""Escribe 03_AS004_PRODUCTORES_CLAVES_CONSUMIDORES.csv y su lista de descartes a partir de:
- apariciones.csv (mapa_claves_as004.py, estático, con la columna `receptor` obtenida por AST) y
- sonda_claves.json (sonda_claves_as004.py, dinámico: 7 series × h ∈ {1,12,18,24} + sesión heredada).

Filtro REPRODUCIBLE: una lectura cuenta como consumidora de `horizonte_info` solo si su receptor (AST) es uno de
RECEPTORES_HI, todos verificados como alias de `horizonte_info` / `analisis_horizontes_completo` en 102f194. El resto
de lecturas de claves homónimas va a la lista de descartes con su receptor, para que pueda auditarse.

Las líneas citadas se calculan por AST; se comprueba además que la raíz es 102f194 (posición de la función).
Uso: python escribir_03_csv.py <raiz_102f194> <apariciones.csv> <sonda.json> <salida.csv> <descartes.csv>
"""
import ast
import csv
import json
import sys
from pathlib import Path

raiz, f_ap, f_sonda, salida, f_desc = sys.argv[1:]
SP = Path(raiz) / "app_icociv/proyeccion/servicio_proyeccion.py"
arbol = ast.parse(SP.read_text(encoding="utf-8-sig"))
defs = {n.name: n for n in arbol.body if isinstance(n, ast.FunctionDef)}
DET = defs["determinar_horizonte_maximo_estadistico"]
assert (DET.lineno, DET.end_lineno) == (3274, 3531), "la raíz no es 102f194: las líneas citadas no valdrían"
RSP = defs["_resultado_sin_proyeccion"]
plantilla = next(n for n in ast.walk(RSP) if isinstance(n, ast.Dict)
                 and any(isinstance(k, ast.Constant) and k.value == "horizonte_maximo_recomendado" for k in n.keys))
PLANTILLA = {k.value for k in plantilla.keys if isinstance(k, ast.Constant)}
TXT_PLANTILLA = f"plantilla por defecto de _resultado_sin_proyeccion (L{plantilla.lineno}-{plantilla.end_lineno}), solo si horizonte_info llega vacío"
TXT_DET = f"determinar_horizonte_maximo_estadistico (servicio_proyeccion.py L{DET.lineno}-{DET.end_lineno}; no se invoca)"

ap = list(csv.DictReader(open(f_ap, encoding="utf-8")))
sonda = json.load(open(f_sonda, encoding="utf-8"))
esc = sonda["escenarios"]
CLAVES = sonda["claves_determinar"]
SUBSISTEMA = {"determinar_horizonte_maximo_estadistico", "_serializar_evaluaciones_horizonte", "_item_horizonte_global",
              "_mayor_horizonte_con", "_ultimo_horizonte_por_clasificacion", "_evidencia_horizonte"}
RECEPTORES_HI = {"info", "horizonte_info", "horizonte_info or {}", "analisis",
                 "resultado.get('horizonte_info') or {}", "resultado_proyeccion.get('horizonte_info') or {}",
                 "proyeccion.get('horizonte_info') or {}", "proyeccion.get('analisis_horizontes_completo') or {}"}
SUBCLAVE_TRAZA = "info.get('trazabilidad') or {}"  # subclave de trazabilidad, no clave de horizonte_info
VIGENTE = {"horizonte_solicitado", "horizonte_finalmente_permitido", "razones", "mensaje", "evaluaciones", "trazabilidad"}
EXPOSICION = {
    "construir_dataframe_reproducibilidad": "CSV reproducible exportado (columna)",
    "_estructurar_resultado_horizontes": "interna: resultado_horizonte_solicitado y filas «No evaluado»",
    "_categorizar_advertencias": "advertencias_categorizadas (UI e informes)",
    "_encabezado": "UI: texto del encabezado (3.ª opción)",
    "_resultado_solicitado": "UI: respaldo si falta resultado_horizonte_solicitado",
    "_backtesting_relevante": "UI: respaldo si falta backtesting.metricas",
    "construir_html_explicacion_tarjeta": "UI: tarjetas de explicación",
    "_tabla_horizonte_estadistico": "UI: tabla de horizonte",
    "_analisis_horizontes": "UI: tabla_horizontes de respaldo",
    "_horizontes": "PDF/DOCX: auxiliar", "_seccion_horizonte": "PDF/DOCX: sección de horizonte",
    "grafica_errores_horizonte": "PDF/DOCX: gráfica de error por horizonte",
    "_analisis_horizontes_completo": "auxiliar del CSV y de _lineas_*",
}


def presencia(clave):
    nuevos = sorted({n.split("|")[0] for n, d in esc.items() if not n.startswith("sesion_heredada")
                     and clave in d.get("claves_historicas_presentes", {})})
    return ",".join(nuevos) if nuevos else "ausente en todos los resultados nuevos (7 series × h=1,12,18,24)"


def csv_nuevo(columna):
    if columna is None:
        return "-"
    vals = sorted({d["csv_columnas_historicas"].get(columna, "<no medida>") for n, d in esc.items()
                   if not n.startswith("sesion_heredada") and "csv_columnas_historicas" in d})
    return " | ".join(repr(v) for v in vals)


HEREDADAS = set(sonda.get("claves_heredadas_inyectadas", []))


def csv_heredado(columna, clave):
    if columna is None:
        return "-"
    if clave not in HEREDADAS:
        return "<no inyectada>"
    d = esc.get("sesion_heredada|h12", {})
    return repr(d.get("csv_columnas_historicas", {}).get(columna, "<no medida>"))


#: Claves que el esencial test_presentacion_resultados::test_exportable_diferencia_recomendado_evaluado_y_limite_operativo
#: exige leer en el CSV (aserciones sobre horizonte_maximo_recomendado, _evaluado, limite_operativo_auditoria y
#: razon_parada_horizontes).
ESENCIAL_CSV = {"horizonte_maximo_recomendado", "horizonte_maximo_evaluado", "horizonte_maximo_busqueda_configurado", "razon_parada"}


def _efecto_csv(nuevos, col, k):
    """Efecto calculado a partir de lo MEDIDO: «cambia con la plantilla» solo si algún resultado nuevo escribe un valor
    distinto del valor por defecto del .get (cadena vacía o False)."""
    con_valor = [v for v in nuevos.split(" | ") if v not in ("''", "'False'")]
    heredado = csv_heredado(col, k)
    return ("si se ELIMINA la columna: cambia la cabecera del CSV (Golden sesion_exportables / informe_proyeccion.csv). "
            "Si se conserva y solo se deja de leer (sustituyendo por el mismo valor por defecto del .get): "
            + (f"cambia con la plantilla ({', '.join(con_valor)} -> valor por defecto)" if con_valor
               else "igual con todos los resultados nuevos medidos")
            + ("; cambia con sesiones heredadas" if heredado not in ("<no inyectada>", "''") else
               "; con sesiones heredadas: no medido (clave no inyectada)" if heredado == "<no inyectada>" else ""))


COLUMNA_CSV = {"razon_parada": "razon_parada_horizontes", "horizonte_maximo_busqueda_configurado": "limite_operativo_auditoria"}
filas, descartes, lecturas = [], [], {}
for a in ap:
    if not (a["archivo"].startswith("app_icociv") and a["rol"].startswith("consumidor")):
        continue
    if a["definicion"] in SUBSISTEMA:
        motivo = "subsistema 2D-1"
    elif a["receptor"] == SUBCLAVE_TRAZA:
        motivo = "subclave de horizonte_info.trazabilidad (no clave de nivel superior)"
    elif a["receptor"] not in RECEPTORES_HI:
        motivo = "receptor distinto de horizonte_info"
    else:
        lecturas.setdefault(a["clave"], {})[(a["archivo"], a["linea"])] = a
        continue
    descartes.append([a["clave"], f"{a['archivo']}:{a['linea']}", a["definicion"], a["receptor"], motivo])
for k in CLAVES:
    actual = ("ruta vigente (clave genérica)" if k in VIGENTE else TXT_PLANTILLA if k in PLANTILLA
              else "ninguno (exclusiva de determinar_horizonte_maximo_estadistico)")
    regs = list(lecturas.get(k, {}).values())
    if k in VIGENTE:
        filas.append([k, TXT_DET, actual, presencia(k), f"{len(regs)} lecturas (ver apariciones_claves.csv)", "varios",
                      "produccion", "clave genérica también producida por la ruta vigente", "-", "-", "-",
                      "ninguno: su productor vigente no depende de 2D-1", "no aplica: no es una clave histórica"])
        continue
    if not regs:
        filas.append([k, TXT_DET, actual, presencia(k), "-", "-", "-", "ninguna", "-", "-", "-",
                      "ninguno: no hay lector", "ninguno: no hay lector"])
        continue
    for a in regs:
        es_csv = a["definicion"] == "construir_dataframe_reproducibilidad"
        col = COLUMNA_CSV.get(k, k) if es_csv else None
        prod = a["alcanzable_desde"]
        nuevos = csv_nuevo(col)
        if prod != "produccion":
            efecto_as004 = ("sin efecto productivo (definición no alcanzable)" if prod == "inalcanzable"
                            else f"sin efecto productivo (alcanzable solo desde {prod})")
        elif es_csv and k in ESENCIAL_CSV:
            efecto_as004 = ("ROMPE el esencial tests/test_presentacion_resultados.py::test_exportable_diferencia_recomendado_"
                            "evaluado_y_limite_operativo (fija que el CSV lea esta clave de analisis_horizontes_completo), "
                            "tanto si se elimina la columna como si solo se deja de leer. Además: ")
            efecto_as004 += _efecto_csv(nuevos, col, k)
        elif es_csv:
            efecto_as004 = _efecto_csv(nuevos, col, k)
        elif a["definicion"] == "_encabezado":
            efecto_as004 = "igual con resultados nuevos (no se alcanza); cambia con sesiones heredadas sin razon_principal ni explicacion (medido)"
        elif a["definicion"] in ("_estructurar_resultado_horizontes", "_categorizar_advertencias"):
            efecto_as004 = ("ninguno: solo se ejecuta dentro de ejecutar_proyeccion (no lee sesiones restauradas) y el 0/[] de la "
                            "plantilla equivale al `or 0` / `or []` del lector")
        else:
            efecto_as004 = "a evaluar en la fase AS-004"
        filas.append([k, TXT_DET, actual, presencia(k), f"{a['archivo']}:{a['linea']}", a["definicion"], prod,
                      EXPOSICION.get(a["definicion"], "ver definición"), col or "-", nuevos, csv_heredado(col, k),
                      "ninguno: la lectura no depende de que exista determinar_* (0 llamadas; misma salida con 2D-1 oculto, 06)",
                      efecto_as004])

cab = ["clave", "productor_historico", "productor_actual", "presencia_en_resultados_nuevos", "consumidor_ruta_linea",
       "consumidor_definicion", "consumidor_alcanzable_desde", "exposicion", "columna_csv",
       "valor_csv_resultados_nuevos", "valor_csv_sesion_heredada", "efecto_retiro_2d1", "efecto_retiro_lectura_as004"]
with open(salida, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, lineterminator="\n"); w.writerow(cab); w.writerows(filas)
with open(f_desc, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, lineterminator="\n"); w.writerow(["clave", "ruta_linea", "definicion", "receptor", "motivo"])
    w.writerows(sorted(descartes))
print(len(filas), "filas;", len(descartes), "lecturas descartadas")
