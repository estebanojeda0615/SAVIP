# 05 · G4: equivalencia estadística, económica y de exportables

**Condiciones comunes a todas las capturas**
- Oráculo `evidencia/scripts/oraculo.py` (01 §1) y arnés idéntico para todas las raíces.
- Mismo equipo, mismo Python 3.12.10 y mismos paquetes que el EXE original (00 §1).
- Comparación exacta con `float.hex` y sin tolerancias.
- La tabla obligatoria del comparador está en `evidencia/tabla_comparador_G4.csv`: 66 filas, con las columnas del prompt §7 y el SHA del resultado canónico de cada versión por caso.

**Raíces comparadas**

| Raíz | Commit | Hash de datos de la captura | Determinismo (2 capturas) |
|---|---|---|---|
| V1.1.2 original | `66725293f304426ae6edf144b8f4dadbcbeefe10` (fuente demostrada del EXE) | Captura 2: `5d74b128…` | Una línea del PDF de sesión se parte en otro punto; el texto unido es idéntico (01 §2) |
| V1.1.1 | `dfdb3e046126093e23b045147f789fbc52961a73` | `0943387e…` | Idénticas |
| Anti-Slop anterior | `54789587d0fa7714b4dc464ec48ca8f2ce254611` | `766a34b8a8968b02c1db35fb2dcdb7a94ebbf61b9450f70e415985e69ca1bb3f` | Idénticas |
| **Lote 2D-2 final** | `55ba5646…`. Su producción es idéntica a la de `49106f95`, el último commit de código: `git diff 55ba564 49106f9 -- app_icociv` está vacío | **`766a34b8a8968b02c1db35fb2dcdb7a94ebbf61b9450f70e415985e69ca1bb3f`** | Idénticas: archivo `90a2db66…` en las dos capturas |

## Las cuatro comparaciones

| Comparación | Escenarios | Resultado | Evidencia | Limitaciones |
|---|---|---|---|---|
| **A. V1.1.2 original ↔ 2D-2 final** | 66 | **65 iguales.** El único distinto es `extremo_finito_x1e150\|h11`, la **excepción AS-001 aceptada**: la original lanza `OverflowError` y el final da «no calculable», **idéntico a 5478958**. En motor (35), fixtures (6), rechazos, economía y empalme, y GUI con sesión y exportables: **0 diferencias** | `cmp_6672529_55ba564.txt`, `tabla_comparador_G4.csv` | Se compara con la fuente demostrada del EXE, no con el EXE ejecutado (00 §1). Igualdad comprobada en 65 escenarios, no universal |
| **B. V1.1.2 original ↔ Anti-Slop anterior** | 66 | 65 iguales; el mismo caso AS-001 (01 §3) | `cmp_6672529_5478958.txt` | Ídem |
| **C. Anti-Slop anterior ↔ 2D-2 final** | 66 | **66/66 idénticos**. Hash de datos total idéntico (`766a34b8…`) y sección a sección también | `cmp_5478958_55ba564.txt` | — |
| **D. V1.1.1 ↔ V1.1.2 original** | 66 | En motor, series, fixtures, rechazos, economía y empalme: idénticas, incluido el caso extremo, donde las dos lanzan `OverflowError`. En la GUI solo cambia la etiqueta de versión «1.1.1»/«1.1.2», en 9 lugares | `cmp_6672529_dfdb3e0.txt` | La 1.1.1 no tiene artefacto empaquetado |

**Golden Masters sin tolerancia** (`rel_tol=0`, `abs_tol=0`), generados sobre 6672529:

| Raíz | Motor (5 series) | Economía | Rechazos |
|---|---|---|---|
| 6672529 | 0 | 0 | 0 |
| 5478958 | 0 | 0 | 0 |
| **2D-2 final** | **0** | **0** | **0** |

Detalle en `golden_exacto_*.txt`.

## Matriz de campos comparados

| Superficie | Campos | Escenarios |
|---|---|---|
| Selección y pronóstico | Modelo elegido y segundo; los 21 candidatos y su orden; W*; horizontes de la matriz; pares comunes W*×24, en orden; **SSE exacto (Fraction) de cada candidato**; RMSErect de selección y del segundo; diferencias; trayectoria de 24 meses; `y_proj`; periodo proyectado; factor de actualización; variación acumulada; número de llamadas al selector | 35 de motor (H 1, 6, 11, 12, 17, 23 y 24), 22 de series extra y 6 de fixtures |
| Resultado completo | **Todas las claves** públicas y anidadas de `ejecutar_proyeccion`, salvo las de reloj: tablas por horizonte con RMSE, MAE, MASE, sMAPE, sesgo y W; backtesting; factibilidad; diagnóstico; textos; catálogo; calendario; DataFrames con columnas, dtypes, índice y filas; `None`, NaN e inf distinguidos | Ídem |
| Rechazos | Historia insuficiente y validación de 11 valores de horizonte (mensajes exactos) | 1 |
| Economía y empalme | Factores (p, F en texto exacto); importes de actualización; rechazos económicos; factor legado; 11 casos de empalme ICCP–ICOCIV, incluidos el acero y los errores | 1 |
| Sesión y exportables (GUI real) | Invariantes del flujo; sesión guardada (resumen); reapertura sin motor; consultas H11→H23→H11; **Excel de 5 hojas con fórmulas y valores**; texto del PDF y del DOCX de la sesión, con párrafos y tablas; factor legado; CSV, DOCX y PDF del informe de proyección | 1 |

**Exclusiones y normalización:**
- Claves de reloj (`timestamp`, `fecha_calculo`, `fecha_hora`, `generado_en`).
- En la sección GUI, rutas temporales, fechas-hora e IDs aleatorios en los textos, y flotantes no finitos convertidos a `None`, con el normalizador del arnés Fase 0.

No se normaliza ningún número, fórmula ni decisión.

## Excepción AS-001 (aceptada el 05-11-2026 a las 22:40 UTC)

| Aspecto | Evidencia |
|---|---|
| Qué es | Corrección **anterior a este lote** (Fase 1B, commit `8159d52`, 26-10-2026). En `_seleccionar_modelo_rectangular`, el RMSE informado usa `_rmse_desde_sse`. Esa función conserva `math.sqrt(float(sse) / n)` y solo recurre a `Decimal` cuando `float(sse)` desborda |
| Alcance | Solo cuando el SSE exacto supera el rango de `float`. En el barrido, a partir de una serie de 10^150 |
| No modifica los resultados ordinarios | Barrido de 10^0 a 10^148 idéntico bit a bit; 65/65 escenarios ordinarios idénticos; golden con 0 diferencias exactas |
| 2D-2 no la amplía ni la cambia | En el caso extremo, el lote final da exactamente lo mismo que 5478958 (comparación C) |
