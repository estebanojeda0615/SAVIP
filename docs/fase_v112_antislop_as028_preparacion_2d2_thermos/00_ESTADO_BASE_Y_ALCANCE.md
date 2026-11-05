# 00 · Estado base y alcance de AS-028

## 1. Árbol y base

| Dato | Valor |
|---|---|
| Base | `56c75a6f0c47f01f5cdbca250986e6359b97de03` (`maintenance/v1.1.2-fase2d-lote5-thermos`, lote 2D-5 APTO, CI [41773840522](https://github.com/estebanojeda0615/SAVIP/actions/runs/41773840522)) |
| Rama nueva | `maintenance/v1.1.2-as028-preparacion-2d2-thermos`, creada desde la base |
| Clon de trabajo | `C:\Users\Esteban\Desktop\SAVIP_V112_AS028`, independiente |
| Copias de prueba | `C:\Pruebas SAVIP\A28\base` (base) y `C:\Pruebas SAVIP\A28\final` (último commit de código). Son copias limpias sin `.git`, fuera del repositorio |
| Identidad de los commits | Esteban Ojeda `<346522303+estebanojeda0615@users.noreply.github.com>`, sin trailers |

**Protección del trabajo:**
- No se tocaron el repositorio de desarrollo del usuario (`SAVIP_V1_1_REPOSITORIO_INDEPENDIENTE`, `1923246`, con cambios locales propios), los clones de fases anteriores ni sus carpetas de pruebas.
- No hubo ZIP, EXE, merge, PR, tag ni release.

**Ramas remotas al empezar** (`git ls-remote`):

| Ref | SHA |
|---|---|
| `main` | `dfdb3e0` |
| `develop/v1.1.2` | `6672529` |
| `maintenance/v1.1.2-fase2d-lote5-thermos` | `56c75a6` |
| tag `v1.1.2-rc.1` | `08f364b`, que apunta a `6672529` |

## 2. Versiones

| Herramienta | Versión |
|---|---|
| Python (`venv-test`) | 3.12.10 |
| Claude Code | 2.1.238 (sin `--effort`) |
| Thermos | `thermos@thermos-claude-plugin` 1.1.0, alcance usuario. Ya estaba instalado y no se reinstaló |
| Entorno de pruebas | `QT_QPA_PLATFORM=offscreen`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONIOENCODING=utf-8` |

## 3. Línea base medida (G0, sobre `56c75a6`)

| Comprobación | Resultado | Evidencia |
|---|---|---|
| Perfil esencial | **811/811 PASS**: 82 archivos, 0 fallos, 0 skip/xfail, sin intermitentes, 2 071 s. Incluye golden 29/29 y AS-001 16/16 | `evidencia/esenciales_base_resumen.txt` |
| `--listar` | 811 esenciales, 242 históricas (3 errores de recolección) y 13 GUI: 1 066 en total | `evidencia/base_listar.txt` |
| `pytest --collect-only -q tests` | 1 066 recogidos y **3 errores históricos**: `test_equivalencia_presupuestal_fase_4e_b`, `test_p0c_objeto_publico_sin_intervalo` y `test_p0c_regresion_negativa_c2` | `evidencia/coleccion_base.txt` |
| Huella semántica | 20/20 casos, **0 diferencias** frente a la huella del lote 2D-5 | `evidencia/huella_base.txt` |
| Script, con pytest | **22 PASS / 8 FAIL** en 151 s, igual que el registro histórico de la fase 2C. Fallos: 3 `ValueError` por pedir h=25 (contrato H=24) y 5 aserciones sobre textos de informes antiguos | `evidencia/script_base_pytest.xml` |
| Script, ejecución directa | Se detiene en el 2.º test de `main()` (`horizonte_25_estable`, `ValueError`) con código 1, en 22 s | `evidencia/script_base_directo.txt` |
| `pruebas/prueba_estadistica.py` | Sin argumento: `FileNotFoundError` («Indique la ruta de un archivo .xlsx/.xlsb»), código 1. Es su comportamiento previo, porque exige un Excel | `evidencia/prueba_estadistica_base.txt` |
| Escrituras en disco | Ejecutar el script (con pytest y directo) y `prueba_estadistica` no deja ningún archivo nuevo ni borrado. El script solo escribe en `tempfile` | `evidencia/escrituras_disco.txt` |

## 4. Alcance

| Autorizado | No autorizado |
|---|---|
| Revisar los 30 tests del script y escribir el inventario | `app_icociv/**`, `aplicacion.py`, `VERSION`, `packaging/**`, `requirements*`, `tests/fixtures/**` |
| Retirar **solo** el test del selector heredado, con lápida y su línea de `main()` | Corregir los 8 fallos históricos, añadir `skip`/`xfail` o cambiar expectativas |
| Un archivo de `tests/` solo si hay un contrato vigente sin cobertura (no hizo falta) | Tocar los 3 tests de 2D-1, `ejemplo_uso.py` o `prueba_estadistica.py` |
| Una línea en el workflow, otra en `.gitignore` y la documentación | Retirar `seleccionar_modelo_por_rmse_oos_global` o `_errores_oos_por_par` (eso es 2D-2) |
| — | P0-C (cancelado), `criterios.py` (C-SEL-001/AS-024) y `generador_reportes.py` (AS-004) |
