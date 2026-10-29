# 05 · Informe de cierre del lote 2D-4 (AS-003)

## Dictamen: **APTO**

**Qué se retiró.** `seleccionar_modelo_por_evidencia` y sus 9 auxiliares de `modelos_interpretables.py`, todos con evidencia de no uso (G1), junto con la única prueba esencial que solo exigía su existencia.

**Verificación:**
- huella semántica exacta con 0 diferencias;
- 29 golden sin cambios;
- AS-001 en PASS;
- 803 ids esenciales, que son los 804 menos el retirado, todos en PASS;
- CI en verde.

Se declaran 2 intermitentes de la **línea base** sobre código sin modificar (04 §3).

## Cifras

| Indicador | Valor |
|---|---|
| Definiciones retiradas | **10** (332 líneas de definición) |
| Imports retirados | 2 (`UMBRAL_RRMSE_PEOR_BENCHMARK` y `TOLERANCIA_RRMSE_BENCHMARK`, solo en este módulo) |
| Líneas de producción eliminadas | **354** (332 de definición, 20 en blanco y 2 de imports); 0 añadidas |
| Archivos de producción tocados | 1: `modelos_interpretables.py`. `criterios.py`, sin cambios: 06 no asigna ficha a este lote |
| Pruebas | 1 esencial retirada y 0 adaptadas; 1 059 → 1 058 recolectadas |
| Ids esenciales | **804 → 803** |
| AS-003 restante | **21 definiciones y 1 391 líneas** en `servicio_proyeccion.py`, lotes 2D-1, 2D-2, 2D-3 y 2D-5 |

## Riesgos y pendientes

- **Texto extraído del PDF no determinista.** El golden `pdf_sesion` falló una vez en la línea base por un salto de línea distinto en el texto extraído del PDF. No es reproducible: 96 casos repetidos en PASS. Conviene estudiarlo aparte, sin cambiar golden ni comparadores.
- **Comentario restante.** `servicio_proyeccion.py:2592` menciona `seleccionar_modelo_por_evidencia` dentro de un comentario de una función heredada del lote 2D-3. Se limpia con ese lote o con 2D-6.
- **Lotes siguientes, NO autorizados:**
  - 2D-5 depende de la decisión AS-007 sobre `r3`;
  - 2D-2 y 2D-1 dependen de AS-028 y AS-004;
  - 2D-3 depende de la regla del punto no finito y de «MAPE no calculable».

  No se inició ninguno.

## Ramas y versión

`main`, `develop/v1.1.2`, las ramas de las fases 0 a 2C, el tag y el Release `v1.1.2-rc.1` no se modificaron. No hubo merge, PR, tag, release, ejecutable ni ZIP.

## Enlaces

- Rama: https://github.com/estebanojeda0615/SAVIP/tree/maintenance/v1.1.2-fase2d-lote4
- Comparación: https://github.com/estebanojeda0615/SAVIP/compare/maintenance/v1.1.2-fase2c-registro-historico...maintenance/v1.1.2-fase2d-lote4
- Commits: `2b89a6c` (retiro y prueba), `2fa128d` (workflow) y el commit de documentación.
- CI del código: [40953589320](https://github.com/estebanojeda0615/SAVIP/actions/runs/40953589320), success, 803/803 y 0 fallos en la primera ejecución. El CI del HEAD final se informa en el mensaje de entrega.
