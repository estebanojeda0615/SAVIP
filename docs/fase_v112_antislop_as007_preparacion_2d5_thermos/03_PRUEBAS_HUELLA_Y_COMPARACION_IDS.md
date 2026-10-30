# 03 · Pruebas, huella y comparación de ids

**Entorno.** Mismo equipo y venv antes y después (00 §2), con `QT_QPA_PLATFORM=offscreen`, `PYTHONDONTWRITEBYTECODE=1` y `PYTHONIOENCODING=utf-8`. Cada ejecución se hizo sobre una copia limpia del árbol, fuera del repositorio: `C:/Pruebas SAVIP/AS007/base` para `6ac158d` y `.../final` para `c656e19` y, después, para `da04725`.

## 1. Perfil esencial

**Comando:** `python scripts/pruebas_fase0.py esenciales --junitxml=resultados/esenciales.xml -o junit_family=xunit2`

| Ejecución | Archivos | Ids | PASS | FAIL | Skip/xfail | Fallos en la 1.ª ejecución | Intermitentes | Golden | AS-001 |
|---|---|---|---|---|---|---|---|---|---|
| Local, base `6ac158d` | 81 | 803 | 803 | 0 | 0 | **0** | ninguna | 29/29 | 16/16 |
| Local, `c656e19` (1 929 s, sin carga) | 82 | 812 | 812 | 0 | 0 | 0 | ninguna | 29/29 | 16/16 |
| **Local, `da04725`** (3 769 s; duración inflada porque corrían a la vez las revisiones Thermos y las mutaciones) | 82 | **812** | **812** | **0** | **0** | **0** | ninguna | **29/29** | **16/16** |
| CI [41003966465](https://github.com/estebanojeda0615/SAVIP/actions/runs/41003966465), `fceadea` (solo docs y filtro) | 81 | 803 | 803 | 0 | 0 | 0 | ninguna | 29/29 | — |
| CI [41004130161](https://github.com/estebanojeda0615/SAVIP/actions/runs/41004130161), `febd981` (1.ª versión de las pruebas) | 82 | 812 | 812 | 0 | 0 | 0 | ninguna | 29/29 | — |
| CI [41007527954](https://github.com/estebanojeda0615/SAVIP/actions/runs/41007527954), `c656e19` | 82 | 812 | 812 | 0 | 0 | 0 | ninguna | 29/29 | — |
| CI [41007657860](https://github.com/estebanojeda0615/SAVIP/actions/runs/41007657860), `866d2e4` (docs) | 82 | 812 | 812 | 0 | 0 | 0 | ninguna | 29/29 | — |

**Último commit de código: `1f6fa6a`.** Solo cambia, respecto a `da04725`, el archivo nuevo de pruebas: la normalización de encabezados, la aserción del anexo y los docstrings. En local pasa 9/9 y detecta las 14 mutaciones. El perfil completo sobre `1f6fa6a` y sobre el HEAD documental lo ejecuta el CI; su resultado está en 06 y en el mensaje de entrega.

Evidencias: [`evidencia/esenciales_resumen.txt`](evidencia/esenciales_resumen.txt) y [`evidencia/ci_resumen.txt`](evidencia/ci_resumen.txt).

## 2. Ids antes y después

`comparar_ids_esenciales.py` (Fase 2B) compara los JUnit de la primera ejecución por `(classname, name)` ([`evidencia/comparacion_ids_esenciales.txt`](evidencia/comparacion_ids_esenciales.txt)):

- **solo antes: 0**. Los **803 ids originales se conservan todos y pasan**.
- **solo después: 9**, los de `tests/test_as007_contratos_r3_vigentes.py`:
  - `test_p0c_tablas_de_ventanas_sin_errores_ni_limites_ci`
  - `test_p0c_dataframe_de_proyecciones_sin_columnas_de_intervalo`
  - `test_p0c_sesion_json_sin_errores_oos_y_con_agregados`
  - `test_p0c_csv_sin_columnas_de_intervalo_y_con_agregados`
  - `test_p0c_interfaz_sin_vocabulario_de_intervalo`
  - `test_p0c_docx_sin_vocabulario_ni_columnas_de_error`
  - `test_p0c_pdf_sin_vocabulario_de_intervalo`
  - `test_p0e_la_evidencia_oos_se_declara_provisional`
  - `test_p0c_conserva_agregados_oos_y_diseno_de_ventanas`
- **estado cambiado: 0**.

## 3. Recolección total

Fuente: [`evidencia/coleccion_diff.txt`](evidencia/coleccion_diff.txt).

- Se pasa de **1 058 a 1 067** pruebas recolectadas. Las 9 nuevas son las únicas diferencias y no desaparece ningún id.
- Los **3 errores históricos siguen igual** y **no se declaran resueltos**: `test_equivalencia_presupuestal_fase_4e_b` (`docs.fase_4e_b_unificada`), `test_p0c_objeto_publico_sin_intervalo` y `test_p0c_regresion_negativa_c2` (`tests.test_p0c_retiro_intervalos_no_sustentados`).
- Con el retiro de 2D-5 simulado en memoria (02 §1), la base sube a 4 errores y la fase final se queda en 3.

## 4. Huella semántica exacta

`docs/fase_v112_antislop_02a_as003/evidencia/huella_semantica.py` cubre:
- 20 casos motor×horizonte;
- el SSE de los 21 candidatos;
- H1–H24 y MAE(h);
- economía, empalme y rechazos.

Resultados ([`evidencia/huella_resumen.txt`](evidencia/huella_resumen.txt)):
- **Base:** dos capturas, 0 diferencias.
- **Final frente a base:** 20/20 casos, **0 diferencias exactas**.
- **SHA-256 idéntico en las tres capturas:** `d6be699b700b3fa3379c743cc9d0ccbf5c185cacfa228208dbb95c2735370191`. Es el mismo valor que en las fases 2A a 2D-4.

No hay ningún cambio de producción: `git diff 6ac158d HEAD -- app_icociv aplicacion.py packaging VERSION requirements*.txt tests/fixtures` está vacío.

## 5. r3, ejecución directa

**Comando:** `python tests/test_residuales_auditoria_independiente_r3.py`. Se ejecuta en Qt offscreen, tarda unos 15 s y solo escribe en un `TemporaryDirectory`.

| Árbol | Resultado | FAIL |
|---|---|---|
| Base `6ac158d` | 21/27, código 1 | C12 («La tabla de ventanas perdio 'Periodo'»), HG4 (aserción sin mensaje), HG5 («El primer origen no se declara provisional»), HG6 («Una sola ventana volvio a negar la proyeccion»), B («n=7 volvio a bloquearse») y G (aserción sin mensaje) |
| `febd981`, `c656e19` y `da04725` | **21/27, código 1: salida idéntica línea a línea** | Los mismos 6, con los mismos mensajes |
| Final con 2D-5 simulado | **21/27, idéntico** | Los mismos 6 |

Sensibilidad del nuevo `_tramo`:
- si se desplaza la frontera 3, HG6 falla en la aserción de tramos;
- si cambia la redacción del texto, HG6 falla con «Texto de tramo no reconocido».

Evidencias:
- [`evidencia/r3_ejecucion_directa_base.txt`](evidencia/r3_ejecucion_directa_base.txt)
- [`evidencia/r3_ejecucion_directa_final.txt`](evidencia/r3_ejecucion_directa_final.txt)
- [`evidencia/r3_mutacion_frontera.txt`](evidencia/r3_mutacion_frontera.txt)
- [`evidencia/r3_mutacion_texto.txt`](evidencia/r3_mutacion_texto.txt)

## 6. Pruebas focalizadas y comprobaciones adicionales

| Comprobación | Resultado |
|---|---|
| `test_as007_contratos_r3_vigentes` | 9/9 PASS |
| 14 mutaciones en memoria sobre las pruebas nuevas | 14/14 detectadas ([`evidencia/mutaciones_pruebas_nuevas.txt`](evidencia/mutaciones_pruebas_nuevas.txt)). Una de ellas mete vocabulario en `Formula.general`: ahora la detectan las pruebas de DOCX y de PDF |
| PS-01…05, 2C, 1A (con AS-001) y AS-007 | 63/63 PASS con `febd981` y 19/19 de PS y 2C con `c656e19` |
| `compileall` de `app_icociv`, `aplicacion.py`, `scripts`, `pruebas` y `tests` | OK |
| Importar los 86 módulos de `app_icociv` y `aplicacion`, y crear `VentanaPrincipal` en Qt offscreen | OK |
| `git diff --check` en cada commit | sin avisos |
| Workflow | +1 línea en el filtro de ramas. GitHub lo ejecutó en esta rama, así que la sintaxis es válida. No cambian pasos, reintentos, timeouts ni condiciones |

## 7. Lo que estas pruebas no cubren

- **El residual P0-C de producción** (`errores_extremos.observaciones[*].error_absoluto`, 04 hallazgo B-A1) **no lo cubre ninguna prueba**. C1 lo declara fuera de su alcance. Corregirlo exige cambiar producción.
- Thermos no sustituye a estas pruebas, y estas pruebas tampoco sustituyen a Thermos (04).
