# 05 · Revisión Thermos

## Plugin e invocación

| Dato | Valor |
|---|---|
| Plugin | `thermos@thermos-claude-plugin` **1.1.0**, alcance usuario. Verificado con `claude plugin list` y no reinstalado |
| Claude Code | 2.1.238, sin `--effort` |
| Invocación | Skill `thermos:thermos`. En cada pasada lanza **en paralelo y en segundo plano** los dos agentes del plugin: `thermos:thermo-nuclear-reviewer`, para corrección, regresiones, seguridad y daños por retirada, y `thermos:thermo-nuclear-code-quality-reviewer`, para límites modulares, duplicación de pruebas, claridad y deuda transferida |
| Entrada | El diff exacto contra **`56c75a6`**, guardado en un `.patch` fuera del repositorio, más los archivos completos |
| Contexto que reciben los agentes | No tocar producción ni P0-C; los 30 tests y su resultado 22/8; las cuatro dependencias; 2D-1 frente a 2D-2; el JUnit de la base; la cobertura de Fase 1A; el inventario |
| Modo | Solo lectura. Los agentes solo ejecutaron `pytest` y `pyflakes` |

Thermos revisa el diff. **No sustituye** a la huella, los golden ni las pruebas.

## Pasadas

| Pasada | Diff | Corrección | Calidad |
|---|---|---|---|
| 1.ª | `56c75a6...0929b29` | **Sin hallazgos críticos, altos ni medios.** 1 bajo nuevo (la lápida remite a «…/03», inexistente) y 3 informativos preexistentes. Ejecutó el script: 21/8 con los mismos 8 fallos | «APROBADO con observaciones». **2 medios nuevos**: M1 (la referencia al 03) y M2 (la lápida nombra el símbolo heredado). 1 bajo nuevo (longitud), 2 bajos preexistentes y 1 observación (falta la ejecución posterior del script) |
| 2.ª | `56c75a6...5acb09f` | **Sin hallazgos de ninguna severidad.** Confirma las tres correcciones y la hermeticidad. Script más Fase 1A: 56 PASS / 8 FAIL, con los 8 históricos | **«APROBADO»**, con dos condiciones de cierre que no afectan al código: que el 03 llegue junto a la lápida y que se guarde la ejecución final del script |

Las salidas de cada agente, condensadas sin alterar los hallazgos, están en [`evidencia/thermos_pasadas.md`](evidencia/thermos_pasadas.md).

## Hallazgos y clasificación

| Hallazgo | Archivo:línea | Severidad | Agente | Confirmación propia | Estado |
|---|---|---|---|---|---|
| La lápida cita «docs/…/03», que no existe y no es una ruta | `pruebas/prueba_horizonte_dinamico_ui_reportes.py:282` (en `0929b29`) | Medio (calidad) / bajo (corrección) | Ambos (1.ª) | Confirmado | **Resuelto en `5acb09f`**: ruta completa `03_CAMBIOS_Y_MIGRACIONES.md`, que sube en el HEAD documental |
| La lápida vuelve a escribir en el script el nombre del símbolo que 2D-2 tiene que borrar | `:280` (en `0929b29`) | Medio | Calidad (1.ª) | Confirmado: era la única coincidencia en `pruebas/` | **Resuelto en `5acb09f`**: «selector heredado de C-SEL-001». `grep` del par en el script da 0 |
| Cuatro líneas de lápida repiten el commit y el inventario | `:279-282` | Bajo | Calidad (1.ª) | Confirmado | **Resuelto**: 3 líneas |
| Falta la ejecución posterior del script como evidencia | — | Observación | Calidad (1.ª) | Confirmado | **Resuelto**: `evidencia/script_final_pytest.xml` |
| El mensaje de `0929b29` dice «el único test atado al selector heredado» | commit `0929b29` | Informativo | Corrección (1.ª) | Correcto para el script, no para el repositorio | Aclarado en 03 §2. No se reescribe el historial |
| `main()` es un registro manual que aborta en el primer FAIL | `:950-980` | Bajo, **preexistente** | Calidad | — | Deuda del saneamiento posterior del script (07 §4) |
| Las listas del workflow y de `.gitignore` crecen una línea por fase | `fase0-pruebas.yml:9-18`, `.gitignore:111-120` | Bajo, **preexistente** | Calidad | — | Se mantiene el patrón de fases previas. Cambiarlo a un glob requiere autorización (prompt §11) |
| Otras pruebas históricas atadas al selector, entre ellas un gemelo del test retirado en `test_horizonte_evidencia_reducida.py:375-389` | varios | Informativo, **preexistente** | Corrección | Confirmado | Registrado como bloqueo de 2D-2 (02 §2 y 06 §2) |
| El docstring retirado decía que ganaba `exponencial_log_lineal` | — | Informativo, preexistente | Corrección | Confirmado (sondeo G3: hoy gana `drift`) | Desaparece con el retiro |
| P0-C / IC95 | — | — | — | No aparece en el diff | **Fuera de alcance.** P0-C sigue cancelado |

**Criterio:** ningún hallazgo nuevo crítico, alto o medio confirmado por Thermos queda abierto en el código cambiado. **Se cumple.** Los dos medios se corrigieron en `5acb09f` y la 2.ª pasada, que cubre el HEAD de código, los da por resueltos.
