# 00 · Causa y alcance de AS-001

## 1. Base verificada

| Referencia | SHA | Estado |
|---|---|---|
| `maintenance/v1.1.2-fase1a-as006-as007` (base) | `428fdc0` | Remoto = local. CI [40403298861](https://github.com/estebanojeda0615/SAVIP/actions/runs/40403298861): success |
| `maintenance/v1.1.2-fase0-reproducibilidad` | `4c46a03` | Sin cambios |
| `main` / `develop/v1.1.2` | `dfdb3e0` / `6672529` | Sin cambios |
| Tag `v1.1.2-rc.1` | `08f364b` → `6672529` | Sin cambios |

- Rama nueva: `maintenance/v1.1.2-fase1b-as001`, creada desde `428fdc0`.
- Clon nuevo: `Desktop\SAVIP_V112_FASE1B_AS001`. No se usaron la carpeta de desarrollo ni los clones de las fases 0 y 1A.

## 2. Origen exacto de la excepción

- **Archivo:** `app_icociv/proyeccion/servicio_proyeccion.py`.
- **Función:** `_seleccionar_modelo_rectangular`, el selector vigente de la ruta productiva. La ruta es `ejecutar_proyeccion` → `_ejecutar_proyeccion_base` → `_matriz_rectangular_12_24` → `_seleccionar_modelo_rectangular`.
- **Línea (en `428fdc0`):** `rmse = math.sqrt(float(sse) / len(valores))`.

`sse` es la `Fraction` exacta de `_sse_exacto`. `float(Fraction)` ejecuta `int(numerador) / int(denominador)` (`numbers.py`, línea 316). La división entera verdadera de Python lanza `OverflowError` si el cociente no cabe en float; **no devuelve `inf`**. La excepción sale del selector y aborta la proyección completa.

## 3. Reproducción antes del cambio (`428fdc0`)

**Prueba del selector.** Se ejecutó sin modificar nada: 19 pasan y 1 `xfail`. El `xfail` es `test_as001_candidato_divergente_no_aborta_la_seleccion`, con la excepción prevista, `raises=OverflowError` estricto.

**Reproducción mínima.** Dos candidatos sobre los mismos 2 pares: `divergente = [1.2258e240, 1.2258e240]` y `sano = [1.0, 2.0]`. Sus datos son sintéticos y en memoria; no se toca ningún fixture aprobado.

```
SSE exacto (Fraction) bits del numerador: 1597 | cabe en float: False
EXCEPCION: OverflowError integer division result too large for a float
en ...\Lib\numbers.py linea 316 : return int(self.numerator) / int(self.denominator)
division 1.2258e+240 / 1e-300 = inf
division 1e+308 / 1e-10 = inf
```

Las dos últimas líneas muestran el contraste con la división de dos float, que desborda a `inf` sin excepción. Importa para los campos de diferencias (01 §4).

**Prueba del cambio (§4.E).** Las 16 pruebas `test_as001_*` nuevas se ejecutaron contra una copia limpia del árbol con `servicio_proyeccion.py` de `428fdc0`:
- las **8** de escala extrema fallan y las 8 lo hacen con `OverflowError` en `numbers.py:316`;
- las **8** del rango ordinario pasan, como se espera, porque comprueban que el RMSE no cambia bit a bit.

Con la corrección pasan las 16 (02 §1). Evidencia: [`evidencia/as001_codigo_anterior.txt`](evidencia/as001_codigo_anterior.txt).

## 4. Por qué el SSE exacto no se modifica

- El selector minimiza `RMSE_m = sqrt(SSE_m / n)` sobre la misma muestra común y el mismo `n`. La raíz es creciente, así que `argmin RMSE = argmin SSE`.
- `_sse_exacto` (P0-D) suma en enteros de precisión arbitraria. El resultado es exacto, independiente del orden, sin desbordamiento y capaz de distinguir 1 ULP, cosa que la suma flotante no logra.
- El defecto **no** está en el orden. Está solo en la conversión del valor **informado** a float.
- Por eso `_sse_exacto`, el `sort` por `item[1]` (la `Fraction`), el desempate por orden del banco, la muestra común, los pesos y los 21 candidatos quedan intactos.

## 5. Consumidores de `rmse_segundo_oos`, `diferencia_absoluta` y `diferencia_porcentual` (§2.5)

**Dónde se publican.** `_ejecutar_proyeccion_base` copia los tres campos al resultado:
- `rmse_segundo_oos`;
- `diferencia_absoluta_segundo`;
- `diferencia_porcentual_segundo`.

**Cómo los trata cada consumidor.**

| Consumidor | Campo | Tratamiento de valores no finitos |
|---|---|---|
| `interfaz/presentacion_resultados.py` (281, 703) | `diferencia_porcentual_segundo` | `formatear_porcentaje` → `_numero` devuelve `None` si no es finito → «No disponible» |
| `reportes/contenido.py` (255, 1150) | `diferencia_porcentual_segundo` | `es_numero` (exige finitud) → se omite el párrafo o se escribe «No aplica» |
| `reportes/generador_reportes.py` (1051–1091) | `rmse_segundo_oos`, `diferencia_porcentual_segundo` | `_formatear_numero` → «No aplica» si no es finito |
| `persistencia/gestor_sesiones.py` | todo el resultado | `_convertir_json_seguro` convierte un float no finito en `None` antes de `json.dump(..., allow_nan=False)` |
| `exportables/*` | — | No leen estos campos. Los `diferencia_porcentual` de `excel_modulos` y `actualizacion_icociv` son otros: los del cálculo económico |

**Conclusión.** Ningún consumidor supone que los tres campos son finitos. `nan` ya era posible antes, con un RMSE ganador igual a 0. No hace falta cambiar ningún contrato ni tocar otro archivo de producción.

## 6. Alcance

**Corregido:** solo AS-001, en `servicio_proyeccion.py`, el único archivo de producción tocado.

**Sin tocar:**
- los modelos, el entrenamiento y las ventanas;
- la matriz 12/24, H24 y `_sse_exacto`;
- el orden y el desempate;
- el selector retirado `seleccionar_modelo_por_rmse_oos_global` y `_rmse_global_estable`;
- los Golden Masters y sus tolerancias;
- la interfaz, las sesiones, los exportables y la economía;
- `VERSION`, `packaging` y el EXE.
