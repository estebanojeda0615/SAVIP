"""Fase 2B (AS-003, opción B): sensibilidad de la prueba esencial adaptada.

Uso: python sensibilidad_prueba_integracion.py <copia_limpia_del_repo> <carpeta_de_trabajo> <servicio_proyeccion_base.py>

Copia el repositorio a una carpeta de trabajo por escenario, aplica UNA mutación a la copia de
`servicio_proyeccion.py` (nunca al repositorio) y ejecuta solo
`test_la_ruta_productiva_usa_el_selector_rectangular_y_ningun_selector_retirado`. Cada mutación debe hacerla FALLAR:

  S0  producción de la base (1848275): las tres funciones retiradas siguen definidas -> falla la exigencia de ausencia.
  S1  la ruta productiva invoca además el selector heredado `seleccionar_modelo_por_rmse_oos_global`
      -> falla el espía (call_count != 0).
  S2  la ruta productiva sustituye el selector rectangular por un mutante que ordena por suma FLOTANTE sobre TODOS
      los pares de cada candidato (viola SSE exacto y muestra común) -> falla `vigente.call_count == 1`.
  CTRL sin mutación -> debe PASAR.
"""
import shutil
import subprocess
import sys
from pathlib import Path

origen, trabajo, base = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
PRUEBA = "tests/test_fase1a_selector_rectangular.py::test_la_ruta_productiva_usa_el_selector_rectangular_y_ningun_selector_retirado"
LLAMADA = "    seleccion = _seleccionar_modelo_rectangular(matriz, modelos_evaluados)\n"
MUTANTE = '''

def _selector_mutante(matriz, modelos):
    datos = matriz["datos"]
    sse = {m: sum(v[0] ** 2 for v in datos[m].values()) for m in modelos
           if all(math.isfinite(v[0]) for v in datos[m].values())}
    ganador = min(sse, key=sse.get)
    return {"modelo": ganador, "rmse_seleccion_oos": math.sqrt(sse[ganador] / len(datos[ganador])),
            "modelo_segundo": None, "rmse_segundo_oos": None, "diferencia_absoluta": None,
            "diferencia_porcentual": None, "pares_comunes": len(datos[ganador]),
            "pares_esperados": int(matriz["w_estrella"]) * len(matriz["horizontes"])}
'''


def escenario(nombre, mutar):
    destino = trabajo / nombre
    if destino.exists():
        shutil.rmtree(destino)
    shutil.copytree(origen, destino, ignore=shutil.ignore_patterns("__pycache__", "resultados"))
    archivo = destino / "app_icociv" / "proyeccion" / "servicio_proyeccion.py"
    texto = archivo.read_text(encoding="utf-8-sig")
    archivo.write_text(mutar(texto), encoding="utf-8")
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", PRUEBA],
                       cwd=destino, capture_output=True, text=True, encoding="utf-8", errors="replace")
    lineas = [l for l in r.stdout.splitlines() if l.startswith("E ") or "passed" in l or "failed" in l]
    motivo = next((l for l in lineas if l.startswith("E ")), "")
    print(f"{nombre}: {'PASA' if r.returncode == 0 else 'FALLA'} | {lineas[-1] if lineas else ''} | {motivo[:160]}")
    return r.returncode


def reemplazar_una(texto, viejo, nuevo):
    assert texto.count(viejo) == 1, viejo
    return texto.replace(viejo, nuevo)


codigos = {
    "CTRL_sin_mutacion": escenario("CTRL_sin_mutacion", lambda t: t),
    "S0_produccion_base": escenario("S0_produccion_base", lambda t: base.read_text(encoding="utf-8-sig")),
    "S1_invoca_selector_heredado": escenario("S1_invoca_selector_heredado", lambda t: reemplazar_una(
        t, LLAMADA, "    seleccionar_modelo_por_rmse_oos_global({}, (1,))\n" + LLAMADA)),
    "S2_selector_mutante": escenario("S2_selector_mutante", lambda t: reemplazar_una(
        t, LLAMADA, LLAMADA.replace("_seleccionar_modelo_rectangular(", "_selector_mutante(")) + MUTANTE),
}
esperado = {"CTRL_sin_mutacion": 0}
ok = all((c == 0) == (esperado.get(n, 1) == 0) for n, c in codigos.items())
print("RESULTADO:", "sensibilidad confirmada" if ok else "SENSIBILIDAD INSUFICIENTE")
sys.exit(0 if ok else 1)
