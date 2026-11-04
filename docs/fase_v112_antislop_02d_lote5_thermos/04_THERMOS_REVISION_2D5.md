# 04 · Revisión Thermos del lote 2D-5

## Plugin e invocación

| Dato | Valor |
|---|---|
| Plugin | `thermos@thermos-claude-plugin` **1.1.0**, alcance usuario, `✔ enabled`. Ya estaba instalado y no se reinstaló |
| Claude Code | 2.1.238. No se usa `--effort` |
| Invocación | Skill `thermos:thermos`. En cada pasada lanza **en paralelo y en segundo plano** los dos agentes del plugin: `thermos:thermo-nuclear-reviewer` (corrección, regresiones y seguridad) y `thermos:thermo-nuclear-code-quality-reviewer` (mantenibilidad, acoplamiento y modularidad) |
| Entrada | El diff de código contra la base **AS-007 `dfcaaa9`**, sin docs ni archivos generados, guardado en un `.patch` fuera del repositorio. Además, los archivos modificados completos. No se comparó contra `main` ni contra ninguna rama P0-C |
| Modo | Solo lectura. Como mucho se ejecutó `pytest` de los dos archivos de prueba modificados |

Thermos revisa el diff, no la arquitectura completa del producto. **No sustituye** al grafo G1, la huella exacta ni las pruebas.

## Pasadas

| Pasada | Diff | Corrección | Calidad |
|---|---|---|---|
| 1.ª | `dfcaaa9...a056d9f` | **Sin hallazgos críticos, altos ni medios.** 2 bajos nuevos (B1: el corte 3 queda sin ancla; B2: comentarios de r3 y `test_as007`), 1 bajo preexistente y 1 informativo preexistente | «Aprobado con observaciones menores»: 3 bajos nuevos, 1 falso positivo y 2 preexistentes o fuera de alcance |
| 2.ª | `dfcaaa9...1c8c952` | **Sin hallazgos críticos, altos ni medios.** El cuerpo de `_texto_evidencia_oos` es idéntico al de la base (SHA-256 `28a68a34…cbaa`, extraído con `ast`). 2 nits | «Aprobado con observaciones menores»: 2 bajos nuevos de esa pasada |
| 3.ª | `dfcaaa9...cae9f04` (delta `1c8c952..cae9f04`) | **Sin hallazgos de ninguna severidad** | **«APROBADO»**, sin deuda nueva |

Las salidas de cada agente, condensadas sin alterar los hallazgos, están en [`evidencia/thermos_pasadas.md`](evidencia/thermos_pasadas.md).

## Hallazgos y clasificación

| Hallazgo | Agente | Clasificación | Verificación propia | Estado |
|---|---|---|---|---|
| B1: al retirar PS-03, el corte literal 3 deja de estar anclado | Corrección (1.ª) | Nuevo por el diff | Confirmado | **Resuelto**: `assert MIN_ITERACIONES_WF_ESCENARIO == 3` con mensaje. Las mutaciones a 2 y a 4 se detectan |
| «Sustituiría» en condicional; ids partidos; línea de 167 columnas | Calidad (1.ª y 2.ª), corrección (2.ª) | Nuevo por el diff | Confirmado | **Resuelto** |
| Lápida de PS-03 demasiado larga, con valores de W escritos a mano | Calidad (1.ª) | Nuevo por el diff | Confirmado | **Resuelto**: dos líneas con el id completo |
| Redacción del docstring trasladado | Calidad (1.ª) | Arrastrado | — | **Resuelto**: «El corte (`MIN_ITERACIONES_WF_ESCENARIO`, hoy 3)…», «reintroduciría» |
| Ancla con literales duplicados | Calidad (2.ª) | Nuevo, de esa pasada | Confirmado | **Resuelto** |
| `tramo_evidencia_oos` sigue en la tupla `HEREDADAS` | Calidad (1.ª) | **Falso positivo** | La lista no exige que el nombre exista, ya contiene otros 6 nombres retirados y sirve de barrera contra su reintroducción | Sin cambio |
| Comentarios de r3 (`:513-514`) y de `test_as007` (`:14`) que nombran la función retirada | Ambos (1.ª) | Consecuencia del diff, en archivos no tocados | Confirmado | **Pendiente, fuera de alcance**: el prompt prohíbe cambiar r3 y limita el diff de pruebas a dos archivos |
| La columna CSV `tramo_evidencia_oos_horizonte_solicitado` siempre sale vacía; HG4 de r3 la espera | Ambos (1.ª) | **Preexistente, fuera de alcance** | Confirmado: nadie produce esa clave, ni en la base ni ahora | Pendiente (05 §4) |
| `_texto_evidencia_oos` solo se llama con 0 en la ruta vigente; las otras ramas dependen de `_clasificar_evidencia_horizonte` (2D-3) | Corrección (1.ª) | **Preexistente, informativo** | — | Registrado para 2D-3 |
| Cifra «(6)» de `MIN_ITERACIONES_WF` en prosa, sin ancla | Calidad (3.ª) | Preexistente, documental | — | Sin cambio |
| Reconstrucción del IC95 desde métricas publicadas (P0-C) | — | **Preexistente, fuera de alcance**. No aparece en este diff | — | **No se interviene.** La corrección P0-C está cancelada |

**Criterio:** ningún defecto nuevo crítico, alto o medio confirmado por Thermos queda abierto en el código cambiado. **Se cumple.** Todos los cambios posteriores a cada pasada se revisaron en la pasada siguiente; la 3.ª cubre el HEAD de código `cae9f04`.
