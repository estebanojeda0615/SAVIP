# 06 · GO/NO-GO para el lote 2D-2

## Dictamen: **GO para SOLICITAR** el prompt de retiro 2D-2

Este dictamen **no autoriza** borrar `seleccionar_modelo_por_rmse_oos_global` ni `_errores_oos_por_par`. Solo afirma que el script histórico ya no bloquea ese retiro y que la propiedad que protegía sigue cubierta por pruebas esenciales concretas. El propietario decide si abre 2D-2 en una fase separada.

## 1. Por qué GO para solicitar

| Condición (prompt §8) | Evidencia |
|---|---|
| La referencia real al selector heredado en el script desapareció | En la base estaba en L292 y L300 (importación y llamada dentro de `test_el_modelo_entregado_es_el_de_minimo_error_oos_global`). En `5acb09f` el `grep` de los dos nombres en el script da **0**. La lápida no los nombra |
| No hay referencias nuevas al par | `git diff 56c75a6 5acb09f` no añade ninguna línea con esos nombres. Solo los retira (03 §1) |
| El script preparado se importa y se recoge con el par oculto | G3, con el plugin `evidencia/g3_ocultar_par_2d2.py` (borra los dos atributos del módulo en memoria). `--collect-only` del script: **29 tests recogidos, código 0**. `pytest` del script: **21 PASS / 8 FAIL**, los mismos 8 históricos. Ningún `ImportError` ni `AttributeError` |
| El sondeo es sensible | El mismo sondeo sobre el script **base** hace fallar `test_el_modelo_entregado_es_el_de_minimo_error_oos_global` con `ImportError` (`evidencia/g3_base_selector_oculto.txt`). El plugin detecta la dependencia que AS-028 retira |
| Los tests de selección vigentes verifican SSE exacta, RMSErect y 21 candidatos sobre W*×24 | `tests/test_fase1a_selector_rectangular.py`, ejecutado con el par visible (`evidencia/g3_fase1a.txt`): **35/35 PASS**. Incluye `test_selector_vigente_cumple` (7 propiedades), los **5 mutantes detectados** (`suma_flotante`, `ultimo_en_empate`, `peso_1_h`, `todos_los_pares`, `rmse_sin_n`), la ruta productiva con 21 candidatos y W*×24, y los 16 AS-001 |
| La propiedad protegida sigue demostrada | `test_la_ruta_productiva_usa_el_selector_rectangular_y_ningun_selector_retirado` compara el modelo entregado con `_seleccionar_modelo_rectangular` sobre la matriz real (21 candidatos, H 1..24, pares comunes = W*×24, 0 llamadas al heredado). Las 7 propiedades y los 5 mutantes fijan SSE exacta, pesos uniformes, solo pares comunes, desempate y RMSE (03 §3) |

## 2. Bloqueos de 2D-2 que siguen abiertos fuera del script

AS-028 preparado no equivale a 2D-2 autorizado. La simulación con el par oculto (G3, `evidencia/g3_*`) da:

| Efecto con el par oculto | Archivo e id | Perfil | Tratamiento propuesto para 2D-2 (matriz 2C) |
|---|---|---|---|
| **Error de recolección** (importación sin uso, L35) | `tests/test_remediacion_r2_h1_h2_h3_h7.py`: los 9 ids del archivo | **esencial** | Quitar la importación. El archivo no usa el símbolo |
| FAIL (`patch.object` de un atributo inexistente) | `test_fase1a_selector_rectangular.py::test_la_ruta_productiva_usa_el_selector_rectangular_y_ningun_selector_retirado` | esencial | Pasar el nombre de `retirados` a `eliminados` (exigir ausencia) |
| FAIL | `test_origen_inicial_backtesting.py::test_p0d_la_regla_de_seleccion_no_cambia` | esencial | Retirar el id |
| FAIL | `test_nmin_adversarial.py::test_muestra_comun_intacta_desde_el_primer_origen` | esencial | Retirar el id |
| FAIL (`AttributeError`) | `test_nmin_adversarial.py::test_p0a_p0b_p0d_intactos` | esencial | Migrar la parte vigente |
| Sin efecto | `test_fase2c_contratos_vigentes.py` (`HEREDADAS`) | esencial | Ninguno: es una lista de exclusión |
| Error de recolección | `test_p0d_rmse_orden_exacto.py`, `test_rmse_global_estable.py`, `test_seleccion_rmse_global.py` | histórica | Según la matriz 2C |

`pytest --collect-only tests` con el par oculto: **1 025 recogidos y 7 errores**, es decir, los 3 históricos más 4 nuevos (`evidencia/g3_collect_tests_oculto_resumen.txt`). Ejecutar con el par oculto los 5 archivos esenciales que lo nombran da 4 FAIL, 65 PASS y 1 error de recolección (`evidencia/g3_esenciales_afectados_oculto.txt`).

A eso se suma lo que la simulación no ejecuta:
- **Pruebas históricas:** `test_cierre_metodologico.py:414,437`, `test_horizonte_evidencia_reducida.py:375-393`, `test_p0d_rmse_orden_exacto.py`, `test_rmse_global_estable.py` y `test_seleccion_rmse_global.py`. Fallarán o darán errores de recolección dentro del perfil histórico. El prompt de 2D-2 tiene que decidir su destino. La matriz 2C (`docs/fase_v112_antislop_02c_registro_historico/03_MATRIZ_MIGRACION_PRUEBAS.csv`) ya propone el tratamiento.
- **Ficha C-SEL-001** en `app_icociv/estadistica/criterios.py:566-568` (AS-024). Nombra la ruta del selector heredado; si no se actualiza, quedaría apuntando a un símbolo inexistente. Aquí no se edita.

## 3. Lo que debería incluir el prompt de 2D-2 (recomendación, no ejecutada)

1. Retirar los dos símbolos en un commit atómico junto con las pruebas que dependen de ellos.
2. Quitar la importación sin uso de `tests/test_remediacion_r2_h1_h2_h3_h7.py:35`, que es esencial.
3. Seguir el plan 2C para `test_origen_inicial_backtesting.py:250` y `test_nmin_adversarial.py:136`.
4. Pasar los nombres de la tupla `retirados` a `eliminados` en `test_fase1a…:305`.
5. Decidir qué se hace con los 5 archivos históricos y con la ficha C-SEL-001.
6. Verificar la huella exacta, los 811 ids (menos las bajas autorizadas), golden y AS-001, y pasar Thermos.
