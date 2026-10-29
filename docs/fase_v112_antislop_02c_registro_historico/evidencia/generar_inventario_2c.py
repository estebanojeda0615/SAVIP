"""Fase 2C: genera 01_INVENTARIO_DEFINICIONES_AS003.csv (31 definiciones heredadas en 2f70391).

Uso: python generar_inventario_2c.py <raiz_repo> <grafo.json> <pruebas_dependientes.json> <espia.jsonl> <salida.csv>

Recuento: definiciones de nivel superior de servicio_proyeccion.py y modelos_interpretables.py NO alcanzables desde
producción según grafo_as003.py (Fase 2A). `lineas` = end_lineno − lineno + 1 del AST (sin separadores ni imports).
validacion_series.validar_serie/detectar_outliers_extremos no entran: son contrato S de pruebas/prueba_estadistica.py
(Fase 2A) y se conservan.
"""
import ast
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

raiz, grafo, dep, espia, salida = Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
SHA = "2f70391e1b920764e79fa50ec2c2da6b6b572e53"
g = json.load(open(grafo, encoding="utf-8"))
d = json.load(open(dep, encoding="utf-8"))
ejecutada = defaultdict(set)
for linea in open(espia, encoding="utf-8"):
    x = json.loads(linea)
    ejecutada[x["simbolo"].split(":")[1]].add(x["prueba"].split("::")[0])
ess, hist = defaultdict(set), defaultdict(set)
for r in d["pruebas"]:
    for s in r["usos"]:
        for i in r["ids"]:
            (ess if r["esencial"] else hist)[s].add(i)
FICHAS = {"seleccionar_modelo_por_rmse_oos_global": "C-SEL-001", "_evaluar_horizontes_proyeccion": "C-ALC-001",
          "_mayor_horizonte_con": "C-ALC-002", "_seleccionar_horizonte_permitido": "C-ALC-003",
          "_aplicar_salvaguarda_benchmarks": "C-SAL-001", "peor_que_benchmark_naive": "C-BEN-002"}
SCRIPTS = {"seleccionar_modelo_por_rmse_oos_global": "pruebas/prueba_horizonte_dinamico_ui_reportes.py",
           "determinar_horizonte_maximo_estadistico": "pruebas/prueba_horizonte_dinamico_ui_reportes.py"}
