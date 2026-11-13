# 03 · Diff atómico y reversibilidad (G4.1-G4.4)

## 1. Commits

| Commit | Tipo | Contenido | Comprobación |
|---|---|---|---|
| `5706e85` | Administrativo | `.github/workflows/fase0-pruebas.yml` (+1, la rama en `on.push.branches`) y `.gitignore` (+1, excepción de esta carpeta de docs) | Jobs, setup, perfiles y reintentos sin cambios |
| `fbaa0be` | **G4.1, pruebas** | `tests/test_resultado_horizonte_solicitado.py`: −6 tests, −1 nombre en el import y lápida. `tests/test_presentacion_resultados.py`: −2 tests y lápida. `tests/test_cierre_metodologico.py`: −1 aserción y comentario | Es autoconsistente y está en verde **con la producción aún intacta**. En los 6 archivos afectados: 95 PASS y 1 FAIL **preexistente** (`test_no_hay_modelo_por_horizonte`). Colección: 1 028 (−8) con los mismos 3 errores (`evidencia/g41_afectados.txt`, `evidencia/g41_collect.txt`) |
| `406e1dd` | **G4.2, retiro atómico** | `app_icociv/proyeccion/servicio_proyeccion.py`: **−432 líneas, 0 añadidas**. `tests/test_fase1a_selector_rectangular.py`: guarda adaptada (+4/−3) **en el mismo commit** | Ver §2 |
| (posteriores) | Correcciones de Thermos, si las hay, y documentación | Ver 07 y 09 | — |

## 2. El diff productivo

**Herramienta:** `evidencia/scripts/retirar_2d1.py`, que trabaja por AST y no por rangos de líneas a ciegas. Antes de reescribir el archivo comprueba:
1. que, para cada definición, borra desde su primera línea hasta `end_lineno`, más las **dos líneas en blanco** separadoras;
2. que el módulo resultante tiene **las mismas definiciones de nivel superior menos las seis** (78 → 72), en el mismo orden;
3. que **cada definición y sentencia conservada es idéntica** en `ast.dump` a la original;
4. que los compartidos `_tipo_uso_horizonte` y `_mayor_horizonte_permitido` **siguen presentes**;
5. que **ningún import queda sin uso** por el retiro.

Primero se ensayó sobre una copia: el resultado fue **byte a byte idéntico** al que se aplicó en el clon.

**Definiciones retiradas** (líneas en `8e5a62b`):

| Definición | Líneas | N.º |
|---|---|---|
| `determinar_horizonte_maximo_estadistico` | 3274-3531 | 258 |
| `_serializar_evaluaciones_horizonte` | 3534-3603 | 70 |
| `_item_horizonte_global` | 3606-3622 | 17 |
| `_mayor_horizonte_con` | 3625-3650 | 26 |
| `_ultimo_horizonte_por_clasificacion` | 3687-3714 | 28 |
| `_evidencia_horizonte` | 3717-3737 | 21 |
| **Total** | | **420** de definición, más 12 líneas en blanco separadoras = **432** |

**Se conservan intactos:**
- `_mayor_horizonte_permitido` (L3653-3684 en la base), situado entre `_mayor_horizonte_con` y `_ultimo_horizonte_por_clasificacion`;
- `_tipo_uso_horizonte` (L2362-2373).

El diff (`evidencia/diff_produccion_8e5a62b_406e1dd.patch`, generado con `git diff -U0`, sin líneas de contexto) tiene **dos bloques de borrado** y ninguna línea añadida: L3274-3652 y L3685-3737. En el segundo, `git diff` representa como borradas las dos líneas en blanco anteriores a `_ultimo_…` en lugar de las dos posteriores a `_evidencia_…`; es un texto equivalente.

**Diff completo frente a la base:**

```bash
git diff 8e5a62b 406e1dd -- app_icociv aplicacion.py VERSION packaging requirements-lock.txt requirements-test.txt tests/fixtures scripts pruebas
```

Solo muestra `servicio_proyeccion.py | 432 -`.

**Guarda de la Fase 1A** (`evidencia/scripts/adaptar_fase1a.py`):
- `"determinar_horizonte_maximo_estadistico"` se añade a `eliminados`;
- `retirados` queda en `("_evaluar_horizontes_proyeccion",)`;
- el comentario menciona el lote 2D-1.

## 3. Reversión (no destructiva; no se ejecutó)

La regla es `git revert` de los commits propios en orden inverso. No se reescribe la historia ni se tocan ramas previas.

```bash
git revert <commit-docs> <commits de corrección, si los hay> 406e1dd fbaa0be 5706e85
```

- Revertir solo `406e1dd` devuelve las 6 definiciones y la guarda espiada, y deja en verde el estado de `fbaa0be`.
- Revertir también `fbaa0be` devuelve las 8 pruebas, el import y la aserción de la histórica.

Ninguna comprobación ha motivado la reversión.
