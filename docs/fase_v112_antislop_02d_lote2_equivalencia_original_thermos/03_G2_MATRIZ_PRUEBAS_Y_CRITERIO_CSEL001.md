# 03 · G2: matriz de pruebas afectadas y criterio C-SEL-001

**Estado base:** el de `5478958`. «PASS (base)» significa que la prueba pasaba antes del cambio. «FAIL preexistente» significa que ya fallaba en la base y no se toca.

## 1. Esenciales

| Id | Estado base | Qué verificaba | ¿Selector vigente? | Sustituto esencial exacto | Destino |
|---|---|---|---|---|---|
| `test_origen_inicial_backtesting::test_p0d_la_regla_de_seleccion_no_cambia` | PASS | Cuatro propiedades P0-D **sobre el selector heredado**: muestra común, una ULP, orden de inserción y desempate | No | `test_fase1a_selector_rectangular::test_selector_vigente_cumple[p_solo_pares_comunes]`, `[p_sse_exacto_decide_una_ulp]`, `[p_invariante_al_orden_de_entrada]` y `[p_empate_primer_candidato_del_banco]`, con los mutantes `todos_los_pares`, `suma_flotante` y `ultimo_en_empate`. AS-001 (16 ids) y `test_metodologia_n0_12_h24` (N0=12, H=24, W*) | **Retirado** (autorizado), junto con sus auxiliares `_P0D_ULP_A/B`, `_p0d_banco` y `_p0d_lista`, usados solo por él. Queda una lápida |
| `test_nmin_adversarial::test_muestra_comun_intacta_desde_el_primer_origen` | PASS | Con `_errores_oos_por_par`, que la muestra común del backtesting comparativo coincide con la unión | No: extractor heredado | `test_fase1a…::test_la_ruta_productiva_usa_el_selector_rectangular_y_ningun_selector_retirado` (pares comunes = pares esperados = W*×24, 21 candidatos, sobre la matriz real de la ruta productiva) y `test_metodologia_n0_12_h24::test_c_rectangulo_n65_da_w_estrella_30_y_mismos_origenes_por_h` (orígenes del rectángulo). Ambos son conductuales | **Retirado** (autorizado). Queda una lápida |
| `test_nmin_adversarial::test_p0a_p0b_p0d_intactos` | PASS | P0-A y P0-B por inspección, y P0-D llamando al test anterior | P0-A y P0-B sí; P0-D no | — | **Id conservado.** P0-D pasa a `p0d_en_el_selector_vigente()`, que aplica `p_sse_exacto_decide_una_ulp`, `p_invariante_al_orden_de_entrada` y `p_empate_primer_candidato_del_banco` de Fase 1A sobre su `SELECTOR`. Mutación: se detectan `suma_flotante` y `ultimo_en_empate` (`evidencia/sensibilidad_p0d_vigente.txt`). Las demás expectativas no cambian |
| `test_fase1a…::test_la_ruta_productiva_usa_el_selector_rectangular_y_ningun_selector_retirado` | PASS | Espiaba el selector heredado, todavía definido | — | — | **Id conservado.** El par pasa a `eliminados`, donde se exige su ausencia. Se siguen espiando los dos evaluadores heredados que continúan definidos, y se mantiene sin cambios la verificación estricta de `_seleccionar_modelo_rectangular` |
| `test_remediacion_r2_h1_h2_h3_h7.py` (9 ids) | PASS | — | — | — | Se quita **solo** la importación sin uso (L35). Los 9 ids se conservan |
| `test_fase2c_contratos_vigentes.py` (`HEREDADAS`) | PASS | Barrera anti-regresión | — | — | **Sin cambio** |

**Cuenta:** 811 → **809**. Las 2 bajas son las autorizadas y no hay altas. Ningún otro id esencial desaparece (06).

## 2. Históricas

