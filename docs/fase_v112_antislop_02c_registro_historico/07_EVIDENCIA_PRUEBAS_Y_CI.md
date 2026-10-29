# 07 · Evidencia de pruebas y CI

## 1. Perfil esencial

| Ejecución | Pruebas | PASS | FAIL | XFAIL | SKIP | Reintentos | Intermitentes | Golden | Tiempo (JUnit) |
|---|---|---|---|---|---|---|---|---|---|
| Local, base `2f70391` | 797 | 797 | 0 | 0 | 0 | 0 | ninguna | 29/29 | 1 905 s |
| Local instrumentada (espía G2), base | 797 | — | 0 | — | — | 0 | ninguna | — | — |
| **Local, HEAD de código `7acd0ce`** | **804** | **804** | **0** | **0** | **0** | **0** | ninguna | **29/29** | 1 814 s |
| **CI [40816459661](https://github.com/estebanojeda0615/SAVIP/actions/runs/40816459661), `7acd0ce`** | **804** | **804** | **0** | **0** | **0** | **0** («0 fallos en la primera ejecución») | ninguna | 29/29 | 43 min |

**Ids** ([`evidencia/comparacion_ids_esenciales.txt`](evidencia/comparacion_ids_esenciales.txt), por `(classname, name)`):
- 797 ids antes y 804 después;
- 0 ids solo antes y 0 estados cambiados: **los 797 originales se conservan y pasan**;
- 7 ids solo después: los de `tests/test_fase2c_contratos_vigentes.py`.

**Recolección** ([`evidencia/coleccion_diff.txt`](evidencia/coleccion_diff.txt)):
- `pytest --collect-only tests` da 1 052 ids antes y 1 059 después;
- se añaden 7 y no desaparece ninguno;
- los mismos 3 errores de recolección previos, que no se cuentan como éxitos.

**`--listar`.** Esenciales 797 → 804 (80 → 81 archivos). Históricas 242 + 3, gui 13 y total 1 052 → 1 059.

## 2. Pruebas nuevas

| Id | Contrato vigente | Sustituiría (2D) |
|---|---|---|
| `test_escasez_de_ventanas_entrega_el_punto_con_advertencia_y_sin_intervalo[36]`, `[37]`, `[41]` | W* = 1, 2 y 6. Punto finito entregado, trayectoria de 24 meses finita y 6 claves de intervalo en `None`. Advertencia «tiene W ventanas» solo si W* < `MIN_ITERACIONES_WF`, y niega la validación | PS03 (`tramo_evidencia_oos`); `test_sin_ventanas_…`; `test_iteraciones_insuficientes_…` |
| `test_banda_no_construible_no_cancela_el_punto` | Con `_intervalos_prediccion` fallando: mismo modelo, `y_proj` y trayectoria; sin intervalo; el motivo no se publica | Dirección 1 de `test_vocabulario_vc…`; `test_banda_no_valida_…`; `test_p0g…::test_g6` |
| `test_texto_evidencia_oos_tres_tramos_sin_vocabulario_de_validacion` | Redacción de `_texto_evidencia_oos` en los tres tramos, sin «valid/certific» | Vocabulario de PS03 |
| `test_sin_errores_finitos_comunes_no_se_fabrica_un_modelo` | Todos los errores en NaN: `proyeccion_generada = False`, sin modelo ni valor finito, con explicación | `test_sin_evidencia_comparable_…` (lee la fuente de `_evaluar_horizontes_proyeccion`) |
| `test_la_ruta_vigente_no_referencia_el_subsistema_heredado` | Ninguna de las 7 funciones de la ruta vigente nombra una definición heredada (AST, sin comentarios ni docstrings) | `test_la_ruta_productiva_no_invoca_el_selector_de_respaldo`; complementa el espía de la Fase 1A |

**Condiciones que cumplen.**
- Ejercen la ruta real con datos sintéticos.
- No importan ni exigen código heredado: pasan antes y después de la 2D.
- No tocan golden ni tolerancias.

**Sensibilidad** ([`evidencia/sensibilidad.txt`](evidencia/sensibilidad.txt)). Seis mutaciones, aplicadas solo a copias:

| Mutación | Qué rompe | Resultado |
|---|---|---|
| M0 | Se publica el intervalo | FALLA |
| M1 | La banda cancela el punto | FALLA |
| M2 | Se retira la advertencia de escasez | FALLA |
| M3 | El tramo limitado se llama «validada» | FALLA |
| M4 | Se fabrica un modelo sin errores finitos | FALLA |
| M5 | La ruta vuelve a nombrar el selector heredado | FALLA |
| Control, sin mutación | — | PASA |

## 3. Golden Masters, AS-001 y huella

- **Golden.** 29/29 en la base, en el final y en el CI. `git diff 2f70391 HEAD -- tests/fixtures` está vacío: fixtures, valores esperados y tolerancias (1e-9; 1e-2 solo para Holt/Huber perdedores) sin cambios.
- **AS-001.** Los 16 casos `test_as001_*` pasan en todas las ejecuciones.
- **Huella semántica exacta** ([`evidencia/huella_resumen.txt`](evidencia/huella_resumen.txt)). Base ×2 y final: SHA-256 `d6be699b700b3fa3379c743cc9d0ccbf5c185cacfa228208dbb95c2735370191`, idéntico, con **0 diferencias**. Cubre:
  - 20 casos motor×horizonte;
  - el SSE exacto y el RMSErect de los 21 candidatos;
  - H1–H24 y MAE(h);
  - la economía, el empalme y los rechazos.

## 4. Espía G2

[`evidencia/g2_espia.txt`](evidencia/g2_espia.txt): perfil esencial completo de la base con las candidatas envueltas.
- Ninguna prueba de flujo productivo (golden, GUI, integración de 21 candidatos) ejecuta una definición heredada.
- Solo las ejecutan las pruebas unitarias que las nombran (las de 03).

## 5. Diff y estado del repositorio

```bash
git diff --stat 2f70391 7acd0ce -- app_icociv aplicacion.py packaging VERSION requirements.txt requirements-lock.txt requirements-build.txt requirements-test.txt pruebas
```

Resultado: **vacío**. El diff productivo es nulo.

```bash
git diff --stat 2f70391 7acd0ce
```

Resultado: `.github/workflows/fase0-pruebas.yml` (+1), `scripts/pruebas_fase0.py` (+2: la nueva entrada del perfil esencial) y `tests/test_fase2c_contratos_vigentes.py` (nuevo).

- **`git diff --check`:** sin avisos.
- **`compileall` e importaciones:** la recolección completa importa todos los módulos de prueba. El perfil esencial ejercita la interfaz Qt offscreen.

## 6. Comandos

```bash
python scripts/pruebas_fase0.py --listar
```

```bash
python scripts/pruebas_fase0.py esenciales --junitxml=resultados/esenciales.xml -o junit_family=xunit2
```

```bash
python -m pytest --collect-only -q tests
```

```bash
python docs/fase_v112_antislop_02a_as003/evidencia/huella_semantica.py capturar <salida.json>
```

```bash
python docs/fase_v112_antislop_02a_as003/evidencia/huella_semantica.py comparar <a.json> <b.json>
```

```bash
python docs/fase_v112_antislop_02a_as003/evidencia/grafo_as003.py . <grafo.json>
```

```bash
python docs/fase_v112_antislop_02c_registro_historico/evidencia/pruebas_dependientes.py . <grafo.json> <collect.txt> <salida.json>
```

```bash
python docs/fase_v112_antislop_02c_registro_historico/evidencia/sensibilidad_pruebas_nuevas.py <copia> <trabajo>
```

## 7. Limitaciones

- **PS02 no protege en un clon limpio.** `test_cierre_semantico_ps01_ps05::test_ps02_ninguna_metrica_niega_un_horizonte_con_evidencia` necesita el anexo DANE: en un clon limpio imprime «OMITIDA» y pasa sin comprobar nada. No se corrige aquí (AS-007), y figura como riesgo en 03 y 08.
- **Perfiles gui e histórico.** No se ejecutaron completos (fuera de alcance). Los 4 archivos de `tests/` de estilo script no se ejecutan en ningún perfil.
- **CI del HEAD final.** Se informa en el mensaje de entrega: este documento forma parte de ese commit.
