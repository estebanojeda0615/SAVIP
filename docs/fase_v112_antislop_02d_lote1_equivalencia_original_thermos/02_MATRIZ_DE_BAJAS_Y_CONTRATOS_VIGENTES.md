# 02 · Matriz de bajas y contratos vigentes (G2)

**Fuente primaria:** `docs/fase_v112_antislop_as028_preparacion_2d1_as004_thermos/05_MAPA_PRUEBAS_ESENCIALES_2D1.md` y `06_SIMULACION_SIN_MODIFICAR_PRODUCCION.md`.

Las aserciones se extrajeron una a una por AST sobre la base `8e5a62b`: `evidencia/asserts_afectados_8e5a62b.txt`. Todos los ids de este documento están en **PASS** en la base (809/809).

## 1. Las ocho bajas esenciales autorizadas

En los ocho casos, todas las aserciones leen la salida de `determinar_horizonte_maximo_estadistico`, alimentada con evaluaciones **sintéticas**. Esa función no se invoca desde ninguna ruta productiva: 0 llamadas en 28 ejecuciones reales más la sesión heredada (01). Ninguna aserción observa `ejecutar_proyeccion`, la UI productiva, los informes ni los exportables. Las propiedades que comprueban **no existen** en el `horizonte_info` vigente; sobre la salida productiva, todas las claves leídas darían `KeyError` (AS-028/02).

