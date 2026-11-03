# 07 · Informe de cierre: residual P0-C del IC95

## Veredicto: **NO-GO por incompatibilidad matemática**

No he modificado producción y P0-C no se declara corregido.

El IC95 retirado se reconstruye desde el vector de errores filtrado (vía A), y también sin la clave `error_absoluto`, a partir de `z_modificado` con la mediana y el MAD (vía A'). Además sale **sin ningún dato por ventana**, solo con agregados que el contrato protege:

| Vía | Datos usados | Resultado |
|---|---|---|
| B1 | `backtesting_comparativo[<modelo>_h<p>].metricas.rmse` + `iteraciones` | Exacto bit a bit en los 6 escenarios con banda. Ese RMSE **es** la `sigma_h` del intervalo |
| B2 | `desviacion_error` (ddof=1) + `error_medio` + n | Exacto (un caso con 2,8·10⁻¹⁴) |
| B4 | `mae` + `estabilidad_error` + n | Exacto en los 6 |
| B3 | RMSE_h persistido (tabla de horizontes, CSV, sesión, interfaz e informes) con su W | **Exacto en h=24 para cualquier serie**, porque ahí las muestras coinciden. En los demás horizontes es una aproximación: 6–13 % del semiancho, 0,16–0,42 % del pronóstico |

Retirar solo `errores_extremos.observaciones` pondría en verde la prueba del vector sin volver irreconstruible el intervalo: sería un cierre falso. Lo demuestran `test_caracterizacion_no_go_retirar_solo_el_vector_no_cierra_p0c` y `…retirar_solo_error_absoluto_no_basta`, en 03. El detalle está en 01.

## 1. Qué se hizo y qué no

**Hecho:**
- Diagnóstico de las vías A, A', B1–B4 con `ejecutar_proyeccion` real en 7 escenarios. En el de historia insuficiente no hay banda.
- Inventario de superficies y consumidores, incluidos los alias.
- Prueba adversarial reproducible, RED en la base: 4 FAIL del contrato y 31 PASS (caracterización, detector y escenarios).
- Huella sin cambios.
- Dos pasadas de Thermos sobre el diff (05).

**No hecho, por decisión del GATE 0:**
- ningún cambio en `app_icociv/**`;
- ninguna supresión de métricas;
- no se añadió ruido, redondeo ni ocultación;
- no se creó un método de banda nuevo;
- no se corrigió el comentario de producción engañoso (§4).

La comparación con lista blanca (04) **no aplica**, porque no se retiró ninguna ruta: la huella completa es idéntica (`d6be699b…0191`, 0 diferencias).

**Fuera de alcance, sin tocar:** 2D-5, AS-003, AS-004, AS-024, AS-028, `tests/**`, el perfil esencial, `main`, `develop/v1.1.2`, las ramas anteriores, el tag, el release, el ejecutable, el ZIP y `VERSION`.

## 2. Qué parte del objetivo de P0-C se puede cumplir

| Objetivo | ¿Alcanzable conservando los agregados? |
|---|---|
| No presentar ni publicar los límites del intervalo (`ci95_*` y réplicas) | **Sí.** Ya se cumple |
| No publicar el vector de errores por ventana | **Sí.** Basta retirar el registro por ventana completo (`observaciones`), no solo `error_absoluto`, porque `z_modificado` reconstruye el vector. No tiene consumidores en la aplicación (02 §1) |
| Que el intervalo sea **matemáticamente irreconstruible** desde la salida pública | **No.** La banda es `y ± c(n)·RMSE` (el factor de calendario vale 1 desde P0-F) y se publican el RMSE, n e y, además de otros pares equivalentes (B2, B4). Con RMSE_h y W persistidos, la banda del paso 24 es exacta en cualquier serie |

## 3. Alternativas (requieren decisión del propietario)

**A. Contrato honesto sin tocar los agregados.** *Recomendada.*
- **Qué es:** P0-C pasa a significar que «SAVIP no presenta ni publica una banda de predicción ni el vector de errores por ventana». Deja de prometer irreconstruibilidad. Se declara expresamente que, con el RMSE por horizonte y su número de ventanas, cualquiera puede calcular una banda clásica, que SAVIP no presenta como sustentada.
- **Cambios, en una fase separada y autorizada:**
  1. retirar el registro por ventana `observaciones` de `backtesting_comparativo[*].metricas.errores_extremos` en la salida pública, como higiene. La prueba adversarial del vector quedaría en GREEN. No hay que usar ese verde como prueba de irreconstruibilidad: el detector es heurístico;
  2. corregir el comentario de `COLUMNAS_OOS_RECONSTRUCTIVAS` y los docstrings que afirman que los agregados no permiten reconstruir;
  3. ajustar la redacción de los documentos de P0-C.
- **A favor:** conserva toda la evidencia OOS que sostiene la tesis. Es mínima y veraz.
- **En contra:** la banda sigue siendo deducible por quien haga la cuenta. P0-C queda redefinido, no «cerrado» en su sentido original.

**B. Revisión formal del contrato de publicación de agregados.** *Requiere nueva autorización y una evaluación académica.*
- **Qué es:** dejar de publicar en el objeto las métricas por modelo y horizonte del comparativo (`rmse`, `desviacion_error`, `error_medio`, `mae` + `estabilidad_error` y el detalle de extremos), y conservarlas solo internamente.
- **A favor:** elimina las vías B1, B2 y B4 del objeto.
- **En contra:**
  - **no basta**: B3 sigue dando la banda exacta en h=24 desde el RMSE_h protegido, y la aproxima en el resto;
  - para la irreconstruibilidad total habría que retirar o alterar el RMSE_h o su W, y eso choca con el REQ 16 y con la sustentación;
  - se pierde transparencia del banco de 21 candidatos.

**C. Cambio metodológico** (que la `sigma` del intervalo deje de ser el RMSE publicado). *No recomendado y no autorizado.*

Cambia el método estadístico solo para ocultar un número. Contradice la regla de no inventar métodos y no resuelve la cuestión de fondo.

**Mitigación del vector en una fase separada:** sí es posible y no causa regresión (02 §4). Pero tiene que presentarse como higiene de datos, **no** como cierre de P0-C.

## 4. Hallazgo documental en producción (no corregido)

`servicio_proyeccion.py:625-656`, en el comentario de `COLUMNAS_OOS_RECONSTRUCTIVAS`, justifica conservar los agregados diciendo que «de un promedio de cuadrados no se recupera la muestra». Es cierto pero irrelevante: la banda no necesita la muestra, solo `sigma = RMSE` y n.

El comentario lleva a creer que los agregados son inocuos para P0-C. Corregirlo es un cambio de producción (solo de comentario) y queda propuesto en la alternativa A.

## 5. Resultados de control

Detalle en 03, 05 y 06.

| Control | Resultado |
|---|---|
| Huella | Idéntica: SHA-256 `d6be699b…0191`, 0 diferencias. No hay cambios de producción |
| Prueba adversarial en la base | RED: 4 FAIL del contrato del vector, con mensaje y rutas reales (1 008). Las 16 pruebas de caracterización dan PASS, lo que demuestra la contradicción |
| Sensibilidad | 9 casos del detector con asserts y 2 «correcciones parciales» simuladas (sin el vector y sin `error_absoluto`). Las dos demuestran un cierre falso |
| Perfil esencial y golden | El código es el mismo que en `dfcaaa9` (812/812, 29/29). El CI de la rama se informa en 06 |
| Thermos | Ver 05 |

## 6. Siguiente paso propuesto

Que decidas entre A, B o C. Si eliges A, propongo un prompt independiente para la fase de higiene:
- retirar el registro por ventana;
- corregir el comentario;
- llevar a `tests/` solo los grupos «contrato» y «detector» de la prueba adversarial, unificando el detector con los que ya existen allí. La caracterización se queda como diagnóstico, porque protegería la vulnerabilidad;
- comparar la huella contra una lista blanca de `observaciones`.

**2D-5 sigue sin ejecutarse.**
