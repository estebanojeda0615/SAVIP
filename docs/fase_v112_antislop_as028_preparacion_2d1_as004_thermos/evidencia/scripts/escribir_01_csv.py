"""Escribe 01_INVENTARIO_SCRIPT_29_TESTS.csv: parte del inventario de AS-028/2D-2 (30 filas), retira la fila ya
retirada entonces, recalcula líneas sobre la base 102f194 (AST), toma estado y duración de los JUnit base/final y
reescribe las filas de las tres pruebas 2D-1 con el análisis G1 de esta fase.
Uso: python escribir_01_csv.py <csv_2d2> <script_base.py> <junit_base> <junit_final> <salida.csv>
"""
import ast
import csv
import io
import sys
import xml.etree.ElementTree as E

csv_prev, script, jb, jf, salida = sys.argv[1:]
filas = list(csv.DictReader(open(csv_prev, encoding="utf-8")))
filas = [f for f in filas if f["id"] != "test_el_modelo_entregado_es_el_de_minimo_error_oos_global"]
lineas = {n.name: f"{n.lineno}-{n.end_lineno}" for n in ast.parse(open(script, encoding="utf-8").read()).body
          if isinstance(n, ast.FunctionDef)}


def estados(ruta):
    out = {}
    for c in E.parse(ruta).getroot().iter("testcase"):
        f = c.find("failure") if c.find("failure") is not None else c.find("error")
        if f is None:
            out[c.get("name")] = f"PASS {float(c.get('time')):.1f} s"
        else:
            msg = (f.get("message") or "").splitlines()[0]
            loc = [l for l in (f.text or "").splitlines() if "prueba_horizonte_dinamico_ui_reportes.py:" in l]
            linea = loc[-1].split(".py:")[1].split(":")[0] if loc else "?"
            out[c.get("name")] = f"FAIL {msg.split(':')[0]} L{linea}"
    return out


eb, ef = estados(jb), estados(jf)
G1 = "02_AS028_TRES_DEPENDENCIAS_2D1.md; evidencia/asercion_por_asercion.json"
RET = {
    "test_horizonte_maximo_no_es_18_si_h18_no_cumple": dict(
        clasificacion="DEPENDENCIA 2D-1 — HISTÓRICA / NO APLICA",
        contrato="evaluador heredado de horizonte máximo (función no alcanzable desde producción)",
        prueba_equivalente_exacta="no aplica: la propiedad no existe en la ruta vigente (KeyError en las 5 aserciones sobre ejecutar_proyeccion h=12/h=18). Contrato vigente: test_metodologia_n0_12_h24::test_b_h_operativo_max_es_24 y ::test_efg_horizonte_solicitado_no_cambia_modelo_ni_trayectoria; test_fase1a_selector_rectangular::test_la_ruta_productiva_usa_el_selector_rectangular_y_ningun_selector_retirado; test_fase2c_contratos_vigentes::test_la_ruta_vigente_no_referencia_el_subsistema_heredado",
        divergencia_de_expectativa="bajo N0=12/H=24 no hay máximo recomendado/escenario por horizonte: alcance fijo de 24 y h=18 se entrega",
        decision="RETIRADO en 5133abc (lápida corregida en 56d9562; main() actualizado)", riesgo="nulo: sin contrato vigente perdido", futuro_lote="2D-1 (elimina una de las tres referencias del script)"),
    "test_mensaje_no_recomendables_no_imprime_lista_vacia": dict(
        clasificacion="DEPENDENCIA 2D-1 — HISTÓRICA / NO APLICA",
        contrato="formato de mensajes del evaluador heredado (mensaje_ui, mensaje_no_recomendables)",
        prueba_equivalente_exacta="no aplica: mensaje_ui y mensaje_no_recomendables no se producen en la ruta vigente (KeyError en las 4 aserciones). La UI vigente usa razon_principal (sonda AS-004: 28/28 ejecuciones nuevas)",
        divergencia_de_expectativa="la ruta vigente no tiene lista de horizontes no recomendables",
        decision="RETIRADO en 5133abc (lápida corregida en 56d9562; main() actualizado)", riesgo="nulo", futuro_lote="2D-1"),
    "test_h18_no_se_redacta_como_intervalos_aceptables": dict(
        clasificacion="DEPENDENCIA 2D-1 + AS-004 — HISTÓRICA / NO APLICA (ambas mitades)",
        contrato="(a) clasificación del evaluador heredado; (b) redacción del informe previa a 12/24 en _lineas_horizontes/_lineas_determinacion_horizonte",
        prueba_equivalente_exacta="no aplica: con su propia entrada falla (2 False + 4 TypeError: no existe la línea '18 meses |'); sobre la salida productiva h=18 solo pasan '18 meses' y la ausencia de 'backtesting e intervalos aceptables', cadena que solo existe en el fixture del propio script (L122). Redacción vigente de _lineas_*: test_pool_calendario_fourier_seasonal::test_casoJ_ids_internos_no_visibles_en_ui_ni_reportes (sin cambios)",
        divergencia_de_expectativa="el generador ya redacta 'Horizonte solicitado/Alcance máximo' (comentario Prompt 12); el informe productivo (contenido.py) no publica intervalos (P0-C)",
        decision="RETIRADO en 5133abc (lápida corregida en 56d9562; main() actualizado)", riesgo="nulo: el FAIL histórico desaparece por baja justificada, no por cambio de expectativa", futuro_lote="2D-1 y AS-004"),
}
out = []
for f in filas:
    t = f["id"]
    nuevo = {"id": t, "rango_lineas_102f194": lineas.get(t, "?"), "clasificacion": f["clasificacion"],
             "importaciones": f["importaciones"], "llamadas_heredadas": f["llamadas_heredadas"],
             "superficie_validada": f["superficie_validada"], "contrato": f["contrato"],
             "estado_102f194": eb.get(t, "AUSENTE"), "estado_56d9562": ef.get(t, "RETIRADO"),
             "evidencia": f"evidencia/script_base_pytest.xml; evidencia/script_56d9562_pytest.xml",
             "prueba_equivalente_exacta": f["prueba_equivalente_exacta"],
             "divergencia_de_expectativa": f["divergencia_de_expectativa"],
             "decision": "CONSERVAR sin cambios (fuera de la autorización de esta fase)", "riesgo": f["riesgo"].replace("2D-2", "2D-1"),
             "futuro_lote": f["futuro_lote"]}
    if t in RET:
        nuevo.update(RET[t]); nuevo["evidencia"] += "; " + G1
    if t in ("test_horizonte_dinamico_con_serie_drift", "test_horizonte_dinamico_con_serie_holt"):
        nuevo["clasificacion"] = "HISTÓRICO; DEPENDENCIA AS-004 (no 2D-1)"
        nuevo["llamadas_heredadas"] = nuevo["llamadas_heredadas"].replace("(prod=False)", "(alcanzables solo desde tests/scripts)")
        nuevo["decision"] = "CONSERVAR sin cambios (§5.2: asunto posterior de AS-004)"
        nuevo["riesgo"] = "bloquea el retiro AS-004 de _lineas_*, no 2D-1"
    out.append(nuevo)
assert len(out) == 29 and len({r["id"] for r in out}) == 29
buf = io.StringIO()
w = csv.DictWriter(buf, fieldnames=list(out[0]), lineterminator="\n")
w.writeheader(); w.writerows(out)
open(salida, "wb").write(buf.getvalue().encode("utf-8"))
print("filas", len(out))
