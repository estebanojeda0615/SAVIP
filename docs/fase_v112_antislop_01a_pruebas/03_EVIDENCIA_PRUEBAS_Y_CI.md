# 03 · Evidencia de pruebas y CI

## 1. Comandos exactos

**Entorno.** Igual en local y en CI: Python 3.12.10 x64 y un venv con las versiones exactas.

```bash
python -m venv .venv-test
```

```bash
.venv-test/Scripts/python -m pip install --no-deps -r requirements-lock.txt
```

```bash
.venv-test/Scripts/python -m pip install --no-deps -r requirements-test.txt
```

**Perfil esencial y recuentos.**

```bash
.venv-test/Scripts/python scripts/pruebas_fase0.py esenciales --junitxml=resultados/esenciales.xml -o junit_family=xunit2
```

```bash
.venv-test/Scripts/python scripts/pruebas_fase0.py --listar
```

**Copia limpia local.** Contiene solo los archivos rastreados y nuevos no ignorados del clon (`git ls-files -co --exclude-standard`). No tiene `docs/` salvo los informes Anti-Slop publicados. Va en `C:\Pruebas SAVIP\Fase1A\<etapa>`, fuera del clon.

## 2. Antes y después

### 2.1 Recuento por perfil (`--listar`)

| Perfil | Antes (`4c46a03`) | Después (rama Fase 1A) |
|---|---|---|
| esenciales | 612 | **782** (+20 de AS-006, +4 de 4I-H, +148 de los 23 archivos migrados, −2 carreras de tiempo al perfil gui) |
| dane | 133 | **0** (no existía dependencia DANE real, ver 02 §1) |
| historicas | 271 + 3 errores de recolección | 251 + 3 errores de recolección |
| gui | 10 | 13 (+ `test_B` de 4G, la principal de 4I-J y `T01B_5` de 01B: carreras de tiempo) |
| **Total** | **1026** | **1046** (+20 nuevas) |

### 2.2 Perfil esencial ejecutado

| Ejecución | PASS | FAIL | XFAIL | ERROR | Notas |
|---|---|---|---|---|---|
| Línea base local, `4c46a03` | 612 | 0 | 0 | 0 | 36 min; escribió 18 archivos en `docs/` |
| CI 40263623668, `4c46a03` (Fase 0) | 612 | 0 | 0 | 0 | success |
| CI [40265487874](https://github.com/estebanojeda0615/SAVIP/actions/runs/40265487874), `ba6a3c9` (AS-006) | 631 | 0 | **1** (AS-001) | 0 | **success** (614 + 17 aisladas) |
| Local, `5f40295` (AS-007 parte 1) | 627 + 17 | 1 | 1 | 0 | Fallo: escritura residual a `docs/fase_3/capturas` (regresión mía, corregida en `50df00e`) |
| CI [40267519823](https://github.com/estebanojeda0615/SAVIP/actions/runs/40267519823), `5f40295` | 627 + 17 | 1 | 1 | 0 | **failure** (mismo fallo) |
| CI [40272254960](https://github.com/estebanojeda0615/SAVIP/actions/runs/40272254960), `50df00e` (784 pruebas en una sesión de pytest) | — | — | — | — | **cancelled** a los 150 min. Se observan 1 F en `test_historial_empalme_fase_4b::test_edicion_borrado…` (pasa 6/6 aislado) y luego una prueba sin terminar. Contaminación entre módulos: se pasa a un proceso por archivo (`cd59281`) |
| **Local, `cd59281`** (copia limpia, un proceso por archivo) | **783** | **0** | **1** (AS-001) | **0** | 80 archivos; «Archivos con fallo: ninguno»; código 0 |
| CI [40373565637](https://github.com/estebanojeda0615/SAVIP/actions/runs/40373565637), `cd59281` | 781 | **2** | 1 | 0 | **failure**, solo en el runner. `test_fase_4i_j_fecha_comun::test_presupuesto…`: `guardar_sesion_actual` → False (guardado tras una carga). `01B::test_T01B_5`: 3 de ≥ 10 muestras del indicador. Ambas pasan en local; pasan al perfil gui en `e341515`, sin cambiar expectativas |
| CI del commit de cierre | PENDIENTE_CI | | | | |

## 3. Golden Masters sin cambios

- `git diff 4c46a03 HEAD -- tests/fixtures/fase0/golden` → **vacío**: los 4 JSON son byte a byte los de `78fe2c1`.
- No se tocaron las tolerancias (`captura.py`: `REL_TOL`, `REL_TOL_OPTIMIZADOR`).
- Las 29 pruebas Golden Master pasaron en todas las corridas anteriores (local y CI) y siguen en el perfil esencial.
- `git diff 4c46a03 HEAD -- app_icociv aplicacion.py packaging VERSION requirements.txt requirements-lock.txt requirements-build.txt` → **vacío**.

## 4. Sin escrituras en `docs/`

| Corrida | Archivos escritos en `docs/` por las pruebas |
|---|---|
| Línea base `4c46a03` | 18 (`fase_3`: 11, `fase_4i_n`: 3, `fase_4i_p`: 2, `fase_4i_j_k`: 2, más la carpeta `fase_3c_a`) |
| Después (copias `despues` y `final`) | **0**: solo existen las carpetas de informes Anti-Slop copiadas del clon (`fase_v112_antislop_00` y, en la copia final, `fase_v112_antislop_01a_pruebas`) |

## 5. Limitaciones

- No se recompiló el EXE (cambio solo de pruebas) ni se publicó ningún ZIP.
- **Perfil histórico:** se ejecutó por archivo para caracterizarlo (02 §4). No corre en el CI, porque mezcla fallos esperados documentados.
- **Perfil gui:** sus pruebas fallan o son intermitentes por diseño (fuentes y carreras de tiempo). La lista manual sigue pendiente de verificación física.
- **Duración del CI:** ~1 h con 782–784 pruebas en `windows-latest`. El límite es de 150 min.
