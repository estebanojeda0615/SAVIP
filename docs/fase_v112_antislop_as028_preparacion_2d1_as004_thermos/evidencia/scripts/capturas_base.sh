#!/usr/bin/env bash
# G0: capturas de la base 102f194 (copia limpia, fuera del clon). Se ejecuta tras el perfil esencial.
set -u
A="C:/Pruebas SAVIP/A28D1"; D="$A/base"; G="$A/g0"
P="C:/Pruebas SAVIP/Fase0/venv-test/Scripts/python.exe"
EVID="$D/docs/fase_v112_antislop_02a_as003/evidencia"
export QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8
cd "$D" || exit 1
find . -type f -not -path "./resultados/*" | sort > "$G/base_archivos_antes.txt"
S=$(date +%s); "$P" -m pytest pruebas/prueba_horizonte_dinamico_ui_reportes.py -p no:cacheprovider -q -rA --junitxml="$G/script_base_pytest.xml" > "$G/script_base_pytest.txt" 2>&1; echo "codigo=$? duracion=$(( $(date +%s)-S ))s" >> "$G/script_base_pytest.txt"
S=$(date +%s); "$P" pruebas/prueba_horizonte_dinamico_ui_reportes.py > "$G/script_base_directo.txt" 2>&1; echo "codigo=$? duracion=$(( $(date +%s)-S ))s" >> "$G/script_base_directo.txt"
"$P" -m pytest --collect-only -q -p no:cacheprovider tests > "$G/base_collect.txt" 2>&1; echo "codigo=$?" >> "$G/base_collect.txt"
"$P" "$EVID/huella_semantica.py" capturar "$G/huella_base.json" > "$G/huella_base.txt" 2>&1
"$P" "$EVID/huella_semantica.py" comparar "C:/Pruebas SAVIP/A28/huella_base.json" "$G/huella_base.json" >> "$G/huella_base.txt" 2>&1
sha256sum "C:/Pruebas SAVIP/A28/huella_base.json" "$G/huella_base.json" >> "$G/huella_base.txt"
find . -name "__pycache__" -type d -prune -exec rm -rf {} +
find . -type f -not -path "./resultados/*" | sort > "$G/base_archivos_despues.txt"
echo FIN
