# 02 · G1: consumidores del par 2D-2 y simulación del retiro

G1 se ejecutó después de que el propietario aceptara AS-001 como excepción preexistente (decisión del 05-11-2026, 22:40 UTC). Se trabajó sobre una copia limpia de la rama en `02426ef`, cuyo código es idéntico al de `5478958`.

## 1. Grafo AST (`docs/fase_v112_antislop_02a_as003/evidencia/grafo_as003.py`)

| Símbolo | Líneas | `produccion` | `scripts` | `referenciado_por` | Pruebas directas | Citas documentales |
|---|---|---|---|---|---|---|
| `seleccionar_modelo_por_rmse_oos_global` | 3142-3220 (79) | **False** | False | ninguno | cierre_metodologico, fase1a, fase2c, horizonte_evidencia_reducida, origen_inicial_backtesting, p0d_rmse_orden_exacto | `app_icociv.estadistica.criterios` (C-SEL-001) |
| `_errores_oos_por_par` | 3112-3139 (28) | **False** | False | solo el selector heredado | fase2c, horizonte_evidencia_reducida, nmin_adversarial, p0d_rmse_orden_exacto, seleccion_rmse_global | — |
| `_seleccionar_modelo_rectangular` (referencia) | 912-970 | True | True | `_ejecutar_proyeccion_base` | — | — |

En total suman **107 líneas de definición**, la misma cifra que el inventario de la Fase 2C. El grafo cuenta 806 definiciones, de las que 719 son alcanzables desde producción (`evidencia/grafo_par.txt`).

## 2. Búsqueda estática y usos dinámicos

**Búsqueda textual** en `*.py`, `*.yml`, `*.spec` y `*.txt` de todo el repositorio salvo `docs/`, más el análisis AST por prueba de `evidencia/usos_por_test.txt`:
- **Producción:** solo las dos definiciones y la cadena `ubicacion` de C-SEL-001.
- **Sin usos dinámicos:** no hay `getattr`, `importlib`, `globals`, callbacks, strings de configuración ni referencias en `packaging/`.
- **Scripts:** en `scripts/` y `pruebas/` no queda ninguna referencia ejecutable. En el script histórico solo está la lápida de AS-028, que no nombra el símbolo.

**Consumidores en pruebas** (AST; «USA» incluye el uso indirecto a través de auxiliares del mismo archivo):

| Archivo | Perfil | Uso |
|---|---|---|
| `test_origen_inicial_backtesting.py` | esencial | 1 de 17: `test_p0d_la_regla_de_seleccion_no_cambia`. **Lo invocan además** `test_nmin_adversarial::test_p0a_p0b_p0d_intactos` (esencial) y `test_integracion_fhg::test_p0abd_intactos` (histórica), que el AST por archivo no detecta y la búsqueda textual sí |
| `test_nmin_adversarial.py` | esencial | 1 de 10: `test_muestra_comun_intacta_desde_el_primer_origen` |
| `test_remediacion_r2_h1_h2_h3_h7.py` | esencial | Importación de módulo **sin uso** (L35) |
| `test_fase1a_selector_rectangular.py` | esencial | Solo como cadena en la tupla espiada |
| `test_fase2c_contratos_vigentes.py` | esencial | Solo como texto en `HEREDADAS`, una lista de exclusión que no exige existencia |
| `test_p0d_rmse_orden_exacto.py` | histórica | 11 de 13, e importación de módulo |
| `test_rmse_global_estable.py` | histórica | 4 de 4, e importación de módulo |
| `test_seleccion_rmse_global.py` | histórica | 14 de 15, e importación de módulo |
| `test_cierre_metodologico.py` | histórica | 2 de 23 |
| `test_horizonte_evidencia_reducida.py` | histórica | 1 de 9 |

## 3. Espías en la ruta productiva (`evidencia/espias_base.txt`)

Se usaron `patch.object(..., wraps=...)` sobre los dos símbolos y sobre el selector vigente. Son espías que observan sin sustituir nada. Escenarios:
- los 35 casos de motor del oráculo (5 series × H 1, 6, 11, 12, 17, 23 y 24);
- los 6 fixtures `horizonte_dinamico`;
- el recorrido GUI real de Fase 0: dos análisis, reconsultas, guardar y reabrir la sesión, Excel, PDF y DOCX de la sesión, factor legado, e informe de proyección CSV, DOCX y PDF.

| Símbolo | Llamadas |
|---|---|
| `seleccionar_modelo_por_rmse_oos_global` | **0** |
| `_errores_oos_por_par` | **0** |
| `_seleccionar_modelo_rectangular` (vigente) | 44 |

## 4. Simulación del retiro con el par oculto en memoria

Se usó el plugin `evidencia/g3_ocultar_par_2d2.py` de AS-028, que borra los dos atributos del módulo en el proceso, sin editar producción, sobre una copia aislada.

| Ejecución | Resultado con el par oculto |
|---|---|
| `pytest --collect-only tests` | **1 025 recogidos y 7 errores**: los 3 históricos más 4 nuevos (`test_p0d_rmse_orden_exacto`, `test_remediacion_r2_h1_h2_h3_h7` (esencial), `test_rmse_global_estable` y `test_seleccion_rmse_global`) |
| Esenciales afectados (5 archivos) | 4 FAIL y 1 error de recolección (`test_remediacion`, 9 ids). Los FAIL: `test_fase1a…::test_la_ruta_productiva…` (`patch.object` de un atributo inexistente), `test_origen…::test_p0d_la_regla_de_seleccion_no_cambia`, `test_nmin…::test_muestra_comun_intacta_desde_el_primer_origen` y `test_nmin…::test_p0a_p0b_p0d_intactos` |
| Históricas afectadas (5 archivos) | 3 errores de recolección (los 3 archivos con importación de módulo). En `test_cierre_metodologico`, 2 FAIL nuevos (las 2 pruebas del selector heredado), más `test_no_hay_modelo_por_horizonte`, preexistente. En `test_horizonte_evidencia_reducida`, 1 FAIL nuevo (`test_modelo_agregado…`) más 3 preexistentes |
| Script `prueba_horizonte_dinamico_ui_reportes.py` | **29 recogidos: 21 PASS y 8 FAIL**, los mismos 8 históricos. Ningún error de importación |

Cada efecto tiene su tratamiento en G2 (03). Ningún efecto alcanza a la producción, a los scripts conservados ni a la ruta vigente.

## 5. Dictamen de G1

**GO.**
- Ningún consumidor productivo, plugin público ni contrato de resultados depende del par.
- Todos los efectos del retiro se limitan a pruebas, que se tratan en G2 (03).
- No hay imports ni constantes que queden huérfanos en producción: `Fraction`, `Decimal`, `localcontext`, `math`, `pd` y `_numero_finito` siguen en uso (AST, `evidencia/imports_huerfanos.txt`).
