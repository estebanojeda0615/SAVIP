# 02 · Matriz G5: pruebas históricas y prueba esencial adaptada

**Cómo se midió.**
- Estados por id, sacados del JUnit de cada archivo ejecutado aislado en la misma copia limpia y el mismo equipo.
- «Antes» es `1848275`. «Después» es `54f7ccf` (código de `10f1d0d`).
- Archivos con referencia real a los nombres retirados, encontrados por búsqueda: **4 históricos y 1 esencial**, la cifra que anticipaba la Fase 2A.

## 1. Prueba esencial adaptada (G3)

**Prueba:** `tests/test_fase1a_selector_rectangular.py::test_la_ruta_productiva_usa_el_selector_rectangular_y_ningun_selector_retirado`. **Mismo id.**

| Propiedad | Antes | Después |
|---|---|---|
| Ejecuta `ejecutar_proyeccion` real, sin mocks vacíos (serie `tendencia_lineal_ruido`, h=11) | Sí | Sí |
| `_matriz_rectangular_12_24` y `_seleccionar_modelo_rectangular` llamados exactamente 1 vez | Sí | Sí |
| Espía sobre selectores y evaluadores heredados presentes, con `call_count == 0` | 6 nombres | **3 nombres que siguen existiendo**: `seleccionar_modelo_por_rmse_oos_global`, `determinar_horizonte_maximo_estadistico`, `_evaluar_horizontes_proyeccion` |
| Las 3 funciones retiradas | Se espiaban | **Se exige su ausencia**: `[n for n in eliminados if hasattr(sp, n)] == []`. Ningún `getattr(..., None)` silencioso |
| Selección reproducida desde la matriz = resultado (`modelo_codigo`, `rmse_seleccion_oos`) | Sí | Sí |
| 21 candidatos, horizontes exactamente `1..24`, `pares_comunes == pares_esperados == W*·24` | Sí | Sí |

**Sensibilidad.** Lo comprueba [`evidencia/sensibilidad_prueba_integracion.py`](evidencia/sensibilidad_prueba_integracion.py). Las mutaciones se aplican solo a copias de trabajo, nunca al repositorio. Resultado en [`evidencia/sensibilidad.txt`](evidencia/sensibilidad.txt):

| Escenario | Resultado | Motivo |
|---|---|---|
| Control, sin mutación | **PASA** | — |
| S0: producción de `1848275`, con las 3 funciones aún definidas | **FALLA** | Exigencia de ausencia |
| S1: la ruta productiva invoca además `seleccionar_modelo_por_rmse_oos_global` | **FALLA** | Espía `call_count != 0` |
| S2: la ruta sustituye el selector rectangular por un mutante (suma **flotante** sobre **todos** los pares: viola SSE exacto y muestra común) | **FALLA** | `vigente.call_count == 0` |

**Los cinco mutantes de la Fase 1A**, intactos y detectados (`test_cada_mutante_es_detectado`, 5/5 PASS):

| Mutante | Qué rompe |
|---|---|
| `suma_flotante` | Ordena por suma flotante en vez de SSE exacto (falla la propiedad de 1 ULP) |
| `ultimo_en_empate` | Desempata por el último del banco |
| `peso_1_h` | Pondera con 1/h |
| `todos_los_pares` | Usa todos los pares del candidato en vez de la muestra común |
| `rmse_sin_n` | Informa `sqrt(SSE)` sin dividir por n |

## 2. Pruebas históricas afectadas (no esenciales): destino caso a caso

**`tests/test_rmse_global_estable.py`** (11 ids → 4)

| Id | Antes | Después | Referencia | Decisión y justificación |
|---|---|---|---|---|
| `test_t1_ordinario_coincide_con_la_formula_directa` | PASS | — | `_rmse_global_estable` | **RETIRADA.** Solo probaba la API retirada (hypot) |
| `test_t2_dos_errores_enormes_no_desbordan` | PASS | — | ídem | **RETIRADA.** La propiedad vigente (RMSE finito con errores enormes) la prueban `test_as001_*` sobre el selector vigente, en el perfil esencial |
| `test_t3_caso_del_hallazgo_no_levanta_overflow` | PASS | — | ídem | **RETIRADA.** Cubierta por `test_as001_candidato_divergente_no_aborta_la_seleccion` (1,2258e240), esencial |
| `test_t4_todos_ceros_dan_cero` | PASS | — | ídem | **RETIRADA.** Solo API retirada |
| `test_t5_un_error_infinito_produce_rmse_no_finito` | PASS | — | ídem | **RETIRADA.** El selector vigente excluye los no finitos: `test_un_error_no_finito_excluye_solo_a_ese_candidato` y `test_as001_errores_no_finitos_siguen_excluidos_junto_a_enormes`, esenciales |
| `test_t6_un_error_nan_produce_rmse_no_finito` | PASS | — | ídem | **RETIRADA.** Ídem |
| `test_t6b_una_suma_que_no_cabe_en_float_da_infinito_sin_excepcion` | PASS | — | ídem | **RETIRADA.** Describía `inf` de hypot. El vigente informa el RMSE finito (`test_as001_una_ulp_en_el_borde_de_dbl_max`) |
| `test_t7_…`, `test_t7b_…`, `test_t8_…`, `test_t9_…` | PASS | **PASS** | Usan `seleccionar_modelo_por_rmse_oos_global`, que se conserva | **CONSERVADAS.** Solo se quitó del import el nombre retirado (y `math`/`numpy`, usados solo por T1–T6b) |

