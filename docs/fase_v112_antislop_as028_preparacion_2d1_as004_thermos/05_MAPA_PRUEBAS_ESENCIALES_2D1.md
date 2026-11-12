# 05 · Mapa de pruebas esenciales e históricas que dependen de 2D-1 (G3, solo inventario)

**En esta fase no se eliminó ni se cambió ninguna prueba de `tests/`.** Este documento solo dice qué haría falta en una futura ejecución de 2D-1, y bajo qué autorización.

## 1. Método

Los consumidores se recalcularon sobre el HEAD real (`102f194`) por cuatro vías, sin fiarse de los recuentos del plan 2C:

| Vía | Qué detecta | Evidencia |
|---|---|---|
| AST por test | Nombres y atributos, cadenas literales, importaciones de nivel de módulo, y el uso indirecto a través de auxiliares del mismo archivo, incluidos los métodos de clase | `evidencia/scripts/usos_por_test_2d1.py` → `evidencia/usos_por_test.txt` |
| Grafo de definiciones | Alcanzabilidad desde producción, scripts y tests | `evidencia/grafo_102f194_2d1.json` |
| `grep` textual | `inspect`, `patch.object`, `getattr` y cadenas en comentarios | §4 |
| Simulación de ausencia | Ids que fallan al ocultar las 6 definiciones en memoria | 06 |

**Perfiles** según `scripts/pruebas_fase0.py`:
- **esenciales:** `test_resultado_horizonte_solicitado`, `test_presentacion_resultados`, `test_fase1a_selector_rectangular`, `test_fase2c_contratos_vigentes` y `test_pool_calendario_fourier_seasonal`;
- **históricas:** `test_cierre_metodologico` y `test_regresiones_auditoria_independiente_bghc` (estilo script: 0 tests recogidos).

**Estado en la base:** todos los ids esenciales de la tabla están en **PASS** (`evidencia/esenciales_base_resumen.txt`, 809/809). La histórica `test_cierre_metodologico::test_no_queda_cascada…` también está en **PASS** (`evidencia/cierre_base.txt`).

## 2. Ids afectados por un retiro futuro de las 6 definiciones

Leyenda de las decisiones:
- **RETIRAR**: la prueba solo ejerce la función muerta. Requiere la autorización explícita de 2D-1 para dar de baja ids esenciales.
- **ADAPTAR-IMPORT**: el contrato es vigente y no cambia. Solo se quita el nombre del `import` de nivel de módulo, sin tocar ninguna aserción.
- **ADAPTAR-AUSENCIA**: el contrato pasa de «0 llamadas» a «el símbolo no existe».

### 2.1 `tests/test_resultado_horizonte_solicitado.py` (esencial, 15 ids)

El módulo importa `determinar_horizonte_maximo_estadistico` en su nivel superior (L10-16). Si la función desapareciera, **los 15 ids** se convertirían en un error de recolección, no solo los 6 que la usan (lo confirma 06).

También importa `_lineas_determinacion_horizonte` (L18). Esa importación **no se usa**: el nombre solo aparece en un docstring. Es un acoplamiento con AS-004 y no con 2D-1.

