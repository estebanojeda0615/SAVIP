"""Fase 2A (AS-003): genera 01_INVENTARIO_SIMBOLOS_AS003.csv a partir del grafo (c9166c6), el espía G2 y las
decisiones de la fase.

Uso: python generar_inventario.py <raiz_repo> <grafo_base.json> <espia_esenciales.jsonl> <salida.csv>
"""
import csv
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path

raiz, grafo, espia, salida = Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
g = json.load(open(grafo, encoding="utf-8"))
spec = importlib.util.spec_from_file_location("pf", raiz / "scripts" / "pruebas_fase0.py")
pf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pf)
esenciales = set(pf.ESENCIALES)
ejecutada = defaultdict(set)
for linea in open(espia, encoding="utf-8"):
    x = json.loads(linea)
    ejecutada[x["simbolo"]].add(x["prueba"].split("::")[0])

ALCANCE = ("servicio_proyeccion.py", "modelos_interpretables.py", "validacion_series.py")
ELIMINADAS = {"_metadatos_auditoria_horizontes": "d7429df", "_numero_parametros_modelo": "d7429df",
              "_metricas_desde_predicciones": "d7429df", "_explicacion_factibilidad": "d7429df",
              "_validar_ajuste_calendario_serie": "d7429df", "resumen_validacion": "c6ca863"}
OPCION_B = {"_rmse_global_estable", "_modelo_consistente_desde_comparativo", "_modelo_trayectoria_consistente"}
SP = "app_icociv.proyeccion.servicio_proyeccion:"
VIGENTES = {
    SP + "ejecutar_analisis": ("MANTENER", "S",
        "API documentada (docstring con ejemplo) e importada por pruebas/ejemplo_uso.py. Solo llama a la ruta vigente "
        "(cargar_todas_tablas, resolver_fila_seleccionada, construir_serie, ejecutar_proyeccion): no obliga a conservar "
        "ningún código heredado. La GUI usa otro método homónimo (ControladorPrincipal.ejecutar_analisis)."),
    SP + "ejecutar_proyeccion": ("MANTENER", "P", "Ruta productiva vigente (prohibido tocar)."),
    SP + "_ejecutar_proyeccion_base": ("MANTENER", "P", "Ruta productiva vigente (prohibido tocar)."),
    SP + "_matriz_rectangular_12_24": ("MANTENER", "P", "Ruta productiva vigente: matriz W*×24 (prohibido tocar)."),
    SP + "_seleccionar_modelo_rectangular": ("MANTENER", "P", "Selector vigente RMSErect por SSE exacto (prohibido tocar)."),
    SP + "_sse_exacto": ("MANTENER", "P", "Obligatoria: puntuación exacta del orden (prohibido tocar)."),
    SP + "_rmse_desde_sse": ("MANTENER", "P", "Obligatoria: corrección AS-001 de la Fase 1B (prohibido tocar)."),
    "app_icociv.estadistica.calendario_anual:evaluar_ajuste_en_backtesting": ("FUERA DE ALCANCE", "T",
        "Su único llamador era _validar_ajuste_calendario_serie (retirada en el Lote 1); ya era inalcanzable desde "
        "producción en c9166c6. Está en calendario_anual.py, fuera de los tres módulos de AS-003: se registra, no se toca."),
}


def categoria(v):
    c = []
    if v["produccion"]:
        c.append("P")
    if v["scripts_directos"] or (v["scripts"] and not v["produccion"]):
        c.append("S")
    if v["citas_documentales"]:
        c.append("D")
    if v["tests"]:
        c.append("T")
    return "+".join(c) or "sin consumidores"


