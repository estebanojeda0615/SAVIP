# 05 · Informe de cierre de la Fase 2A (AS-003)

## Dictamen: **APTO CON RESERVAS**

**Lo que se hizo.** Se retiraron 6 definiciones demostradamente muertas: **200 líneas de producción** en 2 módulos. Todas superaron las puertas G1–G6.

**Verificación:**
- huella semántica exacta idéntica;
- 29/29 golden;
- 797/797 esenciales, con el mismo conjunto de ids;
- CI en verde.

**La reserva.** **AS-003 no queda resuelto.** El núcleo del subsistema heredado, unas 1 827 líneas en 34 definiciones, sigue DEFERIDO. Lo anclan:
- 9 pruebas esenciales que lo ejercen directamente;
- 2 scripts de `pruebas/`;
- 6 fichas de `criterios.py`.

Retirarlo exige la decisión que ya pedía la auditoría: si el «registro de auditoría» debe seguir en código ejecutable.

## 1. Cifras comprobadas

| Indicador | Valor |
|---|---|
| Líneas de producción retiradas | **200** (`servicio_proyeccion.py` −185, `validacion_series.py` −15). De ellas, 183 son líneas de definición |
| Definiciones retiradas | **6**: `_metadatos_auditoria_horizontes`, `_numero_parametros_modelo`, `_metricas_desde_predicciones`, `_explicacion_factibilidad`, `_validar_ajuste_calendario_serie` y `resumen_validacion` |
| Imports retirados | **6** que solo usaban esas funciones: `hashlib`, `datetime`, `timezone`, `TOLERANCIA_DETERIORO_AJUSTE_CALENDARIO`, `evaluar_ajuste_en_backtesting` y `calcular_escala_naive_insample` |
| Módulos afectados | 2. `modelos_interpretables.py` no cambió |
| Pruebas | **0** retiradas y **0** adaptadas. Se preservan las 797 esenciales (mismos ids) y las 1 061 recolectadas (mismos ids) |
| Rutas afectadas | Ninguna ruta vigente. Las 6 funciones no tenían ningún llamador |
| Símbolos DEFERIDOS | 34 (1 827 líneas). FUERA DE ALCANCE: 1 (`calendario_anual.evaluar_ajuste_en_backtesting`) |
| Tiempo del perfil esencial | Base: 1 838 s. Final: 1 691 s (mismo equipo; la diferencia es ruido de ejecución) |

**Hallazgo lateral.** `_metricas_desde_predicciones` usaba un nombre no definido (`detectar_errores_extremos`): si alguien la hubiera llamado, habría lanzado `NameError`. Ninguna ruta la usaba.

## 2. Funciones que se conservan por contrato

| Función | Motivo |
|---|---|
| `servicio_proyeccion.ejecutar_analisis` | **API documentada** y contrato de `pruebas/ejemplo_uso.py`. Solo llama a la ruta vigente, así que **no obliga a conservar ninguna línea heredada**. La GUI usa otro método homónimo, `ControladorPrincipal.ejecutar_analisis` |
| `validacion_series.validar_serie` y `detectar_outliers_extremos` | Contrato S: las usa `pruebas/prueba_estadistica.py`, que se ejecutó antes y después con salida idéntica. La auditoría las daba por muertas porque no miró `pruebas/` |
| `_sse_exacto`, `_rmse_desde_sse` y la ruta `ejecutar_proyeccion → _ejecutar_proyeccion_base → _matriz_rectangular_12_24 → _seleccionar_modelo_rectangular` | Obligatorias. No se tocaron |
| Subsistema heredado: selector por RMSE global, evaluación, clasificación y decisión de horizontes, salvaguarda, `seleccionar_modelo_por_evidencia` y auxiliares | DEFERIDO. Lo anclan pruebas esenciales, scripts y fichas (02 §4) |

## 3. Confirmaciones

