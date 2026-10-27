# 04 · CI y regresión

## 1. Perfil esencial y Golden Masters

| Ejecución | Pruebas | PASS | FAIL | XFAIL | SKIP | Reintentos | Intermitentes | Golden | Tiempo (JUnit) |
|---|---|---|---|---|---|---|---|---|---|
| Local, copia limpia de la base `1848275` | 797 | 797 | 0 | 0 | 0 | 0 | ninguna | 29/29 | 2 146 s |
| **Local, copia limpia del HEAD de código** (`10f1d0d`) | **797** | **797** | **0** | **0** | **0** | **0** | ninguna | **29/29** | 1 774 s |
| **CI [40578617725](https://github.com/estebanojeda0615/SAVIP/actions/runs/40578617725)**, `10f1d0d` | **797** | **797** | **0** | **0** | **0** | **0** («0 fallos en la primera ejecución») | ninguna | 29/29 | 62 min |

**Mismos 797 ids.** [`evidencia/comparar_ids_esenciales.py`](evidencia/comparar_ids_esenciales.py) compara por `(classname, name)` los JUnit de las dos ejecuciones locales. Resultado ([`evidencia/comparacion_ids_esenciales.txt`](evidencia/comparacion_ids_esenciales.txt)):
- 797 ids antes y 797 después;
- 0 ids solo antes, 0 solo después y 0 estados cambiados: **conjunto idéntico**.

**Reintentos.** En ninguna de las tres ejecuciones hay archivos `__reintento.xml` ni la línea «Intermitentes» del CI lista nada. **Ningún verde depende de un reintento.**

**Golden Masters.**
- `git diff 1848275 HEAD -- tests/fixtures` está vacío: los JSON, `captura.py` y las tolerancias (1e-9, y 1e-2 para Holt/Huber perdedores) no cambian.
- No se regeneró ningún golden.

## 2. Equivalencia semántica

**Huella exacta.** Base, base y después dan el mismo SHA-256, `d6be699b…`, con **0 diferencias** en 20 casos. Cubre:
- el ganador y el segundo;
- el SSE `Fraction` exacto y el RMSErect de los 21 candidatos;
- los pares W*×24, la trayectoria H1–H24, MAE(h), el sesgo y las métricas;
- la economía, el empalme y los rechazos.

Detalle en 03 §4.

**Contratos de aplicación.** Dentro de la cobertura existente, ningún contrato cambió: sesiones, deshacer y rehacer, apertura y guardado, y Excel (con fórmulas), PDF, DOCX y CSV.
- Los cubren los 12 golden de sesiones y exportables y las pruebas GUI y de sesión del perfil esencial, todas en PASS.
- `pruebas/` produce la misma salida.

## 3. Recolección histórica

| Medida | Antes | Después |
|---|---|---|
| `pytest --collect-only tests` | 1 061 ids y 3 errores | **1 052** ids y los **mismos 3 errores** |
| Diferencia | — | Exactamente los 9 ids retirados en `73e565c` (02 §2; [`evidencia/coleccion_diff.txt`](evidencia/coleccion_diff.txt)) |
| `--listar` | esenciales 797 · históricas 251 + 3 · gui 13 · total 1 061 | esenciales **797** · históricas 242 + 3 · gui 13 · total 1 052 |

Los 3 errores de recolección (`test_equivalencia_presupuestal_fase_4e_b`, `test_p0c_objeto_publico_sin_intervalo`, `test_p0c_regresion_negativa_c2`) son previos, se mantienen identificados y no se cuentan como éxitos.

## 4. Puerta G2: espía

**Ejecución.** Plugin `espia_as003.py` de la Fase 2A, envolviendo **solo las 3 funciones**, sobre el **código base**, en el perfil esencial completo y los 4 históricos. Detalle en [`evidencia/g2_espia_y_anomalia.txt`](evidencia/g2_espia_y_anomalia.txt).

| Función | Pruebas que la ejecutaron |
|---|---|
| `_rmse_global_estable` | `test_rmse_global_estable` T1–T6b (retiradas) y `test_p0d…::test_d1` (adaptada) |
| `_modelo_consistente_desde_comparativo` | **Ninguna.** Solo se inspeccionaba su fuente |
| `_modelo_trayectoria_consistente` | `test_seleccion_rmse_global::test_no_hay_peso_por_horizonte` (adaptada) |

**Ninguna prueba esencial ni ningún flujo productivo las ejecuta**: ni los golden, ni la GUI, ni la integración de 21 candidatos.

## 5. Anomalías

**Una prueba GUI falló una vez en la corrida instrumentada sobre el código BASE.** Es `tests/test_v112_01_esqueleto_dialogos.py::test_trabajador_informa_progreso_en_el_hilo_de_interfaz`:
- falló en la primera ejecución y en el reintento, con `resultado == []`: la señal del `QThread` aún no se había procesado al salir del bucle de espera;
- no toca `servicio_proyeccion` y ocurrió **antes** del retiro.

**Caracterización en el mismo equipo:**
- aislada: 25/25 PASS en la base y 25/25 en el final;
- archivo completo: 5/5 en cada uno;
- con el plugin: 15/15 aislada y 3/3 del archivo.

**No es reproducible**, y pasó en la base limpia, en el final local y en el CI. Es una carrera de tiempo heredada: el bucle termina con el hilo acabado sin esperar la señal en cola. Se declara aquí, no se oculta, y no se corrige: está fuera de alcance, junto a los otros problemas de temporización ya registrados en la Fase 1A.

## 6. Enlaces

| Qué | Enlace |
|---|---|
| Rama | https://github.com/estebanojeda0615/SAVIP/tree/maintenance/v1.1.2-fase2b-as003-opcion-b |
| Comparación con la Fase 2A | https://github.com/estebanojeda0615/SAVIP/compare/maintenance/v1.1.2-fase2a-as003...maintenance/v1.1.2-fase2b-as003-opcion-b |
| CI del código | [40578617725](https://github.com/estebanojeda0615/SAVIP/actions/runs/40578617725) (`10f1d0d`, success) |
| CI del HEAD final | Lo dispara el commit de documentación; se informa en el mensaje de entrega |
