# 07 · Equivalencia estricta con la V1.1.2 original y con la fase previa (G5)

## 1. Producción y áreas vetadas

| Comprobación | Resultado |
|---|---|
| `git diff 102f194 56d9562 -- app_icociv aplicacion.py VERSION packaging requirements-lock.txt requirements-test.txt tests/fixtures scripts tests` | **Vacío** |
| Archivos cambiados (`git diff --stat 102f194 56d9562`) | `.github/workflows/fase0-pruebas.yml` (+1), `.gitignore` (+1) y `pruebas/prueba_horizonte_dinamico_ui_reportes.py` (+9/−63) |
| Árbol Git de `app_icociv` | `f4f0a0c752e9…` en `102f194`, `7993060` y `56d9562`. Es el mismo de `49106f9` (último commit productivo de 2D-2) |
| Parche 3c_a | **Intacto**: `tests/` no cambia. `esperar_ajuste_de_ancho` y los 4 ids de `test_interaccion_fase_3c_a` siguen en PASS |
| `git diff --check` | Sin errores en cada commit |

## 2. Pruebas sobre copias limpias

Las copias de la base (`102f194`) y del final (`7993060`, mismo código ejecutable que `56d9562`) se generaron sin `.git` y fuera del repositorio.

| Comprobación | Base `102f194` | Final | Conclusión |
|---|---|---|---|
| Perfil esencial | 809/809 PASS, 0 fallos en la 1.ª ejecución, sin intermitentes | **809/809 PASS**, 0 fallos en la 1.ª ejecución, 0 errores, 0 skip/xfail, sin intermitentes (2 040 s) | **Conjunto de ids idéntico**: 0 altas, 0 bajas y 0 cambios (`evidencia/comparacion_ids_base_final.txt`). No se autoriza ninguna alta ni baja esencial, y no hubo ninguna |
| Golden Masters (en el perfil) | 29/29 | **29/29** | Fixtures y tolerancias intactos (diff vacío en `tests/fixtures`) |
| Golden con **tolerancia cero** (`golden_exacto.py`, arnés de 2D-2) | — | **0 diferencias exactas** | `evidencia/oraculo/golden_exacto_7993060.txt` |
| AS-001 (en el perfil) | 16/16 | **16/16** | Sin extender la excepción |
| Umbral AS-001 (`umbral_as001.py`) | — | Idéntico, línea a línea, al de `5478958` (2D-2) | `evidencia/oraculo/umbral_as001_7993060.txt` |
| Huella semántica: 20 escenarios, SSE de los 21 candidatos, H1-H24, MAE(h), economía, empalme, sesiones y rechazos | 20/20 frente a AS-028/2D-2 | **20/20, 0 diferencias** | SHA-256 `d6be699b700b3fa3379c743cc9d0ccbf5c185cacfa228208dbb95c2735370191` **idéntico** (`evidencia/huella_final.txt`) |
| `--listar` | 809 / 214 / 13 | 809 / 214 / 13 | Igual |
| `pytest --collect-only -q tests` | 1 036, con 3 errores históricos | 1 036, con **los mismos 3**: `fase_4e_b`, `p0c_objeto_publico` y `p0c_regresion_negativa_c2` | **0 errores nuevos**. P0-C no se reabre |
| `compileall` (`pruebas`, `app_icociv`, `aplicacion.py`, `tests` y `scripts`) | — | Código 0 | |
| Importación de los 86 módulos de `app_icociv` más `aplicacion` y construcción de `VentanaPrincipal` | — | OK | `evidencia/final_imports.txt` |
| `pip check` | OK | OK | |
| Escrituras en disco de las capturas | Ninguna | Ninguna | `evidencia/escrituras_base.txt` |

## 3. Oráculo ampliado de 66 escenarios: **ejecutado de nuevo en esta fase**

**Arnés:** es el mismo de 2D-2. `oraculo.py` es idéntico byte a byte a `docs/fase_v112_antislop_02d_lote2_equivalencia_original_thermos/evidencia/scripts/oraculo.py`, y la copia externa del arnés tiene el SHA-256 registrado en `arnes_sha256.txt`. Lee las fuentes extraídas con `git archive`, que llevan su `.fuente_git.txt` (SHA del commit y del árbol `app_icociv`). Compara con `float.hex` todas las claves de resultados, estadísticas, trayectorias, economía, sesiones y exportables.

| Comparación | Capturas | Resultado |
|---|---|---|
| Determinismo del final | `7993060` r1 frente a r2 | **66/66 idénticos**. Hash de datos `766a34b8a8968b02c1db35fb2dcdb7a94ebbf61b9450f70e415985e69ca1bb3f` |
| **B. Fase previa → final** | `102f194` r1 frente a `7993060` r1, **las dos ejecutadas en esta fase** | **66/66 idénticos, 0 diferencias.** Mismo hash de datos |
| Continuidad con 2D-2 | `5478958` (2D-2) frente a `7993060` | 66/66 idénticos, mismo hash |
| **A. V1.1.2 original → final** | `6672529` r3 (**ejecutada en esta fase**) frente a `7993060` r1 | **64/66 idénticos.** Diferencias: (1) `series_extra.extremo_finito_x1e150` = **AS-001** (la original lanza `OverflowError` y Anti-Slop produce un resultado), y (2) `gui_sesion_exportables`, solo por un salto de línea del texto del PDF de sesión (§3.1) |
| A, contra la otra captura de la original | `6672529` r2 (2D-2) frente a `7993060` r1 | **65/66.** Solo AS-001 |
| Determinismo de la original | `6672529` r1 = r3, ≠ r2 | **La propia original varía** el salto de línea del PDF entre ejecuciones (`evidencia/oraculo/cmp_6672529_r1_r2.txt`, ya registrado en 2D-2) |
| **C. V1.1.1 → V1.1.2 original** | `dfdb3e0` frente a `6672529` | **Evidencia heredada de 2D-2, no repetida** (`evidencia/oraculo/cmp_6672529_dfdb3e0.txt`). Ninguna de las dos versiones cambia, así que la comparación sigue siendo válida. Las diferencias de etiqueta de versión de la UI no son numéricas |

