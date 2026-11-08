# 01 · G0: oráculo y comparación con la base original (antes de cualquier cambio)

> Comparación **antes de cualquier cambio**. Su resultado (una diferencia, AS-001) dio lugar al NO-GO previo de `02426ef`.
> El propietario aceptó AS-001 como única excepción preexistente (05-11-2026, 22:40 UTC). Los resultados después del
> cambio están en 05.

## 1. Oráculo

`evidencia/scripts/oraculo.py` es externo a los tres árboles y no copia lógica estadística.

**Origen del código y de las entradas**
- `app_icociv` y `aplicacion` se importan de la raíz evaluada. El script verifica la ruta real del módulo.
- El arnés de captura de Fase 0 (`generadores.py`, `captura.py` y `captura_gui.py`) y los dos fixtures CSV se toman de una copia literal fuera de los árboles (`evidencia/arnes_sha256.txt`). Es el mismo para las tres raíces, así que las entradas son idénticas.

**Ejecución**
- Mismo equipo y mismo intérprete (Python 3.12.10).
- Mismos paquetes: los del EXE (00 §1).
- `QT_QPA_PLATFORM=offscreen` y `python -I`.

**Formato canónico**
- Cada `float` se guarda en `float.hex`: distingue 1 ULP, `-0.0`, `nan` e `inf`.
- Enteros, textos, `None` y booleanos se guardan con su tipo.
- DataFrames: columnas, dtypes, índice y filas, en orden.
- Las listas conservan su orden. Solo se ordenan las claves de diccionario.
- Se excluyen únicamente las claves de reloj (`timestamp`, `fecha_calculo`, `fecha_hora` y `generado_en`).

### Escenarios (66 filas en `evidencia/tabla_comparador_G0.csv`)

| Sección | Casos | Qué se compara |
|---|---|---|
| `motor` | 35: las 5 series del Golden Master × H = 1, 6, 11, 12, 17, 23 y 24 | El resultado **completo** de `ejecutar_proyeccion`: modelo, segundo, RMSErect, W*, pares, trayectoria H1–H24, tabla por horizonte con MAE(h), backtesting, factibilidad, textos y periodos. Además, la lista de los 21 candidatos, los pares comunes W*×24, el **SSE exacto (Fraction) de cada candidato** y el número de llamadas al selector |
| `series_extra` | 22: serie volátil, escala ×1e6, escala ×1e-3, cambio de nivel, casi constante, 120 meses y mínima de 36 (todas con semilla) × H 1, 12 y 24; más el extremo finito ×1e150 con H 11 | Lo mismo que `motor` |
| `fixtures_horizonte_dinamico` | 6: `serie_drift.csv` y `serie_holt.csv` × H 1, 12 y 24 | Lo mismo que `motor` |
| `rechazos` | 1, con la historia insuficiente y 11 valores de horizonte | Resultado y mensajes |
| `economico_empalme` | 1, que agrupa factores, importes, rechazos económicos, factor legado y 11 casos de empalme ICCP–ICOCIV (incluido el acero) | Todos los campos |
| `gui_sesion_exportables` | 1: recorrido real de la ventana | Proyección de dos series, actividades, reconsultas H11→H23→H11 sin motor, deshacer/rehacer, guardar, Ctrl+S, cancelación y error de escritura, reapertura sin motor, **Excel de 5 hojas con fórmulas**, PDF y DOCX de la sesión, factor legado y CSV/DOCX/PDF del informe de proyección |

**Normalización (solo en la sección GUI, la del arnés Fase 0):**
- rutas temporales, fechas-hora e identificadores aleatorios en los textos;
- flotantes no finitos convertidos a `None`.

Ningún número, fórmula ni decisión se normaliza.

## 2. Determinismo (dos capturas por versión)

| Versión | Captura 1 frente a captura 2 |
|---|---|
| 5478958 | **Idénticas**: SHA-256 del archivo `1cf85e5e…3b653f` en las dos |
| dfdb3e0 | **Idénticas**: `35f530cf…53329c` en las dos |
| 6672529 | Idénticas en motor, series, fixtures, rechazos, economía, empalme, sesión, Excel y DOCX. **Difieren 2 líneas del texto del PDF de sesión**: la frase «Análisis activo: `<ID1>`. Proyecciones visibles guardadas: 2. Registros calculados: 3.» se parte en otro punto. El texto unido es idéntico. **Causa:** el identificador aleatorio del análisis (un hex que se sustituye por `<ID1>` después de maquetar) cambia la anchura de la línea. Es la intermitencia conocida de `pdf_sesion` y no afecta al contenido (`evidencia/cmp_6672529_r1_r2.txt`). La captura 2 de 6672529 coincide byte a byte, en la sección GUI, con las dos de 5478958 |

