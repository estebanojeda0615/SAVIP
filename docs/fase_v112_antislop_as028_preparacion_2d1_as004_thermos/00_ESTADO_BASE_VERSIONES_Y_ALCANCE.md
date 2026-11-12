# 00 · Estado base, versiones y alcance: AS-028 (preparación de 2D-1) y diagnóstico AS-004

## 1. Base y rama

| Dato | Valor |
|---|---|
| Repositorio | `estebanojeda0615/SAVIP` |
| Base | `102f194cfffc4f92d57006f4b9a0b80eb0b225d1` (`maintenance/v1.1.2-auditoria-gui-3ca-thermos`), con CI [42956928286](https://github.com/estebanojeda0615/SAVIP/actions/runs/42956928286) en `success` sobre ese SHA. Cierre de la fase GUI en `docs/fase_v112_antislop_auditoria_gui_3ca_thermos/07_INFORME_CIERRE_GUI_3CA.md` (APTO) |
| Rama nueva | `maintenance/v1.1.2-as028-preparacion-2d1-as004-thermos`, creada **exactamente** desde `102f194` |
| Clon de trabajo | `C:\Users\Esteban\Desktop\SAVIP_V112_AS028_2D1`, nuevo e independiente |
| Copias de prueba | `C:\Pruebas SAVIP\A28D1\base` (`102f194`) y `C:\Pruebas SAVIP\A28D1\final` (último commit de código). Son copias limpias sin `.git` y fuera del repositorio |
| Identidad de los commits | Esteban Ojeda `<346522303+estebanojeda0615@users.noreply.github.com>` como autor y committer, sin trailers |

**Por qué se continúa la línea acumulada.** La arquitectura de lotes de la Fase 2C proponía bases aisladas. Aquí se continúa **a propósito** la línea ya validada (2D-5 → AS-028/2D-2 → 2D-2 → 3c_a), por dos motivos:
- el prompt lo exige;
- `102f194` ya contiene el retiro de 2D-2 (`49106f9`), aprobado y equivalente a la original salvo AS-001, y el parche de la prueba GUI 3c_a.

Partir de otra base reintroduciría código ya retirado o la intermitencia ya corregida.

**Verificación al empezar** (`git ls-remote`, 2026-11-11 18:3x UTC):

| Ref | SHA | Coincide |
|---|---|---|
| `maintenance/v1.1.2-auditoria-gui-3ca-thermos` | `102f194cfffc…` | Sí |
| `maintenance/v1.1.2-fase2d-lote2-equivalencia-original-thermos` | `863de0c1745a…` | Sí (no se tocó) |
| `main` | `dfdb3e046126…` (V1.1.1) | Sí |
| `develop/v1.1.2` | `66725293f304…` (V1.1.2 original) | Sí |
| tag `v1.1.2-rc.1` | `08f364b`, que apunta a `6672529` | Sí |
| Rama nueva | No existía | — |

Otras comprobaciones:
- En la base, `git status` estaba limpio.
- El árbol `app_icociv` de `102f194` es `f4f0a0c752e9…`, **idéntico** al del último commit productivo de 2D-2 (`49106f9`).
- No se tocó el repositorio de desarrollo del usuario (`SAVIP_V1_1_REPOSITORIO_INDEPENDIENTE`, con cambios locales propios), ni los clones ni las carpetas de pruebas de fases anteriores.

## 2. Referencias de equivalencia

| Referencia | Identificador | Uso en esta fase |
|---|---|---|
| **V1.1.2 ORIGINAL empaquetada** | Fuente `6672529`; tag `v1.1.2-rc.1`; ZIP de la release con SHA-256 `cee5897f82753d5ca1b6650023da81384bc1bfb50b5a5468ddbb26e5e7a94600` | Oráculo principal **de solo lectura**. La correspondencia del EXE con la fuente (87/87 módulos `app_icociv` más `aplicacion`, idénticos en bytecode a `6672529`) se demostró en el lote 2D-2 (`docs/fase_v112_antislop_02d_lote2_equivalencia_original_thermos/`). **En esta fase no se ejecutó el EXE**: se ejecuta su fuente |
| V1.1.1 | `dfdb3e0` | Referencia secundaria (continuidad histórica) |
| Fase anterior aprobada | `102f194` | Exige cero diferencias |
| **AS-001** | Única excepción autorizada | La original aborta con `OverflowError` ante una SSE extrema; Anti-Slop calcula con `_rmse_desde_sse`. **No se toca ni se amplía en esta fase** |

## 3. Versiones y entorno

| Herramienta | Versión |
|---|---|
| Python (`venv-test`) | 3.12.10 |
| PySide6 / numpy / pandas / statsmodels | 6.11.0 / 2.4.2 / 2.3.3 / 0.14.6 |
| `pip check` | «No broken requirements found» |
| `requirements-lock.txt` / `requirements-test.txt` (SHA-256) | `ab30ed94…bb3f` / `c3c5679e…41e5`, sin cambios |
| Claude Code | 2.1.238, sin `--effort` |
| Thermos | `thermos@thermos-claude-plugin` 1.1.0, alcance usuario, commit `dc8791f8`. Ya estaba instalado y no se reinstaló |
| Variables | `QT_QPA_PLATFORM=offscreen`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONIOENCODING=utf-8` |

## 4. Línea base medida sobre `102f194` (G0)

| Comprobación | Resultado | Evidencia |
|---|---|---|
| Perfil esencial | **809/809 PASS**: 82 archivos, 0 fallos en la 1.ª ejecución, 0 errores, 0 skip/xfail, sin intermitentes. **Conjunto idéntico** al de la fase 3c_a: 0 altas, 0 bajas y 0 cambios de estado | `evidencia/esenciales_base_resumen.txt`, `evidencia/comparacion_ids_base_vs_3ca.txt` |
| Golden / AS-001 | 29/29 y 16/16, dentro del perfil esencial | Ídem |
| Huella semántica | 20/20 casos, **0 diferencias**. SHA-256 `d6be699b700b3fa3379c743cc9d0ccbf5c185cacfa228208dbb95c2735370191`, idéntico | `evidencia/huella_base.txt` |
| `--listar` | 809 esenciales / 214 históricas (3 errores de recolección) / 13 GUI | `evidencia/base_listar.txt` |
| `pytest --collect-only -q tests` | 1 036 tests, con los **3 errores históricos**: `test_equivalencia_presupuestal_fase_4e_b`, `test_p0c_objeto_publico_sin_intervalo` y `test_p0c_regresion_negativa_c2` | `evidencia/base_collect.txt` |
| Script con pytest | **29 tests: 21 PASS / 8 FAIL**, en 136 s | `evidencia/script_base_pytest.xml`, `evidencia/script_base_fallos.txt` |
| Script, ejecución directa | Se detiene en el 2.º test de `main()` (`test_horizonte_25_estable…`, `ValueError` por h=25), con código 1 | `evidencia/script_base_directo.txt` |
| Escrituras en disco | Ninguna: el árbol queda igual antes y después de las capturas | `evidencia/escrituras_base.txt` |
| Oráculo de 66 escenarios | Se recuperaron sus scripts (`docs/fase_v112_antislop_02d_lote2_equivalencia_original_thermos/evidencia/scripts/`) y el arnés externo (`C:\Pruebas SAVIP\L2\oraculo`, `arnes_sha256.txt`), sin cambios. Se **volvió a ejecutar** en esta fase (07) | 07 |
| Inventario AST y textual | Las 6 definiciones de 2D-1 suman **420 líneas**, igual que el plan 2C | 06 §1, `evidencia/grafo_102f194_2d1.json` |

## 5. Alcance

| Autorizado | No autorizado |
|---|---|
| Inventariar las 29 pruebas del script y analizar las 3 de 2D-1 aserción por aserción | `app_icociv/**`, `aplicacion.py`, `VERSION`, `packaging/**`, `requirements*`, `tests/fixtures/**`, Golden y `scripts/` |
| Retirar **solo** esas 3 pruebas del script y sus llamadas en `main()`, si se justifica, dejando una lápida | Las otras 26 pruebas: sus aserciones, el orden de `main()`, drift/holt y los 7 FAIL históricos restantes |
| Diagnosticar AS-004 **sin editar** `generador_reportes.py` | Retirar 2D-1 de producción, ejecutar AS-004, 2D-3, 2D-6, AS-007 o AS-024 |
| Una entrada `push` en el workflow, una excepción en `.gitignore` y la documentación | Cualquier prueba de `tests/` (esenciales e históricas): **solo inventario** |
| — | P0-C/IC95 (cancelado), cambios de CI distintos de la rama, `skip`/`xfail`/reintentos, merge, PR, tag, release, EXE, ZIP y VERSION |

## 6. Orden real de los pasos

1. G0 completo sobre `102f194`: perfil esencial, capturas, grafo y sonda AS-004.
2. Análisis G1 y edición del script en el clon, todavía sin commit.
3. Commits locales `19c4649` (CI y `.gitignore`), `5133abc` (baja de las 3 pruebas) y `7993060` (restauración del auxiliar, por la nota de control sobre el alcance estricto).
4. **Inventario G3 cerrado** con los estados base por id. Solo después, push de `7993060` (19:24:57 UTC) y su CI.
5. G4 y G5 locales en segundo plano. Thermos, 1.ª pasada.
6. Commit `56d9562`: corrección de la lápida pedida por Thermos (solo comentarios). Push y CI. **Es el último commit de código.**
7. El CI de `56d9562` (run 43087996118) falla en su intento 1 por la infraestructura de artefactos. Se detiene por cuota de uso y se espera la decisión del propietario.
8. 2026-11-12, 00:47 UTC: el propietario autoriza **un único** relanzamiento. El intento 2 termina en success (07 §6).
9. Correcciones de las herramientas de evidencia (hallazgos de calidad de Thermos), sondas finales y Thermos, 2.ª pasada. Esta pasada se relanzó completa, porque la primera ejecución se detuvo por cuota.
10. Commit documental, push y CI.
