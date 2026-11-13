# 07 · Thermos: dos pasadas reales con los dos agentes (G7)

| Dato | Valor |
|---|---|
| Plugin | `thermos@thermos-claude-plugin` 1.1.0, ya instalado (commit `dc8791f8`). Claude Code 2.1.238, sin `--effort` |
| Agentes | `thermos:thermo-nuclear-reviewer` (corrección, regresiones, seguridad de la eliminación y contratos) y `thermos:thermo-nuclear-code-quality-reviewer` (arquitectura, deuda, claridad de pruebas y mantenibilidad). Se lanzaron en paralelo y en segundo plano, con la skill `thermos:thermos` |
| Entrada | `diff_pasada{1,2}.patch` = `git diff 8e5a62b 406e1dd`, fuera del repositorio. Contexto escrito (`evidencia/thermos/contexto_pasada{1,2}.md`): la original empaquetada, AS-001, las prohibiciones de AS-004, P0-C, 2D-3 y `_evaluacion_horizonte`, la matriz 02 y la evidencia G0/G5. Además, el clon, las copias y las herramientas |
| Modo | Solo lectura. Los agentes hicieron `git archive` a sus temporales, comparaciones AST propias, `git grep`, ejecución de `pytest` y lectura de los JSON del oráculo |

> Thermos revisa; no sustituye a las pruebas, al oráculo ni al CI (04, 06), ni autoriza cambios.

## 1. Pasadas

| Pasada | SHA | Corrección | Calidad |
|---|---|---|---|
| **1.ª**, tras el retiro atómico | `8e5a62b..406e1dd` | **APROBADO.** Ningún hallazgo crítico, alto ni medio. Verificó por su cuenta: solo se borran las 6 definiciones y el resto es idéntico en AST; no quedan referencias ni accesos dinámicos; no hay imports huérfanos; 92 pasan y 1 falla (el preexistente) en sus ejecuciones; las lápidas citan contratos existentes. Bajo: el docstring de la histórica de la cascada. Info: C-ALC-002, comentarios de producción, el auxiliar sin uso y el doc 02 todavía sin versionar | **APROBADO, con deuda registrada.** Solo borra código y el archivo baja de 5 744 a 5 312 líneas. Medios (deuda **fuera de alcance**, no cambios a hacer): `_evaluacion_horizonte_ui` sin uso y C-ALC-002 apuntando a un símbolo inexistente. Bajos: docstring de la histórica, comentarios de producción, el import sin uso preexistente y el nombre `retirados` |
| **2.ª** (final), sobre el **último commit de código** | `8e5a62b..406e1dd`. No hubo commits de corrección: ninguna pasada exigió cambios dentro del alcance | **APROBADO.** Recomprobó el AST (144 definiciones y sentencias idénticas), el oráculo (`8e5a62b_r1` y `406e1dd_r1` son idénticos salvo el bloque `meta`; r1 = r2; frente a la original solo AS-001, más el salto de línea del PDF que la original varía), el script 26/26 por id, la bisección segura de los commits y que las sesiones no pueden depender de las funciones (sin pickle ni acceso dinámico). Bajo: la guarda de la Fase 1A solo exige la ausencia del nombre público. Info: el doc 02 debe versionarse | **APROBADO.** Ningún hallazgo crítico, alto ni medio, y sin deriva de alcance. Recomprobó el AST, el oráculo y las cifras de los docs 00-03. Solo bajos e informativos, ya registrados, más uno nuevo: la tupla `HEREDADAS` |

## 2. Hallazgos y destino

| Id | Severidad | Hallazgo | Archivo y línea | Verificación propia | Destino |
|---|---|---|---|---|---|
| C1-B1 / Q1-B3 / Q2-2 | Bajo | El nombre y el docstring de la histórica hablan de «dos máximos» | `tests/test_cierre_metodologico.py` L444-476 | El comentario de L473-475 lo explica; la prueba sigue en PASS (21/1) | **Documentado fuera de alcance** (08): §3.4 autoriza retirar solo la aserción |
| Q1-M1 / C1-I4 / Q2-6 | Medio (calidad) / Info | `_evaluacion_horizonte_ui` sin uso | `tests/test_presentacion_resultados.py` L462-507 | `grep`: sin llamadas | **Documentado fuera de alcance** (08). El propietario no autoriza limpiar auxiliares |
| Q1-M2 / C1-I2 / C2-I / Q2-5 | Medio (calidad) / Info | C-ALC-002 apunta a `_mayor_horizonte_con`, que ya no existe | `app_icociv/estadistica/criterios.py` L639 | Ningún código ni prueba resuelve la ruta | **Documentado fuera de alcance**: deuda AS-024 con propuesta concreta (08) |
| Q1-B4 / C1-I3 / Q2-4 | Bajo / Info | Comentarios de producción que citan la función retirada | `analisis_series.py` L713 y L797; `presentacion_resultados.py` L1333 | Solo comentarios | **Documentado fuera de alcance** (08, 2D-6/AS-024) |
| Q1-B5 / Q2-6 | Bajo | Import sin uso de `_lineas_determinacion_horizonte` | `tests/test_resultado_horizonte_solicitado.py` L17 | Ya existía en la base | **Documentado fuera de alcance** (AS-004, 08) |
| Q1-B6 / Q2-3 | Bajo | El nombre `retirados` agrupa símbolos todavía definidos | `tests/test_fase1a_selector_rectangular.py` L306-307 | La guarda es correcta | **Documentado** (08, 2D-3) |
| C2-B | Bajo | La guarda de ausencia no cubre los 5 auxiliares privados | `tests/test_fase1a_selector_rectangular.py` L301-304 | Tras el retiro no queda ninguna referencia (AST y `grep`) | **Documentado fuera de alcance**: §3.3 autoriza mover exactamente un nombre (08) |
| Q2-7 | Info | La tupla `HEREDADAS` nombra las seis como texto | `tests/test_fase2c_contratos_vigentes.py` L32-34 | No exige ni existencia ni ausencia | **Documentado fuera de alcance**: §3.6 (08) |
| C1-I5 / C2-I | Info | El doc 02 que citan las lápidas aún no estaba versionado | Carpeta de docs | `.gitignore` tiene la excepción | **Corregido** en el commit documental |
| Q2-8 | Info | Lápidas de 11 y 14 líneas | Archivos de prueba | Siguen la convención | Sin acción |
| — | — | P0-C / IC95 | — | No aparece | Fuera de alcance |

**Criterio de cierre:** no queda abierto ningún hallazgo crítico, alto ni medio **del diff** que deba resolverse dentro del alcance. Los dos «medios» de calidad son deudas ajenas a las seis definiciones, cuya corrección el propietario no ha autorizado. Ningún hallazgo exige cambiar resultados ni producción. Thermos «aprobado» **no sustituye** a la equivalencia numérica, las pruebas ni el CI.
