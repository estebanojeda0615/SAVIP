# 01 · Inventario G1 de referencias

**Árbol analizado.** `1848275`. Búsqueda textual de cada nombre en **todo** el repositorio:
- `app_icociv/`, `aplicacion.py`, `tests/`, `pruebas/`, `scripts/`;
- `packaging/` y `*.spec`, `.github/`, `docs/`;
- los `__init__.py`.

Grafo AST conservador de la Fase 2A (`grafo_as003.py`), recalculado sobre este árbol antes y después del retiro.

## 1. Las tres funciones (`app_icociv/proyeccion/servicio_proyeccion.py` en `1848275`)

| Función | Líneas | Firma | Qué hacía | Efectos secundarios |
|---|---|---|---|---|
| `_rmse_global_estable` | 3128–3157 (30) | `(valores: list[float]) -> float` | `hypot(*valores) / sqrt(n)`: el RMSE sin desbordar, del selector global del 13-08-2026 | Ninguno (función pura) |
| `_modelo_consistente_desde_comparativo` | 3271–3284 (14) | `(backtesting_comparativo, horizontes) -> str \| None` | Delegaba en `seleccionar_modelo_por_rmse_oos_global` | Ninguno |
| `_modelo_trayectoria_consistente` | 3287–3346 (60) | `(evaluaciones: list[dict]) -> str \| None` | Regla retirada el 08-08-2026: RMSE relativo al mejor de cada horizonte, con peso 1/h | Ninguno. Usaba `_numero_finito` y `np` |

**Total:** 104 líneas de definición.

**Imports.** Ningún import era exclusivo de ellas:
- `math`, `np`, `Any` y `Fraction` siguen usándose en el módulo;
- `_numero_finito` y `seleccionar_modelo_por_rmse_oos_global` siguen definidas y referenciadas.

Con `pyflakes`, el módulo da exactamente los mismos avisos antes y después: 5 imports sin uso y 2 variables locales, todos previos (Fase 2A, 02 §6).

## 2. Matriz símbolo → consumidores reales → decisión

| Símbolo | Producción | Scripts (`pruebas/`, `scripts/`) | Docs / fichas `criterios.py` | Pruebas esenciales | Pruebas no esenciales | Decisión |
|---|---|---|---|---|---|---|
| `_rmse_global_estable` | Ninguna llamada | Ninguno | Ninguna ficha. Citas en informes de fases 0–2A | `test_fase1a_selector_rectangular.py:301`: la espía, con `patch.object` | `test_rmse_global_estable.py` (import, T1–T6b) y `test_p0d_rmse_orden_exacto.py` (import, D1) | **ELIMINAR** |
| `_modelo_consistente_desde_comparativo` | Ninguna llamada. Mencionada en el docstring de `seleccionar_modelo_por_rmse_oos_global` (l. 3233) | Ninguno | Ninguna ficha | `test_fase1a_selector_rectangular.py:301` (espía) | `test_seleccion_rmse_global.py:194, 202` y `test_cierre_metodologico.py:428` (`inspect.getsource`) | **ELIMINAR** |
| `_modelo_trayectoria_consistente` | Ninguna llamada. Mencionada en docstrings (l. 2492, 3231, 3356) | Ninguno | Ninguna ficha. El docstring la declaraba parte del «registro de auditoría» de la comparación 1/h frente a RMSE global | `test_fase1a_selector_rectangular.py:302` (espía) | `test_seleccion_rmse_global.py:6` (docstring), `:115` (llamada), `:205`, `:209-211` | **ELIMINAR** (autorización expresa de esta fase) |

## 3. Uso dinámico

**Búsqueda de acceso dinámico** sobre `app_icociv`, `aplicacion.py`, `scripts` y `pruebas`: `globals()`, `getattr(sp|servicio…)`, `importlib`, `__import__`, `eval(` y `exec(`.
- Solo existe `importlib.import_module` en `config/dependencias.py`, que importa **módulos** de terceros.
- Los `exec()` son de diálogos Qt.
- El grafo enlaza también por atributo y por cadena literal exacta (getattr, patch, despacho, Qt). Ninguno de los tres tiene arista desde producción ni desde scripts.

**Reexportaciones.** `app_icociv/proyeccion/__init__.py` solo reexporta `ejecutar_proyeccion`. `packaging/SAVIP.spec` no las nombra.

## 4. Conjunto cerrado y efecto en el grafo

- **Antes** (`1848275`): 820 definiciones, 101 no alcanzables. Las tres tienen `referenciado_por` vacío: ninguna otra definición las llama.
- **Después** (`54f7ccf`): 817 definiciones. Comprobaciones:
  - **ninguna definición nueva** pasa a no alcanzable;
  - **ninguna cambia de alcance** (producción, scripts o pruebas).
  - Solo pierden un referenciante `seleccionar_modelo_por_rmse_oos_global` y `_numero_finito`, que se conservan. La primera la anclan pruebas esenciales, `pruebas/` y la ficha C-SEL-001; la segunda la usa la ruta productiva.
- **El conjunto `{3 funciones}` es cerrado.** Nada de lo que se conserva depende de él.

## 5. Menciones que quedan, deliberadamente

- **Docstrings y comentarios.** Siguen mencionando las funciones en `servicio_proyeccion.py` (l. 2492, 3231–3233 y 3356 de `1848275`) y en los docstrings de módulo de `test_rmse_global_estable.py` y `test_seleccion_rmse_global.py`.
- **Por qué no se tocan:**
  - El prompt limita la producción a «las tres definiciones e imports exclusivos».
  - Son texto histórico que explica por qué se retiró cada regla.
  - Ninguna es una llamada: la prueba `test_la_regla_retirada_ya_no_se_invoca_en_la_ruta_productiva` lo comprueba con 0 apariciones de `_modelo_trayectoria_consistente(`.
- **Pendiente para la limpieza de AS-003 (Fase 2C):** actualizar esos comentarios.
