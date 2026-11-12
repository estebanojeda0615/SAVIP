# 04 · AS-004: funciones del generador, claves históricas y rutas de los informes (diagnóstico)

**`app_icociv/reportes/generador_reportes.py` no se modificó** (diff vacío frente a `102f194`). Todo lo que sigue es lectura estática y sondeo dinámico **no intrusivo**.

## 1. Instrumentos

| Instrumento | Qué hace | Salida |
|---|---|---|
| `evidencia/scripts/mapa_claves_as004.py` | Por AST, localiza todas las apariciones de las **43 claves** que devuelve `determinar_horizonte_maximo_estadistico` en `app_icociv`, `aplicacion.py`, `tests/`, `pruebas/` y `scripts/`. Clasifica cada una (productor por dict o asignación; consumidor por `.get`, subíndice o pertenencia; cadena) y la cruza con el grafo de alcanzabilidad | `evidencia/apariciones_claves.csv` (674 apariciones) |
| `evidencia/scripts/sonda_claves_as004.py` | Ejecuta `ejecutar_proyeccion` en 7 series × h ∈ {1, 12, 18, 24} (28 ejecuciones), más una «sesión heredada» con datos antiguos inyectados, con espías **pasivos** sobre las 8 funciones (solo cuentan y delegan). Registra qué claves históricas existen en `horizonte_info`, qué escribe el CSV reproducible en sus columnas históricas y de dónde saca la UI el texto del encabezado | `evidencia/sonda_claves_base.json` |
| `evidencia/scripts/escribir_03_csv.py` | Une los dos anteriores. Se queda solo con las lecturas cuyo **receptor** (obtenido por AST) es un alias verificado de `horizonte_info` o `analisis_horizontes_completo`. Las demás lecturas de claves homónimas van a una lista de descartes que se puede auditar. Además, comprueba que la raíz es `102f194` | `03_AS004_PRODUCTORES_CLAVES_CONSUMIDORES.csv` (60 filas) y `evidencia/03_descartes_lecturas_otros_receptores.csv` (101 lecturas; la subclave `trazabilidad.horizonte_maximo_evaluable_por_datos` se descarta como subclave, no como clave de `horizonte_info`) |
| `evidencia/scripts/sonda_oculto.py` | Repite la sonda con las 6 definiciones 2D-1 sustituidas en memoria por stubs que **fallan si se llaman**, y compara | 06 |

## 2. Hallazgos

### 2.1 Productores de claves históricas

| Productor | Alcanzable desde producción | Qué produce hoy |
|---|---|---|
| `determinar_horizonte_maximo_estadistico` (L3274-3531) | **No** (grafo; 0 llamadas en la sonda) | Las 43 claves, pero no se ejecuta |
| `_ejecutar_proyeccion_base`, `horizonte_info` (L1338-1373) | Sí | Ninguna clave «máximo/escenario/no recomendable». Solo `horizonte_solicitado`, `horizonte_finalmente_permitido` y `razones`, que son genéricas |
| `horizonte_info_insuficiente` (L1168-1175), historia insuficiente | Sí | `razones` y `mensaje` |
| **Plantilla por defecto de `_resultado_sin_proyeccion`** (L3934-3949) | **Sí** | Cuando `horizonte_info` llega vacío (serie sin valores válidos, errores críticos, ningún candidato con errores finitos comunes, o un fallo de reajuste): `horizonte_maximo`, `horizonte_maximo_recomendado`, `_permitido_como_escenario`, `_admisible`, `_evaluado` y `_busqueda_configurado`, todas a **0**; `primer_horizonte_no_viable=0`; listas vacías; y `accion="bloquear"`. La sonda lo confirma en el escenario `sin_valores_validos` |
| `_estructurar_resultado_horizontes` (L1660-1988) | Sí | Copia `info` y le añade `tabla_horizontes`, `evaluaciones` y `trazabilidad` |

### 2.2 Consumidores productivos de claves históricas

