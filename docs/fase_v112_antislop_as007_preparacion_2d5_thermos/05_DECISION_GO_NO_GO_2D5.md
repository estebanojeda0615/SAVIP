# 05 · Decisión GO / NO-GO del futuro lote 2D-5

**Lo que significa esta decisión.** Un GO solo **recomienda pedir autorización** para el lote 2D-5 en un prompt y una fase independientes. **No lo ejecuta.** En esta fase no se retiró `tramo_evidencia_oos`, ni sus constantes, ni PS-03.

## 1. Matriz por condición

| # | Condición | Evidencia | Estado |
|---|---|---|---|
| 1 | r3 no queda con importaciones rotas cuando se retira `tramo_evidencia_oos` | r3 ya no importa la función ni `TRAMO_OOS_*`. Con el retiro simulado en memoria, r3 se importa y da 21/27, igual que la base (02 §1; [evidencia](evidencia/simulacion_retiro_2d5.txt)) | **CUMPLE** |
| 2 | No aparece ningún error de recolección nuevo | Con el retiro simulado, la base sube a 4 errores y la rama final se queda en 3, los históricos. Sin simulación: 1 058 → 1 067 recolectados, con los mismos 3 errores (03 §3) | **CUMPLE** |
| 3 | PS-03 tiene cobertura equivalente identificada | `test_ps03_la_escasez_…` se cubre con `test_fase2c_contratos_vigentes::test_texto_evidencia_oos_tres_tramos_sin_vocabulario_de_validacion` (W=0/1/2/3/50 y vocabulario sobre el texto publicado) y `::test_escasez_de_ventanas_…[36\|37\|41]` (punto con advertencia). Las dos están en el perfil esencial y pasan (02 §4) | **CUMPLE**. Matiz: no hay un caso literal W=10; se puede añadir en el mismo lote |
| 4 | Constantes `TRAMO_OOS_*` evaluadas | No tienen consumidores productivos. Solo las usan la función, PS-03 y un docstring. Recomendación: retirarlas con la función, con autorización expresa, y trasladar el comentario HGRID al docstring de `_texto_evidencia_oos` (02 §4) | **CUMPLE**. Requiere una decisión del propietario |
| 5 | Golden y huella intactos | 29/29 golden. SHA-256 de la huella `d6be699b…` idéntico, con 0 diferencias. `git diff` de producción y fixtures vacío (03 §1 y §4) | **CUMPLE** |
| 6 | Los 803 ids esenciales se conservan | En el JUnit de la primera ejecución están los 803 originales y todos pasan; se suman 9 nuevos y ninguno cambia de estado (03 §2) | **CUMPLE** |
| 7 | Thermos sin hallazgos altos sin resolver que afecten al cambio | A: ninguno alto. B: los dos ALTOS del cambio quedaron resueltos (falso verde de C1 y extractor del PDF), y la segunda pasada no dejó hallazgos críticos, altos ni medios sin tratar (04 §3). La tercera pasada (delta `c656e19..da04725`): corrección sin hallazgos críticos, altos ni medios; calidad «Aprobado» (04 §3.3) | **CUMPLE** para el cambio |
| 8 | AS-007 parcial explicado | r3 queda resuelto para 2D-5. Siguen abiertos `test_p0c_*` ×2, `bghc` y PS-02/anexo DANE, que bloquean 2D-3, no 2D-5 (02 §6) | **CUMPLE**, con alcance parcial declarado |
| 9 | CI ejecutado en la rama nueva | Todos los commits hasta `73490c5`: success en el primer intento, sin fallos en la primera ejecución (06 §4). El CI del HEAD final figura en el mensaje de entrega | **CUMPLE** |

## 2. Dictamen

**GO para PEDIR autorización del lote 2D-5.** Para un prompt independiente, se recomienda este alcance:

1. Retirar `tramo_evidencia_oos` de `servicio_proyeccion.py` (11 líneas).
2. Retirar `TRAMO_OOS_*` (3 líneas), si se autoriza expresamente. Trasladar el comentario HGRID de las líneas ~2030-2041 al docstring de `_texto_evidencia_oos` y quitar «Ver `TRAMO_OOS_SIN_EVIDENCIA`».
3. Retirar el id esencial `tests/test_cierre_semantico_ps01_ps05.py::test_ps03_la_escasez_de_evidencia_no_equivale_a_su_inexistencia` **en el mismo commit**, con autorización expresa para retirar ese id. Ids esperados: 812 → 811.
4. Opcional: añadir W=10 a `test_texto_evidencia_oos_tres_tramos_…`.
5. Opcional, si se autoriza el tratamiento final de r3: retirar de r3 los controles C1–C7 y los auxiliares que solo usan ellos (`_ic95_desde`, `_multiplicador_intervalo` y `NIVEL_NOMINAL_95` en r3), que ya están migrados a pytest. También se puede convertir r3 en un archivo documental. El prompt de esta fase prohibía hacerlo.
6. Criterios de aceptación: los de siempre, es decir, huella idéntica, 29 golden, perfil esencial completo, recolección sin errores nuevos, CI verde y Thermos sobre el diff del lote.

**Reversión:** `git revert` del commit del lote.

## 3. Decisiones del propietario, separadas de cualquier autorización de retiro

1. **Residual P0-C de producción (Thermos B-A1, ALTO, previo a esta fase).** `ejecutar_proyeccion` publica `backtesting_comparativo.<modelo_h>.metricas.errores_extremos.observaciones[*].error_absoluto`, y con eso se reconstruye bit a bit el IC95 retirado. No llega a la sesión JSON, al CSV, a los informes ni a la interfaz (allí solo aparecen conteos). Corregirlo exige cambiar producción, por ejemplo:
   - limpiar `observaciones` en `_retirar_errores_oos_de_publicacion`, publicando solo `cantidad`, `n`, `proporcion` y `umbral_z`;
   - o no publicar `backtesting_comparativo`.

   Hace falta una fase autorizada, con una prueba que hoy falle y después pase. **No bloquea 2D-5**, porque no tiene relación con `tramo_evidencia_oos`, pero **sí afecta al cierre de P0-C**.
2. **C12 · `Periodo` en la tabla de ventanas** (02 §5).
3. **HG4/HG5 · claves de traza que se leen pero que nadie produce**, en `generador_reportes.py:378-388` (02 §5, tipo AS-004).
4. **Restos de 2D-4 detectados por Thermos A** (04 §2): `MIN_ITERACIONES_SELECCION` y su import, `MODELOS_SERIE_TEMPORAL`, y las claves `descartes_modelos`/`ranking_backtesting`. Se proponen para 2D-6 o para el lote que corresponda.
5. **Política de CI:** usar patrones en el filtro del workflow y en `.gitignore`, en lugar de añadir una línea por fase.
