# 03 · Cambios y migraciones

## 1. Archivos (`git diff --numstat 56c75a6 5acb09f`, sin docs)

| Archivo | + | − | Contenido |
|---|---|---|---|
| `pruebas/prueba_horizonte_dinamico_ui_reportes.py` | 3 | 28 | Retira `test_el_modelo_entregado_es_el_de_minimo_error_oos_global` (27 líneas) y su llamada en `main()` (1). Deja una lápida de 3 líneas |
| `.github/workflows/fase0-pruebas.yml` | 1 | 0 | Añade la rama al filtro de `push`. No toca jobs, pruebas, dependencias ni permisos |
| `.gitignore` | 1 | 0 | Excepción para esta carpeta |

**Sin cambios:**
- los otros 29 tests del script, incluidos los tres de 2D-1;
- `pruebas/ejemplo_uso.py` y `pruebas/prueba_estadistica.py`;
- `scripts/pruebas_fase0.py`, porque no se añade ningún archivo esencial;
- todo `tests/` (no hay archivo nuevo ni migración), `app_icociv/**`, `aplicacion.py`, `VERSION`, `packaging/**`, `requirements*` y `tests/fixtures/**`.

La lápida final dice:

```python
# AS-028: retirado test_el_modelo_entregado_es_el_de_minimo_error_oos_global (hasta 56c75a6), atado al selector
# heredado de C-SEL-001. Cubre la regla vigente tests/test_fase1a_selector_rectangular.py; ver
# docs/fase_v112_antislop_as028_preparacion_2d2_thermos/03_CAMBIOS_Y_MIGRACIONES.md.
```

No nombra el símbolo heredado (hallazgo M2 de Thermos): el `grep` del par en el script da 0. Tampoco contiene la cadena que vigila `test_ninguna_prueba_depende_de_reportes_generados`. El test completo se recupera con `git show 56c75a6:pruebas/prueba_horizonte_dinamico_ui_reportes.py` (L279-305).

## 2. Commits

| Commit | Contenido |
|---|---|
| `4218340` | `ci(as-028)`: filtro del workflow (+1) y `.gitignore` (+1). Va antes del código para que el CI corra sobre el propio commit de código |
| `0929b29` | `test(as-028)`: retiro del test y de su llamada en `main()`, con lápida |
| `5acb09f` | `test(as-028)`: lápida corregida tras la 1.ª pasada de Thermos. **Último commit de código** |
| HEAD documental | Esta carpeta |

El mensaje de `0929b29` dice «el único test atado al selector heredado». Se refiere al **script**. En `tests/` quedan otras pruebas atadas al selector, inventariadas en 02 §2. No se reescribe el historial.

## 3. Destino del test del selector: retirar, no reescribir ni NO-GO

| Opción del prompt (§7.1) | Valoración |
|---|---|
| **Retirar con lápida** | **Elegida.** Sus invariantes vigentes ya están cubiertos por esenciales (tabla siguiente) y su expectativa propia es una regla que ya no gobierna el resultado |
| Reescribirlo contra el contrato vigente | Sin valor nuevo: repetiría `test_la_ruta_productiva_usa_el_selector_rectangular_y_ningun_selector_retirado`, que ya compara el modelo entregado con `_seleccionar_modelo_rectangular` sobre la matriz real. Compararlo con una reimplementación propia sería «reimplementar la selección para compararla consigo misma», algo que el prompt descarta |
| NO-GO | No procede: ninguna propiedad vigente queda sin cobertura |

**Qué afirmaba el test y quién lo cubre hoy:**

| Aserción o propiedad | ¿Vigente? | Cobertura esencial |
|---|---|---|
| `modelo_codigo == seleccionar_modelo_por_rmse_oos_global(backtesting_comparativo, 1..24)` | **No.** El selector heredado usa todos los pares del backtesting comparativo y RMSE en coma flotante. La ruta vigente usa la muestra común W*×24 de la matriz rectangular y SSE exacta. El sondeo `evidencia/g3_divergencia_selector.txt` da modelos distintos en **4 de las 5** series Fase 0. En la serie del test los dos selectores coinciden (`drift`), mientras su docstring sostenía que ganaba `exponencial_log_lineal` | — (no debe cubrirse: sería una segunda regla de selección) |
| Se entrega el modelo de mínimo error OOS sobre una muestra común | Sí | `test_fase1a…::test_la_ruta_productiva_usa_el_selector_rectangular_y_ningun_selector_retirado`: modelo entregado = `_seleccionar_modelo_rectangular(m_rect, modelos)`, 21 candidatos, H 1..24, pares comunes = W*×24 y 0 llamadas al selector heredado. Además, `p_minimo_sse` en `test_selector_vigente_cumple` |
| Pesos uniformes entre horizontes (cierre H-9, «la selección deja de ponderar por 1/h») | Sí | `p_pesos_uniformes_por_horizonte` y el mutante `peso_1_h` en `test_cada_mutante_es_detectado` |
| Solo pares comunes, SSE exacta, desempate y RMSE coherente | Sí | Las demás propiedades y los mutantes `todos_los_pares`, `suma_flotante`, `ultimo_en_empate` y `rmse_sin_n` |
| La selección no aborta con un candidato divergente | Sí | `test_as001_ruta_productiva_con_21_candidatos_y_uno_divergente` |

## 4. Migraciones a `tests/`: ninguna

El inventario (`01_…csv`) clasifica 19 tests como VIGENTE ÚNICO.
- Todos pasan, pero no se comparó cada aserción con un esencial equivalente, así que **no se declaran duplicados**.
- No se migran en esta fase porque:
  1. siguen en el script, sin cambios, y no dependen del par de 2D-2, de modo que AS-028 no les quita protección;
  2. migrarlos crearía una segunda suite paralela, contra la regla del prompt de «no migrar 30 casos por reflejo».

El revisor de calidad de Thermos lo valoró como «razonable, y desde la rúbrica es la opción correcta».

**Deuda que queda registrada:**
- el script no corre en CI;
- su `main()` se detiene en el 2.º test.

Esos 19 casos son candidatos a una migración mínima en una fase de saneamiento del script, ajena a 2D-2.

## 5. Script antes y después (JUnit)

| Ejecución | Tests | PASS | FAIL | Fallos |
|---|---|---|---|---|
| Base `56c75a6` (`evidencia/script_base_pytest.xml`) | 30 | 22 | 8 | `horizonte_25_estable`, `horizonte_25_erratico`, `h18_no_se_redacta`, `parametros_drift_receta_csv`, `pdf_y_docx_contienen_horizontes_con_escenario`, `horizonte_dinamico_con_serie_drift`, `horizonte_dinamico_con_serie_holt`, `docx_777` |
| Final `5acb09f` (`evidencia/script_final_pytest.xml`) | 29 | 21 | 8 | **Los mismos 8** |

- La única baja es el test retirado, que pasaba.
- Ningún test cambia de estado.
- Los 8 fallos históricos no se corrigen, ni se marcan con `skip`/`xfail`, ni se toca ninguna expectativa.
- La ejecución directa (`python pruebas/prueba_horizonte_dinamico_ui_reportes.py`) se detiene en las dos versiones en el 2.º test de `main()` (h=25, `ValueError`), con código 1.
