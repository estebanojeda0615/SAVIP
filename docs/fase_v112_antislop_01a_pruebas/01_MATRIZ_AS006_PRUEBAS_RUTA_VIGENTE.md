# 01 · AS-006: pruebas de la ruta vigente

**Resumen.** El selector que usa SAVIP es `_seleccionar_modelo_rectangular`. Hasta esta fase, sus propiedades (SSE exacto, desempate, muestra común, candidato divergente) solo estaban probadas sobre el selector retirado `seleccionar_modelo_por_rmse_oos_global`.

La nueva suite `tests/test_fase1a_selector_rectangular.py` (20 pruebas) las verifica sobre el selector vigente:
- comprueba que el conjunto **detecta 5 mutantes**;
- confirma por espía que la ruta productiva no toca ningún selector retirado;
- registra **AS-001** como `xfail(strict=True, raises=OverflowError)`, sin corregirlo.

No se modificó ni se borró ninguna prueba ni función antigua.

## 1. Ruta productiva (evidencia dinámica + estática)

**Traza dinámica** (`C:\Pruebas SAVIP\Fase1A\traza_alcanzabilidad.py`, local):
- **Método.** Envuelve con contadores `wraps` las 218 funciones de módulo de `servicio_proyeccion`, `modelos_interpretables`, `validacion_series`, `generador_reportes` y `contenido`. Incluye todas sus referencias `from x import f` en cualquier módulo `app_icociv.*`.
- **Escenarios ejecutados:** los 5 del motor (H11 y H23), el rechazo n = 30 y el recorrido GUI completo del Golden Master (2 series, guardar, reabrir, Excel/PDF/DOCX, factor legado, informe CSV/DOCX/PDF).
- **Resultado:** 135 funciones llamadas y 83 nunca llamadas.

| Función | Llamadas | Papel |
|---|---|---|
| `ejecutar_proyeccion` → `_ejecutar_proyeccion_base` | 14 / 14 | Entrada del motor (la GUI llega por `ControladorPrincipal.ejecutar_analisis`) |
| `_matriz_rectangular_12_24` | 14 | Matriz rectangular 12/24 |
| `_seleccionar_modelo_rectangular` | 13 | **Selector vigente**: 13, porque el rechazo n = 30 no llega a seleccionar |
| `_sse_exacto` | 483 | SSE con `Fraction` |
| `ajustar_modelos_candidatos` | 14 | Ajuste de los 21 candidatos |
| `seleccionar_modelo_por_rmse_oos_global`, `_rmse_global_estable`, `_errores_oos_por_par`, `_modelo_consistente_desde_comparativo`, `_modelo_trayectoria_consistente`, `_puntaje_rmse_ponderado`, `_aplicar_salvaguarda_benchmarks`, `determinar_horizonte_maximo_estadistico`, `_evaluar_horizontes_proyeccion`, `_clasificar_evidencia_horizonte`, `servicio_proyeccion.ejecutar_analisis` | **0** | Retiradas de la ruta |

**Referencias estáticas** de los símbolos de AS-006 fuera de su propia cadena. No confundo «no alcanzable desde la UI» con «innecesario»:

| Símbolo | Consumidores fuera de la cadena muerta |
|---|---|
| `seleccionar_modelo_por_rmse_oos_global` | Solo `_modelo_consistente_desde_comparativo` (también muerta). Aparece como **texto** en el registro de criterios `estadistica/criterios.py:568` (ruta documental, no llamada). Lo usa el script manual `pruebas/prueba_horizonte_dinamico_ui_reportes.py` |
| `_rmse_global_estable` | Ninguno en `app_icociv/`, `pruebas/`, `scripts/` ni `aplicacion.py`: solo pruebas |
| `determinar_horizonte_maximo_estadistico` | Ninguno en `app_icociv/` (solo comentarios). Script manual `pruebas/prueba_horizonte_dinamico_ui_reportes.py` |
| `servicio_proyeccion.ejecutar_analisis` | `pruebas/ejemplo_uso.py`, `prueba_estadistica.py` y `prueba_sesiones_reportes.py` (scripts manuales). Los `ejecutar_analisis` de `ventana_principal.py` son del **controlador**, otra función |

**Conclusión.** Estas funciones no se ejecutan en la aplicación, pero **conservan consumidores**: scripts manuales de `pruebas/` y el registro documental de `criterios.py`. Su retiro corresponde a AS-003, con esos consumidores en cuenta. Aquí no se toca nada de producción.

**Límite de la traza.** Es dinámica: una función no llamada en estos escenarios podría alcanzarse por otra rama, por ejemplo el informe del Empalme, que no se recorrió. Por eso las conclusiones de retiro se apoyan además en la búsqueda estática.

## 2. Pruebas involucradas (inventario y decisión)

