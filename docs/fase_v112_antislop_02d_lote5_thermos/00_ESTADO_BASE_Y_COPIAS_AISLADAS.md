# 00 · Estado base y copias aisladas (lote 2D-5)

## Base y rama

| Dato | Valor |
|---|---|
| Base | `maintenance/v1.1.2-as007-preparacion-2d5-thermos`, commit `dfcaaa9be1f50cbe529daa3483bd23a10344bfdc`, comprobado contra el remoto con `git ls-remote` |
| CI de la base | [41118696947](https://github.com/estebanojeda0615/SAVIP/actions/runs/41118696947): success en el primer intento, 812/812 |
| Rama nueva | `maintenance/v1.1.2-fase2d-lote5-thermos`, creada directamente desde `dfcaaa9`. Antes de crearla, `git ls-remote` no devolvía nada para `maintenance/v1.1.2-fase2d-lote5*` |
| Clon aislado | `Desktop/SAVIP_V112_FASE2D_LOTE5`, clon nuevo con el remoto apuntando a GitHub. Al empezar, `git status` estaba vacío y HEAD era `dfcaaa9` |
| Identidad | `Esteban Ojeda <346522303+estebanojeda0615@users.noreply.github.com>`, configurada en el clon. Sin trailers |
| Entorno | Windows 11 10.0.26200; Python 3.12.10 en el venv `C:/Pruebas SAVIP/Fase0/venv-test` (lock + test); PySide6 6.11.0 offscreen; Claude Code 2.1.238 |
| Thermos | `thermos@thermos-claude-plugin` **1.1.0**, alcance usuario, `✔ enabled`. Ya estaba instalado y no se reinstaló |

## Inspección de la ejecución detenida (P0-C), antes de trabajar

| Lugar | Estado encontrado | Qué se hizo |
|---|---|---|
| Repositorio de desarrollo del usuario `SAVIP_V1_1_REPOSITORIO_INDEPENDIENTE` | Rama `develop/v1.1`, HEAD `1923246`, 162 entradas en `git status` (cambios propios del usuario, anteriores a estas fases), sin stash y con un solo worktree | Nada. No se ejecutó ningún comando de escritura |
| Clon P0-C-R `SAVIP_V112_P0C_RESIDUAL` | Rama `maintenance/v1.1.2-p0c-residual-ic95-thermos`, HEAD `fde777f` ya publicado, `git status` vacío | Se conserva intacto. No se usó como base ni se mezcló |
| Borrador del prompt cancelado `PROMPT_CLAUDE_SAVIP_V112_P0C_CONTRATO_HONESTO.md` | Solo en la carpeta temporal de la sesión. Nunca se ejecutó | Se conserva sin cambios. No forma parte del repositorio |
| Otros clones de fases anteriores (`SAVIP_V112_*`) | Sin tocar | — |

La intervención P0-C-H no llegó a empezar: no hay commits, archivos ni ramas suyos. La rama P0-C-R es de una fase ya cerrada (NO-GO documental). **Ningún archivo ni commit de P0-C entra en el diff de este lote** (verificación final en 03).

## Alcance

**Autorizado y ejecutado:**
- retirar `tramo_evidencia_oos` y las tres constantes `TRAMO_OOS_*` de `servicio_proyeccion.py`;
- trasladar la nota HGRID al docstring de `_texto_evidencia_oos`;
- retirar el id esencial `test_ps03_la_escasez_de_evidencia_no_equivale_a_su_inexistencia`;
- añadir W=10 al test vigente de 2C;
- añadir +1 línea al filtro del workflow y +1 excepción en `.gitignore` para esta carpeta.

**Sin cambios:**
- P0-C, los vectores OOS públicos, RMSE, RMSErect y los demás agregados, y la fórmula del IC95;
- la lógica de proyección, economía, empalme, interfaz, reportes, sesiones y exportables;
- r3, `scripts/pruebas_fase0.py`, `tests/fixtures/**`, `VERSION`, `packaging/` y `requirements*`;
- `main`, `develop/v1.1.2`, el tag y release `v1.1.2-rc.1`, y las ramas anteriores.

**No iniciado:** 2D-1, 2D-2, 2D-3 ni 2D-6.