filas = []
claves = [k for k, v in g.items() if v["archivo"].endswith(ALCANCE) and not v["produccion"]] + list(VIGENTES)
for k in sorted(set(claves), key=lambda k: (g[k]["archivo"], g[k]["ini"])):
    v = g[k]
    nombre = k.split(":")[1]
    tests_ess = sorted(t for t in v["tests_directos"] if t in esenciales)
    tests_hist = sorted(t for t in v["tests_directos"] if t not in esenciales)
    consumidores = "; ".join(
        [f"llamada por {r.split(':')[1]}" for r in v["referenciado_por"]]
        + [f"script {s}" for s in v["scripts_directos"]]
        + [f"ficha documental en {d.split('.')[-1]}.py" for d in v["citas_documentales"]]
        + [f"prueba esencial {t}" for t in tests_ess] + [f"prueba o fixture no esencial {t}" for t in tests_hist]) or "ninguno"
    if k == SP + "ejecutar_analisis":  # el grafo funde el homónimo ControladorPrincipal.ejecutar_analisis
        consumidores = ("script pruebas/ejemplo_uso.py (único importador de la función del servicio, verificado con grep). "
                        "No son esta función: ControladorPrincipal.ejecutar_analisis, usado por VentanaPrincipal, "
                        "pruebas/prueba_estadistica.py, pruebas/prueba_sesiones_reportes.py y las pruebas de la GUI")
    if k in VIGENTES:
        decision, cat, motivo = VIGENTES[k]
        g_ = ("SI",) * 6 if decision == "MANTENER" else ("SI", "SI", "NA", "NA", "NA", "NA")
        prueba = "Ruta productiva cubierta por los 29 Golden Masters y la integración de 21 candidatos" if cat == "P" else \
            ("pruebas/ejemplo_uso.py ejecutado con anexo sintético antes y después: misma salida" if nombre == "ejecutar_analisis"
             else "grafo AST")
    else:
        cat = categoria(v)
        ej = sorted(ejecutada.get(k, ()))
        prueba = ("espía G2 en el perfil esencial: no la ejecuta ninguna prueba" if not ej
                  else "espía G2: solo la ejecutan pruebas unitarias que la llaman por su nombre: " + ", ".join(ej))
        if nombre in ELIMINADAS:
            decision, g_ = "ELIMINAR", ("SI",) * 6
            motivo = (f"Commit {ELIMINADAS[nombre]}. Sin ninguna referencia en el repositorio (código, scripts, pruebas, "
                      "docs, packaging) ni acceso dinámico. Huella exacta idéntica, 29 golden y 797 esenciales en PASS.")
        elif nombre in ("validar_serie", "detectar_outliers_extremos"):
            decision, g_ = "MANTENER", ("SI", "SI", "NO", "NA", "NA", "NA")
            motivo = "Contrato S: pruebas/prueba_estadistica.py usa validar_serie (y esta a detectar_outliers_extremos)."
        elif nombre in OPCION_B:
            decision, g_ = "DEFERIR POR RIESGO", ("SI", "SI", "NO", "NA", "NO", "NA")
            motivo = ("Solo la ancla la prueba esencial de la Fase 1A que espía los nombres retirados. Retirable si se "
                      "autoriza adaptar esa prueba (opción B, pendiente de decisión), con trato G5 individual de las "
                      "pruebas históricas que la ejercen.")
        else:
            decision, g_ = "DEFERIR POR RIESGO", ("SI", "SI", "NO", "NA", "NO", "NA")
            anclas = ([f"prueba esencial {t}" for t in tests_ess] + [f"script {s}" for s in v["scripts_directos"]]
                      + [f"ficha de {d.split('.')[-1]}.py" for d in v["citas_documentales"]])
            motivo = ("Anclada por " + "; ".join(anclas) + "." if anclas else
                      "La llaman otras definiciones conservadas: " + ", ".join(r.split(":")[1] for r in v["referenciado_por"]) + ".")
            motivo += " Retirarla exige retirar casos esenciales o decidir sobre el registro de auditoría, pruebas/ (AS-028) y criterios.py (AS-024)."
    filas.append({"modulo": v["archivo"], "simbolo": nombre, "linea_inicio": v["ini"], "linea_fin": v["fin"],
                  "lineas": v["lineas"], "alcanzable_produccion": "SI" if v["produccion"] else "NO", "categoria": cat,
                  "consumidores": consumidores, "prueba_de_no_uso": prueba, "decision": decision,
                  "G1": g_[0], "G2": g_[1], "G3": g_[2], "G4": g_[3], "G5": g_[4], "G6": g_[5], "motivo": motivo})

with open(salida, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(filas[0]), delimiter=";")
    w.writeheader()
    w.writerows(filas)
from collections import Counter
print(len(filas), "filas;", dict(Counter(r["decision"] for r in filas)))
print("líneas por decisión:", {d: sum(r["lineas"] for r in filas if r["decision"] == d) for d in set(r["decision"] for r in filas)})
