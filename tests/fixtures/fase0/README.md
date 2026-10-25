# Fixtures y Golden Masters de la Fase 0 (SAVIP 1.1.2)

Datos 100 % sintéticos y deterministas: no hay anexos del DANE, sesiones personales ni rutas locales.

| Archivo | Qué es |
|---|---|
| `generadores.py` | Series del motor (5 escenarios con semillas fijas y una serie de 30 meses para el rechazo), anexo 16 sintético de 2 grupos (2023-01 a 2026-12) y vectores económicos. Todo se genera en memoria o en una carpeta temporal. |
| `captura.py` | Ejecuta el motor, las reglas económicas y el empalme reales y extrae lo observable. También contiene el comparador con tolerancias y la normalización de textos (fechas, IDs y rutas temporales). |
| `captura_gui.py` | Recorrido completo en la ventana real (Qt offscreen): proyectar, calcular actividades, consultar H11→H23→H11, deshacer/rehacer, guardar, reabrir y exportar Excel, PDF, DOCX y CSV. |
| `generar_golden.py` | Escribe `golden/*.json` **una sola vez**. Se niega si el código productivo difiere del commit `6672529` o si ya existe algún golden. |
| `golden/metadatos.json` | Commit de referencia, árbol `app_icociv`, versiones de los paquetes y tolerancias. |
| `golden/motor.json`, `golden/economico.json`, `golden/sesion_exportables.json` | Valores esperados congelados. |

## Reglas

- Las pruebas (`tests/test_fase0_golden_*.py`) **solo leen** los golden; nunca los reescriben.
- Si un cambio de comportamiento se acepta deliberadamente, se borran los golden afectados en un commit propio que explique el cambio. Después se regeneran con `python -m tests.fixtures.fase0.generar_golden` sobre el commit nuevo y se actualiza `COMMIT_REFERENCIA`.
- Tolerancia de flotantes: `rel_tol = 1e-9`, `abs_tol = 1e-12`.
  - Motivo: el lock fija las versiones, pero los núcleos BLAS/LAPACK eligen instrucciones SIMD según la CPU y pueden variar en los últimos bits (~1e-15 relativo).
  - Textos, códigos de modelo, enteros, booleanos, órdenes y el porcentaje/factor `Decimal` se comparan exactos.
- Empate exacto (`lineal_exacta_empate`): hay 3 candidatos con SSE 0. Se exige que el ganador esté en ese grupo empatado y que sea el mínimo obtenido. Es la regla de desempate documentada en `_seleccionar_modelo_rectangular`.