Detectadas por análisis AST: cada función `test_*` que nombra una función con 0 llamadas en la traza. Son **75 pruebas en 16 archivos**.

| Archivo | Pruebas | Función que ejercita | Ruta productiva | Propiedad que protege | Decisión |
|---|---|---|---|---|---|
| `test_rmse_global_estable.py` | 11 | `_rmse_global_estable`, `seleccionar_modelo_por_rmse_oos_global` | **No** | RMSE sin desbordar (`hypot`), divergente que pierde, muestra común, desempate | **Conservar como caracterización histórica** (perfil `historicas`). Propiedades migradas (§3); T3/T7 reaparecen como AS-001 `xfail`. Retiro propuesto junto con el código en AS-003 |
| `test_seleccion_rmse_global.py` | 15 | `seleccionar_modelo_por_rmse_oos_global`, `_modelo_*` | **No** | Mínimo RMSE global, raíz del ECM, sin peso por h, pares comunes, invariancias, empate | Ídem |
| `test_p0d_rmse_orden_exacto.py` | 11 | `seleccionar_modelo_por_rmse_oos_global`, `_rmse_global_estable` (y `_sse_exacto`, vigente) | Parcial | Orden por SSE exacto (ULP), desempate, ±inf/NaN, pesos uniformes, sin tolerancia | Ídem |
| `test_origen_inicial_backtesting.py` | 1 (`test_p0d_la_regla_de_seleccion_no_cambia`) | Selector retirado | No | Muestra común, pesos, desempate y aritmética exacta | Conservar (perfil esencial, pasa); **duplicada** por la suite nueva; pendiente AS-003 |
| `test_nmin_adversarial.py` | 1 (`test_muestra_comun_intacta…`) | `_errores_oos_por_par` | No | Muestra común | Conservar; cubierta en vigente por `p_solo_pares_comunes` y la prueba de integración (W*·24) |
| `test_cierre_metodologico.py` | 10 | Inspección de fuente (`inspect.getsource`) de funciones retiradas | No | Que no reaparezcan umbrales, pesos 1/h ni cascadas | **Marcar pendiente AS-003**: evidencia textual histórica; se retirarían con el código |
| `test_fundamentacion_metodologica.py` | 6 | Inspección de fuente / `_clasificar_evidencia_horizonte`, `seleccionar_modelo_por_evidencia` | No | Que el selector de respaldo no se use; bloqueo solo por imposibilidad | Pendiente AS-003 |
| `test_resultado_horizonte_solicitado.py` | 6 | `determinar_horizonte_maximo_estadistico` | No | Campos de la estructura triangular retirada (lo declara su propio docstring) | Pendiente AS-003 |
| `test_presentacion_resultados.py` | 3 | `determinar_horizonte_maximo_estadistico`, `_clasificar_evidencia_horizonte` | No | Clasificación por horizonte retirada | Pendiente AS-003 |
| `test_remediacion_r2_h1_h2_h3_h7.py` | 2 | `_clasificar_evidencia_horizonte`, `_aplicar_salvaguarda_benchmarks` | No | Textos de defensa / salvaguarda | Pendiente AS-003 |
| `test_mensajes_ljung_box.py` | 3 | `contenido._motivo_ljung_box` (0 referencias en `app_icociv`) | No | Redacción del motivo Ljung-Box | **Pendiente AS-004** (generador antiguo). `calcular_ljung_box`, que sí es vigente, lo prueban otras pruebas del mismo archivo |
| `test_vocabulario_cobertura.py` | 2 | `describir_metodo_cobertura` (solo pruebas) | No | Vocabulario de cobertura | Pendiente AS-004 |
| `test_pool_calendario_fourier_seasonal.py` | 1 (`casoJ`) | `_lineas_horizontes`, `_lineas_determinacion_horizonte` + `ejecutar_proyeccion` | Mixta | IDs internos no visibles | Conservar: también ejercita la ruta vigente |
| `test_cierre_semantico_ps01_ps05.py`, `test_vocabulario_vc.py`, `test_integracion_fhg.py` | 1 + 1 + 1 | `tramo_evidencia_oos`, `_clasificar_evidencia_horizonte`, `_evaluar_horizontes_proyeccion` | No | Semántica de evidencia retirada | Pendiente AS-003 |

**Retiros en esta fase: 0.** Ninguna de estas pruebas vigila solo una regla abandonada sin vínculo con código existente. Todas ejercitan funciones que **siguen existiendo**, algunas con consumidores en `pruebas/`. Retirarlas antes que su código reduciría cobertura de algo vivo. Se propone retirarlas en AS-003/AS-004, junto con el código y con esta matriz como guía.

## 3. Trazabilidad: propiedad antigua → prueba del contrato vigente

