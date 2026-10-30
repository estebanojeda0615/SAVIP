# 00 · Estado base, plugin Thermos y alcance

## 1. Repositorio y base (comprobado antes de escribir)

| Dato | Valor |
|---|---|
| Remoto | `origin https://github.com/estebanojeda0615/SAVIP.git` (fetch/push) |
| Rama base | `maintenance/v1.1.2-fase2d-lote4` |
| HEAD base local | `6ac158de5edef1f537cbd05ad55c541653e9e099` |
| HEAD base remoto (`git ls-remote`) | `6ac158de5edef1f537cbd05ad55c541653e9e099`: coincide, la rama no avanzó |
| Commit base | `docs(fase2d-lote4): estado base, G1, G5, diff y equivalencia, CI y cierre del lote 2D-4` |
| Autor y confirmador del commit base | `Esteban Ojeda <346522303+estebanojeda0615@users.noreply.github.com>` |
| Rama nueva | `maintenance/v1.1.2-as007-preparacion-2d5-thermos`. Antes de crearla, `git ls-remote` no devolvía nada |
| Identidad local del clon | `Esteban Ojeda <346522303+estebanojeda0615@users.noreply.github.com>`. Sin trailers de coautoría, a petición del propietario |
| HEAD nuevo | En 06 y en el mensaje de entrega; esta carpeta se publica por etapas |

**Aislamiento.** Trabajo en un clon limpio aparte, `Desktop/SAVIP_V112_AS007_2D5_THERMOS`. El repositorio de trabajo del usuario tiene cambios sin confirmar y no se tocó: no hubo `reset`, `clean`, checkout destructivo ni sincronización. Las ejecuciones de referencia se hicieron sobre una copia de la base en `C:/Pruebas SAVIP/AS007/base`, fuera del repositorio.

## 2. Entorno

| Elemento | Valor |
|---|---|
| Sistema | Windows 11 Home 10.0.26200 |
| Python | 3.12.10, venv `C:/Pruebas SAVIP/Fase0/venv-test`, instalado desde `requirements-lock.txt` + `requirements-test.txt` |
| Qt | PySide6 6.11.0 con `QT_QPA_PLATFORM=offscreen` |
| `pip check` | `No broken requirements found.` |
| `scripts/pruebas_fase0.py --listar` en la base | esenciales: 81 entradas, **803 pruebas**, 0 errores · dane: 0 · históricas: 28 entradas, 242 pruebas, **3 errores de recolección** |
| Recolección total en la base | **1 058** recolectadas, **3 errores** históricos: `test_equivalencia_presupuestal_fase_4e_b`, `test_p0c_objeto_publico_sin_intervalo` y `test_p0c_regresion_negativa_c2` |
| Huella semántica en la base | 20/20 casos de motor y **0 diferencias exactas** entre dos capturas. SHA-256 en 03 |

## 3. Thermos

| Comprobación | Resultado |
|---|---|
| Claude Code | `2.1.238 (Claude Code)`. Es anterior a v2.1.292, así que **no** se puede usar `--effort` |
| Estado previo | No estaba instalado |
| Instalación | Desde el marketplace `LayZeeDK/thermos-claude-plugin` (README del plugin), con alcance de usuario. No se añadió a `requirements*`, al empaquetado ni al repositorio |
| `claude plugin list` | `thermos@thermos-claude-plugin · Version: 1.1.0 · Scope: user · Status: ✔ enabled` ([evidencia](evidencia/thermos_plugin_list.txt)) |
| Archivos instalados | `skills/thermos/SKILL.md`, `skills/thermo-nuclear-review/SKILL.md`, `skills/thermo-nuclear-code-quality-review/SKILL.md`, `agents/thermo-nuclear-reviewer.md` y `agents/thermo-nuclear-code-quality-reviewer.md` |
| Ejecución real | **BLOQUEADA en esta sesión.** La sesión en curso arrancó antes de la instalación, así que sus skills y agentes no se cargaron. La vía sin interfaz, `claude -p "/thermos 83549e7...6ac158d"`, terminó en 5 s con código 1 y este error literal: `Not logged in · Please run /login`. La CLI de este equipo no tiene sesión propia: la autenticación es la de la aplicación de escritorio, y no está permitido iniciar sesión por el propietario |

**Consecuencia.** Mientras no se ejecuten realmente las revisiones A y B en una sesión nueva de Claude Code con el plugin cargado, el requisito Thermos queda **pendiente** y el cierre no puede ser APTO (§3 del prompt). Ninguna revisión manual de este informe se presenta como Thermos.

## 4. Alcance

**Archivos que esta fase puede cambiar, y cambia:**
- `tests/test_residuales_auditoria_independiente_r3.py`: cambio conservador para no depender de `tramo_evidencia_oos`;
- `tests/test_as007_contratos_p0c_vigentes.py`: archivo nuevo;
- `scripts/pruebas_fase0.py`: una entrada más en `ESENCIALES`;
- `.github/workflows/fase0-pruebas.yml`: filtro de rama, 1 línea;
- `.gitignore`: excepción de esta carpeta;
- esta carpeta.

**Sin cambios:** `app_icociv/**` (incluidos `tramo_evidencia_oos`, `TRAMO_OOS_*` y `_texto_evidencia_oos`), `aplicacion.py`, `packaging/**`, `VERSION`, `requirements*`, `tests/fixtures/**` (golden y tolerancias), PS-03, las 21 definiciones AS-003, `main`, `develop/v1.1.2`, las ramas anteriores, el tag y el release `v1.1.2-rc.1`.

**No autorizado y no iniciado:** el retiro de 2D-5 o de cualquier otro lote. Tampoco hubo merge, PR, release, EXE ni ZIP.