| Consumidor | Ruta | Claves históricas que lee | Exposición | Con la clave ausente |
|---|---|---|---|---|
| `construir_dataframe_reproducibilidad` (`generador_reportes.py` L102-420) | **Productiva**: `generar_csv_reproducibilidad` ← `VentanaPrincipal` y `_verificar_exportables` | `mensaje_no_recomendables`, `horizontes_evaluados`, `horizonte_maximo_recomendado`, `_con_cautela`, `_escenario` y `primer_horizonte_no_viable` (L157-162, L220-225, L277-282); `razon_parada`, `horizonte_maximo_evaluado`, `_permitido_como_escenario`, `_admisible`, `base_horizonte_maximo_recomendado`, `base_horizonte_maximo_escenario`, `advertencia_metodologica_horizontes`, `horizonte_maximo_evaluable_por_datos`, `horizonte_maximo_busqueda_configurado` y `horizonte_solicitado_cubierto` (L315-332) | **Columnas del CSV reproducible exportado**, con el mismo nombre o renombradas (`razon_parada_horizontes`, `limite_operativo_auditoria`) | Escribe `''` (y `False` en `horizonte_solicitado_cubierto`). Con la plantilla por defecto, escribe `0` |
| `_estructurar_resultado_horizontes` (L1668-1677, L1768-1772, L1861) | Productiva | `horizonte_maximo_admisible`, `horizonte_maximo_permitido`, `horizonte_maximo_evaluable_por_datos`, `horizontes_no_evaluados` y `primer_horizonte_no_viable` | Interna: redacción de la negativa y filas «No evaluado» | `0` o `[]`. Solo se ejecuta dentro de `ejecutar_proyeccion` (no lee sesiones restauradas) y el `0`/`[]` de la plantilla equivale al `or 0`/`or []` del lector: **sin efecto** |
| `_categorizar_advertencias` (L3827) | Productiva | `advertencias_por_horizonte` | `advertencias_categorizadas` | Lista vacía |
| `presentacion_resultados._encabezado` (L455-463) | Productiva | `mensaje_ui`, como **3.ª** opción tras `razon_principal` y `explicacion` | Texto del encabezado en la UI | Recurre a «Análisis ejecutado.». En las 28 ejecuciones se usa `razon_principal` (comparación por prefijo: `_encabezado` recorta textos largos); con la sesión heredada, `mensaje_ui` |
| `presentacion_resultados._resultado_solicitado` (L1322-1351) | Productiva | Solo como respaldo si falta `resultado_horizonte_solicitado` | UI | Usa `explicacion` |

**Constancia en un Golden Master.** Las columnas históricas del CSV forman parte del **Golden Master inmutable** `tests/fixtures/fase0/golden/sesion_exportables.json` (sección `csv` del informe `informe_proyeccion.csv`, L6659 y siguientes, que lista `mensaje_no_recomendables`, `horizonte_maximo_recomendado`, `horizonte_maximo_escenario`, `base_horizonte_maximo_recomendado`, etc.), protegido por el esencial `tests/test_fase0_golden_sesion_exportables.py`. Además, el esencial `tests/test_presentacion_resultados.py::test_exportable_diferencia_recomendado_evaluado_y_limite_operativo` (L436-458) **fija que el CSV lea** `horizonte_maximo_recomendado`, `horizonte_maximo_evaluado`, `horizonte_maximo_busqueda_configurado` (columna `limite_operativo_auditoria`) y `razon_parada` (columna `razon_parada_horizontes`) de `analisis_horizontes_completo`. Dejar de leerlas lo rompería aunque se conservara la columna. También son las de la V1.1.2 original: `git diff 6672529 102f194 -- app_icociv/reportes app_icociv/interfaz app_icociv/persistencia app_icociv/servicios` está **vacío**.

**Observación de AS-004 (sin intervenir).** Las columnas `firma_serie_sha256` y `version_criterios` del CSV (L333-334) leen subclaves de `horizonte_info.trazabilidad` que **ningún** productor de `app_icociv` genera, ni siquiera `determinar_*`, que solo reenvía `metadatos_auditoria`. Hoy siempre se escribe `''`. Es otra lectura sin productor y se suma al inventario de AS-004.

**Medición (sonda ampliada, 7 series × h ∈ {1, 12, 18, 24})**
- Con resultados nuevos, todas las columnas históricas del CSV valen `''`, salvo dos casos:
  - la plantilla (`sin_valores_validos`) escribe `0`;
  - `horizonte_solicitado_cubierto` vale `False`.
- Con la **sesión heredada** inyectada aparecen los valores antiguos (por ejemplo, `horizonte_maximo_recomendado=12`), y el encabezado de la UI pasa a `mensaje_ui`.
- Columnas `valor_csv_*` del CSV 03 y `evidencia/sonda_claves_base.json`.

