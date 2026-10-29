"""Fase 2C: genera 03_MATRIZ_MIGRACION_PRUEBAS.csv.

Uso: python generar_matriz_pruebas.py <pruebas_dependientes.json> <carpeta_junit_esenciales> <carpeta_junit_historicas> <salida.csv>

Las filas salen de pruebas_dependientes.py (todas las funciones de prueba que nombran una definición heredada). El
estado ANTES se lee de los JUnit de la línea base (2f70391). Las decisiones y equivalencias están escritas a mano,
caso por caso, en las tablas de este archivo: cada fila debe tener destino o el script falla.
"""
import csv
import glob
import json
import sys
import xml.etree.ElementTree as ET

dep = json.load(open(sys.argv[1], encoding="utf-8"))
NUEVA = "tests/test_fase2c_contratos_vigentes.py::"
P1A = "tests/test_fase1a_selector_rectangular.py::"
MET = "tests/test_metodologia_n0_12_h24.py::"
PS = "tests/test_cierre_semantico_ps01_ps05.py::"


def estados(carpeta):
    d = {}
    for p in glob.glob(f"{carpeta}/*.xml"):
        if "__reintento" in p:
            continue
        for tc in ET.parse(p).getroot().iter("testcase"):
            e = ("FAIL" if tc.find("failure") is not None else "ERROR" if tc.find("error") is not None
                 else "SKIP" if tc.find("skipped") is not None else "PASS")
            d[tc.get("name")] = e
    return d


ESTADO = {**estados(sys.argv[3]), **estados(sys.argv[2])}

# (contrato, equivalente vigente, prueba vigente, estado_migracion, decision_2D, lote, reemplazo, consecuencia, riesgo)
SELECTOR_CUBIERTO = ("La regla de selección por RMSE OOS sobre la muestra común (orden exacto, desempate, pesos "
                     "uniformes, no finitos) en el selector heredado.",
                     "_seleccionar_modelo_rectangular (RMSErect por SSE exacto sobre W*×24)",
                     P1A + "test_selector_vigente_cumple[*] (7 propiedades), test_cada_mutante_es_detectado[*] (5), "
                     "test_as001_* (16); " + MET + "test_d_seleccion_usa_muestra_comun_y_rmse_global_del_rectangulo",
                     "CUBIERTO YA", "Retirar por obsolescencia documentada", "2D-2",
                     "Ninguna: las propiedades ya están sobre el selector vigente (Fase 1A)",
                     "−1 id histórico; sin pérdida de contrato vigente",
                     "Bajo: las mismas propiedades protegen el selector que decide; los mutantes lo demuestran")
CLASIF_HISTORICA = ("Comportamiento del clasificador heredado por horizonte (permitido/no recomendable, mensajes).",
                    "Ninguno: la ruta vigente no clasifica horizontes; entrega la trayectoria de 24 meses",
                    "—", "SIN EQUIVALENTE / NO APLICA", "Pasar a histórico (retirar con el lote)", "2D-3",
                    "Ninguna; la regla queda documentada en 02 y en Git (2f70391)",
                    "−1 id; la regla describía una decisión que ya no existe",
                    "Bajo: describe código no alcanzable desde producción (grafo + espía)")
HORIZONTE_HISTORICO = ("Cálculo del horizonte máximo dinámico (recomendado/escenario/admisible) del evaluador heredado.",
                       "Ninguno: alcance fijo H_OPERATIVO_MAX = 24 y trayectoria única",
                       MET + "test_b_h_operativo_max_es_24, test_efg_horizonte_solicitado_no_cambia_modelo_ni_trayectoria;"
                       " golden del motor (h11/h23)",
                       "SIN EQUIVALENTE / NO APLICA", "Retirar por obsolescencia documentada", "2D-1",
                       "Ninguna: la función describe un mecanismo retirado",
                       "−1 id esencial (requiere autorización expresa de retirar casos esenciales)",
                       "Medio documental: generador_reportes.py aún lee horizonte_maximo_recomendado (AS-004)")
SCRIPT = ("Comprobación de estilo script (no la recoge pytest) sobre funciones heredadas.",
          "—", "—", "DECISIÓN PENDIENTE", "Pasar a histórico con AS-007 (no se ejecuta en ningún perfil)",
          "2D-0", "Decidir con AS-007: retirar el archivo o reescribirlo como prueba recolectable",
          "0 ids recolectados hoy; no cambia el recuento",
          "Bajo para la app; hoy ya no se ejecuta (error de importación o sin funciones test_)")

