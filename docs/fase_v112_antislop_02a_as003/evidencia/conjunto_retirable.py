"""Fase 2A (AS-003): conjunto retirable cerrado a partir del grafo de grafo_as003.py.

Uso: python conjunto_retirable.py <raiz_del_repo> <grafo.json> [prueba_esencial_ignorada ...]

Las pruebas esenciales pasadas como argumento extra no cuentan como ancla (simulación de su adaptación).

Candidatas: definiciones de servicio_proyeccion.py, modelos_interpretables.py y validacion_series.py NO
alcanzables desde producción. Se conservan (y con ellas todo lo que llaman) las que:
  - referencia directamente una prueba del perfil esencial (las 797 no deben tocarse);
  - referencia un script de pruebas/ o scripts/ (contrato S);
  - cita como ubicación una ficha de criterios.py (contrato D).
Retirable = candidatas fuera del cierre de lo conservado.
"""
import importlib.util
import json
import re
import sys
from pathlib import Path

raiz = Path(sys.argv[1])
d = json.load(open(sys.argv[2], encoding="utf-8"))
ALCANCE = ("servicio_proyeccion.py", "modelos_interpretables.py", "validacion_series.py")
cand = {k for k, v in d.items() if v["archivo"].endswith(ALCANCE) and not v["produccion"]}

spec = importlib.util.spec_from_file_location("pf", raiz / "scripts" / "pruebas_fase0.py")
pf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pf)
esenciales = set(pf.ESENCIALES) - set(sys.argv[3:])

motivo = {}
for k in cand:
    v = d[k]
    ess = [t for t in v["tests_directos"] if t in esenciales]
    if ess:
        motivo[k] = "prueba esencial: " + ", ".join(ess)
    elif v["scripts_directos"]:
        motivo[k] = "script: " + ", ".join(v["scripts_directos"])
    elif v["citas_documentales"]:
        motivo[k] = "ficha documental: " + ", ".join(v["citas_documentales"])

# Aristas salientes reconstruidas desde referenciado_por.
salientes = {k: set() for k in d}
for k, v in d.items():
    for r in v["referenciado_por"]:
        salientes[r].add(k)

conservar = set(motivo)
pila = list(conservar)
while pila:
    x = pila.pop()
    for y in salientes[x]:
        if y in cand and y not in conservar:
            conservar.add(y)
            motivo[y] = "llamada por conservada: " + x.split(":")[1]
            pila.append(y)

retirable = cand - conservar
# Comprobación de cierre: nadie fuera del conjunto retirable referencia algo del conjunto.
for k in retirable:
    fuera = [r for r in d[k]["referenciado_por"] if r not in retirable]
    assert not fuera, (k, fuera)

def fila(k):
    v = d[k]
    return f"{v['archivo'].split('/')[-1]}:{v['ini']}-{v['fin']} ({v['lineas']}) {k.split(':')[1]}"

print("RETIRABLES (cerrado):", len(retirable), "definiciones,", sum(d[k]["lineas"] for k in retirable), "líneas")
for k in sorted(retirable, key=lambda k: (d[k]["archivo"], d[k]["ini"])):
    print("  ", fila(k), "| pruebas no esenciales:", ", ".join(d[k]["tests_directos"]) or "ninguna")
print("CONSERVADAS:", len(conservar), "definiciones,", sum(d[k]["lineas"] for k in conservar), "líneas")
for k in sorted(conservar, key=lambda k: (d[k]["archivo"], d[k]["ini"])):
    print("  ", fila(k), "|", motivo[k])