| Id | Base | Símbolo | Aserciones relevantes | Contrato vigente que conservar | Sustituta identificada | Decisión propuesta para 2D-1 | Riesgo |
|---|---|---|---|---|---|---|---|
| `test_maximos_se_derivan_de_clasificaciones_y_no_del_limite_de_grilla` | PASS | `determinar_*` | `horizonte_maximo_recomendado==8`, `_como_escenario==11`, `_evaluado==12`, `primer_horizonte_no_viable==12` y `horizonte_maximo==8` sobre la entrada sintética | Ninguno: es la aritmética de la función muerta | `test_metodologia_n0_12_h24::test_b_h_operativo_max_es_24`; `test_resultado_horizonte_solicitado::test_maximo_tarjeta_usa_alcance_operativo_vigente` | RETIRAR | Bajo |
| `test_limite_evaluable_se_informa_sin_convertirlo_en_validez_absoluta` | PASS | `determinar_*` | `tipo_parada`, `horizontes_no_evaluados==[6..10]`, `maximo_recomendado_es_limite_observado` | Ninguno | Las mismas | RETIRAR | Bajo |
| `test_maximo_evaluado_20_es_descriptivo_de_la_funcion_retirada` | PASS | `determinar_*` (más `_lineas_determinacion_horizonte` en el docstring) | Campos de la función muerta; su docstring lo declara así | Ninguno | Las mismas | RETIRAR | Bajo |
| `test_20_puede_ser_maximo_recomendado_si_h20_es_tecnico` | PASS | `determinar_*` | Máximos con h=20 técnico | Ninguno | Las mismas | RETIRAR | Bajo |
| `test_20_puede_ser_maximo_escenario_si_h20_es_escenario_explicito` | PASS | `determinar_*` | Máximo de escenario | Ninguno | Las mismas | RETIRAR | Bajo |
| `test_parada_en_20_por_evidencia_incluye_advertencia_y_no_extrapola` | PASS | `determinar_*` | `advertencia_metodologica_horizontes` y la parada | Ninguno | Las mismas | RETIRAR | Bajo |
| `test_predeterminado_admisible_centra_h12_y_conserva_tabla_completa`, `test_manual_admisible_identifica_origen_y_h7`, `test_no_admisible_nunca_se_llama_proyeccion_tecnica`, `test_h32_no_admisible_no_expone_proyeccion_y_marca_no_evaluados`, `test_restriccion_no_hace_pasar_h12_como_resultado_de_h18`, `test_horizonte_manual_invalido`, `test_evaluacion_es_mensual_continua`, `test_h45_se_rechaza_explicitamente_h12_se_genera_normalmente`, `test_maximo_tarjeta_usa_alcance_operativo_vigente` (9) | PASS | Ninguno; solo les afecta el `import` del módulo | Las suyas, sin cambios | **Vigentes**: resultado solicitado, origen, rechazo de h fuera de 1..24 y tarjeta «máximo» | No procede | **ADAPTAR-IMPORT**: quitar `determinar_horizonte_maximo_estadistico` del `import` de L10-16, sin tocar ninguna aserción | Medio si se olvida, porque 15 ids caerían en error de recolección |

### 2.2 `tests/test_presentacion_resultados.py` (esencial; 2 de 13 ids)

En este archivo la importación es local, dentro de cada test. Solo fallarían estos dos.

| Id | Base | Aserciones relevantes | Contrato vigente | Sustituta | Decisión propuesta | Riesgo |
|---|---|---|---|---|---|---|
| `test_horizonte_dinamico_diferencia_tecnico_cautela_y_no_evaluado` | PASS | `horizonte_maximo_recomendado==12`, `_como_escenario==18`, `accion=="permitir con cautela"` / `"restringir"` sobre entrada sintética | Ninguno: su docstring admite que esa combinación «ya no ocurre con datos reales» | `test_metodologia_n0_12_h24::test_efg…`; `test_resultado_horizonte_solicitado::test_restriccion_no_hace_pasar_h12_como_resultado_de_h18` | RETIRAR | Bajo |
| `test_horizonte_no_salta_un_corte_no_viable` | PASS | Un hueco en h=2 no veta h=4; `primer_horizonte_no_viable==2` | Ninguno en producción: bajo 12/24 no hay veto por horizonte | `test_fase2c_contratos_vigentes::test_la_ruta_vigente_no_referencia_el_subsistema_heredado` | RETIRAR | Bajo |

### 2.3 `tests/test_fase1a_selector_rectangular.py` (esencial)

| Id | Base | Símbolo | Cambio futuro necesario | Riesgo |
|---|---|---|---|---|
| `test_la_ruta_productiva_usa_el_selector_rectangular_y_ningun_selector_retirado` | PASS | `"determinar_horizonte_maximo_estadistico"` en la tupla `retirados`, que se espía con `patch.object(sp, n, wraps=getattr(sp, n))` | **ADAPTAR-AUSENCIA.** Pasar el nombre de `retirados` (espiado) a `eliminados`, cuya regla es `assert [n for n in eliminados if hasattr(sp, n)] == []`. No basta con un `patch.object` sobre un símbolo inexistente: daría `AttributeError`. `_evaluar_horizontes_proyeccion` (2D-3) sigue espiado | Bajo |

### 2.4 `tests/test_fase2c_contratos_vigentes.py` (esencial)

| Id | Base | Símbolo | Cambio futuro | Riesgo |
|---|---|---|---|---|
| `test_la_ruta_vigente_no_referencia_el_subsistema_heredado` y los 6 restantes | PASS | La tupla `HEREDADAS` de nivel de módulo nombra las 8 definiciones (las 6 objetivo y las 2 compartidas) **como texto**: «no exige que existan ni que falten». `test_escasez_…[36/37/41]` y `test_banda_no_construible_…` contienen la subcadena `_evidencia_horizonte` solo como parte de otro nombre o de un comentario | **Ninguno.** Pasa con los símbolos presentes o ausentes (lo confirma 06) | Nulo |

