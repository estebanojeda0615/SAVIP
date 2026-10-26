# 02 · Pruebas y Golden Masters

## 1. Pruebas AS-001 (`tests/test_fase1a_selector_rectangular.py`)

**Cómo se ejecutaron.** Todas llaman al selector productivo (`SELECTOR = sp._seleccionar_modelo_rectangular`) o a `ejecutar_proyeccion`, nunca al helper nuevo. Así, contra el código anterior fallan por la causa real.

**Qué significa cada columna.**
- «Antes»: la prueba ejecutada sobre `servicio_proyeccion.py` de `428fdc0`, en una copia limpia ([evidencia](evidencia/as001_codigo_anterior.txt)).
- «Después»: la misma prueba sobre la corrección ([evidencia](evidencia/selector_despues.txt)).

| Prueba | Valores | Esperado | Obtenido después | Antes | Después |
|---|---|---|---|---|---|
| `test_as001_candidato_divergente_no_aborta_la_seleccion` (antes `xfail` estricto) | divergente `[1.2258e240]×2`, sano `[1, 2]` | gana sano y queda segundo divergente; RMSE `√2,5` y `1.2258e240`; diferencias finitas | igual, con RMSE segundo `== 1.2258e240` y diferencia absoluta `1.2258e240 − √2,5` | XFAIL (`OverflowError`) | **PASS** |
| `…dos_candidatos_enormes_ordenados_por_sse_exacto_y_rmse_preciso` | a `[1.2258e240, 1e240, −3e239]`, b `[1.2258e240, 1.1e240, −3e239]`, c `[1e300]×3` | gana a y queda segundo b; RMSE a 1 ULP o menos de la referencia Decimal de 100 dígitos | a y b; los dos RMSE a 0 ULP | FAIL `OverflowError` | **PASS** |
| `…empate_exacto_a_escala_extrema_gana_el_primero_del_banco` | x `[1e300, −2e300]`, y `[−2e300, 1e300]`, z `[1e300, 2e300]` (SSE idéntico) | x; con el banco invertido, z; diferencias 0 | x / z; RMSE iguales; diferencias 0,0 | FAIL `OverflowError` | **PASS** |
| `…una_ulp_en_el_borde_de_dbl_max` | a `[DBL_MAX]×3`, b `[nextafter(DBL_MAX, 0)]×3` | gana b por 1 ULP; RMSE exactos; diferencia `ulp` | b, `menor`, `DBL_MAX` y `ulp(menor)` | FAIL `OverflowError` | **PASS** |
| `…errores_no_finitos_siguen_excluidos_junto_a_enormes` | `[inf, .1]`, `[nan, .1]`, `[1.2258e240, 1]`, `[1, 1]` | gana sano y queda segundo enorme; no finitos excluidos | igual | FAIL `OverflowError` | **PASS** |
| `…muestra_comun_y_pesos_uniformes_a_escala_extrema` | a con `1e308` en un par que b no tiene; `[2e200, 0]` frente a `[0, 2e200]` | gana a; 2 de 3 pares comunes; RMSE `1e200`; empate → a | igual | FAIL `OverflowError` | **PASS** |
| `…rango_ordinario_rmse_identico_bit_a_bit` ×8 | escalas 1e-150, 1e-20, 1e-3, 1, 37,5, 1e6, 1e50 y 1e150 | `== math.sqrt(float(_sse_exacto(v))/n)` | igualdad exacta en las 8 | PASS (sin cambio) | **PASS** |
| `…diferencia_porcentual_no_representable_es_inf_y_los_consumidores_la_omiten` | fino `[1e-100]×2`, enorme `[1e300]×2` | gana fino; RMSE y diferencia absoluta finitos; `diferencia_porcentual == inf`; UI «No disponible»; `es_numero` False; JSON `None` | igual | FAIL `OverflowError` | **PASS** |
| `…ruta_productiva_con_21_candidatos_y_uno_divergente` | `ejecutar_proyeccion` (serie `tendencia_lineal_ruido`) con un candidato, ni ganador ni segundo, puesto a `1.2258e240` en todos los pares | 21 candidatos; con horizonte consultado 11, 1 y 24, igual ganador, segundo, RMSE y trayectoria de 24 meses que sin divergente; 1 llamada al selector por ejecución | igual | FAIL `OverflowError` (la proyección completa aborta) | **PASS** |

