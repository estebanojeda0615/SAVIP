# 04 · Evidencia del clon limpio y de la integración continua

## 1. Rama publicada

| Dato | Valor |
|---|---|
| Rama | [`maintenance/v1.1.2-fase0-reproducibilidad`](https://github.com/estebanojeda0615/SAVIP/tree/maintenance/v1.1.2-fase0-reproducibilidad), creada desde `develop/v1.1.2` = `6672529` |
| Autor y confirmador de todos los commits | Esteban Ojeda `<346522303+estebanojeda0615@users.noreply.github.com>`, sin trailers ni coautores |
| Push | Normal, solo de esta rama (`refs/heads/maintenance/v1.1.2-fase0-reproducibilidad`). Sin `--force`, sin PR y sin merge |
| Cambios fuera de pruebas, fixtures, CI y documentación | Ninguno: `git diff 6672529 -- app_icociv aplicacion.py packaging VERSION requirements.txt requirements-lock.txt requirements-build.txt` y los scripts de distribución salen vacíos |

| Commit | Contenido |
|---|---|
| [`78fe2c1`](https://github.com/estebanojeda0615/SAVIP/commit/78fe2c15d883dd5366f7d08ffaeb6220246c34d6) | Fixtures y Golden Masters, 3 archivos de prueba, `scripts/pruebas_fase0.py`, workflow, `requirements-test.txt`, excepción de `.gitignore`, ajuste de `test_historial_empalme_fase_4b`, informes 00–03 |
| [`41d35c8`](https://github.com/estebanojeda0615/SAVIP/commit/41d35c8d71f4bbf686ec1df56ff8dfdf28b214ee) | CI en entorno virtual, aislamiento de `test_interfaz_componentes`, `01_INVENTARIO_PRUEBAS.csv` |
| [`d6daa3f`](https://github.com/estebanojeda0615/SAVIP/commit/d6daa3f52c469c48f7204736da58a5b8a9f025ac) | Tolerancia para candidatos con optimizador iterativo, 2 nodos con carreras de tiempo al perfil gui, mensajes completos de diferencias |
| [`edff801`](https://github.com/estebanojeda0615/SAVIP/commit/edff8010291211fdf12c2ebf457155e45183da8f) | Informe 04 y hallazgo entre CPU en 02/03 (CI [40256137859](https://github.com/estebanojeda0615/SAVIP/actions/runs/40256137859): success) |
| Commit final | Informe 05 y cifras finales de 04 |

**Los golden (`tests/fixtures/fase0/golden/*.json`) no cambiaron desde `78fe2c1`.** `git diff 78fe2c1 d6daa3f -- tests/fixtures/fase0/golden` sale vacío.

## 2. Workflow `fase0-pruebas.yml`

- **Disparo:** push a la rama de la Fase 0, o manual.
- **Entorno:** `windows-latest`, Python 3.12.10 x64.
- **Instalación:** `.venv-test` nuevo con `requirements-lock.txt` y `requirements-test.txt` (`--no-deps`), seguido de `pip check`.
- **Pasos:** `--listar`, luego el perfil `esenciales`, y por último sube el JUnit como artefacto.
- **Permisos:** solo `contents: read`; sin secretos.

| Run | Commit | Resultado | Causa / evidencia |
|---|---|---|---|
| [40236320271](https://github.com/estebanojeda0615/SAVIP/actions/runs/40236320271) | `78fe2c1` | **failure** en la instalación (1 min 36 s) | `pip check`: el Python del runner trae `pipx 1.18.4`, que exige `packaging>=26.3`, y el lock fija `26.0`. Se corrigió instalando en `.venv-test`, como hace `build_portatil.ps1` con `.venv-build`. |
| [40240413329](https://github.com/estebanojeda0615/SAVIP/actions/runs/40240413329) | `41d35c8` | **failure**: 588 pasan y 9 fallan, + 17/17 aislados (55 min) | **(1) Diferencias entre CPU** en candidatos con optimizador iterativo (5 escenarios del motor y 2 secciones PDF/DOCX). Ver 02 §5 bis: los ganadores, trayectorias, puntos y cifras económicas coincidieron con 1e-9. **(2)** `test_layout_adaptable_y_temas_sin_cambiar_entrada`: carrera con el temporizador de 60 ms. **(3)** `test_integracion_sesion_con_excel_y_trabajadores_reales`: guarda sin esperar el fin de la carga. |
| [**40245287987**](https://github.com/estebanojeda0615/SAVIP/actions/runs/40245287987) | **`d6daa3f`** | **success: 595 pasan, 2 deseleccionadas, + 17/17 aislados = 612/612** (38 min) | Todos los pasos en verde. `pip check`: «No broken requirements found». Recuento de `--listar` idéntico al local: 612 / 133 / 271 (+3 errores de recolección) / 10. Artefacto `fase0-esenciales-junit` (id 12620220066) |

**Lo que el CI no ejecuta:** los perfiles `dane`, `historicas` y `gui`. Fallan por diseño en un clon limpio o necesitan pantalla física.

## 3. Clon limpio local (Windows 11, `venv-test` con el mismo lock)

| Corrida | Configuración | Resultado | Nota |
|---|---|---|---|
| 1 | `78fe2c1` (antes del aislamiento) | 612 pasan, 2 fallan | Duró 1 h 53 min porque el portátil se suspendió. Fallos: una comprobación de la Fase 0 («±MAE» con «no corresponde a»), ya corregida, y `test_sombras_…` por contaminación entre módulos |
| 2 | Aislando `test_proyecciones_redisenio_visual` | 613 pasan, 1 falla | El contaminante entra por importación transitiva desde otras suites; el espía localizó el origen. Se cambió a aislar la víctima |
| 3 | Aislando `test_interfaz_componentes` | 613 pasan, 1 falla | `test_layout_adaptable_…`: carrera de tiempo, después confirmada en el runner |
| 4 (final) | `d6daa3f` | **595 pasan + 17/17 aisladas = 612/612, código 0** (34 min) | Copia limpia sin `docs/`, misma configuración que el CI verde |

## 4. Reproducción desde cero (cualquier equipo Windows x64)

```bash
git clone -b maintenance/v1.1.2-fase0-reproducibilidad https://github.com/estebanojeda0615/SAVIP.git
```

```bash
python -m venv .venv-test
```

```bash
.venv-test/Scripts/python -m pip install --no-deps -r requirements-lock.txt -r requirements-test.txt
```

```bash
.venv-test/Scripts/python scripts/pruebas_fase0.py esenciales
```

Para reconstruir el ejecutable: `scripts/build_portatil.ps1` (ver 00).