| Archivo | Casos | Estado base | Destino | Sustituto vigente |
|---|---|---|---|---|
| `test_p0d_rmse_orden_exacto.py` | D1, D2, D3, D5, D6, D7, D8, D9 y D10 | PASS | **Retirados**. Ejercitaban el selector heredado | D1: `p_sse_exacto_decide_una_ulp`; D2: `p_invariante_al_orden_de_entrada`; D3: `p_empate_primer_candidato_del_banco`; D5: `p_minimo_sse`; D6: `test_as001_candidato_divergente_no_aborta_la_seleccion`; D7 y D8: `test_un_error_no_finito_excluye_solo_a_ese_candidato`; D9: `test_sin_muestra_comun_o_banco_vacio_devuelve_none`; D10: `p_solo_pares_comunes` |
| | D11 y D12 | PASS | **Conservados**, redirigidos a `_seleccionar_modelo_rectangular` | — (siguen pasando) |
| | D4 y D13 | PASS | **Conservados sin cambio**. Prueban `_sse_exacto`, que sigue vigente | — |
| `test_rmse_global_estable.py` | T7, T7b, T8 y T9: los 4 casos del archivo | PASS | **Archivo borrado**. Los 4 casos ejercitaban el selector heredado y la cabecera y `_banco` solo existían para ellos. El contenido íntegro sigue en Git (`5478958`) | T7: `test_as001_candidato_divergente_no_aborta_la_seleccion`; T7b: `test_as001_una_ulp_en_el_borde_de_dbl_max` y `test_as001_dos_candidatos_enormes_ordenados_por_sse_exacto_y_rmse_preciso`; T8: `p_solo_pares_comunes`; T9: `p_empate_primer_candidato_del_banco` |
| `test_seleccion_rmse_global.py` | 13 casos que llamaban al selector heredado | PASS | **Retirados** | `p_minimo_sse`; `p_rmse_coherente`; `test_rmse_reportado_coincide_con_sse_exacto`; `p_pesos_uniformes_por_horizonte`; `p_solo_pares_comunes`; `test_sin_muestra_comun_o_banco_vacio_devuelve_none`; `test_un_error_no_finito_excluye_solo_a_ese_candidato`; `p_invariante_al_orden_de_entrada`; `p_empate_primer_candidato_del_banco`; `test_es_reproducible_y_no_muta_la_matriz`; `test_as001_ruta_productiva_con_21_candidatos_y_uno_divergente` (un solo modelo para toda la trayectoria) |
| | `test_la_regla_no_consulta_umbrales_ni_identidad` | PASS | **Conservado**, redirigido al selector vigente | — |
| | `test_la_regla_retirada_ya_no_se_invoca_en_la_ruta_productiva` | PASS | **Conservado sin cambio** | — |
| `test_cierre_metodologico.py` | `test_la_seleccion_elige_el_de_menor_error_oos` | PASS | **Retirado** | `p_minimo_sse` |
| | `test_la_seleccion_no_consulta_ningun_umbral` | PASS | **Conservado**, redirigido al selector vigente (commit preparatorio) | — |
| `test_horizonte_evidencia_reducida.py` | `test_modelo_agregado_minimiza_el_error_oos_global` | PASS (por coincidencia, igual que el test del script retirado en AS-028) | **Retirado**. Comparaba con otra regla. El bloque `__main__` se conserva sin esa llamada | `test_fase1a…::test_la_ruta_productiva_usa_el_selector_rectangular_y_ningun_selector_retirado` |
| `test_integracion_fhg.py` | `test_p0abd_intactos` | PASS | **Conservado**. Llama a `p0d_en_el_selector_vigente()` | — |

**Fallos históricos preexistentes en los archivos tocados.** Fallan igual en la fuente de 5478958 y no se tocan:
- `test_cierre_metodologico::test_no_hay_modelo_por_horizonte`;
- `test_integracion_fhg::test_h3_el_tope_60_solo_restringe_la_entrada` y `::test_h4_el_maximo_publicado_declara_que_admite_huecos`;
- `test_horizonte_evidencia_reducida::test_serie_corta_publica_su_cobertura_y_niega_solo_por_ventanas`, `::test_la_rejilla_de_horizontes_no_tiene_tope_historico_ni_cascada` y `::test_serie_erratica_se_entrega_con_su_incertidumbre_a_la_vista`.

**Cuenta histórica:** 242 → **214**, una baja de 28 casos (9 + 4 + 13 + 1 + 1). No hay altas y se mantienen los mismos 3 errores de recolección.

## 3. Criterio C-SEL-001 (AS-024)

| Pregunta | Respuesta verificada |
|---|---|
| ¿Dónde está el campo? | `app_icociv/estadistica/criterios.py:568`, en el campo `ubicacion` de `CriterioEstadistico("C-SEL-001", …)` |
| ¿Se publica? | **No.** `CRITERIOS_ESTADISTICOS` solo lo leen `matriz_criterios()`, `validar_tipos_criterios()` y `exportar_matriz_criterios_markdown()` / `generar_markdown_criterios()`. Ninguna se llama desde la aplicación, la UI, los reportes, las sesiones ni los exportables (búsqueda en `app_icociv/`, `aplicacion.py` y `scripts/`). Solo lo leen pruebas, y ninguna lee `ubicacion` |
| ¿Es decisorio? | No. Es un texto descriptivo; el código no lo interpreta |
| Cambio | `…::seleccionar_modelo_por_rmse_oos_global` → `…::_seleccionar_modelo_rectangular`. Es la función que aplica la regla que describe la ficha («argmin RMSE_global sobre la muestra común de pares»): con la misma muestra común y el mismo n, argmin RMSE = argmin SSE exacto. **No se tocaron** criterio, tipo, valor, fuente, justificación ni acción |
| Efecto sobre resultados | Ninguno, comprobado por el oráculo exacto (05) y por la huella |
| Deuda preexistente (AS-024) | Algunas fichas usan rutas sin `::` o con tildes, por ejemplo `app_icociv/estadística/...` a partir de la L269. No se tocan |
