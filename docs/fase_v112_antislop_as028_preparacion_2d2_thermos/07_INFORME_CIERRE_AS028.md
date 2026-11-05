# 07 · Informe de cierre AS-028 (preparación de 2D-2)

## 1. Veredicto: **APTO** para AS-028 en el alcance de 2D-2

**Para 2D-2, el script queda preparado:**
- `pruebas/prueba_horizonte_dinamico_ui_reportes.py` ya no depende de `seleccionar_modelo_por_rmse_oos_global` ni de `_errores_oos_por_par`;
- se importa y se recoge aunque el par se oculte;
- la propiedad vigente que protegía el test retirado sigue cubierta por esenciales concretos.

**Sigue sin tocarse:** producción, los resultados, los exportables, los 811 ids esenciales y la huella.

**AS-028 no queda cerrado para 2D-1.** Ver §9.

## 2. Rama, HEAD y CI

- **Rama:** https://github.com/estebanojeda0615/SAVIP/tree/maintenance/v1.1.2-as028-preparacion-2d2-thermos
- **Comparación:** https://github.com/estebanojeda0615/SAVIP/compare/56c75a6f0c47f01f5cdbca250986e6359b97de03...maintenance/v1.1.2-as028-preparacion-2d2-thermos

| Commit | Contenido |
|---|---|
| `4218340` | Filtro del CI y `.gitignore` |
| `0929b29` | Retiro del test del selector y de su llamada en `main()`, con lápida |
| `5acb09f5bed1fa2becd2e1edc4e112c4469b1a44` | Lápida corregida tras la 1.ª pasada de Thermos. **Último commit de código** |
| HEAD documental | Esta carpeta. SHA completo en el mensaje de entrega |

