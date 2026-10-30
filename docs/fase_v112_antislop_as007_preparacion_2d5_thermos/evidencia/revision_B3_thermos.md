# Thermos B, tercera pasada · delta c656e19..da04725 (solo `tests/test_as007_contratos_r3_vigentes.py`)

**Invocación.** Usé la skill `thermos:thermos` (Thermos 1.1.0) para lanzar en paralelo, en segundo plano, `thermos:thermo-nuclear-reviewer` y `thermos:thermo-nuclear-code-quality-reviewer`. Les pasé `diff_B3_delta.patch` y `diff_B3_codigo.patch` (`6ac158d...da04725`). Claude Code 2.1.238. Ambos trabajaron en solo lectura.

## thermo-nuclear-reviewer

**Hallazgos críticos, altos y medios:** ninguno. **Defectos nuevos introducidos por el delta:** ninguno.

Ejecutó el archivo y pasaron las 9 pruebas. Tardó 66 s porque el perfil esencial corría a la vez en el mismo equipo; sin carga tarda unos 11 s.

Lo que confirmó:
- El `replace` sobre `ConfiguracionInforme` es correcto. La clase es una dataclass sin `frozen`; `frozenset | set` sigue devolviendo un `frozenset`.
- El anexo se genera de verdad (`contenido.py:1329-1357, 1457-1458`), y ninguno de sus encabezados coincide con los prohibidos. Eso respalda no haber aplicado BAJO-5.
- El extractor es una copia fiel del canónico, ampliada con portada y pie.
- El renombre de C1 y los docstrings están bien acotados.

| Severidad | Hallazgo | Estado |
|---|---|---|
| BAJO-1 | El docstring de `_texto_informe` dice «todo el texto que dibuja el informe», pero `pdf_render` también dibuja constantes: cabecera, fecha, «Página N», «Contenido» y firmas. Impacto nulo | **Resuelto**: el docstring pasa a decir «todo el texto de contenido» |
| Nota (hipótesis) | Los 66 s se deben a arranque en frío y a la carga del equipo | Explicado: en las mediciones sin carga tarda unos 11 s |

## thermo-nuclear-code-quality-reviewer

**Veredicto: aprobado.** El delta cumple la condición de B2: N1 y N2 quedan resueltos en el código y N3 en las docs. N4, BAJO-1 y BAJO-4 quedan cerrados.

| Severidad | Hallazgo | Estado |
|---|---|---|
| BAJO 1 | El conjunto de encabezados prohibidos no estaba normalizado como el renderizador, que en el anexo aplica `c.replace("_", " ")`. Por eso no se detectaban «error escalado abs» ni «escala naive insample» | **Resuelto**: el conjunto incluye ahora cada columna en minúsculas, con «_» y con espacios. La mutación `anexo_escalado` se detecta |
| BAJO 2 | El extractor está duplicado respecto al canónico. Es una deuda aceptada y declarada | Diferido: mover el extractor a un helper compartido cuando se trate `test_informes_rediseno` |
| NIT 3 | Nada exigía que el anexo trajera la tabla por ventana, así que la comprobación podía quedar vacía | **Resuelto**: C6 exige `seccion.clave == "anexos"` con el encabezado «Origen» |
| NIT 4 | `informe.pie or ""` sobra | Sin cambio; es cosmético |
