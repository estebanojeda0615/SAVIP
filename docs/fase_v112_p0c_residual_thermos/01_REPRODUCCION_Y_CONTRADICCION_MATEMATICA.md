# 01 · Reproducción y contradicción matemática (GATE 0)

## 1. Qué calcula el intervalo interno (trazado en el código)

1. **Errores** (`_ejecutar_proyeccion_base`, línea 1421). `errores_oos_modelo = _errores_por_horizonte(backtesting_comparativo, modelo, 1..h)` toma, para cada paso p, la columna `Error` de `backtesting_comparativo[f"{modelo}_h{p}"].predicciones` sin los NaN. Es el walk-forward completo de ese modelo a horizonte exacto p, sobre todos los orígenes disponibles. No es la muestra rectangular.
2. **Banda** (`_intervalos_prediccion`, línea 4497, y `_cuantiles_intervalo`, línea 4318):
   - `sigma = sqrt(mean(e²))` sobre los errores finitos del paso;
   - `c = _multiplicador_intervalo(nivel, n)`, un cuantil t con n grados de libertad;
   - límites = `(base ± c·sigma)·factor` con `base = y/factor`. El límite inferior se recorta con `max(…, 0)` (líneas 4560 y 4562).
   - Desde P0-F, `factor` vale siempre 1: `_ajustar_salto_anual` no aplica el ajuste. Se publica en `ajuste_calendario.factores_por_paso` (línea 4223), y vale `[1.0]` en los escenarios examinados.
   - Por tanto, límites = `y ± c·sigma`, salvo el recorte en 0, que solo actúa en series cercanas a cero.
3. **Publicación** (`ejecutar_proyeccion`, línea 578). `_retirar_intervalo_de_publicacion` vacía `ci95_lo`/`ci95_hi` y sus réplicas, y quita las columnas de error de `backtesting.predicciones` y de `backtesting_comparativo[*].predicciones`. **No toca `metricas`.**
4. **Métricas del comparativo** (`app_icociv/validacion/backtesting.py:504-549`, `_metricas_backtesting`). Se calculan sobre los mismos errores:
   - `rmse = calcular_rmse(observado, predicho) = sqrt(mean((y−ŷ)²))` (`estadistica/metricas.py:112-116`). **Es la misma magnitud que `sigma`**.
   - `iteraciones` es el número de ventanas.
   - `desviacion_error = std(e, ddof=1)`, `error_medio` es la media y `mae = mean(|e|)`.
   - `estabilidad_error = std(|e|, ddof=1)/mean(|e|)`.
   - `errores_extremos = detectar_errores_extremos(errores, periodos)`, con `observaciones` (un registro por ventana: `error_absoluto`, `z_modificado`…), `mediana_error_absoluto`, `mad_error_absoluto`, `factor` y `n` (el número de errores finitos).
5. **RMSE_h persistido** (`tabla_horizontes`, `backtesting.metricas`, sesión, CSV `rmse_horizonte`, interfaz e informes). Se calcula sobre la muestra rectangular común W* = n − 36 + 1, con orígenes 12…n−24. El walk-forward a horizonte h usa los orígenes 12…n−h. La matriz rectangular se filtra del mismo `backtesting_comparativo` (líneas 866 y 1190). En consecuencia, **cuando h = 24 las filas, su orden y la aritmética coinciden y la igualdad es exacta por construcción.**

## 2. Resultados (igualdad exacta `==`, sin tolerancias)

**Archivos:**
- Script: [`evidencia/diagnostico_vias_a_b.py`](evidencia/diagnostico_vias_a_b.py).
- Utilidades: [`evidencia/caso_ic95.py`](evidencia/caso_ic95.py).
- Salida: [`evidencia/salida_diagnostico_vias_a_b.txt`](evidencia/salida_diagnostico_vias_a_b.txt).

**Método:**
- Cada escenario ejecuta `ejecutar_proyeccion` real.
- El IC95 interno se captura con un espía justo antes de que se vacíe; el espía se restaura siempre.
- **A** lee el vector `error_absoluto`.
- **A'** reconstruye ese vector sin `error_absoluto`, con `|e| = mediana + z_modificado·MAD/factor`.
- **B1**, **B2**, **B4** y **B3** usan solo agregados.

