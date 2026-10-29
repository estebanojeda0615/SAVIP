"""Fase 2C: sensibilidad de tests/test_fase2c_contratos_vigentes.py.

Uso: python sensibilidad_pruebas_nuevas.py <copia_limpia_del_repo> <carpeta_de_trabajo>

Por escenario copia el repositorio, aplica UNA mutación a la copia (nunca al repositorio) y ejecuta la prueba
indicada, que debe FALLAR. CTRL ejecuta el archivo completo sin mutación y debe PASAR.

  M0 publica el intervalo: `ejecutar_proyeccion` deja de pasar por `_retirar_intervalo_de_publicacion`.
  M1 acopla banda y punto: si el intervalo no se puede construir, la excepción cancela la proyección.
  M2 retira la advertencia de escasez de ventanas (analisis_series).
  M3 `_texto_evidencia_oos` llama «validada» al tramo muy limitado.
  M4 sin errores finitos comunes se fabrica un modelo (el primero del banco) en vez de no entregar.
  M5 la ruta vigente vuelve a llamar al selector heredado.
"""
import shutil
import subprocess
import sys
from pathlib import Path

origen, trabajo = Path(sys.argv[1]), Path(sys.argv[2])
ARCHIVO = "tests/test_fase2c_contratos_vigentes.py"
SP = "app_icociv/proyeccion/servicio_proyeccion.py"
AS = "app_icociv/estadistica/analisis_series.py"


def reemplazar(ruta, viejo, nuevo):
    def mutar(destino):
        p = destino / ruta
        t = p.read_text(encoding="utf-8-sig")
        assert t.count(viejo) == 1, (ruta, viejo[:60], t.count(viejo))
        p.write_text(t.replace(viejo, nuevo), encoding="utf-8")
    return mutar


ESCENARIOS = [
    ("CTRL_sin_mutacion", None, ARCHIVO, 0),
    ("M0_publica_el_intervalo", reemplazar(SP, "    return _retirar_intervalo_de_publicacion(\n",
                                           "    return (lambda resultado: resultado)(\n"),
     ARCHIVO + "::test_escasez_de_ventanas_entrega_el_punto_con_advertencia_y_sin_intervalo", 1),
    ("M1_banda_cancela_punto", reemplazar(SP, "        intervalos = []\n", "        raise\n"),
     ARCHIVO + "::test_banda_no_construible_no_cancela_el_punto", 1),
    ("M2_sin_advertencia_de_escasez", reemplazar(AS, "        if iteraciones < MIN_ITERACIONES_BACKTESTING:\n",
                                                 "        if False:\n"),
     ARCHIVO + "::test_escasez_de_ventanas_entrega_el_punto_con_advertencia_y_sin_intervalo", 1),
    ("M3_tramo_limitado_validado", reemplazar(
        SP, 'return f"Evidencia fuera de muestra disponible pero muy limitada (n={w})."',
        'return f"Evidencia fuera de muestra validada (n={w})."'),
     ARCHIVO + "::test_texto_evidencia_oos_tres_tramos_sin_vocabulario_de_validacion", 1),
    ("M4_modelo_fabricado", reemplazar(
        SP, "    seleccion = _seleccionar_modelo_rectangular(matriz, modelos_evaluados)\n    if seleccion is None:\n",
        "    seleccion = _seleccionar_modelo_rectangular(matriz, modelos_evaluados)\n"
        "    if seleccion is None:\n        seleccion = {'modelo': modelos_evaluados[0]}\n    if False:\n"),
     ARCHIVO + "::test_sin_errores_finitos_comunes_no_se_fabrica_un_modelo", 1),
    ("M5_ruta_llama_selector_heredado", reemplazar(
        SP, "    seleccion = _seleccionar_modelo_rectangular(matriz, modelos_evaluados)\n",
        "    seleccion = _seleccionar_modelo_rectangular(matriz, modelos_evaluados)\n"
        "    _ = seleccionar_modelo_por_rmse_oos_global  # mutante\n"),
     ARCHIVO + "::test_la_ruta_vigente_no_referencia_el_subsistema_heredado", 1),
]

ok = True
for nombre, mutar, objetivo, esperado_falla in ESCENARIOS:
    destino = trabajo / nombre
    if destino.exists():
        shutil.rmtree(destino)
    shutil.copytree(origen, destino, ignore=shutil.ignore_patterns("__pycache__", "resultados"))
    if mutar:
        mutar(destino)
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", objetivo], cwd=destino,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    falla = r.returncode != 0
    resumen = next((l for l in reversed(r.stdout.splitlines()) if "passed" in l or "failed" in l or "error" in l), "")
    print(f"{nombre}: {'FALLA' if falla else 'PASA'} | {resumen}")
    ok &= falla == bool(esperado_falla)
print("RESULTADO:", "sensibilidad confirmada" if ok else "SENSIBILIDAD INSUFICIENTE")
sys.exit(0 if ok else 1)