Según la huella exacta, los golden y el perfil esencial:
- **No cambiaron:**
  - el modelo ganador y el segundo;
  - el RMSErect y el SSE exacto de los 21 candidatos;
  - los pares W*×24;
  - la trayectoria H1–H24, MAE(h) y el sesgo;
  - la consulta de horizonte sin recálculo;
  - las cifras económicas;
  - las sesiones y los exportables (Excel con fórmulas, PDF, DOCX y CSV).
- **AS-001** sigue corregido: 16 casos en PASS.
- **Fuera de AS-003:** no se tocó ningún archivo de producción. Solo se añadió la rama al filtro del workflow, algo autorizado.
- **Ramas y versión:** `main`, `develop/v1.1.2`, las ramas de las fases 0, 1A y 1B, el tag y el Release `v1.1.2-rc.1` no se modificaron. No hubo nueva release, `VERSION`, ZIP ni ejecutable.

## 4. Pendientes y riesgos

- **Decisión pendiente (opción B).** Consiste en autorizar la adaptación de la prueba esencial de la Fase 1A `test_la_ruta_productiva_usa_el_selector_rectangular_y_ningun_selector_retirado`. Hoy espía 6 nombres retirados; pasaría a comprobar «ausente o no llamado». Sería el mismo caso, con las 797 intactas. Eso liberaría 3 funciones (104 líneas), con trato G5 individual de 4 archivos históricos.
- **Decisión sobre el «registro de auditoría».** Si se decide que las reglas retiradas no deben vivir en código ejecutable, habría que:
  1. sustituir o retirar los casos esenciales que las ejercen, con autorización expresa, porque hoy está prohibido perder casos esenciales;
  2. decidir sobre `pruebas/prueba_horizonte_dinamico_ui_reportes.py` (AS-028);
  3. separar las fichas de `criterios.py` de su «ubicación» ejecutable (AS-024).

  Solo entonces se liberarían unas 1 800 líneas.
- **Riesgo residual de G1.** El grafo es estático. Un acceso por nombre construido en tiempo de ejecución (`f"_{x}"`) escaparía, aunque no se encontró ninguno. Lo mitigan G2, porque ninguna prueba del perfil llamó a las 6 funciones; `grep` de todo el repositorio; y que una de ellas ni siquiera podía ejecutarse.
- **Fuera de alcance, sin tocar:**
  - 5 imports sin uso y 2 variables locales sin uso que ya existían en `c9166c6`, en la ruta vigente;
  - `calendario_anual.evaluar_ajuste_en_backtesting`, que ya no tiene llamador en producción;
  - el defecto de `pruebas/ejemplo_uso.py` con `ci_lo=None` (AS-028);
  - AS-004, AS-005, AS-013, AS-014, AS-015, AS-016, AS-024, AS-028 y el resto de la auditoría.

## 5. Recomendación

1. Decidir la opción B: es un lote pequeño, verificable con el mismo protocolo.
2. Decidir el destino del «registro de auditoría» antes de cualquier otra fase sobre el motor. Es la decisión que bloquea el resto de AS-003, y conviene tomarla junto con AS-024 y AS-028.
3. No iniciar otros hallazgos hasta revisar esta fase.

## 6. Enlaces

| Qué | Enlace |
|---|---|
| Rama | https://github.com/estebanojeda0615/SAVIP/tree/maintenance/v1.1.2-fase2a-as003 |
| Comparación con la Fase 1B | https://github.com/estebanojeda0615/SAVIP/compare/maintenance/v1.1.2-fase1b-as001...maintenance/v1.1.2-fase2a-as003 |
| Commits | `d7429df`, `c6ca863` (retiros), `81a8247` (workflow) y el commit de documentación |
| CI del código | [40445532574](https://github.com/estebanojeda0615/SAVIP/actions/runs/40445532574) (`81a8247`, success, 797/797). El CI del HEAD final se informa en el mensaje de entrega |
