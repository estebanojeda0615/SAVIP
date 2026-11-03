# 02 · Inventario de publicación y consumidores

**Herramientas:**
- [`evidencia/inventario_superficies.py`](evidencia/inventario_superficies.py), con su salida en [`evidencia/salida_inventario_superficies.txt`](evidencia/salida_inventario_superficies.txt);
- el detector `vectores_por_ventana` de [`evidencia/adversarial_p0c_residual_ic95.py`](evidencia/adversarial_p0c_residual_ic95.py);
- un recorrido sin deduplicar alias. Lo hice yo en la sesión y no está versionado; la revisión Thermos de corrección lo repitió por su cuenta con el mismo resultado (05).

El caso principal es n48_h6. Los agregados se comprobaron además en los otros cinco escenarios con banda (01 §2).

## 1. Matriz por ruta

| Ruta pública | Naturaleza | Quién la escribe | Consumidores | Capacidad reconstructiva **demostrada** | Efecto de quitarla | Propuesta |
|---|---|---|---|---|---|---|
| `backtesting_comparativo.<m>_h<p>.metricas.errores_extremos.observaciones[*].error_absoluto` (504 entradas; 13–36 registros por entrada en n48_h6) | **Vector** \|e\| por ventana, con `periodo`, `posicion`, `z_modificado` y `extremo` | `metricas.detectar_errores_extremos` ← `backtesting._metricas_backtesting` | Ninguno en la aplicación: interfaz, sesión, CSV e informes no lo leen (§2) | **Exacta** (vía A) | Ninguno funcional | Se puede retirar, pero **eso solo no cierra P0-C** (vía B). Mitigación en una fase aparte (07 §3) |
| `…metricas.rmse` + `.iteraciones` (504) | Agregado residual | `backtesting._metricas_backtesting` (`calcular_rmse`) | Fuera del servicio, ningún lector en la aplicación. Documenta el RMSE por modelo y horizonte del banco de 21 candidatos | **Exacta** (vía B1): **es** `sigma_h` | Se pierde el RMSE por modelo y horizonte del walk-forward completo | **Protegido**. Retirarlo exige revisar el contrato (07, alternativa B) |
| `…metricas.desviacion_error` + `.error_medio` (+ n) | Agregados residuales | Ídem | Ídem | **Exacta** (vía B2) | Ídem | Ídem |
| `…observaciones[*].z_modificado` + `errores_extremos.mediana_error_absoluto`, `mad_error_absoluto`, `factor` | El vector por ventana en otra escala, más sus parámetros | `metricas.detectar_errores_extremos` | Ninguno | **Exacta** (vía A'): `\|e\| = mediana + z·MAD/factor`. Por eso **quitar solo `error_absoluto` no basta** | Ninguno funcional | Si se retira el vector, retirar el registro por ventana completo, no solo una clave |
| `…metricas.mae` + `.estabilidad_error` (+ n) | Agregados residuales | `backtesting._metricas_backtesting` | `estabilidad_error`: ningún lector fuera del servicio. `mae`: es el MAE por modelo y horizonte | **Exacta** (vía B4): `sigma² = mae²·(1 + estab²·(n−1)/n)` | Ídem B1 | **Protegido** (MAE). Ídem B1 |
| `…metricas.mase`, `mape`, `smape`, `sesgo_medio`; `errores_extremos.cantidad`, `n`, `proporcion`, `umbral_z` | Agregados | Ídem | `presentacion_resultados._texto_errores_extremos` lee `cantidad`, `n`, `proporcion` y `umbral_z` del backtesting **publicado**, no del comparativo | No hay ninguna vía demostrada en esta fase. Por separado no dan `sigma`; no he explorado todas las combinaciones | — | Conservar |
| `backtesting_comparativo.<m>_h<p>.interpretacion` (504) | Texto con «MAPE=…, MASE=…, RMSE=x.xxx, MAE=…» | `backtesting.interpretar_backtesting` (`backtesting.py:409-413`) | Ninguno fuera del servicio para el comparativo | **Casi exacta** (vía B5): con `iteraciones`, error de la banda ≤ c(n)·5·10⁻⁴, que en los escenarios es el 0,004–0,05 % del semiancho, en todos los horizontes | Se pierde una lectura textual por candidato | Si algún día se retiran los agregados numéricos (alternativa B), hay que quitar las cifras de este texto o regenerarlo |
| `horizonte_info.tabla_horizontes[h].rmse` + `.W`, y su réplica en `backtesting.metricas.rmse` / `iteraciones` | **Agregado protegido** (RMSE_h rectangular W*) | `_metricas_horizonte_rectangular` | Interfaz (comprobado: el HTML muestra 1,9151 y 13), informes (comprobado), sesión JSON y CSV | **Exacta en h=24** para cualquier serie, porque las muestras coinciden. Desde el CSV, a 10⁻¹⁴ por el redondeo del texto. En el resto de horizontes, solo **aproximación**: 6–13 % del semiancho, 0,16–0,42 % del pronóstico | Se pierde la evidencia OOS por horizonte que sostiene la tesis (REQ 16) | **Protegido**. No se toca |
| `backtesting_comparativo.<m>_h<p>.predicciones` | Diseño: `Periodo`, `t`, `Origen`, `Horizonte`, `Modelo`, `Modelo_codigo`, `Observaciones_entrenamiento` | `_retirar_errores_oos_de_publicacion` ya retiró `Observado`, `Predicho`, `Error`… | — | Ninguna | — | Conservar |
| `backtesting_comparativo.<m>_h<p>.errores` | Lista | `ejecutar_backtesting` | — | Ninguna: está vacía en los casos examinados | — | — |
| `ci95_lo/hi`, `ci80_*`, `ci_*`, `stats.width*`, anchos relativos y cobertura | Intervalo | Ya vaciados por `_retirar_intervalo_de_publicacion` | — | Ninguna: valen `None` | — | Sin cambio |
| `proyecciones`, `y_proj`, `trayectoria_24_meses` | Punto | Motor | Todas las superficies | Aportan el centro de la banda; son necesarios y públicos por diseño | — | Conservar |

## 2. Superficies persistidas o visibles

| Superficie | Vector (vía A) | `sigma_h` exacta (B1/B2) | RMSE_h + W (B3) |
|---|---|---|---|
| Sesión JSON (`ControladorPrincipal._proyeccion_serializable`) | No: no contiene `error_absoluto` | No: no serializa `backtesting_comparativo` | **Sí**, en `backtesting.metricas` (`float` completo) |
| CSV de reproducibilidad | No | No | **Sí**: `rmse_horizonte` (texto con redondeo, diferencia de 4,4·10⁻¹⁶) e `iteraciones_backtesting_horizonte` |
| `horizonte_info.tabla_horizontes` (objeto, que alimenta interfaz e informes) | No | No | **Sí**, para los 24 horizontes |
| DOCX y PDF, con o sin anexo de backtesting | No (verificado en AS-007) | No | Sí: el texto del informe técnico lleva el RMSE_h (1,9151) y las 13 ventanas |
| Interfaz (HTML de resultados y detalle) | No: solo los conteos de extremos | No | Sí: muestra el RMSE_h (1,9151) y las 13 ventanas |

**Conclusión:** en lo persistido y visible, el IC95 sigue siendo deducible a partir del RMSE_h protegido. Es exacto en el paso 24 y aproximado en los demás.

## 3. Alias

- **Sin deduplicar alias**, el objeto público tiene una sola forma con vector: `backtesting_comparativo.<m_h>.metricas.errores_extremos.observaciones`, con 504 apariciones (n48_h6 y n72_h24).
- **Alias latente.** `_serializar_evaluaciones_horizonte` (`servicio_proyeccion.py:3718`) copia `errores_extremos_detalle = metricas.get("errores_extremos")`: el dict completo, `observaciones` incluidas. Pertenece al subsistema heredado de 2D-1 y **no aparece en el objeto público actual**. Si se reactivara, publicaría el vector por otra ruta. 2D-1 la retira.
- **Precaución para cualquier corrección futura.** Los dicts de `metricas` son los mismos objetos que usa el cálculo interno. Un saneamiento tiene que hacerse después de todos los lectores, como ya hace `_retirar_intervalo_de_publicacion`. Un `pop` previo alteraría los diagnósticos.

## 4. Propuesta mínima

No existe una propuesta mínima que **cierre** P0-C sin retirar agregados protegidos (01 §3).

La única acción mínima sin regresión es retirar `observaciones` del comparativo publicado. **Solo mitiga la exposición del vector**: la banda sigue siendo reconstruible. Por eso no la he aplicado y queda como opción para una fase separada (07, alternativa A).
