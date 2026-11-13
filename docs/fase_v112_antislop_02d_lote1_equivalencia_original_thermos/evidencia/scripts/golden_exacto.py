"""Compara, SIN tolerancia, la captura Fase 0 de una raíz con los Golden Masters generados sobre 6672529.

Uso: python -I golden_exacto.py <raiz_app> <dir_golden> <salida.txt>
Los golden (`metadatos.json`: commit_referencia 6672529, mismo equipo y paquetes) son una foto de la V1.1.2 original.
Se reutilizan las funciones de captura del arnés (motor y económico) y su comparador con rel_tol=0 y abs_tol=0:
cualquier diferencia de un bit en un flotante cuenta. La sección GUI la cubre oraculo.py.
"""
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
raiz, golden, salida = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
sys.path[:0] = [str(AQUI / "arnes"), str(raiz)]
import app_icociv  # noqa: E402
from tests.fixtures.fase0 import captura as c, generadores as gen  # noqa: E402

assert raiz.resolve() in Path(app_icociv.__file__).resolve().parents
lineas = [f"raiz={raiz}", f"golden={golden}", "tolerancia: rel_tol=0 abs_tol=0 (exacta)"]
motor = json.loads((golden / "motor.json").read_text(encoding="utf-8"))
economico = json.loads((golden / "economico.json").read_text(encoding="utf-8"))
total = 0
for nombre in gen.ESCENARIOS_MOTOR:
    d = c.diferencias(motor["escenarios"][nombre], c.capturar_motor(nombre),
                      f"motor.{nombre}", limite=50, rel_tol=0.0, abs_tol=0.0)
    total += len(d)
    lineas.append(f"motor.{nombre}: {len(d)} diferencias")
    lineas += ["   " + x for x in d[:20]]
for clave, esperado, fn in (("economico", economico, c.capturar_economico), ("rechazos", motor["rechazos"], c.capturar_rechazos)):
    d = c.diferencias(esperado, fn(), clave, limite=50, rel_tol=0.0, abs_tol=0.0)
    total += len(d)
    lineas.append(f"{clave}: {len(d)} diferencias")
    lineas += ["   " + x for x in d[:20]]
lineas.append(f"TOTAL diferencias exactas: {total}")
salida.write_text("\n".join(lineas) + "\n", encoding="utf-8", newline="\n")
print("\n".join(lineas[-12:]))