### 2.3 Sesiones guardadas

- `ControladorPrincipal` serializa `horizonte_info` completo en la sesión (`controlador_principal.py` L409).
- `VentanaPrincipal._restaurar_sesion_pendiente` (L2313-2337) muestra el resultado guardado **sin recalcular**.
- Por tanto, una sesión guardada por una versión anterior que sí ejecutara `determinar_*` puede contener valores no nulos de esas claves. La UI y el CSV los mostrarían.
- Esto es **independiente** de que la función exista: son datos, no código.

### 2.4 Lecturas que no son de `horizonte_info`

Varias lecturas usan claves genéricas homónimas, pero el receptor es otro objeto:
- `.get("mensaje")` y `.get("accion")` de una evaluación o del bloque `resultado_horizonte_solicitado`;
- `advertencias` de `factibilidad`.

Se descartaron tras revisarlas una a una. Las claves genéricas que también produce la ruta vigente (`horizonte_solicitado`, `horizonte_finalmente_permitido`, `razones`, `mensaje`, `evaluaciones` y `trazabilidad`) tienen una sola fila resumen en 03.

## 3. Matriz de funciones históricas

| Función | Invocadores reales | Categoría | Evidencia |
|---|---|---|---|
| `_lineas_factibilidad` (L958-1003) | `generar_reporte_html` y el script (`test_horizonte_dinamico_con_serie_drift`) | **SOLO TEST HISTÓRICO** | Grafo: `produccion=false`. Ya lee la estructura **vigente** (`alcance_maximo_proyeccion`, `n0_backtesting`, `modelo_seleccionado`, `rmse_seleccion_oos`); comentario «Prompt 12» |
| `_lineas_horizontes` (L1038-1062) | `generar_reporte_html`; script (drift y holt); esencial `test_pool_calendario_fourier_seasonal::test_casoJ…` | **SOLO TEST** (con un contrato **vigente** en `casoJ`) | Grafo: `produccion=false`. Lee `tabla_horizontes` de h=1..24 |
| `_lineas_determinacion_horizonte` (L1065-1098) | `generar_reporte_html`; esencial `casoJ`; importación **sin uso** en `tests/test_resultado_horizonte_solicitado.py` L18 | **SOLO TEST** (contrato vigente en `casoJ`) | Grafo: `produccion=false`. Su comentario dice «Retirada la semántica triangular» |
| `generar_reporte_html` (L758-852) | `tests/test_p0c_regresion_negativa_c2.py`, archivo histórico con error de recolección conocido | **SOLO TEST HISTÓRICO** | Grafo: `produccion=false` y ningún `referenciado_por` |
| `_lineas_ejemplo_dinamico` (L855-939) y `_lineas_proyeccion` (L1379-1436) | `generar_reporte_html` | **SOLO TEST HISTÓRICO** | Son los únicos que leen `horizontes_no_recomendables` (L890) y `evaluaciones` (L1429) del modelo antiguo |
| `construir_dataframe_reproducibilidad` (L102-420) | `generar_csv_reproducibilidad` ← `VentanaPrincipal` y `_verificar_exportables` | **USADA EN PRODUCCIÓN** | Grafo: `produccion=true`; Golden `sesion_exportables` |
| Plantilla de `_resultado_sin_proyeccion` (`servicio_proyeccion.py` L3934-3949) | 4 de las 5 salidas tempranas de `_ejecutar_proyeccion_base` | **USADA EN PRODUCCIÓN** | Sonda: `sin_valores_validos` |
| `presentacion_resultados._encabezado`, rama `mensaje_ui` | `_encabezado` es productiva; la rama solo actúa si faltan `razon_principal` y `explicacion` | **SIN EVIDENCIA SUFICIENTE** de que esa rama se alcance con resultados nuevos (0 de 28). Sí se alcanza con la sesión heredada inyectada | Sonda: `encabezado_ui_fuente` |
| `presentacion_resultados._accion_horizonte` y `_proyeccion_restringida` | Ninguno | **NO ALCANZABLE** | Grafo: ninguna referencia |
| Ficha `C-ALC-002` (`criterios.py` L630-645) | Ninguno: es metadato que cita `servicio_proyeccion.py::_mayor_horizonte_con` | Documental | Cita documental del grafo (`citas_documentales`) |
| Informe productivo PDF/DOCX (`reportes/contenido.py`, `graficas.py`) | `generar_reporte_pdf` / `construir_bytes_reporte_docx` ← `_datos_informe` | **USADA EN PRODUCCIÓN**. **No** lee ninguna clave exclusiva de `determinar_*`: solo `tabla_horizontes` y `evaluaciones` | `03` |