| # | Id (`tests/…`) | Aserciones exactas (sobre la salida de la función muerta) | Qué comprobaba | Por qué se retira | Contrato vigente que protege el comportamiento real |
|---|---|---|---|---|---|
| 1 | `test_resultado_horizonte_solicitado.py::test_maximos_se_derivan_de_clasificaciones_y_no_del_limite_de_grilla` | `horizonte_maximo_recomendado==8`, `horizonte_maximo_permitido_como_escenario==11`, `horizonte_maximo_evaluado==12`, `primer_horizonte_no_viable==12`, `horizonte_maximo==8` | Máximos por clasificación técnico/escenario de la rejilla triangular | La regla se abandonó con N0=12/H=24: el alcance es fijo (24) y no se clasifica por horizonte | `test_metodologia_n0_12_h24.py::test_b_h_operativo_max_es_24` y `::test_efg_horizonte_solicitado_no_cambia_modelo_ni_trayectoria`; `test_resultado_horizonte_solicitado.py::test_maximo_tarjeta_usa_alcance_operativo_vigente` |
| 2 | `…::test_limite_evaluable_se_informa_sin_convertirlo_en_validez_absoluta` | `horizonte_maximo_recomendado==5`, `horizonte_maximo_evaluado==5`, `horizonte_maximo_busqueda_configurado==10`, `maximo_recomendado_es_limite_observado is True`, `primer_horizonte_no_viable==0`, `tipo_parada=="evidencia_oos_insuficiente"`, `horizontes_no_evaluados==[6..10]` | Parada de la evaluación por falta de evidencia | Con 12/24, W* es común a h=1..24 y no hay parada por horizonte. La historia insuficiente se trata antes y de forma explícita | `test_metodologia_n0_12_h24.py::test_i_historia_insuficiente_devuelve_estado_explicito_no_fallback` y `::test_i_frontera_n36_es_suficiente_w_estrella_1` |
| 3 | `…::test_maximo_evaluado_20_es_descriptivo_de_la_funcion_retirada` | `horizonte_maximo_evaluado==20`, `horizonte_maximo_recomendado==13`, `horizonte_maximo_permitido_como_escenario==0`, `maximo_recomendado_es_limite_observado is False` | Campos internos de la función (el docstring la declara «función muerta») | Desaparece la función | Igual que la fila 1 |
| 4 | `…::test_20_puede_ser_maximo_recomendado_si_h20_es_tecnico` | `horizonte_maximo_recomendado==20`, `…_como_escenario==0`, `evidencia_horizonte_maximo_recomendado` (horizonte 20, `tecnica_cautela`) | Máximo recomendado en h=20 | Regla abandonada | `test_metodologia_n0_12_h24.py::test_efg…` (h=6/12/17/24: el mismo modelo y la misma trayectoria) |
| 5 | `…::test_20_puede_ser_maximo_escenario_si_h20_es_escenario_explicito` | `horizonte_maximo_recomendado==12`, `…_como_escenario==20`, `horizonte_maximo_admisible==20`, `evidencia_horizonte_maximo_escenario` (20, `escenario_alta_incertidumbre`) | Máximo de escenario | Bajo 12/24 no existe el «escenario» por horizonte | `test_metodologia_n0_12_h24.py::test_efg…`; `test_maximo_tarjeta_usa_alcance_operativo_vigente`, que exige que la tarjeta no diga «escenario» |
| 6 | `…::test_parada_en_20_por_evidencia_incluye_advertencia_y_no_extrapola` | `horizonte_maximo_evaluado==20`, `horizonte_maximo_recomendado==10`, `…_como_escenario==0`, `primer_horizonte_no_viable==0`, `tipo_parada==…`, texto de `advertencia_metodologica_horizontes` | Parada y advertencia | Igual que la fila 2 | Igual que la fila 2 |
| 7 | `test_presentacion_resultados.py::test_horizonte_dinamico_diferencia_tecnico_cautela_y_no_evaluado` | `horizonte_maximo_recomendado==12`, `…_como_escenario==18`, `horizonte_finalmente_permitido==18`, `accion=="permitir con cautela"`, `primer_horizonte_no_viable==0`; y, sin h18: `recomendado==12`, `como_escenario==0`, `admisible==12`, `18 in horizontes_no_evaluados`, `accion=="restringir"`, `finalmente_permitido==12` | Acciones «permitir con cautela» y «restringir» de la función muerta. Su docstring admite que esa combinación «ya no ocurre con datos reales» | No existe esa acción en la ruta vigente | `test_resultado_horizonte_solicitado.py::test_restriccion_no_hace_pasar_h12_como_resultado_de_h18`, `::test_h32_no_admisible_no_expone_proyeccion_y_marca_no_evaluados`, `::test_h45_se_rechaza_explicitamente_h12_se_genera_normalmente`; `test_metodologia_n0_12_h24.py::test_b…` |
| 8 | `test_presentacion_resultados.py::test_horizonte_no_salta_un_corte_no_viable` | `horizonte_maximo_recomendado==4`, `horizonte_maximo_admisible==4`, `primer_horizonte_no_viable==2`, `horizonte_finalmente_permitido==4`, `accion!="bloquear"`; y dos aserciones sobre la **entrada** sintética (`estados[2]` no permitido) | Hueco en h=2 sin veto sobre h=3 y h=4 | Bajo 12/24 no hay veto por horizonte. La aserción sobre la entrada no observa SAVIP | `test_fase2c_contratos_vigentes.py::test_la_ruta_vigente_no_referencia_el_subsistema_heredado`; `test_metodologia_n0_12_h24.py::test_efg…` |

**Lápidas.** Son comentarios no ejecutables, uno por archivo, situados donde estaba la primera prueba retirada. Nombran cada id en su propia línea, qué comprobaba, por qué se retira, el contrato vigente y este documento. Pytest **no** las recoge como pruebas: se comprobó con `--collect-only` (06). El texto anterior se recupera con:

```bash
git show 8e5a62b:tests/<archivo>
```

## 2. Los nueve ids vigentes de `tests/test_resultado_horizonte_solicitado.py`, conservados íntegros

**Único cambio:** se quita `determinar_horizonte_maximo_estadistico` del `import` de nivel de módulo (L10-15). Sin él, el archivo entero caería en un error de recolección al retirar la función (AS-028/06 §3.1).

**Ninguna aserción cambia.** El diff del archivo muestra solo la línea del import, las 6 funciones retiradas y la lápida. `_evaluacion` se conserva porque la usa el auxiliar vigente `_resultado`. La importación sin uso de `_lineas_determinacion_horizonte` **no se toca**: es AS-004.

