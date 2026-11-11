"""Analiza las trazas del plugin pasivo. Para cada ventana del spy de `contraccion_cambiada` (desde su creación hasta el
siguiente evento de preparación: otro spy o un resize) cuenta las emisiones y su origen, y si el temporizador de ancho
venció dentro de la ventana.

Uso: python analizar_traza_3ca.py <traza.jsonl> [<traza.jsonl> ...]
"""
import json
import sys
from collections import Counter


def _origen(s):
    o = s["origen"]
    if any("_adaptar_ancho" in x for x in o):
        return "temporizador"
    if any("alternar_contraccion" in x for x in o):
        return "clic"
    if any("test_interaccion" in x for x in o):
        return "test"
    return "otro"


def ventanas(filas):
    ev = [r for r in filas if r["tipo"] == "traza"]
    res = [r for r in filas if r["tipo"] == "resultado"]
    salida = []
    for i, r in enumerate(ev):
        if r["evento"] == "QSignalSpy_creado" and "contraccion_cambiada" in r["senal"]:
            dentro = []
            for s in ev[i + 1:]:
                # La ventana termina en el siguiente paso de PREPARACIÓN del test: otro spy o una emisión causada por una
                # llamada directa del test a establecer_contraccion (iteración siguiente). Un resize DENTRO de la ventana
                # se conserva y se informa (no corta la ventana: ocultaría su efecto).
                if s["evento"] == "QSignalSpy_creado":
                    break
                if s["evento"] == "contraccion_cambiada" and _origen(s) == "test":
                    break
                dentro.append(s)
            emis = [s for s in dentro if s["evento"] == "contraccion_cambiada"]
            salida.append({
                "t_spy_ms": r["t_ms"], "desde_resize_ms": r["desde_resize_ms"],
                "clicked": sum(s["evento"] == "boton_contraer.clicked" for s in dentro),
                "emisiones": [(s["arg"], _origen(s)) for s in emis],
                "resize_en_ventana": [s["tam"] for s in dentro if s["evento"] == "resizeEvent"],
                "temporizador_en_ventana": [(s["ancho"], s["desde_resize_ms"], s["modo_compacto_tras_ajuste"], s["contraida_tras_ajuste"])
                                            for s in dentro if s["evento"] == "_temporizador_ancho.timeout"],
            })
    return salida, res


for archivo in sys.argv[1:]:
    filas = [json.loads(l) for l in open(archivo, encoding="utf-8")]
    vs, res = ventanas(filas)
    anomalas = [v for v in vs if len(v["emisiones"]) != 1 or v["clicked"] != 1]
    con_timer = [v for v in vs if v["temporizador_en_ventana"]]
    print(f"{archivo}: resultado={[r['resultado'] for r in res]} ventanas_toggle={len(vs)} anomalas={len(anomalas)} "
          f"temporizador_dentro={len(con_timer)} origenes={dict(Counter(o for v in vs for _, o in v['emisiones']))}")
    for v in anomalas + [v for v in con_timer if v not in anomalas]:
        print("   ", v)
