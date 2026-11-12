# 02 · AS-028: las tres pruebas del script que dependen de 2D-1

**Archivo:** `pruebas/prueba_horizonte_dinamico_ui_reportes.py`. Las líneas citadas son las de la base `102f194`.

## 1. Método

Cada prueba se analizó por separado, aserción por aserción, con cuatro fuentes:

1. **Estado en la base inmutable:** `pytest` sobre una copia limpia de `102f194` (`evidencia/script_base_pytest.xml`).
2. **Aserciones con la entrada del propio test:** cada aserción se evalúa por separado contra la función heredada, con la misma entrada sintética del test. La herramienta es `evidencia/scripts/asercion_por_asercion.py` y su salida, `evidencia/asercion_por_asercion.json`.
3. **Las mismas aserciones sobre la salida productiva real:** `ejecutar_proyeccion` con la misma serie estable de 120 meses del script, para h=12 y h=18. Sirve para saber si la propiedad **existe** en la ruta vigente.
4. **Alcanzabilidad:**
   - grafo AST (`evidencia/grafo_102f194_2d1.json`, generado con `docs/fase_v112_antislop_02a_as003/evidencia/grafo_as003.py`);
   - espías pasivos sobre 28 ejecuciones reales (7 series × h ∈ {1, 12, 18, 24}) (`evidencia/sonda_claves_base.json`);
   - pruebas esenciales vigentes.

**Hechos comunes a las tres**

- `determinar_horizonte_maximo_estadistico` (`servicio_proyeccion.py` L3274-3531):
  - **no es alcanzable desde producción** (grafo: `produccion=false`, `referenciado_por=[]`);
  - recibe **0 llamadas** en las 28 ejecuciones de la sonda (series drift, holt, estable de 120 meses, historia insuficiente, sin valores válidos, valor negativo y valor cero, cada una con h=1, 12, 18 y 24);
  - el espía esencial de la Fase 1A exige esas mismas 0 llamadas en la ruta productiva.
- **Ruta vigente** (`_ejecutar_proyeccion_base` L1338-1373):
  - publica `horizonte_info` con `alcance_maximo_proyeccion=24`, `n0_backtesting`, `w_estrella`, el modelo seleccionado y su RMSE, y `tabla_horizontes` de h=1 a h=24;
  - **no** publica `horizonte_maximo_recomendado`, `mensaje_ui`, `horizontes_no_recomendables`, `tipo_uso_recomendado` ni `mensaje_no_recomendables`. Las 27 claves productivas están en `asercion_por_asercion.json`, `contexto_productivo_h18`.
- **Metodología vigente** (N0=12/H=24):
  - el alcance es fijo y se entrega cualquier h entre 1 y 24 (h=18 incluido: `horizonte_permitido=18`, `proyeccion_generada=True`);
  - **no existe** la clasificación por horizonte en técnico/escenario/no recomendable.

## 2. `test_horizonte_maximo_no_es_18_si_h18_no_cumple` (L207-233). Base: **PASS**

**Entrada:** 12 evaluaciones sintéticas (h=1..12, técnicas) más h=18 no recomendable, construidas con `_evaluacion_horizonte`. Se pasan a `determinar_horizonte_maximo_estadistico(None, None, None, evaluaciones, None, horizonte_solicitado=12)`.

| # | Aserción | Con la entrada del test | Sobre la salida productiva (h=12 / h=18) | Contrato |
|---|---|---|---|---|
| 1 | `horizonte_maximo_recomendado == 12` | True | `KeyError` / `KeyError` | Histórico: máximo recomendado por clasificación |
| 2 | `horizonte_maximo_permitido_como_escenario == 0` | True | `KeyError` / `KeyError` | Histórico: escenario puro |
| 3 | `horizontes_no_recomendables == [18]` | True | `KeyError` / `KeyError` | Histórico: lista de no recomendables |
| 4 | `"h=18" in mensaje_ui` | True | `KeyError` / `KeyError` | Histórico: mensaje de la UI antigua |
| 5 | `tipo_uso_recomendado == "Proyección extendida con cautela"` | True | `KeyError` / `KeyError` | Histórico: tipo de uso por tramo |

