# 06 · Informe de cierre: AS-007 y preparación del lote 2D-5

## Veredicto: **APTO CON RESERVAS**

**Lo que se cumple:**
- r3 queda preparado para 2D-5, sin importaciones que vayan a romperse.
- Los contratos vigentes que solo afirmaba r3 son ahora 9 pruebas esenciales, cuya sensibilidad está comprobada con 14 mutaciones.
- Se conservan los 803 ids esenciales, los 29 golden y AS-001.
- La huella es exacta, con 0 diferencias.
- No hay ningún cambio de producción.
- Thermos se ejecutó de verdad en tres pasadas sobre el diff, y no queda ningún hallazgo crítico, alto ni medio del cambio sin resolver.
- CI verde.

**Reservas (no se ocultan):**
1. **Residual P0-C de producción (ALTO, anterior a esta fase).** El IC95 retirado se reconstruye bit a bit desde `backtesting_comparativo.<modelo_h>.metricas.errores_extremos.observaciones[*].error_absoluto`. Esta fase no puede corregirlo, porque `app_icociv/**` está prohibido. Ninguna prueba lo cubre y la prueba C1 lo declara fuera de su alcance. Lo tiene que decidir el propietario (05 §3).
2. **AS-007 solo está resuelto en parte.** Queda resuelto r3 respecto a 2D-5. Siguen abiertos:
   - los dos `test_p0c_*`, con error de recolección;
   - `bghc`;
   - PS-02 / anexo DANE;
   - las decisiones C12 `Periodo`, las claves de traza sin productor y H1–H6.
3. **El perfil esencial completo en local se ejecutó sobre `da04725`.** El último commit de código, `1f6fa6a`, solo cambia el archivo nuevo de pruebas. Su perfil completo lo da el CI (§4).

## 1. Qué se modificó

| Archivo | Cambio |
|---|---|
| `tests/test_residuales_auditoria_independiente_r3.py` | Ya no importa `tramo_evidencia_oos` ni `TRAMO_OOS_*`. Usa un `_tramo()` local que lee `_texto_evidencia_oos`, con las mismas fronteras, y falla si no reconoce el texto. Se cambian literales por constantes. Diff de +23/−11, y los 27 controles quedan intactos |
| `tests/test_as007_contratos_r3_vigentes.py` | **Nuevo**, con 9 pruebas: C1–C7, la parte vigente de C12 y la parte P0-E de HG5. El informe incluye el anexo de backtesting, y el extractor de texto cubre portada, pie y los ocho tipos de bloque |
| `scripts/pruebas_fase0.py` | +1 entrada en `ESENCIALES` con su comentario |
| `.github/workflows/fase0-pruebas.yml` | +1 línea en el filtro de ramas |
| `.gitignore` | +1 excepción para esta carpeta |
| `docs/fase_v112_antislop_as007_preparacion_2d5_thermos/` | Informes 00–06 y evidencias |

**Lo que no se modificó:**
- `app_icociv/**`, incluidos `tramo_evidencia_oos`, `TRAMO_OOS_*` y `_texto_evidencia_oos`;
- `aplicacion.py`, `packaging/**`, `VERSION`, `requirements*` y `tests/fixtures/**` (golden y tolerancias);
- PS-03 y las 21 definiciones AS-003;
- la metodología N0=12, H=24, W*×24, los 21 candidatos, SSE y RMSErect;
- la economía;
- `main`, `develop/v1.1.2`, las ramas anteriores, y el tag y release `v1.1.2-rc.1`.

No hubo merge, PR, release, EXE ni ZIP. `git diff 6ac158d HEAD -- app_icociv aplicacion.py packaging VERSION requirements*.txt tests/fixtures` está vacío.

## 2. Commits (autor y confirmador: Esteban Ojeda, sin trailers)

| Commit | Contenido |
|---|---|
| `fceadea` | docs 00/01, filtro del workflow y `.gitignore` |
| `febd981` | Pruebas nuevas, r3 sin `tramo_evidencia_oos` y entrada en `ESENCIALES` |
| `c656e19` | Correcciones de la 1.ª pasada de Thermos B |
| `866d2e4` | docs 02, evidencias y salidas de Thermos A y B (1.ª pasada) |
| `da04725` | Correcciones de la 2.ª pasada de Thermos B |
| `1f6fa6a` | Correcciones de la 3.ª pasada de Thermos B (último commit de código) |
| HEAD documental | docs 03–06, evidencias finales y ajustes de 00–02 |

## 3. Resultados