# simbolo: (familia, qué hace realmente, recomendación 2D, lote, bloqueo / evidencia que falta)
R_SEL = "RETIRABLE TRAS MIGRAR"
CEX = "CONSUMIDOR EXTERNO POR RESOLVER"
NP = "REQUERIRÍA NUEVA PRUEBA"
META = {
    "seleccionar_modelo_por_evidencia": ("M", "Selector retirado (P0-A, 09-08-2026): puntuación con once coeficientes sin fuente sobre backtesting, parsimonia, residuos e interpretabilidad. Sin llamadas.", R_SEL, "2D-4", "Solo lo exige test_el_selector_retirado_conserva_su_definicion_para_auditoria (existencia)."),
    "_benchmark_dominante": ("M", "Auxiliar del selector retirado: prioriza drift/naive si dominan fuera de muestra.", R_SEL, "2D-4", "Exclusiva de seleccionar_modelo_por_evidencia."),
    "comparar_modelo_con_benchmarks": ("M", "Auxiliar: compara un candidato con naive y drift en backtesting.", R_SEL, "2D-4", "Exclusiva del selector retirado."),
    "resumir_ranking_backtesting": ("M", "Auxiliar: ganadores por métrica fuera de muestra.", R_SEL, "2D-4", "Exclusiva del selector retirado."),
    "_mejor_candidato_no_elegible": ("M", "Auxiliar: candidato no benchmark de menor RMSE, para diagnóstico.", R_SEL, "2D-4", "Exclusiva del selector retirado."),
    "_razones_descartes": ("M", "Auxiliar: texto de descartes del selector retirado.", R_SEL, "2D-4", "Exclusiva del selector retirado."),
    "_ratio": ("M", "Auxiliar numérico (cociente seguro) de comparar_modelo_con_benchmarks.", R_SEL, "2D-4", "Nombre genérico: comprobar homónimos al retirar."),
    "_mejor_por": ("M", "Auxiliar: mejor fila por campo para resumir_ranking_backtesting.", R_SEL, "2D-4", "Nombre genérico."),
    "_numero": ("M", "Auxiliar: conversión a float con valor por defecto, solo del selector retirado.", R_SEL, "2D-4", "Nombre genérico: tests/test_fase_4i_p2 usa otro `_numero` (reportes.sesion_modulos)."),
    "_fmt": ("M", "Auxiliar de formato del selector retirado.", R_SEL, "2D-4", "Nombre genérico."),
    "tramo_evidencia_oos": ("T", "Clasifica W en tres tramos (sin evidencia / muy limitada / disponible) con umbral MIN_ITERACIONES_WF_ESCENARIO=3. La ruta vigente no lo llama; usa _texto_evidencia_oos y la advertencia de analisis_series (umbral 6).", R_SEL, "2D-5", "PS03 esencial; nuevas pruebas incorporadas. r3 (script no recolectado) la importa: decidir con AS-007."),
    "_backtesting_por_modelo_horizonte": ("E", "Extrae el backtesting de un modelo para un horizonte del comparativo.", R_SEL, "2D-3", "Usada por _evaluar_horizontes_proyeccion y _puntaje_rmse_ponderado."),
    "_tipo_uso_horizonte": ("E", "Etiqueta comunicacional del horizonte (corto/medio/largo) sin límite rígido.", R_SEL, "2D-3", "Compartida por el clasificador y por determinar_horizonte_maximo_estadistico: retirar con el último de los dos."),
    "_estado_por_horizonte": ("E", "Etiqueta del horizonte; desde el CIERRE 08-08-2026 ya no depende de cortes de amplitud.", NP, "2D-3", "Exclusiva del clasificador."),
    "peor_que_benchmark_naive": ("E", "Lectura descriptiva rRMSE frente a naive > 1 (C-BEN-002). No decide.", R_SEL, "2D-3", "Ficha C-BEN-002 (AS-024). La llama _comparacion_desde_backtesting."),
    "_comparacion_desde_backtesting": ("E", "Construye la comparación con benchmarks desde el backtesting.", R_SEL, "2D-3", "Exclusiva de _evaluar_horizontes_proyeccion."),
    "_evaluar_horizontes_proyeccion": ("E", "Evaluador por horizonte retirado: clasifica cada h con el clasificador y fija modelo y trayectoria comunes (P0-H: continue, no break).", NP, "2D-3", "Ficha C-ALC-001; espía de la Fase 1A; inspect en 2 esenciales. Llamada por la salvaguarda."),
    "_clasificar_evidencia_horizonte": ("E", "Clasificador heredado: decide permitido/no recomendable por horizonte; contiene la única expresión de «un punto no finito bloquea» (P0-G).", NP, "2D-3", "DECISIÓN PENDIENTE: la ruta vigente no aplica la regla del punto no finito ni redacta «MAPE no calculable»."),
    "_errores_oos_por_par": ("S", "Errores OOS por (objetivo, horizonte) desde el backtesting comparativo, para el selector global.", CEX, "2D-2", "Exclusiva del selector global; 1 esencial (nmin) y 3 históricas."),
    "seleccionar_modelo_por_rmse_oos_global": ("S", "Selector global retirado (C-SEL-001): mínimo RMSE OOS sobre la muestra común con SSE exacto. Sustituido por _seleccionar_modelo_rectangular (W*×24).", CEX, "2D-2", "Script pruebas/prueba_horizonte_dinamico_ui_reportes.py (AS-028); ficha C-SEL-001; 2 esenciales."),
    "_puntaje_rmse_ponderado": ("B", "RMSE relativo al mejor de cada h con peso 1/h, para ordenar benchmarks de respaldo de la salvaguarda.", R_SEL, "2D-3", "Exclusiva de la salvaguarda."),
    "_aplicar_salvaguarda_benchmarks": ("B", "Salvaguarda diagnóstica: reevalúa Drift/Naive si el modelo deja un horizonte no recomendable; nunca sustituye. Sin llamadas.", R_SEL, "2D-3", "Ficha C-SAL-001; 1 esencial (remediacion h2) cubierto por PS01."),
    "_seleccionar_horizonte_permitido": ("H", "Selecciona la evaluación del horizonte solicitado (C-ALC-003). Sin llamadas ni pruebas.", R_SEL, "2D-3", "Solo la ficha C-ALC-003."),
    "determinar_horizonte_maximo_estadistico": ("H", "Consolida horizonte máximo recomendado/escenario/admisible desde evaluaciones por horizonte. La ruta vigente no lo calcula (alcance fijo 24).", CEX, "2D-1", "Script pruebas/prueba_horizonte_dinamico_ui_reportes.py (AS-028); 8 esenciales; generador_reportes lee sus claves (AS-004)."),
    "_serializar_evaluaciones_horizonte": ("H", "Serializa las evaluaciones por horizonte para el resumen del máximo.", CEX, "2D-1", "Exclusiva de determinar_horizonte_maximo_estadistico."),
    "_item_horizonte_global": ("H", "Uso global del horizonte solicitado/permitido.", CEX, "2D-1", "Exclusiva de determinar_horizonte_maximo_estadistico."),
    "_mayor_horizonte_con": ("H", "Mayor h que cumple una clave con su propia evidencia (P0-H retiró el prefijo).", CEX, "2D-1", "Ficha C-ALC-002; exclusiva de determinar_…."),
    "_mayor_horizonte_permitido": ("H", "Mayor h con evidencia propia suficiente (P0-H).", CEX, "2D-1/2D-3", "Compartida por determinar_… y la salvaguarda: retirar con el último de los dos."),
    "_ultimo_horizonte_por_clasificacion": ("H", "Mayor h cuya clasificación está en un conjunto (P0-H, 17-08-2026).", CEX, "2D-1", "Exclusiva de determinar_…."),
    "_evidencia_horizonte": ("H", "Evidencia de un horizonte concreto para el resumen.", CEX, "2D-1", "Exclusiva de determinar_…."),
    "_mensaje_horizonte_no_permitido": ("E", "Redacta el bloqueo por horizonte del clasificador.", NP, "2D-3", "Exclusiva del clasificador."),
}
FAMILIAS = {"M": "selector por evidencia (modelos_interpretables)", "T": "tramos de evidencia OOS",
            "E": "evaluación y clasificación por horizonte", "S": "selección RMSE global",
            "B": "salvaguarda de benchmarks", "H": "decisión de horizonte máximo"}

