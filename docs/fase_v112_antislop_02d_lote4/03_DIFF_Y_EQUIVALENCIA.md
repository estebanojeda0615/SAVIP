# 03 · Diff y equivalencia

## Commits

| Commit | Contenido |
|---|---|
| `2b89a6c` | `refactor(AS-003)`: retiro de las 10 definiciones y de los 2 imports huérfanos, más la prueba esencial que exigía su existencia. Va en el mismo commit porque esa prueba falla en cuanto la función desaparece: separados, el primer commit quedaría en rojo |
| `2fa128d` | `ci`: añade la rama al filtro del workflow (+1 línea) |
| Commit de documentación | Esta carpeta y la excepción en `.gitignore` |

## Líneas (`git diff --numstat 83549e7 2fa128d`)

| Categoría | Archivo | − | + |
|---|---|---|---|
| Producción: definiciones | `app_icociv/estadistica/modelos_interpretables.py` | 332 | 0 |
| Producción: líneas en blanco separadoras | ídem | 20 | 0 |
| Producción: imports (`UMBRAL_RRMSE_PEOR_BENCHMARK`, `TOLERANCIA_RRMSE_BENCHMARK`) | ídem | 2 | 0 |
| **Total producción** | | **354** | **0** |
| Prueba esencial | `tests/test_fundamentacion_metodologica.py` | 5 | 6 (comentario de trazabilidad) |
| Workflow | `.github/workflows/fase0-pruebas.yml` | 0 | 1 |

**Archivos que no cambian:** `criterios.py`, `servicio_proyeccion.py`, `validacion_series.py`, `aplicacion.py`, `packaging/`, `VERSION`, `requirements*`, `pruebas/`, `scripts/` y `tests/fixtures/` (golden y tolerancias).

`git diff --check` no da avisos. El módulo pasa de 1 381 a 1 027 líneas.

## Equivalencia (mismo equipo y entorno)

| Comprobación | Antes (`83549e7`) | Después (`2fa128d`) |
|---|---|---|
| Huella semántica exacta: 20 casos motor×horizonte, SSE de los 21 candidatos, H1–H24, MAE(h), economía y rechazos | SHA-256 `d6be699b…`; dos capturas con 0 diferencias | **SHA-256 `d6be699b…` idéntico, 0 diferencias** |
| `compileall` de `app_icociv`, `aplicacion.py`, `scripts`, `pruebas` y `tests` | — | OK |
| Importar todos los módulos de `app_icociv` y `aplicacion`; `VentanaPrincipal` en Qt offscreen | — | OK |
| 29 golden, `test_fase1a_selector_rectangular` (35, con AS-001), `test_fase2c_contratos_vigentes` (7), `test_fundamentacion_metodologica`, `test_nmin_adversarial`, `test_origen_inicial_backtesting`, `test_auditoria_formulas_estadisticas` y `test_metodologia_n0_12_h24` | — | **143/143 PASS** |
| `test_integracion_fhg` (histórica) | 2 FAIL previos (`h3`, `h4`) y 17 PASS | Iguales: mismos 2 ids |
| `pruebas/prueba_estadistica.py` | Código 0 | **Código 0, salida idéntica** |
| Grafo | 817 definiciones | 807: ninguna definición nueva inalcanzable y ningún cambio de alcance |