| Propiedad (pruebas antiguas) | Nueva prueba sobre `_seleccionar_modelo_rectangular` |
|---|---|
| Elige el mínimo (`test_elige_el_minimo_rmse_global`, `d5`) | `p_minimo_sse` |
| RMSE = √(SSE/n), segundo y diferencias (`test_el_valor_es_la_raiz…`, `t1`) | `p_rmse_coherente`, `test_rmse_reportado_coincide_con_sse_exacto` |
| Una ULP decide por suma exacta (`d1`, `d12`) | `p_sse_exacto_decide_una_ulp`: 1e16 + 1 frente a 1e16 + 0,81, iguales en `float` |
| Empate exacto → primero del banco (`t9`, `d3`, `test_el_empate_exacto…`) | `p_empate_primer_candidato_del_banco` |
| Pesos uniformes, sin 1/h (`d11`, `test_no_hay_peso_por_horizonte`) | `p_pesos_uniformes_por_horizonte` |
| Solo pares comunes (`test_solo_compara_pares…`, `d10`, `t8`, nmin) | `p_solo_pares_comunes`; integración: `pares_comunes == pares_esperados == W*·24` |
| Invariancia al orden (`d2`, `test_invariante_al_orden…`) | `p_invariante_al_orden_de_entrada` (orden del banco sin empates y orden de inserción de pares) |
| ±inf/NaN no gana (`d7`, `d8`, `t5`, `t6`, `t7b`, `test_los_errores_no_finitos…`) | `test_un_error_no_finito_excluye_solo_a_ese_candidato` |
| Sin candidatos → None (`d9`, `test_banco_vacio…`, `test_sin_muestra_comun…`) | `test_sin_muestra_comun_o_banco_vacio_devuelve_none` |
| Reproducible (`test_es_reproducible`) | `test_es_reproducible_y_no_muta_la_matriz` |
| Divergente representable pierde | `test_candidato_sano_gana_frente_a_divergente_en_rango_representable` (1e150) |
| **Divergente no aborta** (`t3`, `t6b`, `t7`) | **`test_as001_candidato_divergente_no_aborta_la_seleccion`: `xfail` estricto (AS-001)** |
| Un solo modelo para la trayectoria; regla vigente en producción | `test_la_ruta_productiva_usa_el_selector_rectangular_y_ningun_selector_retirado`: 1 llamada al vigente; 0 a los 6 retirados; 21 candidatos y 24 horizontes |

**Sin equivalente vigente (no se migran):**
- el RMSE con `hypot` (`t1`–`t6b`) es una implementación del selector retirado. El vigente no la usa: es precisamente AS-001;
- las inspecciones de fuente.

## 4. Sensibilidad (mutantes definidos en la prueba, sin tocar producción)

`_referencia(...)` reimplementa el contrato con un defecto activable. `test_cada_mutante_es_detectado` exige que al menos una propiedad falle. `test_la_referencia_sin_defectos_cumple_todas_las_propiedades` comprueba que la referencia sin defectos las cumple.

| Mutante | Propiedades que lo detectan |
|---|---|
| `suma_flotante` (SSE en `float`) | `p_sse_exacto_decide_una_ulp` |
| `ultimo_en_empate` | `p_empate_primer_candidato_del_banco`, `p_pesos_uniformes_por_horizonte` |
| `peso_1_h` | `p_rmse_coherente`, `p_pesos_uniformes_por_horizonte` |
| `todos_los_pares` (sin muestra común) | `p_solo_pares_comunes` |
| `rmse_sin_n` | `p_rmse_coherente` |

## 5. AS-001: reproducido, **no corregido**

- **Prueba:** `test_as001_candidato_divergente_no_aborta_la_seleccion`, con banco `divergente = [1,2258e240, 1,2258e240]` y `sano = [1, 2]`.
- **Hoy:** `_seleccionar_modelo_rectangular` ordena bien por SSE exacto, pero en L949 hace `math.sqrt(float(sse) / n)`. `float()` de un `Fraction` de ~1,5e480 lanza `OverflowError`, y la proyección entera aborta.
- **Marcador:** `xfail(strict=True, raises=OverflowError)`. Cualquier otro fallo (por ejemplo, que gane `divergente`) **no** se acepta como esperado y la prueba falla. No es una corrección funcional.
- **Paso a PASS (Fase 1B):** al corregir el RMSE informativo sin convertir el SSE completo a `float` (p. ej. `OverflowError` → `inf`), la prueba pasará. `strict=True` la convertirá en **XPASS = fallo**, lo que obliga a retirar el marcador en el mismo commit de la corrección.
- **Cobertura del resto de la fase:** los Golden Masters del motor y las 7 propiedades garantizan que la corrección no cambie ninguna selección.