filas = []
claves = [k for k, v in g.items() if v["archivo"].endswith(("servicio_proyeccion.py", "modelos_interpretables.py"))
          and not v["produccion"]]
fuentes = {}
for k in sorted(claves, key=lambda k: (g[k]["archivo"], g[k]["ini"])):
    v = g[k]
    nombre = k.split(":")[1]
    fuente = fuentes.setdefault(v["archivo"], (raiz / v["archivo"]).read_text(encoding="utf-8-sig"))
    nodo = next(n for n in ast.parse(fuente).body if getattr(n, "name", None) == nombre)
    fam, que, rec, lote, bloqueo = META[nombre]
    filas.append({
        "modulo": v["archivo"], "simbolo": nombre, "firma": f"{nombre}({ast.unparse(nodo.args)})",
        "linea_inicio": v["ini"], "linea_fin": v["fin"], "lineas": v["lineas"],
        "familia": FAMILIAS[fam], "que_hace": que,
        "alcanzable_produccion": "NO",
        "evidencia_no_uso": "grafo AST conservador (sin arista desde producción ni desde aplicacion.py); "
                            + ("espía 2C: solo la ejecutan pruebas que la llaman por su nombre ("
                               + ", ".join(sorted(ejecutada[nombre])) + ")" if ejecutada.get(nombre)
                               else "espía 2C: ninguna prueba esencial la ejecuta"),
        "llamadores_heredados": ", ".join(r.split(":")[1] for r in v["referenciado_por"]) or "ninguno",
        "scripts": SCRIPTS.get(nombre, "ninguno"),
        "pruebas_esenciales": len(ess.get(nombre, ())), "pruebas_historicas": len(hist.get(nombre, ())),
        "ficha_criterios": FICHAS.get(nombre, "ninguna"),
        "recomendacion_2D": rec, "lote_2D": lote, "bloqueo_o_evidencia_faltante": bloqueo,
        "referencia_permanente": f"https://github.com/estebanojeda0615/SAVIP/blob/{SHA}/{v['archivo']}#L{v['ini']}-L{v['fin']}",
    })
with open(salida, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(filas[0]), delimiter=";")
    w.writeheader()
    w.writerows(filas)
from collections import Counter
print(len(filas), "definiciones;", sum(f["lineas"] for f in filas), "líneas;", dict(Counter(f["recomendacion_2D"] for f in filas)))
