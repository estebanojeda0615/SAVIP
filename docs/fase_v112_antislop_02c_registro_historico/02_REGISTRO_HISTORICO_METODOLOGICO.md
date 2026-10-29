# 02 · Registro histórico metodológico de SAVIP

**Propósito.** Explicar qué reglas estadísticas abandonó SAVIP, cuándo y por qué, dónde se conserva su código y qué hace hoy el motor. No duplica el código: lo enlaza en commits inmutables.

**Fuentes.**
- El código publicado en `2f70391` (rama de la Fase 2B).
- Sus docstrings y comentarios fechados.
- Las fichas de `app_icociv/estadistica/criterios.py`.
- Los informes de las fases 0 a 2B.

**Convenciones.**
- Una fecha «según el código» procede de un comentario o docstring del propio repositorio. No hay otra fuente en GitHub.
- Se marca «desconocido» lo que no consta.

Enlaces base:
- `2f70391`: https://github.com/estebanojeda0615/SAVIP/blob/2f70391e1b920764e79fa50ec2c2da6b6b572e53/
- `1848275` (antes de la Fase 2B): https://github.com/estebanojeda0615/SAVIP/blob/1848275e124a0242f57c3582b4cd643c58f0e3f7/
- `dfdb3e0` (SAVIP 1.1.1, raíz del historial de GitHub): https://github.com/estebanojeda0615/SAVIP/blob/dfdb3e046126093e23b045147f789fbc52961a73/

## 1. Lo que el historial de GitHub permite afirmar

- **Raíz del historial.** El primer commit del repositorio es `dfdb3e0`, «SAVIP 1.1.1» (2026-10-22). En él la ruta productiva **ya** es la rectangular: `_ejecutar_proyeccion_base` llama a `_seleccionar_modelo_rectangular` en la línea 1195. Las mismas 29 definiciones heredadas (1 665 líneas) de `servicio_proyeccion.py` ya eran inalcanzables desde producción: grafo `grafo_as003.py` ejecutado sobre un `git archive dfdb3e0`.
- **Lo que no está.** **En GitHub no existe ninguna versión en la que las reglas heredadas decidieran el resultado.** Su época productiva es anterior a la publicación del repositorio y solo consta en los comentarios fechados del código y en documentos externos citados por nombre, que no están en el repositorio. Por ejemplo, `CIERRE_FINAL_H9_RMSE_GLOBAL_SAVIP_2026-08-08`, citado en el docstring de `_modelo_trayectoria_consistente` en `1848275`. **Las versiones productivas anteriores son desconocidas para este registro.**
- **Lo que sí está.** El texto de cada regla retirada se conserva íntegro en `2f70391` (31 definiciones) y en `1848275`, donde siguen las 3 retiradas en la Fase 2B.

## 2. Metodología vigente (ruta real)