**Resumen del archivo.**

| Momento | PASS | XFAIL | FAIL |
|---|---|---|---|
| Antes (`428fdc0`) | 19 | 1 | 0 |
| Después (`c42cbbf`) | **35** | **0** | 0 |

Las 19 pruebas previas (propiedades, bordes, mutantes e integración de la Fase 1A) siguen pasando sin cambios. Los 5 mutantes siguen detectados.

**Prueba del cambio (§4.E).** Contra el código anterior: 8 FAIL, todos por `OverflowError` en `numbers.py:316`, y 8 PASS, que son las 8 de rango ordinario. Contra la corrección pasan las 16.

## 2. Golden Masters (29)

- `git diff 428fdc0 HEAD -- tests/fixtures/fase0` está **vacío**:
  - los 4 JSON golden son idénticos byte a byte;
  - `captura.py` no cambia: `REL_TOL` 1e-9 y `REL_TOL_OPTIMIZADOR` 1e-2 para Holt/Huber.
- Comparación antes y después:

| Archivo | Pruebas | Antes (CI 40403298861, `428fdc0`) | Después (local `df4fb16` y CI 40415465901) |
|---|---|---|---|
| `test_fase0_golden_motor.py` | 11 | PASS | **PASS** |
| `test_fase0_golden_economico.py` | 6 | PASS | **PASS** |
| `test_fase0_golden_sesion_exportables.py` | 12 | PASS | **PASS** |

- **Qué fijan los golden.**
  - Motor: ganadores, RMSErect, trayectorias de 24 meses, MAE(h), estados y evidencias.
  - Economía: porcentajes, factores e importes.
  - Sesiones y exportables: Excel, PDF, DOCX y CSV.
- **Resultado.** Pasan con las tolerancias de siempre. Ningún dato real llega al camino Decimal, porque ningún SSE desborda, así que el número informado no cambia.
- **Holgura entre CPU (§4.D).** El 1e-2 se aplica solo al RMSErect de candidatos perdedores ajustados por optimizador iterativo (Fase 0, 02 §5 bis). No se amplió y no hubo diferencias.

## 3. Perfil esencial

| Ejecución | Pruebas | PASS | FAIL | XFAIL | SKIP | Intermitentes | Tiempo |
|---|---|---|---|---|---|---|---|
| Fase 1A, CI 40394420320 / 40403298861 | 782 | 781 | 0 | 1 | 0 | ninguna | ~59 min |
| **Local, copia limpia de `df4fb16`** | **797** | **797** | **0** | **0** | **0** | ninguna | 56 min (3 383 s en JUnit) |
| **CI [40415465901](https://github.com/estebanojeda0615/SAVIP/actions/runs/40415465901), `df4fb16`** | **797** | **797** | **0** | **0** | **0** | ninguna | 60 min |

**Recuento.** 797 = 782 − 1 (el `xfail` retirado, que reaparece como PASS) + 16 (la prueba AS-001 reescrita más 15 nuevas). Recuento por perfil (`--listar`, [evidencia](evidencia/listar_despues.txt)):

| Perfil | Pruebas |
|---|---|
| esenciales | 797 |
| dane | 0 |
| historicas | 251, más 3 errores de recolección (sin cambios) |
| gui | 13 |
| **Total** | **1 061** |

**El commit `c42cbbf`** solo amplía la prueba de integración (horizontes 1 y 24). Su selector pasa 35 de 35 en local. El perfil completo del HEAD final lo ejecuta el CI (03 §2).

**Lo que no se ejecutó.** Según el prompt, ni las 251 pruebas históricas ni el perfil gui.

**Observación, previa a esta fase.**
- `--listar` recolecta también `tests/test_visual_fase_3c_b.py`, del perfil histórico.
- Ese archivo crea al importarse la carpeta vacía `docs/fase_3c_b/temporal` (`mkdir` a nivel de módulo).
- No lo produce el perfil esencial ni ninguna prueba de esta fase. Queda para la limpieza de AS-007 o del perfil histórico.

**Evidencias.**
- [`esenciales_local.txt`](evidencia/esenciales_local.txt): salida completa local.
- [`ci_40415465901_resumen.txt`](evidencia/ci_40415465901_resumen.txt): resumen del CI.
