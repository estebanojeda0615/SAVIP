# 09 · Informe de cierre y dictamen del lote 2D-1

## Dictamen: **APTO CON RESERVAS DOCUMENTADAS**

Las reservas son **preexistentes** y **no alteran resultados ni contratos**:
1. se ejecutó la **fuente** `6672529` de la V1.1.2 original, no el EXE (la correspondencia 87/87 es de 2D-2);
2. la comparación **D** (V1.1.1 → V1.1.2) se reutilizó de 2D-2, sin repetirla;
3. los fallos, el tiempo agotado y los errores de las pruebas **históricas** son idénticos en la base y en el final.

No se detectó **ninguna** diferencia nueva. CI verde en el último commit de código y en el HEAD documental (ver el mensaje de entrega).

## 1. Seis definiciones

- **Retiradas** de `app_icociv/proyeccion/servicio_proyeccion.py` (420 líneas de definición, 432 con separadores, 0 añadidas):
  - `determinar_horizonte_maximo_estadistico`
  - `_serializar_evaluaciones_horizonte`
  - `_item_horizonte_global`
  - `_mayor_horizonte_con`
  - `_ultimo_horizonte_por_clasificacion`
  - `_evidencia_horizonte`
- **Conservadas:** los compartidos `_tipo_uso_horizonte` y `_mayor_horizonte_permitido`; todo 2D-3 (`_evaluar_horizontes_proyeccion`, `_clasificar_evidencia_horizonte`, `_aplicar_salvaguarda_benchmarks`…); `_resultado_sin_proyeccion`, con su plantilla y sus claves; `_estructurar_resultado_horizontes`; y el resto del motor. **El resto del módulo es idéntico en AST.**

## 2. Ocho ids retirados y protección vigente

**Retirados** (con lápida y la justificación de cada aserción en 02):
- `test_resultado_horizonte_solicitado`: `test_maximos_se_derivan_de_clasificaciones_y_no_del_limite_de_grilla`, `test_limite_evaluable_se_informa_sin_convertirlo_en_validez_absoluta`, `test_maximo_evaluado_20_es_descriptivo_de_la_funcion_retirada`, `test_20_puede_ser_maximo_recomendado_si_h20_es_tecnico`, `test_20_puede_ser_maximo_escenario_si_h20_es_escenario_explicito` y `test_parada_en_20_por_evidencia_incluye_advertencia_y_no_extrapola`.
- `test_presentacion_resultados`: `test_horizonte_dinamico_diferencia_tecnico_cautela_y_no_evaluado` y `test_horizonte_no_salta_un_corte_no_viable`.

**Siguen protegidos** (PASS):
- los 9 ids vigentes de `test_resultado_horizonte_solicitado` (solo se quitó un nombre del import);
- la guarda de la Fase 1A, que ahora exige la ausencia;
- la histórica de la cascada, con el mismo id y sin la aserción del símbolo eliminado;
- `test_metodologia_n0_12_h24`, la Fase 2C, `pool_calendario`, el CSV de AS-004 y 3c_a.

## 3. Cifras

| Requisito | Resultado |
|---|---|
| Esenciales | **801/801**, en local y en CI; 8 bajas exactas, 0 altas, 0 cambios |
| Golden | **29/29**; con tolerancia cero, 0 diferencias |
| AS-001 | **16/16**; umbral idéntico |
| Huella | **Idéntica**, 0 diferencias (`d6be699b…0191`) |
| Históricas | 213, idénticas por id y estado (163/50 preexistentes) |
| Script manual | 26: 19/7, idéntico |
| Colección | 1 028, con 3 errores históricos y **0 nuevos** |

## 4. Oráculo de 66 escenarios (ejecutado)

- **66/66 frente a la fase anterior** (`8e5a62b`), bit a bit.
- **65/66 frente a la V1.1.2 original** (`6672529` r4/r2); la única diferencia es **AS-001**, la misma que ya existía en la base.
- Frente a la captura r1 de la original aparece además un salto de línea del PDF que la propia original varía entre ejecuciones. El texto es idéntico; está documentado en 04 §3.

## 5. Cero diferencias nuevas

