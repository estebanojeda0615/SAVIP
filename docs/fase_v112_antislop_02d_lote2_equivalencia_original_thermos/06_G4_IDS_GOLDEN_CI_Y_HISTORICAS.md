# 06 · G4: ids, golden, AS-001, huella, históricas, CI

## 1. Ejecuciones

| Ejecución | Base | Final |
|---|---|---|
| Perfil esencial | Copia de `5acb09f` (AS-028). Sus pruebas y su producción son idénticas a las de `5478958`, porque los commits posteriores solo tocan docs | **Copia de `49106f95`** (último commit de código) |
| Perfil histórico | Copia de `02426ef` (código = `5478958`) | Copia de `49106f95` |
| Entorno | Venv de pruebas: Python 3.12.10 y los mismos paquetes que el EXE original | Ídem |

Comando: `python scripts/pruebas_fase0.py {esenciales|historicas} --junitxml=… -o junit_family=xunit2`. Los ids se comparan por `(classname, name)` con `comparar_ids_esenciales.py` (Fase 2B) y con `evidencia/conciliacion_historicas.txt`.

## 2. Perfil esencial

| | Ids | PASS | FAIL | Skip/xfail | Fallos en la 1.ª ejecución | Intermitentes | Golden | AS-001 | Tiempo |
|---|---|---|---|---|---|---|---|---|---|
| Base | 811 | 811 | 0 | 0 | 0 | ninguna | 29/29 | 16/16 | — |
| **Final** | **809** | **809** | **0** | **0** | **0** | **ninguna** | **29/29** | **16/16** | 2 611 s |

**Comparación de ids** (`evidencia/comparacion_ids_esenciales.txt`):

| Concepto | Resultado |
|---|---|
| Solo en la base | **2**, los autorizados: `tests.test_nmin_adversarial::test_muestra_comun_intacta_desde_el_primer_origen` y `tests.test_origen_inicial_backtesting::test_p0d_la_regla_de_seleccion_no_cambia` |
| Solo en el final | **0** |
| Estado cambiado | **0**. Los 809 ids conservados siguen en PASS |

## 3. Perfil histórico: conciliación id por id

**Criterio de conteo.**
- El JUnit separa fallos (`failure`) y errores (`error`). Los 3 `error` son las entradas de los 3 errores de recolección históricos.
- El runner informa «N fallos en la primera ejecución, M errores». El perfil histórico no reintenta.
- Un archivo que agota el tiempo (1 200 s) no deja JUnit.
- Los archivos-script sin tests recogibles salen con el código 5 de pytest, «(5)».

| | Ids JUnit | PASS | FAIL | ERROR | Listado (`--listar`) | Archivos con fallo (runner) |
|---|---|---|---|---|---|---|
| Base `5478958` | 241 | 191 | 47 | 3 | 242 | `test_fase_4a_c` (tiempo agotado), `bghc` (5), `r3` (5) |
| **Final `49106f95`** | **213** | **163** | **47** | **3** | **214** | Los mismos |

**Por qué el listado y el JUnit no coinciden.** El listado cuenta las 4 pruebas de `test_fase_4a_c`, que no tienen JUnit porque el archivo agota el tiempo en las dos ejecuciones. El JUnit, a su vez, añade las 3 entradas ERROR. Así:
- base: 242 − 4 + 3 = 241;
- final: 214 − 4 + 3 = 213.

**Comparación id por id** (`evidencia/conciliacion_historicas.txt` y `comparacion_ids_historicas.txt`):

| Concepto | Resultado |
|---|---|
| Solo en la base | **28**, los retirados en G2, todos PASS en la base (03 §2) |
| Solo en el final | **0** |
| Estado cambiado | **0** |
| PASS en la base que no pasa en el final | **Ninguno** |
| Líneas `FAILED`/`ERROR` del runner | **Idénticas** en base y final (diff vacío) |

Los 47 FAIL son preexistentes y se reparten en 22 archivos (detalle por archivo en la conciliación). Entre ellos están los 6 de los archivos tocados por el lote: `test_no_hay_modelo_por_horizonte`, `h3` y `h4` de fhg, y 3 de `test_horizonte_evidencia_reducida`. No se resuelven ni se ocultan.

## 4. Recolección y otras comprobaciones (copia del final)

| Comprobación | Base | Final |
|---|---|---|
| `pytest --collect-only -q tests` | 1 066 recogidos y 3 errores | **1 036 recogidos y los mismos 3 errores** (`test_equivalencia_presupuestal_fase_4e_b`, `test_p0c_objeto_publico_sin_intervalo`, `test_p0c_regresion_negativa_c2`). La baja de 30 es intencionada: 2 esenciales y 28 históricas; no es una corrección funcional |
| `--listar` | 811 / 242 / 13 | **809 / 214 / 13** |
| Huella semántica (`huella_semantica.py`) | SHA-256 `d6be699b…0191` | **20/20 con 0 diferencias exactas y el SHA-256 `d6be699b700b3fa3379c743cc9d0ccbf5c185cacfa228208dbb95c2735370191` idéntico** |
| Oráculo ampliado (05) | — | C: 66/66 idénticos frente a 5478958; A: 65/66 frente a la original (el caso distinto es AS-001) |
| Golden con tolerancia cero | 0 diferencias | **0 diferencias** |
| `pruebas/prueba_horizonte_dinamico_ui_reportes.py` | 29 tests: 21 PASS / 8 FAIL | **29: 21 / 8, con los mismos ids y estados**. La ejecución directa se detiene en el 2.º test, igual que antes |
| `pruebas/ejemplo_uso.py` y `pruebas/prueba_estadistica.py` | Error preexistente: `ModuleNotFoundError` y `FileNotFoundError` (sin anexo DANE) | **Salida idéntica** salvo la ruta de la copia. No se pudieron ejecutar de forma comparable con datos reales: no hay anexo DANE |
| Escrituras en disco de los scripts | — | Ninguna |
| `pip check` | — | `No broken requirements found.` |
| `compileall` de `app_icociv`, `aplicacion.py`, `tests` y `pruebas` | — | Código 0 |
| Importación de los 86 módulos, `aplicacion` y `VentanaPrincipal` (Qt offscreen) | — | OK. El par queda ausente |
| `tests/fixtures/**` | — | Diff vacío |

## 5. GitHub Actions (`fase0-pruebas`, perfil esencial completo)

| Run | Commit | Resultado |
|---|---|---|
| [41954109682](https://github.com/estebanojeda0615/SAVIP/actions/runs/41954109682) | `5478958`, la base | success; 811/811; 0 fallos en la 1.ª ejecución |
| [42108454515](https://github.com/estebanojeda0615/SAVIP/actions/runs/42108454515) | `02426ef`, el informe preliminar de G0 (código = `5478958`) | **failure**: `test_interaccion_fase_3c_a::test_a_acciones_geometria_click_teclado_y_senales` falló en la 1.ª ejecución y también en el reintento (`QSignalSpy.count() == 2` frente a 1, `:140`). Es la intermitente GUI conocida (AS-028). El código evaluado era idéntico al de 5478958, y en local el archivo pasó 4/4 tres veces. No se relanzó |
| [42426437658](https://github.com/estebanojeda0615/SAVIP/actions/runs/42426437658) | `49106f95`, el último commit de código | **success**; **809/809**; **0 fallos en la 1.ª ejecución**; intermitentes: ninguna; 1.er intento del run |
| — | HEAD documental | Ver el mensaje de entrega |
