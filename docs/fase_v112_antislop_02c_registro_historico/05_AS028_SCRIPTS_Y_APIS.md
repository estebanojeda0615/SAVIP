# 05 · AS-028: scripts heredados y API secundaria

**Estado.** Esta fase **no modifica** `pruebas/`. El estado de partida se midió en una copia limpia de `2f70391`, con los datos sintéticos del repositorio y sin datos DANE. El destino que se propone para la 2D requiere autorización.

## 1. Consumidores de definiciones heredadas fuera de `tests/`

| Script | Símbolos heredados que usa | Cómo se ejecuta | Estado medido en `2f70391` |
|---|---|---|---|
| `pruebas/prueba_horizonte_dinamico_ui_reportes.py` (1 009 líneas, 30 funciones `test_*`) | `determinar_horizonte_maximo_estadistico` (3 pruebas) y `seleccionar_modelo_por_rmse_oos_global` (1 prueba) | `pytest pruebas/prueba_horizonte_dinamico_ui_reportes.py`, o `python …` (`main()`). Ningún perfil de `scripts/pruebas_fase0.py` lo incluye | **22 PASS / 8 FAIL**, todos previos |
| `pruebas/ejemplo_uso.py` | Ninguno heredado: usa `servicio_proyeccion.ejecutar_analisis` (API vigente) | `PYTHONPATH=. python pruebas/ejemplo_uso.py <anexo>` | `ejecutar_analisis` responde. El script falla después en la línea 87, al formatear `proj['ci_lo']`, que vale `None` desde P0-C (código 1) |
| `pruebas/prueba_estadistica.py` | Ninguno heredado: usa `validacion_series.validar_serie` / `detectar_outliers_extremos`, que se conservan | Igual, con un anexo sintético de 40 meses | Código 0 |
| Otros 6 archivos de `pruebas/` (9 en total) | Ninguno de los 31 símbolos (búsqueda textual de los 27 nombres no genéricos) | — | No afectados por AS-003 |

**Detalle de `prueba_horizonte_dinamico_ui_reportes.py`.**

| Prueba | Heredado | Estado | Causa del fallo, si falla |
|---|---|---|---|
| `test_horizonte_maximo_no_es_18_si_h18_no_cumple` | `determinar_…` | PASS | — |
| `test_mensaje_no_recomendables_no_imprime_lista_vacia` | `determinar_…` | PASS | — |
| `test_h18_no_se_redacta_como_intervalos_aceptables` | `determinar_…` | FAIL | Espera «Horizonte máximo recomendado: 12» en el texto de informe; la ruta vigente ya no lo redacta |
| `test_el_modelo_entregado_es_el_de_minimo_error_oos_global` | `seleccionar_modelo_por_rmse_oos_global` | PASS | — |
| `test_horizonte_25_estable_…`, `test_horizonte_25_erratico_…`, `test_horizonte_dinamico_con_serie_drift`, `…_holt` | — | FAIL | `ValueError`: horizonte > 24 (el alcance vigente es 24) |
| `test_parametros_drift_receta_y_csv_reproducible`, `test_pdf_y_docx_contienen_horizontes_con_escenario`, `test_docx_777_separa_advertencias_globales_y_horizonte` | — | FAIL | Esperan textos de informe anteriores a 12/24 («Horizonte estadístico admisible», «máximo permitido como escenario») |
| Los otros 19 | — | PASS | — |

## 2. Clasificación y destino propuesto (2D)

| Script | Propósito real | Contrato utilizable | Destino propuesto |
|---|---|---|---|
| `prueba_horizonte_dinamico_ui_reportes.py` | Prueba manual de desarrollo de la época del horizonte dinámico. 8 de sus 30 expectativas ya no corresponden a la metodología 12/24 | 19 pruebas pasan sin heredado (UI, catálogo, gráficas, intervalos internos). **No se ha verificado** si duplican cobertura de `tests/` | **DECISIÓN PENDIENTE (AS-028).** Opción A: retirar el script completo, con trazabilidad a `2f70391`. Opción B: migrar a `tests/` solo las pruebas vigentes sin cobertura equivalente (requiere revisarlas una por una) y retirar las 4 heredadas y las 8 obsoletas. **Mientras no se decida, los lotes 2D-1 y 2D-2 son NO-GO** |
| `ejemplo_uso.py` | Ejemplo de uso de la API `ejecutar_analisis` | La API funciona; el ejemplo está roto por `ci_lo=None` | Modernizar en AS-028: imprimir la trayectoria y ±MAE(h) descriptivo en vez de `ci_lo`/`ci_hi`. Parche abajo. **Conservar `servicio_proyeccion.ejecutar_analisis`** |
| `prueba_estadistica.py` | Manual de validación estadística | Funciona | Mantener; no le afecta ningún lote |

### Parche propuesto para `pruebas/ejemplo_uso.py` (NO aplicado)

```diff
-print(f"IC 95%:               [{proj['ci_lo']:.4f}, {proj['ci_hi']:.4f}]")
+# P0-C: SAVIP no publica intervalo de predicción; ±MAE(h) es una referencia descriptiva del error histórico.
+print("Intervalo de predicción: no se publica (P0-C)")
```

Antes de aplicarlo en AS-028 hay que comprobar las líneas siguientes del script, que pueden usar otras claves retiradas.

## 3. API secundaria `servicio_proyeccion.ejecutar_analisis`

- **Estado:** contrato documentado (docstring con ejemplo) y único importador, `pruebas/ejemplo_uso.py`. La interfaz usa `ControladorPrincipal.ejecutar_analisis`, que es otra función.
- **Dependencias:** solo llama a la ruta vigente (`cargar_todas_tablas`, `resolver_fila_seleccionada`, `construir_serie`, `ejecutar_proyeccion`). Ningún lote 2D la toca.
- **Recomendación:** conservar. Cambiarla requiere una autorización distinta (Fase 2A, 02 §3).

## 4. Otros consumidores encontrados (no son scripts)

- **`app_icociv/reportes/generador_reportes.py`** lee `horizonte_maximo_recomendado`, `base_horizonte_maximo_recomendado` y claves afines de `horizonte_info`. Solo las producía `determinar_horizonte_maximo_estadistico`, o `_resultado_sin_proyeccion` con valor 0.
  - Ese módulo tiene 28 definiciones inalcanzables, que son el generador de informes antiguo (AS-004).
  - Retirar `determinar_…` no rompe su importación, porque lee con `.get(...)`. Pero conviene resolver AS-004 antes o junto con 2D-1 para no dejar lecturas de claves que nadie produce.
- **Archivos de `tests/` de estilo script, que pytest no recoge:**
  - `test_p0c_objeto_publico_sin_intervalo.py` y `test_p0c_regresion_negativa_c2.py`: error de importación, porque no existe `tests.test_p0c_retiro_intervalos_no_sustentados`;
  - `test_regresiones_auditoria_independiente_bghc.py` y `test_residuales_auditoria_independiente_r3.py`: sin funciones `test_`.
  - Importan `_clasificar_evidencia_horizonte`, `_mayor_horizonte_permitido` y `tramo_evidencia_oos`.
  - Hoy no se ejecutan, así que no bloquean ningún perfil. Pero dejarían de importarse aún más tras la 2D, y se deben decidir con AS-007 (03, filas «NO RECOLECTADA»).