**No hay ninguna diferencia nueva** en estadística, economía, GUI, sesiones ni exportables:
- **Estadística:** SSE, RMSErect, selección, 21 candidatos, W*×24, H1-H24 y métricas.
- **Economía:** ICOCIV/ICCP, factor, unitarios, totales y empalme.
- **GUI y sesiones:** recorrido real de la GUI y sesión guardada y restaurada sin recalcular.
- **Exportables:** CSV completo con sus 17 columnas históricas, Excel, PDF y DOCX.

Se comprobó con el oráculo, el Golden con tolerancia cero, la huella, la sonda AS-004 (29 casos con las funciones ausentes) y los perfiles.

## 6. Thermos, CI, SHA, reversión y pendientes

| Elemento | Valor |
|---|---|
| Thermos | Dos pasadas reales con `thermo-nuclear-reviewer` y `thermo-nuclear-code-quality-reviewer`: **APROBADO** en las cuatro revisiones. Ningún hallazgo crítico, alto ni medio sin resolver dentro del alcance; las deudas están en 08 (07) |
| Rama | [`maintenance/v1.1.2-fase2d-lote1-equivalencia-original-thermos`](https://github.com/estebanojeda0615/SAVIP/tree/maintenance/v1.1.2-fase2d-lote1-equivalencia-original-thermos) |
| Commits | `5706e85` (administrativo), `fbaa0be` (G4.1, pruebas), **`406e1dd`** (G4.2, retiro atómico: **último commit de código**) y el commit documental (HEAD) |
| Comparación | https://github.com/estebanojeda0615/SAVIP/compare/8e5a62b00fbdac3819c755e509236c174ebcb78f...maintenance/v1.1.2-fase2d-lote1-equivalencia-original-thermos |
| CI del código | [43304324537](https://github.com/estebanojeda0615/SAVIP/actions/runs/43304324537): success en el **1.er intento**, 801/0 y JUnit verificado |
| CI del HEAD documental | Ver el mensaje de entrega. Sin `[skip ci]` |
| Reversión | `git revert <docs> 406e1dd fbaa0be 5706e85`, no destructiva y no ejecutada (03 §3) |
| Pendientes fuera de alcance | AS-004 (NO-GO por dependencias); AS-024 (C-ALC-002 apunta a un símbolo inexistente; propuesta en 08); 2D-3; 2D-6 (comentarios); `_evaluacion_horizonte` y `_evaluacion_horizonte_ui` sin uso; docstring de la histórica; guarda 1A ampliable; P0-C cancelado |

## 7. Matriz de requisitos

| Requisito del prompt | Estado |
|---|---|
| Base `8e5a62b` verificada; rama nueva; nada más tocado | Cumple (00) |
| Grafo, espías, rutas dinámicas y puerta de alcanzabilidad antes de borrar | Cumple (01) |
| Exactamente 6 definiciones por AST; compartidos conservados | Cumple (01, 03) |
| 8 bajas con lápida; 9 vigentes intactos; Fase 1A en el mismo commit; histórica con el mismo id | Cumple (02, 03) |
| AS-004 / CSV / sesiones / C-ALC-002 / comentarios sin cambios | Cumple (05, 08) |
| Equivalencia A, B, C (ejecutadas) y D (reutilizada, declarada) | Cumple (04) |
| 801 / 29 / 16 / huella / sonda / 3c_a | Cumple (06) |
| Thermos, dos pasadas y dos agentes | Cumple (07) |
| CI del código y de los docs, sin relanzamientos | Cumple (06; HEAD documental en el mensaje de entrega) |
| No ejecutar el EXE ni afirmarlo; sin merge, PR, tag ni release | Cumple |

## 8. Declaración

**Este lote no modificó ningún resultado:**
- ni la metodología, la SSE exacta, RMSErect, `_rmse_desde_sse`, el orden ni el desempate de los 21 candidatos, W*×24, N0=12, H=24, el backtesting ni la trayectoria;
- ni ICOCIV, ICCP, el empalme, la economía, la GUI, las sesiones, la recuperación de sesiones, los exportables, el packaging ni las dependencias.

La única excepción sigue siendo **AS-001**, sin cambios ni ampliación. P0-C sigue cancelado.

**FASE DETENIDA a la espera de la revisión del propietario.** No se inicia 2D-3, 2D-6, AS-004, AS-024 ni ningún otro lote.
