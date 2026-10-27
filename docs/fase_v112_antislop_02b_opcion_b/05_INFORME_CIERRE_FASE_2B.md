# 05 · Informe de cierre de la Fase 2B (AS-003, opción B)

## Dictamen: **APTO**

**Qué se hizo.** Se retiraron las tres funciones previstas tras superar G1–G5. Se adaptó la prueba esencial que exigía su existencia, sin debilitarla y con sensibilidad comprobada, y se trataron una a una las pruebas históricas afectadas.

**Verificación:**
- los mismos 797 ids esenciales, todos en PASS;
- 29/29 golden sin cambios;
- AS-001 en PASS;
- huella semántica exacta con 0 diferencias;
- CI en verde sin reintentos.

**Alcance.** La opción B queda completa. **AS-003 no queda resuelto**: el resto del subsistema sigue bloqueado por el registro de auditoría (§3).

## 1. Respuestas del §9

**¿Se retiraron exactamente los tres símbolos previstos?** **Sí**, y nada más:
- `_rmse_global_estable` (30 líneas);
- `_modelo_consistente_desde_comparativo` (14);
- `_modelo_trayectoria_consistente` (60).

Ninguno tenía consumidores en producción, scripts, `pruebas/`, `packaging`, fichas de `criterios.py` ni acceso dinámico (01).

**¿Qué archivo esencial se adaptó y cómo comprobamos que no se debilitó?** `tests/test_fase1a_selector_rectangular.py::test_la_ruta_productiva_usa_el_selector_rectangular_y_ningun_selector_retirado`, con el **mismo id**.
- **Lo que pasa a exigir:** que las tres funciones estén **ausentes**.
- **Lo que sigue comprobando:**
  - que la ruta productiva no llame a los 3 heredados que permanecen (espías con `call_count == 0`);
  - una llamada a la matriz y otra al selector rectangular;
  - la concordancia de la selección;
  - 21 candidatos, h=1..24 y W*×24.
- **Sensibilidad.** Falla con las funciones presentes (S0), si la ruta invoca el selector heredado (S1) y si se sustituye el selector rectangular por un mutante que viola el SSE exacto y la muestra común (S2). El control pasa.
- **Los 5 mutantes de la Fase 1A** siguen detectados (02 §1).

**¿Qué pruebas históricas se afectaron y cuál fue su destino?** 4 archivos y 64 ids (02 §2):
- `test_rmse_global_estable`: 7 retiradas (T1–T6b, solo API retirada) y 4 conservadas;
- `test_p0d_rmse_orden_exacto`: D1 adaptada, con las mismas aserciones, y 12 sin cambio;
- `test_seleccion_rmse_global`: 1 retirada, 3 adaptadas (una más estricta) y 12 sin cambio;
- `test_cierre_metodologico`: 1 retirada y 23 sin cambio, incluido 1 FAIL previo.

Ningún archivo borrado y ninguna expectativa sustantiva cambiada. Las propiedades vigentes las cubren pruebas esenciales.

**¿Se conservan los 797 ids esenciales y los 29 Golden Masters?** **Sí.** El conjunto de ids es idéntico por `(classname, name)` y todo pasa. Los golden no cambian: diff vacío en `tests/fixtures`.

**¿Hubo 0 diferencias exactas en la huella semántica?** **Sí.** El SHA-256 es idéntico (`d6be699b…`) en la base (dos capturas) y después.

**¿Cuántas líneas se eliminaron de verdad?**

| Categoría | Líneas |
|---|---|
| Producción | **−110**: 104 de definiciones, 6 separadores en blanco y **0 imports** |
| Pruebas | −87 / +33 (neto **−54**). La esencial gana 4 líneas (+6/−2) y las históricas pierden 58 en neto |
| Workflow | +1 |
| Documentación | Solo se añade: esta carpeta y la excepción en `.gitignore` |

**¿Cuál es el SHA del HEAD publicado y su CI verde?**
- El código es `10f1d0d`, con CI [40578617725](https://github.com/estebanojeda0615/SAVIP/actions/runs/40578617725): success, 797/797, ninguna intermitente.
- El HEAD final es el commit de documentación que contiene este informe. Su SHA y su CI se informan en el mensaje de entrega.

**¿Qué partes de AS-003 siguen BLOQUEADAS?** 31 definiciones y unas 1 723 líneas:
- el selector `seleccionar_modelo_por_rmse_oos_global` y `_errores_oos_por_par`;
- `_evaluar_horizontes_proyeccion` y `_clasificar_evidencia_horizonte`, con sus auxiliares;
- `determinar_horizonte_maximo_estadistico` y sus 6 auxiliares;
- la salvaguarda de benchmarks;
- `seleccionar_modelo_por_evidencia` y sus 9 auxiliares;
- `tramo_evidencia_oos`.

Las anclan:
- 9 pruebas esenciales: 8 las ejercen como registro de auditoría y la adaptada de la Fase 1A espía tres de ellas;
- 2 scripts de `pruebas/`;
- 6 fichas de `criterios.py`.

## 2. Riesgos y límites

- **Comentarios históricos.** Quedan menciones a las funciones retiradas en docstrings y comentarios: 3 lugares de `servicio_proyeccion.py` y 2 docstrings de módulo de prueba. No son llamadas, y la producción estaba limitada a las 3 definiciones. Conviene actualizarlas en 2C.
- **El valor de auditoría de `_modelo_trayectoria_consistente`.** Su docstring la declaraba parte del registro (1/h frente a RMSE global). Su retiro estaba autorizado expresamente. El contraste se conserva así:
  - de forma explícita en `test_no_hay_peso_por_horizonte`;
  - el código completo, en `1848275`.
- **Anomalía declarada (04 §5).** Una prueba GUI de temporización heredada falló una vez sobre el código base en la corrida instrumentada. No es reproducible (0 fallos en 65 ejecuciones del caso y 13 del archivo) y no es una regresión.
- **Grafo estático.** Su riesgo residual lo mitigan G2 (espía en tiempo de ejecución), el `grep` de todo el repositorio y la prueba esencial que ahora exige la ausencia de las tres funciones.

## 3. Propuesta para la Fase 2C

Antes de tocar más código, decidir el destino del **registro de auditoría ejecutable**. Hay dos opciones:

**(a) Mantenerlo como código.**
- Cierra AS-003 tal como está.
- Solo se actualizan los comentarios que citan funciones retiradas.

**(b) Retirarlo.** Exigiría, con autorización expresa:
1. sustituir los casos esenciales que ejercen reglas retiradas por su equivalente documental, o retirarlos, con los ids registrados;
2. decidir sobre `pruebas/prueba_horizonte_dinamico_ui_reportes.py` (AS-028);
3. separar las fichas de `criterios.py` de sus «ubicaciones» ejecutables (AS-024).

Hecho eso, se aplicaría el mismo protocolo de esta fase: G1–G6, huella exacta, los 797 ids y CI.

## 4. Lo que no se tocó

- **Ramas y versión:** `main`, `develop/v1.1.2`, las ramas de las fases 0, 1A, 1B y 2A, el tag y el Release `v1.1.2-rc.1`.
- **Código y configuración:** `VERSION`, `packaging/`, dependencias, `criterios.py`, `pruebas/`, la ruta vigente, la economía, las sesiones y los exportables.
- **Operaciones no realizadas:** merge, PR, tag, release, ejecutable y ZIP.
