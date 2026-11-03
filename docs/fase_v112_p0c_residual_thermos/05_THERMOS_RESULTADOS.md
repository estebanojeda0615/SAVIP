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
| Bajo B6 | Referencias a 04–07 inexistentes y un recorrido de alias no versionado | Confirmado | **Resuelto.** 04–07 añadidos; 02 dice que el recorrido de alias no está versionado y que el revisor lo repitió |

### thermo-nuclear-code-quality-reviewer (calidad)

**Veredicto:** no aprobado tal cual, aunque ningún punto afecta a la conclusión NO-GO, que «está bien sostenida por los números».

| Sev. | Hallazgo | Estado |
|---|---|---|
| Alto 1 | Duplicación entre scripts (series, periodo objetivo, espía, banda) y respecto a los helpers de `tests/` | **Resuelto dentro de la evidencia.** Un único `evidencia/caso_ic95.py` concentra series, escenarios, `proyectar` (con `functools.cache` y espía restaurado), `banda` y `vias`; el diagnóstico se reduce a un bucle. **Diferido fuera de alcance:** unificar con los helpers de `tests/`, porque esta fase no toca `tests/`. Se recomienda al promover la prueba (07 §6) |
| Medio 2 | Docstrings que exageraban: el detector no recorría Series/arrays, no había prueba de B2 y el inventario «reconstruía» bandas sin hacerlo | **Resuelto.** El detector recorre Series y celdas, con casos de prueba; B2 y B4 se prueban; el docstring del inventario dice lo que hace |
| Medio 3 | La guarda NaN fallaba y el `except` estaba mal justificado | **Resuelto.** `proyectar` devuelve `interno=None` si la banda no es finita; se quitó el `except` |
| Medio 4 | La prueba mezclaba contrato, caracterización y detector; las mutaciones solo imprimían | **Resuelto.** Tres grupos con nombres explícitos; las mutaciones son ahora `test_detector_sensibilidad` y las dos «correcciones parciales», con asserts. Se borraron `mutaciones_adversarial.py` y su salida |
| Medio 5 | Reproducibilidad: comandos distintos, salida filtrada, Qt y `sys.path` | **Resuelto.** Un único comando canónico; salida completa sin filtrar; `caso_ic95` fija Qt offscreen y `sys.path`; la huella documenta sus comandos |
| Medio 6 | Referencias a documentos inexistentes | **Resuelto** (04–07) |
| Bajo 7 | Restos: `factor` sin uso, `CLAVES` copiadas a mano, `.get` sobre `None`, prosa del proceso | **Resuelto.** `CLAVES_POR_VENTANA` se deriva de `sp.COLUMNAS_OOS_RECONSTRUCTIVAS`; el calendario se comprueba con `sin_calendario` |
| Bajo 8 | Configuración que crece una línea por fase | **Diferido.** Lo decide el propietario, como en las fases anteriores |

## Segunda pasada: diff final

Ver más abajo, en §«Segunda pasada»: la añado cuando terminen los agentes.
