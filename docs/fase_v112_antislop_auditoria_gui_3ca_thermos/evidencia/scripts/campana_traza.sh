#!/usr/bin/env bash
# Campaña G1/G2 con el plugin pasivo de trazas. Uso: campana_traza.sh <raiz> <etiqueta> <N> <objetivo> [procesos_carga]
RAIZ="$1"; ET="$2"; N="$3"; OBJ="$4"; CARGA="${5:-0}"
AQUI="$(cd "$(dirname "$0")" && pwd)"
# Intérprete y carpeta de salida configurables; por defecto, los de la ejecución original de la auditoría.
P="${PYTHON_3CA:-C:/Pruebas SAVIP/Fase0/venv-test/Scripts/python.exe}"
export QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8
D="${SALIDA_3CA:-C:/Pruebas SAVIP/3CA/campanas}/$ET"; mkdir -p "$D"; M="$D/manifiesto.tsv"
echo -e "intento\tinicio_utc\tduracion_s\tcodigo\tresultado\tcarga_procesos" > "$M"
cd "$RAIZ"
for i in $(seq -w 1 "$N"); do
  if [ "$CARGA" -gt 0 ]; then "$P" "${SONDA_3CA:-$AQUI/sonda}/carga_cpu.py" "$CARGA" 8 & CP=$!; sleep 1; fi
  I=$(date -u +%Y-%m-%dT%H:%M:%SZ); S=$(date +%s.%N)
  PYTHONPATH="${SONDA_3CA:-$AQUI/sonda}" TRAZA_3CA="$D/traza_$i.jsonl" "$P" -m pytest -p no:cacheprovider -p plugin_traza_3ca -q -rA "$OBJ" --junitxml="$D/junit_$i.xml" > "$D/salida_$i.txt" 2>&1; C=$?
  E=$("$P" -c "print(round($(date +%s.%N)-$S,2))")
  R=$([ $C -eq 0 ] && echo PASS || echo FAIL)
  echo -e "$i\t$I\t$E\t$C\t$R\t$CARGA" >> "$M"
  if [ "$CARGA" -gt 0 ]; then wait $CP 2>/dev/null; fi
done
echo "FIN $ET: $(grep -c PASS "$M") PASS, $(grep -c FAIL "$M") FAIL de $N"
