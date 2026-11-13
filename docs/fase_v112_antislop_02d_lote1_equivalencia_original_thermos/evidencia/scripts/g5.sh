#!/usr/bin/env bash
# Lote 2D-1, G4.3/G5/G6 sobre una copia limpia del último commit de código (sin .git) y la base 8e5a62b.
set -u
A="C:/Pruebas SAVIP/L1D1"; B="$A/base"; G="$A/g5"; L2="C:/Pruebas SAVIP/L2/oraculo"; CLON="C:/Users/Esteban/Desktop/SAVIP_V112_LOTE2D1"
P="C:/Pruebas SAVIP/Fase0/venv-test/Scripts/python.exe"
SHA=$(git -C "$CLON" rev-parse --short=7 HEAD); D="$A/final_$SHA"
export QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8
echo "$(git -C "$CLON" rev-parse HEAD)" > "$G/final_head.txt"
rm -rf "$D" && mkdir -p "$D" && git -C "$CLON" archive HEAD | tar -x -C "$D"
EVID="$D/docs/fase_v112_antislop_02a_as003/evidencia"
cd "$D" || exit 1
find . -type f | sort > "$G/final_archivos_antes.txt"
echo "[$(date -u +%T)] estatico"
"$P" - > "$G/ast_ausencia_y_compartidos.txt" 2>&1 <<'PY'
import ast, hashlib
src=open("app_icociv/proyeccion/servicio_proyeccion.py",encoding="utf-8").read(); t=ast.parse(src)
tops={n.name:n for n in t.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
SEIS=["determinar_horizonte_maximo_estadistico","_serializar_evaluaciones_horizonte","_item_horizonte_global","_mayor_horizonte_con","_ultimo_horizonte_por_clasificacion","_evidencia_horizonte"]
print("definiciones de nivel superior:",len(tops)); print("seis ausentes:",all(n not in tops for n in SEIS))
for n in ["_tipo_uso_horizonte","_mayor_horizonte_permitido","_evaluar_horizontes_proyeccion","_clasificar_evidencia_horizonte","_aplicar_salvaguarda_benchmarks","_resultado_sin_proyeccion","_estructurar_resultado_horizontes"]:
    f=tops[n]; print("presente",n,"L%d-%d"%(f.lineno,f.end_lineno),hashlib.sha256(ast.dump(f).encode()).hexdigest()[:16])
nombres={x.id for x in ast.walk(t) if isinstance(x,ast.Name)}|{x.attr for x in ast.walk(t) if isinstance(x,ast.Attribute)}
print("referencias residuales a las seis (Name/Attribute):",sorted(nombres & set(SEIS)))
PY
"$P" "$EVID/grafo_as003.py" "$D" "$G/grafo_final.json" > "$G/grafo_final.txt" 2>&1
"$P" scripts/pruebas_fase0.py --listar > "$G/final_listar.txt" 2>&1
"$P" -m pytest --collect-only -q -p no:cacheprovider tests > "$G/final_collect.txt" 2>&1; echo "codigo=$?" >> "$G/final_collect.txt"
"$P" -m compileall -q app_icociv aplicacion.py tests scripts pruebas > "$G/final_compileall.txt" 2>&1; echo "codigo=$?" >> "$G/final_compileall.txt"
find . -name "__pycache__" -type d -prune -exec rm -rf {} +
"$P" -c "import pkgutil, importlib, app_icociv, aplicacion; m=[n for _,n,_ in pkgutil.walk_packages(app_icociv.__path__, 'app_icociv.')]; [importlib.import_module(x) for x in m]; from PySide6.QtWidgets import QApplication; a=QApplication([]); from app_icociv.interfaz.ventana_principal import VentanaPrincipal; VentanaPrincipal(); from app_icociv.proyeccion import servicio_proyeccion as sp; from app_icociv.estadistica import modelos_interpretables as mi; print('modulos', len(m), 'aplicacion OK, VentanaPrincipal OK; 2D-1 ausente:', not any(hasattr(sp,n) for n in ('determinar_horizonte_maximo_estadistico','_serializar_evaluaciones_horizonte','_item_horizonte_global','_mayor_horizonte_con','_ultimo_horizonte_por_clasificacion','_evidencia_horizonte')), '; compartidos presentes:', hasattr(sp,'_tipo_uso_horizonte') and hasattr(sp,'_mayor_horizonte_permitido'))" > "$G/final_imports.txt" 2>&1; echo "codigo=$?" >> "$G/final_imports.txt"
"$P" -m pip check > "$G/pip_check.txt" 2>&1; echo "codigo=$?" >> "$G/pip_check.txt"
"$P" "$EVID/huella_semantica.py" capturar "$G/huella_final.json" > "$G/huella_final.txt" 2>&1
"$P" "$EVID/huella_semantica.py" comparar "$A/g0/huella_base.json" "$G/huella_final.json" >> "$G/huella_final.txt" 2>&1
sha256sum "$A/g0/huella_base.json" "$G/huella_final.json" >> "$G/huella_final.txt"
echo "[$(date -u +%T)] script e historicas afectadas"
"$P" -m pytest pruebas/prueba_horizonte_dinamico_ui_reportes.py -p no:cacheprovider -q -rA --junitxml="$G/script_final_pytest.xml" > "$G/script_final_pytest.txt" 2>&1; echo "codigo=$?" >> "$G/script_final_pytest.txt"
"$P" pruebas/prueba_horizonte_dinamico_ui_reportes.py > "$G/script_final_directo.txt" 2>&1; echo "codigo=$?" >> "$G/script_final_directo.txt"
"$P" -m pytest -p no:cacheprovider -q -rfE tests/test_cierre_metodologico.py --junitxml="$G/cierre_final.xml" > "$G/cierre_final.txt" 2>&1; echo "codigo=$?" >> "$G/cierre_final.txt"
find . -name "__pycache__" -type d -prune -exec rm -rf {} +
echo "[$(date -u +%T)] sonda AS-004"
cd "$A"
SONDA_FUENTE_CLAVES="$B" "$P" "$G/herr/sonda_claves_as004.py" "$B" "$G/sonda_base.json" > "$G/sonda_base.txt" 2>&1
SONDA_FUENTE_CLAVES="$B" "$P" "$G/herr/sonda_claves_as004.py" "$D" "$G/sonda_final.json" > "$G/sonda_final.txt" 2>&1
find "$B" "$D" -name "__pycache__" -type d -prune -exec rm -rf {} +
echo "[$(date -u +%T)] esenciales final"
cd "$D"
S=$(date +%s); "$P" scripts/pruebas_fase0.py esenciales --junitxml=resultados/esenciales.xml -o junit_family=xunit2 > "$G/final_esenciales.txt" 2>&1; echo "codigo=$? duracion=$(( $(date +%s)-S ))s" >> "$G/final_esenciales.txt"
find . -name "__pycache__" -type d -prune -exec rm -rf {} +
find . -type f -not -path "./resultados/*" | sort > "$G/final_archivos_despues.txt"
echo "[$(date -u +%T)] oraculo"
F="C:/Pruebas SAVIP/L2/fuentes/$SHA"
rm -rf "$F" && mkdir -p "$F" && git -C "$CLON" archive HEAD | tar -x -C "$F" && echo "$(git -C "$CLON" rev-parse HEAD) $(git -C "$CLON" rev-parse HEAD:app_icociv)" > "$F/.fuente_git.txt"
bash "$L2/correr.sh" "$SHA"
cd "$L2"
"$P" -I golden_exacto.py "$F" "$F/tests/fixtures/fase0/golden" "salidas/golden_exacto_$SHA.txt" > /dev/null 2>&1
"$P" -I umbral_as001.py "$F" > "salidas/umbral_as001_$SHA.txt" 2>&1
echo "[$(date -u +%T)] historicas base"
cd "$B"
S=$(date +%s); "$P" scripts/pruebas_fase0.py historicas --junitxml=resultados_hist/historicas.xml -o junit_family=xunit2 > "$G/base_historicas.txt" 2>&1; echo "codigo=$? duracion=$(( $(date +%s)-S ))s" >> "$G/base_historicas.txt"
find . -name "__pycache__" -type d -prune -exec rm -rf {} +
echo "[$(date -u +%T)] historicas final"
cd "$D"
S=$(date +%s); "$P" scripts/pruebas_fase0.py historicas --junitxml=resultados_hist/historicas.xml -o junit_family=xunit2 > "$G/final_historicas.txt" 2>&1; echo "codigo=$? duracion=$(( $(date +%s)-S ))s" >> "$G/final_historicas.txt"
find . -name "__pycache__" -type d -prune -exec rm -rf {} +
echo "[$(date -u +%T)] FIN"
