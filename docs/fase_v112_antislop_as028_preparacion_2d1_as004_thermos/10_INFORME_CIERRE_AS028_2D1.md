# 10 · Informe de cierre: AS-028 (preparación del lote 2D-1) y diagnóstico AS-004

## 1. Rama, SHA y enlaces

| Dato | Valor |
|---|---|
| Rama | [`maintenance/v1.1.2-as028-preparacion-2d1-as004-thermos`](https://github.com/estebanojeda0615/SAVIP/tree/maintenance/v1.1.2-as028-preparacion-2d1-as004-thermos) |
| SHA base | `102f194cfffc4f92d57006f4b9a0b80eb0b225d1` |
| Último commit de pruebas y código | `56d9562aeb273c20fff3f82197c2c7b031d4c1a4` |
| HEAD | Commit documental con esta carpeta (el SHA y su CI se indican en el mensaje de entrega) |
| Comparación | https://github.com/estebanojeda0615/SAVIP/compare/102f194cfffc4f92d57006f4b9a0b80eb0b225d1...maintenance/v1.1.2-as028-preparacion-2d1-as004-thermos |

## 2. Archivos realmente cambiados (`git diff --stat 102f194 56d9562`)

| Commit | Archivo | Cambio |
|---|---|---|
| `19c4649` | `.github/workflows/fase0-pruebas.yml` | +1: la rama, en el filtro `push`. Jobs y política de reintentos sin cambios |
| `19c4649` | `.gitignore` | +1: excepción para esta carpeta de docs |
| `5133abc` | `pruebas/prueba_horizonte_dinamico_ui_reportes.py` | Baja de las 3 pruebas y de sus 3 llamadas en `main()`, con lápida (en este commit se retiró también el auxiliar) |
| `7993060` | El mismo script | Restauración **byte a byte** de `_evaluacion_horizonte`, por alcance estricto |
| `56d9562` | El mismo script | Lápida corregida tras Thermos: solo comentarios |
| **Neto** | 3 archivos | +11 / −63 |

**Diff productivo vacío:**

```bash
git diff 102f194 56d9562 -- app_icociv aplicacion.py VERSION packaging requirements-lock.txt requirements-test.txt tests/fixtures scripts tests
```

no devuelve nada.

## 3. Inventario de las 29 pruebas y bajas

- **Inventario:** `01_INVENTARIO_SCRIPT_29_TESTS.csv`, con 29 filas. Incluye líneas, estados en `102f194` y en `56d9562`, contrato, equivalencia y decisión.
- **Bajas autorizadas (3):**
  - `test_horizonte_maximo_no_es_18_si_h18_no_cumple` (PASS);
  - `test_mensaje_no_recomendables_no_imprime_lista_vacia` (PASS);
  - `test_h18_no_se_redacta_como_intervalos_aceptables` (FAIL histórico).
- Las tres quedan clasificadas como **HISTÓRICA / NO APLICA**, aserción por aserción (02):
  - sobre la salida productiva real, sus aserciones dan `KeyError` o se refieren a una redacción que ya no existe;
  - la cadena «intervalos aceptables» solo existe en el fixture del propio script;
  - el contrato vigente lo cubren `test_metodologia_n0_12_h24::test_b…` y `::test_efg…`, el espía de la Fase 1A y el AST de la Fase 2C.
- **Recuento:** 29 → **26** tests y 21/8 → **19/7**, coincidiendo con la predicción. 0 altas y 0 cambios de estado.
- Los 7 FAIL históricos restantes se conservan intactos. **No se tocaron las otras 26 pruebas**, incluidas drift/holt de AS-004.
- `_evaluacion_horizonte` queda **sin uso**: se conserva y es candidato a retirarse con 2D-1.

## 4. Mapa AS-004

**Entregables:** `03_AS004_PRODUCTORES_CLAVES_CONSUMIDORES.csv` (60 filas, con filtro reproducible por receptor y 101 lecturas en la lista de descartes) y `04_AS004_FUNCIONES_Y_REPORTES.md`.

**Productores de claves históricas**
- `determinar_*`: no se invoca.
- Plantilla por defecto de `_resultado_sin_proyeccion`: valores 0, `[]` y `"bloquear"`.
- La ruta vigente **no** produce ninguna clave de «máximo / escenario / no recomendable».

**Consumidor productivo con exposición visible:** el **CSV reproducible** (`construir_dataframe_reproducibilidad`), que tiene 17 columnas históricas. Lo protegen:
- el Golden `sesion_exportables`;
- el esencial `test_presentacion_resultados::test_exportable_diferencia_recomendado_evaluado_y_limite_operativo`, que obliga a leer 4 de esas claves.

Con resultados nuevos escribe `''`; con la plantilla, `0`; con sesiones heredadas, los valores antiguos (comprobado inyectando una).

**Funciones `_lineas_*` y `generar_reporte_html`:** SOLO TEST. Ya leen la estructura 12/24 vigente.

**Riesgos**
- Retirar o dejar de leer las columnas cambiaría un exportable y rompería un Golden y un esencial.
- El encabezado de la UI solo usa `mensaje_ui` con sesiones heredadas.
- `firma_serie_sha256` y `version_criterios` no tienen productor.

**Propuesta independiente:** opción **(b)**, una fase preparatoria de pruebas:
1. migrar `casoJ` al informe productivo;
2. fijar todas las columnas del CSV;
3. quitar el import sin uso.

Después, decidir por separado: retirar la cadena solo-test (c), y **no** retirar las columnas dentro de Anti-Slop.

## 5. Pruebas, Golden, AS-001, huella y oráculo

| Comprobación | Resultado | Ejecutado en esta fase |
|---|---|---|
| Perfil esencial, base y final | **809/809**, 0 fallos en la 1.ª ejecución; conjunto de ids idéntico | Sí (local y CI) |
| Golden | **29/29**; con tolerancia cero, **0 diferencias** | Sí |
| AS-001 | **16/16**; umbral idéntico al de 2D-2 | Sí |
| Huella (20 escenarios) | **0 diferencias**; SHA `d6be699b…0191` idéntico | Sí |
| Oráculo de 66 escenarios frente a `102f194` | **66/66** (hash de datos `766a34b8…`); final r1 = r2 | Sí, en ambas copias |
| Oráculo de 66 escenarios frente a la V1.1.2 original `6672529` | **Única diferencia: AS-001.** Además, en una de las capturas de la original aparece un salto de línea del PDF de sesión que la propia original varía entre ejecuciones (r1 ≠ r2), con el texto normalizado idéntico en las 7 capturas. Es un metadato no determinista admitido por el prompt; **no** se trata como una diferencia funcional | Sí (`6672529` r3). El EXE **no** se ejecutó: se usó su fuente, con la correspondencia 87/87 heredada de 2D-2 |
| V1.1.1 → V1.1.2 original | Evidencia **heredada** de 2D-2 (ninguna de las dos cambió) | No |
| Colección | 1 036 tests y los mismos 3 errores históricos; **0 nuevos** | Sí |
| `compileall`, imports, `pip check` y `git diff --check` | OK | Sí |
| Simulación de 2D-1 oculto | Script: idéntico por id. Esencial: fallan los **18** ids previstos. Salidas AS-004: **0 diferencias** en 29 casos | Sí |
| Parche 3c_a | Intacto | Sí |

## 6. Thermos

Dos pasadas reales con `thermos:thermo-nuclear-reviewer` y `thermos:thermo-nuclear-code-quality-reviewer` (08).

- **1.ª pasada:** corrección GO. Calidad con hallazgos A1/A2 sobre la evidencia.
- **2.ª pasada** (diff completo hasta `56d9562`): **corrección APTO, calidad APROBADO en el código**. Hubo hallazgos medios de documentación y evidencia (M-1, que refuerza el NO-GO de AS-004; efectos del CSV 03; comparación del encabezado; doc 02 desfasado). **Todos están resueltos** antes del commit documental.
- No queda abierto ningún hallazgo crítico, alto ni medio del diff.
- Se registra como observación sin cambio el auxiliar conservado (M1 de calidad), por decisión de alcance del propietario.

## 7. CI real

| Run | Commit | Resultado |
|---|---|---|
| [43086981441](https://github.com/estebanojeda0615/SAVIP/actions/runs/43086981441), intento 1 | `7993060` | success: 809 pruebas, 0 fallos en la 1.ª ejecución, sin intermitentes |
| [43087996118](https://github.com/estebanojeda0615/SAVIP/actions/runs/43087996118), intento 1 | `56d9562` | **failure de infraestructura**: el paso de pruebas terminó en success, falló `upload-artifact` («CreateArtifact 404 workflow run not found») y el log no se pudo descargar |
| 43087996118, **intento 2** (único relanzamiento, autorizado) | `56d9562` | **success**: 809 pruebas, 0 fallos en la 1.ª ejecución, sin intermitentes. El JUnit del artefacto confirma 809 PASS, **29 Golden** y **16 AS-001**, con el conjunto de ids idéntico a la base |
| HEAD documental | Commit de docs | Ver el mensaje de entrega. No se usa `[skip ci]` |

## 8. Tres dictámenes separados (09)

1. **AS-028 (script para 2D-1): GO.** El script ya no tiene ninguna dependencia ejecutable de `determinar_horizonte_maximo_estadistico` y conserva todos los contratos vigentes.
2. **AS-004 (generador histórico): NO-GO POR DEPENDENCIAS.** El diagnóstico está completo. El CSV reproducible publica columnas históricas, protegidas por un Golden y un esencial. **AS-004 no se ejecutó ni se limpió.**
3. **Lote 2D-1 productivo: GO SOLO PARA SOLICITAR PROMPT.** El inventario está completo, sin consumidores productivos y sin diferencias de salida. Falta autorizar 8 bajas esenciales, 9 adaptaciones de import, la Fase 1A, una histórica y `C-ALC-002`. **No autoriza a empezar 2D-1.**

## 9. Declaración de no modificación

**No se cambió:**
- la metodología, la SSE exacta (`Fraction`), `_rmse_desde_sse`, RMSErect, la selección y el desempate, N0=12 / H=24, W*×24, los 21 candidatos, la trayectoria ni los horizontes;
- ICOCIV/ICCP, el empalme, la economía, la GUI, las sesiones, los informes ni los exportables;
- los Golden, las tolerancias ni las dependencias.

La única excepción histórica sigue siendo **AS-001**, sin modificar ni ampliar. **P0-C** sigue cancelado y no se tocó.

No se tocaron `main`, `develop/v1.1.2`, el tag ni la release `v1.1.2-rc.1`, las ramas anteriores ni el repositorio de desarrollo. No hubo merge, PR, tag, release, EXE ni ZIP.

## 10. Deudas, limitaciones, reversión y siguiente autorización

**Deudas registradas**
- `_evaluacion_horizonte`, sin uso.
- Comentarios y la ficha `C-ALC-002`, que citan funciones de 2D-1.
- Columnas `firma_serie_sha256` y `version_criterios`, sin productor.
- Cadena `generar_reporte_html` → `_lineas_*`, solo-test.
- `COLS_CSV`/`COLUMNA_CSV` copiados a mano en dos herramientas.
- Workflow y `.gitignore`, que crecen con una línea por fase.
- La observación de producción de 3c_a (ajuste de ancho) y la cuarentena `test_layout_adaptable…`, heredadas.

**Limitaciones**
- El oráculo se ejecutó sobre la fuente, no sobre el EXE.
- La comparación V1.1.1 → V1.1.2 es heredada.
- Que no se observen llamadas no sustituye a la inspección estática; aquí se combinaron ambas.

**Reversión** (no destructiva, no ejecutada):

```bash
git revert <docs> 56d9562 7993060 5133abc 19c4649
```

**Para continuar** hace falta un prompt nuevo y expreso para el lote 2D-1 (plan en 09 §4) y, por separado, la decisión sobre AS-004 (opción b).

**FASE DETENIDA a la espera de la revisión del propietario.**
