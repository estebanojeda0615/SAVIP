# Contexto Thermos — Lote 2D-1 (Anti-Slop SAVIP V1.1.2), PASADA 1

MODO SOLO LECTURA. No edites el repositorio ni `C:/Pruebas SAVIP/L1D1/*`; temporales en tu propio directorio.
Python: "C:/Pruebas SAVIP/Fase0/venv-test/Scripts/python.exe" (QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1).
Hay una campaña larga corriendo en `C:/Pruebas SAVIP/L1D1/final_406e1dd` (no escribir ahí).

## Referencias
- V1.1.2 ORIGINAL empaquetada: fuente 6672529 (tag v1.1.2-rc.1), ZIP sha cee5897f…a94600; correspondencia bytecode 87/87 verificada en 2D-2; el EXE no se ejecuta, solo su fuente.
- Única excepción autorizada: AS-001 (la original lanza OverflowError al convertir una SSE extrema a float; Anti-Slop usa `_rmse_desde_sse`). No se toca en este lote.
- Base inmediata: 8e5a62b (rama maintenance/v1.1.2-as028-preparacion-2d1-as004-thermos, CI 43136025902 verde). Clon: `C:/Users/Esteban/Desktop/SAVIP_V112_LOTE2D1`, rama `maintenance/v1.1.2-fase2d-lote1-equivalencia-original-thermos`. Copia de la base: `C:/Pruebas SAVIP/L1D1/base`.
- Prohibido: cambiar cálculo/metodología (SSE Fraction, RMSErect, N0=12, H=24, 21 candidatos, W*×24), economía, GUI, sesiones, exportables, CSV reproducible y sus 17 columnas históricas (AS-004), P0-C/IC95, criterios.py (C-ALC-002 queda como deuda AS-024), 2D-3, `_evaluacion_horizonte` del script.

## Autorizado y hecho (diff `diff_pasada1.patch` = git diff 8e5a62b 406e1dd)
- `5706e85`: workflow (+1 rama) y .gitignore (+1 excepción docs).
- `fbaa0be` (G4.1, pruebas): retira 8 ids esenciales que solo ejercían `determinar_horizonte_maximo_estadistico` (6 en tests/test_resultado_horizonte_solicitado.py, 2 en tests/test_presentacion_resultados.py) con lápidas en comentario; quita `determinar_*` del import de módulo de test_resultado_horizonte_solicitado (los 9 ids vigentes no cambian); en la histórica tests/test_cierre_metodologico.py::test_no_queda_cascada_de_prefijo_en_ninguno_de_los_dos_maximos retira solo la aserción sobre `_mayor_horizonte_con` y conserva el resto. `_evaluacion_horizonte_ui` (presentación) queda sin uso y se conserva (alcance estricto).
- `406e1dd` (G4.2, atómico): retira por AST (`C:/Pruebas SAVIP/L1D1/g1/retirar_2d1.py`) las 6 definiciones de app_icociv/proyeccion/servicio_proyeccion.py (420 líneas de definición, 432 con separadores, 0 añadidas; resto del módulo idéntico en ast.dump; compartidos `_tipo_uso_horizonte` y `_mayor_horizonte_permitido` conservados; sin imports huérfanos) y en el MISMO commit adapta la guarda Fase 1A (`determinar_*` pasa de `retirados` espiado a `eliminados` con hasattr False; se mantiene el espía de `_evaluar_horizontes_proyeccion`).
- Matriz ID por ID y aserciones: `C:/Users/Esteban/Desktop/SAVIP_V112_LOTE2D1/docs/fase_v112_antislop_02d_lote1_equivalencia_original_thermos/02_MATRIZ_DE_BAJAS_Y_CONTRATOS_VIGENTES.md`.
- Inventario previo aprobado (AS-028): `docs/fase_v112_antislop_as028_preparacion_2d1_as004_thermos/` (05, 06, 04, 07, 09).

## Evidencias G0 (base 8e5a62b) en `C:/Pruebas SAVIP/L1D1/g0/`
- huella 0 dif (d6be699b…); collect 1036 + 3 errores históricos; script 19/7; cierre 21/1 (fallo preexistente test_no_hay_modelo_por_horizonte); oráculo 66: 8e5a62b = 7993060 (hash 766a34b8…); original r4 vs 8e5a62b solo AS-001; golden exacto 0; umbral AS-001 idéntico.
- Simulación de ausencia (sin editar): solo fallan los 18 esenciales previstos + la histórica cascada; script 19/7 idéntico; sonda AS-004 29 casos 0 diferencias; `referencias_dinamicas.txt` (sin getattr/importlib/__all__/spec sobre servicio_proyeccion).
- G4.1 verificado: `C:/Pruebas SAVIP/L1D1/g1/g41_afectados.txt` (1 FAIL preexistente) y collect 1028 + 3 errores.

## Pedido
Revisión del diff completo contra 8e5a62b: corrección de la eliminación (¿quedan referencias/llamadas, imports, acceso dinámico, sesiones?), que el diff productivo solo borre esas 6 definiciones, preservación de contratos (9 vigentes, Fase 1A, histórica), lápidas, y riesgos AS-004/2D-3. Hallazgos priorizados (crítico/alto/medio/bajo/info) con archivo:línea y evidencia propia; veredicto. Sé conciso. Responde en español.
