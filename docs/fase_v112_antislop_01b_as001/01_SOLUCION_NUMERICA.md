# 01 · Solución numérica

## 1. Algoritmo elegido

Nueva función privada `_rmse_desde_sse(sse, n)` en `servicio_proyeccion.py`, junto a `_sse_exacto`. El selector la llama en lugar de la expresión directa:

```python
def _rmse_desde_sse(sse: Fraction, n: int) -> float:
    try:
        return math.sqrt(float(sse) / n)
    except OverflowError:
        with localcontext() as ctx:
            ctx.prec = 60
            return float((Decimal(sse.numerator) / Decimal(sse.denominator) / n).sqrt())
```

- **Rango ordinario.** La rama `try` es literalmente la expresión anterior. Mientras `float(sse)` no desborda, el RMSE informado es el mismo float, bit a bit.
- **Desbordamiento.** Solo se entra en el `except` cuando `float(sse)` lanza `OverflowError`, que es justo el caso AS-001. Allí:
  1. `Decimal(int)` construye el numerador y el denominador **exactos**, porque la construcción no redondea;
  2. la división, `/ n` y `sqrt()` se hacen a 60 dígitos significativos (`sqrt` de Decimal redondea correctamente);
  3. `float()` redondea **una sola vez** al double más cercano.
- **Contexto aislado.** `localcontext` no altera el contexto Decimal global del proceso.

**Por qué el resultado siempre es finito.** Con errores finitos, `RMSE = sqrt(Σe²/n) ≤ max|e| ≤ DBL_MAX ≈ 1,7977e308`. El RMSE siempre cabe en float aunque el SSE no quepa, y `float(Decimal)` no puede pasar de `max|e|`. El caso límite, todos los errores iguales a `DBL_MAX`, está cubierto por la prueba `test_as001_una_ulp_en_el_borde_de_dbl_max`.

**Qué no cambia.**
- El selector sigue ordenando por la `Fraction` `sse` (`resultados.sort(key=lambda item: item[1])`), nunca por el RMSE ni por `float(sse)`.
- Siguen igual el desempate, la muestra común, los pesos y la exclusión de no finitos.
- `_rmse_desde_sse` solo produce el número que se informa.

## 2. Precisión medida

Script [`evidencia/estudio_precision.py`](evidencia/estudio_precision.py), semilla fija 20261026. Resultado completo en [`estudio_precision.txt`](evidencia/estudio_precision.txt).

| Medida | Corrección elegida (Decimal 60) | Alternativa: escalado por max\|e\| |
|---|---|---|
| Casos extremos (n ∈ {2, 24, 48, 240, 480}, \|e\| hasta ~1,8e308, todos con `float(sse)` desbordado) | 20 000 | 20 000 |
| Peor error frente a la referencia Decimal de 100 dígitos | **0 ULP** | 2 ULP |
| Casos distintos del redondeo correcto | **0** | 6 674 (33 %) |
| Rango ordinario (20 000 casos, \|e\| entre 1e-6 y 1e6): distinto de `math.sqrt(float(sse)/n)` | **0** | 6 625 (33 %) |
| Coste del camino de desbordamiento | ~23 µs por candidato afectado | — |

El coste solo aparece cuando un candidato desborda, como mucho una vez por candidato y por proyección. El rango ordinario no paga nada nuevo: es el mismo `try`.

## 3. Alternativas rechazadas

| Alternativa | Motivo |
|---|---|
| `except OverflowError: return inf` | Lo prohíbe el prompt. Además el RMSE real sí cabe en float: informar `inf` sería falso |
| Escalar los errores por `max\|e\|` en flotante: `s·sqrt(Σ(e/s)²/n)` | Hasta 2 ULP de error y, aplicado siempre, cambia el número informado en el 33 % de los casos ordinarios. Aplicado solo al desbordar, exige pasar los errores además del SSE y sigue siendo menos preciso que la fracción exacta, que ya existe |
| `math.isqrt` con escalado entero | Igual de exacto, pero exige elegir a mano la escala y redondear. Decimal hace lo mismo en una línea |
| Calcular siempre con Decimal | Cambiaría la ruta ordinaria (riesgo de 1 ULP por doble redondeo frente a la expresión histórica) y su coste. No hace falta |
| `_rmse_global_estable` (hypot) | Pertenece al selector retirado. Además no redondea igual que `sqrt(SSE/n)` (P0-D): cambiaría el RMSE informado en el rango ordinario |
| Recortar, penalizar o descartar candidatos enormes | Lo prohíbe el prompt y cambiaría la selección |

## 4. Campos de diferencias

| Campo | Cómo se calcula (sin cambios) | Con la corrección |
|---|---|---|
| `rmse_seleccion_oos` / `rmse_segundo_oos` | `_rmse_desde_sse` | Finitos siempre que los errores sean finitos |
| `diferencia_absoluta` | `rmse_segundo − rmse_ganador` | Finita: resta de dos valores en [0, DBL_MAX]. Es ≥ 0, porque la raíz es monótona y ambos caminos redondean al más cercano |
| `diferencia_porcentual` | `dif / rmse_ganador · 100` si `rmse_ganador > 0`, `nan` si no | Puede desbordar a `+inf` **sin excepción** (división de float) cuando el ganador es diminuto y el segundo enorme, p. ej. 1e-100 frente a 1e300 |

**Decisión.** La `diferencia_porcentual` no cambia: ni su fórmula ni su contrato.
- `inf` no es un valor inventado. Es el resultado IEEE de una razón que no cabe en float, y ya podía ocurrir antes de esta fase, con divisiones ordinarias.
- Todos los consumidores lo muestran como «No disponible» o «No aplica», o lo guardan como `null` (00 §5).
- Lo fija la prueba `test_as001_diferencia_porcentual_no_representable_es_inf_y_los_consumidores_la_omiten`.

## 5. Límites conocidos (no corregidos, fuera de AS-001)

- **Subdesbordamiento.** Con errores diminutos (|e| ≲ 1e-162), `float(sse)` redondea a 0 **sin excepción**. El RMSE informado es entonces 0,0 aunque el real sea representable, y `diferencia_porcentual` es `nan`. La **selección sigue siendo correcta**, porque ordena por la fracción exacta. Es el comportamiento de `428fdc0` y no aborta nada. Verificado: `[1e-200]·2` frente a `[2e-200]·2` da ganador `a` y RMSE 0,0 / 0,0. Los errores reales, en puntos de índice, están muchos órdenes por encima. Si se quisiera cubrir, bastaría usar la misma rama Decimal cuando `float(sse) == 0` y `sse != 0`. Queda como recomendación, no aplicada (04 §5).
- **Errores no finitos** (`nan`, `±inf`): siguen excluyendo al candidato, como antes. Lo comprueban las pruebas existentes y `test_as001_errores_no_finitos_siguen_excluidos_junto_a_enormes`.
- **Precisión de 60 dígitos.** Basta y sobra para el redondeo final a 53 bits (~16 dígitos). La medición dio 0 casos distintos del redondeo correcto, aunque el doble redondeo podría, en teoría, desviarse 1 ULP en un empate de redondeo extraordinariamente raro.
