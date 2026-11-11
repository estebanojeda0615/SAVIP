# 05 · Equivalencia, pruebas y CI

## 1. Producción y áreas vetadas

| Comprobación | Resultado |
|---|---|
| `git diff --stat 863de0c 06feeb4` sobre `app_icociv/`, `aplicacion.py`, `VERSION`, `requirements*`, `packaging/`, `tests/fixtures/` y `scripts/` | **Vacío** |
| Archivos cambiados (sin docs) | `.github/workflows/fase0-pruebas.yml` (+1, filtro de rama), `.gitignore` (+1) y `tests/test_interaccion_fase_3c_a.py` (+13) |
| Otros tests | Sin cambios |

## 2. Perfil esencial (local, copia de `06feeb4`, `scripts/pruebas_fase0.py esenciales`)

| Concepto | Resultado |
|---|---|
| Ids | **809/809 PASS**, 0 fallos en la 1.ª ejecución, 0 skip/xfail, sin intermitentes (2 059 s) |
| Comparación con el JUnit de la base 2D-2 (`49106f9`, mismo código de producción y mismas pruebas salvo este archivo) | **CONJUNTO IDÉNTICO**: 0 altas, 0 bajas, 0 cambios de estado (`evidencia/comparacion_ids_esenciales.txt`) |
| Los 4 ids de `test_interaccion_fase_3c_a` | PASS, con el mismo id |
| Golden / AS-001 | **29/29** / **16/16** |
| `--listar` | 809 / 214 / 13, igual que en la base |
| `pytest --collect-only tests` | 1 036 tests, con los **mismos 3 errores** históricos |
| `pip check` | OK |

## 3. Equivalencia con la V1.1.2 original y con el lote anterior

| Comprobación | Tipo | Resultado |
|---|---|---|
| Huella semántica (20 casos, SSE de los 21 candidatos, H1-H24, economía, empalme, sesiones y rechazos) | **Ejecutada en esta fase** | 20/20 con **0 diferencias**; SHA-256 `d6be699b700b3fa3379c743cc9d0ccbf5c185cacfa228208dbb95c2735370191` idéntico |
| Oráculo ampliado (66 escenarios) | **Evidencia heredada, no repetida** | `app_icociv` tiene el mismo árbol Git (`f4f0a0c7…`) que el código evaluado en 2D-2. Las dependencias, el lock y los fixtures no cambian. Por tanto valen los resultados de 2D-2: 66/66 frente a la rama anterior y 65/66 frente a la V1.1.2 original, siendo la única diferencia AS-001 |
| Economía, empalme, ICOCIV/ICCP, sesiones y exportables | Sin cambios de código | Golden 29/29, entre ellos los de sesión y exportables, y huella idéntica |

## 4. GitHub Actions (`fase0-pruebas`)

Se registra la primera ejecución y el reintento interno de **todos** los nodos, con atención especial a `test_interaccion_fase_3c_a`. El historial anterior está en 01.

| Run · intento | Commit | Resultado global | 1.ª ejecución | Reintento interno | `test_a` (3c_a) |
|---|---|---|---|---|---|
| [42952282245](https://github.com/estebanojeda0615/SAVIP/actions/runs/42952282245) · 1 | `06feeb4` (último commit de código) | **success** (03:22 → 04:04 UTC) | **809 pruebas, 0 fallos en la 1.ª ejecución** | Ninguno («Intermitentes: ninguna») | PASS en la 1.ª ejecución |
| Ver el mensaje de entrega | HEAD documental | — | — | — | — |

Que un run sea `success` después de un fallo y un reintento **no** se clasifica como prueba estable.
