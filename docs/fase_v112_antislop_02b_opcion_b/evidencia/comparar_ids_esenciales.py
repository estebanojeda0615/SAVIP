"""Fase 2B: compara el conjunto de ids y estados del perfil esencial entre dos ejecuciones.

Uso: python comparar_ids_esenciales.py <resultados_antes/> <resultados_despues/>

Lee los JUnit por archivo que deja `scripts/pruebas_fase0.py esenciales` (sin los `__reintento.xml`) y compara
(classname, name) y su estado. Sale con 1 si cambia el conjunto o algún estado.
"""
import glob
import sys
import xml.etree.ElementTree as ET


def estados(carpeta):
    d = {}
    for p in glob.glob(f"{carpeta}/*.xml"):
        if "__reintento" in p:
            continue
        for tc in ET.parse(p).getroot().iter("testcase"):
            estado = ("FAIL" if tc.find("failure") is not None or tc.find("error") is not None
                      else "SKIP" if tc.find("skipped") is not None else "PASS")
            d[(tc.get("classname"), tc.get("name"))] = estado
    return d


a, b = estados(sys.argv[1]), estados(sys.argv[2])
solo_antes, solo_despues = sorted(set(a) - set(b)), sorted(set(b) - set(a))
cambiados = sorted(k for k in set(a) & set(b) if a[k] != b[k])
for nombre, d in (("antes", a), ("después", b)):
    print(f"{nombre}: {len(d)} ids; " + ", ".join(f"{e} {list(d.values()).count(e)}" for e in ("PASS", "FAIL", "SKIP")))
print(f"solo antes: {len(solo_antes)}; solo después: {len(solo_despues)}; estado cambiado: {len(cambiados)}")
for k in solo_antes + solo_despues + cambiados:
    print("  ", k)
print("CONJUNTO IDÉNTICO" if not (solo_antes or solo_despues or cambiados) else "DIFERENCIAS")
sys.exit(1 if (solo_antes or solo_despues or cambiados) else 0)
