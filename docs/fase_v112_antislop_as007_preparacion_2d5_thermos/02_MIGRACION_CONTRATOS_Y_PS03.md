# 02 · Migración de contratos, PS-03 y constantes TRAMO

## 1. Qué es r3 y por qué bloqueaba 2D-5

`tests/test_residuales_auditoria_independiente_r3.py` es un **script**: tiene una lista `PRUEBAS` de 27 controles y `main()`, y ninguna función empieza por `test_`.
- Pytest **lo importa al recolectar** (el nombre empieza por `test_`), pero no recolecta ningún caso.
- Ningún perfil lo ejecuta: su único uso es `python tests/test_residuales_auditoria_independiente_r3.py`.

En la base importaba `tramo_evidencia_oos` y las tres `TRAMO_OOS_*`. Lo he comprobado retirando esos nombres **solo en memoria**, con un plugin de pytest que hace `delattr` sobre el módulo, sin tocar archivos:

| Árbol | Recolección con el retiro simulado | Ejecución directa de r3 con el retiro simulado |
|---|---|---|
| Base `6ac158d` | **4 errores**: los 3 históricos más `ImportError` en r3, `cannot import name 'TRAMO_OOS_DISPONIBLE'` | No importa |
| Esta fase `febd981` | **3 errores**, los históricos. 1 067 recolectadas | **21/27, idéntico** a la base |

Es exactamente el NO-GO que preveía el plan 2C: el perfil histórico pasaba de 3 a 4 errores. Evidencia en [`evidencia/simulacion_retiro_2d5.txt`](evidencia/simulacion_retiro_2d5.txt).

## 2. Tratamiento por control

El detalle de cada uno está en 01. Por categorías:

| Categoría | Controles | Tratamiento |
|---|---|---|
| **A. Vigentes sin cobertura recolectada** | C1–C7, C12 (parte vigente), HG5 (parte P0-E) | Migrados a `tests/test_as007_contratos_r3_vigentes.py`, 9 pruebas, en el perfil esencial. Usan los mismos datos (serie ondulada n=48, h=6) y las mismas superficies reales: objeto, DataFrame, `ControladorPrincipal._proyeccion_serializable`, `generar_csv_reproducibilidad`, el HTML de la interfaz y `docx_render`/`pdf_render` escritos en un `TemporaryDirectory`. No importan r3 ni recalculan el intervalo. Siguen también en r3 |
| **B. Vigentes ya cubiertos** | D, HG1–HG3 y los tramos de HG6 | D: `test_fase1a_selector_rectangular::test_rmse_reportado_coincide_con_sse_exacto` y `::test_as001_una_ulp_en_el_borde_de_dbl_max`. HG1/HG2/HG6, tramos y vocabulario: `test_fase2c_contratos_vigentes::test_texto_evidencia_oos_tres_tramos_sin_vocabulario_de_validacion`. HG1/HG3, W: `test_cierre_semantico_ps01_ps05::test_ps03_w_es_cero_exactamente_cuando_el_dato_no_existe` y `::test_ps02_…`. HG3 compara además contra `ejecutar_backtesting` con n<14, algo que nada más hace: se conserva en r3 |
| **C. Históricos o no vigentes** | B, G, C8–C11 y el final de HG6 | Esperan comportamiento anterior a N0=12/H=24: una serie de n=7 u 8 debía proyectar. B, G y HG6 fallan en la base; C8–C11 pasan sin ejercer nada, porque no hay proyección. No se recrean. La regla vigente («pocas ventanas no niegan el punto») la cubre `test_escasez_de_ventanas_entrega_el_punto_con_advertencia_y_sin_intervalo[36|37|41]`, con W*=1, 2 y 6. Se conservan en r3 como registro |
| **D. Ambiguos o que fallan en la base** | C12 (`Periodo`), HG4, HG5 (claves de traza), H1–H6 | **DECISIÓN PENDIENTE**, §5 |

**Sensibilidad de las 9 pruebas nuevas.** Rompí cada contrato en memoria con un plugin de mutación sin tocar producción. Las 9 pruebas pasan sin mutación y cada una de las 9 mutaciones hace fallar al menos su prueba ([`evidencia/mutaciones_pruebas_nuevas.txt`](evidencia/mutaciones_pruebas_nuevas.txt)):

