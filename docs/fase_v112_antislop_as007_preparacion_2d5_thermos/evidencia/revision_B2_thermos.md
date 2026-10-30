# Thermos B, segunda pasada · alcance 6ac158d...c656e19

**Invocación.** Skill `thermos:thermos` (Thermos 1.1.0), que lanza en segundo plano y en paralelo los agentes `thermos:thermo-nuclear-reviewer` y `thermos:thermo-nuclear-code-quality-reviewer`. Entradas: `diff_B2_codigo.patch` y `diff_B2_delta_correcciones.patch`. Claude Code 2.1.238, revisión en solo lectura. Lo que sigue es la salida de cada revisor, condensada sin alterar sus hallazgos.

## thermo-nuclear-reviewer (corrección, seguridad y regresiones)

**Resultado: ningún hallazgo crítico, alto ni medio.**

**Comprobado:**
- Pruebas: 9/9 PASS.
- Escaneo del objeto: la única ruta con errores por ventana es `errores_extremos.observaciones[*].error_absoluto` (504 entradas).
- Superficies limpias: sesión, CSV, HTML, el PDF real extraído con pypdf y el DOCX con el anexo de backtesting.
- `_tramo()` coincide con `_texto_evidencia_oos` y con los literales de `TRAMO_OOS_*`.
- Runner: el import de `tests.test_informes_rediseno` funciona con él. Hay precedente en el perfil esencial, y si llegara a fallar fallaría a la vista.

**Hallazgos BAJOS:**
- **BAJO-1.** El primer párrafo del docstring del módulo y el nombre de C1 todavía insinúan que el objeto está limpio. Remedio: acotar el párrafo y renombrar C1. A1 se da por resuelto en lo esencial: no hay falso verde y el residual queda escalado.
- **BAJO-2.** C7 importa un módulo histórico que, al importarse, lanza una proyección n=72 (unos 11 s). Es una dependencia frágil. Remedio: copia local.
- **BAJO-3.** C7 no lee la portada ni el pie, que el PDF sí dibuja.
- **BAJO-4.** C6 y C7 nunca generan el anexo de backtesting, que es la única tabla por ventana del informe. Remedio: `replace(cfg, secciones=cfg.secciones | {"anexos"}, incluir_anexo_backtesting=True)`.
- **BAJO-5.** Los encabezados se comparan por igualdad exacta y no detectan «Error absoluto». Es una hipótesis: ningún encabezado actual cae en ese caso.
- **BAJO-6 (nota).** Los docstrings citan documentos 04 y 05 que todavía no existían.

**Estado de la primera pasada:**

| Hallazgo | Estado |
|---|---|
| A1 | Resuelto en lo que toca al cambio |
| B1 | Parcial (faltaban portada y pie) |
| B2 | Parcial |
| B3, B4, B5, B6 | Resueltos |

## thermo-nuclear-code-quality-reviewer (calidad y mantenibilidad)

**Veredicto: aprobable con una condición.**

**Hallazgos:**
- **N1, MEDIO.** C7, que es esencial, queda acoplada a un módulo histórico que lanza una proyección al importarse: 10,9 s, y el archivo pasa de unos 10,5 s a 25,4 s. Es la dirección equivocada: lo esencial pasa a depender de lo histórico. Remedio: copiar el extractor completo con portada y pie.
- **N2, BAJO.** El docstring de C7 promete más de lo que mira, porque no cubre la portada ni el pie.
- **N3, BAJO.** Queda el nombre viejo del archivo en `00_ESTADO_BASE...md:48`.
- **N4, BAJO.** El conjunto de encabezados prohibidos se reconstruye dentro del doble bucle.

**Estado de la primera pasada:**

| Hallazgo | Estado |
|---|---|
| 1 | Resuelto en cobertura, pero con la deuda N1 |
| 2 | Resuelto |
| 3 | Diferido con justificación: el disparador está en el CSV; como sugerencia opcional, una referencia en r3 |
| 4 | Resuelto |
| 5 | Resuelto, con el resto N3 |
| 6 | Diferido con justificación |
| A1 | Acotado y declarado. Sugerencia opcional: `xfail(strict=True)` como alarma |

**Condición:** corregir N1 (lo que cierra también N2) y N3.

## Tratamiento posterior: commit `da04725`, más las docs

| Hallazgo | Estado | Qué se hizo |
|---|---|---|
| N1 / BAJO-2 | **Resuelto** | Extractor local copiado del canónico y ampliado con portada y pie. Ya no se importa el módulo histórico. El archivo tarda unos 11 s |
| N2 / BAJO-3 | **Resuelto** | Mutación `portada_pie` detectada por C7 |
| BAJO-4 | **Resuelto** | El informe de C6 y C7 incluye el anexo de backtesting. Mutación `anexo_error` detectada por C6 |
| BAJO-1 | **Resuelto** | C1 pasa a llamarse `test_p0c_tablas_de_ventanas_sin_errores_ni_limites_ci` y el primer párrafo queda acotado |
| N4 | **Resuelto** | Constante `ENCABEZADOS_PROHIBIDOS` |
| N3 | **Resuelto** | En 00 |
| BAJO-5 | **No aplicado (hipótesis)** | Comparar por subcadena daría falsos positivos con el anexo activado, cuyo encabezado legítimo es «Índice observado». Se mantiene la igualdad sobre la lista de r3 más los nombres internos |
| BAJO-6 | **Resuelto** | 02, 04 y 05 existen en el HEAD documental |
| `xfail(strict=True)` para A1 | **No aplicado** | El prompt de la fase prohíbe usar xfail para obtener PASS. Decide el propietario (05) |
| Duplicado C1–C7 en r3 | **Diferido** | El prompt prohíbe retirar comprobaciones de r3 en esta fase. El disparador está en el CSV |

Las 13 mutaciones en memoria se detectan todas (14 tras la 3.ª pasada: `anexo_escalado`): [`mutaciones_pruebas_nuevas.txt`](mutaciones_pruebas_nuevas.txt).
