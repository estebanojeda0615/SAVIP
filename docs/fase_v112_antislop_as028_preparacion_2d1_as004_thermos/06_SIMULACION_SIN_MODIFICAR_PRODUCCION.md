# 06 · Sondeos de alcanzabilidad y simulación del retiro de 2D-1, sin modificar producción (G4)

## 1. Grafo sobre el HEAD real (`102f194`)

Herramienta: `docs/fase_v112_antislop_02a_as003/evidencia/grafo_as003.py`. Salida: `evidencia/grafo_102f194_2d1.json`.

| Definición (`servicio_proyeccion.py`) | Líneas | N.º | Alcanzable desde producción | Referenciada por (código) |
|---|---|---|---|---|
| `determinar_horizonte_maximo_estadistico` | 3274-3531 | 258 | **No** | Nadie en `app_icociv`. Script, y tests `fase1a`, `fase2c`, `presentacion_resultados` y `resultado_horizonte_solicitado` |
| `_serializar_evaluaciones_horizonte` | 3534-3603 | 70 | No | Solo `determinar_*` |
| `_item_horizonte_global` | 3606-3622 | 17 | No | Solo `determinar_*` |
| `_mayor_horizonte_con` | 3625-3650 | 26 | No | Solo `determinar_*`. Cita documental en `criterios.py` (C-ALC-002) y uso en el test histórico `test_cierre_metodologico` |
| `_ultimo_horizonte_por_clasificacion` | 3687-3714 | 28 | No | Solo `determinar_*` |
| `_evidencia_horizonte` | 3717-3737 | 21 | No | Solo `determinar_*` |
| **Total del lote 2D-1** | | **420** | | Coincide con el plan 2C. El conjunto es **cerrado**: ningún otro código llama a las 5 auxiliares |
| `_tipo_uso_horizonte` (compartido) | 2362-2373 | 12 | No | `determinar_*`, `_serializar_…` y **`_clasificar_evidencia_horizonte`** (2D-3) |
| `_mayor_horizonte_permitido` (compartido) | 3653-3684 | 32 | No | `determinar_*` y **`_aplicar_salvaguarda_benchmarks`** (2D-3) |

**Conclusión:** sigue vigente la regla del plan 2C. Los dos auxiliares compartidos **se conservan** con 2D-1 y se retiran con 2D-3, porque `_clasificar_evidencia_horizonte` y `_aplicar_salvaguarda_benchmarks` siguen definidas y los usan.

No hay acceso dinámico: no hay `getattr`, `importlib` ni `import *` sobre `servicio_proyeccion` en `app_icociv`, tampoco está en `__all__` ni en el spec de PyInstaller. Lo verificó el revisor de corrección de Thermos (08).

## 2. Espías pasivos sobre la ejecución real

Herramienta: `evidencia/scripts/sonda_claves_as004.py`. Los espías cuentan las llamadas y delegan, sin alterar argumentos ni retornos.

| Casos | Llamadas a las 8 funciones (6 de 2D-1 y 2 compartidas) |
|---|---|
| 7 series (fixture drift, fixture holt, estable de 120, historia insuficiente de 20, sin valores válidos, valor negativo, valor cero) × h ∈ {1, 12, 18, 24} = 28 ejecuciones de `ejecutar_proyeccion`, más la sesión heredada | **0**, en la base y en el final (`evidencia/sonda_claves_base.json`, `evidencia/sonda_claves_final.json`) |

**Límite:** que no se observen llamadas no sustituye a la inspección de referencias dinámicas. Por eso se combina con el §1 y con la simulación de ausencia del §3.

## 3. Ausencia simulada en memoria

El plugin de pytest `evidencia/scripts/ocultar_2d1.py` borra con `delattr` las 6 definiciones del módulo ya importado, dentro del propio proceso. **No edita ningún archivo** y deja presentes los 2 compartidos (lo comprueba con un `assert`). Se ejecutó sobre copias limpias de la base y del último commit de código.

| Ejecución | Resultado | Evidencia |
|---|---|---|
| Script **final**, colección con 2D-1 oculto | 26 recogidos, código 0 | `evidencia/g4_script_final_collect_oculto.txt` |
| Script **final**, ejecución con 2D-1 oculto | **19 PASS / 7 FAIL, idéntico id a id** al script final con 2D-1 visible. Los 7 FAIL son los históricos, ninguno relacionado con 2D-1 | `evidencia/g4_script_final_oculto.xml` |
| Script **base** con 2D-1 oculto (sensibilidad de la sonda) | 19 PASS / 10 FAIL. Respecto a la base visible solo cambian `test_horizonte_maximo_no_es_18…` y `test_mensaje_no_recomendables…` (PASS → FAIL). `test_h18…` ya fallaba | `evidencia/g4_script_base_oculto.xml` |
| `pytest --collect-only tests` con 2D-1 oculto | 1 021 recogidos y **4 errores**: los 3 históricos más **`tests/test_resultado_horizonte_solicitado.py`** (ImportError en el `import` de nivel de módulo) | `evidencia/g4_collect_tests_oculto.txt` |
| **Perfil esencial completo** con 2D-1 oculto | 795 entradas (809 − 15 + 1 error de recolección): 791 PASS, 3 fallos y 1 error, sin intermitentes | `evidencia/g4_esenciales_oculto.txt` |
| Históricas afectadas, con 2D-1 oculto | `test_cierre_metodologico`: 2 FAIL | `evidencia/g4_historicas_afectadas_oculto.txt`, `evidencia/g4_historicas_afectadas_base_visible.txt` |

