# 06 · Plan de ejecución de la Fase 2D (solo propuesta)

Nada de este plan se ha ejecutado. Cada lote requiere autorización separada.

**Base de todos los lotes:** el HEAD final de la Fase 2C. **Herramientas:** las de las fases 2A–2C:
- `retirar_definiciones.py`, `grafo_as003.py`, `huella_semantica.py`;
- `espia_as003.py`, `comparar_ids_esenciales.py`.

## 1. Orden determinado por el grafo

Lo determinan las llamadas internas, no la lista del prompt:

```
seleccionar_modelo_por_evidencia ── 9 auxiliares exclusivos                     (lote 2D-4, aislado)
tramo_evidencia_oos                                                             (lote 2D-5, aislado)
seleccionar_modelo_por_rmse_oos_global ── _errores_oos_por_par                  (lote 2D-2, aislado)
determinar_horizonte_maximo_estadistico ── 5 exclusivos ─┐
                                                         ├─ _tipo_uso_horizonte, _mayor_horizonte_permitido (compartidos)
_aplicar_salvaguarda_benchmarks ── _evaluar_horizontes_proyeccion ── _clasificar_evidencia_horizonte ── …┘   (lote 2D-3)
_seleccionar_horizonte_permitido                                                (aislado; con 2D-3 por su ficha C-ALC-003)
```

**Regla de cierre.** Los dos compartidos se retiran con el **último** lote que los use: 2D-3 si 2D-1 va antes. Ningún lote deja una llamada colgante, porque cada conjunto es cerrado según el grafo.

## 2. Lotes