### 2.5 `tests/test_pool_calendario_fourier_seasonal.py` (esencial): AS-004, no 2D-1

| Id | Base | Símbolo | Cambio futuro | Riesgo |
|---|---|---|---|---|
| `test_casoJ_ids_internos_no_visibles_en_ui_ni_reportes` | PASS | `_lineas_horizontes` y `_lineas_determinacion_horizonte` | **Ninguno para 2D-1.** Si en el futuro se autoriza retirar `_lineas_*` (AS-004), habría que migrar este contrato **vigente** (los ids internos no se ven) al generador productivo (`contenido.py`) **antes** de la baja | Medio solo para AS-004 |

### 2.6 Históricas

| Id | Perfil | Base | Símbolo | Decisión propuesta | Riesgo |
|---|---|---|---|---|---|
| `tests/test_cierre_metodologico.py::test_no_queda_cascada_de_prefijo_en_ninguno_de_los_dos_maximos` | históricas | PASS | `sp._mayor_horizonte_con` (2D-1) y `sp._mayor_horizonte_permitido` (compartido), más el AST de `_evaluar_horizontes_proyeccion` (2D-3) | Con 2D-1 fallaría por `AttributeError` en `_mayor_horizonte_con` (06). Opciones para el futuro prompt: retirar la línea de `_mayor_horizonte_con` y conservar las demás aserciones hasta 2D-3, o retirar el test con 2D-3. **Decisión del propietario** | Bajo: es histórica |
| `tests/test_regresiones_auditoria_independiente_bghc.py` | históricas (estilo script; pytest no recoge tests, código 5) | — | Solo `_mayor_horizonte_permitido` (compartido; queda con 2D-3) | **Ninguno para 2D-1.** Su destino es AS-007/2D-3 | Nulo para 2D-1 |

## 3. Recuentos frente al plan 2C

| Concepto | Plan 2C | HEAD real `102f194` |
|---|---|---|
| Esenciales que ejercen 2D-1 directamente | 8 (6 + 2) | **8** (6 + 2), coincide |
| Esenciales que fallarían al retirar 2D-1 | No se calculó | **18 ids**: 15 de `test_resultado_horizonte_solicitado` (por el `import` del módulo; 9 de ellos son vigentes y solo necesitan ADAPTAR-IMPORT) + 2 de `test_presentacion_resultados` + 1 de la Fase 1A. Medido en 06: coincide exactamente (1 error de recolección que arrastra 15 ids, 2 ImportError y 1 AttributeError) |
| Adaptación de la Fase 1A | Prevista | Confirmada: ADAPTAR-AUSENCIA |
| Históricas | `test_cierre_metodologico::test_no_queda_cascada_…` | La misma. No se hallaron otras |
| Script | 3 pruebas | Retiradas en esta fase (02) |

## 4. Referencias textuales en producción (sin intervenir)

| Ubicación | Naturaleza | Efecto de 2D-1 |
|---|---|---|
| `app_icociv/estadistica/analisis_series.py` L712-713 y L797 | Comentarios que citan `determinar_horizonte_maximo_estadistico` | Ninguno en la ejecución; quedarían desactualizados (higiene documental) |
| `app_icociv/interfaz/presentacion_resultados.py` L1333 | Comentario | Ídem |
| `app_icociv/estadistica/criterios.py` L637-639, ficha `C-ALC-002` | Texto `"app_icociv/proyeccion/servicio_proyeccion.py::_mayor_horizonte_con"` como ubicación documental. No es una arista del grafo | La ficha apuntaría a un símbolo inexistente. Habría que decidir sus metadatos con AS-024; **sin modificar en esta fase** |
| `servicio_proyeccion.py`: docstrings y comentarios de los auxiliares compartidos | Texto | Ninguno |

## 5. Pruebas nuevas propuestas (no añadidas)

No hacen falta para retirar 2D-1: la cobertura vigente del §2 ya existe.

Para AS-004, en cambio, conviene proponer **antes** de cualquier baja de `_lineas_*`:
- una prueba que fije las **columnas del CSV reproducible** frente al estado actual, para que no cambien por accidente. Hoy ya las protegen en parte el Golden `sesion_exportables` y `tests/test_presentacion_resultados.py::test_exportable_diferencia_recomendado_evaluado_y_limite_operativo` (4 claves leídas de `analisis_horizontes_completo`); faltaría cubrir las 13 restantes;
- una prueba de `test_casoJ` sobre el informe productivo (04).
