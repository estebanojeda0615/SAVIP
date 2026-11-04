# 03 · Huella, ids y CI

Las dos ejecuciones se hicieron en el mismo equipo y entorno (00), cada una sobre una copia limpia del árbol fuera del repositorio. La base es `dfcaaa9` y el final, `cae9f04`, que es el último commit de código.

## 1. Perfil esencial

**Comando:** `python scripts/pruebas_fase0.py esenciales --junitxml=resultados/esenciales.xml -o junit_family=xunit2`

| Ejecución | Archivos | Ids | PASS | FAIL | Skip/xfail | Fallos en la 1.ª ejecución | Intermitentes | Golden | AS-001 | Tiempo |
|---|---|---|---|---|---|---|---|---|---|---|
| Local, base `dfcaaa9` | 82 | **812** | 812 | 0 | 0 | 0 | ninguna | 29/29 | 16/16 | 2 003 s |
| **Local, final `cae9f04`** | 82 | **811** | **811** | **0** | **0** | **0** | ninguna | **29/29** | **16/16** | 1 974 s |

**Ids antes y después.** Comparo los JUnit con `comparar_ids_esenciales.py` (Fase 2B), por `(classname, name)` ([`evidencia/comparacion_ids_esenciales.txt`](evidencia/comparacion_ids_esenciales.txt)):

| Concepto | Resultado |
|---|---|
| Solo antes | **1**: `tests.test_cierre_semantico_ps01_ps05::test_ps03_la_escasez_de_evidencia_no_equivale_a_su_inexistencia`, el autorizado |
| Solo después | **0**. W=10 no añade ningún id |
| Estado cambiado | **0** |

El conjunto final es exactamente el de la base menos ese id.

**Recolección** (`pytest --collect-only -q tests`): pasa de **1 067 a 1 066**. Solo falta el id retirado y siguen los **mismos 3 errores históricos** ([`evidencia/coleccion_diff.txt`](evidencia/coleccion_diff.txt)). `scripts/pruebas_fase0.py --listar` da 812 → 811 en esenciales y 242 en históricas, con 3 errores, sin cambios.

## 2. Huella semántica exacta

`docs/fase_v112_antislop_02a_as003/evidencia/huella_semantica.py` cubre 20 casos motor × horizonte, el SSE de los 21 candidatos, H1–H24, RMSErect, MAE(h), economía, empalme, sesiones y rechazos.

| Captura | Resultado |
|---|---|
| Base: dos capturas | 20/20 casos, 0 diferencias |
| **Final frente a base** | **20/20 casos, 0 diferencias exactas** |
| SHA-256 (base 1, base 2 y final) | `d6be699b700b3fa3379c743cc9d0ccbf5c185cacfa228208dbb95c2735370191` en las tres |

No hay excepciones de comparación: en este lote no se autoriza ningún cambio público. Detalle en [`evidencia/huella_resumen.txt`](evidencia/huella_resumen.txt).

## 3. Otras comprobaciones

| Comprobación | Resultado |
|---|---|
| `pip check` | `No broken requirements found.` |
| Compilación de los 3 archivos modificados, importación de los 86 módulos de `app_icociv` y de `aplicacion`, y `VentanaPrincipal` en Qt offscreen | OK. Los cuatro símbolos retirados ya no existen en el módulo |
| Pruebas focalizadas: PS-01…05, 2C y AS-007 | 27/27 tras el commit atómico |
| Los dos archivos de prueba modificados, tras cada corrección | 18/18 |
| Mutación del corte (`MIN_ITERACIONES_WF_ESCENARIO` = 2 o 4) | Detectada con el mensaje del ancla |
| r3 directo | Base y final 21/27, con salida idéntica |
| `git diff --check` en cada commit | Sin avisos |
| Diff de `tests/fixtures/`, `VERSION`, `requirements*`, `packaging/`, `aplicacion.py`, reportes, interfaz, estadística, validación, persistencia, servicios, exportables, `scripts/` y r3 | **Vacío** |
| Archivos o commits de P0-C en el diff contra `dfcaaa9` | **Ninguno**. Los archivos del diff son el workflow, `.gitignore`, `servicio_proyeccion.py`, los dos archivos de prueba y esta carpeta |

## 4. GitHub Actions (`fase0-pruebas`, perfil esencial completo)

| Run | Commit | Resultado |
|---|---|---|
| [41766294797](https://github.com/estebanojeda0615/SAVIP/actions/runs/41766294797) | `a056d9f` (commit atómico) | success · 811/811 · 0 fallos en la 1.ª ejecución · intermitentes: ninguna · 1.er intento |
| [41766989903](https://github.com/estebanojeda0615/SAVIP/actions/runs/41766989903) | `1c8c952` | success · 811/811 · 0 · ninguna · 1.er intento |
| [41767344083](https://github.com/estebanojeda0615/SAVIP/actions/runs/41767344083) | `cae9f04` (último commit de código) | success · 811/811 · 0 · ninguna · 1.er intento |
| — | HEAD documental final | Ver el mensaje de entrega |

Los 29 golden están dentro del perfil esencial. Las intermitentes conocidas (`test_interaccion_fase_3c_a::test_a` y `pdf_sesion`) no aparecieron.
