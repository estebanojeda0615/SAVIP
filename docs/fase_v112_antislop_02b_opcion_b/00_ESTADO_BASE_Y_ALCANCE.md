# 00 · Estado base y alcance

## 1. Referencias remotas verificadas (2026-10-27, 20:00 UTC, `git ls-remote`)

| Referencia | SHA | Estado |
|---|---|---|
| `maintenance/v1.1.2-fase2a-as003` (base) | `1848275e124a0242f57c3582b4cd643c58f0e3f7` | Coincide con el esperado. CI [40454685755](https://github.com/estebanojeda0615/SAVIP/actions/runs/40454685755): success |
| `maintenance/v1.1.2-fase1b-as001` / `fase1a` / `fase0` | `c9166c6` / `428fdc0` / `4c46a03` | Sin cambios |
| `main` / `develop/v1.1.2` | `dfdb3e0` / `6672529` | Sin cambios |
| Tag `v1.1.2-rc.1` | `08f364b` → `6672529` | Sin cambios |
| `maintenance/v1.1.2-fase2b-as003-opcion-b` | — | No existía |

**Clon de trabajo.** Es nuevo: `Desktop\SAVIP_V112_FASE2B_OPCION_B`.
- La rama `maintenance/v1.1.2-fase2b-as003-opcion-b` sale de `1848275`. `HEAD` y `merge-base` valen `1848275`, el diff inicial está vacío y el árbol, limpio.
- La identidad es solo local: `Esteban Ojeda <346522303+estebanojeda0615@users.noreply.github.com>`.

**Ejecuciones.**
- Corren en copias limpias (`git ls-files -co --exclude-standard`) bajo `C:\Pruebas SAVIP\Fase2B\`.
- El equipo y el entorno son los de la Fase 2A (00 §2 de esa fase): Python 3.12.10, `requirements-lock.txt` y `requirements-test.txt`, AMD Family 25.

**Workflow base.** `fase0-pruebas.yml`, con `windows-latest`, Python 3.12.10, el perfil esencial, `timeout-minutes: 150` y un único reintento por prueba fallida en `scripts/pruebas_fase0.py`. Solo se añade la rama nueva al filtro.

## 2. Recuentos antes del cambio (`1848275`)

| Medida | Resultado |
|---|---|
| `--listar` | esenciales 797 · dane 0 · históricas 251 + 3 errores de recolección · gui 13 · total 1 061 |
| `pytest --collect-only tests` | 1 061 ids y 3 errores de recolección previos |
| Perfil esencial | Ver 04 §1 |
| Huella semántica, dos capturas | **0 diferencias**, SHA-256 `d6be699b…` en ambas: el mismo de la Fase 2A |
| Pruebas que citan las 3 funciones | 1 esencial (35/35 en su archivo) y 4 históricos: 11, 13, 16 y 24 ids. El único fallo es `test_cierre_metodologico::test_no_hay_modelo_por_horizonte`, previo |
| `pruebas/prueba_estadistica.py` / `ejemplo_uso.py` (anexo sintético de 40 meses) | Código 0 / código 1, por `ci_lo=None` (AS-028, previo) |

## 3. Alcance cerrado

**Autorizado:**
- retirar `_rmse_global_estable`, `_modelo_consistente_desde_comparativo` y `_modelo_trayectoria_consistente` de `servicio_proyeccion.py`;
- adaptar la prueba esencial `test_la_ruta_productiva_usa_el_selector_rectangular_y_ningun_selector_retirado`;
- tratar caso a caso las pruebas históricas que las citan;
- añadir una rama al workflow;
- documentación y la excepción en `.gitignore`.

**Fuera de alcance, y no se tocó:**
- el resto del subsistema heredado (unas 1 723 líneas tras esta fase), `criterios.py`, `pruebas/` y `packaging/`;
- `VERSION`, los golden y sus tolerancias;
- la ruta vigente (`_sse_exacto`, `_rmse_desde_sse`, `_seleccionar_modelo_rectangular`);
- AS-004, AS-005, AS-007 restante, AS-014, AS-024 y AS-028.