## 4. Efecto de cada retiro hipotético

| Retiro hipotético | Efecto sobre las salidas | Fundamento |
|---|---|---|
| **2D-1** (las 6 definiciones) | **Ninguno.** Ninguna clave de las que leen los consumidores productivos procede hoy de `determinar_*`: unas no se producen y otras vienen de la plantilla de `_resultado_sin_proyeccion`, que no depende de 2D-1 | Grafo; sonda con 0 llamadas; sonda con la función oculta y comparación de claves, CSV y encabezado (06) |
| AS-004: **eliminar** columnas históricas del CSV | **Cambio visible**: cambia la cabecera del CSV exportado. Rompe el Golden `sesion_exportables` y `tests/test_presentacion_resultados.py::test_exportable_diferencia_recomendado_evaluado_y_limite_operativo`, y difiere de la V1.1.2 original | §2.2 |
| AS-004: conservar las columnas y **dejar de leer** las claves (sustituyendo por el valor por defecto del `.get`) | Igual con resultados nuevos. **Cambia** con la plantilla (`0` → `''` en 6 columnas) y con sesiones heredadas. **Rompe** `tests/test_presentacion_resultados.py::test_exportable_diferencia_recomendado_evaluado_y_limite_operativo` en sus 4 claves | §2.2 y CSV 03 |
| AS-004: quitar `mensaje_ui` del encabezado | Ninguno con resultados nuevos (28 de 28). **Cambio visible** con sesiones heredadas que no tengan `razon_principal` ni `explicacion` (comprobado con la inyección) | §2.3 |
| AS-004: retirar `_lineas_*` y `generar_reporte_html` | Ninguno sobre salidas productivas, pero caerían el esencial `casoJ` (contrato vigente), las pruebas drift/holt del script y el archivo histórico p0c | §3 |

## 5. Conclusión y recomendación independiente para AS-004

- **Hay un consumidor productivo que lee claves antiguas y publica columnas visibles:** el CSV reproducible, protegido por un Golden Master inmutable y por la equivalencia con la V1.1.2 original. Quitar esas lecturas **cambiaría un exportable**.
- Por eso, **cualquier retiro de las lecturas productivas de AS-004 es NO-GO POR DEPENDENCIAS** bajo la regla vigente («no permito nuevas diferencias»). Eso **no** se arregla cambiando el generador: no se hizo.
- **Esa dependencia no es de 2D-1.** Las lecturas no requieren que exista ninguna de las 6 funciones, y lo demuestra la simulación de 06. AS-004 deja de ser un bloqueo **técnico** del lote 2D-1. Sigue siendo una decisión pendiente **sobre el CSV**.
- **Recomendación: opción (b), una fase preparatoria de pruebas**, sin cambios de producción, que:
  1. fije por prueba el conjunto y el orden de las columnas del CSV. Ya lo cubren en parte el Golden `sesion_exportables` y `tests/test_presentacion_resultados.py::test_exportable_diferencia_recomendado_evaluado_y_limite_operativo` (4 claves); se explicitaría para las 13 columnas restantes;
  2. migre el contrato vigente de `casoJ` al informe productivo (`contenido.py`);
  3. quite la importación sin uso de `_lineas_determinacion_horizonte` en `test_resultado_horizonte_solicitado` (es solo de test).
- Después, decidir por separado y con permiso explícito:
  - el retiro de `generar_reporte_html` y su cadena `_lineas_*`, que es una opción (c) sin efecto productivo;
  - el destino de las columnas históricas del CSV. Retirarlas sería una **diferencia funcional** frente a la V1.1.2 original y exigiría que el propietario la aceptara de forma expresa, como AS-001. **No se recomienda dentro de Anti-Slop.**
- La opción (a), más análisis documental, no hace falta: el mapa está completo para lo que decide.

**Nunca se afirma que AS-004 se haya ejecutado o limpiado. No se tocó ninguna línea del generador.**
