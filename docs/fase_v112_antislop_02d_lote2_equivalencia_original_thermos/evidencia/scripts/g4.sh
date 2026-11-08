#!/usr/bin/env bash
# G4 de 2D-2 sobre una copia limpia del último commit de código.
set -u
L="C:/Pruebas SAVIP/L2"; D="$L/g4/final"; CLON="C:/Users/Esteban/Desktop/SAVIP_V112_LOTE2D2_EQUIV"
P="C:/Pruebas SAVIP/Fase0/venv-test/Scripts/python.exe"
export QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8
git -C "$CLON" rev-parse HEAD > "$L/g4/final_head.txt"
rm -rf "$D" && bash "C:/Pruebas SAVIP/Fase1A/copiar.sh" "$CLON" "$D" >/dev/null
rm -rf "$D/docs/fase_v112_antislop_02d_lote2_equivalencia_original_thermos"
cd "$D" || exit 1
find . -type f -not -path "./resultados/*" | sort > "$L/g4/archivos_antes.txt"
"$P" -m pytest pruebas/prueba_horizonte_dinamico_ui_reportes.py -p no:cacheprovider -q -rA --junitxml="$L/g4/script_final_pytest.xml" > "$L/g4/script_final_pytest.txt" 2>&1; echo "codigo=$?" >> "$L/g4/script_final_pytest.txt"
"$P" pruebas/prueba_horizonte_dinamico_ui_reportes.py > "$L/g4/script_final_directo.txt" 2>&1; echo "codigo=$?" >> "$L/g4/script_final_directo.txt"
"$P" pruebas/ejemplo_uso.py > "$L/g4/ejemplo_uso_final.txt" 2>&1; echo "codigo=$?" >> "$L/g4/ejemplo_uso_final.txt"
"$P" pruebas/prueba_estadistica.py > "$L/g4/prueba_estadistica_final.txt" 2>&1; echo "codigo=$?" >> "$L/g4/prueba_estadistica_final.txt"
find . -type f -not -path "./resultados/*" | sort > "$L/g4/archivos_despues.txt"
"$P" scripts/pruebas_fase0.py --listar > "$L/g4/final_listar.txt" 2>&1
"$P" -m pytest --collect-only -q -p no:cacheprovider tests > "$L/g4/final_collect.txt" 2>&1
"$P" -m pip check > "$L/g4/pip_check.txt" 2>&1
"$P" -m compileall -q app_icociv aplicacion.py tests pruebas > "$L/g4/compileall.txt" 2>&1; echo "codigo=$?" >> "$L/g4/compileall.txt"
find . -name "__pycache__" -type d -prune -exec rm -rf {} +
"$P" -c "import pkgutil, importlib, app_icociv, aplicacion; m=[n for _,n,_ in pkgutil.walk_packages(app_icociv.__path__, 'app_icociv.')]; [importlib.import_module(x) for x in m]; from PySide6.QtWidgets import QApplication; a=QApplication([]); from app_icociv.interfaz.ventana_principal import VentanaPrincipal; VentanaPrincipal(); from app_icociv.proyeccion import servicio_proyeccion as sp; print('modulos', len(m), 'aplicacion OK, VentanaPrincipal OK, par ausente:', not hasattr(sp,'seleccionar_modelo_por_rmse_oos_global') and not hasattr(sp,'_errores_oos_por_par'))" > "$L/g4/imports.txt" 2>&1; echo "codigo=$?" >> "$L/g4/imports.txt"
"$P" "$CLON/docs/fase_v112_antislop_02a_as003/evidencia/huella_semantica.py" capturar "$L/g4/huella_final.json" > "$L/g4/huella.txt" 2>&1
"$P" "$CLON/docs/fase_v112_antislop_02a_as003/evidencia/huella_semantica.py" comparar "C:/Pruebas SAVIP/A28/huella_base.json" "$L/g4/huella_final.json" >> "$L/g4/huella.txt" 2>&1
sha256sum "C:/Pruebas SAVIP/A28/huella_base.json" "$L/g4/huella_final.json" >> "$L/g4/huella.txt"
S=$(date +%s); "$P" scripts/pruebas_fase0.py historicas --junitxml=resultados_h/historicas.xml -o junit_family=xunit2 > "$L/g4/historicas_final.txt" 2>&1; echo "codigo=$? duracion=$(( $(date +%s)-S ))s" >> "$L/g4/historicas_final.txt"
S=$(date +%s); "$P" scripts/pruebas_fase0.py esenciales --junitxml=resultados/esenciales.xml -o junit_family=xunit2 > "$L/g4/esenciales_final.txt" 2>&1; echo "codigo=$? duracion=$(( $(date +%s)-S ))s" >> "$L/g4/esenciales_final.txt"
echo FIN
