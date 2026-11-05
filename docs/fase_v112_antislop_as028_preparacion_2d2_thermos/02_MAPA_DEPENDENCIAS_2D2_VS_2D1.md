# 02 · Mapa de dependencias: 2D-2 frente a 2D-1

## 1. Las cuatro dependencias del script

| Dependencia | Lote | Definición | Alcanzable desde producción | Tests del script que la usan |
|---|---|---|---|---|
| `seleccionar_modelo_por_rmse_oos_global` | **2D-2** | `servicio_proyeccion.py:3142` | **No** | 1: `test_el_modelo_entregado_es_el_de_minimo_error_oos_global` (**retirado en esta fase**) |
| `_errores_oos_por_par` | **2D-2** | `servicio_proyeccion.py:3112`. Solo la llama el selector heredado (`:3190`) | **No** | Ninguno de forma directa |
| `determinar_horizonte_maximo_estadistico` | 2D-1 | `servicio_proyeccion.py` | **No** | 3: `test_horizonte_maximo_no_es_18_si_h18_no_cumple`, `test_mensaje_no_recomendables_no_imprime_lista_vacia` y `test_h18_no_se_redacta_como_intervalos_aceptables`. **Intactos** |
| `_lineas_horizontes`, `_lineas_determinacion_horizonte` y `_lineas_factibilidad` | AS-004 | `generador_reportes.py` | **No** | `test_h18_no_se_redacta…`, `test_horizonte_dinamico_con_serie_drift` y `test_horizonte_dinamico_con_serie_holt`. **Intactos** |

La alcanzabilidad sale del grafo AST de llamadas de `56c75a6`, generado con `docs/fase_v112_antislop_02a_as003/evidencia/grafo_as003.py`. La ruta productiva vigente es:

```
ejecutar_proyeccion → _ejecutar_proyeccion_base → _matriz_rectangular_12_24 → _seleccionar_modelo_rectangular
```

## 2. Consumidores del par 2D-2 en todo el repositorio (tras AS-028)

Búsqueda textual de los dos nombres en `*.py`, `*.yml`, `*.spec` y `*.txt`, excluyendo `docs/`. En el script no hay `getattr` ni `importlib`.

| Archivo | Línea | Uso | Perfil | Efecto si 2D-2 retira el par |
|---|---|---|---|---|
| `pruebas/prueba_horizonte_dinamico_ui_reportes.py` | 279-282 | **Solo comentario** (la lápida) | script, fuera del CI | Ninguno. Comprobado en G3 con el par oculto |
| `app_icociv/estadistica/criterios.py` | 568 | Cadena en la ficha C-SEL-001 | producción (datos) | No rompe la importación, pero la ficha apuntaría a un símbolo inexistente (AS-024) |
| `tests/test_remediacion_r2_h1_h2_h3_h7.py` | 35 | **Importación a nivel de módulo**, sin ningún uso en el archivo | **esencial** | **Error de recolección de un archivo esencial** |
| `tests/test_origen_inicial_backtesting.py` | 250 | `SP.seleccionar_modelo_por_rmse_oos_global` | esencial | El id que lo usa falla |
| `tests/test_nmin_adversarial.py` | 136 | `SP._errores_oos_por_par` | esencial | El id que lo usa falla |
| `tests/test_fase1a_selector_rectangular.py` | 305 | Tupla `retirados` que se espía con `patch.object` | esencial | `patch.object` de un atributo inexistente: el id falla. Hay que pasar el nombre a la tupla `eliminados` (presencia → ausencia) |
| `tests/test_fase2c_contratos_vigentes.py` | 30 | Tupla `HEREDADAS` | esencial | Ninguno. La tupla es una lista de exclusión: `:173-174` exige que la ruta vigente no llame a ninguno de esos nombres, pero no que existan. En 2D-5, `tramo_evidencia_oos` siguió en ella sin romper nada |
| `tests/test_cierre_metodologico.py` | 414, 437 | `inspect.getsource` y llamada | histórica | Fallo histórico adicional |
| `tests/test_horizonte_evidencia_reducida.py` | 375-393 | Importación y llamadas | histórica | Fallo histórico adicional |
| `tests/test_p0d_rmse_orden_exacto.py` | 47-238 | Importación y llamadas | histórica | Error de recolección o fallos adicionales |
| `tests/test_rmse_global_estable.py` | 41-136 | Importación y llamadas | histórica | Error de recolección o fallos adicionales |
| `tests/test_seleccion_rmse_global.py` | 46-236 | Importación y llamadas | histórica | Error de recolección o fallos adicionales |

`docs/` contiene 26 archivos que mencionan el par: son registros de fases anteriores y no son ejecutables.

La simulación dinámica de G3 (`evidencia/g3_*`) cuantifica estos efectos ocultando el par en memoria. Producción no se edita.

## 3. 2D-2 frente a 2D-1 en este script

- **2D-2:** tras AS-028, el script **ya no depende** del par. La única referencia ejecutable desapareció y lo que queda es un comentario.
- **2D-1:** el script **sigue dependiendo** de `determinar_horizonte_maximo_estadistico` en 3 tests, y de las funciones `_lineas_*` de AS-004 en otros 2. El prompt exige conservarlos intactos. AS-028 **no está cerrado para 2D-1**.

## 4. Lo que AS-028 no resuelve para 2D-2

Preparar el script no equivale a autorizar 2D-2. Para retirar el par sin nuevos `ImportError`, el prompt de 2D-2 tendrá que tratar, al menos:

1. **`tests/test_remediacion_r2_h1_h2_h3_h7.py:35`**: quitar la importación sin uso. Es esencial y, si no se hace, su recolección falla.
2. **`test_origen_inicial_backtesting.py:250` y `test_nmin_adversarial.py:136`**: retirar o migrar los ids según el plan 2C (retirar `test_p0d_…` y `test_muestra_comun_…`, migrar `test_p0a_p0b_p0d_intactos`).
3. **`test_fase1a…:305`**: mover el nombre de `retirados` (espiado) a `eliminados` (exigido ausente).
4. **Los 5 archivos históricos** que lo usan.
5. **La ficha C-SEL-001** en `criterios.py:568` (AS-024).
