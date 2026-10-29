# 04 · CI y regresión

## 1. Perfil esencial

| Ejecución | Ids | PASS | FAIL | XFAIL | SKIP | Fallos en la 1.ª ejecución | Intermitentes | Golden | Tiempo |
|---|---|---|---|---|---|---|---|---|---|
| Local, base `83549e7` | 804 | 804 | 0 | 0 | 0 | **2** | **2** (ver §3) | 29/29 tras el reintento | 1 914 s |
| **Local, después** (código de `2fa128d`) | **803** | **803** | **0** | **0** | **0** | **0** | ninguna | **29/29** | 1 874 s |
| **CI [40953589320](https://github.com/estebanojeda0615/SAVIP/actions/runs/40953589320)**, `2fa128d` | **803** | **803** | **0** | **0** | **0** | **0** | ninguna | 29/29 | 41 min |

## 2. Ids antes y después

Comparación de los JUnit de la primera ejecución, por `(classname, name)`, en [`evidencia/comparacion_ids_esenciales.txt`](evidencia/comparacion_ids_esenciales.txt):
- **solo antes: 1**, `test_fundamentacion_metodologica::test_el_selector_retirado_conserva_su_definicion_para_auditoria`, el retirado;
- solo después: 0;
- **los 803 ids restantes son exactamente los 804 de la base menos el retirado, y todos pasan**.

El comparador marca 2 «estados cambiados»: son las 2 intermitentes de la base (§3), que fallaron en su primera ejecución y pasan en la ejecución final.

**Recolección** ([`evidencia/coleccion_diff.txt`](evidencia/coleccion_diff.txt)): 1 059 → 1 058. Solo desaparece el id retirado, y los 3 errores previos siguen igual.

## 3. Intermitentes de la línea base (código sin cambios, `83549e7`)

**Se declaran expresamente.** La base pasó gracias al reintento: 2 pruebas fallaron en la primera ejecución y pasaron al reintento. Detalle en [`evidencia/intermitentes_linea_base.txt`](evidencia/intermitentes_linea_base.txt).

1. **`test_fase0_golden_sesion_exportables::test_golden_sesion_exportables[pdf_sesion]`.**
   - Dos diferencias en el texto extraído del PDF: la palabra «Registros» pasa a la línea anterior. El contenido es el mismo; cambia el salto de línea.
   - Ocurrió sobre código sin modificar.
   - Repetición del archivo completo en el mismo equipo: base 4/4 y después 4/4 en PASS (96/96 casos).
   - No se ha reproducido. Queda registrada como **riesgo de no determinismo del texto extraído del PDF**, que no se corrige aquí (no se tocan golden ni comparadores).
2. **`test_interaccion_fase_3c_a::test_a_acciones_geometria_click_teclado_y_senales`.** La señal `contraccion_cambiada` se emitió dos veces. Es la carrera de temporización ya conocida desde la Fase 1A, la que justificó el único reintento.

En la ejecución local posterior y en el CI del código no hubo ningún fallo en la primera ejecución.

## 4. Golden Masters y AS-001

- `git diff 83549e7 HEAD -- tests/fixtures` está vacío: fixtures, valores esperados y tolerancias sin cambios.
- Los 29 golden pasan en el CI y en la ejecución local final.
- AS-001: los 16 casos `test_as001_*` pasan.

## 5. Enlaces

- Rama: https://github.com/estebanojeda0615/SAVIP/tree/maintenance/v1.1.2-fase2d-lote4
- Comparación con 2C: https://github.com/estebanojeda0615/SAVIP/compare/maintenance/v1.1.2-fase2c-registro-historico...maintenance/v1.1.2-fase2d-lote4
- CI del código: [40953589320](https://github.com/estebanojeda0615/SAVIP/actions/runs/40953589320)
- El CI del HEAD documental final se informa en el mensaje de entrega.