### 3.1 El salto de línea del PDF no es una diferencia funcional

Las dos líneas afectadas son `texto[122]` y `texto[123]`:
- en una variante, «…Proyecciones visibles guardadas: 2. Registros» / «calculados: 3.»;
- en la otra, «…Proyecciones visibles guardadas: 2.» / «Registros calculados: 3.».

Al unir las líneas y normalizar los espacios, **el texto es idéntico en las 7 capturas** (`6672529` r1/r2/r3, `102f194`, `7993060` r1/r2 y `5478958`).

La causa es el identificador del análisis activo (`uuid4().hex`, `proyecciones_icociv.py:543`). El oráculo lo sustituye por `<ID1>`. Siempre tiene 32 caracteres, pero el **ancho renderizado** con fuente proporcional varía según sus caracteres y, con él, el corte de la línea en el PDF. La V1.1.2 original lo muestra **ella sola**: r1 ≠ r2.

El §8.2 del prompt admite excluir exactamente esto («saltos de línea de PDF sin cambio de texto»). No se normalizó ningún número, fórmula ni resultado.

**Conclusión:** 0 diferencias frente a `102f194`. Frente a la V1.1.2 original, la única diferencia es **AS-001**. No hay ninguna excepción nueva.

**SHA-256 de las capturas y fuentes:** `evidencia/oraculo/sha256_capturas.txt`. El EXE **no** se ejecutó: se ejecutó su fuente `6672529`, cuya correspondencia de bytecode (87/87) se demostró en 2D-2.

## 4. Salidas AS-004 con 2D-1 visible y oculto

| Comparación | Casos | Resultado |
|---|---|---|
| Sonda base `102f194` frente a final | 29: 7 series × h ∈ {1, 12, 18, 24}, más la sesión heredada | **0 diferencias** en `proyeccion_generada`, claves históricas de `horizonte_info`, 17 columnas históricas del CSV, fuente del encabezado y llamadas (`evidencia/sonda_base_vs_final.txt`) |
| Sonda base frente a **final con las 6 definiciones 2D-1 borradas** (stubs que fallan si alguien los llama) | 29 | **0 diferencias, 0 excepciones** (`evidencia/sonda_oculto.txt`) |

## 5. Script histórico: comparación por id

| | Base `102f194` | Final `56d9562` | Final con 2D-1 oculto |
|---|---|---|---|
| Tests | 29 | 26 | 26 |
| PASS / FAIL | 21 / 8 | **19 / 7** | 19 / 7 |
| Bajas | — | 3, las autorizadas: `test_horizonte_maximo_no_es_18…` (PASS), `test_mensaje_no_recomendables…` (PASS) y `test_h18_no_se_redacta…` (FAIL) | — |
| Altas / cambios de estado | — | **0 / 0** | Idéntico al final visible, id a id |
| Ejecución directa | Se detiene en el 2.º test (`ValueError` h=25), código 1 | **Igual** | — |

Los 7 FAIL históricos que se conservan son los mismos ids, con la misma causa y sin cambios de expectativa: h25 estable, h25 errático, parámetros drift, pdf/docx con escenario, drift, holt y docx 777 (`evidencia/script_56d9562_pytest.xml`). Ningún FAIL histórico desaparece salvo la baja justificada de `test_h18…`.

## 6. GitHub Actions (`fase0-pruebas`)

| Run | Commit | Resultado | 1.ª ejecución | Reintento interno | Observaciones |
|---|---|---|---|---|---|
| [43086981441](https://github.com/estebanojeda0615/SAVIP/actions/runs/43086981441), intento 1 | `7993060` | **success** | 809 pruebas, **0 fallos** | Ninguno («Intermitentes: ninguna») | Mismo código ejecutable que `56d9562`: el CI no ejecuta `pruebas/` |
| [43087996118](https://github.com/estebanojeda0615/SAVIP/actions/runs/43087996118), **intento 1** | `56d9562` (**último commit de código**) | **failure, de infraestructura** | El paso «Tests autocontenidos esenciales» terminó en success. El log no se pudo descargar («The specified blob does not exist») | — | Falló el paso «Publicar el resultado JUnit» (`upload-artifact`) con la anotación «Failed to CreateArtifact: Received non-retryable error: (404) Not Found: workflow run not found». Job de 65 min (`evidencia/ci/run_43087996118_intento1_56d9562.txt`) |
| [43087996118](https://github.com/estebanojeda0615/SAVIP/actions/runs/43087996118), **intento 2** (relanzamiento **único**, autorizado expresamente por el propietario el 2026-11-12 a las 00:47 UTC) | `56d9562` | **success**, de 00:48 a 01:34 UTC. Todos los pasos en success, incluida la publicación del JUnit | **809 pruebas, 0 fallos**, 0 errores, 0 omitidas | Ninguno («Intermitentes: ninguna») | **JUnit del artefacto verificado:** 82 archivos y 809 casos PASS, con **29 Golden Masters** y **16 AS-001**. Conjunto de ids **idéntico** al perfil esencial local de la base `102f194` (`evidencia/ci/run_43087996118_intento2_*.txt`). No se cambiaron código, pruebas, dependencias ni workflow. No hubo más intentos |
| HEAD documental | Ver 10 | — | — | — | — |

Que un run termine en `success` tras un fallo y un reintento **no** se clasificaría como estable. En esta fase no hubo reintentos internos.
