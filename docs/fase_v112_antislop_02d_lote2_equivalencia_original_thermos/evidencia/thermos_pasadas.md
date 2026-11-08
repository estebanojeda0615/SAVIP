# Thermos: salidas de cada pasada

Las salidas de los agentes están transcritas fielmente y condensadas sin eliminar ningún hallazgo. Ambos agentes trabajaron en solo lectura sobre el `.patch` guardado fuera del repositorio y sobre los archivos completos.

> Thermos solo revisa diffs. No sustituye la prueba contra la V1.1.2 original (oráculo, golden exacto, huella y perfiles), que está en 01 y 05.

## 1.ª pasada · diff `54789587…5478958...55ba5646` (código, sin docs)

### `thermos:thermo-nuclear-reviewer` (corrección)

**Resultado:** sin hallazgos críticos, altos ni medios.

**Comprobaciones del agente**
- Producción solo cambia en 2 archivos:
  - `servicio_proyeccion.py`: +0 −111 (28 + 79 + 4 separadores);
  - `criterios.py:568`: 1 línea, el campo `ubicacion`.
- No toca el motor, `_seleccionar_modelo_rectangular`, `_matriz_rectangular_12_24`, `_sse_exacto`, `_rmse_desde_sse` ni `_ejecutar_proyeccion_base`.
- El par solo queda en lápidas y comentarios, en la tupla de ausencia exigida (`test_fase1a…:303`) y en `HEREDADAS` (texto). No hay `__all__`, `getattr`, `import_module` ni `runpy` sobre esos nombres.
- Los imports del módulo productivo siguen en uso. `_sse_exacto` conserva un único llamador: el selector vigente.
- **C-SEL-001:**
  - el nuevo `ubicacion` existe;
  - ninguna prueba ni artefacto compara ese campo;
  - la columna solo la usa `como_fila_markdown`.
- **Runner:**
  - `pruebas_fase0.py` calcula las históricas por glob, así que borrar `test_rmse_global_estable.py` no rompe nada;
  - los archivos esenciales tocados siguen en `ESENCIALES`.
- **`p0d_en_el_selector_vigente`:**
  - la matriz tiene la forma correcta;
  - `1e16+1 == 1e16+0,81` también con `sum` y con `math.fsum`;
  - la mutación propia (suma flotante, `hypot`, último en empate, orden de `datos`) se detecta en todos los casos;
  - no se recoge como prueba.
- Las 4 pruebas redirigidas pasan sobre el selector vigente.
- Las 14 citas de las lápidas existen y coinciden con lo que prueban.
- No hay imports huérfanos nuevos.
- `pytest` de los 9 archivos tocados: 118 PASS y 6 FAIL, todos preexistentes (I-1 y los 3 ya conocidos).

**Hallazgos**
- **B-1, bajo, nuevo:** se borró entero el bloque `if __name__ == "__main__":` de `tests/test_horizonte_evidencia_reducida.py`, y la ejecución directa ya no corre nada.
- **I-1, preexistente:** en ese archivo también fallan `test_serie_corta_publica_su_cobertura_y_niega_solo_por_ventanas`, `test_la_rejilla_de_horizontes_no_tiene_tope_historico_ni_cascada` y `test_serie_erratica_se_entrega_con_su_incertidumbre_a_la_vista`. Lo mismo ocurre en la base 5478958.
- **I-2, nuevo y aceptable:** `test_la_regla_no_consulta_umbrales_ni_identidad` ya no inspecciona un extractor; el anterior era código muerto.
- **I-3, cosmético:** el encabezado «9, 10 y 11» de test_origen y el docstring «(D1-D12)». Además, el caso 1e16 no es «una ULP», aunque cubre el mismo defecto con más fuerza.
- **Preexistentes:**
  - `import struct` (test_p0d) e `import math` (test_cierre) sin usar;
  - el docstring de `_puntaje_rmse_ponderado`;
  - la 2.ª aserción de D11, trivial.

### `thermos:thermo-nuclear-code-quality-reviewer` (calidad)