POR_PRUEBA = {
    # ---------------------------------------------------------------- ESENCIALES (27)
    "test_ps03_la_escasez_de_evidencia_no_equivale_a_su_inexistencia": (
        "W=0 sin evidencia; W∈{1,2} muy limitada; W≥3 disponible; ningún tramo se llama validado (tramo_evidencia_oos).",
        "_texto_evidencia_oos (mismos tramos y umbral) y advertencia de escasez de analisis_series (umbral MIN_ITERACIONES_WF=6)",
        NUEVA + "test_texto_evidencia_oos_tres_tramos_sin_vocabulario_de_validacion; " + NUEVA +
        "test_escasez_de_ventanas_entrega_el_punto_con_advertencia_y_sin_intervalo[36|37|41]",
        "PRUEBA NUEVA INCORPORADA", "Retirar por obsolescencia documentada", "2D-5",
        "Las 4 pruebas nuevas citadas", "−1 id esencial, +4 ids esenciales nuevos",
        "Bajo; discrepancia de umbral (3 frente a 6) documentada en 02 §5, no se homologa"),
    "test_la_ruta_productiva_usa_el_selector_rectangular_y_ningun_selector_retirado": (
        "La ruta productiva llama una vez a la matriz y al selector rectangular y nunca a los heredados; 21 candidatos, h=1..24, W*×24.",
        "La misma ruta", "El propio caso + " + NUEVA + "test_la_ruta_vigente_no_referencia_el_subsistema_heredado",
        "CUBIERTO YA", "Mantener (adaptar en cada lote: el nombre retirado pasa de espía a ausencia exigida, como en 2B)",
        "2D-1/2D-2/2D-3", "—", "Mismo id", "Bajo: patrón ya aplicado en 2B con sensibilidad comprobada"),
    "test_mape_no_finito_no_bloquea_el_horizonte": (
        "Métricas porcentuales no finitas no bloquean el horizonte (clasificador heredado).",
        "La ruta vigente no consulta métricas para generar ni para seleccionar (solo SSE exacto)",
        P1A + "test_selector_vigente_cumple[*]; " + MET + "test_j_no_existe_tolerancia_smape_productiva",
        "REQUIERE CREAR", "Migrar", "2D-3",
        "Prueba de ruta vigente con una serie cuyo MAPE no sea finito y proyeccion_generada=True; requiere decidir "
        "si una serie con observaciones 0 es válida (hoy la validación puede rechazarla)",
        "−1 id, +1 id", "Medio: PS02 (que lo cubriría) se omite sin el anexo DANE en clon limpio (AS-007)"),
    "test_mape_no_calculable_se_publica_como_advertencia": (
        "El clasificador heredado publica «MAPE/sMAPE no calculable» como advertencia.",
        "Ninguno: la ruta vigente no redacta esa advertencia (el texto solo existe en _clasificar_evidencia_horizonte)",
        "—", "DECISIÓN PENDIENTE", "Decidir si la advertencia debe existir en la ruta vigente antes de retirar",
        "2D-3", "Si se decide conservar la comunicación: nueva prueba sobre la ruta vigente; si no: retirar",
        "−1 id", "Medio: pérdida de un aviso que hoy tampoco se publica"),
    "test_sin_ventanas_suficientes_el_punto_sigue_pero_el_intervalo_no": (
        "Con 2 ventanas el horizonte se permite, se dice «muy limitada (n=2)» y no se menciona el intervalo.",
        "Escasez de ventanas en la ruta vigente: punto entregado, advertencia con el número, intervalo no publicado",
        NUEVA + "test_escasez_de_ventanas_entrega_el_punto_con_advertencia_y_sin_intervalo[36|37|41]",
        "PRUEBA NUEVA INCORPORADA", "Retirar por obsolescencia documentada", "2D-3",
        "La prueba nueva citada", "−1 id, cubierto por +3", "Bajo; el texto vigente es otro (analisis_series)"),
    "test_banda_no_valida_se_declara_sin_bloquear_el_punto": (
        "Una banda no válida no bloquea el punto y su vocabulario no se publica.",
        "Rama de _ejecutar_proyeccion_base que captura el fallo de _intervalos_prediccion",
        NUEVA + "test_banda_no_construible_no_cancela_el_punto",
        "PRUEBA NUEVA INCORPORADA", "Retirar por obsolescencia documentada", "2D-3",
        "La prueba nueva citada", "−1 id, +1 id", "Bajo"),
    "test_lo_que_bloquea_son_imposibilidades_del_resultado_no_carencias_de_evidencia": (
        "Solo PUNTO_NO_FINITO bloquea; los demás estados de banda y la escasez no.",
        "Parcial: la ruta vigente no bloquea por banda ni por escasez; NO aplica ninguna regla para un punto no finito",
        NUEVA + "test_banda_no_construible_no_cancela_el_punto; " + NUEVA + "test_escasez_*",
        "DECISIÓN PENDIENTE", "No retirar hasta decidir la regla del punto no finito en la ruta vigente", "2D-3",
        "Si se decide que un punto no finito debe bloquear: cambio de producción autorizado + prueba nueva",
        "−1 id solo tras la decisión", "ALTO si se retira sin decidir: se perdería la única expresión de la regla P0-G"),
    "test_la_ruta_productiva_no_invoca_el_selector_de_respaldo": (
        "La fuente de _evaluar_horizontes_proyeccion no llama a seleccionar_modelo_por_evidencia.",
        "Ruta vigente", NUEVA + "test_la_ruta_vigente_no_referencia_el_subsistema_heredado; " + P1A +
        "test_la_ruta_productiva_usa_el_selector_rectangular_y_ningun_selector_retirado",
        "PRUEBA NUEVA INCORPORADA", "Retirar por obsolescencia documentada", "2D-3",
        "Las pruebas citadas", "−1 id", "Bajo"),
    "test_el_selector_de_respaldo_no_se_importa_en_la_ruta_productiva": (
        "Ningún import del servicio trae seleccionar_modelo_por_evidencia (comprobación textual).",
        "La misma: no depende de que la función exista", "El propio caso",
        "CUBIERTO YA", "Mantener", "—", "—", "Mismo id", "Ninguno: sobrevive a la 2D"),
    "test_sin_evidencia_comparable_el_horizonte_no_se_entrega": (
        "Sin decisión C-SEL-001 no se fabrica un modelo (lee la fuente de _evaluar_horizontes_proyeccion).",
        "Rama `seleccion is None` de _ejecutar_proyeccion_base", NUEVA + "test_sin_errores_finitos_comunes_no_se_fabrica_un_modelo",
        "PRUEBA NUEVA INCORPORADA", "Retirar por obsolescencia documentada", "2D-3",
        "La prueba nueva citada", "−1 id, +1 id", "Bajo"),
    "test_el_selector_retirado_conserva_su_definicion_para_auditoria": (
        "seleccionar_modelo_por_evidencia existe y su docstring dice «RETIRADA COMO SELECTOR».",
        "Ninguno: exige la existencia del código, que pasa a conservarse en Git (2f70391) y en 02",
        "—", "SIN EQUIVALENTE / NO APLICA", "Retirar por obsolescencia documentada", "2D-4",
        "Ninguna; trazabilidad en 02 §4 con enlace inmutable", "−1 id esencial",
        "Bajo; es la decisión de opción (b) ya tomada"),
    "test_muestra_comun_intacta_desde_el_primer_origen": (
        "Todos los candidatos tienen errores sobre los mismos pares desde el primer origen (via _errores_oos_por_par).",
        "_matriz_rectangular_12_24: mismos orígenes por h y pares_comunes == pares_esperados",
        MET + "test_c_rectangulo_n65_da_w_estrella_30_y_mismos_origenes_por_h; " + P1A +
        "test_la_ruta_productiva_usa_el_selector_rectangular_y_ningun_selector_retirado",
        "CUBIERTO YA", "Retirar por obsolescencia documentada", "2D-2", "—", "−1 id esencial", "Bajo"),
    "test_p0a_p0b_p0d_intactos": (
        "P0-A (sin llamada a seleccionar_modelo_por_evidencia), P0-B (modelos sin sustento) y P0-D llamando a "
        "test_origen_inicial_backtesting::test_p0d_la_regla_de_seleccion_no_cambia (selector heredado).",
        "P0-A y P0-B: los mismos; P0-D: propiedades del selector rectangular", P1A + "test_selector_vigente_cumple[*]",
        "CUBIERTO YA", "Migrar: quitar la llamada a test_p0d y conservar P0-A/P0-B", "2D-2",
        "El mismo caso sin la llamada (P0-D queda en las propiedades de la Fase 1A)", "Mismo id",
        "Bajo; si no se migra, el caso falla al retirar el selector heredado"),
    "test_p0a_el_selector_de_respaldo_sigue_retirado": (
        "La fuente del servicio no contiene la llamada «seleccionar_modelo_por_evidencia(».",
        "La misma: no depende de la existencia", "El propio caso",
        "CUBIERTO YA", "Mantener", "—", "—", "Mismo id", "Ninguno: sobrevive a la 2D"),
    "test_p0d_la_regla_de_seleccion_no_cambia": SELECTOR_CUBIERTO[:5] + ("2D-2",) + SELECTOR_CUBIERTO[6:7] +
        ("−1 id esencial",) + SELECTOR_CUBIERTO[8:],
    "test_horizonte_dinamico_diferencia_tecnico_cautela_y_no_evaluado": HORIZONTE_HISTORICO,
    "test_horizonte_no_salta_un_corte_no_viable": HORIZONTE_HISTORICO,
    "test_iteraciones_insuficientes_limitan_el_intervalo_no_el_horizonte": (
        "Con 1 ventana el horizonte no se cancela y la carencia se comunica (clasificador heredado).",
        "Escasez de ventanas en la ruta vigente", NUEVA + "test_escasez_de_ventanas_entrega_el_punto_con_advertencia_y_sin_intervalo[36|37|41]",
        "PRUEBA NUEVA INCORPORADA", "Retirar por obsolescencia documentada", "2D-3",
        "La prueba nueva citada", "−1 id esencial, cubierto por +3", "Bajo"),
    "test_h1_la_defensa_de_un_horizonte_sin_cautelas_no_menciona_intervalos": (
        "El mensaje «tecnica_alta» del clasificador heredado no cita «e intervalos».",
        "Ninguno: la ruta vigente no produce ese mensaje; el intervalo no se publica (P0-C)",
        NUEVA + "test_escasez_* (intervalo no publicado)", "SIN EQUIVALENTE / NO APLICA",
        "Retirar por obsolescencia documentada", "2D-3", "—", "−1 id esencial", "Bajo"),
    "test_h2_benchmark_habria_ampliado_no_implica_sustitucion": (
        "La salvaguarda heredada sin fallo no se intenta y no sustituye el modelo.",
        "La ruta vigente no llama a la salvaguarda: salvaguarda_benchmark = {intentada: False}",
        PS + "test_ps01_la_salvaguarda_no_sustituye_el_modelo_entregado; " + PS +
        "test_ps01_arena_entrega_drift_por_merito_y_sin_intentar_salvaguarda",
        "CUBIERTO YA", "Retirar por obsolescencia documentada", "2D-3", "—", "−1 id esencial",
        "Bajo; comprobar en 2D que los PS01 no dependan del anexo DANE"),
    "test_maximos_se_derivan_de_clasificaciones_y_no_del_limite_de_grilla": HORIZONTE_HISTORICO,
    "test_limite_evaluable_se_informa_sin_convertirlo_en_validez_absoluta": HORIZONTE_HISTORICO,
    "test_maximo_evaluado_20_es_descriptivo_de_la_funcion_retirada": HORIZONTE_HISTORICO,
    "test_20_puede_ser_maximo_recomendado_si_h20_es_tecnico": HORIZONTE_HISTORICO,
    "test_20_puede_ser_maximo_escenario_si_h20_es_escenario_explicito": HORIZONTE_HISTORICO,
    "test_parada_en_20_por_evidencia_incluye_advertencia_y_no_extrapola": HORIZONTE_HISTORICO,
    "test_la_banda_ausente_no_bloquea_el_punto_pero_el_punto_no_finito_si": (
        "Dirección 1: ninguna banda ausente bloquea un punto finito. Dirección 2: un punto no finito bloquea.",
        "Dirección 1: rama vigente que captura el fallo de la banda. Dirección 2: NO existe en la ruta vigente",
        NUEVA + "test_banda_no_construible_no_cancela_el_punto (solo dirección 1)",
        "DECISIÓN PENDIENTE", "No retirar hasta decidir la regla del punto no finito", "2D-3",
        "Dirección 2 requiere decisión y, si se mantiene la regla, un cambio de producción autorizado",
        "−1 id solo tras la decisión", "ALTO si se retira sin decidir (misma regla P0-G)"),
    # ---------------------------------------------------------------- HISTÓRICAS recolectadas
    "test_la_comparacion_con_el_benchmark_es_frente_a_uno": (
        "peor_que_benchmark_naive: corte 1 frente a naive (lectura descriptiva, C-BEN-002).",
        "Ninguno en la ruta vigente", "—", "SIN EQUIVALENTE / NO APLICA", "Pasar a histórico (retirar con el lote)",
        "2D-3", "—", "−1 id histórico", "Bajo; ficha C-BEN-002 se reubica en AS-024"),
    "test_la_clave_de_factibilidad_es_descriptiva": CLASIF_HISTORICA,
    "test_el_corte_125_no_queda_en_ninguna_via_decisoria": CLASIF_HISTORICA,
    "test_la_salvaguarda_no_sustituye_el_modelo": (
        "La fuente de la salvaguarda no sustituye el modelo.", "La ruta vigente no llama a la salvaguarda",
        PS + "test_ps01_la_salvaguarda_no_sustituye_el_modelo_entregado", "CUBIERTO YA",
        "Retirar por obsolescencia documentada", "2D-3", "—", "−1 id histórico", "Bajo"),
    "test_la_seleccion_no_consulta_ningun_umbral": SELECTOR_CUBIERTO,
    "test_la_seleccion_elige_el_de_menor_error_oos": SELECTOR_CUBIERTO,
    "test_no_queda_cascada_de_prefijo_en_ninguno_de_los_dos_maximos": HORIZONTE_HISTORICO[:3] + (
        "SIN EQUIVALENTE / NO APLICA", "Pasar a histórico (retirar con el lote)", "2D-1/2D-3", "—",
        "−1 id histórico", "Bajo"),
    "test_modelo_agregado_minimiza_el_error_oos_global": SELECTOR_CUBIERTO,
    "test_h1_el_bucle_no_se_detiene_en_el_primer_horizonte_no_recomendable": CLASIF_HISTORICA,
    "test_p0abd_intactos": (
        "P0-A/B/D intactos (comprobación textual y conductual).", "Ídem al caso esencial de test_nmin_adversarial",
        P1A + "test_selector_vigente_cumple[*]", "CUBIERTO YA", "Mantener (revisar en 2D-2 si llama a test_p0d)",
        "2D-2", "—", "Mismo id", "Bajo"),
    "test_g6_los_limites_invertidos_se_clasifican_sin_bloquear_el_punto": (
        "Límites invertidos no bloquean el punto (clasificador heredado).", "Rama vigente que captura el fallo de la banda",
        NUEVA + "test_banda_no_construible_no_cancela_el_punto", "PRUEBA NUEVA INCORPORADA",
        "Pasar a histórico (retirar con el lote)", "2D-3", "—", "−1 id histórico", "Bajo"),
    "test_g7_un_punto_no_finito_sigue_bloqueando": (
        "Un punto no finito bloquea (clasificador heredado).", "NO existe en la ruta vigente", "—",
        "DECISIÓN PENDIENTE", "No retirar hasta decidir la regla del punto no finito", "2D-3",
        "Ver caso esencial equivalente de test_vocabulario_vc", "−1 id solo tras la decisión", "ALTO si se retira sin decidir"),
}
POR_ARCHIVO = {
    "tests/test_cierre_metodologico.py": CLASIF_HISTORICA,
    "tests/test_p0d_rmse_orden_exacto.py": SELECTOR_CUBIERTO,
    "tests/test_rmse_global_estable.py": SELECTOR_CUBIERTO,
    "tests/test_seleccion_rmse_global.py": SELECTOR_CUBIERTO,
    "tests/test_p0c_objeto_publico_sin_intervalo.py": SCRIPT,
    "tests/test_p0c_regresion_negativa_c2.py": SCRIPT,
    "tests/test_regresiones_auditoria_independiente_bghc.py": SCRIPT,
    "tests/test_residuales_auditoria_independiente_r3.py": SCRIPT,
}
CAMPOS = ("contrato", "equivalente_vigente", "prueba_vigente_de_cobertura", "estado_migracion", "decision_2D",
          "lote_2D", "prueba_que_reemplazaria", "consecuencia_inventario", "riesgo_y_justificacion")

filas = []
for r in dep["pruebas"]:
    regla = POR_PRUEBA.get(r["prueba"]) or POR_ARCHIVO.get(r["archivo"])
    assert regla and len(regla) == 9, (r["archivo"], r["prueba"])
    for id_ in r["ids"]:
        if not r.get("recolectada", True):
            antes = "NO RECOLECTADA (error de importación)" if "p0c" in r["archivo"] else "NO RECOLECTADA (sin funciones test_)"
        else:
            antes = ESTADO.get(id_.split("::")[-1], "SIN DATO")
        filas.append({"id": id_, "perfil": "esencial" if r["esencial"] else "historica",
                      "estado_antes_2f70391": antes,
                      "dependencia_heredada": "; ".join(f"{k} ({'/'.join(v)})" for k, v in r["usos"].items()),
                      **dict(zip(CAMPOS, regla))})
with open(sys.argv[4], "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(filas[0]), delimiter=";")
    w.writeheader()
    w.writerows(filas)
from collections import Counter
print(len(filas), "filas;", dict(Counter((x["perfil"], x["estado_migracion"]) for x in filas)))
print("estados antes:", dict(Counter(x["estado_antes_2f70391"] for x in filas)))
