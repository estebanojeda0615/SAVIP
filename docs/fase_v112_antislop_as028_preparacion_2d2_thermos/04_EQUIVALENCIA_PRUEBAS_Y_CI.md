# 04 · Equivalencia de pruebas y CI

Las dos ejecuciones se hicieron en el mismo equipo y entorno (00), cada una sobre una copia limpia del árbol, fuera del repositorio.
- **Base:** `56c75a6`.
- **Final:** `5acb09f`, el último commit de código.

## 1. Perfil esencial

**Comando:** `python scripts/pruebas_fase0.py esenciales --junitxml=resultados/esenciales.xml -o junit_family=xunit2`

| Ejecución | Archivos | Ids | PASS | FAIL | Skip/xfail | Intermitentes | Golden | AS-001 | Tiempo |
|---|---|---|---|---|---|---|---|---|---|
| Local, base `56c75a6` | 82 | **811** | 811 | 0 | 0 | ninguna | 29/29 | 16/16 | 2 071 s |
| **Local, final `5acb09f`** | 82 | **811** | **811** | **0** | **0** | ninguna | **29/29** | **16/16** | 1 993 s |

**Comparación de ids** por `(classname, name)`, con `comparar_ids_esenciales.py` de la fase 2B (`evidencia/comparacion_ids.txt`):

| Concepto | Resultado |
|---|---|
| Solo en la base | **0** |
| Solo en el final | **0** |
| Estado cambiado | **0** |

El conjunto es **idéntico**. No se retira ni se añade ningún id esencial; el único test retirado pertenece al script histórico, que no forma parte del perfil.

Golden y AS-001 se cuentan en los JUnit: 29 casos en los archivos `*golden*` y 16 ids `as001`, en verde tanto en la base como en el final.

## 2. Huella semántica exacta

`docs/fase_v112_antislop_02a_as003/evidencia/huella_semantica.py` cubre:
- 20 casos motor × horizonte;
- el SSE de los 21 candidatos;
- H1–H24, RMSErect y MAE(h);
- economía, empalme, sesiones y rechazos.

| Captura | Resultado |
|---|---|
| Base, frente a la huella del lote 2D-5 | 20/20, 0 diferencias |
| **Final frente a base** | **20/20, 0 diferencias exactas** |
| SHA-256 de la base y del final | `d6be699b700b3fa3379c743cc9d0ccbf5c185cacfa228208dbb95c2735370191` en los dos, igual al de 2D-5 |

No hay excepciones: no se cambia producción. Evidencia en `evidencia/huella_base.txt` y `evidencia/huella_final.txt`.

## 3. Otras comprobaciones

| Comprobación | Base | Final |
|---|---|---|
| `pytest --collect-only -q tests` | 1 066 y 3 errores históricos | **1 066 y los mismos 3** (`evidencia/coleccion_*.txt`) |
| `scripts/pruebas_fase0.py --listar` | 811 / 242 / 13 | **Igual** |
| Script histórico, con pytest | 30 tests: 22 PASS / 8 FAIL | **29 tests: 21 PASS / 8 FAIL, con los mismos 8.** La única baja es el test retirado (03 §5) |
| Script histórico, ejecución directa | Se detiene en el 2.º test, código 1 | **Igual** |
| `pruebas/prueba_estadistica.py` | `FileNotFoundError` sin Excel, código 1 | **Salida idéntica** |
| Escrituras en disco del script y de `prueba_estadistica` | Ninguna | **Ninguna** |
| `compileall` del script, `app_icociv` y `aplicacion.py` | — | Código 0 |
| Importación de los 86 módulos de `app_icociv` y de `aplicacion`, y `VentanaPrincipal` en Qt offscreen | — | OK. El par de 2D-2 sigue presente en producción |
| `git diff --check` en cada commit | — | Sin avisos |
| Diff de `app_icociv/`, `aplicacion.py`, `VERSION`, `packaging/`, `requirements*`, `tests/` y `scripts/` | — | **Vacío** |
| Diff de `pruebas/ejemplo_uso.py` y `pruebas/prueba_estadistica.py` | — | **Vacío** |

## 4. GitHub Actions (`fase0-pruebas`, perfil esencial completo)

| Run | Commit | Resultado |
|---|---|---|
| [41948898532](https://github.com/estebanojeda0615/SAVIP/actions/runs/41948898532) | `5acb09f` (último commit de código) | success, **811/811**, en el 1.er intento del run. 1 fallo en la 1.ª ejecución que pasó al reintento: `test_interaccion_fase_3c_a.py::test_a_acciones_geometria_click_teclado_y_senales`, con `QSignalSpy.count() == 2` frente al 1 esperado en `:140`. Es la intermitente GUI ya conocida de lotes anteriores (2D-5, 05 §4). No guarda relación con el diff: el CI no ejecuta `pruebas/`, el archivo y la interfaz no cambian, y en local pasó tanto en la base como en el final. Extracto en `evidencia/ci_41948898532_intermitente.txt` |
| — | HEAD documental | Ver el mensaje de entrega |

El workflow no ejecuta `pruebas/`. El script histórico se valida en local (§3 y 03 §5).

## 5. Orden de publicación

- **Primer push:** solo los commits de código, hasta `5acb09f`. Así el CI corre sobre el último commit de código.
- **Segundo push:** la carpeta de documentación, en cuanto ese CI terminó.

Entre los dos pushes, la ruta del 03 que cita la lápida no existió en GitHub durante unos minutos. Fue la condición de cierre del revisor de calidad de Thermos y queda cumplida en el HEAD documental.