| Paso | Símbolo (en `2f70391`) | Qué hace |
|---|---|---|
| Entrada | [`ejecutar_proyeccion`](https://github.com/estebanojeda0615/SAVIP/blob/2f70391e1b920764e79fa50ec2c2da6b6b572e53/app_icociv/proyeccion/servicio_proyeccion.py#L564-L580) | Valida y delega; retira del objeto público la banda no sustentada (`_retirar_intervalo_de_publicacion`, [L699-L794](https://github.com/estebanojeda0615/SAVIP/blob/2f70391e1b920764e79fa50ec2c2da6b6b572e53/app_icociv/proyeccion/servicio_proyeccion.py#L699-L794)) |
| Backtesting | [`_matriz_rectangular_12_24`](https://github.com/estebanojeda0615/SAVIP/blob/2f70391e1b920764e79fa50ec2c2da6b6b572e53/app_icociv/proyeccion/servicio_proyeccion.py#L824-L909) | 21 candidatos; origen inicial N0 = 12; horizontes 1..24; rectángulo de W* = n − 12 − 24 + 1 orígenes, el mismo para todos los h |
| Selección | [`_seleccionar_modelo_rectangular`](https://github.com/estebanojeda0615/SAVIP/blob/2f70391e1b920764e79fa50ec2c2da6b6b572e53/app_icociv/proyeccion/servicio_proyeccion.py#L912-L970) | RMSErect sobre la muestra común W*×24. Ordena por el SSE exacto ([`_sse_exacto`](https://github.com/estebanojeda0615/SAVIP/blob/2f70391e1b920764e79fa50ec2c2da6b6b572e53/app_icociv/proyeccion/servicio_proyeccion.py#L3063-L3105)) y desempata por el orden del banco. El RMSE informado sale de [`_rmse_desde_sse`](https://github.com/estebanojeda0615/SAVIP/blob/2f70391e1b920764e79fa50ec2c2da6b6b572e53/app_icociv/proyeccion/servicio_proyeccion.py#L3108-L3125) (AS-001) |
| Proyección | [`_ejecutar_proyeccion_base`](https://github.com/estebanojeda0615/SAVIP/blob/2f70391e1b920764e79fa50ec2c2da6b6b572e53/app_icociv/proyeccion/servicio_proyeccion.py#L1054-L1655) | Reajusta el ganador con toda la serie y produce **una** trayectoria de 24 meses. El horizonte consultado solo elige el mes publicado: no cambia el modelo ni la trayectoria |
| Diagnóstico | Misma función y [`evaluar_factibilidad_proyeccion`](https://github.com/estebanojeda0615/SAVIP/blob/2f70391e1b920764e79fa50ec2c2da6b6b572e53/app_icociv/estadistica/analisis_series.py#L540-L792) | Tabla por horizonte (W, RMSE, MAE(h), sesgo). Advertencias descriptivas, como la de escasez de ventanas si W* < `MIN_ITERACIONES_WF` = 6 ([L593](https://github.com/estebanojeda0615/SAVIP/blob/2f70391e1b920764e79fa50ec2c2da6b6b572e53/app_icociv/estadistica/analisis_series.py#L593)). ±MAE(h) es una referencia descriptiva del error histórico, **no** un intervalo con cobertura |
| Intervalo | `_intervalos_prediccion`, `estado_banda` | Se calcula como diagnóstico interno y **no se publica** (bloqueo P0-C en `BLOQUEOS_METODOLOGICOS_VIGENTES`, [L514-L525](https://github.com/estebanojeda0615/SAVIP/blob/2f70391e1b920764e79fa50ec2c2da6b6b572e53/app_icociv/proyeccion/servicio_proyeccion.py#L514-L525)). Si no se puede construir, el punto se entrega igual |

**Protección del motor vigente:**
- los 29 Golden Masters;
- `tests/test_fase1a_selector_rectangular.py`: 7 propiedades, 5 mutantes, AS-001 e integración;
- `tests/test_metodologia_n0_12_h24.py`;
- desde esta fase, `tests/test_fase2c_contratos_vigentes.py` (03, 07).

## 3. Reglas históricas, motivos y trazabilidad

**Cómo se clasifican los motivos.**
- **SS (sin sustento):** el código declara que la regla no tenía fuente.
- **EV (evidencia técnica):** el código describe una demostración o medición. Si la medición es externa, se indica.
- **DM (decisión metodológica):** decisión documentada sin demostración numérica en el repositorio.

| Regla histórica | Fecha según el código | Símbolo y versión que lo conserva | Motivo (tipo) | Prueba histórica | Principio vigente | Prueba vigente | Estado |
|---|---|---|---|---|---|---|---|
| R1. Selección por puntuación compuesta de once coeficientes (backtesting, parsimonia, residuos, interpretabilidad) | Retirada el 09-08-2026 (P0-A) | `seleccionar_modelo_por_evidencia` y 9 auxiliares, [modelos_interpretables.py L280-L597, L1352-L1381](https://github.com/estebanojeda0615/SAVIP/blob/2f70391e1b920764e79fa50ec2c2da6b6b572e53/app_icociv/estadistica/modelos_interpretables.py#L280-L444) | **SS**: «ONCE coeficientes sin ninguna fuente» (docstring) | `test_fundamentacion_metodologica::test_el_selector_retirado_conserva_su_definicion_para_auditoria` (solo existencia) | RMSErect sobre W*×24 | Propiedades y mutantes de la Fase 1A | Retirable en 2D-4 |
| R2. RMSE relativo al mejor de cada h promediado con **peso 1/h** | Retirada el 08-08-2026 (H-9, CIERRE) | `_modelo_trayectoria_consistente`, [1848275 L3287-L3346](https://github.com/estebanojeda0615/SAVIP/blob/1848275e124a0242f57c3582b4cd643c58f0e3f7/app_icociv/proyeccion/servicio_proyeccion.py#L3287-L3346) (retirada del código en la Fase 2B). Sigue en `2f70391`, solo para ordenar benchmarks: `_puntaje_rmse_ponderado` | **SS**: «el peso 1/h no tenía fuente» (docstring). La medición «las dos reglas discrepan en una de diez series» la cita la ficha C-SEL-001 desde un documento **externo** no verificable aquí | `test_seleccion_rmse_global::test_no_hay_peso_por_horizonte` (contraste explícito desde la Fase 2B) | Pesos uniformes por par (origen, h) | `p_pesos_uniformes_por_horizonte` y mutante `peso_1_h` (Fase 1A) | Retirada; contraste documentado |
| R3. Selección por RMSE OOS global sobre la muestra común de pares (objetivo, h) en h=1..h_max (C-SEL-001), con SSE exacto desde P0-D (14-08-2026) | Vigente desde el 08-08-2026 hasta la metodología 12/24 («post-r1-metodologia-12-24, 19/20-08-2026», comentarios L122-L190, L461-L468) | `seleccionar_modelo_por_rmse_oos_global`, `_errores_oos_por_par`, [L3128-L3236](https://github.com/estebanojeda0615/SAVIP/blob/2f70391e1b920764e79fa50ec2c2da6b6b572e53/app_icociv/proyeccion/servicio_proyeccion.py#L3128-L3236) | **DM**: sustituida por el rectángulo común W*×24 (mismos orígenes para todo h). El motivo detallado no consta fuera de los comentarios | `test_seleccion_rmse_global` (14), `test_p0d_rmse_orden_exacto` (11), `test_rmse_global_estable` (4), `test_origen_inicial_backtesting::test_p0d…` (esencial) | Mismo criterio (mínimo SSE exacto, muestra común, desempate) sobre el rectángulo | Fase 1A: 7 propiedades, 5 mutantes, AS-001 | Retirable en 2D-2, tras AS-028 |
| R4. Clasificación por horizonte con vetos (amplitud del IC, MAPE/sMAPE, MASE, ventanas, estabilidad) | El CIERRE del 08-08-2026 retira los vetos de amplitud y métricas. P0-G (12-08 y 14-08-2026) separa punto y banda. P0-H (12-08 y 16-08-2026): `continue` en vez de `break` | `_clasificar_evidencia_horizonte`, `_evaluar_horizontes_proyeccion` y auxiliares, [L2549-L3060](https://github.com/estebanojeda0615/SAVIP/blob/2f70391e1b920764e79fa50ec2c2da6b6b572e53/app_icociv/proyeccion/servicio_proyeccion.py#L2549-L3060) (auxiliares desde L2366) | **SS** en los vetos: «literales internos sin fuente» (`_estado_por_horizonte`). **EV** en P0-G: «Codex lo demostró end-to-end» con n=8 y h=2 (ficha C-HOR-003) | 8 esenciales y unas 20 históricas (03) | La ruta vigente no clasifica: entrega la trayectoria y advierte | `test_fase2c_contratos_vigentes`: escasez y banda no construible | **DECISIÓN PENDIENTE**: la regla «un punto no finito bloquea» solo existe aquí (L2840) |
| R5. Horizonte máximo dinámico (recomendado, escenario, admisible) por prefijo consecutivo | Tope de 30 retirado el 12-08-2026 (P0-H). Prefijo retirado el 16-08 y el 17-08-2026 (P0-H, V-CODEX-3 / R3) | `determinar_horizonte_maximo_estadistico` y auxiliares, [L3401-L3864](https://github.com/estebanojeda0615/SAVIP/blob/2f70391e1b920764e79fa50ec2c2da6b6b572e53/app_icociv/proyeccion/servicio_proyeccion.py#L3401-L3658) | **SS**: el prefijo era una «regla decisoria CRÍTICA sin fuente» (comentario de la prueba). **DM**: alcance fijo de 24 meses | `test_resultado_horizonte_solicitado` (6) y `test_presentacion_resultados` (2), esenciales | `H_OPERATIVO_MAX = 24`; la consulta no recalcula | `test_metodologia_n0_12_h24::test_b`, `test_efg`; golden h11/h23 | Retirable en 2D-1, tras AS-028 |
| R6. Salvaguarda por benchmarks (Drift/Naive) como decisora | Retirada como decisora el 08-08-2026 (CIERRE); corregida el 18-08-2026 | `_aplicar_salvaguarda_benchmarks`, `_puntaje_rmse_ponderado`, [L3239-L3387](https://github.com/estebanojeda0615/SAVIP/blob/2f70391e1b920764e79fa50ec2c2da6b6b572e53/app_icociv/proyeccion/servicio_proyeccion.py#L3269-L3387) | **DM**: diagnóstico, no sustitución (docstring) | `test_remediacion_r2…::test_h2` (esencial) | Un solo modelo: el ganador del rectángulo; `salvaguarda_benchmark.intentada = False` | `test_cierre_semantico_ps01_ps05::test_ps01_*` | Retirable en 2D-3 |
| R7. Tramos de evidencia OOS (0 / 1-2 / ≥3) | El CIERRE del 08-08-2026 deja de degradar. P0-G (16-08-2026): el corte pasa a ser la cota de existencia (ficha C-HOR-003) | `tramo_evidencia_oos`, [L2047-L2057](https://github.com/estebanojeda0615/SAVIP/blob/2f70391e1b920764e79fa50ec2c2da6b6b572e53/app_icociv/proyeccion/servicio_proyeccion.py#L2047-L2057) | **EV/DM** (ficha C-HOR-003) | `test_cierre_semantico…::test_ps03…` (esencial) | Advertencia descriptiva con el número de ventanas si W* < 6 y `_texto_evidencia_oos` | `test_fase2c_contratos_vigentes` (4 casos) | Retirable en 2D-5 |
| R8. Intervalo de predicción publicado (IC80/IC95) | P0-C (15 a 17-08-2026): se retira su publicación; el cálculo sigue como diagnóstico | Código **vigente** (no heredado): `_intervalos_prediccion`, `clasificar_intervalo_por_cobertura`, fichas C-INT-001 a C-INT-005 | **DM**: «no existe una construcción adoptable» (`BLOQUEOS_METODOLOGICOS_VIGENTES`) | Historial P0-C (archivos `test_p0c_*`, no recolectables: falta el módulo `test_p0c_retiro_intervalos_no_sustentados`) | Ningún intervalo publicado; ±MAE(h) descriptivo | Golden del motor (`intervalos_publicados` = None) y `test_escasez_*` | Fuera de AS-003 (AS-014) |

## 4. Recuperación desde Git (sin copiar código a `docs/`)

```bash
git show 2f70391e1b920764e79fa50ec2c2da6b6b572e53:app_icociv/proyeccion/servicio_proyeccion.py
```

```bash
git show 2f70391e1b920764e79fa50ec2c2da6b6b572e53:app_icociv/estadistica/modelos_interpretables.py
```

```bash
git show 1848275e124a0242f57c3582b4cd643c58f0e3f7:app_icociv/proyeccion/servicio_proyeccion.py
```

- **Líneas exactas de cada definición:** en `01_INVENTARIO_DEFINICIONES_AS003.csv` (columna `referencia_permanente`, enlace a `blob/<SHA>/…#Lini-Lfin`).
- **Las 3 retiradas en la Fase 2B** están en `1848275`: `_rmse_global_estable` L3128-L3157, `_modelo_consistente_desde_comparativo` L3271-L3284 y `_modelo_trayectoria_consistente` L3287-L3346.
- **Las 6 retiradas en la Fase 2A** están en `c9166c6` (Fase 2A, 03 §2).
- **Los commits se conservan** mientras existan las ramas de mantenimiento y el tag `v1.1.2-rc.1` (`6672529`, que también contiene todas las funciones).

## 5. Riesgos de lectura

- **Fichas que citan código heredado.** Las fichas de `criterios.py` con ubicación en código heredado (C-SEL-001, C-ALC-001, C-ALC-002, C-ALC-003, C-SAL-001 y C-BEN-002) son **registro documental**: su función citada no se ejecuta. La regla que decide hoy es la de §2 (04 describe el parche propuesto).
- **C-HOR-003.** Habla de ventanas por horizonte (`n − N0 − h + 1`, ventana expansiva). La ruta vigente usa un rectángulo único (`W* = n − N0 − H + 1`). No se homologan: la ficha describe el diseño anterior.
- **Dos umbrales distintos.** `tramo_evidencia_oos` (heredada) usa 3. La advertencia vigente de escasez usa 6 (`MIN_ITERACIONES_WF`). La ficha C-HOR-003 declara ambos como «cortes descriptivos».
- **Intervalos e IC95.** Su cálculo es vigente pero **no se publica** (P0-C). Ninguna ficha C-INT autoriza a decir que SAVIP entrega un intervalo.
- **Comentarios engañosos en código vigente.** Hay comentarios que atribuyen un bloqueo a `_clasificar_evidencia_horizonte`, que la ruta no llama:
  - [L1502](https://github.com/estebanojeda0615/SAVIP/blob/2f70391e1b920764e79fa50ec2c2da6b6b572e53/app_icociv/proyeccion/servicio_proyeccion.py#L1502): «vive en `_clasificar_evidencia_horizonte`»;
  - [L4979](https://github.com/estebanojeda0615/SAVIP/blob/2f70391e1b920764e79fa50ec2c2da6b6b572e53/app_icociv/proyeccion/servicio_proyeccion.py#L4979): «siguen bloqueando en `_clasificar_evidencia_horizonte`».

  Leídos hoy, describen un bloqueo que **no ocurre** en la ruta vigente (decisión 1 de 06 §3). Su corrección es de la 2D-6.
- **Prueba t de la media residual (C-RES-002).** `contrastar_media_residual` es alcanzable desde producción según el grafo. Es un diagnóstico informativo («no bloquea, no degrada», según la ficha). No se verificó su ejecución en tiempo real en esta fase.

## 6. Lo que no se sabe

- **Las versiones de SAVIP** en las que R1–R7 fueron productivas: anteriores a `dfdb3e0`.
- **El contenido de los documentos externos** citados por nombre (`CIERRE_FINAL_H9_…`, `FHG_TANDA2_HALLAZGO_B_OVERFLOW_SELECTOR.md` y los informes V-CODEX). No están en el repositorio.
- **La fecha exacta** en que `seleccionar_modelo_por_rmse_oos_global` dejó la ruta productiva. Consta por los comentarios entre el 19 y el 20-08-2026, sin otra fuente.
