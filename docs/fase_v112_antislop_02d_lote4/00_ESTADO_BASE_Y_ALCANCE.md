# 00 · Estado base y alcance (Fase 2D, lote 2D-4)

**Autorización.** Esteban, 2026-10-29, 20:40 UTC, tarjeta de decisión «¿Autorizo la Fase 2D empezando por el lote 2D-4?», opción «Solo 2D-4». No autoriza 2D-5 ni ningún otro lote.

**Alcance.** El lote 2D-4 de `docs/fase_v112_antislop_02c_registro_historico/06_PLAN_EJECUCION_FASE_2D.md`:
- retirar `seleccionar_modelo_por_evidencia` y sus 9 auxiliares de `app_icociv/estadistica/modelos_interpretables.py`;
- retirar la única prueba esencial que solo exige su existencia.

El plan 06 no asigna a este lote ninguna ficha de `criterios.py`: **`criterios.py` no se toca**.

## Referencias remotas (`git ls-remote`, 2026-10-29, 20:41 UTC)

| Referencia | SHA | Estado |
|---|---|---|
| `maintenance/v1.1.2-fase2c-registro-historico` (base) | `83549e7da6c81c005898e4edf9760af8400f8a5c` | Coincide. CI [40825119810](https://github.com/estebanojeda0615/SAVIP/actions/runs/40825119810): success |
| Fases 2B / 2A / 1B / 1A / 0 | `2f70391` / `1848275` / `c9166c6` / `428fdc0` / `4c46a03` | Sin cambios |
| `main` / `develop/v1.1.2` / tag `v1.1.2-rc.1` | `dfdb3e0` / `6672529` / `08f364b` → `6672529` | Sin cambios |

**Clon nuevo:** `Desktop\SAVIP_V112_FASE2D_LOTE4`, con la rama `maintenance/v1.1.2-fase2d-lote4` creada desde `83549e7`, diff inicial vacío e identidad solo local (Esteban Ojeda, dirección `noreply`). El código de `83549e7` es idéntico al de `7acd0ce`: solo difieren `docs/` y `.gitignore`.

## Línea base (copia limpia de `83549e7`, mismo equipo y entorno que las fases 2A–2C)

| Medida | Resultado |
|---|---|
| `--listar` | esenciales 804 (81 archivos); total 1 059 |
| `pytest --collect-only tests` | 1 059 ids y 3 errores de recolección previos |
| Perfil esencial | **804 PASS**, 0 FAIL, 0 XFAIL y 0 SKIP en el resultado final. **2 pruebas fallaron en la primera ejecución y pasaron al reintento** (ver 04 §3). Golden 29/29 tras el reintento. 1 914 s |
| Huella semántica, dos capturas | 0 diferencias. SHA-256 `d6be699b…`, el mismo de las fases 2A–2C |
| `pruebas/prueba_estadistica.py` (anexo sintético de 40 meses) | Código 0 |
