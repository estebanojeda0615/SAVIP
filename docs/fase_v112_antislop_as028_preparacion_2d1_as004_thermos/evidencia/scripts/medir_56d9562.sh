#!/usr/bin/env bash
# Mediciones del script histórico sobre el último commit de código (56d9562), copia limpia sin .git.
set -u
A="C:/Pruebas SAVIP/A28D1"; P="C:/Pruebas SAVIP/Fase0/venv-test/Scripts/python.exe"
export QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8
bash "C:/Pruebas SAVIP/Fase1A/copiar.sh" "C:/Users/Esteban/Desktop/SAVIP_V112_AS028_2D1" "$A/final_56d9562"
rm -rf "$A/final_56d9562/docs/fase_v112_antislop_as028_preparacion_2d1_as004_thermos"
cd "$A/final_56d9562" || exit 1
"$P" -m pytest pruebas/prueba_horizonte_dinamico_ui_reportes.py -p no:cacheprovider -q -rA --junitxml=../g5/script_56d9562_pytest.xml > ../g5/script_56d9562_pytest.txt 2>&1; echo "codigo=$?" >> ../g5/script_56d9562_pytest.txt
"$P" pruebas/prueba_horizonte_dinamico_ui_reportes.py > ../g5/script_56d9562_directo.txt 2>&1; echo "codigo=$?" >> ../g5/script_56d9562_directo.txt
PYTHONPATH=../g4 "$P" -m pytest -p ocultar_2d1 -p no:cacheprovider -q pruebas/prueba_horizonte_dinamico_ui_reportes.py --junitxml=../g4/script_56d9562_oculto.xml > ../g4/script_56d9562_oculto.txt 2>&1
# Sondas AS-004 (base, final y final con 2D-1 sustituido por stubs que fallan si se llaman)
cd "$A"
"$P" g2/sonda_claves_as004.py base g2/sonda_base.json > g2/sonda_base.txt 2>&1
"$P" g2/sonda_claves_as004.py final_56d9562 g5/sonda_final.json > g5/sonda_final.txt 2>&1
"$P" g4/sonda_oculto.py final_56d9562 g2/sonda_claves_as004.py g2/sonda_base.json g4/sonda_oculto.json > g4/sonda_oculto.txt 2>&1
"$P" g2/mapa_claves_as004.py base g0/grafo.json g2/apariciones.csv
"$P" g2/escribir_03_csv.py base g2/apariciones.csv g2/sonda_base.json g2/03.csv g2/03_descartes.csv
