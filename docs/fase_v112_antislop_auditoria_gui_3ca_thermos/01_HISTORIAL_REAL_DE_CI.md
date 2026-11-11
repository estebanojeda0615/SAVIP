# 01 · Historial real de CI de `test_interaccion_fase_3c_a::test_a`

**Workflow:** `fase0-pruebas.yml` en `windows-latest`. El runner esencial ejecuta los tests por archivo y reintenta **una vez**, dentro del mismo run, los ids que fallan.

**Criterio de esta auditoría:** cada fallo cuenta como fallo de primera ejecución, aunque pase en el reintento.

Ids completos: `tests/test_interaccion_fase_3c_a.py::test_a_acciones_geometria_click_teclado_y_senales`. En los fallos, la aserción es siempre `assert toggle_spy.count()==1 and not v.navegacion.esta_contraida()` → `assert (2 == 1)`, en la línea 140 del test de la base.

| # | Run · intento | Fecha (UTC) | Commit (código evaluado) | 1.ª ejecución | Reintento interno | Resultado del run |
|---|---|---|---|---|---|---|
| 1 | [41948898532](https://github.com/estebanojeda0615/SAVIP/actions/runs/41948898532) · 1 | 05-11-2026 | `5acb09f` (AS-028) | **FALLÓ** | pasó | success, con 1 intermitente declarada |
| 2 | [41954109682](https://github.com/estebanojeda0615/SAVIP/actions/runs/41954109682) · 1 | 05-11-2026 | `5478958` (AS-028) | pasó | — | success |
| 3 | [42108454515](https://github.com/estebanojeda0615/SAVIP/actions/runs/42108454515) · 1 | 05-11-2026 | `02426ef` (2D-2; código = 5478958) | **FALLÓ** | **FALLÓ** | failure |
| 4 | [42426437658](https://github.com/estebanojeda0615/SAVIP/actions/runs/42426437658) · 1 | 07/08-11-2026 | `49106f9` (2D-2, último código) | pasó | — | success |
| 5 | [42502142744](https://github.com/estebanojeda0615/SAVIP/actions/runs/42502142744) · 1 | 08-11-2026 | `d7cc472` (2D-2 docs; código = 49106f9) | **FALLÓ** | **FALLÓ** | failure |
| 6 | [42502142744](https://github.com/estebanojeda0615/SAVIP/actions/runs/42502142744) · 2 | 09-11-2026 | `d7cc472` (único relanzamiento autorizado) | pasó | — | success |

**En total:** 3 fallos de 1.ª ejecución en 6 ejecuciones registradas, y en 2 de ellas falló también el reintento interno. No se extrapola ninguna tasa poblacional a partir de esas cifras.

Los runs de esta fase se añaden en 05 §4 sin sobrescribir este registro.
