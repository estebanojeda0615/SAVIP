# 07 · G5: revisiones Thermos

## Plugin e invocación

| Dato | Valor |
|---|---|
| Plugin | `thermos@thermos-claude-plugin` **1.1.0**, alcance usuario. Verificado con `claude plugin list` y no reinstalado |
| Claude Code | 2.1.238, sin `--effort` |
| Invocación | Skill `thermos:thermos`. En cada pasada lanza en paralelo y en segundo plano los dos agentes: `thermos:thermo-nuclear-reviewer` y `thermos:thermo-nuclear-code-quality-reviewer` |
| Entrada | El diff exacto de código, sin docs, contra **`54789587…`** (la rama anterior), guardado en un `.patch` fuera del repositorio, más los archivos completos |
| Contexto que recibieron los agentes | La referencia es la V1.1.2 original. Se exige igualdad exacta salvo AS-001. No se puede tocar el motor, el golden ni P0-C. Además: resultados de G0/G1 (oráculo 65/66 con el caso AS-001), grafo y espías, matriz de pruebas, cuentas 811→809 y 242→214, y los fallos preexistentes |
| Modo | Solo lectura. Los agentes ejecutaron `pytest`, `pyflakes`, `git grep`, `git archive` y mutaciones en memoria; no editaron nada |

> **Thermos solo revisa diffs.** No sustituye la prueba contra la V1.1.2 original (oráculo, golden exacto, huella y perfiles: 01, 05 y 06).

## Pasadas

| Pasada | Diff (SHA revisados) | Corrección | Calidad |
|---|---|---|---|
| 1.ª | `54789587d0fa…...55ba5646faad…` | **Sin hallazgos críticos, altos ni medios.** B-1 (nuevo): `__main__` borrado entero. I-1 (preexistente): 3 FAIL en test_horizonte. I-2 e I-3, informativos | «APROBADO CON OBSERVACIONES». M1: helper P0-D duplicado. M2: inspecciones de fuente redirigidas. M3: lápidas largas. B1 a B3 |
| 2.ª | `54789587d0fa…...49106f95bacd…` (delta `55ba564..49106f9`) | **Sin hallazgos nuevos de corrección.** Capacidad de detección del helper idéntica; sin ciclo de importación; ids esenciales: solo faltan los 2 autorizados | **«APROBADO»**. Pide registrar el solape de guardias cierre/seleccion (D-2D2-1) y confirmar que el doc 03 entra en la rama |

La 2.ª pasada cubre el **último commit de código** (`49106f95`).

Las salidas de ambos agentes, transcritas sin eliminar hallazgos, están en [`evidencia/thermos_pasadas.md`](evidencia/thermos_pasadas.md).

## Hallazgos y clasificación

| Hallazgo | Severidad | Agente | Nuevo / preexistente / falso positivo | Verificación propia | Estado |
|---|---|---|---|---|---|
| `__main__` de `test_horizonte_evidencia_reducida` borrado entero | Bajo | Ambos (1.ª) | Nuevo | Confirmado: mi corte llegaba hasta el final del archivo | **Resuelto** en `49106f9`, con las 8 llamadas restantes |
| `p0d_en_el_selector_vigente` duplicaba datos y constructor de Fase 1A | Medio | Calidad (1.ª) | Nuevo | Confirmado | **Resuelto**: compone 3 propiedades canónicas de Fase 1A. La mutación se sigue detectando |
| Lápidas largas con mapeo repetido | Medio | Calidad (1.ª) | Nuevo | Confirmado | **Resuelto**: 3-4 líneas, con puntero a Fase 1A y a 03 (ruta completa) |
| Restos documentales: encabezados, docstring D1-D12, banners, tupla de un elemento, «una ULP» | Bajo | Ambos (1.ª) | Nuevo | Confirmado | **Resuelto** |
| Inspecciones de fuente redirigidas: D12 cambia de semántica; `assert "rmse"` | Medio (1.ª), rebajado en la 2.ª | Calidad | Nuevo por la redirección | La 2.ª pasada corrige su propio diagnóstico: `"rmse"` también lo satisface el código. D12 conserva su intención | **Diferido**. Se conservan los ids |
| Solape de las guardias `test_cierre…:413-417` ⊂ `test_seleccion…:52-57` | Bajo, no bloqueante | Calidad (2.ª) | Nuevo, introducido por el lote | Confirmado | **Deuda registrada D-2D2-1** (08 §4) |
| La ejecución directa de nmin y fhg necesita pytest | Informativo | Corrección (2.ª) | Nuevo | Confirmado. Ningún docstring promete lo contrario y el venv lo trae | Aceptado |
| Doc 03 citado y aún no versionado | Informativo | Ambos (2.ª) | Nuevo | — | **Resuelto**: entra en el commit documental de esta rama |
| 6 FAIL históricos en los archivos tocados | — | Corrección | **Preexistente** | Confirmado en la fuente 5478958 | Registrado (06) |
| Imports sin uso y variables muertas en `servicio_proyeccion` y en pruebas; docstring de `_puntaje_rmse_ponderado` | — | Ambos | **Preexistente** | Confirmado (pyflakes y AST frente a la base) | Fuera de alcance (08 §4) |
| Fichas de criterios con rutas sin `::` o con tildes (AS-024) | — | Calidad | **Preexistente** | — | Fuera de alcance |
| P0-C / IC95 | — | — | Preexistente; no aparece en el diff | — | **Fuera de alcance.** P0-C sigue cancelado |

No hubo falsos positivos que resolver: todos los hallazgos nuevos se confirmaron.

**Criterio:** no queda abierto ningún hallazgo crítico, alto ni medio confirmado del propio diff. **Se cumple.** El medio que queda (M2) se rebajó en la 2.ª pasada y está diferido de forma explícita: no afecta a resultados ni a ids.
