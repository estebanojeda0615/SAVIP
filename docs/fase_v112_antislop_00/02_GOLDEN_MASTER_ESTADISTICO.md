# 02 · Golden Master del motor estadístico

**Ligado a:** commit `66725293f304426ae6edf144b8f4dadbcbeefe10` (tag `v1.1.2-rc.1`). Árbol `app_icociv` = `8af9547d6a2bd904af67ae0c52ee17b34dd4b17f`.

- **Generación publicada:** 2026-10-25 14:14 (hora de Colombia; 19:14 UTC), con Python 3.12.10 y las versiones exactas de `requirements-lock.txt`. Detalle en `tests/fixtures/fase0/golden/metadatos.json`.
- **Dos generaciones previas descartadas antes de publicar** (13:43 y 14:02). La normalización del arnés de sesión dejaba pasar datos que cambian en cada ejecución:
  - IDs aleatorios de filas técnicas e IDs partidos entre líneas del PDF;
  - la fecha «25 de octubre de 2026, 14:02».

  Se corrigió solo el arnés de prueba, nunca código productivo. Dos capturas completas en procesos, carpetas y minutos distintos dieron 0 diferencias. **`motor.json` y `economico.json` salieron idénticos byte a byte en las tres generaciones.**
- **Esperados:** `tests/fixtures/fase0/golden/motor.json` (61 699 bytes; SHA-256 `7b7329a6…`).
- **Prueba:** `tests/test_fase0_golden_motor.py` (11 pruebas).
- **Generador:** `tests/fixtures/fase0/generar_golden.py`. Se niega a correr si `app_icociv/`, `aplicacion.py`, `packaging/`, los scripts de distribución, `VERSION` o los `requirements*.txt` de la aplicación difieren de `6672529`, o si ya existe algún golden.

## 1. Escenarios sintéticos

Todos los escenarios están en `tests/fixtures/fase0/generadores.py`, con semilla fija y sin datos del DANE. Cada uno se consulta a **H11** y **H23** con `ejecutar_proyeccion` real (21 candidatos, matriz rectangular 12/24, RMSErect con `_sse_exacto`).

| Escenario | n | Modelo elegido | 2.º lugar (Δ %) | RMSErect | W* | H11 (periodo → I) | H23 (periodo → I) | MAE(h=11) |
|---|---|---|---|---|---|---|---|---|
| `tendencia_lineal_ruido` (0,5/mes + N(0; 1,2)) | 60 | `fourier_k1__exponencial_log_lineal` | `exponencial_log_lineal` (12,22 %) | 1,276591 | 25 | 2025-11 → 137,1714 | 2026-11 → 144,7662 | 0,9942 |
| `estacional` (0,3/mes + 2·sen(2πt/12) + N(0; 0,4)) | 72 | `fourier_k1__exponencial_log_lineal` | `fourier_k1__huber` (9,14 %) | 0,423548 | 37 | 2026-11 → 123,5897 | 2027-11 → 127,7537 | 0,3228 |
| `exponencial` (1 %/mes × (1 + N(0; 0,002))) | 48 | `exponencial_log_lineal` | `fourier_k1__exponencial_log_lineal` (31,02 %) | 0,313070 | 13 | 2024-11 → 178,6586 | 2025-11 → 201,4587 | 0,1703 |
| `paseo_aleatorio` (N(0,1; 0,8) acumulado) | 40 | `seasonal_naive` | `naive` (8,25 %) | 3,018306 | 5 | 2024-03 → 94,4775 | 2025-03 → 94,4775 | 2,0396 |
| `lineal_exacta_empate` (100 + 0,5·t, sin ruido) | 36 | `lineal` (desempate) | `holt_lineal` (empate exacto) | 0 | 1 | 2023-11 → 123,0 | 2024-11 → 129,0 | 0 |

Los cinco escenarios cubren familias distintas:
- Fourier + log-lineal;
- log-lineal puro;
- benchmark estacional (`seasonal_naive`);
- empate exacto resuelto por orden del banco.

`lineal_exacta_empate` está en la frontera mínima n = 36 (W* = 1).

## 2. Qué fija cada escenario (por consulta H11 y H23)

- **Selección:**
  - `modelo_codigo`, `model_name`, `modelo_segundo`;
  - `rmse_seleccion_oos`, `rmse_segundo_oos`, `diferencia_porcentual_segundo`;
  - `w_estrella`, `pares_comunes` = `pares_esperados` = W*·24;
  - lista de los **21 candidatos evaluados**.
- **RMSErect de los 21 candidatos**, ordenado como lo ordena la selección.
  - Se captura con un espía `wraps=` sobre `_seleccionar_modelo_rectangular`: observa la matriz real y no sustituye nada.
  - El RMSErect se recalcula sobre la muestra común con el `_sse_exacto` productivo.
- **Trayectoria interna H1..H24** (`trayectoria_24_meses`).
- **Tabla por horizonte h = 1..24:** W, RMSE(h) y **MAE(h)**. Es la fuente del «±MAE» de la interfaz.
- **Punto consultado:** `periodo_proj`, `y_proj`, `factor_actualizacion`, `variacion_acumulada`.
- **Backtesting del horizonte solicitado:** horizonte, iteraciones, RMSE y MAE.
- **Intervalos publicados:** los seis límites `ci_*` deben seguir en `None`. Los intervalos no publicados no se tocan.