| Id | Base | Final |
|---|---|---|
| `test_predeterminado_admisible_centra_h12_y_conserva_tabla_completa` | PASS | PASS |
| `test_manual_admisible_identifica_origen_y_h7` | PASS | PASS |
| `test_no_admisible_nunca_se_llama_proyeccion_tecnica` | PASS | PASS |
| `test_h32_no_admisible_no_expone_proyeccion_y_marca_no_evaluados` | PASS | PASS |
| `test_restriccion_no_hace_pasar_h12_como_resultado_de_h18` | PASS | PASS |
| `test_horizonte_manual_invalido` | PASS | PASS |
| `test_evaluacion_es_mensual_continua` | PASS | PASS |
| `test_h45_se_rechaza_explicitamente_h12_se_genera_normalmente` | PASS | PASS |
| `test_maximo_tarjeta_usa_alcance_operativo_vigente` | PASS | PASS |

## 3. Guarda de la Fase 1A, adaptada en el **mismo** commit que el retiro de producción

`tests/test_fase1a_selector_rectangular.py::test_la_ruta_productiva_usa_el_selector_rectangular_y_ningun_selector_retirado`:
- se pasa `"determinar_horizonte_maximo_estadistico"` de la tupla `retirados` (espiada con `patch.object(..., wraps=getattr(sp, n))`) a la tupla `eliminados` (`assert [n for n in eliminados if hasattr(sp, n)] == []`);
- **se conserva** el espía de `_evaluar_horizontes_proyeccion` (2D-3);
- herramienta: `evidencia/scripts/adaptar_fase1a.py`.

**Por qué en el mismo commit:**
- antes del retiro, la aserción de ausencia fallaría;
- después del retiro, si no se adaptara, el espía daría `AttributeError` (AS-028/06).

## 4. Histórica con dependencia parcial

`tests/test_cierre_metodologico.py::test_no_queda_cascada_de_prefijo_en_ninguno_de_los_dos_maximos` (perfil histórico):

| Aserción | Decisión | Motivo |
|---|---|---|
| `sp._mayor_horizonte_con(estado, "permitido_para_proyeccion_tecnica") == 4` | **Se retira** y se deja un comentario | El símbolo desaparece en este lote |
| `sp._mayor_horizonte_permitido(estado) == 4` | Se conserva | El auxiliar compartido sigue vivo hasta 2D-3 y protege el mismo contrato: no hay cascada de prefijo en el máximo que sí gobierna `max_admisible` |
| `estado[1]["permitido_para_proyeccion_tecnica"] is False`, `estado[1]["permitido_como_escenario"] is False` | Se conservan | Son aserciones sobre el estado de entrada; no dependen de 2D-1 |
| Comprobación AST: no hay `break` bajo `if … no_recomendable` en `_evaluar_horizontes_proyeccion` | Se conserva | Es de 2D-3 |

**Resultado:**
- se mantiene el id;
- el contrato restante sigue verificado y **no se vuelve engañoso**: el comentario explica que el otro máximo ya no existe;
- el estado se mide antes y después: PASS → PASS (06 §2).

## 5. Lo que no cambia

- `pruebas/prueba_horizonte_dinamico_ui_reportes.py`: **sin cambios**. Siguen 26 tests (19 PASS / 7 FAIL históricos) y se conserva `_evaluacion_horizonte`.
- `tests/test_fase2c_contratos_vigentes.py`: sin cambios. `HEREDADAS` es una lista de textos y su prueba AST pasa con los símbolos presentes o ausentes (AS-028/06).
- `tests/fixtures`, Golden Masters, tolerancias y los ids de las pruebas que permanecen: sin cambios.
- En `test_presentacion_resultados.py`, el auxiliar `_evaluacion_horizonte_ui` queda **sin uso** y se conserva por alcance estricto. Se registra en 08.

**Recuento esperado:** el perfil esencial pasa de 809 a **801**, por las 8 bajas de §1 y sin altas.
