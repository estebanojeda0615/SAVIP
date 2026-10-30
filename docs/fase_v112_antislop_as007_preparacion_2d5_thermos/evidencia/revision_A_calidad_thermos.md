# Thermos A · thermos:thermo-nuclear-code-quality-reviewer · alcance 83549e7...6ac158d (lote 2D-4)

Invocación: skill `thermos:thermos` (Thermos 1.1.0). Lanza en segundo plano el agente `thermos:thermo-nuclear-code-quality-reviewer` con el diff `diff_A_codigo.patch`. Claude Code 2.1.238. Revisión de solo lectura. Lo que sigue es la salida del revisor, condensada sin alterar los hallazgos.

**Veredicto.** El lote es una simplificación real: −354 líneas, sin ramas ni conceptos nuevos, y la ruta productiva no cambia. **No hay hallazgos críticos ni altos.** Deja restos huérfanos porque el inventario 2C se hizo por `def`, no por constantes de módulo ni por claves de diccionario.

## Hallazgos

1. **MEDIO. `MIN_ITERACIONES_SELECCION` sin consumidor.**
   - Ubicación: `modelos_interpretables.py:43`, más el import de `MIN_ITERACIONES_WF` en la línea 13, que solo la alimenta.
   - Su único consumidor era la función retirada; en `6ac158d` `git grep` solo encuentra la definición.
   - Remedio: borrar la línea y el import.
   - Clasificación: nuevo defecto (resto huérfano).
2. **MEDIO. `MODELOS_SERIE_TEMPORAL` solo la sostienen las pruebas.**
   - Ubicación: `modelos_interpretables.py:36-41`.
   - El diff retiró su último uso productivo. Hoy solo la leen `tests/test_auditoria_formulas_estadisticas.py:195,203` y `pruebas/prueba_horizonte_dinamico_ui_reportes.py:729,740`.
   - Remedio: retirarla junto con las aserciones redundantes, en un lote con validación propia.
   - Clasificación: nuevo defecto.
3. **MEDIO. Claves `descartes_modelos` y `ranking_backtesting` sin productor.**
   - Lecturas en:
     - `servicio_proyeccion.py:1542, 1545, 1639, 2276, 3933-3939, 4024, 4124`;
     - `reportes/contenido.py:819`;
     - `generador_reportes.py:1012-1015`.
   - Solo las escribía la función retirada; quedan lecturas que siempre devuelven `[]`/`{}`.
   - Hipótesis: compatibilidad con sesiones antiguas.
   - Remedio: decidirlo en un lote posterior.
   - Clasificación: riesgo previo, que el diff vuelve demostrable.
4. **BAJO. Comentario que apunta a un símbolo inexistente.**
   - Ubicación: `servicio_proyeccion.py:2591-2599`.
   - Ya registrado en 05 de 2D-4 para 2D-3/2D-6.
   - Clasificación: nuevo resto.
5. **BAJO. Comentario lápida y guardias duplicadas.**
   - Comentario: `test_fundamentacion_metodologica.py:264-269`, de 6 líneas.
   - La guardia textual «sin llamada a seleccionar_modelo_por_evidencia(» está repetida en `:247`, `:252`, `test_integracion_fhg.py:263`, `test_nmin_adversarial.py:180` y `test_origen_inicial_backtesting.py:191`. Ahora pasa siempre y solo impide reintroducir el nombre.
   - Clasificación: el comentario es un defecto menor nuevo; las guardias, riesgo previo.
6. **BAJO. Lista `HEREDADAS` desactualizada.**
   - Ubicación: `tests/test_fase2c_contratos_vigentes.py:23-37`.
   - Aún incluye los 6 nombres retirados en 2D-4.
   - No afecta al funcionamiento, porque se usa como intersección de texto.
   - Clasificación: nuevo resto.
7. **BAJO. `.gitignore` y workflow crecen una línea por fase.**
   - Remedio: usar patrones. Es una decisión de política.
   - Clasificación: riesgo previo.
8. **Tamaño.**
   - `modelos_interpretables.py` pasa de 1 381 a 1 027 líneas: sigue por encima de 1 000.
   - Hipótesis: sacar el bloque Fourier K=1/Seasonal Naive a otro módulo.
   - Clasificación: riesgo previo, fuera de alcance.

## Falsos positivos descartados

- `UMBRAL_RRMSE_PEOR_BENCHMARK` y `TOLERANCIA_RRMSE_BENCHMARK`: siguen en uso en `criterios.py:795` y en `servicio_proyeccion.py:38-39`.
- `EPS_NUMERICO`, `math` y `Any`: siguen en uso.
- La cita a `2f70391` es correcta.
- Los auxiliares de nombre genérico no tenían consumidores externos.

## Recomendación de proceso

En la comprobación G1 de los próximos lotes, buscar también por nombre las constantes de módulo y las claves de diccionario que escribían las funciones retiradas.