**Veredicto:** «APROBADO CON OBSERVACIONES», sin hallazgos críticos ni altos. El agente pasó pyflakes en base y HEAD y comprobó los 12 localizadores `::` y los 14 ids citados.

**Medios**
- **M1, nuevo:** `p0d_en_el_selector_vigente` duplicaba datos, constructor y empate de Fase 1A. Propuesta: componer las propiedades de Fase 1A.
- **M2, nuevo por la redirección:**
  - D12 cambia de semántica: el selector vigente también calcula lo que se reporta, y `_rmse_desde_sse` no se escanea;
  - `test_cierre…:413` es un subconjunto de `test_seleccion…:58`;
  - `assert "rmse" in fuente` se satisface con el docstring.

  No son huecas del todo: impiden reintroducir constantes de umbral. Se aceptan para conservar los ids y se recomienda unificarlas en un lote posterior.
- **M3, nuevo:** las lápidas repiten el mapeo en tres archivos, con unos 30 ids que nada verifica.

**Bajos**
- **B1, nuevo:** `__main__` borrado en test_horizonte (coincide con B-1).
- **B2, nuevo:** restos documentales:
  - el docstring «(D1-D12)»;
  - el encabezado «6, 7 y 8»;
  - banners dobles en test_seleccion;
  - tupla de un elemento;
  - `retirados` de fase1a, nombre preexistente.
- **B3, informativo:** D1, D5 y D6 tenían aserciones sobre `_sse_exacto`; quedan cubiertas por D13.

**Respuestas del agente:**
- no hay huérfanos;
- C-SEL-001 es coherente (las rutas sin `::` y con tildes son AS-024, preexistente);
- borrar `test_rmse_global_estable.py` está justificado: T7 → as001 divergente, T7b → as001 ULP/DBL_MAX, T8 → `p_solo_pares_comunes`, T9 → `p_empate_primer_candidato_del_banco`;
- retirar `test_modelo_agregado…` fue correcto.

**Preexistentes registrados por el agente:**
- imports sin uso en `servicio_proyeccion` (`UMBRAL_RRMSE_PEOR_BENCHMARK`, `TOLERANCIA_RRMSE_BENCHMARK`, `aplicar_ajuste_calendario`, `eneros_en_horizonte`, `calcular_metricas`);
- variables muertas `comparacion_benchmarks` (L1252) y `sesgo` (L2756);
- el docstring de `_puntaje_rmse_ponderado`;
- las listas del CI y de `.gitignore`, que crecen con cada fase.

### Resolución (commit `49106f95`, solo pruebas; `git diff 55ba564 49106f9 -- app_icociv` vacío)

| Hallazgo | Verificación propia | Estado |
|---|---|---|
| B-1 / B1: `__main__` borrado | Confirmado: mi corte llegaba hasta el final del archivo | **Resuelto**: restaurado con las 8 llamadas restantes |
| M1: helper duplicado | Confirmado | **Resuelto**: compone `p_sse_exacto_decide_una_ulp`, `p_invariante_al_orden_de_entrada` y `p_empate_primer_candidato_del_banco` sobre `SELECTOR` de Fase 1A. La mutación (`_referencia` con `flotante` y con `ultimo_en_empate`) se sigue detectando (`evidencia/sensibilidad_p0d_vigente.txt`) |
| M3: lápidas largas | Confirmado | **Resuelto**: 3-4 líneas, con puntero a Fase 1A y a `03_G2_MATRIZ_PRUEBAS_Y_CRITERIO_CSEL001.md` (ruta completa) |
| I-3 / B2: restos documentales | Confirmado | **Resuelto**: encabezados de test_origen y test_nmin, docstring de test_p0d, banners y tupla de test_seleccion, y «SSE exacto» en lugar de «una ULP» en la lápida |
| M2: inspecciones de fuente | Confirmado. Ya buscaban cadenas en la base y se conservan para no perder ids | **Diferido** (08 §4). Unificarlas modificaría pruebas fuera del alcance mínimo |
| I-1: 3 FAIL preexistentes en test_horizonte | Confirmado en 5478958 | Registrado (06) |
| I-2 y B3 | — | Aceptados, sin cambio |
| Preexistentes | — | Registrados (08 §4). No se tocan |

