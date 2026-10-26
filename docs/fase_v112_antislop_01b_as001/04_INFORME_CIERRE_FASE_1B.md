# 04 · Informe de cierre de la Fase 1B (AS-001)

## Veredicto: **APTO**

**Qué se corrigió.** AS-001 está corregido en el único archivo de producción autorizado.

**Pruebas.**
- La prueba del hallazgo pasa sin `xfail`.
- Hay 15 casos adversariales nuevos.
- Los 29 Golden Masters no cambian.

**Perfil esencial y CI.**
- El perfil esencial, local y en CI, da 797 PASS, 0 FAIL, 0 XFAIL, 0 SKIP y ninguna intermitente ([run 40415465901](https://github.com/estebanojeda0615/SAVIP/actions/runs/40415465901)).
- El CI del HEAD final (documentación más `c42cbbf`) se informa en el mensaje de entrega.

**Alcance.** Solo se corrige AS-001; el motor **no** queda «completamente saneado».

## 1. Declaraciones expresas (§6)

| Declaración | Respuesta |
|---|---|
| ¿`test_as001_candidato_divergente_no_aborta_la_seleccion` es PASS sin XFAIL? | **Sí.** Se retiró el marcador en el mismo commit de la corrección (`8159d52`). No hay `skip`, `xfail` ni aserción debilitada. La aserción se reforzó: RMSE del segundo `== 1.2258e240` y diferencias finitas |
| ¿Se conservan el ganador y el segundo en escenarios ordinarios y extremos? | **Sí.** Ordinarios: las 19 pruebas previas, las 8 de bit a bit y los golden. Extremos: AS-001, ambos enormes, empate, 1 ULP en `DBL_MAX`, no finitos, muestra común y la ruta productiva con 21 candidatos, en la que ganador, segundo, RMSE y trayectoria H24 son idénticos con horizontes 1, 11 y 24 |
| ¿El RMSE representable es finito en el caso `1.2258e240`? | **Sí.** `rmse_segundo_oos == 1.2258e240`, finito y exacto. En 20 000 casos extremos hay 0 ULP de diferencia con la referencia Decimal de 100 dígitos |
| ¿Cambió algún Golden Master? | **No.** El diff de `tests/fixtures/fase0` está vacío, las tolerancias no cambian y los 29 pasan |
| ¿El perfil esencial y el CI quedaron en verde? | **Sí.** Local: 797/797. CI 40415465901: success, 797/797, ninguna intermitente |
| ¿Hubo modificaciones fuera del archivo de producción autorizado? | **No.** Producción: solo `servicio_proyeccion.py` (+22/−1). Fuera de producción: la prueba, el filtro de rama del workflow (autorizado) y la documentación con su excepción en `.gitignore` |
| ¿Qué problemas Anti-Slop siguen sin resolver? | Ver §4 |

## 2. Qué cambió

- **Función nueva.** `_rmse_desde_sse(sse, n)` (01 §1):
  - devuelve la misma expresión de siempre mientras `float(sse)` cabe en float;
  - si desborda, calcula la raíz desde la `Fraction` exacta con Decimal a 60 dígitos.
- **Lo que no cambia:** el orden por SSE exacto, el desempate, la muestra rectangular W*×24, los pesos, los 21 candidatos, el backtesting, la trayectoria de 24 meses y las claves públicas.
- **Consumidores.** Ninguno supone que los campos de diferencias son finitos (00 §5). La `diferencia_porcentual` puede valer `+inf` cuando la razón no cabe en float; se muestra como «No disponible» o se guarda como `null`. No hubo que cambiar ningún contrato.

## 3. Riesgos

- **Doble redondeo en el camino Decimal.** Es teórico (60 dígitos y luego 53 bits): como mucho 1 ULP en un empate de redondeo extremadamente raro. Medido: 0 casos en 20 000. Solo afecta al número informado, nunca al orden.
- **Subdesbordamiento.** Con errores menores que ~1e-162, el RMSE informado es 0 y `diferencia_porcentual` vale `nan`. Ya ocurría antes, no aborta y la selección sigue siendo correcta (01 §5). Está muy lejos de los errores reales.
- **Variación entre CPU (Holt/Huber).** Se mantiene la holgura documentada en la Fase 0, sin ampliarla. No hubo diferencias en esta fase.
- **Reintento único del CI.** Sigue en 1. Este run no lo necesitó (ninguna intermitente). La lista debe revisarse en cada run.

## 4. Pendientes Anti-Slop (no abordados aquí)

- **AS-003 y AS-004:** código redundante y retirado. Incluye:
  - el selector `seleccionar_modelo_por_rmse_oos_global`;
  - `_rmse_global_estable` y los demás retirados;
  - sus 75 pruebas y sus consumidores en `pruebas/`.
- **AS-007 parcial (Fase 1A, 04 §2):**
  - expectativas de reutilización (10) y de la metodología 12/24 (25);
  - evidencia histórica `.bak` (8 + 3C-B);
  - dependencias perdidas (3);
  - carreras de tiempo en el perfil gui (5);
  - escrituras a nivel de módulo de pruebas históricas: `test_visual_fase_3c_b` crea `docs/fase_3c_b/temporal` al recolectarse.
- **El resto de la auditoría Anti-Slop.** Ninguno de estos puntos se tocó en esta fase.

## 5. Recomendaciones

1. Revisar este informe y el diff antes de autorizar la fase siguiente (AS-003).
2. **Opcional, fuera de alcance:** cubrir el subdesbordamiento con la misma rama Decimal cuando `float(sse) == 0` y `sse != 0`. Solo cambiaría el número informado en errores de ~1e-162 o menores; requiere autorización.
3. En la limpieza de AS-003, conservar `_sse_exacto` y `_rmse_desde_sse`, que son los que usa el selector vigente, y retirar `_rmse_global_estable` junto con el selector antiguo.

## 6. Enlaces

| Qué | Enlace |
|---|---|
| Rama | https://github.com/estebanojeda0615/SAVIP/tree/maintenance/v1.1.2-fase1b-as001 |
| Comparación con la Fase 1A | https://github.com/estebanojeda0615/SAVIP/compare/maintenance/v1.1.2-fase1a-as006-as007...maintenance/v1.1.2-fase1b-as001 |
| CI de la corrección | [40415465901](https://github.com/estebanojeda0615/SAVIP/actions/runs/40415465901) (`df4fb16`, success) |
| Commits | `8159d52` (corrección), `df4fb16` (workflow), `c42cbbf` (prueba de horizontes), commit de documentación |
