"""G1 (solo lectura): evalúa una a una las aserciones de los tres tests del script que dependen de 2D-1,
(a) con la entrada sintética del propio test (función heredada) y (b) sobre la salida PRODUCTIVA real
(`ejecutar_proyeccion` con la misma serie estable del script, h=12 y h=18), para mostrar si la propiedad
existe en la ruta vigente. No modifica nada.

Las aserciones se transcriben de la versión 102f194 del script; se registra el SHA-256 del script cargado y se exige
que contenga las tres pruebas (ejecutar sobre la copia de la base, no sobre el HEAD final, donde ya no están).
Uso: python asercion_por_asercion.py <raiz_repo_102f194> <salida.json>
"""
import importlib.util
import json
import sys
from pathlib import Path

raiz = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(raiz))
import hashlib  # noqa: E402
RUTA_SCRIPT = raiz / "pruebas/prueba_horizonte_dinamico_ui_reportes.py"
SHA_SCRIPT = hashlib.sha256(RUTA_SCRIPT.read_bytes()).hexdigest()
for t in ("test_horizonte_maximo_no_es_18_si_h18_no_cumple", "test_mensaje_no_recomendables_no_imprime_lista_vacia",
          "test_h18_no_se_redacta_como_intervalos_aceptables"):
    assert f"def {t}(" in RUTA_SCRIPT.read_text(encoding="utf-8"), f"{t} no está en el script: use la copia de 102f194"
spec = importlib.util.spec_from_file_location("script_hist", RUTA_SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
from app_icociv.proyeccion.servicio_proyeccion import determinar_horizonte_maximo_estadistico as det, ejecutar_proyeccion  # noqa: E402
from app_icociv.reportes.generador_reportes import _lineas_horizontes, _lineas_determinacion_horizonte  # noqa: E402

ev = m._evaluacion_horizonte


def evaluar(asertos, ctx):
    out = []
    for texto in asertos:
        try:
            out.append([texto, bool(eval(texto, {}, ctx))])
        except Exception as e:  # la propiedad no existe en ese objeto
            out.append([texto, f"{type(e).__name__}: {e}"[:140]])
    return out


R = {"sha256_script_fuente": SHA_SCRIPT}
# ---- test 1
e1 = [ev(h, rmse=0.8 + 0.19 * h, mape=0.6 + 0.12 * h, ic95=0.05 + 0.01 * h) for h in range(1, 13)]
e1.append(ev(18, tecnico=False, escenario=False, rmse=5.8823, mae=5.1511, mape=3.8063, ic95=0.5350, decision="No recomendable"))
A1 = ['info["horizonte_maximo_recomendado"] == 12', 'info["horizonte_maximo_permitido_como_escenario"] == 0',
      'info["horizontes_no_recomendables"] == [18]', '"h=18" in info["mensaje_ui"]',
      'info["tipo_uso_recomendado"] == "Proyección extendida con cautela"']
# ---- test 2
e2 = [ev(h, estado="Alta confiabilidad relativa") for h in range(1, 7)]
A2 = ['info["horizontes_no_recomendables"] == []', '"[]" not in info["mensaje_ui"]',
      '"No se identificaron horizontes no recomendables" in info["mensaje_no_recomendables"]',
      'info["primer_horizonte_no_viable"] == 0']
# ---- test 3
e3 = [ev(h) for h in range(1, 13)] + [ev(18, tecnico=False, escenario=False, rmse=5.8823, mape=3.8063, ic95=0.5350)]
A3 = ['"Horizonte máximo recomendado: 12" in lineas', '"h=18 no recomendable" in lineas', '"18 meses" in lineas',
      '"permitido=No" in linea_h18', '"técnico=No" in linea_h18', '"escenario=No" in linea_h18',
      '"backtesting e intervalos aceptables" not in linea_h18']


def lineas_de(resultado):
    txt = "\n".join(_lineas_horizontes(resultado) + _lineas_determinacion_horizonte(resultado))
    h18 = next((l for l in txt.splitlines() if l.startswith("18 meses |")), None)
    return txt, h18


info1 = det(None, None, None, e1, None, horizonte_solicitado=12)
info2 = det(None, None, None, e2, None, horizonte_solicitado=6)
info3 = det(None, None, None, e3, None, horizonte_solicitado=12)
res3 = {"horizonte_info": info3, "horizonte_solicitado": 12, "model_name": "Drift", "horizonte_permitido": 12}
l3, h3 = lineas_de(res3)
R["test_horizonte_maximo_no_es_18_si_h18_no_cumple"] = {"entrada_del_test": evaluar(A1, {"info": info1})}
R["test_mensaje_no_recomendables_no_imprime_lista_vacia"] = {"entrada_del_test": evaluar(A2, {"info": info2})}
R["test_h18_no_se_redacta_como_intervalos_aceptables"] = {"entrada_del_test": evaluar(A3, {"lineas": l3, "linea_h18": h3}),
                                                          "linea_h18_encontrada": h3}

# ---- ruta productiva: misma serie estable del script, h=12 y h=18
for h, (anio, mes) in {12: (2031, 12), 18: (2032, 6)}.items():
    r = ejecutar_proyeccion(m._serie_estable(120), anio, mes, 2021)
    info = r.get("horizonte_info") or {}
    lp, hp = lineas_de(r)
    clave = f"productivo_h{h}"
    R["test_horizonte_maximo_no_es_18_si_h18_no_cumple"][clave] = evaluar(A1, {"info": info})
    R["test_mensaje_no_recomendables_no_imprime_lista_vacia"][clave] = evaluar(A2, {"info": info})
    R["test_h18_no_se_redacta_como_intervalos_aceptables"][clave] = evaluar(A3, {"lineas": lp, "linea_h18": hp or ""})
    R[f"contexto_{clave}"] = {"horizonte_solicitado": r.get("horizonte_solicitado"), "horizonte_permitido": r.get("horizonte_permitido"),
                              "proyeccion_generada": r.get("proyeccion_generada"),
                              "alcance_maximo_proyeccion": info.get("alcance_maximo_proyeccion"),
                              "filas_tabla_horizontes": len(info.get("tabla_horizontes") or []),
                              "claves_horizonte_info": sorted(info)}
json.dump(R, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for t, d in R.items():
    if not isinstance(d, dict):
        print(t, d); continue
    print("==", t)
    for k, v in d.items():
        if isinstance(v, list) and v and isinstance(v[0], list):
            print("  ", k, [x[1] if isinstance(x[1], bool) else x[1].split(":")[0] for x in v])
        else:
            print("  ", k, v if not isinstance(v, list) else "")
