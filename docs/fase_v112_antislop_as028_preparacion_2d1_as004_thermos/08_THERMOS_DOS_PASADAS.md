# 08 · Thermos: dos pasadas reales con los dos agentes

| Dato | Valor |
|---|---|
| Plugin | `thermos@thermos-claude-plugin` 1.1.0, ya instalado (commit `dc8791f8`). No se reinstaló. Claude Code 2.1.238, sin `--effort` |
| Invocación | Skill `thermos:thermos`, que lanza los dos agentes reales en paralelo y en segundo plano: `thermos:thermo-nuclear-reviewer` (corrección) y `thermos:thermo-nuclear-code-quality-reviewer` (calidad) |
| Entrada | Diff exacto contra **`102f194`**, guardado en un `.patch` fuera del repositorio. Además: copias limpias de la base y del final; un contexto escrito con el alcance, la regla de que la producción no se toca, el mapa AS-004, las listas de ids, el motivo de cada baja y los resultados base; y las herramientas y evidencias |
| Modo | Solo lectura. Los agentes ejecutaron AST, `grep`, `git` en lectura y sus propias regeneraciones y sondas, en temporales fuera del repositorio |
| Interrupción | La 2.ª pasada se lanzó por primera vez a las 21:4x UTC y **se detuvo** por el límite de cuota antes de devolver resultados. Se volvió a lanzar completa al reanudar (2026-11-12). Solo cuentan los resultados del relanzamiento |

> **Thermos solo revisa.** No sustituye a las ejecuciones, las sondas, el oráculo ni el perfil esencial (02-07), ni autoriza cambios de producción.

## 1. Pasadas

| Pasada | SHA y archivos revisados | Corrección | Calidad |
|---|---|---|---|
| **1.ª** | `102f194..5133abc` (primer diff material: workflow, `.gitignore` y script), más el delta `5133abc..7993060` (restauración de `_evaluacion_horizonte`) y el borrador del CSV AS-004 | **GO.** Ningún hallazgo crítico, alto ni medio. Confirma que ningún assert retirado protegía un contrato vigente; que `main()` tiene 26/26 llamadas y no queda ningún `NameError`; la conclusión de AS-004, reforzada por las sesiones restauradas sin recálculo; y la ausencia de accesos dinámicos. Considera correcto conservar el auxiliar (I-1). Bajos: B-1 (la lápida remite al doc 02, todavía sin versionar) y B-2 (un nombre de test partido en dos líneas) | **Código del script aprobable con cambios menores. Evidencias NO aprobadas tal como estaban.** A1 (alto): falsos positivos en el CSV 03 (lecturas de otros diccionarios). A2 (alto): el efecto «CAMBIO VISIBLE» estaba sobreafirmado. M1: prefería retirar el auxiliar. M2: lápida. M3: la sonda solo usaba h=12 y reimplementaba la UI. M4: líneas fijadas a mano y extracción sin `assert`. Bajos B1-B5 |
| **2.ª** (final) | `102f194..56d9562`, diff **completo** desde la base hasta el **último commit de código**, más el delta `7993060..56d9562`, las herramientas corregidas y los docs 00-07 | **APTO.** Código sin hallazgos y diff productivo vacío. M-1 (medio, docs): faltaba citar el esencial `test_presentacion_resultados::test_exportable_diferencia_recomendado_evaluado_y_limite_operativo`, que fija 4 lecturas históricas del CSV y **refuerza** el NO-GO de AS-004. Bajos: B-1 (cifra del encabezado), B-2 (doc 02 desfasado), B-3 (dos textos del CSV 03), B-4 (estado del CI en el 07). Info: I-1 (causa del salto de línea del PDF), I-2 (línea suelta en un archivo de hashes), I-3 (nombre de la sección del Golden). Verifica como correctos los 18 ids, el Golden, la sesión heredada, el oráculo y el CSV 03, que regeneró **byte a byte** | **Código APROBADO. Docs y evidencias aprobados con condiciones**: 1) efecto «plantilla 0→''» aplicado también a `horizontes_evaluados`; 2) claves sin inyectar en la sesión heredada; 3) efecto «ver lector» sin resolver; 4) la comparación del encabezado fallaba porque `_encabezado` recorta el texto; 5) doc 02 desfasado; 6-10 bajos/info (subclave de `trazabilidad`, valor por defecto del `.get`, precisión del doc 04, duplicaciones en las herramientas, comando de 56d9562 sin versionar) |

## 2. Hallazgos y resolución

