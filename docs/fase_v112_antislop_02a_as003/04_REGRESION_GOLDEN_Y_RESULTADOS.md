# 04 · Regresión, Golden Masters y resultados

Todas las comparaciones locales se hicieron en el **mismo equipo y entorno** (00 §2), sobre copias limpias.

## 1. Huella semántica exacta

**Herramienta.** [`evidencia/huella_semantica.py`](evidencia/huella_semantica.py) captura los 5 escenarios sintéticos del Golden Master del motor con los horizontes consultados 1, 11, 23 y 24, es decir, 20 casos. Por caso guarda:
- el **resultado completo** de `ejecutar_proyeccion` (las 65 claves públicas y todo lo anidado), sin campos de reloj;
- el **SSE exacto** (`Fraction`) de los 21 candidatos sobre la muestra común;
- los pares comunes;
- el número de llamadas al selector.

Añade además la economía (12 factores, 7 importes, 6 rechazos, factor legado y empalme) y los rechazos de horizonte y de historia insuficiente.

**Cómo se compara.** Igualdad exacta, sin tolerancia. Los float se comparan por su `repr`.

| Comparación | Diferencias |
|---|---|
| Línea base consigo misma (2 capturas) | **0**: archivos idénticos byte a byte (SHA-256 `d6be699b…`) |
| Línea base frente al Lote 1 | **0**: mismo SHA-256 |

**Resultado por escenario.** El ganador, el segundo, el RMSErect, los pares comunes y la trayectoria de 24 meses son idénticos con los 4 horizontes consultados: consultar otro horizonte no cambia el modelo ni la trayectoria.

| Escenario | Ganador | Segundo | RMSErect | Pares comunes | Trayectoria |
|---|---|---|---|---|---|
| estacional | `fourier_k1__exponencial_log_lineal` | `fourier_k1__huber` | 0,42354816475952406 | 888 | 24 meses |
| exponencial | `exponencial_log_lineal` | `fourier_k1__exponencial_log_lineal` | 0,313069726353369 | 312 | 24 |
| lineal_exacta_empate | `lineal` | `holt_lineal` | 0,0 | 24 | 24 |
| paseo_aleatorio | `seasonal_naive` | `naive` | 3,018305948174487 | 120 | 24 |
| tendencia_lineal_ruido | `fourier_k1__exponencial_log_lineal` | `exponencial_log_lineal` | 1,2765909871825984 | 600 | 24 |

Detalle en [`evidencia/huella_resumen.txt`](evidencia/huella_resumen.txt). Los JSON completos, de unos 155 MB, se conservan localmente y no se publican.

## 2. Perfil esencial y Golden Masters

| Ejecución | Pruebas | PASS | FAIL | XFAIL | SKIP | Intermitentes | Golden | Tiempo (JUnit) |
|---|---|---|---|---|---|---|---|---|
| Línea base local, copia limpia de `c9166c6` | 797 | 797 | 0 | 0 | 0 | ninguna | 29/29 | 1 838 s |
| Espía G2 sobre `c9166c6` (02 §1) | 797 | 797 | 0 | 0 | 0 | ninguna | 29/29 | — |
| **Final local, copia limpia del Lote 1** (`81a8247`, el mismo código del HEAD final) | **797** | **797** | **0** | **0** | **0** | ninguna | **29/29** | 1 691 s |
| **CI [40445532574](https://github.com/estebanojeda0615/SAVIP/actions/runs/40445532574)**, `81a8247` | **797** | **797** | **0** | **0** | **0** | ninguna | 29/29 | 61 min |

- **Mismo conjunto de pruebas.** Los 797 ids de prueba esencial, por clase y nombre en el JUnit, son **idénticos** en la base y en el final. Ningún caso esencial se perdió ni se sustituyó.
- **Recolección.** `pytest --collect-only tests` da 1 061 ids idénticos en la base y en el final, con los mismos 3 errores de recolección previos. `--listar` da el mismo recuento por perfil (`evidencia/listar_*.txt`).
- **Golden Masters.** No se modificaron sus fixtures, sus tolerancias ni el comparador: `git diff c9166c6 -- tests/` está vacío.
- **Otras comprobaciones:**
  - AS-001 sigue en PASS (`test_as001_*`, 16 casos, dentro del perfil);
  - la integración con 21 candidatos y los horizontes 1, 11 y 24 pasa.

## 3. Resultados funcionales y de aplicación

| Aspecto | Evidencia | Resultado |
|---|---|---|
| Modelo, segundo, RMSErect, SSE exacto, pares, trayectoria H1–H24, MAE(h), sesgo | Huella exacta + golden del motor | Idénticos |
| Cifras económicas, factores, importes, empalme | Huella exacta + golden económico | Idénticos |
| Sesiones y exportables Excel (con fórmulas), PDF, DOCX y CSV | Golden de sesiones y exportables (12 casos) | PASS |
| Arranque e importaciones Qt (offscreen) | Importar los módulos de `app_icociv` y `aplicacion` + flujos GUI del perfil esencial | Sin errores |
| `compileall` | `app_icociv`, `aplicacion.py`, `scripts`, `pruebas` | OK |
| `packaging/SAVIP.spec` | Los imports retirados (`hashlib`, `datetime`) son de la biblioteca estándar y no figuran en `hiddenimports`; el `.spec` no cambia | Compatible; no se compiló ningún ejecutable |

## 4. Pruebas históricas relacionadas con AS-003

**Qué se ejecutó.** Los 11 archivos no esenciales que citan funciones candidatas, archivo por archivo, en la base y en el Lote 1 ([`evidencia/historicas_as003.txt`](evidencia/historicas_as003.txt)). Resultado: **el mismo estado**.
- **12 fallos previos, con los mismos ids:**
  - `test_cierre_metodologico`: 1;
  - `test_horizonte_evidencia_reducida`: 3;
  - `test_integracion_fhg`: 2;
  - `test_p0g_desacople_punto_intervalo`: 6.
- **2 errores de recolección previos:** los dos `test_p0c_*`.
- **Pasan en ambos:**
  - `test_p0d_rmse_orden_exacto`: 13;
  - `test_rmse_global_estable`: 11;
  - `test_seleccion_rmse_global`: 16.
- **Sin pruebas en ambos:** los 2 archivos de auditoría independiente (`no tests ran`).

**Lectura.** Ningún fallo nuevo. Los existentes son deuda histórica documentada en la Fase 1A (02 §4), no regresiones.

## 5. Salvedades sobre la CPU

- **Equipo de los resultados locales.** Todos salen del mismo equipo, un AMD Family 25.
- **Golden en el CI.** El CI corre en `windows-latest`, con otra CPU. Allí los golden usan la tolerancia existente de 1e-2, solo para el RMSErect de candidatos perdedores de Holt/Huber, y 1e-9 para todo lo demás. No se amplió y no hubo fallos.
- **Huella exacta.** Se comparó solo en el mismo equipo, como pide el prompt. No hubo ninguna diferencia, ni siquiera en Holt/Huber: el código retirado no interviene en ningún cálculo.
