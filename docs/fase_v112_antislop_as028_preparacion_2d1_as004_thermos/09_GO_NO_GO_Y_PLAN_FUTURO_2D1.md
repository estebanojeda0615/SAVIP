# 09 · Dictámenes y plan futuro de 2D-1 (sin ejecutar)

Los tres dictámenes son **independientes**. **Ninguno autoriza a empezar 2D-1** ni ningún otro lote.

## 1. Dictamen AS-028 (script del lote 2D-1): **GO**

- El script `pruebas/prueba_horizonte_dinamico_ui_reportes.py` ya no tiene **ninguna dependencia ejecutable** de `determinar_horizonte_maximo_estadistico`. El nombre solo queda en el comentario de la lápida (02 §5).
- Con 2D-1 oculto en memoria, recoge y ejecuta sus 26 pruebas con **los mismos estados id por id** que con 2D-1 visible: 19 PASS y 7 FAIL históricos (06 §3).
- Las tres bajas están justificadas aserción por aserción como **HISTÓRICA / NO APLICA**: ningún contrato vigente pierde protección (02).
- Ningún FAIL histórico se ocultó ni pasó a PASS. Las otras 26 pruebas, `main()` (salvo las 3 llamadas) y drift/holt quedan intactas.
- Queda **sin uso** el auxiliar `_evaluacion_horizonte`. Se conservó por alcance estricto y es candidato a retiro en el lote 2D-1 autorizado.

## 2. Dictamen AS-004 (generador histórico): **NO-GO POR DEPENDENCIAS** (diagnóstico completo)

- **AS-004 no se ejecutó ni se limpió.** El generador no cambió.
- Hay un **consumidor productivo** que lee claves antiguas y publica **columnas visibles**: `construir_dataframe_reproducibilidad`, el CSV reproducible.
  - Esas columnas forman parte del **Golden Master inmutable** `sesion_exportables` y del CSV de la V1.1.2 original, y el esencial `tests/test_presentacion_resultados.py::test_exportable_diferencia_recomendado_evaluado_y_limite_operativo` exige leer 4 de esas claves.
  - Con sesiones heredadas muestran valores antiguos: se comprobó inyectando una (04 §2).
  - Retirar esas lecturas o columnas **cambiaría un exportable**. Bajo «no permito nuevas diferencias», eso es NO-GO.
- La cadena `generar_reporte_html` → `_lineas_*` es **SOLO TEST**: no tiene efecto productivo. Su retiro sí sería viable con una fase preparatoria (04 §5, recomendación b):
  1. migrar el contrato vigente de `test_pool_calendario_fourier_seasonal::test_casoJ…` al informe productivo;
  2. explicitar la protección de las columnas del CSV;
  3. quitar la importación sin uso de `test_resultado_horizonte_solicitado`.
- **AS-004 no bloquea técnicamente 2D-1.** Las lecturas no dependen de que existan las 6 funciones: 0 diferencias en las salidas con 2D-1 oculto (07 §4).

## 3. Dictamen del lote 2D-1 productivo: **GO SOLO PARA SOLICITAR PROMPT**

- **El inventario está completo:**
  - grafo cerrado de 420 líneas;
  - 0 consumidores productivos;
  - 0 llamadas en 28 ejecuciones reales;
  - 0 diferencias de salida con las funciones ocultas;
  - 18 ids esenciales y 1 histórico afectados, todos identificados con su causa y destino (05 y 06).
- **Falta autorización expresa** para lo que 2D-1 exigiría. El lote no es ejecutable sin ella:
  1. dar de baja **8 ids esenciales** que solo ejercen la función muerta (6 + 2);
  2. **adaptar** 9 ids vigentes, quitando el nombre del `import` de nivel de módulo, sin tocar ninguna aserción;
  3. adaptar la Fase 1A para que exija la **ausencia** de la función;
  4. decidir el destino de `test_cierre_metodologico::test_no_queda_cascada…` (histórica);
  5. decidir, con AS-024, los metadatos de `C-ALC-002`.
- **No hay riesgo de diferencias:** no hay campos públicos sin conciliar que dependan de 2D-1 (la dependencia de AS-004 es de claves, no de funciones).

## 4. Propuesta para el próximo prompt de 2D-1 (no ejecutada)

| Paso | Contenido | Prueba de aceptación |
|---|---|---|
| 0 | Base: HEAD documental de esta fase | Los mismos SHA y CI |
| 1 | Commit de **pruebas**, antes de tocar producción: quitar `determinar_horizonte_maximo_estadistico` del `import` de `tests/test_resultado_horizonte_solicitado.py` L10-16; retirar sus 6 ids de la función muerta y los 2 de `test_presentacion_resultados`, con lápida; pasar el nombre de `retirados` a `eliminados` en la Fase 1A, **pero solo en el mismo commit en que desaparezca la función** (si no, la aserción de ausencia fallaría antes) | Perfil esencial: 809 − 8 = **801** ids, con las bajas listadas una por una y 0 fallos |
| 2 | Commit de **producción**: retirar las 6 definiciones (`servicio_proyeccion.py` L3274-3531 y L3534-3737, sin `_mayor_horizonte_permitido`, L3653-3684) y conservar `_tipo_uso_horizonte` y `_mayor_horizonte_permitido` hasta 2D-3. Actualizar la Fase 1A a ausencia, en el mismo commit | El grafo no deja ninguna llamada colgante; 801/801 |
| 3 | Higiene documental opcional, solo si se autoriza: comentarios de `analisis_series.py` L712-713 y L797, `presentacion_resultados.py` L1333 y la ficha `C-ALC-002` | Sin efecto sobre el bytecode ejecutado de la ruta productiva |
| 4 | Equivalencia | Oráculo de 66 escenarios: 66/66 frente a esta fase y 65/66 frente a la original (solo AS-001). Huella `d6be699b…` idéntica. Golden 29/29 con tolerancia cero. Sonda AS-004 con 0 diferencias |
| 5 | Script histórico | Sin cambios: ya no depende de 2D-1 |
| 6 | Opcional, si se autoriza | Retirar `_evaluacion_horizonte` del script, que quedó sin uso |
| 7 | Thermos con dos pasadas y CI del código y de los docs | Las mismas reglas |

**Reversión de esta fase,** no destructiva y en orden inverso:

```bash
git revert <commit-docs> 56d9562 7993060 5133abc 19c4649
```

No es necesaria: ninguna comprobación la motiva.