| Indicador | Valor |
|---|---|
| Ids esenciales | 803 → **812**. Los 803 originales están todos presentes y en PASS; se suman 9 nuevos y no cambia el estado de ninguno (03 §2) |
| Golden / AS-001 | **29/29** · **16/16** |
| Huella | 20/20 casos, **0 diferencias**, SHA-256 `d6be699b…0191` idéntico |
| Recolección | 1 058 → 1 067, con los mismos **3 errores históricos**, que no se declaran resueltos |
| r3 directo | **21/27, idéntico** a la base (los mismos 6 fallos previos: C12, HG4, HG5, HG6, B y G) |
| 2D-5 simulado | Errores de recolección: base 4 frente a rama final **3**. r3 21/27. PS-03 falla al ejecutarse, como se espera |
| Sensibilidad | **14/14** mutaciones detectadas |
| Primeras ejecuciones e intermitentes | 0 fallos en primera ejecución en todas las ejecuciones locales y de CI de esta fase. Ninguna intermitente. Las conocidas (`test_interaccion_fase_3c_a::test_a` y `pdf_sesion`) no aparecieron |

## 4. CI (GitHub Actions, `fase0-pruebas`)

| Run | Commit | Resultado |
|---|---|---|
| [41003966465](https://github.com/estebanojeda0615/SAVIP/actions/runs/41003966465) | `fceadea` | success · 803/803 · 0 fallos en la 1.ª ejecución |
| [41004130161](https://github.com/estebanojeda0615/SAVIP/actions/runs/41004130161) | `febd981` | success · 812/812 · 0 |
| [41007527954](https://github.com/estebanojeda0615/SAVIP/actions/runs/41007527954) | `c656e19` | success · 812/812 · 0 |
| [41007657860](https://github.com/estebanojeda0615/SAVIP/actions/runs/41007657860) | `866d2e4` | success · 812/812 · 0 |
| [41012146058](https://github.com/estebanojeda0615/SAVIP/actions/runs/41012146058) | `da04725` | success · 812/812 · 0 |
| [41014677965](https://github.com/estebanojeda0615/SAVIP/actions/runs/41014677965) | `1f6fa6a` | Ver el mensaje de entrega |
| — | HEAD documental | Ver el mensaje de entrega |

Todos los runs terminaron en su primer intento (`run_attempt` 1).

## 5. Thermos (04)

- **Versión:** Thermos 1.1.0 sobre Claude Code 2.1.238.
- **Cómo se invocó:** con la skill `thermos:thermos`, que lanzó en paralelo los dos agentes del plugin en cada pasada. El primer intento por CLI sin interfaz falló con «Not logged in», y lo dejo registrado.
- **A (2D-4, referencia):** sin hallazgos críticos ni altos. Quedan restos huérfanos de producción, deferidos (04 §2).
- **B1:** dos ALTOS, el falso verde de C1 y el extractor de PDF incompleto, más varios medios y bajos. Todos resueltos o diferidos con su justificación.
- **B2:** el revisor de corrección no encontró nada crítico, alto ni medio. El de calidad aprobó con una condición: N1, el acoplamiento a un módulo histórico. Se resolvió.
- **B3**, sobre el delta `c656e19..da04725`: el revisor de corrección no encontró nada crítico, alto ni medio ni ningún defecto nuevo. El de calidad dio **«Aprobado»**. Sus bajos están aplicados en `1f6fa6a`, que no tuvo una 4.ª pasada: es un delta de 14 líneas que siguió al pie de la letra el remedio propuesto, y lo verifiqué con 14 mutaciones.
- Thermos solo revisa el diff. Los resultados de Thermos se presentan separados de los de las pruebas.

## 6. Riesgos

- El residual P0-C (reserva 1) existe en el objeto en memoria. Las superficies persistidas e impresas están limpias.
- La duplicación C1–C7 entre r3 y el archivo nuevo está declarada, con una condición de retiro en 01. Las dos copias pueden divergir.
- El extractor de texto está duplicado respecto a `test_informes_rediseno` y declarado en su docstring.
- Hay pruebas históricas no esenciales con fallos previos, por ejemplo `test_cierre_metodologico::test_no_hay_modelo_por_horizonte`, detectada por Thermos A. Esta fase no las altera.

## 7. Propuesta para el próximo lote

1. **2D-5:** solicitar autorización con el alcance de 05 §2. Implica retirar la función, las constantes con autorización expresa, el id PS-03 en el mismo commit y, opcionalmente, C1–C7 de r3.
2. **Fase de producción P0-C:** cerrar el residual de `errores_extremos.observaciones` con una prueba que hoy falle.
3. **2D-6:** limpiar los restos de 2D-4 que señaló Thermos A.
4. **Decisiones pendientes:** C12 `Periodo`, claves de traza (tipo AS-004), H1–H6, punto no finito y MAPE no calculable (2D-3).
5. **Proceso:** en la comprobación G1 de cada lote, buscar también constantes de módulo y claves de diccionario. Pasar a patrones en el filtro del CI y en `.gitignore`.

## 8. Enlaces

- Rama: https://github.com/estebanojeda0615/SAVIP/tree/maintenance/v1.1.2-as007-preparacion-2d5-thermos
- Comparación con la base: https://github.com/estebanojeda0615/SAVIP/compare/maintenance/v1.1.2-fase2d-lote4...maintenance/v1.1.2-as007-preparacion-2d5-thermos

No se retiró `tramo_evidencia_oos` ni se inició el lote 2D-5; no se modificó código productivo, ramas estables ni release.
