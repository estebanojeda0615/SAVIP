# 05 · Resultados de Thermos

## Plugin e invocación

| Dato | Valor |
|---|---|
| Plugin | `thermos@thermos-claude-plugin` **1.1.0**, ámbito usuario, `✔ enabled` según `claude plugin list` |
| Claude Code | 2.1.238. No se usa `--effort` |
| Invocación | Skill `thermos:thermos`, que lanza en paralelo y en segundo plano los agentes `thermos:thermo-nuclear-reviewer` y `thermos:thermo-nuclear-code-quality-reviewer`. Cada uno recibe el diff guardado en un `.patch` fuera del repositorio y el contexto de producción necesario para verificar las afirmaciones |
| Modo | Solo lectura. El revisor de corrección exportó `12319df` con `git archive` a una carpeta temporal para trabajar sobre una copia fija, porque el árbol cambió mientras revisaba |

Thermos revisa el diff, no la arquitectura completa. El análisis matemático del contrato (01) es mío, y Thermos lo comprobó como parte del diff.

## Primera pasada: `dfcaaa9...12319df`

### thermo-nuclear-reviewer (corrección)

**Veredicto:** el NO-GO se sostiene, «con más fuerza de la que el propio informe declara». No hay hallazgos críticos ni altos.

Confirmó en el código:
- la fórmula de la banda;
- la coincidencia estructural de las muestras en h=24;
- B1 y B2;
- que `_retirar_intervalo_de_publicacion` no toca `metricas`;
- que el vector no tiene alias (504 apariciones, sin deduplicar);
- la reproducibilidad de las salidas;
- que la prueba no se recolecta, que el perfil esencial no cambia (82 entradas y 812 pruebas) y que no hay riesgos de seguridad ni de CI.

| Sev. | Hallazgo | Verificación propia | Estado |
|---|---|---|---|
| Medio M1 | **Vía B4** sin documentar: `mae` + `estabilidad_error` dan `sigma` exacta | Confirmado: exacta en los 6 escenarios | **Resuelto.** Añadida a `caso_ic95.vias`, a la caracterización (4 casos) y a 01 y 02 |
| Medio M2 | El detector da falso verde si se quita solo `error_absoluto`: `z_modificado` + mediana + MAD devuelven el vector | Confirmado: vía A', exacta en los 6 | **Resuelto.** `z_modificado` está en el detector, hay una prueba nueva `…retirar_solo_error_absoluto_no_basta` y el detector se declara heurístico, con la caracterización como oráculo semántico |
| Bajo B1 | Sobra la salvedad del calendario: desde P0-F el factor vale siempre 1 y se publica en `factores_por_paso` | Confirmado en `_ajustar_salto_anual` | **Resuelto** en 01 |
| Bajo B2 | B3 fuera de h=24 estaba exagerado | Confirmado | **Resuelto.** Se da el error frente al semiancho (6–13 %) y se califica como «aproximación» |
| Bajo B3 | Faltaban precisiones: el recorte `max(…, 0)`; que la vía A no está siempre disponible (MAD nulo); y que `iteraciones` incluye predicciones no finitas | Confirmado (`backtesting.py:272`) | **Resuelto** en 01 §2, «Condiciones de validez» |
| Bajo B4 | Un agregado NaN pasaba; la prueba de h24 no comprobaba la banda; la prueba «sin extremos» podía elegir una entrada no calculable | Confirmado | **Resuelto.** Se comprueba la finitud, todas las caracterizaciones pasan por `_con_banda` y se filtra por `calculable` |
| Bajo B5 | El espía del diagnóstico no se restauraba | Confirmado | **Resuelto.** El espía está ahora solo en `caso_ic95.proyectar`, con `try/finally` |
| Bajo B6 | Referencias a 04–07 inexistentes y un recorrido de alias no versionado | Confirmado | **Resuelto en el HEAD final.** 04, 05 y 07 se añadieron en `f8c8336` y 06 en el commit documental final. 02 aclara que el recorrido de alias no está versionado y que el revisor lo repitió |

### thermo-nuclear-code-quality-reviewer (calidad)

**Veredicto:** no aprobado tal cual, aunque ningún punto afecta a la conclusión NO-GO, que «está bien sostenida por los números».

