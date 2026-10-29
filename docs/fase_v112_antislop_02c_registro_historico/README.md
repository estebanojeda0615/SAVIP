# Fase 2C (AS-003): registro histórico y preparación del retiro

Base: `2f70391` (Fase 2B). Sin cambios de producción.

| Archivo | Contenido |
|---|---|
| [00_ESTADO_BASE_Y_ALCANCE.md](00_ESTADO_BASE_Y_ALCANCE.md) | Referencias remotas, entorno, línea base y alcance |
| [01_INVENTARIO_DEFINICIONES_AS003.csv](01_INVENTARIO_DEFINICIONES_AS003.csv) | Las 31 definiciones heredadas: líneas, qué hacen, consumidores, ficha, recomendación, lote y enlace inmutable |
| [02_REGISTRO_HISTORICO_METODOLOGICO.md](02_REGISTRO_HISTORICO_METODOLOGICO.md) | Metodología vigente, reglas retiradas, motivos, trazabilidad, recuperación desde Git y lo que no se sabe |
| [03_MATRIZ_MIGRACION_PRUEBAS.csv](03_MATRIZ_MIGRACION_PRUEBAS.csv) | Los 95 ids o comprobaciones que dependen del código heredado, con su destino en 2D |
| [04_AS024_CRITERIOS_Y_REFERENCIAS.md](04_AS024_CRITERIOS_Y_REFERENCIAS.md) | Fichas de `criterios.py` afectadas y cambio propuesto (sin aplicar) |
| [05_AS028_SCRIPTS_Y_APIS.md](05_AS028_SCRIPTS_Y_APIS.md) | Scripts de `pruebas/` y API `ejecutar_analisis`: estado medido y destino propuesto |
| [06_PLAN_EJECUCION_FASE_2D.md](06_PLAN_EJECUCION_FASE_2D.md) | Lotes cerrados, decisiones previas, GO/NO-GO y reversión |
| [07_EVIDENCIA_PRUEBAS_Y_CI.md](07_EVIDENCIA_PRUEBAS_Y_CI.md) | Recuentos, ids, golden, huella, CI y comandos |
| [08_INFORME_CIERRE_FASE_2C.md](08_INFORME_CIERRE_FASE_2C.md) | Dictamen y respuestas numeradas |
| [evidencia/](evidencia/) | Scripts reproducibles y resúmenes (sin huellas completas ni datos reales) |

Pruebas nuevas: [`tests/test_fase2c_contratos_vigentes.py`](../../tests/test_fase2c_contratos_vigentes.py).
