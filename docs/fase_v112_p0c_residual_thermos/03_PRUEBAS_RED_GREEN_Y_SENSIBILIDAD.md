# 03 · Prueba adversarial RED y sensibilidad

**No hay GREEN.** El contrato de irreconstruibilidad del IC95 es inviable mientras se conserven los agregados protegidos (01). Por eso **no hay corrección**, y tampoco un GREEN fingido.

## 1. Prueba adversarial (diagnóstica, fuera del perfil esencial)

**Archivo:** [`evidencia/adversarial_p0c_residual_ic95.py`](evidencia/adversarial_p0c_residual_ic95.py).
- Vive en `docs/` y su nombre no empieza por `test_`. Por eso `pytest --collect-only` no la recoge y `scripts/pruebas_fase0.py` no la asigna a ningún perfil.
- No deja el CI en rojo y no usa `skip` ni `xfail`.

**Comando:**

```text
QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 python -m pytest docs/fase_v112_p0c_residual_thermos/evidencia/adversarial_p0c_residual_ic95.py -p no:cacheprovider -q -rA
```

**Ejecución sobre la base `dfcaaa9`.** La rama no cambia producción, así que la base es el mismo código. Entorno de 00. **Código de salida 1**: 4 fallos y 13 PASS en 25,75 s. Salida en [`evidencia/salida_adversarial_red_base.txt`](evidencia/salida_adversarial_red_base.txt).

| Prueba | Casos | Resultado en la base | Qué significa |
|---|---|---|---|
| `test_red_sin_vector_individual_de_errores_oos` | n48_h6, n72_h12, n38_h24, n72_h24 | **4 FAIL** | Mensaje: «Vector de errores OOS por ventana publicado (vía A, reconstruye el IC95): 504 rutas; formas: ['resultado.backtesting_comparativo.<modelo_h>.metricas.errores_extremos.observaciones[*].error_absoluto']» |
| `test_comparativo_conserva_agregados` | 4 | PASS | El comparativo publica `rmse`, `mae`, `mase`, `iteraciones` y `sesgo_medio` |
| `test_via_b_el_rmse_del_comparativo_reconstruye_el_ic95_exacto` | 4 | **PASS** | Con `metricas.rmse` y `iteraciones`, sin leer el vector, se obtiene el IC95 interno **exacto** (`==`). Esto **demuestra la contradicción**; no es un éxito |
| `test_via_b_el_rmse_h_persistido_reconstruye_el_ic95_exacto_en_h24` | n38_h24, n72_h24 | **PASS** | Con `tabla_horizontes[24].rmse` y `W` sale la banda exacta del paso 24 |
| `test_historia_insuficiente_no_rompe_el_recorrido` | n=30 | PASS | Sin proyección y sin vectores, y el recorrido no falla |
| `test_el_recorrido_tolera_none_y_estructuras_faltantes` | sintético | PASS | Admite entradas `None` y `observaciones` vacías o `None` |
| `test_entradas_sin_extremos_siguen_publicando_el_vector` | n48_h6 | PASS | Un candidato con `cantidad == 0` publica igualmente `observaciones` completas (= `iteraciones`) |

**Por qué no es un falso verde ni un falso rojo:**
- **El detector recorre todo el objeto:** dicts, listas, tuplas, DataFrames, Series y arrays, con protección de ciclos. Busca listas de registros, columnas y secuencias con nombres de error, observado o predicho.
- **El fallo da la ruta real** y el número de apariciones.
- **Las pruebas de la vía B usan igualdad exacta**, sin tolerancia, y comprueban antes que existe una banda interna y que no se publica.

## 2. Sensibilidad (mutaciones en memoria, sin tocar producción)

Script: [`evidencia/mutaciones_adversarial.py`](evidencia/mutaciones_adversarial.py). Salida: [`evidencia/salida_mutaciones_adversarial.txt`](evidencia/salida_mutaciones_adversarial.txt).

| Mutación | Detector | Lectura |
|---|---|---|
| M0, base | 504 rutas | RED |
| **M1, «corrección parcial»: retirar `observaciones` de todo el comparativo** | **0 rutas** (la prueba RED pasaría a verde) | **…pero la vía B sigue exacta: `True`.** Es exactamente el cierre falso que el prompt prohíbe |
| M2, lista de registros con `Error` en otra ruta | detectado | |
| M3, columna `Predicho` en `backtesting.predicciones` | detectado | |
| M4, clave `error_absoluto` con una secuencia numérica | detectado | |
| M5, DataFrame anidado con `Observado` | detectado | |
| M6, un único registro (no es un vector) | no detectado (correcto) | |

## 3. Huella y regresión

**Huella.** No hay cambios de producción. `huella_semantica.py` (Fase 2A) en la rama nueva da 20/20 casos y **0 diferencias**. SHA-256 `d6be699b700b3fa3379c743cc9d0ccbf5c185cacfa228208dbb95c2735370191`, idéntico al de la base ([evidencia](evidencia/huella_resumen.txt)).

**Comparador con lista blanca (§5.1):** no aplica, porque no se retiró ninguna ruta.

**Perfil esencial y golden:** son los de `dfcaaa9`. La rama solo añade documentación, scripts en `docs/` y dos líneas de configuración. El CI de la rama los ejecuta (06).
