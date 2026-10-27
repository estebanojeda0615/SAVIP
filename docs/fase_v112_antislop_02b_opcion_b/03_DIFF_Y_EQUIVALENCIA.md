# 03 · Diff y equivalencia

## 1. Commits

| Commit | Qué | Por qué separado |
|---|---|---|
| `73e565c` | `test(AS-003)`: tratamiento G5 de las pruebas históricas (02 §2) | Válido antes y después del retiro: con el código de `1848275` pasa igual (4 / 13 / 15 / 22 más el FAIL previo). Revertible por sí solo |
| `54f7ccf` | `refactor(AS-003)`: retiro de las 3 funciones, adaptación de la prueba esencial y de `test_la_regla_retirada_ya_no_se_invoca_en_la_ruta_productiva` | Las dos pruebas **exigen la ausencia** de las funciones, así que no pueden ir en un commit anterior al retiro: lo dejarían en rojo. Tampoco sirve hacerlas condicionales, porque silenciaría la aserción. Revertir este commit restaura las funciones y las dos pruebas a la vez |
| `10f1d0d` | `ci`: añade la rama al filtro del workflow | — |
| commit de documentación | Documentos 00–05, evidencias y excepción en `.gitignore` | — |

## 2. Líneas eliminadas de verdad (`git diff --numstat 1848275 10f1d0d`)

| Categoría | Archivo | − | + | Neto |
|---|---|---|---|---|
| **Producción: definiciones** | `servicio_proyeccion.py` | 104 | 0 | −104 |
| Producción: líneas en blanco separadoras | `servicio_proyeccion.py` | 6 | 0 | −6 |
| **Producción: imports** | — | **0** | 0 | 0 (ninguno era exclusivo) |
| **Total producción** | | **110** | 0 | **−110** (de 5 981 a 5 871 líneas) |
| Prueba esencial | `test_fase1a_selector_rectangular.py` | 2 | 6 | +4 |
| Pruebas históricas | `test_rmse_global_estable.py` (55/4), `test_seleccion_rmse_global.py` (17/17), `test_cierre_metodologico.py` (11/4), `test_p0d_rmse_orden_exacto.py` (2/2) | 85 | 27 | −58 |
| **Total pruebas** | | 87 | 33 | **−54** |
| Workflow | `fase0-pruebas.yml` | 0 | 1 | +1 |
| Documentación | `docs/fase_v112_antislop_02b_opcion_b/` y `.gitignore` | — | — | Solo se añade |

**Comprobaciones del diff.**
- `git diff --check` no da avisos.
- No cambian `aplicacion.py`, `packaging/`, `VERSION`, `requirements*`, `scripts/`, `pruebas/` ni `tests/fixtures/` (golden y tolerancias incluidos).

## 3. Pruebas tras cada lote (mismo equipo y entorno)

**Tras `73e565c`, con el código de la base:**
- los 4 archivos históricos dan 4 PASS, 13 PASS, 15 PASS, y 22 PASS más 1 FAIL previo;
- `pyflakes` deja los archivos de prueba con los mismos avisos que antes. Se retiraron `math` y `numpy` de `test_rmse_global_estable.py`, que solo usaban T1–T6b.

**Tras `54f7ccf`, en la copia limpia `despues`:**
- `compileall` de `app_icociv`, `aplicacion.py`, `scripts`, `pruebas` y `tests`: OK;
- todos los módulos importan y `VentanaPrincipal` arranca en Qt offscreen;
- `tests/test_fase1a_selector_rectangular.py`: **35/35 PASS**. Incluye los 16 casos AS-001, los de 1 ULP, empate, muestra común, pesos y los 5 mutantes, y la prueba adaptada;
- 29 Golden Masters más focalizadas (`test_metodologia_n0_12_h24`, `test_horizonte_24_ic95_mae`, `test_presentacion_resultados`, `test_resultado_horizonte_solicitado`, `test_fundamentacion_metodologica`, `test_cierre_semantico_ps01_ps05`, `test_vocabulario_vc`, `test_remediacion_r2_h1_h2_h3_h7`, `test_nmin_adversarial`, `test_origen_inicial_backtesting` y `test_auditoria_formulas_estadisticas`): **176/176 PASS**;
- los 4 históricos dan los mismos estados por id, salvo los 9 retirados (02 §2);
- `pruebas/prueba_estadistica.py` y `pruebas/ejemplo_uso.py` dan **salida idéntica** a la base, con el mismo `ci_lo=None` previo en `ejemplo_uso`;
- sensibilidad de la prueba esencial adaptada: confirmada (02 §1).

## 4. Huella semántica exacta

**Herramienta.** La misma de la Fase 2A, sin cambios (`docs/fase_v112_antislop_02a_as003/evidencia/huella_semantica.py`). Captura:
- los 5 escenarios con horizontes 1, 11, 23 y 24: 20 casos;
- el resultado completo de `ejecutar_proyeccion` (65 claves);
- el SSE exacto (`Fraction`) de los 21 candidatos y los pares W*×24;
- la economía, el empalme y los rechazos.

**Comparación.** Exacta, sin tolerancia.

| Captura | SHA-256 | Diferencias exactas |
|---|---|---|
| Base `1848275`, captura 1 | `d6be699b700b3fa3379c743cc9d0ccbf5c185cacfa228208dbb95c2735370191` | — |
| Base `1848275`, captura 2 | `d6be699b…` (idéntico) | 0 frente a la captura 1 |
| Después `54f7ccf` | `d6be699b…` (idéntico) | **0** |

Es el mismo SHA-256 que en las Fases 2A y la línea base de `c9166c6`. Los JSON (~155 MB) se conservan localmente, fuera de Git, en `C:\Pruebas SAVIP\Fase2B\`.
