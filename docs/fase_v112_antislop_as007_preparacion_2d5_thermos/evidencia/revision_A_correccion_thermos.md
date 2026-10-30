# Thermos A · thermos:thermo-nuclear-reviewer · alcance 83549e7...6ac158d (lote 2D-4)

**Invocación.** Skill `thermos:thermos` (Thermos 1.1.0), que lanza en segundo plano el agente `thermos:thermo-nuclear-reviewer` con el diff `diff_A_codigo.patch`. Claude Code 2.1.238. El revisor trabajó en solo lectura: hizo `git archive` de `6ac158d` a una carpeta temporal fuera del repositorio. Lo que sigue es su salida condensada; los hallazgos no se han alterado.

**Resultado.** Ningún hallazgo crítico, alto ni medio. Dos bajos y una nota informativa. Al no haber hallazgos de severidad media o superior, no se revisó la discusión del PR.

## Verificaciones sin hallazgo

1. **Consumidores.** Se buscaron con `git grep -w` los 10 nombres retirados y sus constantes en todo el árbol, sin `docs/`. No hay ninguna llamada. Quedan:
   - el comentario de `servicio_proyeccion.py:2592`;
   - la tupla de cadenas `HEREDADAS`;
   - las guardas textuales de ausencia.

   `_numero` en otros módulos son homónimos propios, no el retirado.
2. **Imports desde `modelos_interpretables`.** Revisados `servicio_proyeccion.py:82`, `validacion/backtesting.py:24`, `pruebas/prueba_horizonte_dinamico_ui_reportes.py:728`, 10 pruebas y los usos `MI.`/`mi.`: todos los símbolos usados siguen existiendo.
3. **Imports dinámicos.** No hay `import *`, `getattr` ni `importlib` sobre el módulo, y `__init__` no reexporta nada.
4. **Sesiones y reportes.** Nada lee `score_seleccion` ni `razones_*`. `ranking_backtesting`, `descartes_modelos` y `comparacion_benchmarks` se leen con valor por defecto. Una sesión JSON antigua sigue funcionando.
5. **El módulo tras el retiro.** El AST es correcto. `math`, `EPS_NUMERICO` y `MIN_ITERACIONES_WF` siguen en uso. `pyflakes` solo da un aviso previo en la línea 598. Los 2 imports retirados siguen definidos en `criterios.py:152-153`, y `test_cierre_metodologico:445-446` los lee a través de `sp`.
6. **Ruta vigente.** Intacta. `git diff --quiet 83549e7 6ac158d -- app_icociv/proyeccion` sale limpio.
7. **CI y manifiesto.** El manifiesto lista archivos, no ids. El workflow solo añade la rama y la excepción de `.gitignore` está acotada.
8. **Pruebas sobre la copia de `6ac158d`.** 157 pasan. Hay fallos ajenos al lote:
   - `test_cierre_metodologico::test_no_hay_modelo_por_horizonte`, en la línea 510. Busca por texto la línea `modelo = seleccion_horizonte["modelo"]`, que ya no existe; ni el archivo ni la prueba cambian en 2D-4, y la prueba no es esencial. Clasificación: **riesgo previo**.
   - 3 fallos de `test_dependencia_statsmodels`, causados por la copia del revisor, que no incluye `requirements*` ni `packaging/`. Es un artefacto de su entorno.

## Hallazgos

- **B-1. BAJO, nuevo defecto (deuda menor).** En `modelos_interpretables.py:43`, `MIN_ITERACIONES_SELECCION` queda sin lectores: su único uso estaba en la función retirada. Por eso la frase de los docs del lote «solo quedaron huérfanos 2 imports» es exacta para las funciones, pero no para esta constante. Remedio: retirarla o anotarla como huérfana conocida.
- **B-2. BAJO, nuevo defecto documental.** El comentario de `tests/test_fundamentacion_metodologica.py:264-269` cita `2f70391` L280-L444, pero ese rango solo cubre el selector. Los 9 auxiliares están en L447-L597 y L1352-L1381. Arrastra la misma truncación del ancla de R1 en `02_REGISTRO_HISTORICO_METODOLOGICO.md:52`, un documento previo que queda fuera del diff. Remedio: citar «L280-L597 y L1352-L1381».
- **I-1. Informativo.** Las guardas textuales P0-A ahora solo fallan si se reintroduce la función. La prueba de la línea 244 inspecciona `_evaluar_horizontes_proyeccion`, que es heredada (2D-3) y no la ruta vigente, así que esa parte del comentario no es exacta. Remedio: revisarlas con 2D-3.

## Falsos positivos descartados

- «Los imports retirados rompen a consumidores que los leen a través de `modelos_interpretables`».
- «Retirar el id rompe el manifiesto».
- «`_numero` en otros módulos depende del retirado».
