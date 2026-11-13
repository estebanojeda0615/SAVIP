"""Lote 2D-1 (G4.2, mismo commit que el retiro de producción): mueve determinar_horizonte_maximo_estadistico de la
tupla `retirados` (espiada) a `eliminados` (se exige su ausencia) en la guarda de la Fase 1A. Conserva el espía
de _evaluar_horizontes_proyeccion (2D-3). Uso: python adaptar_fase1a.py <tests/test_fase1a_selector_rectangular.py>"""
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()
pares = [
    ('''    # Fase 2B (AS-003, opción B) y lote 2D-2: retirados del módulo; se exige su AUSENCIA.
    eliminados = ("_rmse_global_estable", "_modelo_consistente_desde_comparativo", "_modelo_trayectoria_consistente",
                  "seleccionar_modelo_por_rmse_oos_global", "_errores_oos_por_par")''',
     '''    # Fase 2B (AS-003, opción B), lote 2D-2 y lote 2D-1: retirados del módulo; se exige su AUSENCIA.
    eliminados = ("_rmse_global_estable", "_modelo_consistente_desde_comparativo", "_modelo_trayectoria_consistente",
                  "seleccionar_modelo_por_rmse_oos_global", "_errores_oos_por_par",
                  "determinar_horizonte_maximo_estadistico")'''),
    ('''    retirados = ("determinar_horizonte_maximo_estadistico", "_evaluar_horizontes_proyeccion")''',
     '''    retirados = ("_evaluar_horizontes_proyeccion",)'''),
]
for a, b in pares:
    assert s.count(a) == 1, a
    s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("guarda Fase 1A adaptada")
