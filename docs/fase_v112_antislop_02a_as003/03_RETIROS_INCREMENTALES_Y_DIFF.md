# 03 · Retiros incrementales y diff

## 1. Lotes

| Lote | Commit | Qué | Archivos | Líneas | Estado |
|---|---|---|---|---|---|
| 1a | `d7429df` | 5 definiciones sin ninguna referencia y los 6 imports que solo ellas usaban | `app_icociv/proyeccion/servicio_proyeccion.py` | −185 | Hecho, verificado y publicado |
| 1b | `c6ca863` | `resumen_validacion`, sin ninguna referencia | `app_icociv/estadistica/validacion_series.py` | −15 | Hecho, verificado y publicado |
| CI | `81a8247` | Añade la rama al filtro `on.push.branches` del workflow | `.github/workflows/fase0-pruebas.yml` | +1 | Hecho. Sin cambios en pasos, perfil, tiempo ni reintentos |
| 2 (opción B) | — | `_rmse_global_estable`, `_modelo_consistente_desde_comparativo` y `_modelo_trayectoria_consistente` (104 líneas). Exige adaptar la prueba esencial de la Fase 1A que espía los nombres retirados | — | — | **No ejecutado**: pendiente de decisión de Esteban |
| Resto | — | Selector antiguo, evaluación y clasificación de horizontes, salvaguarda y `seleccionar_modelo_por_evidencia` (unas 1 800 líneas) | — | — | **DEFERIDO** (02 §4) |

No hubo reversiones.

**Herramienta.** El retiro se hizo con [`evidencia/retirar_definiciones.py`](evidencia/retirar_definiciones.py). Borra cada `def` por nombre exacto, usando `lineno`/`end_lineno` del AST, más las líneas en blanco que le siguen; si la definición era la última, no deja líneas en blanco al final. Falla si el nombre no existe o está repetido, y vuelve a parsear el resultado.

## 2. Definiciones retiradas (Lote 1)

| Definición | Origen en `c9166c6` | Líneas | Evidencia de no uso |
|---|---|---|---|
| `servicio_proyeccion._metadatos_auditoria_horizontes` | 2164–2213 | 50 | 0 referencias en el repositorio. G2: no la ejecuta ninguna prueba |
| `servicio_proyeccion._numero_parametros_modelo` | 2216–2221 | 6 | Ídem |
| `servicio_proyeccion._metricas_desde_predicciones` | 2532–2569 | 38 | Ídem. Además usaba el nombre **no definido** `detectar_errores_extremos` (pyflakes): habría lanzado `NameError` si alguien la llamara |
| `servicio_proyeccion._explicacion_factibilidad` | 4357–4368 | 12 | Ídem |
| `servicio_proyeccion._validar_ajuste_calendario_serie` | 4385–4448 | 64 | Ídem. Su docstring ya decía «Ya no decide nada» (P0-F) |
| `validacion_series.resumen_validacion` | 169–181 | 13 | Ídem |
| **Total** | | **183** líneas de definición (200 de diff, con separadores e imports) | |

**Imports retirados en `d7429df`.** Al quitar las definiciones quedaron sin uso:
- `import hashlib`;
- `from datetime import datetime, timezone`;
- `TOLERANCIA_DETERIORO_AJUSTE_CALENDARIO`, de `criterios`;
- `evaluar_ajuste_en_backtesting`, de `calendario_anual`;
- `calcular_escala_naive_insample`, de `metricas`.

Ninguno se lee como atributo `sp.X` ni se importa desde este módulo en el repositorio. Los módulos de origen siguen importándose por otros nombres.

## 3. Diff

```
git diff --stat c9166c6 81a8247 -- app_icociv aplicacion.py packaging VERSION requirements*.txt tests scripts pruebas
 app_icociv/estadistica/validacion_series.py  |  15 ---
 app_icociv/proyeccion/servicio_proyeccion.py | 185 ---------------------------
 2 files changed, 200 deletions(-)

git diff --check c9166c6 81a8247   → sin avisos
```

**No se tocaron:** `tests/`, `scripts/`, `pruebas/`, `packaging/`, `VERSION`, `requirements*`, `tests/fixtures/fase0/golden/*` ni sus tolerancias.

**Tamaño de los módulos.**

| Módulo | Antes | Después |
|---|---|---|
| `servicio_proyeccion.py` | 6 166 | 5 981 |
| `validacion_series.py` | 181 | 166 |

## 4. Pruebas ejecutadas por lote (mismo equipo y entorno)

| Comprobación | Línea base `c9166c6` | Lote 1 (`c6ca863`) |
|---|---|---|
| `compileall` de `app_icociv`, `aplicacion.py`, `scripts` y `pruebas` | — | OK |
| Importar todos los módulos de `app_icociv` y `aplicacion` (Qt offscreen) | — | OK, ningún error |
| Huella semántica exacta: 20 casos motor×horizonte, economía y rechazos | Capturada 2 veces: 0 diferencias | **0 diferencias**, SHA-256 idéntico (`d6be699b…`) |
| 29 Golden Masters más 10 archivos focalizados (selector, AS-001, horizontes, presentación, fundamentación, vocabulario, remediación, nmin, origen N0, cierre semántico) | Incluidas en el perfil esencial | **189/189 PASS** |
| `pytest --collect-only tests` | 1 061 y 3 errores previos | **1 061 idénticas** (`diff` de ids vacío) y los mismos 3 errores |
| Históricas relacionadas con AS-003 (11 archivos) | 12 fallos y 2 errores de recolección, previos | **Mismos ids** de fallo |
| `pruebas/prueba_estadistica.py` y `pruebas/ejemplo_uso.py` (anexo sintético) | Código 0 / código 1 por `ci_lo=None` (defecto previo) | **Salida idéntica** |
| Perfil esencial local | 797/797 | Ver 04 §2 |
| CI [40445532574](https://github.com/estebanojeda0615/SAVIP/actions/runs/40445532574) (`81a8247`) | — | **success**: 797 pruebas, 0 fallos, ninguna intermitente |

## 5. Pruebas retiradas, adaptadas y conservadas (G5)

**Ninguna prueba retirada ni adaptada.** El Lote 1 solo retira definiciones que ninguna prueba usaba.

**Pruebas históricas conservadas.** Las 75 que ejercen código retirado siguen tal cual, porque sus funciones siguen existiendo (DEFERIDAS). Su tratamiento individual corresponde al lote en que se retire cada función.

**Recuentos sin cambios:**
- 797 esenciales;
- 1 061 recolectadas.
