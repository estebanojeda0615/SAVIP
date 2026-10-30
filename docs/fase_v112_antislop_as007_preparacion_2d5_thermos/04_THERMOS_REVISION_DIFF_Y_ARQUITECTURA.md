# 04 · Revisión Thermos del diff y contexto de arquitectura

## 1. Thermos real: versión, activación e invocación

| Dato | Valor |
|---|---|
| Plugin | `thermos@thermos-claude-plugin` **1.1.0**, alcance usuario, habilitado ([evidencia](evidencia/thermos_plugin_list.txt)) |
| Claude Code | 2.1.238. `--effort` no está disponible: exige 2.1.292 o posterior |
| Primer intento | `claude -p "/thermos 83549e7...6ac158d"` falló con `Not logged in · Please run /login` (código 1, 5 s; [evidencia](evidencia/thermos_bloqueo_cli.txt)). No se inició sesión |
| Activación | Durante la sesión, Claude Code cargó el plugin instalado. Aparecieron la skill `thermos:thermos` y los agentes `thermos:thermo-nuclear-reviewer` y `thermos:thermo-nuclear-code-quality-reviewer` |
| Invocación | Skill `thermos:thermos` con argumentos `83549e7...6ac158d`. Siguiendo su flujo, se preparó el diff de código de cada alcance (sin `docs/`) en `C:/Pruebas SAVIP/AS007/thermos/diff_*.patch` y se lanzaron **los dos agentes del plugin en segundo plano y en paralelo para cada alcance**. Se esperó a que terminaran todos y se sintetizaron los resultados |
| Pasadas | **A**: `83549e7...6ac158d`, 2 agentes. **B1**: `6ac158d...febd981`, 2 agentes. **B2**: `6ac158d...c656e19`, 2 agentes, repetida porque el diff cambió. **B3**: delta `c656e19..da04725` dentro de `6ac158d...da04725`, 2 agentes. B2 se lanzó por primera vez y la detuve antes de que terminara para no sobrecargar el equipo mientras corría el perfil esencial; después la relancé completa |
| Modo | Solo lectura. Los agentes no modificaron archivos ni hicieron escrituras git. Cuando necesitaron ejecutar algo usaron `git archive` en carpetas temporales |

Las salidas de cada revisor, condensadas sin alterar los hallazgos, están en [`evidencia/revision_A_correccion_thermos.md`](evidencia/revision_A_correccion_thermos.md), [`revision_A_calidad_thermos.md`](evidencia/revision_A_calidad_thermos.md), [`revision_B_correccion_thermos.md`](evidencia/revision_B_correccion_thermos.md), [`revision_B_calidad_thermos.md`](evidencia/revision_B_calidad_thermos.md) , [`revision_B2_thermos.md`](evidencia/revision_B2_thermos.md) y [`revision_B3_thermos.md`](evidencia/revision_B3_thermos.md).

**Thermos revisa diffs.** No revisó toda la arquitectura de SAVIP. Sus sugerencias de refactorización no autorizan a cambiar producción.

## 2. Revisión A: lote 2D-4 (`83549e7...6ac158d`), solo como referencia

**Veredicto de los dos revisores:** ningún hallazgo crítico ni alto. El lote es una simplificación real (−354 líneas) y no toca la ruta productiva.