## 3. Resultados (sin tolerancia)

### B. V1.1.2 original (6672529) frente a Anti-Slop anterior (5478958)

Detalle en `evidencia/cmp_6672529_5478958.txt`.

| Sección | Casos | Diferencias exactas |
|---|---|---|
| motor | 35 | **0** |
| fixtures_horizonte_dinamico | 6 | **0** |
| rechazos | 1 | **0** |
| economico_empalme | 1 | **0** |
| gui_sesion_exportables | 1 | **0** |
| series_extra | 22 | **1 caso**: `extremo_finito_x1e150\|h11` |

**El caso diferente:**
- **Original:** `OverflowError: integer division result too large for a float`, lanzado al convertir el SSE exacto a float en `_seleccionar_modelo_rectangular`.
- **Anti-Slop:** no hay excepción. Devuelve `proyeccion_generada=False` y `estado_metodologico="no_calculable"`, con la explicación «El modelo seleccionado (fourier_k1__exponencial_log_lineal) no pudo reajustarse…».

### Golden Masters con tolerancia cero

Los golden se generaron el 25-10-2026 sobre 6672529, en este equipo y con los mismos paquetes (`metadatos.json`). Comparación con `rel_tol=0` y `abs_tol=0` (`evidencia/golden_exacto_*.txt`):

| Raíz | Motor (5 series) | Economía | Rechazos | Total |
|---|---|---|---|---|
| 6672529 | 0 | 0 | 0 | **0** |
| 5478958 | 0 | 0 | 0 | **0** |

### D. V1.1.1 (dfdb3e0) frente a V1.1.2 original

Detalle en `evidencia/cmp_6672529_dfdb3e0.txt`.
- Motor, series extra (incluido el extremo, que también lanza `OverflowError`), fixtures, rechazos, economía y empalme: **0 diferencias**.
- GUI: 9 diferencias, **todas la etiqueta de versión** «1.1.1» frente a «1.1.2» en PDF y DOCX. Es una diferencia preexistente y esperada, no metodológica.

## 4. Dominio exacto de la discrepancia

Barrido con la misma serie × 10^k y H = 11 (`evidencia/umbral_as001_*.txt`):

| Escala de la serie | V1.1.2 original | Anti-Slop 5478958 |
|---|---|---|
| 10^0 y 10^50 | Proyección | **Idéntica bit a bit** (modelo e `y_proj` en hex) |
| 10^100 a 10^148 | «No calculable» | **Idéntico** |
| 10^150 a 10^153 | **OverflowError** (en la aplicación: diálogo de error del trabajador) | «No calculable», sin excepción |
| **≥ 10^154** | **OverflowError** | **Proyección generada**, con modelo y valores (por ejemplo, con 10^154, `fourier_k1__exponencial_log_lineal` e `y_proj = 0x1.993a7352df073p+518`) |

**Origen:**
- Commit `8159d52` (26-10-2026, «fix(AS-001): RMSE informado sin OverflowError en el selector rectangular»), de la Fase 1B.
- Cambia `rmse = math.sqrt(float(sse) / len(valores))` por `rmse = _rmse_desde_sse(sse, len(valores))`, que conserva la misma expresión y solo añade una vía `Decimal` cuando `float(sse)` desborda.
- Es el **único cambio no sustractivo** de producción entre 6672529 y 5478958 (`evidencia/diff_produccion_6672529_5478958.patch`: +30 −689 líneas). Las 30 líneas añadidas son esa función, su import, su llamada y docstrings.

**Alcance.** El desbordamiento exige errores fuera de muestra del orden de 1e154. En el barrido aparece con índices de unos 1e150 o más. Los índices ICOCIV e ICCP reales rondan 10². En todos los escenarios de escala ordinaria medidos, la igualdad es exacta. Aun así, **no puedo afirmar una demostración universal**: la igualdad está comprobada en los 65 escenarios listados y el dominio diferente queda caracterizado por el barrido.
