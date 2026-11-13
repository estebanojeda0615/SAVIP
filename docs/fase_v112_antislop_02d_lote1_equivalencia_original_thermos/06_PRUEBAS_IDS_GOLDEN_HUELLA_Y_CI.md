# 06 · Pruebas, ids, Golden, huella y CI (G6 y G8)

Todas las ejecuciones locales se hicieron sobre copias limpias, sin `.git` y fuera del repositorio: `C:\Pruebas SAVIP\L1D1\base` (`8e5a62b`) y `C:\Pruebas SAVIP\L1D1\final_406e1dd`. Variables: `QT_QPA_PLATFORM=offscreen`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONIOENCODING=utf-8`.

## 1. Perfil esencial

| | Base `8e5a62b` | Final `406e1dd` |
|---|---|---|
| Resultado | 809/809. CI 43136025902 sobre el mismo SHA y JUnit local de AS-028 (mismos árboles de `tests` y `app_icociv`) | **801/801 PASS**, 0 fallos en la 1.ª ejecución, 0 errores, 0 skip/xfail, sin intermitentes, 2 033 s (`evidencia/esenciales_final_resumen.txt`) |
| Golden / AS-001 | 29 / 16 | **29 / 16** |

**Comparación por `(classname, name)`** (`evidencia/comparacion_ids_801.txt`):
- **8 bajas exactas**: las autorizadas (02 §1);
- **0 altas**;
- **0 cambios de estado** en los ids que se conservan.

**Ids que siguen protegidos, todos en PASS:**
- los 9 vigentes de `test_resultado_horizonte_solicitado`;
- la guarda de la Fase 1A, ahora con la ausencia de `determinar_*` exigida;
- los 7 ids de `test_fase2c_contratos_vigentes` y los 12 de `test_pool_calendario_fourier_seasonal`;
- `test_presentacion_resultados::test_exportable_diferencia_recomendado_evaluado_y_limite_operativo` (AS-004);
- los 4 ids de `test_interaccion_fase_3c_a`, con el parche y la espera por condición intactos;
- `test_metodologia_n0_12_h24` completo.

## 2. Perfil histórico (por id)

| | Base `8e5a62b` | Final `406e1dd` |
|---|---|---|
| Ids | 213 | 213 |
| PASS / FAIL (incluye los 3 errores de recolección) | 163 / 50 | **163 / 50** |
| Resumen del runner | 47 fallos en la 1.ª ejecución y 3 errores. `test_fase_4a_c` llega al tiempo agotado (1 200 s); fallan `bghc` (5) y `r3` (5) | **Idéntico** |
| Bajas / altas / cambios de estado | — | **0 / 0 / 0** (`evidencia/comparacion_ids_historicas.txt`) |

- **La histórica de la cascada** (`test_no_queda_cascada_de_prefijo_en_ninguno_de_los_dos_maximos`) pasa de **PASS a PASS**, con el mismo id.
- **`test_no_hay_modelo_por_horizonte`** falla igual en la base y en el final: es preexistente y ajeno a 2D-1.
- Los fallos, el tiempo agotado y los errores son **preexistentes**. Se informan; no se corrigieron ni se ocultaron.

**Nota de ejecución:** la primera captura histórica del final se **descartó**. Tras un reinicio de la sesión de Claude Code, dos procesos escribieron a la vez en la misma carpeta. Se repitió sola y limpia: 2 038 s.

## 3. Script manual

| | Base | Final |
|---|---|---|
| `pytest` | 26 tests: 19 PASS / 7 FAIL | **26 tests: 19 PASS / 7 FAIL**, idénticos id a id (lo verificó Thermos) |
| Ejecución directa | Se detiene en el 2.º test (`ValueError` h=25) | Igual |

## 4. Colección

| | `pytest --collect-only -q tests` |
|---|---|
| Base | 1 036, con los **3 errores históricos** (`fase_4e_b`, `p0c_objeto_publico` y `p0c_regresion_negativa_c2`) |
| Después de G4.1 (`fbaa0be`) | 1 028 (−8), con los mismos 3 |
| Final | **1 028**, con los mismos 3. **0 errores nuevos**. La diferencia (−8) son exactamente las bajas esenciales; el histórico no cambia de recuento |

## 5. Otras comprobaciones

| Comprobación | Resultado |
|---|---|
| Huella semántica | 20/20, **0 diferencias**; SHA `d6be699b…0191` idéntico |
| Golden con tolerancia cero / umbral AS-001 | 0 diferencias / idéntico (04) |
| `compileall` (`app_icociv`, `aplicacion.py`, `tests`, `scripts` y `pruebas`) | Código 0 |
| Importación de 86 módulos y de `VentanaPrincipal` | OK. 2D-1 ausente y compartidos presentes |
| `pip check` | OK |
| `git diff --check` | Sin errores en cada commit |
| AST y `grep` de los símbolos eliminados | 0 referencias residuales (01) |
| Sin `skip`, `xfail`, `mark`, `--deselect`, tolerancias ni Golden nuevos | Confirmado: el diff solo borra pruebas, una aserción y un nombre del import |

## 6. GitHub Actions (`fase0-pruebas`)

| Run e intento | Commit | Resultado | 1.ª ejecución | Reintento interno | JUnit |
|---|---|---|---|---|---|
| [43304324537](https://github.com/estebanojeda0615/SAVIP/actions/runs/43304324537), **intento 1** | `406e1dd` (**último commit de código**) | **success**. Todos los pasos en success, incluida la publicación del JUnit | **801 pruebas, 0 fallos**, 0 errores, 0 omitidas | Ninguno («Intermitentes: ninguna») | Artefacto 13988187695: **801 casos PASS, 29 Golden, 16 AS-001**, idéntico id a id al perfil local (`evidencia/ci/`) |
| HEAD documental | Ver 09 | — | — | — | — |

No hubo ningún relanzamiento ni reintento del workflow. **CI verde no equivale a ausencia demostrada de intermitencias**: es una sola corrida por commit.