| Mutación | Pruebas que fallan |
|---|---|
| `ci95_lo`/`ci95_hi` publicados | objeto |
| Tabla con `Origen` + `Error` numérico | objeto |
| `limite_superior_95` en proyecciones | DataFrame |
| «IC95 cuantil» en `model_name` | interfaz, DOCX y PDF |
| «cobertura efectiva» en la sesión | sesión |
| Columna `sigma_h` en el CSV | CSV |
| Sin `rmse` en las métricas | sesión y agregados |
| `evidencia_oos_provisional=False` | P0-E |

## 3. Cambio conservador en r3

**Qué cambia:**
- Se quitan los imports `tramo_evidencia_oos` y `TRAMO_OOS_*`.
- Se añade un `_tramo(ventanas)` local que clasifica según el texto que se publica (`_texto_evidencia_oos`): «Sin evidencia…», «…muy limitada…» o el resto. Las fronteras son las mismas que las de `tramo_evidencia_oos`: W ≤ 0, W < `MIN_ITERACIONES_WF_ESCENARIO` (3) y el resto.
- Las constantes pasan a ser literales: `"sin_evidencia_oos"`, `"evidencia_oos_muy_limitada"` y `"evidencia_oos_disponible"`. En HG4 el literal se compara con una clave de la traza, igual que antes la constante.

**Qué no cambia:** las 27 entradas de `PRUEBAS`, sus nombres, el orden, los datos y el resto de aserciones.

**Comprobación.**
- La ejecución directa antes y después da la misma salida línea a línea: **21/27, los mismos 6 FAIL con los mismos mensajes**, código 1 y unos 15 s en Qt offscreen, sin escribir en `docs/`.
- Al desplazar la frontera 3 de `_texto_evidencia_oos` en memoria, HG6 falla en la aserción de tramos; antes fallaba más adelante, en la proyección. El nuevo `_tramo` mantiene el contrato protegido ([`evidencia/r3_mutacion_frontera.txt`](evidencia/r3_mutacion_frontera.txt)).

**Destino recomendado de r3.** Dividirlo en dos:
- los contratos vigentes ya están en pytest (A);
- el script se queda como registro histórico ejecutable, sin importar funciones candidatas a retiro.

No se borra ni se retira ningún control en esta fase.

## 4. PS-03 y constantes `TRAMO_OOS_*`

**Id esencial afectado:** `tests/test_cierre_semantico_ps01_ps05.py::test_ps03_la_escasez_de_evidencia_no_equivale_a_su_inexistencia`.
- Importa `tramo_evidencia_oos` y `TRAMO_OOS_*` **dentro de la función**, así que con el retiro simulado no da error de recolección: **falla al ejecutarse** con `ImportError`. Comprobado: 1 fallo y 27 PASS en PS-01…05, 2C y AS-007.
- **Se conserva sin cambios en esta fase.**

| Aserción de PS-03 | Cobertura equivalente vigente |
|---|---|
| W=0 → sin evidencia | `test_texto_evidencia_oos_tres_tramos_sin_vocabulario_de_validacion`: `textos[0].startswith("Sin evidencia fuera de muestra")`, más `None` y `"x"` → igual que 0 |
| W=1 y W=2 → muy limitada | Mismo test: W ∈ {1, `MIN_ITERACIONES_WF_ESCENARIO`−1 = 2} contiene «muy limitada» y `(n=W)` |
| W=3 y W=50 → disponible | Mismo test: texto exacto `Evidencia fuera de muestra disponible (n=W).` |
| El tramo «disponible» no se llama validado ni certificado (W=3, 10, 50) | Mismo test, sobre el **texto publicado**, que es más fuerte que el nombre interno del tramo: `not re.search(r"valid\|certific", texto, re.I)` para W=0, 1, 2, 3 y 50 |
| *(docstring)* «W en {1,2} entrega con advertencia» | `test_escasez_de_ventanas_entrega_el_punto_con_advertencia_y_sin_intervalo[36\|37\|41]`: W*=1 y 2 entregan el punto finito, la trayectoria de 24 y la advertencia de escasez, sin intervalo. Ojo: el umbral vigente de la advertencia es `MIN_ITERACIONES_WF` (6), no 3 (registro 02 de 2C) |
| W=10 no validado | Sin caso literal W=10. La regla es la misma rama del código que W=3 y W=50, ambos cubiertos. Si se quiere el caso exacto, añadir 10 a la lista del test 2C en el lote 2D-5 |

