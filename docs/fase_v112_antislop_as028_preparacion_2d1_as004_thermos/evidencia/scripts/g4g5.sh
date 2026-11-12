#!/usr/bin/env bash
# AS-028 (2D-1): G4 (2D-1 oculto en memoria) y G5 (regresión y equivalencia) sobre copias limpias.
# base = 102f194, final = 7993060 (último commit de código). Producción idéntica en ambas.
set -u
A="C:/Pruebas SAVIP/A28D1"; D="$A/final"; B="$A/base"; G4="$A/g4"; G5="$A/g5"
P="C:/Pruebas SAVIP/Fase0/venv-test/Scripts/python.exe"
EVID="$D/docs/fase_v112_antislop_02a_as003/evidencia"
L2="C:/Pruebas SAVIP/L2/oraculo"
export QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8
cd "$D" || exit 1
find . -type f -not -path "./resultados/*" | sort > "$G5/final_archivos_antes.txt"
echo "[$(date -u +%T)] script final"
S=$(date +%s); "$P" -m pytest pruebas/prueba_horizonte_dinamico_ui_reportes.py -p no:cacheprovider -q -rA --junitxml="$G5/script_final_pytest.xml" > "$G5/script_final_pytest.txt" 2>&1; echo "codigo=$? duracion=$(( $(date +%s)-S ))s" >> "$G5/script_final_pytest.txt"
S=$(date +%s); "$P" pruebas/prueba_horizonte_dinamico_ui_reportes.py > "$G5/script_final_directo.txt" 2>&1; echo "codigo=$? duracion=$(( $(date +%s)-S ))s" >> "$G5/script_final_directo.txt"
echo "[$(date -u +%T)] G4"
export PYTHONPATH="$G4"
"$P" -m pytest -p ocultar_2d1 -p no:cacheprovider --collect-only -q pruebas/prueba_horizonte_dinamico_ui_reportes.py > "$G4/script_final_collect_oculto.txt" 2>&1; echo "codigo=$?" >> "$G4/script_final_collect_oculto.txt"
"$P" -m pytest -p ocultar_2d1 -p no:cacheprovider -q -rA pruebas/prueba_horizonte_dinamico_ui_reportes.py --junitxml="$G4/script_final_oculto.xml" > "$G4/script_final_oculto.txt" 2>&1; echo "codigo=$?" >> "$G4/script_final_oculto.txt"
"$P" -m pytest -p ocultar_2d1 -p no:cacheprovider --collect-only -q tests > "$G4/collect_tests_oculto.txt" 2>&1; echo "codigo=$?" >> "$G4/collect_tests_oculto.txt"
"$P" -m pytest -p ocultar_2d1 -p no:cacheprovider -q -rfE tests/test_cierre_metodologico.py tests/test_regresiones_auditoria_independiente_bghc.py > "$G4/historicas_afectadas_oculto.txt" 2>&1; echo "codigo=$?" >> "$G4/historicas_afectadas_oculto.txt"
S=$(date +%s); "$P" scripts/pruebas_fase0.py esenciales -p ocultar_2d1 --junitxml=resultados_oculto/esenciales.xml -o junit_family=xunit2 > "$G4/esenciales_oculto.txt" 2>&1; echo "codigo=$? duracion=$(( $(date +%s)-S ))s" >> "$G4/esenciales_oculto.txt"
unset PYTHONPATH
# Sensibilidad: el script BASE con 2D-1 oculto debe fallar exactamente en las tres pruebas retiradas.
( cd "$B" && PYTHONPATH="$G4" "$P" -m pytest -p ocultar_2d1 -p no:cacheprovider -q -rA pruebas/prueba_horizonte_dinamico_ui_reportes.py --junitxml="$G4/script_base_oculto.xml" > "$G4/script_base_oculto.txt" 2>&1; echo "codigo=$?" >> "$G4/script_base_oculto.txt" )
echo "[$(date -u +%T)] G5 estatico"
"$P" scripts/pruebas_fase0.py --listar > "$G5/final_listar.txt" 2>&1
"$P" -m pytest --collect-only -q -p no:cacheprovider tests > "$G5/final_collect.txt" 2>&1; echo "codigo=$?" >> "$G5/final_collect.txt"
"$P" -m compileall -q pruebas app_icociv aplicacion.py tests scripts > "$G5/final_compileall.txt" 2>&1; echo "codigo=$?" >> "$G5/final_compileall.txt"
find . -name "__pycache__" -type d -prune -exec rm -rf {} +
"$P" -c "import pkgutil, importlib, app_icociv, aplicacion; m=[n for _,n,_ in pkgutil.walk_packages(app_icociv.__path__, 'app_icociv.')]; [importlib.import_module(x) for x in m]; from PySide6.QtWidgets import QApplication; a=QApplication([]); from app_icociv.interfaz.ventana_principal import VentanaPrincipal; VentanaPrincipal(); from app_icociv.proyeccion import servicio_proyeccion as sp; print('modulos', len(m), 'aplicacion OK, VentanaPrincipal OK, 2D-1 presente:', all(hasattr(sp,n) for n in ('determinar_horizonte_maximo_estadistico','_serializar_evaluaciones_horizonte','_item_horizonte_global','_mayor_horizonte_con','_ultimo_horizonte_por_clasificacion','_evidencia_horizonte')))" > "$G5/final_imports.txt" 2>&1; echo "codigo=$?" >> "$G5/final_imports.txt"
"$P" -m pip check > "$G5/pip_check.txt" 2>&1; echo "codigo=$?" >> "$G5/pip_check.txt"
"$P" "$EVID/huella_semantica.py" capturar "$G5/huella_final.json" > "$G5/huella_final.txt" 2>&1
"$P" "$EVID/huella_semantica.py" comparar "$A/g0/huella_base.json" "$G5/huella_final.json" >> "$G5/huella_final.txt" 2>&1
sha256sum "$A/g0/huella_base.json" "$G5/huella_final.json" >> "$G5/huella_final.txt"
"$P" "$A/g2/sonda_claves_as004.py" "$D" "$G5/sonda_final.json" > "$G5/sonda_final.txt" 2>&1
echo "[$(date -u +%T)] esenciales final"
S=$(date +%s); "$P" scripts/pruebas_fase0.py esenciales --junitxml=resultados/esenciales.xml -o junit_family=xunit2 > "$G5/final_esenciales.txt" 2>&1; echo "codigo=$? duracion=$(( $(date +%s)-S ))s" >> "$G5/final_esenciales.txt"
find . -name "__pycache__" -type d -prune -exec rm -rf {} +
find . -type f -not -path "./resultados/*" -not -path "./resultados_oculto/*" | sort > "$G5/final_archivos_despues.txt"
echo "[$(date -u +%T)] oraculo"
# Oráculo de 66 escenarios: misma versión del arnés que 2D-2, sobre fuentes git archive.
for sha in 102f194 7993060; do
  F="C:/Pruebas SAVIP/L2/fuentes/$sha"
  if [ ! -d "$F" ]; then mkdir -p "$F" && git -C "C:/Users/Esteban/Desktop/SAVIP_V112_AS028_2D1" archive "$sha" | tar -x -C "$F" && echo "$(git -C "C:/Users/Esteban/Desktop/SAVIP_V112_AS028_2D1" rev-parse $sha) $(git -C "C:/Users/Esteban/Desktop/SAVIP_V112_AS028_2D1" rev-parse $sha:app_icociv)" > "$F/.fuente_git.txt"; fi
done
bash "$L2/correr.sh" 7993060
S=$(date +%s); ( cd "$L2" && "$P" -I oraculo.py "C:/Pruebas SAVIP/L2/fuentes/102f194" "salidas/102f194_r1.json" > "salidas/102f194_r1.log" 2>&1; echo "codigo=$? duracion=$(( $(date +%s)-S ))s" >> "salidas/102f194_r1.log" )
S=$(date +%s); ( cd "$L2" && "$P" -I oraculo.py "C:/Pruebas SAVIP/L2/fuentes/6672529" "salidas/6672529_r3.json" > "salidas/6672529_r3.log" 2>&1; echo "codigo=$? duracion=$(( $(date +%s)-S ))s" >> "salidas/6672529_r3.log" )
echo "[$(date -u +%T)] FIN"