**CI del código:** [41948898532](https://github.com/estebanojeda0615/SAVIP/actions/runs/41948898532) sobre `5acb09f`, success, 811/811, 1.er intento del run. La intermitente GUI conocida `test_interaccion_fase_3c_a::test_a` falló en la 1.ª ejecución y pasó al reintento, sin relación con el diff (04 §4). El CI del HEAD documental figura en el mensaje de entrega.

**Reversión:** `git revert 5acb09f 0929b29 4218340`. La rama base no se ha modificado.

## 3. Los 30 tests

Inventario fila a fila en `01_INVENTARIO_30_TESTS_AS028.csv`. Las categorías se solapan, así que las cifras no suman 30.

| Categoría | N.º | Detalle |
|---|---|---|
| VIGENTE ÚNICO | **19** | Pasan y protegen comportamiento actual. Sus aserciones no se compararon una a una con los esenciales, así que no se declaran duplicados |
| VIGENTE DUPLICADO | **1** | Solo la parte vigente del test del selector, cubierta por Fase 1A |
| HISTÓRICO | **9** | Los 8 fallos heredados y el test del selector |
| DEPENDENCIA 2D-2 | **1** | El test del selector |
| DEPENDENCIA 2D-1 / AS-004 | **5** | 3 usan `determinar_horizonte_maximo_estadistico` y 2 las `_lineas_*` de AS-004 |
| AMBIGUO | **1** | Las aserciones CSV de `test_parametros_drift_receta_y_csv_reproducible`, que no se alcanzan porque el test cae antes por h=25 |

**Solapamientos:**
- el test del selector es a la vez HISTÓRICO, DEPENDENCIA 2D-2 y VIGENTE DUPLICADO en su parte vigente;
- `test_h18_no_se_redacta…` es HISTÓRICO y 2D-1/AS-004;
- drift y holt son HISTÓRICO y AS-004;
- «parámetros drift» es HISTÓRICO y AMBIGUO.

## 4. Cambios, archivo por archivo

| Archivo | Cambio |
|---|---|
| `pruebas/prueba_horizonte_dinamico_ui_reportes.py` | Retira `test_el_modelo_entregado_es_el_de_minimo_error_oos_global` y su llamada en `main()`. Deja una lápida de 3 líneas con el id, el commit de origen `56c75a6`, la cobertura vigente y la ruta de 03. La lápida no nombra el símbolo heredado |
| `.github/workflows/fase0-pruebas.yml` | +1 rama en el filtro de `push` |
| `.gitignore` | +1 excepción para esta carpeta |
| `docs/fase_v112_antislop_as028_preparacion_2d2_thermos/` | Documentos 00-07 y `evidencia/` |

**Sin tocar, a propósito:**
- los otros 29 tests, incluidos los 3 de 2D-1;
- los 8 fallos históricos: sin `skip`/`xfail` y sin cambiar expectativas;
- `pruebas/ejemplo_uso.py` y `pruebas/prueba_estadistica.py`;
- todo `tests/`, porque no se migra nada (03 §4), y `scripts/`;
- `app_icociv/**`, incluidos `criterios.py` (C-SEL-001) y `generador_reportes.py` (AS-004);
- `aplicacion.py`, `VERSION`, `packaging/`, `requirements*` y `tests/fixtures/`.

**Deuda registrada:**
- el script no corre en CI;
- `main()` es una lista manual que se detiene en el 2.º test;
- los 19 vigentes son candidatos a una migración mínima en una fase de saneamiento ajena a 2D-2;
- las listas del workflow y de `.gitignore` crecen una línea por fase.

## 5. Script histórico: 22/8 frente a la medición actual

| Medición | Tests | PASS | FAIL |
|---|---|---|---|
| Registro histórico (fase 2C, sobre `2f70391`) | 30 | 22 | 8 |
| **Base medida, `56c75a6`** | 30 | **22** | **8**, los mismos 8 |
| **Final, `5acb09f`** | 29 | **21** | **8**, los mismos 8 |
| Final con el par de 2D-2 oculto (G3) | 29 | 21 | 8, los mismos 8 |

**Destino del caso que llamaba al selector antiguo: retirado.** Comparaba el modelo entregado con el selector heredado, que trabaja sobre todos los pares y en coma flotante. Esa regla ya no es la productiva:
- coincidía por casualidad en su serie (`drift`);
- en 4 de las 5 series Fase 0 los dos selectores eligen modelos distintos (`evidencia/g3_divergencia_selector.txt`).

La regla vigente la cubren estos esenciales de `test_fase1a_selector_rectangular.py` (03 §3):
- el espía de la ruta productiva;
- las 7 propiedades;
- los 5 mutantes;
- AS-001.

## 6. Equivalencia

| Comprobación | Resultado |
|---|---|
| Ids esenciales | 811 → **811**, conjunto idéntico: 0 altas, 0 bajas y 0 cambios de estado |
| Golden | **29/29** |
| AS-001 | **16/16** |
| Huella | 20/20 con **0 diferencias**. SHA-256 `d6be699b…0191` idéntico |
| Recolección | 1 066 con los **mismos 3 errores**: `test_equivalencia_presupuestal_fase_4e_b`, `test_p0c_objeto_publico_sin_intervalo` y `test_p0c_regresion_negativa_c2`. No se declaran resueltos |
| `prueba_estadistica` | Salida idéntica |
| compileall e imports | OK |

Detalle en 04.

## 7. Thermos

- **Dos pasadas reales**, cada una con los dos agentes.
- **Corrección:** 1.ª sin hallazgos críticos, altos ni medios; 2.ª sin hallazgos de ninguna severidad.
- **Calidad:** 1.ª «APROBADO con observaciones», con dos medios nuevos (la referencia rota al 03 y el símbolo escrito en la lápida), los dos corregidos en `5acb09f`; 2.ª **«APROBADO»**.

Detalle en 05 y en `evidencia/thermos_pasadas.md`.

**Pendientes fuera de alcance:**
- P0-C / IC95: preexistente, la corrección está cancelada y no aparece en el diff;
- AS-004;
- AS-007 histórico;
- los 3 errores de recolección.

## 8. GO/NO-GO para pedir el prompt de retiro de 2D-2: **GO para SOLICITAR**

**No es una autorización implícita.** Ver 06.

**Bloqueos que el prompt de 2D-2 tendrá que tratar**, medidos con el par oculto:

| Bloqueo | Perfil | Efecto |
|---|---|---|
| `tests/test_remediacion_r2_h1_h2_h3_h7.py:35`: importación **sin uso** del selector | esencial, 9 ids | Error de recolección |
| `test_fase1a…::test_la_ruta_productiva_usa_el_selector_rectangular_y_ningun_selector_retirado` | esencial | Falla: hay que pasar el nombre de `retirados` a `eliminados` |
| `test_origen_inicial_backtesting.py::test_p0d_la_regla_de_seleccion_no_cambia` | esencial | Falla |
| `test_nmin_adversarial.py::test_muestra_comun_intacta_desde_el_primer_origen` | esencial | Falla |
| `test_nmin_adversarial.py::test_p0a_p0b_p0d_intactos` | esencial | Falla |
| `test_p0d_rmse_orden_exacto.py`, `test_rmse_global_estable.py`, `test_seleccion_rmse_global.py` | histórica | Error de recolección |
| `test_cierre_metodologico.py:414,437` y `test_horizonte_evidencia_reducida.py:375-393` | histórica | Fallos adicionales |
| Ficha **C-SEL-001** en `criterios.py:566-568` (**AS-024**) | producción (datos) | Apuntaría a un símbolo inexistente |

## 9. Estado residual de AS-028 para 2D-1

**No está cerrado.** El script sigue dependiendo de `determinar_horizonte_maximo_estadistico` en 3 tests:
- `test_horizonte_maximo_no_es_18_si_h18_no_cumple`;
- `test_mensaje_no_recomendables_no_imprime_lista_vacia`;
- `test_h18_no_se_redacta_como_intervalos_aceptables`.

Depende además de las `_lineas_*` de AS-004 en 2 tests más (drift y holt). Todos se conservaron intactos, como exigía el prompt. Antes de abrir 2D-1 hace falta una fase AS-028 específica para esas dependencias.

## 10. Ramas y versión

No se modificaron:
- `main` (`dfdb3e0`) ni `develop/v1.1.2` (`6672529`);
- el tag ni el release `v1.1.2-rc.1` (`08f364b`);
- las ramas de fases anteriores, incluida la base `maintenance/v1.1.2-fase2d-lote5-thermos` (`56c75a6`);
- el ejecutable publicado.

No hubo merge, PR, tag, release, EXE, ZIP ni versión nueva.

**No se inició 2D-2, 2D-1, 2D-3, 2D-6, AS-004 ni P0-C-R.**