**`tests/test_p0d_rmse_orden_exacto.py`** (13 ids → 13)

| Id | Antes | Después | Decisión |
|---|---|---|---|
| `test_d1_el_contraejemplo_de_una_ulp_se_decide_de_forma_unica` | PASS | **PASS** | **ADAPTADA.** Conserva el contraejemplo documentado: hypot empata a 1 ULP y el SSE exacto distingue. `_rmse_global_estable(x)` se sustituye por la misma expresión de la biblioteca estándar que era su cuerpo, `math.hypot(*x) / math.sqrt(len(x))`. **Las aserciones no cambian** |
| `test_d2` … `test_d13` (12) | PASS | **PASS** | **SIN CAMBIOS** (solo el import) |

**`tests/test_seleccion_rmse_global.py`** (16 ids → 15)

| Id | Antes | Después | Decisión |
|---|---|---|---|
| `test_no_hay_peso_por_horizonte` | PASS | **PASS** | **ADAPTADA.** La aserción principal, que el selector histórico elige `largo`, no cambia. El contraste con la regla 1/h retirada se calcula de forma explícita sobre los mismos 2×2 RMSE: RMSE relativo al mejor de cada horizonte, peso 1/h. **Mismo resultado esperado: `corto`** |
| `test_la_regla_no_consulta_umbrales_ni_identidad` | PASS | **PASS** | **ADAPTADA.** La función retirada sale de la tupla. Se siguen inspeccionando las otras dos con la misma lista de prohibidos |
| `test_no_queda_el_peso_1_h_en_la_ruta_de_seleccion` | PASS | — | **RETIRADA.** Solo inspeccionaba la fuente de `_modelo_consistente_desde_comparativo`. La ausencia de peso 1/h en el selector **vigente** la prueban, de forma conductual, `p_pesos_uniformes_por_horizonte` y el mutante `peso_1_h` (esenciales) |
| `test_la_regla_retirada_ya_no_se_invoca_en_la_ruta_productiva` | PASS | **PASS** | **ADAPTADA, más estricta.** Contaba la definición (`== 1`). Sin definición, exige 0 apariciones de la llamada y que el atributo no exista |
| Otros 12 | PASS | **PASS** | **SIN CAMBIOS** |

**`tests/test_cierre_metodologico.py`** (24 ids → 23)

| Id | Antes | Después | Decisión |
|---|---|---|---|
| `test_la_ponderacion_1_h_ya_no_decide` | PASS | — | **RETIRADA.** Solo inspeccionaba la fuente de la función retirada. Cubierta como la anterior |
| `test_no_hay_modelo_por_horizonte` | **FAIL** | **FAIL** | **SIN CAMBIOS.** Fallo **previo**, ajeno a esta fase: busca un texto de `_ejecutar_proyeccion_base` que ya no existe. No se corrige |
| Otros 22 | PASS | **PASS** | **SIN CAMBIOS** |

**Resumen G5.**

| Destino | Ids |
|---|---|
| Retiradas | 9 (7 + 1 + 1). Todas probaban **solo** código retirado; su propiedad vigente, si existe, la cubren pruebas esenciales |
| Adaptadas | 4 (D1, `test_no_hay_peso_por_horizonte`, `test_la_regla_no_consulta_…`, `test_la_regla_retirada_…`), sin cambiar ninguna expectativa sustantiva |
| Conservadas sin cambio de casos | 51 de los 64 originales: 4 + 12 + 12 + 23, incluido el FAIL previo de `test_cierre_metodologico` |

Ningún archivo se borró. La trazabilidad está en `1848275`, donde siguen el código y las pruebas retiradas.

## 3. Conjunto de las 797 pruebas esenciales

- **Recuento.** `scripts/pruebas_fase0.py --listar` da **797** esenciales antes y después (`evidencia/listar_*.txt`). Ningún archivo esencial cambió salvo la prueba adaptada, con el mismo id.
- **Comparación por id.** El comparador [`evidencia/comparar_ids_esenciales.py`](evidencia/comparar_ids_esenciales.py) cruza los JUnit de los perfiles esenciales locales de antes y después, por `(classname, name)`. Resultado en 04 §1.
- **Recolección completa.** `pytest --collect-only tests` da 1 061 ids antes y **1 052** después. La diferencia son **exactamente** los 9 ids retirados de la tabla anterior ([`evidencia/coleccion_diff.txt`](evidencia/coleccion_diff.txt)). Los 3 errores de recolección previos son los mismos (`test_equivalencia_presupuestal_fase_4e_b`, `test_p0c_objeto_publico_sin_intervalo`, `test_p0c_regresion_negativa_c2`) y no se cuentan como éxitos.
