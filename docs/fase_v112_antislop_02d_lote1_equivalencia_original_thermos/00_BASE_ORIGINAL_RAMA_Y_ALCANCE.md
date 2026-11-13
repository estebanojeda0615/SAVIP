# 00 · Base, original empaquetada, rama y alcance (G0)

## 1. Referencias

| Referencia | Identificador | Uso |
|---|---|---|
| **V1.1.2 ORIGINAL empaquetada** (antes de Anti-Slop) | Fuente `66725293f304426ae6edf144b8f4dadbcbeefe10` (árbol `app_icociv` `b484bd4f…`). Tag `v1.1.2-rc.1`, objeto anotado `08f364b` que apunta a `6672529`. ZIP `SAVIP_1.1.2_Portatil_Windows_x64.zip`, SHA-256 `cee5897f82753d5ca1b6650023da81384bc1bfb50b5a5468ddbb26e5e7a94600` | Referencia principal, de solo lectura. En 2D-2 se demostró que el bytecode del EXE coincide con esta fuente (87/87 módulos `app_icociv` más `aplicacion`) (`docs/fase_v112_antislop_02d_lote2_equivalencia_original_thermos/`). **En esta fase no se ejecutó el EXE**: se ejecutó su fuente `6672529` con el mismo entorno |
| V1.1.1 | `dfdb3e046126093e23b045147f789fbc52961a73` (árbol `app_icociv` `f8f50d4e…`) | Referencia secundaria (comparación D, 04) |
| **Base inmediata** | `8e5a62b00fbdac3819c755e509236c174ebcb78f` (`maintenance/v1.1.2-as028-preparacion-2d1-as004-thermos`), CI [43136025902](https://github.com/estebanojeda0615/SAVIP/actions/runs/43136025902) verde en el 1.er intento (809 pruebas, 0 fallos) | Referencia terciaria; exige 0 diferencias |
| **AS-001** | Única excepción autorizada | La original aborta con `OverflowError` al convertir una SSE extrema a `float`. Este lote no la toca |

## 2. Rama y aislamiento

| Dato | Valor |
|---|---|
| Rama nueva | `maintenance/v1.1.2-fase2d-lote1-equivalencia-original-thermos`, creada **exactamente** desde `8e5a62b`. No existía en el remoto |
| Clon | `C:\Users\Esteban\Desktop\SAVIP_V112_LOTE2D1`, nuevo, con `git status` limpio al empezar |
| Copias de prueba | `C:\Pruebas SAVIP\L1D1\base` (`8e5a62b`) y `C:\Pruebas SAVIP\L1D1\final_<sha>` (último commit de código), extraídas con `git archive` o copia, sin `.git` y fuera del repositorio. Fuentes del oráculo en `C:\Pruebas SAVIP\L2\fuentes\<sha7>`, cada una con su `.fuente_git.txt` |
| Identidad | Esteban Ojeda `<346522303+estebanojeda0615@users.noreply.github.com>` como autor y committer, sin trailers |
| No tocado | `main`, `develop/v1.1.2`, el tag y la release `v1.1.2-rc.1`, el ZIP y el EXE, las ramas anteriores, el repositorio de desarrollo del usuario y los clones de fases previas |

**`git ls-remote` al empezar** (2026-11-12, 18:2x UTC):

| Ref | SHA |
|---|---|
| `maintenance/v1.1.2-as028-preparacion-2d1-as004-thermos` | `8e5a62b` |
| `develop/v1.1.2` | `6672529` |
| `main` | `dfdb3e0` |
| tag `v1.1.2-rc.1` | `08f364b`, que apunta a `6672529` |

## 3. Estado de partida verificado

| Elemento | Valor en `8e5a62b` | Comprobación |
|---|---|---|
| Árbol `app_icociv` | `f4f0a0c752e9…` | Idéntico a `102f194`, `56d9562` y `49106f9` (2D-2) |
| Árbol `tests` | `e17042e6ae25…` | Idéntico a `102f194` y `56d9562`, que es donde se midió AS-028 |
| Árbol `tests/fixtures` | `a4218d636f2f…` | Sin cambios en esta fase |
| `requirements-lock.txt` / `requirements-test.txt` | `ab30ed94…` / `c3c5679e…` | Igual que en AS-028 |
| Runner `scripts/pruebas_fase0.py` | `1f679da5…` | Sin cambios |
| Arnés del oráculo (`C:\Pruebas SAVIP\L2\oraculo`) | `oraculo.py` `42941b93…`, `golden_exacto.py` `db633a2e…`, `umbral_as001.py` `812cf944…` | `oraculo.py` es idéntico al versionado en 2D-2 |
| Entorno | Python 3.12.10, PySide6 6.11.0, numpy 2.4.2, pandas 2.3.3, statsmodels 0.14.6. `pip check` OK. Claude Code 2.1.238; Thermos 1.1.0 | — |

## 4. Línea base G0 (antes de editar)

| Comprobación | Resultado | Evidencia |
|---|---|---|
| Perfil esencial | **809/809**, 0 fallos en la 1.ª ejecución: CI 43136025902 sobre este mismo SHA. Además, el JUnit local de AS-028, sobre el mismo árbol de `tests` y `app_icociv` | `evidencia/esenciales_base_resumen.txt` |
| Golden / AS-001 | **29/29** y **16/16**, dentro del perfil. Golden con **tolerancia cero**: 0 diferencias. Umbral AS-001 idéntico al de AS-028 | `evidencia/oraculo/golden_exacto_8e5a62b.txt` y `umbral_as001_8e5a62b.txt` |
| Huella semántica | 20/20, **0 diferencias**. SHA `d6be699b700b3fa3379c743cc9d0ccbf5c185cacfa228208dbb95c2735370191` | `evidencia/huella_base.txt` |
| Oráculo de 66 escenarios | `8e5a62b` r1, **ejecutado**: idéntico a AS-028 (`7993060`; hash de datos `766a34b8…`) | 04 |
| Comparación B (original → base) | `6672529` r4, **ejecutado**, frente a `8e5a62b`: **solo AS-001** | 04 |
| `--collect-only tests` | 1 036, con los 3 errores históricos | `evidencia/base_collect.txt` |
| Script manual | 26 tests, 19 PASS / 7 FAIL | `evidencia/script_base_pytest.xml` |
| Histórica `test_cierre_metodologico` | 21 PASS / 1 FAIL. El fallo es el preexistente `test_no_hay_modelo_por_horizonte` | `evidencia/cierre_base.txt` |
| Simulación de ausencia, sin editar producción (G4.0) | Solo fallan los 18 esenciales previstos y la histórica de la cascada. Script idéntico. Sonda AS-004 con 0 diferencias. **Ningún consumidor sin catalogar** | 01 §4 |

## 5. Alcance

| Autorizado | No autorizado |
|---|---|
| Retirar **exactamente** las 6 definiciones de `servicio_proyeccion.py` | Cualquier otra línea de producción. Los auxiliares compartidos `_tipo_uso_horizonte` y `_mayor_horizonte_permitido`, y todo 2D-3 |
| 8 bajas esenciales; quitar el nombre del `import` (9 vigentes intactos); la guarda de la Fase 1A, en el mismo commit; una aserción de la histórica | `_evaluacion_horizonte` del script; auxiliares e imports ajenos; `test_fase2c_contratos_vigentes`; `tests/fixtures`; Golden; tolerancias |
| Una entrada en el workflow, una en `.gitignore` y la documentación | AS-004 (`generador_reportes`, las 17 columnas del CSV, `mensaje_ui`…), AS-024 (`criterios.py`, C-ALC-002), P0-C, 2D-3, 2D-6, merge, PR, tag, release, EXE y ZIP |