## 2.ª pasada · diff `54789587...49106f95` (delta `55ba564..49106f9`, solo pruebas)

### `thermos:thermo-nuclear-reviewer` (corrección)

**Resultado:** sin hallazgos de severidad alta ni media, y sin hallazgos nuevos de corrección.

**Comprobaciones del agente**
- **`__main__` de test_horizonte:** coincide con el de 5478958 y 6672529, con las mismas 8 llamadas en el mismo orden, sin la del test retirado.
- **Textos de I-3:** corregidos y coherentes con las funciones que quedan (D4, D11, D12, D13).
- **`p0d_en_el_selector_vigente`:** comparado con la versión anterior frente a los 5 mutantes de `_referencia`, la capacidad de detección es idéntica:
  - detecta `suma_flotante` y `ultimo_en_empate`;
  - ninguna de las dos versiones detecta `peso_1_h`, `todos_los_pares` ni `rmse_sin_n`, que cubre `test_cada_mutante_es_detectado`.
- **Importaciones:** no hay ciclo (fhg → nmin, con la importación dentro de la función → fase1a). Con `tests/__init__.py` el módulo no se carga dos veces.
- **Ejecución directa:** `python tests/test_nmin_adversarial.py` da exit 0 con 9 OK.
- **Ids esenciales** (`--collect-only` sobre ESENCIALES): 816 en la base frente a 814 en HEAD. Solo faltan los 2 autorizados.
  - Recuento propio de esa colección, que incluye parametrizaciones. Las cifras 811/809 son las del runner por JUnit.
- **Producción y referencias:**
  - `git diff 55ba564 49106f9 -- app_icociv scripts .github` está vacío;
  - no queda ninguna referencia viva al par ni a las pruebas retiradas.
- **pytest de los 8 archivos tocados:** 109 PASS y 6 FAIL, todos preexistentes porque fallan igual en 5478958 (3 en test_horizonte, h3 y h4 de fhg, y `test_no_hay_modelo_por_horizonte`).

**Informativos**
- **Nuevo:** la ejecución directa de `test_nmin_adversarial` y `test_integracion_fhg` necesita ahora pytest instalado, porque Fase 1A lo importa. Ninguno de los dos docstrings promete funcionar sin pytest, y el venv lo trae.
- **Nuevo:** el documento 03_G2 citado en las lápidas entra en el commit documental.

### `thermos:thermo-nuclear-code-quality-reviewer` (calidad)

**Veredicto:** **«APROBADO»**.

- **M1** resuelto. La indirección fhg→nmin→fase1a es aceptable.
- **M3, B1 y B2** resueltos. B3 queda como informativo.
- **M2, corrección del propio agente:** `assert "rmse"` también lo satisface el código ejecutable (claves `rmse_*`), no solo el docstring.
- **M2, solape de guardias introducido por este lote:** la guardia de `test_cierre…:413-417` queda contenida en la de `test_seleccion…:52-57`, porque ahora ambas inspeccionan la misma función. Hay que registrarlo como deuda con nombre propio, sin bloquear. Fusionarlas ampliaría el alcance.
- **D12:** conserva su intención («la ruta de decisión no usa tolerancias»).
- **pyflakes frente a la base:** solo avisos preexistentes. El diff no deja huérfanos y elimina uno.
- Ningún archivo supera las 1 000 líneas.

### Resolución

| Hallazgo | Estado |
|---|---|
| Solape de las guardias cierre/seleccion | **Deuda registrada** (08 §4, «D-2D2-1»): fusionarlas en un lote de saneamiento de pruebas |
| Ejecución directa con pytest | Aceptado y registrado. No hay promesa contraria |
| Documento 03_G2 citado | **Resuelto**: entra en el commit documental de esta rama |

La 2.ª pasada cubre el último commit de código, `49106f95`. Después no hubo más cambios de código.
