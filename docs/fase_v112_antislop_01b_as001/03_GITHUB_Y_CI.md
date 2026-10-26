# 03 · GitHub y CI

## 1. Rama, commits e identidad

**Rama:** `maintenance/v1.1.2-fase1b-as001`, creada desde `428fdc0` (Fase 1A). Es la única rama publicada en esta fase.

| Commit | Contenido | Archivos |
|---|---|---|
| `8159d52` | fix(AS-001): `_rmse_desde_sse` en el selector rectangular, retiro del `xfail` y 15 pruebas nuevas | `app_icociv/proyeccion/servicio_proyeccion.py`, `tests/test_fase1a_selector_rectangular.py` |
| `df4fb16` | ci: añade la rama de la Fase 1B al filtro `on.push.branches` | `.github/workflows/fase0-pruebas.yml` (+1 línea) |
| `c42cbbf` | test(AS-001): horizonte consultado 1/11/24 con candidato divergente | `tests/test_fase1a_selector_rectangular.py` |
| commit de documentación | informes 00–04, evidencias y excepción en `.gitignore` | `docs/fase_v112_antislop_01b_as001/**`, `.gitignore` |

**Identidad.** Autor y confirmador de todos los commits: `Esteban Ojeda <346522303+estebanojeda0615@users.noreply.github.com>`. No hay trailers `Co-authored-by`. La identidad se configuró solo en el clon de la fase.

**Workflow.** Solo se añadió la rama al filtro. No cambian:
- los pasos;
- el perfil;
- `timeout-minutes: 150`;
- la política de un único reintento de `scripts/pruebas_fase0.py`.

## 2. GitHub Actions

| Run | Commit | Resultado | Pruebas | Fallos | XFAIL | Intermitentes | Duración |
|---|---|---|---|---|---|---|---|
| [40415465901](https://github.com/estebanojeda0615/SAVIP/actions/runs/40415465901) | `df4fb16` (corrección + workflow) | **success** | 797 | 0 | 0 | **ninguna** | 60 min |

**Lista «Intermitentes».** El script imprime esta línea en cada run: son las pruebas que fallaron y pasaron al reintento. En este run fue «ninguna»; no hubo reintentos ni fallos en la primera ejecución.

**Entorno.** `pip check`: «No broken requirements found».

**Run del HEAD final.** Lo dispara el push del commit de documentación, que incluye `c42cbbf`. Su resultado se informa en el mensaje de entrega. Si saliera en rojo, la fase no se declararía aprobada.

## 3. Diff de alcance (contra `428fdc0`)

```
git diff 428fdc0 --stat -- app_icociv aplicacion.py packaging VERSION requirements.txt requirements-lock.txt requirements-build.txt
 app_icociv/proyeccion/servicio_proyeccion.py | 23 ++++++++++++++++++++++-
 1 file changed, 22 insertions(+), 1 deletion(-)

git diff 428fdc0 --stat -- tests/fixtures/fase0
 (vacío)
```

**Cambios en producción (3 en total):**
1. `import Decimal, localcontext`;
2. la línea del RMSE llama a `_rmse_desde_sse`;
3. la función nueva `_rmse_desde_sse`.

**No se tocaron** modelos, fórmulas, `_sse_exacto`, el orden, snapshots, exportables, recursos visuales, interfaz, sesiones ni `VERSION`.

## 4. Lo que no se tocó en GitHub

- `main` (`dfdb3e0`), `develop/v1.1.2` (`6672529`), `maintenance/v1.1.2-fase0-reproducibilidad` (`4c46a03`) y `maintenance/v1.1.2-fase1a-as006-as007` (`428fdc0`);
- el tag y el Release `v1.1.2-rc.1` y el ZIP portátil.

**Operaciones no realizadas:** merge, PR, tag, release, force-push, `reset --hard` y `clean`.

## 5. Enlaces

| Qué | Enlace |
|---|---|
| Rama | https://github.com/estebanojeda0615/SAVIP/tree/maintenance/v1.1.2-fase1b-as001 |
| Comparación con la Fase 1A | https://github.com/estebanojeda0615/SAVIP/compare/maintenance/v1.1.2-fase1a-as006-as007...maintenance/v1.1.2-fase1b-as001 |
| Runs de la rama | https://github.com/estebanojeda0615/SAVIP/actions?query=branch%3Amaintenance%2Fv1.1.2-fase1b-as001 |