### 3.1 Ids esenciales que fallan con 2D-1 oculto: lista completa

Son los **18** previstos en 05 §2, ni uno más ni uno menos.

| Id | Causa puntual | Cobertura vigente | Destino propuesto (05) |
|---|---|---|---|
| `tests/test_resultado_horizonte_solicitado.py`, **los 15 ids** | Error de recolección: `ImportError` de `determinar_horizonte_maximo_estadistico` en el `import` de L10-16 | 9 de ellos son contratos vigentes que no usan la función | 6: RETIRAR. 9: ADAPTAR-IMPORT |
| `test_presentacion_resultados::test_horizonte_dinamico_diferencia_tecnico_cautela_y_no_evaluado` | `ImportError` (import local, L522) | No aplica: ejerce la función muerta | RETIRAR |
| `test_presentacion_resultados::test_horizonte_no_salta_un_corte_no_viable` | `ImportError` (L552) | No aplica | RETIRAR |
| `test_fase1a_selector_rectangular::test_la_ruta_productiva_usa_el_selector_rectangular_y_ningun_selector_retirado` | `AttributeError` en `getattr(sp, n)` del espía (`patch.object(... wraps=getattr(sp, n))`) | **Vigente** | ADAPTAR-AUSENCIA: pasar el nombre a `eliminados`, cuya regla es `hasattr` debe ser False |

`test_fase2c_contratos_vigentes` (7 ids) y `test_pool_calendario_fourier_seasonal` (12) **pasan** con 2D-1 oculto. Los fallos se repiten en el reintento interno del runner: son deterministas y no son intermitencias.

### 3.2 Históricas

| Id | Base visible | Con 2D-1 oculto | Causa |
|---|---|---|---|
| `test_cierre_metodologico::test_no_queda_cascada_de_prefijo_en_ninguno_de_los_dos_maximos` | PASS | **FAIL** | `AttributeError: _mayor_horizonte_con` (previsto en 05 §2.6) |
| `test_cierre_metodologico::test_no_hay_modelo_por_horizonte` | **FAIL** (preexistente) | FAIL | Busca el texto `modelo = seleccion_horizonte["modelo"]` en `_ejecutar_proyeccion_base`. **Ajeno a 2D-1** |
| `test_regresiones_auditoria_independiente_bghc` | 0 tests (estilo script) | 0 tests | Usa solo el compartido `_mayor_horizonte_permitido` |

Ningún error de recolección nuevo en el perfil histórico, salvo el de `test_resultado_horizonte_solicitado`, que es esencial y ya se ha descrito.

### 3.3 Salidas productivas con 2D-1 oculto

`evidencia/scripts/sonda_oculto.py` borra las 6 definiciones y pone en su lugar funciones que **lanzan `AssertionError` si alguien las llama**. Después repite la sonda (28 ejecuciones más la sesión heredada) y compara con la base estos campos:
- `proyeccion_generada`;
- las claves históricas presentes en `horizonte_info`, con sus valores;
- los valores de las 17 columnas históricas del CSV reproducible;
- la fuente real del encabezado de la UI, observada en el HTML de `_encabezado`.

El resultado está en `evidencia/sonda_oculto.txt` y se resume en 07 §4.

## 4. Dictámenes de esta simulación

| Dictamen | Estado | Motivo |
|---|---|---|
| **AS-028 SCRIPT PREPARADO** | **Sí** | El script recoge y ejecuta sus 26 pruebas **sin depender** de `determinar_horizonte_maximo_estadistico`: misma tasa de fallos y mismos ids con 2D-1 visible u oculto. Las dependencias AS-004 restantes del script (drift y holt) no son de 2D-1 y se registran aparte |
| **LOTE 2D-1 EJECUTABLE** | **No, todavía** | Quedan 18 ids esenciales que fallarían. 8 son bajas que exigen autorización expresa. 10 son adaptaciones de prueba (9 de import y 1 de la Fase 1A) que también la exigen. Hay además una histórica afectada y la ficha `C-ALC-002`. **No hay ningún consumidor productivo** de las 6 funciones (§1, §2 y §3.3) |