| Sev. | Hallazgo | Archivo:línea | Clasificación | Estado |
|---|---|---|---|---|
| Medio (calidad) / Bajo (corrección) | `MIN_ITERACIONES_SELECCION` sin lectores. El import `MIN_ITERACIONES_WF` solo sirve para definirla (lo he comprobado con `git grep`: las dos únicas apariciones son la línea 13 y la 43). El revisor de corrección afirmaba que `MIN_ITERACIONES_WF` «sigue en uso», y **eso es falso** | `modelos_interpretables.py:13,43` | Nuevo resto huérfano de 2D-4 | **Deferido**: es producción. Propuesta para 2D-6 o el próximo lote |
| Medio | `MODELOS_SERIE_TEMPORAL` sin uso productivo. Solo lo leen `test_auditoria_formulas_estadisticas.py:195,203` y `pruebas/prueba_horizonte_dinamico_ui_reportes.py:729,740` | `modelos_interpretables.py:36-41` | Nuevo resto | **Deferido** a un lote con su propia validación (toca `pruebas/`, AS-028) |
| Medio | Las claves `descartes_modelos` y `ranking_backtesting` ya no tienen productor, pero se siguen leyendo con valor por defecto. Puede ser compatibilidad con sesiones antiguas (hipótesis) | `servicio_proyeccion.py:1542,1545,1639,2276,3933-3939,4024,4124`; `contenido.py:819`; `generador_reportes.py:1012-1015` | Riesgo previo | **Deferido**: decisión del tipo AS-004 |
| Bajo | Comentario que cita una función que ya no existe | `servicio_proyeccion.py:2591-2599` | Ya registrado en 05 de 2D-4 | Deferido a 2D-3/2D-6 |
| Bajo | El comentario de trazabilidad cita `2f70391` L280-L444, que solo cubre el selector. Los auxiliares están en L447-L597 y L1352-L1381. La misma truncación aparece en el ancla de R1 de 2C | `test_fundamentacion_metodologica.py:264-269` | Nuevo defecto documental | Deferido: no se cambia 2D-4 en esta fase |
| Bajo | Guardias textuales «sin llamada a seleccionar_modelo_por_evidencia(» repetidas en 4 archivos. Ahora solo impiden reintroducir el nombre | varias | Riesgo previo | Deferido a 2D-3 |
| Bajo | La lista `HEREDADAS` sigue incluyendo los 6 nombres retirados en 2D-4. No afecta a la ejecución | `test_fase2c_contratos_vigentes.py:23-37` | Nuevo resto | Deferido |
| Bajo | `.gitignore` y workflow crecen una línea por fase | — | Riesgo previo | Recomendación: patrones. Decide el propietario |
| Contexto | `modelos_interpretables.py` tiene 1 027 líneas | — | Riesgo previo | Fuera de alcance |
| Info | `test_cierre_metodologico::test_no_hay_modelo_por_horizonte` falla en `6ac158d` (comprobación textual de una línea que ya no existe). No es esencial y no cambia en 2D-4 | `tests/test_cierre_metodologico.py:510` | Riesgo previo, no atribuible a 2D-4 | Registrado |

**Falsos positivos descartados por los propios revisores:** imports retirados que romperían consumidores, el manifiesto de ids y los homónimos `_numero`.

**Recomendación de proceso (calidad A):** en la comprobación G1 de los próximos lotes, buscar también por nombre las **constantes de módulo y las claves de diccionario** que escribían las funciones retiradas, no solo el grafo de `def`.

## 3. Revisión B: esta fase (`6ac158d...HEAD`)

### 3.1 Primera pasada (`febd981`)

| Sev. | Hallazgo | Archivo:línea | Tipo | Estado final |
|---|---|---|---|---|
| **ALTO** (corrección, A1) | **Falso verde en C1.** El IC95 retirado se reconstruye bit a bit desde `backtesting_comparativo.<modelo_h>.metricas.errores_extremos.observaciones[*].error_absoluto`: (117.69742214273187, 125.47330550648688) = `ci95_lo/hi` interno, en 504 entradas modelo×horizonte. La prueba solo miraba DataFrames | `test_as007_…:100-148` (en `febd981`) | Demostrado; **lo verifiqué yo por separado** ([evidencia](evidencia/verificacion_independiente_A1.txt)) | **Falso verde resuelto**: C1 pasa a llamarse `test_p0c_tablas_de_ventanas_sin_errores_ni_limites_ci` y su docstring y el del módulo declaran el residual. **Fuga de producción deferida**: está fuera de alcance porque `app_icociv/**` está prohibido. Escalada al propietario (05 §3) |
| **ALTO** (calidad 1) | C7 extraía solo parte del texto del informe: le faltaban `Formula`, pies, `Ficha.destacados`, portada y pie | `test_as007_…:124-139` | Demostrado | **Resuelto**: extractor local completo (`da04725`); las mutaciones `formula_general` y `portada_pie` se detectan |
| Medio | Código muerto copiado (`_hojas`, `CLAVES_DECLARACION`) | `:55-75`, `:31-33` | Demostrado | **Resuelto** |
| Medio | C1–C7 duplicados en r3 sin fecha de cierre; las copias ya divergen | r3 `:97-195` | Demostrado | **Deferido con disparador**: el prompt prohíbe retirar comprobaciones de r3 en esta fase. Inventario 01: «la copia de r3 se retira cuando se autorice el tratamiento final de r3 (propuesto con 2D-5)» |
| Bajo-Medio | `_tramo()` aceptaba cualquier texto como DISPONIBLE | r3 `:513-521` | Demostrado | **Resuelto**: aserción de prefijo. Una mutación de redacción da «Texto de tramo no reconocido» |
| Bajo | Nombre `_p0c_` con contenido P0-E | — | Demostrado | **Resuelto**: `test_as007_contratos_r3_vigentes.py` |
| Bajo | Encabezados del DOCX comparados por igualdad; no detectaban `Error_abs` | `:221` | Hipótesis | **Resuelto en parte**: se prohíben también los nombres internos (mutación `encabezado_error_abs`). La comparación por subcadena no se aplica porque daría falsos positivos con «Índice observado» |
| Bajo | `lru_cache` comparte un dict mutable | `:46-52` | Hipótesis | **Resuelto**: documentado. Ninguna prueba lo muta (verificado por el revisor) |
| Bajo | La aserción de `model_name` podía ser vacía | `:205` | Hipótesis | **Resuelto** |
| Bajo | El filtro del workflow crece por fase | workflow `:9-16` | Demostrado | Recomendación (patrón `maintenance/v1.1.2-**`). Decide el propietario |

### 3.2 Segunda pasada (`c656e19`)

- **Corrección:** ningún hallazgo crítico, alto ni medio. Da A1 por resuelto en lo que toca al cambio.
- **Calidad:** «aprobable con una condición». **N1 (medio)**: C7 importaba `tests.test_informes_rediseno`, que es histórico y lanza una proyección n=72 al importarse (+11 s, dependencia frágil). Más los bajos N2–N4 y BAJO-1 a BAJO-6.
- **Todos tratados en `da04725` y en las docs** (tabla en [`evidencia/revision_B2_thermos.md`](evidencia/revision_B2_thermos.md)):
  - N1, N2, N3, N4, BAJO-1, BAJO-3, BAJO-4 y BAJO-6: resueltos;
  - BAJO-5: no aplicado, con motivo;
  - `xfail(strict=True)` como alarma para A1: no aplicado, porque el prompt lo prohíbe.

### 3.3 Tercera pasada (delta `c656e19..da04725`)

- **Corrección:** ningún hallazgo crítico, alto ni medio y **ningún defecto nuevo**. Confirma que `replace` sobre la configuración es correcto, que el anexo se genera de verdad y que el extractor es una copia fiel ampliada. Hallazgo BAJO-1: el docstring decía «todo el texto que dibuja». Resuelto en `1f6fa6a`.
- **Calidad: «Aprobado».** El delta cumple la condición de B2. Hallazgos:
  - BAJO 1, encabezados no normalizados como el anexo (`c.replace("_", " ")`): resuelto en `1f6fa6a` y comprobado con la mutación `anexo_escalado`;
  - BAJO 2, extractor duplicado: deuda declarada y diferida;
  - NIT 3, el anexo podía no traer la tabla por ventana: resuelto con una aserción en C6;
  - NIT 4: cosmético, sin cambio.
- Detalle en [`evidencia/revision_B3_thermos.md`](evidencia/revision_B3_thermos.md).

**Estado final.** Ningún hallazgo crítico, alto ni medio **del cambio** queda sin resolver. El único ALTO pendiente es el **residual P0-C de producción**, que este diff no introdujo y que no puede corregir. `1f6fa6a` (14 líneas, aplicando los remedios propuestos) no tuvo una cuarta pasada; lo verifiqué con 9/9 PASS y 14/14 mutaciones.

## 4. Contexto de arquitectura (revisión manual, NO es Thermos)

Fronteras que afectan a este cambio. Es lectura del código base para interpretar el diff, no una auditoría integral:

- **`servicio_proyeccion.py`:**
  - `tramo_evidencia_oos` y `TRAMO_OOS_*` (~2030-2057) ya no tienen consumidores productivos.
  - `_texto_evidencia_oos` (2060-2070) es la redacción vigente y repite la coerción y las fronteras de `tramo_evidencia_oos`; esa duplicación desaparece con 2D-5.
  - La publicación del resultado pasa por `_retirar_intervalo_de_publicacion` y `_retirar_errores_oos_de_publicacion`. Esta última solo limpia `backtesting.predicciones`; ese es el origen del residual A1, porque `backtesting_comparativo.*.metricas.errores_extremos.observaciones` no se limpia.
- **Sesiones y exportables:**
  - `ControladorPrincipal._proyeccion_serializable` no serializa `backtesting_comparativo`, así que la sesión JSON queda limpia.
  - `generar_csv_reproducibilidad` tampoco lleva errores por ventana.
  - Los informes DOCX/PDF, con o sin el anexo de backtesting, están limpios.
  - La interfaz solo muestra conteos de errores extremos.
  - La fuga se queda en el objeto en memoria, que cualquier consumidor de `ejecutar_proyeccion` puede leer.
- **Registros de auditoría:** `generador_reportes.py:378-388` lee claves de traza que nadie produce (`tramo_evidencia_oos_horizonte_solicitado`, `formula_ventanas_oos`, `primer_origen_provisional`…). Las escribe como `""`. Es una decisión pendiente (02 §5), del mismo tipo que AS-004.
- **Pruebas de integración:** r3 y `test_informes_rediseno` son scripts históricos con efectos al importarse. Las pruebas esenciales de esta fase no dependen de ninguno de los dos.

No se propone ningún rediseño global ni cambios de producción en esta fase.
