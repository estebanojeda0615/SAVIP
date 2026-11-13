#!/usr/bin/env bash
# Lote 2D-1, G0/G4.0: línea base sobre copia limpia de 8e5a62b y la original 6672529, sin editar producción.
set -u
A="C:/Pruebas SAVIP/L1D1"; B="$A/base"; G="$A/g0"; L2="C:/Pruebas SAVIP/L2/oraculo"; A28="C:/Pruebas SAVIP/A28D1"
P="C:/Pruebas SAVIP/Fase0/venv-test/Scripts/python.exe"
EVID="$B/docs/fase_v112_antislop_02a_as003/evidencia"
export QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8
cd "$B" || exit 1
echo "[$(date -u +%T)] estatico"
"$P" "$EVID/grafo_as003.py" "$B" "$G/grafo_8e5a62b.json" > "$G/grafo_8e5a62b.txt" 2>&1
"$P" scripts/pruebas_fase0.py --listar > "$G/base_listar.txt" 2>&1
"$P" -m pytest --collect-only -q -p no:cacheprovider tests > "$G/base_collect.txt" 2>&1; echo "codigo=$?" >> "$G/base_collect.txt"
"$P" "$EVID/huella_semantica.py" capturar "$G/huella_base.json" > "$G/huella_base.txt" 2>&1
"$P" "$EVID/huella_semantica.py" comparar "$A28/g0/huella_base.json" "$G/huella_base.json" >> "$G/huella_base.txt" 2>&1
sha256sum "$G/huella_base.json" >> "$G/huella_base.txt"
echo "[$(date -u +%T)] script"
"$P" -m pytest pruebas/prueba_horizonte_dinamico_ui_reportes.py -p no:cacheprovider -q -rA --junitxml="$G/script_base_pytest.xml" > "$G/script_base_pytest.txt" 2>&1; echo "codigo=$?" >> "$G/script_base_pytest.txt"
echo "[$(date -u +%T)] historicas afectadas"
"$P" -m pytest -p no:cacheprovider -q -rfE tests/test_cierre_metodologico.py > "$G/cierre_base.txt" 2>&1; echo "codigo=$?" >> "$G/cierre_base.txt"
echo "[$(date -u +%T)] simulacion de ausencia"
export PYTHONPATH="$A28/g4"
"$P" -m pytest -p ocultar_2d1 -p no:cacheprovider --collect-only -q tests > "$G/collect_oculto.txt" 2>&1; echo "codigo=$?" >> "$G/collect_oculto.txt"
"$P" -m pytest -p ocultar_2d1 -p no:cacheprovider -q -rfE tests/test_resultado_horizonte_solicitado.py tests/test_presentacion_resultados.py tests/test_fase1a_selector_rectangular.py tests/test_fase2c_contratos_vigentes.py tests/test_pool_calendario_fourier_seasonal.py tests/test_cierre_metodologico.py > "$G/afectados_oculto.txt" 2>&1; echo "codigo=$?" >> "$G/afectados_oculto.txt"
"$P" -m pytest -p ocultar_2d1 -p no:cacheprovider -q pruebas/prueba_horizonte_dinamico_ui_reportes.py --junitxml="$G/script_base_oculto.xml" > "$G/script_base_oculto.txt" 2>&1
unset PYTHONPATH
cd "$A"
"$P" "$A28/g2/sonda_claves_as004.py" "$B" "$G/sonda_base.json" > "$G/sonda_base.txt" 2>&1
"$P" "$A28/g4/sonda_oculto.py" "$B" "$A28/g2/sonda_claves_as004.py" "$G/sonda_base.json" "$G/sonda_oculto.json" > "$G/sonda_oculto.txt" 2>&1
find "$B" -name __pycache__ -type d -prune -exec rm -rf {} +
echo "[$(date -u +%T)] oraculo 8e5a62b y original"
cd "$L2"
for sha in 8e5a62b 6672529; do
  run=r1; [ "$sha" = 6672529 ] && run=r4
  S=$(date +%s); "$P" -I oraculo.py "C:/Pruebas SAVIP/L2/fuentes/$sha" "salidas/${sha}_$run.json" > "salidas/${sha}_$run.log" 2>&1; echo "codigo=$? duracion=$(( $(date +%s)-S ))s" >> "salidas/${sha}_$run.log"
done
"$P" -I golden_exacto.py "C:/Pruebas SAVIP/L2/fuentes/8e5a62b" "C:/Pruebas SAVIP/L2/fuentes/8e5a62b/tests/fixtures/fase0/golden" salidas/golden_exacto_8e5a62b.txt > /dev/null 2>&1
"$P" -I umbral_as001.py "C:/Pruebas SAVIP/L2/fuentes/8e5a62b" > salidas/umbral_as001_8e5a62b.txt 2>&1
echo "[$(date -u +%T)] FIN"
