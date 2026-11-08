#!/usr/bin/env bash
# G1/base de 2D-2 sobre una copia limpia de la rama en 02426ef (código = 5478958).
set -u
L="C:/Pruebas SAVIP/L2"; D="$L/g1/base"; CLON="C:/Users/Esteban/Desktop/SAVIP_V112_LOTE2D2_EQUIV"
P="C:/Pruebas SAVIP/Fase0/venv-test/Scripts/python.exe"
export QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8
git -C "$CLON" rev-parse HEAD > "$L/g1/base_head.txt"
rm -rf "$D" && bash "C:/Pruebas SAVIP/Fase1A/copiar.sh" "$CLON" "$D" >/dev/null
cd "$D" || exit 1
# Espías en la ruta productiva
"$P" -I "$L/g1/espias_par.py" "$D" > "$L/g1/espias_base.txt" 2>&1; echo "codigo=$?" >> "$L/g1/espias_base.txt"
# Grafo AST
"$P" docs/fase_v112_antislop_02a_as003/evidencia/grafo_as003.py . "$L/g1/grafo_base.json" > "$L/g1/grafo_base.txt" 2>&1; echo "codigo=$?" >> "$L/g1/grafo_base.txt"
# Perfil histórico base
S=$(date +%s); "$P" scripts/pruebas_fase0.py historicas --junitxml=resultados/historicas.xml -o junit_family=xunit2 > "$L/g1/historicas_base.txt" 2>&1; echo "codigo=$? duracion=$(( $(date +%s)-S ))s" >> "$L/g1/historicas_base.txt"
mv resultados "$L/g1/resultados_historicas_base"
# Simulación: par oculto en memoria
export PYTHONPATH="$L/../A28/g3"
"$P" -m pytest -p ocultar_par_2d2 -p no:cacheprovider --collect-only -q tests > "$L/g1/oculto_collect_tests.txt" 2>&1; echo "codigo=$?" >> "$L/g1/oculto_collect_tests.txt"
"$P" -m pytest -p ocultar_par_2d2 -p no:cacheprovider -q -rf --continue-on-collection-errors tests/test_fase1a_selector_rectangular.py tests/test_origen_inicial_backtesting.py tests/test_nmin_adversarial.py tests/test_remediacion_r2_h1_h2_h3_h7.py tests/test_fase2c_contratos_vigentes.py > "$L/g1/oculto_esenciales_afectados.txt" 2>&1; echo "codigo=$?" >> "$L/g1/oculto_esenciales_afectados.txt"
"$P" -m pytest -p ocultar_par_2d2 -p no:cacheprovider -q -rf --continue-on-collection-errors tests/test_p0d_rmse_orden_exacto.py tests/test_rmse_global_estable.py tests/test_seleccion_rmse_global.py tests/test_cierre_metodologico.py tests/test_horizonte_evidencia_reducida.py > "$L/g1/oculto_historicos_afectados.txt" 2>&1; echo "codigo=$?" >> "$L/g1/oculto_historicos_afectados.txt"
"$P" -m pytest -p ocultar_par_2d2 -p no:cacheprovider -q pruebas/prueba_horizonte_dinamico_ui_reportes.py > "$L/g1/oculto_script_horizonte.txt" 2>&1; echo "codigo=$?" >> "$L/g1/oculto_script_horizonte.txt"
unset PYTHONPATH
"$P" pruebas/ejemplo_uso.py > "$L/g1/ejemplo_uso_base.txt" 2>&1; echo "codigo=$?" >> "$L/g1/ejemplo_uso_base.txt"
"$P" pruebas/prueba_estadistica.py > "$L/g1/prueba_estadistica_base.txt" 2>&1; echo "codigo=$?" >> "$L/g1/prueba_estadistica_base.txt"
echo FIN
