# 01 · G1: referencias de las 10 definiciones (árbol real `83549e7`)

**Método:**
- grafo AST conservador (`docs/fase_v112_antislop_02a_as003/evidencia/grafo_as003.py`) recalculado sobre el árbol del lote;
- `grep` de cada nombre en todo el repositorio, incluidos `docs/`, `pruebas/`, `scripts/`, `packaging/` y `.github/`;
- búsqueda de imports `from …modelos_interpretables import …` y de accesos `mi.`, `MI.` y `modelos_interpretables.`.

**Enlace permanente** de cada definición: `https://github.com/estebanojeda0615/SAVIP/blob/2f70391e1b920764e79fa50ec2c2da6b6b572e53/app_icociv/estadistica/modelos_interpretables.py#L<ini>-L<fin>`.

| Definición | Líneas en `83549e7` | Llamadores | Producción / scripts / fichas | Pruebas |
|---|---|---|---|---|
| `seleccionar_modelo_por_evidencia` | 280–444 (165) | ninguno | ninguno | `test_fundamentacion_metodologica::test_el_selector_retirado_conserva_su_definicion_para_auditoria` (exige que exista). Además, comprobaciones **textuales** de ausencia de llamada en `test_fundamentacion…` ×2, `test_nmin_adversarial`, `test_origen_inicial_backtesting`, `test_integracion_fhg` y `test_fase2c_contratos_vigentes` (`HEREDADAS`): no exigen que exista |
| `_benchmark_dominante` | 447–480 (34) | `seleccionar_modelo_por_evidencia` | ninguno | Solo texto en `HEREDADAS` (2C) |
| `comparar_modelo_con_benchmarks` | 483–540 (58) | ídem | ninguno | ídem |
| `resumir_ranking_backtesting` | 543–565 (23) | ídem | ninguno | ídem |
| `_mejor_candidato_no_elegible` | 568–586 (19) | ídem | ninguno | ídem |
| `_razones_descartes` | 589–597 (9) | ídem | ninguno | ídem |
| `_ratio` | 1352–1355 (4) | `comparar_modelo_con_benchmarks` | ninguno | ninguna |
| `_mejor_por` | 1358–1363 (6) | `resumir_ranking_backtesting` | ninguno | ninguna |
| `_numero` | 1366–1371 (6) | las 6 anteriores del bloque | ninguno | ninguna. `tests/test_fase_4i_p2` usa **otro** `_numero` (de `reportes.sesion_modulos`) |
| `_fmt` | 1374–1381 (8) | `seleccionar_modelo_por_evidencia` | ninguno | ninguna |
| **Total** | **332 líneas** | Conjunto cerrado: nadie fuera del bloque llama a ninguna | — | — |

**Otras comprobaciones:**
- todos los usos de `_numero`, `_ratio`, `_fmt` y `_mejor_por` en `modelos_interpretables.py` están dentro de las líneas 280–597, es decir, del propio bloque;
- ningún módulo los importa desde aquí;
- `servicio_proyeccion.py:2592` menciona `seleccionar_modelo_por_evidencia` en un **comentario** dentro de `_evaluar_horizontes_proyeccion` (heredada, lote 2D-3): no se toca en este lote;
- uso dinámico: ninguno (las búsquedas de la Fase 2C siguen valiendo; no hay `getattr`, `importlib` ni `eval` sobre este módulo).

**Grafo después del retiro.** 817 → 807 definiciones (−10).
- Ninguna definición nueva pasa a no alcanzable y ninguna cambia de alcance (producción, scripts o pruebas).
- Solo `durbin_watson`, que sigue siendo productiva, pierde un referenciante muerto.

**Imports que quedaron huérfanos y se retiraron:** `UMBRAL_RRMSE_PEOR_BENCHMARK` y `TOLERANCIA_RRMSE_BENCHMARK`, de `criterios` (solo los usaba el bloque).
- Nadie los lee a través de `modelos_interpretables`.
- Siguen definidos en `criterios.py`, que no se toca.
- `pyflakes` del módulo después del retiro: solo el aviso previo «f-string is missing placeholders» (ya existía, ahora en la línea 598). Los dos avisos previos de variables sin uso (`mape` y `smape`) desaparecen con el bloque.