**Conclusión: HISTÓRICA / NO APLICA.**
- Las cinco aserciones describen la regla abandonada del «máximo horizonte por evidencia de cada h». Solo son verdaderas sobre una función que ninguna ruta productiva ejecuta.
- La regla vigente equivalente es la contraria: alcance fijo de 24 meses, y el horizonte pedido no cambia ni el modelo ni la trayectoria. La protegen estos tests esenciales:
  - `tests/test_metodologia_n0_12_h24.py::test_b_h_operativo_max_es_24`: H=24, se acepta h=24 y se rechaza h=25;
  - `tests/test_metodologia_n0_12_h24.py::test_efg_horizonte_solicitado_no_cambia_modelo_ni_trayectoria`: h=6, 12, 17 y 24 dan el mismo modelo, el mismo RMSE y la misma trayectoria de 24 meses;
  - `tests/test_fase1a_selector_rectangular.py::test_la_ruta_productiva_usa_el_selector_rectangular_y_ningun_selector_retirado`: 0 llamadas a `determinar_horizonte_maximo_estadistico`;
  - `tests/test_fase2c_contratos_vigentes.py::test_la_ruta_vigente_no_referencia_el_subsistema_heredado`: análisis AST de la ruta vigente;
  - `tests/test_resultado_horizonte_solicitado.py::test_maximo_tarjeta_usa_alcance_operativo_vigente`: la tarjeta «máximo» muestra el alcance de 24 meses y no el «horizonte máximo recomendado».
- **No se inventa un reemplazo.** La regla no existe hoy, y reintroducirla sería resucitar el mecanismo retirado.
- La aritmética interna de la función muerta sigue cubierta, mientras exista, por 6 esenciales de `test_resultado_horizonte_solicitado` y 2 de `test_presentacion_resultados` (05). Esta baja no reduce esa cobertura.

## 3. `test_mensaje_no_recomendables_no_imprime_lista_vacia` (L246-254). Base: **PASS**

**Entrada:** 6 evaluaciones sintéticas con estado «Alta confiabilidad relativa» (un peldaño de la escalera retirada en P0-G) y `horizonte_solicitado=6`.

| # | Aserción | Entrada del test | Productiva h=12 / h=18 | Contrato |
|---|---|---|---|---|
| 1 | `horizontes_no_recomendables == []` | True | `KeyError` / `KeyError` | Histórico |
| 2 | `"[]" not in mensaje_ui` | True | `KeyError` / `KeyError` | Histórico: formato del mensaje de la función muerta |
| 3 | `"No se identificaron horizontes no recomendables" in mensaje_no_recomendables` | True | `KeyError` / `KeyError` | Histórico |
| 4 | `primer_horizonte_no_viable == 0` | True | `KeyError` / `KeyError` | Histórico |

**Conclusión: HISTÓRICA / NO APLICA.**
- La propiedad «no imprimir una lista vacía» se refiere a un texto (`mensaje_ui` y `mensaje_no_recomendables`) que **solo** compone la función muerta.
- La UI vigente toma su encabezado de `resultado_horizonte_solicitado.razon_principal` en las 28 ejecuciones de la sonda (comparación por prefijo, porque `_encabezado` puede recortar el texto). Nunca recurre a `mensaje_ui` (`sonda_claves_base.json`, campo `encabezado_ui_fuente`).
- No hay ninguna lista de «no recomendables» que formatear en la ruta vigente.

## 4. `test_h18_no_se_redacta_como_intervalos_aceptables` (L257-276). Base: **FAIL** (L269)

Esta prueba mezcla dos contratos. Se evaluaron por separado.

**(a) Mitad del cálculo heredado.** Usa la misma estructura de entrada que la prueba del §2 (h=1..12 técnicos y h=18 no recomendable). Aplica todo lo dicho allí.

**(b) Mitad del generador.** `_lineas_horizontes` y `_lineas_determinacion_horizonte` (`generador_reportes.py` L1038-1098):
- se reescribieron en el «Prompt 12» para leer la estructura rectangular vigente. Su comentario dice «Retirada la semántica triangular»;
- **ya no redactan** el «Horizonte máximo recomendado» ni la fila «18 meses | permitido=…»;
- además, solo son alcanzables a través de `generar_reporte_html`, que no es alcanzable desde producción (04).

