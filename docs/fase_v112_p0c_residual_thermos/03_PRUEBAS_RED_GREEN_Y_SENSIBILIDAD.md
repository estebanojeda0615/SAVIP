# 03 · Prueba adversarial RED y sensibilidad

**No hay GREEN.** El contrato de irreconstruibilidad del IC95 no es viable mientras se conserven los agregados protegidos (01). No hay corrección y no simulo un GREEN.

## 1. Prueba adversarial diagnóstica (fuera del perfil esencial)

**Archivo:** [`evidencia/adversarial_p0c_residual_ic95.py`](evidencia/adversarial_p0c_residual_ic95.py), con las utilidades de [`evidencia/caso_ic95.py`](evidencia/caso_ic95.py).
- Vive en `docs/` y su nombre no empieza por `test_`: `pytest --collect-only` no la recoge y `scripts/pruebas_fase0.py` no la asigna a ningún perfil. No deja el CI en rojo y no usa `skip` ni `xfail`.
- `caso_ic95.py` fija `QT_QPA_PLATFORM=offscreen` y añade la raíz a `sys.path`, así que el comando funciona igual en PowerShell y en bash.

**Comando canónico**, desde la raíz:

```text
python -m pytest docs/fase_v112_p0c_residual_thermos/evidencia/adversarial_p0c_residual_ic95.py -p no:cacheprovider -q -rA
```

**Ejecución sobre la base.** El código de producción es el de `dfcaaa9`, porque la rama no lo modifica. Entorno de 00, con `PYTHONDONTWRITEBYTECODE=1`.

**Código de salida 1:** 4 FAIL y 55 PASS en 36,9 s. La salida completa, sin filtrar, está en [`evidencia/salida_adversarial_red_base.txt`](evidencia/salida_adversarial_red_base.txt).

| Grupo | Prueba | Casos | Base | Qué significa |
|---|---|---|---|---|
| Contrato | `test_contrato_sin_vector_individual_de_errores_oos` | n48_h6, n72_h12, n38_h24, n72_h24 | **4 FAIL** | «Vector de errores OOS por ventana publicado (vía A, reconstruye el IC95): 1008 rutas; formas: [`…observaciones[*].error_absoluto`, `…observaciones[*].z_modificado`]» (504 entradas × 2 claves) |
| Contrato | `test_contrato_el_comparativo_conserva_los_agregados` | 4 | PASS | Se publican `rmse`, `mae`, `mase`, `iteraciones` y `sesgo_medio`, y todos son finitos |
| Caracterización del NO-GO | `test_caracterizacion_no_go_cada_via_reconstruye_el_ic95_exacto` | 6 escenarios con banda × {A, B1} | **12 PASS** | Con el vector (A) o con el RMSE publicado (B1), el IC95 interno sale **exacto** (`==`) |
| Caracterización del NO-GO | `test_caracterizacion_no_go_via_algebraica_reconstruye_el_ic95_salvo_un_ulp` | 6 × {A', B2, B4} | **18 PASS** | Identidades algebraicas exactas: `z_modificado`+mediana+MAD, desviación+media y MAE+`estabilidad_error`. Tolerancia declarada `rel_tol=1e-15` (B2 en n48_h24 difiere en un ULP) |
| Caracterización del NO-GO | `test_caracterizacion_no_go_el_texto_interpretacion_da_el_ic95_salvo_el_redondeo_a_3_decimales` | 6 | **6 PASS** | B5: el texto «RMSE=x.xxx» da la banda dentro de la cota c(n)·5·10⁻⁴, que se deduce del formato |
| Caracterización del NO-GO | `test_caracterizacion_no_go_el_rmse_h_persistido_reconstruye_el_ic95_exacto_en_h24` | n38_h24, n72_h24 | **2 PASS** | `tabla_horizontes[24].rmse` y `W` dan la banda exacta del paso 24 |
| Caracterización del NO-GO | `test_caracterizacion_no_go_retirar_solo_el_vector_no_cierra_p0c` | n48_h6 | **PASS** | Sin `observaciones`, el detector no encuentra nada, pero B1 sigue siendo exacta: sería un **cierre falso** |
| Caracterización del NO-GO | `test_caracterizacion_no_go_retirar_solo_error_absoluto_no_basta` | n48_h6 | **PASS** | Sin la clave `error_absoluto`, `z_modificado` + mediana + MAD devuelven el vector y la banda exacta (A') |
| Detector | `test_detector_sensibilidad` | 9 objetos | 9 PASS | Detecta registros con `Error`, la columna `Predicho`, `error_absoluto` como lista y como array, una Series llamada `Error`, un DataFrame anidado con `Observado` y registros con `z_modificado`. Descarta un único registro y las estructuras con `None` o vacías |
| Escenario | `test_escenario_historia_insuficiente_sin_banda_ni_vectores` | n30_h3 | PASS | `proyeccion_generada=False`: no hay banda interna finita, no hay vectores y el recorrido no falla |
| Escenario | `test_escenario_entradas_sin_extremos_publican_el_vector_completo` | n48_h6 | PASS | Un candidato calculable con `cantidad == 0` publica igualmente `observaciones` completas, tantas como `iteraciones` |

**Por qué no es un falso verde ni un falso rojo:**
- El detector recorre dicts, listas, tuplas, DataFrames (columnas y celdas anidadas) y Series (por nombre y por contenido), con protección de ciclos. Los arrays se detectan cuando cuelgan de una clave con nombre de error. **Es heurístico, porque busca por nombre de clave**: un verde suyo no prueba que la banda sea irreconstruible. El oráculo semántico es la caracterización, que reconstruye la banda por las vías identificadas en esta fase: A, A', B1, B2, B4, B5 y B3 en h=24. No se garantiza que no haya otras.
- Su sensibilidad se comprueba con asserts, no por inspección visual.
- El fallo del contrato da la ruta real y el número de apariciones.
- La caracterización usa igualdad exacta sin tolerancia. Antes comprueba, en todos sus casos, que la banda interna es finita, que no se publica y que no hay ajuste de calendario (`_con_banda`).

**Cómo usarla si se promueve.** Solo el grupo «Contrato» y el «Detector» sirven como regresión en `tests/`. El grupo «Caracterización» protegería la vulnerabilidad y debe quedarse como diagnóstico. Convendría además unificar el detector con los de `tests/` (`_errores_recuperables` y `_tablas_de_ventanas`) en lugar de que convivan (05).

## 2. Huella y regresión

**Huella.** No hay cambios de producción. `huella_semantica.py` (Fase 2A) en la rama nueva da 20/20 casos con **0 diferencias** y el mismo SHA-256 que la base: `d6be699b700b3fa3379c743cc9d0ccbf5c185cacfa228208dbb95c2735370191`. Comando y resultado en [`evidencia/huella_resumen.txt`](evidencia/huella_resumen.txt).

**Comparación con lista blanca (§5.1 del prompt de la fase):** no aplica, porque no se ha retirado ninguna ruta (04).

**Perfil esencial y golden:** son los de `dfcaaa9`. La rama solo añade documentación, scripts en `docs/` y dos líneas de configuración. El CI de la rama los ejecuta (06).
