# 01 · Reproducción y contradicción matemática (GATE 0)

## 1. Qué calcula el intervalo interno (trazado en el código)

1. **Errores** (`_ejecutar_proyeccion_base`, línea 1421). `errores_oos_modelo = _errores_por_horizonte(backtesting_comparativo, modelo, 1..h)`. Para cada paso p toma la columna `Error` de `backtesting_comparativo[f"{modelo}_h{p}"].predicciones`: el walk-forward completo de ese modelo a horizonte exacto p, sobre todos los orígenes disponibles. No es la muestra rectangular.
2. **Banda** (`_intervalos_prediccion`, línea 4497, y `_cuantiles_intervalo`, línea 4318):
   - `sigma = sqrt(mean(e²))` sobre los errores finitos del paso;
   - `c = _multiplicador_intervalo(nivel, n)`, que es un cuantil t con n grados de libertad;
   - límites = `(base ± c·sigma)·factor`, donde `base = y/factor` y `factor` es el ajuste de calendario (1 si no se aplica). Por tanto, límites = `y ± c·sigma·factor`.
3. **Publicación** (`ejecutar_proyeccion`, línea 578). `_retirar_intervalo_de_publicacion` vacía `ci95_lo`/`ci95_hi` y las réplicas, y quita las columnas de error de `backtesting.predicciones` y de `backtesting_comparativo[*].predicciones`. **No toca `metricas`**: ni `errores_extremos.observaciones`, ni `rmse`, ni `desviacion_error`/`error_medio`.
4. **Métricas del comparativo** (`app_icociv/validacion/backtesting.py:504-549`, `_metricas_backtesting`). Se calculan sobre esos mismos errores:
   - `metricas.rmse = calcular_rmse(observado, predicho) = sqrt(mean((y−ŷ)²))` (`estadistica/metricas.py:112-116`), es decir, **la misma magnitud que `sigma`**;
   - `metricas.iteraciones` es su `n`;
   - `desviacion_error = np.std(errores, ddof=1)` y `error_medio` es la media del error;
   - `errores_extremos = detectar_errores_extremos(errores, periodos)`, que incluye `observaciones`.
5. **RMSE_h persistido** (`tabla_horizontes`, CSV `rmse_horizonte`, sesión). Se calcula sobre la muestra rectangular común W* = n − 36 + 1, con orígenes 12…n−24. El walk-forward a horizonte h usa los orígenes 12…n−h. **Las dos muestras coinciden exactamente cuando h = 24.**

## 2. Resultados (igualdad exacta `==`, sin tolerancias)

Script: [`evidencia/diagnostico_vias_a_b.py`](evidencia/diagnostico_vias_a_b.py). Salida: [`evidencia/salida_diagnostico_vias_a_b.txt`](evidencia/salida_diagnostico_vias_a_b.txt). Cada escenario ejecuta `ejecutar_proyeccion` real; el IC95 interno se captura con un espía justo antes de que se vacíe.

| Escenario | n del paso | Vía A: vector | Vía B1: `comparativo.metricas.rmse` + `iteraciones` | Vía B2: `desviacion_error` (ddof 1) + `error_medio` + n | Vía B3: RMSE_h persistido + W* |
|---|---|---|---|---|---|
| Ondulada n=48 h=6 (B-A1) | 31 | **exacto** | **exacto** | **exacto** | difiere 0,249 (W*=13) |
| Ruidosa n=72 h=12 | 49 | **exacto** | **exacto** | **exacto** | difiere 0,723 (W*=37) |
| Ondulada n=38 h=24 (pocos pares) | 3 | **exacto** | **exacto** | **exacto** | **exacto** |
| Estacional n=60 h=9 | 40 | **exacto** | **exacto** | **exacto** | difiere 0,185 (W*=25) |
| Ondulada n=48 h=24 | 13 | **exacto** | **exacto** | 2,8·10⁻¹⁴ en el límite superior | **exacto** |
| Ruidosa n=72 h=24 | 37 | **exacto** | **exacto** | **exacto** | **exacto** |
| Ruidosa n=30 h=3 (historia insuficiente) | — | sin banda | sin banda | sin banda | sin banda |

**Caso B-A1 en detalle.**
- Entrada `exponencial_log_lineal_h6`, con 31 errores.
- `rmse` = `1.9063084328995537` = `sqrt(mean(error_absoluto²))`.
- `y_proj` = `121.58536382460937`.
- IC95 interno = (`117.69742214273187`, `125.47330550648688`). Las vías A, B1 y B2 lo reproducen bit a bit.
- B3 usa el RMSE rectangular `1.9151024099696756` con W*=13 y da (117.448, 125.723): una diferencia de 0,25 puntos, el 0,2 % del pronóstico.

Ninguno de los escenarios aplicó ajuste de calendario (`factor` = 1). Con ajuste, la banda quedaría escalada por el factor del paso; este factor no se buscó entre los campos publicados.

**Lo que es y no es la vía A.** `observaciones` tiene un registro por ventana (`posicion`, `periodo`, `error_absoluto`, `z_modificado`, `extremo`), en el orden de las ventanas. Su longitud es igual a `iteraciones` en todas las entradas, también en las que no tienen ningún extremo (`cantidad` = 0). No es un subconjunto: es el vector completo de |e|, y como `sigma` no depende del signo, reconstruye la banda.

## 3. Por qué no hay corrección completa compatible con el contrato

- **B1:** `backtesting_comparativo[<modelo>_h<p>].metricas.rmse` es, por definición, `sigma_h`, y está publicado en las 504 entradas modelo×horizonte, junto con su `n`.
- **B2:** aunque se retirara `rmse`, `desviacion_error` (ddof=1) y `error_medio` dan `sigma` exacta: `sigma² = media² + desviación²·(n−1)/n`.
- **B3:** el **RMSE por horizonte protegido**, el que se persiste en la tabla de horizontes, el CSV y la sesión, reproduce **exactamente** la banda del paso 24 en cualquier serie, porque ahí las dos muestras coinciden. En los demás horizontes la aproxima con diferencias del orden del 0,2–0,4 % del pronóstico, lo que en la práctica la hace deducible.

Retirar solo el vector (lo que proponía el informe anterior) deja la prueba adversarial del vector en verde y la vía B intacta. Lo demuestra la mutación M1 de [`evidencia/salida_mutaciones_adversarial.txt`](evidencia/salida_mutaciones_adversarial.txt). Sería un cierre falso de P0-C.

**El comentario de producción es incorrecto.** El comentario de `COLUMNAS_OOS_RECONSTRUCTIVAS` (`servicio_proyeccion.py:625-656`) justifica conservar los agregados diciendo que «de un promedio de cuadrados no se recupera la muestra». Es cierto, pero no hace falta la muestra: la banda solo necesita `sigma` y `n`, y el RMSE **es** `sigma`. No lo corrijo aquí, porque sería un cambio de producción (07 §4).

## 4. Decisión

**NO-GO para el cierre completo de P0-C.** Los agregados que el contrato protege (RMSE y su n, desviación y media del error, RMSE_h con W) bastan para reconstruir el IC95, exactamente o de forma prácticamente deducible.

Por eso no he suprimido métricas ni introducido ruido, redondeos u ocultación, y **no he cambiado producción**. Las alternativas están en 07 §3.