| Sev. | Hallazgo | Estado |
|---|---|---|
| Alto 1 | Duplicación entre scripts (series, periodo objetivo, espía, banda) y respecto a los helpers de `tests/` | **Resuelto dentro de la evidencia.** Un único `evidencia/caso_ic95.py` concentra series, escenarios, `proyectar` (con `functools.cache` y espía restaurado), `banda` y `vias`; el diagnóstico se reduce a un bucle. **Diferido fuera de alcance:** unificar con los helpers de `tests/`, porque esta fase no toca `tests/`. Se recomienda al promover la prueba (07 §6) |
| Medio 2 | Docstrings que exageraban: el detector no recorría Series/arrays, no había prueba de B2 y el inventario «reconstruía» bandas sin hacerlo | **Resuelto.** El detector recorre Series y celdas, con casos de prueba; B2 y B4 se prueban; el docstring del inventario dice lo que hace |
| Medio 3 | La guarda NaN fallaba y el `except` estaba mal justificado | **Resuelto.** `proyectar` devuelve `interno=None` si la banda no es finita; se quitó el `except` |
| Medio 4 | La prueba mezclaba contrato, caracterización y detector; las mutaciones solo imprimían | **Resuelto.** Tres grupos con nombres explícitos; las mutaciones son ahora `test_detector_sensibilidad` y las dos «correcciones parciales», con asserts. Se borraron `mutaciones_adversarial.py` y su salida |
| Medio 5 | Reproducibilidad: comandos distintos, salida filtrada, Qt y `sys.path` | **Resuelto.** Un único comando canónico; salida completa sin filtrar; `caso_ic95` fija Qt offscreen y `sys.path`; la huella documenta sus comandos |
| Medio 6 | Referencias a documentos inexistentes | **Resuelto en el HEAD final** (06 se añadió después de la segunda pasada) |
| Bajo 7 | Restos: `factor` sin uso, `CLAVES` copiadas a mano, `.get` sobre `None`, prosa del proceso | **Resuelto.** `CLAVES_POR_VENTANA` se deriva de `sp.COLUMNAS_OOS_RECONSTRUCTIVAS`; el calendario se comprueba con `sin_calendario` |
| Bajo 8 | Configuración que crece una línea por fase | **Diferido.** Lo decide el propietario, como en las fases anteriores |

## Segunda pasada: `dfcaaa9...f8c8336`

### thermo-nuclear-reviewer (corrección)

**Veredicto:** el NO-GO se sostiene. M1, M2 y B1–B5 de la primera pasada quedan resueltos y B6 en parte (faltaba 06). La reestructuración no introduce defectos de corrección. No hay hallazgos críticos ni altos.

Verificó ejecutando:
- el comando canónico;
- que las salidas son idénticas;
- 16 series adicionales, con semillas 1–8 y varios n y h, en las que A, A', B1, B2 y B4 dan `==`;
- que `len(observaciones) == iteraciones == errores_extremos.n` en todas las entradas;
- las fórmulas de `vias`;
- que la caché no se muta, que el espía se restaura y que el import funciona con pytest en modo `prepend`.

| Sev. | Hallazgo | Verificación propia | Estado |
|---|---|---|---|
| Medio 1 | **Vía textual B5**: `backtesting_comparativo[*].interpretacion` publica «RMSE=x.xxx». Con `iteraciones` da la banda casi exacta en todos los horizontes. 07 §3 B la omitía | Confirmado: 0,004–0,05 % del semiancho en los 6 escenarios | **Resuelto.** Vía B5 en `vias`, caracterización con la cota deducida del formato, fila en 02, 01 §3 y 07 §3 B |
| Bajo 1 | El `==` del oráculo es frágil en B2/B4/A', porque la `sigma` difiere en un ULP | Confirmado | **Resuelto.** `==` solo en A y B1; `rel_tol=1e-15` declarado en A', B2 y B4, sobre los 6 escenarios |
| Bajo 2 | 05 daba por resuelto B6 y faltaba 06 | Confirmado | **Resuelto** con 06 en el HEAD final |
| Bajo 3 | Referencias de línea del recorte: 4554 y 4556, no 4560 y 4562 | Confirmado | **Resuelto** en 01 |
| Bajo 4 | El CI de 812/812 es de `73490c5`, no de `dfcaaa9` (que solo cambia docs) | Confirmado | **Resuelto** en 04 |

### thermo-nuclear-code-quality-reviewer (calidad)

**Veredicto:** «aprobable con cambios menores». No hay regresión estructural ni deuda nueva relevante, y la reestructuración en torno a `caso_ic95.py` es «la jugada correcta». Los hallazgos 1–7 de la primera pasada quedan resueltos o diferidos con justificación, salvo el 6 (faltaba 06).

| Sev. | Hallazgo | Estado |
|---|---|---|
| Medio 1 | La caracterización «exacta» excluía, sin explicarlo, el escenario donde B2 no es exacta, y 07 se contradecía | **Resuelto.** Caracterización sobre los 6 escenarios con banda, con la tolerancia de B2/B4/A' declarada |
| Medio 2 | 06 no existía | **Resuelto** (HEAD final) |
| Bajo 3 | «Todas las vías» no era cierto: A y A' no tenían una aserción propia | **Resuelto.** A en la prueba exacta, A' en la algebraica |
| Bajo 4 | Dos recorredores de árbol casi gemelos (detector e inventario) | **Diferido.** Es evidencia congelada; se unifica al promover el detector a `tests/` (07 §6) |
| Bajo 5 | El inventario recompone a mano piezas del helper | **Diferido**, con la misma razón |
| Bajo 6 | `sin_calendario` miraba una bandera, no el invariante | **Resuelto.** Ahora exige `factores_por_paso` todos a 1,0 |

## Cambios posteriores a la segunda pasada (sin tercera pasada)

En el commit documental final:
- B5 en `vias` y su prueba;
- separación entre `==` y `rel_tol` en las caracterizaciones;
- `sin_calendario` con `factores_por_paso`;
- ajustes de documentación (01, 02, 03, 04, 05, 06 y 07).

Son la aplicación directa de los remedios propuestos. Los verifiqué con la prueba (4 FAIL del contrato y 55 PASS) y con el diagnóstico, cuya salida en las vías previas no cambia. No hubo una tercera pasada de Thermos.