| # | Aserción | Entrada del test | Productiva h=12 / h=18 | Contrato |
|---|---|---|---|---|
| 1 | `"Horizonte máximo recomendado: 12" in lineas` | **False** (aquí falla el test en la base) | False / False | Redacción anterior a 12/24 |
| 2 | `"h=18 no recomendable" in lineas` | False | False / False | Redacción anterior |
| 3 | `"18 meses" in lineas` | True, por la fila `h=18 meses \| W_h=None…` | True / True | Trivial: cualquier tabla de 24 filas la contiene |
| 4-6 | `permitido=No`, `técnico=No` y `escenario=No` en la fila `18 meses \|` | `TypeError`: la fila ya no existe | False / False | Redacción anterior |
| 7 | `"backtesting e intervalos aceptables" not in linea_h18` | `TypeError` | True / True (vacua) | La cadena **solo** existe en el fixture del propio script (`_evaluacion_horizonte`, L122). No aparece en `app_icociv/` ni en `tests/` |

**Conclusión: HISTÓRICA / NO APLICA en las dos mitades.**
- La única propiedad que podría parecer de informes («no presentar como aceptables los intervalos de un horizonte no recomendable») no tiene objeto en la ruta vigente:
  - no hay horizontes no recomendables entre 1 y 24;
  - el informe productivo no publica intervalos (P0-C, fuera de alcance y sin cambios).
- La redacción vigente de `_lineas_*` sigue protegida por un esencial que esta fase no toca: `tests/test_pool_calendario_fourier_seasonal.py::test_casoJ_ids_internos_no_visibles_en_ui_ni_reportes`.
- Su FAIL histórico **desaparece por una baja justificada**, no porque cambie una expectativa: no hay ninguna aserción reescrita.

## 5. Cambio aplicado

| Commit | Cambio |
|---|---|
| `5133abc` | Se retiran las tres pruebas y sus tres llamadas en `main()`. Se añade una lápida no ejecutable en el lugar de la primera. En este commit se retiró también el auxiliar `_evaluacion_horizonte`, que solo usaban ellas |
| `7993060` | **Se restaura `_evaluacion_horizonte` byte a byte**, igual que en `102f194`. Motivo: la autorización cubre **solo** las tres pruebas y sus llamadas en `main()`; el auxiliar no está en esa lista. Queda **sin uso**, como candidato a retiro en una fase futura autorizada. La lápida lo indica |
| `56d9562` | **Último commit de código.** Lápida corregida tras la 1.ª pasada de Thermos: un nombre de test por línea (antes uno quedaba partido y no se encontraba con grep) y cita del contrato vigente (`test_metodologia_n0_12_h24::test_b…` y `::test_efg…`). Solo comentarios |

**Diff neto en el script frente a `102f194`:** +9 / −63. Contiene la lápida de 9 líneas, las tres funciones de test y las tres llamadas de `main()`. **Ninguna** de las otras 26 pruebas cambia, y tampoco sus aserciones, el orden de `main()` ni las pruebas drift/holt de AS-004.

**Texto anterior recuperable:**

```bash
git show 102f194cfffc4f92d57006f4b9a0b80eb0b225d1:pruebas/prueba_horizonte_dinamico_ui_reportes.py
```

**Comprobaciones estáticas del archivo final**
- 26 funciones `test_*` y 26 llamadas en `main()`, el mismo conjunto en los dos casos.
- Ninguna referencia ejecutable a `determinar_horizonte_maximo_estadistico`: solo aparece en el comentario de la lápida.
- `pytest --collect-only` recoge 26 tests.

## 6. Recuentos (comparación por id en 07)

| | Base `102f194` | Final `56d9562` (medido) |
|---|---|---|
| Tests | 29 | 26 |
| PASS | 21 | **19** (coincide con la predicción condicional) |
| FAIL | 8 | **7** |

Bajas: dos PASS y un FAIL, las tres justificadas arriba. Los 7 FAIL históricos restantes **no se tocan**:
- h25 estable, h25 errático y parámetros drift, que fallan con `ValueError` por h=25;
- pdf/docx con escenario;
- drift y holt, que dependen de AS-004;
- docx 777.
