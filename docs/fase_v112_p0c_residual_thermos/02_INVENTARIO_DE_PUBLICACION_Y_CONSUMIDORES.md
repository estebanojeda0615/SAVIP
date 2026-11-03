# 02 · Inventario de publicación y consumidores

**Herramientas.**
- [`evidencia/inventario_superficies.py`](evidencia/inventario_superficies.py), cuya salida está en [`evidencia/salida_inventario_superficies.txt`](evidencia/salida_inventario_superficies.txt).
- El detector `vectores_por_ventana` de [`evidencia/adversarial_p0c_residual_ic95.py`](evidencia/adversarial_p0c_residual_ic95.py).
- Un recorrido aparte que no deduplica alias.

**Caso principal:** n=48, h=6. Los agregados se comprobaron además en los otros cinco escenarios con banda (01 §2).

## 1. Matriz por ruta

| Ruta pública | Naturaleza | Quién la escribe | Consumidores | Capacidad reconstructiva **demostrada** | Efecto de quitarla | Propuesta |
|---|---|---|---|---|---|---|
| `backtesting_comparativo.<m>_h<p>.metricas.errores_extremos.observaciones[*].error_absoluto` (504 entradas; entre 13 y 36 registros por entrada en el caso principal) | **Vector** \|e\| por ventana, con `periodo`, `posicion`, `z_modificado` y `extremo` | `metricas.detectar_errores_extremos` ← `backtesting._metricas_backtesting` | Ninguno en la aplicación: la interfaz, la sesión, el CSV y los informes no lo leen (§2) | **Exacta** (vía A) | Ninguno funcional | Retirarla es posible, pero **por sí sola no cierra P0-C** (vía B). Mitigación en fase aparte (07 §3) |
| `backtesting_comparativo.<m>_h<p>.metricas.rmse` + `.iteraciones` (504) | Agregado residual | `backtesting._metricas_backtesting` (`calcular_rmse`) | Hoy, ningún lector en la aplicación además del propio servicio. Es la métrica por modelo y horizonte que documenta el banco de 21 candidatos | **Exacta** (vía B1): **es** `sigma_h` | Se perdería el RMSE por modelo y horizonte del walk-forward completo | **Protegido**: retirarlo exige revisar el contrato (07, alternativa B) |
| `…metricas.desviacion_error` + `.error_medio` (+ n) | Agregados residuales | Ídem | Ídem | **Exacta** (vía B2) | Ídem | Ídem |
| `…metricas.mae`, `mase`, `mape`, `smape`, `sesgo_medio`, `mad_error_absoluto`, `mediana_error_absoluto`, `cantidad`, `n`, `proporcion`, `umbral_z` | Agregados | Ídem | `presentacion_resultados._texto_errores_extremos` lee `cantidad`, `n`, `proporcion` y `umbral_z` del backtesting **publicado** (no del comparativo) | No demostrada: no dan `sigma` sin otra información | — | Conservar |
| `horizonte_info.tabla_horizontes[h].rmse` + `.W`, y su réplica en `backtesting.metricas.rmse` / `iteraciones` | **Agregado protegido** (RMSE_h rectangular W*) | `_metricas_horizonte_rectangular` | Interfaz, sesión JSON (`backtesting.metricas`), CSV (`rmse_horizonte`, `iteraciones_backtesting_horizonte`), informes | **Exacta en h=24** para cualquier serie, porque las muestras coinciden. En el resto de horizontes, **aproximada**: diferencias de 0,19 a 0,72 puntos (≈0,2–0,4 % del pronóstico) | Se perdería la evidencia OOS por horizonte que sostiene la tesis (REQ 16) | **Protegido**. No se toca |
| `backtesting_comparativo.<m>_h<p>.predicciones` | Diseño (`Periodo`, `t`, `Origen`, `Horizonte`, `Modelo`, `Modelo_codigo`, `Observaciones_entrenamiento`) | `_retirar_errores_oos_de_publicacion` ya retiró `Observado`, `Predicho`, `Error`… | — | Ninguna | — | Conservar |
| `backtesting_comparativo.<m>_h<p>.errores` | Lista | `ejecutar_backtesting` | — | Ninguna: está vacía en los casos examinados | — | — |
| `ci95_lo/hi`, `ci80_*`, `ci_*`, `stats.width*`, anchos relativos, cobertura | Intervalo | Ya vaciados por `_retirar_intervalo_de_publicacion` | — | No: valen `None` | — | Sin cambio |
| `proyecciones`, `y_proj`, `trayectoria_24_meses` | Punto | Motor | Todas las superficies | Aportan el centro de la banda; son necesarios y públicos por diseño | — | Conservar |

## 2. Superficies persistidas o visibles

| Superficie | Vector (vía A) | `sigma_h` exacta (B1/B2) | RMSE_h rectangular (B3) |
|---|---|---|---|
| Sesión JSON (`ControladorPrincipal._proyeccion_serializable`) | No: `error_absoluto` no aparece | No: no serializa `backtesting_comparativo` | **Sí**: `backtesting.metricas.rmse` y `iteraciones` |
| CSV de reproducibilidad | No | No | **Sí**: `rmse_horizonte` y `iteraciones_backtesting_horizonte` |
| `horizonte_info.tabla_horizontes` (objeto, interfaz e informes) | No | No | **Sí**: `rmse` y `W` para los 24 horizontes |
| DOCX y PDF, con o sin anexo de backtesting | No (verificado en AS-007) | No | Publican el RMSE por horizonte |
| Interfaz | No: solo conteos de extremos | No | Muestra el RMSE |

Conclusión: en lo que se persiste, el IC95 sigue siendo deducible a partir del RMSE_h protegido. Es exacto en el paso 24 y aproximado en los demás.

## 3. Alias

- **Sin deduplicar alias**, el objeto público solo tiene una forma con vector: `backtesting_comparativo.<m_h>.metricas.errores_extremos.observaciones`, con 504 apariciones (comprobado en n48_h6 y n72_h24).
- **Alias latente:** `_serializar_evaluaciones_horizonte` (`servicio_proyeccion.py:3718`) copia `errores_extremos_detalle = metricas.get("errores_extremos")`. Es el dict completo con `observaciones`. Esa función pertenece al subsistema heredado de 2D-1 y **no aparece en el objeto público actual**. Si alguna vez se reactivara, publicaría el vector por otra ruta. 2D-1 la retira.
- **Riesgo para una corrección futura:** los dicts de `metricas` son los mismos objetos que usa el cálculo interno. Cualquier saneamiento futuro tendría que operar después de todos los lectores, como ya hace `_retirar_intervalo_de_publicacion`. Hacer `pop` antes alteraría los diagnósticos.

## 4. Propuesta mínima

No hay ninguna propuesta mínima que **cierre** P0-C sin retirar agregados protegidos (01 §3).

La única acción mínima sin regresión sería retirar `observaciones` del comparativo publicado. Pero **solo mitiga la exposición del vector**: no hace irreconstruible la banda. Por eso no la he aplicado, y la dejo como opción para una fase separada (07, alternativa A).
