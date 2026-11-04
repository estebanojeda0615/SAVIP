# Thermos · lote 2D-5: salidas de la 1.ª y la 2.ª pasada

Invocación: skill `thermos:thermos` (Thermos 1.1.0, Claude Code 2.1.238), que lanza en paralelo y en segundo plano los agentes `thermos:thermo-nuclear-reviewer` y `thermos:thermo-nuclear-code-quality-reviewer`. Cada agente recibe el diff de código contra la base AS-007 `dfcaaa9`, sin docs, guardado en un `.patch` fuera del repositorio, y lee completos los archivos modificados.

Las dos revisiones son solo de lectura. Lo que sigue condensa la salida de cada agente sin alterar sus hallazgos.

## 1.ª pasada · `dfcaaa9...a056d9f`

### thermo-nuclear-reviewer (corrección, regresiones y seguridad)

**No hay hallazgos críticos, altos ni medios.** El revisor ejecutó `pytest` sobre los dos archivos de prueba modificados: 18 passed (11 + 7). La base tenía 19, así que solo se retiró un id.

Lo que comprobó:
- **Consumidores restantes: ninguno.** Usó `git grep` en HEAD y en la base sobre `app_icociv`, `pruebas/`, `scripts/`, `packaging/`, el `.spec`, los fixtures y los golden. No hay `__all__`, reexportación en `__init__`, `getattr` ni `patch`. Lo que queda es solo texto: la tupla `HEREDADAS` (que no exige que el nombre exista), varios docstrings y comentarios, y la lápida.
- **Clave `tramo_evidencia_oos_horizonte_solicitado`:** es otro nombre y el diff no la toca.
- **`_texto_evidencia_oos`:** el cuerpo es idéntico byte a byte. `ventanas_oos_disponibles` no se toca, y `Any` y `MIN_ITERACIONES_WF_ESCENARIO` siguen en uso. Pasar los comentarios `#:` a docstring no afecta a ninguna prueba que lea la fuente.
- **Cobertura:** el test de 2C es un superconjunto del retirado. `test_escasez_…[36|37|41]` y `test_ps03_w_es_cero…` siguen vigentes. No se añaden ids. El perfil selecciona por archivo y no hay ningún `--deselect` del id retirado.

| Sev. | Hallazgo | Clasificación |
|---|---|---|
| Bajo B1 | Al retirar PS-03, el corte literal 3 deja de estar anclado en el perfil esencial | Nuevo por el diff |
| Bajo B2 | Comentarios de r3 (`:513-514`) y de `test_as007` (`:14`) que mencionan la función retirada | Nuevo, consecuencia indirecta: los archivos no se tocan |
| Bajo P1 | La columna CSV `tramo_evidencia_oos_horizonte_solicitado` sale siempre vacía (`generador_reportes.py:381`) | Preexistente, fuera de alcance |
| Info P2 | En la ruta vigente, `_texto_evidencia_oos` solo se llama con 0; las otras ramas dependen de `_clasificar_evidencia_horizonte` (heredada) | Preexistente, fuera de alcance |

**P0-C:** no aparece en el diff; se trata como preexistente y fuera de alcance.

### thermo-nuclear-code-quality-reviewer (calidad)

**Veredicto:** «Aprobado, con observaciones menores no bloqueantes». El lote borra código, no añade ramas ni capas, y la regla de vocabulario queda junto a la función que la aplica.

| Sev. | Hallazgo | Clasificación |
|---|---|---|
| Bajo 1 | «Sustituiría» en condicional en los docstrings de 2C, cuando la sustitución ya se hizo | Nuevo por el diff |
| Bajo 2 | La lápida de PS-03 duplica la trazabilidad y repite a mano los valores de W | Nuevo por el diff |
| Bajo 3 | Redacción del docstring trasladado: «volvería a reintroducir», y el número 3 fijado en el texto | Texto arrastrado de antes |
| Falso positivo 4 | `tramo_evidencia_oos` en `HEREDADAS` | Coherente con la política existente: hay otros 6 nombres retirados en la misma lista |
| Bajo 5 | Comentarios de r3 y `test_as007` que nombran la función retirada | Preexistente en archivos no tocados |
| Fuera de alcance 6 | Columna CSV y aserción HG4 de r3 sobre una clave que nadie escribe | Preexistente |
| Sin observación 7 | W=10 añadido | Correcto |

**Tratamiento** (commit `1c8c952`):
- B1: se anclan los literales 2 y 3 en el mismo test.
- Calidad 1, 2 y 3: corregidos.
- B2, calidad 5, P1 y P2: **no se tocan**. El prompt prohíbe cambiar r3 y limita el diff de pruebas a los dos archivos autorizados. Quedan registrados como pendientes.

## 2.ª pasada · `dfcaaa9...1c8c952`

### thermo-nuclear-reviewer

**No hay hallazgos críticos, altos ni medios.**
- Las correcciones solo amplían las aserciones y no añaden ids: `--collect-only` da 18.
- El corte queda anclado por ambos lados: con 4 fallaría `textos[3]` y con 2 fallaría `textos[2]`.
- No hay consumidores en el código.
- **El cuerpo de `_texto_evidencia_oos` es idéntico al de la base:** extraído con `ast` y comparado con `cmp`, mismo SHA-256 `28a68a34…cbaa`.

| Sev. | Hallazgo | Clasificación |
|---|---|---|
| Bajo N1 | `test_fase2c_contratos_vigentes.py:69` tiene 167 columnas | Nuevo |
| Bajo N2 | Id de PS-03 partido en dos líneas en los docstrings, de modo que el grep no lo encuentra | Nuevo |

### thermo-nuclear-code-quality-reviewer

**Veredicto:** «aprobado con observaciones menores». Los tres puntos accionables de la 1.ª pasada están resueltos.

| Sev. | Hallazgo | Clasificación |
|---|---|---|
| Bajo 1 | El ancla mezcla dos contratos (simbólico y literal) y repite valores. Remedio: `assert MIN_ITERACIONES_WF_ESCENARIO == 3` con mensaje, y la tupla en forma simbólica | Nuevo, de esa pasada |
| Bajo 2 | Línea de 167 columnas e ids partidos | Nuevo, de esa pasada |

**Tratamiento** (commit `cae9f04`): ancla explícita con mensaje, tupla simbólica con W=10 y cada id completo en su propia línea. Las mutaciones del corte a 2 y a 4 se detectan con ese mensaje. Los dos archivos de prueba dan 18/18.

## 3.ª pasada · delta `1c8c952` → `cae9f04` (diff completo `dfcaaa9...cae9f04`)

**thermo-nuclear-reviewer: sin hallazgos de ninguna severidad.**
- Conserva todas las aserciones de la base y añade W=10. Los literales 2 y 3 desaparecen y en su lugar queda el ancla explícita `assert MIN_ITERACIONES_WF_ESCENARIO == 3`.
- Cubre todo lo que comprobaba la prueba retirada: tramos en W = 0, 1, 2, 3 y 50, y vocabulario en W = 3, 10 y 50.
- No añade ningún id.
- Ejecución: 7/7.

**thermo-nuclear-code-quality-reviewer: «APROBADO».** Los dos hallazgos de la 2.ª pasada quedan cerrados y el delta no introduce deuda.

Queda una observación opcional y preexistente: la cifra «(6)» de `MIN_ITERACIONES_WF` en la prosa de la línea 61 y del docstring de la línea 73 no tiene ningún ancla. Es documental y no se toca.
