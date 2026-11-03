# 00 · Estado base y alcance (P0-C-R)

## Base y rama

| Dato | Valor |
|---|---|
| Rama base | `maintenance/v1.1.2-as007-preparacion-2d5-thermos` |
| HEAD base | `dfcaaa9be1f50cbe529daa3483bd23a10344bfdc`. Coincide con el remoto (`git ls-remote`) |
| CI de referencia | [41118696947](https://github.com/estebanojeda0615/SAVIP/actions/runs/41118696947): success en el primer intento, 812/812 |
| Rama nueva | `maintenance/v1.1.2-p0c-residual-ic95-thermos`. Antes de crearla, `git ls-remote` no devolvía nada para `maintenance/v1.1.2-p0c*` |
| Clon | `Desktop/SAVIP_V112_P0C_RESIDUAL`, clonado desde el clon limpio de AS-007 con el remoto apuntando a GitHub. Al empezar: `git status` vacío y HEAD = `dfcaaa9` |
| Identidad | `Esteban Ojeda <346522303+estebanojeda0615@users.noreply.github.com>`, configurada en el clon. Sin trailers |
| Ramas protegidas | `main` `dfdb3e0…`, `develop/v1.1.2` `6672529…` y el tag `v1.1.2-rc.1` `08f364b…` (sobre `6672529`). Las ramas de fases anteriores no se tocan |

No se tocó el repositorio de trabajo del usuario (`SAVIP_V1_1_REPOSITORIO_INDEPENDIENTE`).

## Entorno

- Windows 11 10.0.26200 y Python 3.12.10, con el venv de las fases anteriores (`requirements-lock.txt` + `requirements-test.txt`).
- PySide6 6.11.0 en modo offscreen.
- Claude Code `2.1.238`: no admite `--effort`.

## Thermos

- `claude plugin list` muestra `thermos@thermos-claude-plugin`, versión **1.1.0**, ámbito usuario, `✔ enabled`.
- La skill `thermos:thermos` y los agentes `thermos:thermo-nuclear-reviewer` y `thermos:thermo-nuclear-code-quality-reviewer` están cargados en esta sesión.
- El resultado de su ejecución está en 05.

## Alcance y resultado del GATE 0

**Autorizado:** investigar el residual P0-C y corregirlo solo si la corrección es completa y no obliga a retirar agregados protegidos.

**Resultado:** **NO-GO por incompatibilidad matemática** (01).

Lo que hay en esta rama:
- documentación;
- scripts de diagnóstico y una prueba adversarial que no se recolecta por defecto (`docs/fase_v112_p0c_residual_thermos/evidencia/`);
- una línea en el filtro del workflow y una excepción en `.gitignore`, imprescindibles para que el CI corra en la rama y la carpeta se versione.

**Sin cambios:**
- `app_icociv/**`, `aplicacion.py`, `packaging/**`, `VERSION`, `requirements*` y `tests/**`;
- el perfil esencial;
- la metodología.

**No iniciado:** 2D-5, ni ningún otro lote.

## Superficie pública examinada

- **Objeto de `ejecutar_proyeccion`:** recorrido completo, con protección de ciclos y sin deduplicar alias.
- **Persistidas o visibles:** sesión JSON (`ControladorPrincipal._proyeccion_serializable`), CSV de reproducibilidad y `horizonte_info.tabla_horizontes`.
- **DOCX, PDF e interfaz:** ya verificados en AS-007. No publican errores por ventana y la interfaz solo muestra conteos de extremos.

Detalle en 02.