| Lote | Símbolos | Líneas de definición | Dependencias previas | Pruebas existentes afectadas (03) | Sustitutas | Condición GO | NO-GO si… |
|---|---|---|---|---|---|---|---|
| **2D-0 Previo** (sin borrar código) | — | 0 | — | — | Las 7 nuevas de la Fase 2C (ya incorporadas) | Decisiones 1–6 de §3 tomadas; parche AS-024 preparado por lote | Falta alguna decisión que bloquee el lote siguiente |
| **2D-4 Selector por evidencia** | `seleccionar_modelo_por_evidencia` y 9 auxiliares (`modelos_interpretables.py`) | 332 | Ninguna | 1 esencial: `test_fundamentacion_metodologica::test_el_selector_retirado_conserva_su_definicion_para_auditoria` (solo existencia). Las comprobaciones textuales «sin llamada a seleccionar_modelo_por_evidencia(» sobreviven | No aplica (la trazabilidad pasa a 02 y a Git) | Autorización para retirar ese id esencial | Aparece un consumidor nuevo en el grafo |
| **2D-5 Tramos OOS** | `tramo_evidencia_oos` | 11 | Ninguna | 1 esencial: `test_cierre_semantico_ps01_ps05::test_ps03_…`. 1 script no recolectado: `test_residuales_auditoria_independiente_r3.py` (lo importa) | 4 nuevas: `test_texto_evidencia_oos_…` y `test_escasez_…[36,37,41]` | Autorización para retirar el id; decisión AS-007 sobre r3 | Sin decisión sobre r3, su importación pasaría a ser un **error de recolección nuevo** del perfil histórico (3 → 4) |
| **2D-2 Selector RMSE global** | `seleccionar_modelo_por_rmse_oos_global`, `_errores_oos_por_par` | 107 | **AS-028**: destino de `pruebas/prueba_horizonte_dinamico_ui_reportes.py` | Esenciales: `test_origen_inicial_backtesting::test_p0d_…` (retirar) y `test_nmin_adversarial::test_muestra_comun_…` (retirar). `test_nmin_adversarial::test_p0a_p0b_p0d_intactos`: migrar, quitando la llamada a test_p0d. `test_fase1a…::test_la_ruta_productiva_…`: adaptar a ausencia. Históricas: 14 + 11 + 4 + 2 + 1 (03). Ficha C-SEL-001 | Fase 1A: 7 propiedades, 5 mutantes, AS-001 y `test_metodologia_n0_12_h24::test_c/test_d` | AS-028 decidido; parche C-SEL-001 en el mismo commit | El script sigue usando el selector y no se autorizó retirarlo o modernizarlo |
| **2D-1 Decisión de horizonte máximo** | `determinar_horizonte_maximo_estadistico`, `_serializar_evaluaciones_horizonte`, `_item_horizonte_global`, `_mayor_horizonte_con`, `_ultimo_horizonte_por_clasificacion`, `_evidencia_horizonte` | 420 | **AS-028** (mismo script). **AS-004**: `generador_reportes.py` lee claves que solo producía esta función | 8 esenciales (`test_resultado_horizonte_solicitado` ×6 y `test_presentacion_resultados` ×2): retirar. 1A: adaptar. Histórica: `test_cierre_metodologico::test_no_queda_cascada_…`. Ficha C-ALC-002 | `test_metodologia_n0_12_h24::test_b/test_efg`; golden h11/h23 (alcance fijo, la consulta no recalcula) | AS-028 y AS-004 decididos; autorización para retirar 8 ids esenciales | Quedan lecturas de `horizonte_maximo_*` sin decidir |
| **2D-3 Evaluación, clasificación y salvaguarda** | `_aplicar_salvaguarda_benchmarks`, `_puntaje_rmse_ponderado`, `_backtesting_por_modelo_horizonte`, `_evaluar_horizontes_proyeccion`, `_clasificar_evidencia_horizonte`, `_estado_por_horizonte`, `_mensaje_horizonte_no_permitido`, `_comparacion_desde_backtesting`, `peor_que_benchmark_naive`, `_seleccionar_horizonte_permitido`, más los compartidos `_tipo_uso_horizonte` y `_mayor_horizonte_permitido` | 853 | 2D-1 (por los compartidos). **Decisión del punto no finito** y de «MAPE no calculable». AS-007 sobre los `test_p0c_*` y `bghc` | 11 esenciales (`fundamentacion` ×7, `presentacion` ×1, `remediacion` ×2, `vocabulario_vc` ×1), 1A, unas 20 históricas. Fichas C-ALC-001, C-ALC-003, C-SAL-001, C-BEN-002 | Nuevas: `test_escasez_*`, `test_banda_no_construible_…`, `test_sin_errores_finitos_comunes_…`, `test_la_ruta_vigente_no_referencia_…`; PS01 (salvaguarda) | Las dos decisiones tomadas; si se mantiene la regla del punto no finito, cambio de producción autorizado **antes** del retiro, con su prueba | **Sin decisión sobre el punto no finito: NO-GO** (se perdería la única expresión de P0-G) |
| **2D-6 Limpieza final** | Docstrings y comentarios de código vigente que citan funciones retiradas: L720, L1431, L1502, L4464 y L4979 de `2f70391`. L1502 y L4979 afirman que el bloqueo «vive en» / «sigue en» `_clasificar_evidencia_horizonte`, que no se ejecuta; imports que queden huérfanos; docstrings de módulo de pruebas | — | Todos los anteriores | Ninguna | — | Diff solo de comentarios e imports huérfanos | Cualquier cambio de lógica |

**Suma de líneas de definición:** 332 + 11 + 107 + 420 + 853 = **1 723**, el recuento de 01.

## 3. Decisiones que debe tomar el propietario antes de 2D

1. **Punto no finito.** La regla «un punto no finito bloquea» (P0-G) solo existe en `_clasificar_evidencia_horizonte` (L2840). ¿Debe aplicarse en la ruta vigente?
   - Sí: cambio de producción autorizado y prueba nueva, antes de 2D-3.
   - No: se documenta como regla abandonada y se retiran sus pruebas con 2D-3.
2. **«MAPE no calculable».** ¿Debe la ruta vigente publicar esa advertencia? Hoy solo la redacta el clasificador heredado.
3. **AS-028: `pruebas/prueba_horizonte_dinamico_ui_reportes.py`.**
   - Opción A: retirar el script completo.
   - Opción B: migrar a `tests/` solo lo vigente sin cobertura equivalente y retirar el resto.
   - Bloquea 2D-1 y 2D-2.
4. **AS-007.** Destino de los 4 archivos de estilo script de `tests/` que importan funciones heredadas: `test_p0c_*` ×2, `bghc` y `r3`. Bloquea 2D-3 y 2D-5.
5. **AS-004.** Lecturas de `horizonte_maximo_*` en `generador_reportes.py`. Bloquea 2D-1.
6. **Política de ids esenciales.** Se autoriza retirar los ids listados en cada lote, sin exigir 797, con la regla de §4.
7. *(Opcional)* Ficha nueva C-SEL-002 para el selector vigente (04 §3.2).

## 4. Política de retiro de pruebas en 2D

- Cada id que se retire figura en la matriz 03 con su contrato y su prueba vigente de cobertura, o con la marca `SIN EQUIVALENTE / NO APLICA` y su justificación.
- El informe de cada lote lista los **ids eliminados, añadidos y conservados** y los compara con el JUnit anterior (`comparar_ids_esenciales.py`).
- Se exige **la misma o mayor cobertura de contratos vigentes**, no el mismo recuento. Ningún contrato con estado `DECISIÓN PENDIENTE` puede perder su única prueba hasta resolverse.
- Prohibido: `skip`/`xfail` para ocultar fallos, cambiar expectativas para hacer pasar una prueba, regenerar golden o ampliar tolerancias.

## 5. Aceptación común de cada lote

- **Estadística:** huella semántica exacta con 0 diferencias en el mismo equipo (20 casos, SSE de los 21 candidatos, H1–H24, MAE(h)) y los 29 golden sin cambios.
- **Económica, sesiones y exportables:** los golden económicos y de sesiones y exportables, más el perfil esencial completo.
- **API:** `servicio_proyeccion.ejecutar_analisis` y `validacion_series.validar_serie` intactas. `pruebas/prueba_estadistica.py` con la misma salida.
- **CI:** verde sobre el commit de código y sobre el HEAD documental, sin reintentos ocultos.

## 6. Riesgo, reversión y base

| Lote | Riesgo de regresión | Reversión |
|---|---|---|
| 2D-4 | Muy bajo: módulo distinto y sin llamadas | `git revert <commit del lote>` |
| 2D-5 | Bajo (1 función) | `git revert` |
| 2D-2 | Bajo en ejecución; medio documental (C-SEL-001, script) | `git revert` (incluye ficha y pruebas, en el mismo commit) |
| 2D-1 | Medio: claves leídas por `generador_reportes` | `git revert` |
| 2D-3 | Medio-alto: el clasificador contiene una regla sin equivalente vigente | `git revert`. NO-GO hasta la decisión 1 |

**Commits.** Cada lote es un commit de retiro, o dos (pruebas preparatorias y luego retiro), sobre una rama `maintenance/v1.1.2-fase2d-<lote>` que sale del HEAD de la Fase 2C. La base inmutable de referencia es `2f70391`, donde está el código heredado completo.
