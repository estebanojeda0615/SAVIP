# 04 · G3: diff y commits

## 1. Commits de la rama (base `54789587d0fa7714b4dc464ec48ca8f2ce254611`)

| Commit | Tipo | Contenido |
|---|---|---|
| `be46ca94ec06c199906c858025d55c279b821c4a` | ci | +1 rama en el filtro de `push` del workflow y +1 excepción en `.gitignore`. No cambian jobs, matriz, Python ni permisos |
| `02426ef9e03601c5b4e1789389fb698309e0adf0` | docs | Informe preliminar de G0 (NO-GO previo) |
| `a3cd8e6a7521a23a7cff46e8942c39b9481cd7e5` | test, **preparatorio** | Pruebas sustitutas que pasan con el código antiguo: P0-D sobre el selector vigente y la guardia de umbrales redirigida. Sin cambios de producción |
| `55ba5646faad33c4be458d5cc89e47bb05c2d58a` | refactor, **atómico** | Retira las dos definiciones, cambia el localizador de C-SEL-001 y retira o actualiza las pruebas dependientes |
| `49106f95bacd96699c5233101490586738f5f32d` | test | Correcciones de la 1.ª pasada de Thermos. Solo pruebas. **Último commit de código** |
| HEAD documental | docs | Esta carpeta, completa |

Autor y confirmador de todos los commits: Esteban Ojeda `<346522303+estebanojeda0615@users.noreply.github.com>`, sin trailers.

El commit de correcciones se enmendó una vez en local, antes de cualquier push, para dejar la ruta completa del 03 en las lápidas. No se reescribió nada publicado.

## 2. Archivos (`git diff --numstat 5478958 49106f9`, sin docs)

| Archivo | + | − | Naturaleza |
|---|---|---|---|
| `app_icociv/proyeccion/servicio_proyeccion.py` | 0 | **111** | **Producción.** Retira `_errores_oos_por_par` (L3112-3139, 28 líneas) y `seleccionar_modelo_por_rmse_oos_global` (L3142-3220, 79 líneas), más 4 líneas en blanco separadoras |
| `app_icociv/estadistica/criterios.py` | 1 | 1 | **Producción, metadato no publicado.** Campo `ubicacion` de C-SEL-001 (03 §3) |
| `.github/workflows/fase0-pruebas.yml` | 1 | 0 | Filtro de rama |
| `.gitignore` | 1 | 0 | Excepción para esta carpeta |
| `tests/test_origen_inicial_backtesting.py` | 5 | 76 | Retira el id esencial autorizado y sus 3 auxiliares. Lápida |
| `tests/test_nmin_adversarial.py` | 20 | 26 | Retira el id esencial autorizado. `test_p0a_p0b_p0d_intactos` se conserva con P0-D sobre el selector vigente |
| `tests/test_fase1a_selector_rectangular.py` | 5 | 5 | El par pasa a `eliminados` |
| `tests/test_remediacion_r2_h1_h2_h3_h7.py` | 0 | 1 | Importación sin uso |
| `tests/test_p0d_rmse_orden_exacto.py` | 8 | 152 | Histórica: retira 9 casos y redirige D11 y D12 |
| `tests/test_rmse_global_estable.py` | 0 | 155 | Histórica: archivo borrado (4/4 casos sobre el heredado) |
| `tests/test_seleccion_rmse_global.py` | 9 | 172 | Histórica: retira 13 casos y redirige 1 |
| `tests/test_cierre_metodologico.py` | 5 | 13 | Histórica: retira 1 caso y redirige 1 |
| `tests/test_horizonte_evidencia_reducida.py` | 3 | 45 | Histórica: retira 1 caso; `__main__` sin su llamada |
| `tests/test_integracion_fhg.py` | 5 | 7 | Histórica: `test_p0abd_intactos` usa el helper vigente |

En total: 14 archivos, +63 y −764. **Producción:** 2 archivos, con +1 y −112.

## 3. Restricciones de alcance verificadas

| Comprobación | Resultado |
|---|---|
| `git diff --stat 5478958 49106f9` sobre `app_icociv/` | Solo `servicio_proyeccion.py` (−111) y `criterios.py` (1 línea) |
| `aplicacion.py`, `VERSION`, `packaging/`, `requirements*`, `scripts/`, `pruebas/` y `tests/fixtures/` | **Diff vacío** |
| `_seleccionar_modelo_rectangular`, `_matriz_rectangular_12_24`, `_sse_exacto`, `_rmse_desde_sse` y `_ejecutar_proyeccion_base` | **Sin cambios**: el diff de producción solo borra las líneas 3112-3222 |
| Funciones retiradas en el HEAD | No existen (AST, `hasattr` y búsqueda de texto) |
| Referencias restantes al par fuera de `docs/` | Solo anclas no ejecutables: docstring de Fase 1A, tupla `eliminados`, `HEREDADAS` y lápidas en comentarios |
| Wrappers o reintroducciones bajo otro nombre | Ninguno. La eliminación es neta |
| Imports o constantes huérfanos en producción | Ninguno (AST frente a la base, `evidencia/imports_huerfanos.txt`). pyflakes, ejecutado por Thermos, confirma que no hay avisos nuevos |
| `git diff --check` en cada commit de código | Sin avisos |

**Reversión:** `git revert 49106f9 55ba564 a3cd8e6`. La rama base no se ha modificado.