| Id | Severidad | Hallazgo | Nuevo o preexistente | Evidencia propia | Resolución |
|---|---|---|---|---|---|
| P1-corr B-1 | Bajo | La lápida remite al doc 02, que no estaba versionado | Nuevo | — | **Resuelto** en el commit documental |
| P1-corr B-2 / P1-cal M2 | Bajo / Medio | Nombre de test partido en dos líneas; faltaba citar el contrato vigente; jerga | Nuevo | `grep` del nombre completo | **Resuelto** en `56d9562` (solo comentarios) |
| P1-cal A1 / P2-corr B-3 | Alto | Falsos positivos en el CSV 03 | Nuevo (evidencia) | 7 filas revisadas a mano | **Resuelto:** filtro reproducible por **receptor** obtenido por AST, lista de descartes emitida (101 lecturas) y la subclave de `trazabilidad` también en descartes. El texto «alcanzable solo desde inalcanzable» se corrigió |
| P1-cal A2 / P2-cal 1, 3, 7 | Alto / Medio | Efectos sobreafirmados, mal aplicados o sin resolver | Nuevo (evidencia) | Valores medidos en la sonda | **Resuelto:** columnas separadas (resultados nuevos, sesión heredada, efecto 2D-1 y efecto AS-004), con el efecto **calculado a partir de lo medido**. Lectores internos: «ninguno», con su motivo. Se exige expresamente el valor por defecto del `.get` |
| P1-cal M3 / P2-cal 2, 4 / P2-corr B-1 | Medio | La sonda solo usaba h=12, la UI se reimplementaba, faltaban claves inyectadas y el encabezado no se encontraba | Nuevo (evidencia) | Reproducido en `historia_insuficiente_20` | **Resuelto:** 7 series × h ∈ {1, 12, 18, 24} más la sesión heredada con todas las claves que lee el CSV; el encabezado se **observa** en el HTML, comparando por prefijo. Resultado: 28/28 con `razon_principal` y la sesión heredada con `mensaje_ui` |
| P1-cal M4 / P2-cal 9 | Medio / Bajo | Fragilidad y duplicaciones en las herramientas | Nuevo (evidencia) | — | **Resuelto:** `assert` de return único, raíz `102f194` comprobada por AST, SHA del script registrado, un solo bucle de clasificación y variable muerta eliminada. **No se resuelve** la copia manual de `COLS_CSV`/`COLUMNA_CSV` (bajo; registrada) |
| P1-cal M1 | Medio | Conservar `_evaluacion_horizonte` deja código muerto | Nuevo | — | **No se aplica:** alcance estricto pedido por el propietario. Revisor de corrección: «decisión correcta» (I-1). Candidato a retiro en 2D-1 (09) |
| P2-corr M-1 | Medio | Faltaba citar el esencial que fija 4 lecturas del CSV | Preexistente (prueba) / Nuevo (docs) | `tests/test_presentacion_resultados.py:436-458` | **Resuelto:** citado en 04 (§2.2, §4 y §5), 05 §5, 09 §2 y en el efecto del CSV 03 para sus 4 claves |
| P2-corr B-2 / P2-cal 5 | Bajo / Medio | Doc 02 desfasado | Nuevo (docs) | — | **Resuelto:** fila de `56d9562`, +9/−63 y recuentos medidos |
| P2-corr B-4 | Bajo | Estado del CI en el 07 | Nuevo (docs) | — | **Resuelto** con el resultado del intento 2 (07 §6 y 10) |
| P2-corr I-1 / I-2 / I-3 | Info | Causa del salto de línea (`uuid4().hex`, ancho renderizado), línea suelta en los hashes y nombre de la sección del Golden | — | — | **Resueltos** en 07 §3.1, `evidencia/oraculo/sha256_capturas.txt` y 04 §2.2 |
| P2-cal 8 | Bajo | El 04 mezclaba «eliminar la columna» con «dejar de leer» | Nuevo (docs) | — | **Resuelto:** dos filas separadas en 04 §4 |
| P2-cal 10 | Info | Las evidencias de `56d9562` no tenían comando versionado | Nuevo | — | **Resuelto:** `evidencia/scripts/medir_56d9562.sh` |
| P1-cal B5 | Bajo | Cada fase añade una rama al workflow y una excepción a `.gitignore` | Preexistente | — | Fuera de alcance; propuesta futura |
| P2-corr (nota) | Info | `*.log` en `.gitignore` deja fuera los 4 logs del oráculo | — | — | Se añaden con `git add -f` para que la evidencia esté completa |
| — | — | P0-C / IC95 | No aparece | — | Fuera de alcance; P0-C sigue cancelado |

**Criterio de cierre:** no queda abierto ningún hallazgo crítico, alto ni medio **nuevo y confirmado** del diff. Ningún hallazgo exige cambiar metodología ni producción. Las dos pasadas cubren el último commit de código, `56d9562`.
