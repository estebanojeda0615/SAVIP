#!/usr/bin/env bash
# Campaña G1: N procesos frescos de pytest, sin el runner que reintenta. Uso: campana.sh <raiz> <etiqueta> <N> <objetivo pytest>
RAIZ="$1"; ET="$2"; N="$3"; OBJ="$4"
AQUI="$(cd "$(dirname "$0")" && pwd)"
# Intérprete y carpeta de salida configurables; por defecto, los de la ejecución original de la auditoría.
P="${PYTHON_3CA:-C:/Pruebas SAVIP/Fase0/venv-test/Scripts/python.exe}"
export QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8
D="${SALIDA_3CA:-C:/Pruebas SAVIP/3CA/campanas}/$ET"; mkdir -p "$D"; M="$D/manifiesto.tsv"
echo -e "intento\tinicio_utc\tduracion_s\tcodigo\tresultado" > "$M"
cd "$RAIZ"
for i in $(seq -w 1 "$N"); do
  I=$(date -u +%Y-%m-%dT%H:%M:%SZ); S=$(date +%s.%N)
  "$P" -m pytest -p no:cacheprovider -q -rA "$OBJ" --junitxml="$D/junit_$i.xml" > "$D/salida_$i.txt" 2>&1; C=$?
  E=$("$P" -c "print(round($(date +%s.%N)-$S,2))")
  R=$([ $C -eq 0 ] && echo PASS || echo FAIL)
  echo -e "$i\t$I\t$E\t$C\t$R" >> "$M"
done
echo "FIN $ET: $(grep -c PASS "$M") PASS, $(grep -c FAIL "$M") FAIL de $N"