## 3. Invariantes que se comprueban además del golden

- H11 y H23 dan **el mismo** modelo, ranking, RMSE de selección y trayectoria. El horizonte consultado no reentrena ni cambia la selección.
- `y_proj` es exactamente `trayectoria_24_meses[h−1]` para h = 11 y h = 23.
- El ganador pertenece al grupo de RMSErect mínimo.
- La tabla de horizontes tiene h = 1..24.

## 4. Rechazos (`test_golden_rechazos`)

- **Historia insuficiente (n = 30 < 36):**
  - `proyeccion_generada = False`, modelo «No seleccionado», `y_proj = None`;
  - W* = −5 y `historia_suficiente_12_24 = False`;
  - la explicación literal de la metodología 12/24 queda fijada.
- **`validar_horizonte_solicitado`:**
  - acepta `24` y `"12"`;
  - rechaza, con su mensaje literal: `25` (fuera del alcance de 24), `0`, `-1`, `"1.5"`, `1.5`, `""`, `None`, `True` y `"abc"`.

## 5. Tolerancias (justificación)

| Tipo | Comparación | Por qué |
|---|---|---|
| Flotantes | `rel_tol = 1e-9`, `abs_tol = 1e-12` | El lock fija versiones, pero los núcleos BLAS/LAPACK (OpenBLAS de numpy/scipy) eligen rutas SIMD según la CPU. Pueden variar en los últimos bits (~1e-15 relativo). El margen es seis órdenes mayor que ese ruido y muy inferior a lo que SAVIP muestra (2 a 4 decimales). |
| Texto, códigos, enteros, booleanos, `None` | Exacta | No dependen de la CPU. |
| Orden del ranking | Exacto entre candidatos cuyo RMSErect difiere más que la tolerancia | Dos candidatos separados por menos de 1e-9 relativo pueden intercambiarse por ruido de CPU sin cambiar ninguna cifra visible. |
| RMSErect de candidatos con **optimizador iterativo** (`holt_lineal`, `holt_amortiguado`, `huber` y sus variantes `fourier_k1__…`) | `rel_tol = 1e-4`, `abs_tol = 1e-8` | **Medido en GitHub Actions (run 40240413329)** frente al equipo de referencia: hasta 5e-7 relativo (`holt_lineal` en `exponencial`: 2,838256752 frente a 2,838255296). El optimizador (statsmodels/scikit-learn) converge hasta su tolerancia por rutas SIMD distintas según la CPU. Ningún ganador ni segundo lugar de estos escenarios es de esa familia. |
| Ganador en empate exacto | Debe pertenecer al grupo empatado del golden y ser el mínimo obtenido | Con datos sin ruido, `lineal`, `holt_lineal` y `drift` tienen SSE 0. El desempate documentado (primer candidato del banco) decide solo si el empate sigue siendo exacto. Un error de 1e-15 en otra CPU lo rompería legítimamente. |

## 5 bis. Hallazgo de reproducibilidad entre equipos (documentado, sin corregir)

**Observación en CPU distintas.** Con las mismas versiones exactas del lock, los candidatos ajustados por optimización iterativa no dan resultados bit a bit iguales:
- RMSErect: hasta 5e-7 relativo;
- métricas impresas (MAE/MASE de «Holt tendencia amortiguada»): hasta 3,5e-5, visibles con 4 decimales (`5,7422` → `5,7424`).

**Cuándo podría importar.** Si alguna vez uno de estos candidatos queda a menos de ~1e-6 relativo del ganador, la selección podría cambiar de equipo a equipo. En los 5 escenarios y en la sesión sintética no ocurre: el margen mínimo entre ganador y segundo es 8,25 %, y 0 en el empate exacto, que no es de esta familia.

**Recomendación** para una fase posterior: fijar la tolerancia o la semilla de los optimizadores, o documentar la cota.

## 6. Qué NO cubre

- **Series reales del DANE.** Están en el perfil «integración externa con DANE» (no publicable).
- **Ajuste de calendario/salto anual y diagnósticos de residuos** (Ljung-Box, Jarque-Bera). Se fijan solo indirectamente, por el modelo y las cifras; no hay golden de sus textos ni de sus estadísticos.
- **Otros escenarios:**
  - horizontes distintos de 11 y 23 (sí se fija la trayectoria completa H1..H24);
  - otras fechas de inicio de serie;
  - series con huecos, atípicos marcados o valores no positivos.
- **Banco de candidatos:** que los 21 sean los correctos se fija solo como lista. La pertinencia metodológica de cada candidato no se evalúa.
- **Selector retirado** (`seleccionar_modelo_por_rmse_oos_global`, AS-006) **y AS-001** (desborde con un candidato divergente): no se prueban aquí. AS-001 sigue documentado y sin corregir.
- **Tiempo de cómputo:** no se mide.