| Escenario | n | A | A' | B1 `rmse`+`iteraciones` | B2 `desviacion_error`+`error_medio` | B4 `mae`+`estabilidad_error` | B3 RMSE_h+W |
|---|---|---|---|---|---|---|---|
| n48_h6, ondulada (B-A1) | 31 | **exacto** | **exacto** | **exacto** | **exacto** | **exacto** | aprox.: 0,249 (6,4 % del semiancho) |
| n72_h12, ruidosa | 49 | **exacto** | **exacto** | **exacto** | **exacto** | **exacto** | aprox.: 0,723 (12,5 %) |
| n38_h24, pocos pares | 3 | **exacto** | **exacto** | **exacto** | **exacto** | **exacto** | **exacto** |
| n60_h9, estacional | 40 | **exacto** | **exacto** | **exacto** | **exacto** | **exacto** | aprox.: 0,185 (9,9 %) |
| n48_h24, ondulada | 13 | **exacto** | **exacto** | **exacto** | 2,8·10⁻¹⁴ | **exacto** | **exacto** |
| n72_h24, ruidosa | 37 | **exacto** | **exacto** | **exacto** | **exacto** | **exacto** | **exacto** |
| n30_h3, historia insuficiente | — | no hay banda interna finita (`proyeccion_generada=False`, sin excepción) |||||

**Caso B-A1:**
- `exponencial_log_lineal_h6`, con 31 errores.
- `rmse` = `1.9063084328995537` = `sqrt(mean(error_absoluto²))`.
- `y_proj` = `121.58536382460937`.
- IC95 interno = (`117.69742214273187`, `125.47330550648688`). A, A', B1, B2 y B4 lo reproducen bit a bit.

**B3 fuera de h=24 es una aproximación, no una reconstrucción.** Respecto a la banda interna, el error es del 6–13 % del semiancho y del 0,16–0,42 % del pronóstico. En h=24 es exacta.

**Precisión de B3 según la superficie:**
- El objeto, `tabla_horizontes` y la sesión JSON llevan el `float` completo.
- El CSV escribe texto redondeado: en h=6 la diferencia es de 4,4·10⁻¹⁶. La banda de h=24 reconstruida con 15 cifras difiere en 1–3·10⁻¹⁴.

**Condiciones de validez, sin excepciones ocultas:**
- **A y A'.** `observaciones` está vacía cuando el MAD es nulo o no hay errores finitos (`metricas.py:60-71`; `calculable=False`). En los escenarios de esta carpeta hay observaciones en todas las entradas, y su número coincide con `iteraciones`, incluso cuando no hay ningún extremo (`cantidad`=0). Cuando existe, es el vector completo de |e|, no un subconjunto. Como `sigma` no depende del signo, basta con él.
- **B1, B2 y B4 usan `iteraciones` como n.** `iteraciones` cuenta también las predicciones no finitas (`backtesting.py:272`), mientras que el intervalo descarta los NaN. Si hubiera predicciones no finitas, el n correcto es `errores_extremos.n`, que también se publica. En estos escenarios ambos coinciden.
- **El recorte del límite inferior en 0** solo cambia la banda si `y − c·sigma < 0`, cosa que no ocurre aquí. Quien reconstruya debe aplicarlo igual que el motor.

## 3. Por qué no hay una corrección completa compatible con el contrato

- **B1:** `metricas.rmse` **es** `sigma_h`, y está publicado en las 504 entradas modelo×horizonte junto con su n.
- **B2:** sin `rmse`, `desviacion_error` (ddof=1) y `error_medio` dan `sigma` exacta, porque `sigma² = media² + desv²·(n−1)/n`.
- **B4:** sin `rmse`, `desviacion_error` ni `error_medio`, el par `mae` + `estabilidad_error` también da `sigma` exacta, porque `sigma² = mae²·(1 + estab²·(n−1)/n)`. Retirar las métricas «de dispersión» y conservar el MAE no cierra nada.
- **A':** quitar solo la clave `error_absoluto` de cada observación tampoco basta. `z_modificado`, con la mediana y el MAD publicados, devuelve el vector completo.
- **B3:** el **RMSE_h protegido** que se persiste (tabla de horizontes, sesión, CSV, interfaz e informes) reproduce **exactamente** la banda del paso 24 en cualquier serie. En los demás horizontes da una aproximación cercana.

Retirar solo el vector, como proponía el informe anterior, pondría en verde el contrato del vector y dejaría intactas las vías B. Lo demuestra `test_caracterizacion_no_go_retirar_solo_el_vector_no_cierra_p0c` (03), y sería un cierre falso de P0-C.

**El comentario de producción es incorrecto.** El de `COLUMNAS_OOS_RECONSTRUCTIVAS` (`servicio_proyeccion.py:625-656`) justifica conservar los agregados porque «de un promedio de cuadrados no se recupera la muestra». Es cierto, pero no hace falta la muestra: basta con `sigma` y `n`, y el RMSE **es** `sigma`. No lo corrijo, porque sería un cambio de producción (07 §4).

## 4. Decisión

**NO-GO para el cierre completo de P0-C.** Los agregados que el contrato protege bastan para reconstruir exactamente el IC95:
- RMSE y su n;
- desviación y media del error;
- MAE y estabilidad del error;
- RMSE_h con W en h=24.

Por eso no he suprimido métricas, no he introducido ruido, redondeos ni ocultación, y **no he cambiado producción**. Las alternativas están en 07 §3.
