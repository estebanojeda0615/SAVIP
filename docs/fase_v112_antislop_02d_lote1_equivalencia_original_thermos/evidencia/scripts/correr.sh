#!/usr/bin/env bash
# Corre el oráculo dos veces sobre una raíz (determinismo). Uso: correr.sh <sha7>
P="C:/Pruebas SAVIP/Fase0/venv-test/Scripts/python.exe"
export QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8
cd "C:/Pruebas SAVIP/L2/oraculo"
for i in 1 2; do
  S=$(date +%s)
  "$P" -I oraculo.py "C:/Pruebas SAVIP/L2/fuentes/$1" "salidas/$1_r$i.json" > "salidas/$1_r$i.log" 2>&1
  echo "codigo=$? duracion=$(( $(date +%s)-S ))s" >> "salidas/$1_r$i.log"
done