**Condición exacta para retirar el id en 2D-5:**
1. autorización expresa del propietario para retirar ese id esencial;
2. retirarlo en el **mismo commit** que la función, porque separados el primer commit quedaría en rojo;
3. `test_texto_evidencia_oos_tres_tramos_…` y `test_escasez_…[36|37|41]` presentes y en PASS en el perfil esencial;
4. el informe del lote lista el id retirado y compara los JUnit con `comparar_ids_esenciales.py`.

**Constantes `TRAMO_OOS_*`:**
- Consumidores en todo el repositorio: solo `tramo_evidencia_oos`, PS-03 y, hasta esta fase, r3.
- Además aparecen en el docstring de `_texto_evidencia_oos` («Ver `TRAMO_OOS_SIN_EVIDENCIA`»).
- Ningún consumidor vigente de producción. `generador_reportes.py:381` lee la **clave** `"tramo_evidencia_oos_horizonte_solicitado"`, un texto que no es la función ni las constantes, y nadie la produce (§5).

**Recomendación:** retirar las constantes **con** la función en 2D-5, con autorización expresa, porque el prompt de esta fase las protege. En ese caso hay que trasladar al docstring de `_texto_evidencia_oos` el bloque de comentario HGRID de las líneas ~2030-2041, que explica que los tramos no son umbrales y fija el vocabulario prohibido, y quitar la referencia «Ver `TRAMO_OOS_SIN_EVIDENCIA`». Retirar solo la función y dejar las constantes huérfanas también es posible, pero deja nombres sin uso.

## 5. Decisiones pendientes de AS-007 (no se eligió ningún comportamiento)

1. **C12 · `Periodo` en la tabla de ventanas.** Hoy la tabla publica `Origen` y `Horizonte`. `Periodo` no está entre `COLUMNAS_OOS_RECONSTRUCTIVAS`, así que no parece un retiro P0-C intencionado. ¿Debe publicarse? La parte vigente de C12 queda cubierta sin esa columna.
2. **HG4/HG5 · claves de traza sin productor.** `tramo_evidencia_oos_horizonte_solicitado`, `ventanas_oos_horizonte_solicitado`, `primer_origen_provisional` y `formula_ventanas_oos` no las produce la ruta vigente, pero `generador_reportes.py:381-385` todavía las lee. Es el mismo patrón que AS-004. ¿Se retiran esas lecturas o se publican las claves? No forma parte de 2D-5.
3. **H1–H6 · P0-H con entrada heredada.** `_estructurar_resultado_horizontes` es vigente, pero r3 la alimenta con `evaluaciones` con forma del clasificador heredado (`permitido_para_proyeccion_tecnica`). El destino se decide con 2D-1/2D-3. Pasan y se conservan.
4. **mape/smape** (C12): ligado a «MAPE no calculable», decisión de 2D-3. No se exigen en la prueba nueva.

## 6. Otros bloqueos de AS-007 que siguen abiertos (no resueltos por sanear r3)

- **`test_p0c_objeto_publico_sin_intervalo.py` y `test_p0c_regresion_negativa_c2.py`:** siguen dando error de recolección (`ModuleNotFoundError` de `tests.test_p0c_retiro_intervalos_no_sustentados`). Bloquean 2D-3.
- **`test_regresiones_auditoria_independiente_bghc.py`:** script que importa funciones heredadas de 2D-3. No se ha tratado.
- **PS-02 / anexo DANE:** sin el anexo confidencial, PS-02 pasa sin comprobar nada. Sigue pendiente.
- `test_equivalencia_presupuestal_fase_4e_b.py` es el tercer error histórico de recolección y no tiene relación con 2D-5.
