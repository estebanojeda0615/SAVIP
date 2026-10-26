# 03 · Golden Master económico, de sesiones y de exportables

**Ligado a:** commit `66725293f304426ae6edf144b8f4dadbcbeefe10` (ver `tests/fixtures/fase0/golden/metadatos.json`).

**Esperados congelados:**
- `golden/economico.json` (20 219 bytes);
- `golden/sesion_exportables.json` (366 387 bytes).

**Pruebas:**
- `tests/test_fase0_golden_economico.py` (6 pruebas);
- `tests/test_fase0_golden_sesion_exportables.py` (12 pruebas).

## 1. Reglas económicas (`economico.json`)

### 1.1 Porcentaje y factor ROUND_HALF_UP (`factor_aplicado`, `aplicar_factor`)

Doce pares (I, I0) en las fronteras del redondeo. `p` y `F` se comparan como texto `Decimal`, **sin tolerancia**.

| I | I0 | p (%) | F |
|---|---|---|---|
| 110 | 100 | 10.00 | 1.10 |
| 102,741 | 100 | 2.74 | 1.0274 |
| 102,745 | 100 | **2.75** (mitad hacia arriba) | 1.0275 |
| 102,744 | 100 | 2.74 | 1.0274 |
| 97,255 | 100 | **−2.75** | 0.9725 |
| 100 | 100 | 0.00 | 1.00 |
| 100,005 | 100 | 0.01 | 1.0001 |
| 99,995 | 100 | −0.01 | 0.9999 |
| 133,3333 | 123,4567 | 8.00 | 1.08 |
| 118,92 | 112,37 | 5.83 | 1.0583 |
| 150 | 149,99 | 0.01 | 1.0001 |
| 87,654321 | 91,2345 | −3.92 | 0.9608 |

Para cada par se fija también `aplicar_factor(1000, I, I0)`: porcentaje, factor, R, valor y `factor_indices` = I/I0 (sin redondear, solo trazabilidad).

### 1.2 Importes (`calcular_actualizacion_icociv`)

Siete casos. Cubren:
- **Base = P − A** con anticipo;
- **R = Base·(F − 1)** y **Valor = Base·F**;
- importes de 0,01 a 987 654 321,99;
- variación negativa;
- cantidad nula, fraccionaria y grande.

Se fija el registro completo, incluido el texto `trazabilidad_formula`. Se excluye `fecha_calculo`.

Ejemplos:
- P = 2 500,55 y A = 100,1 con I/I0 = 118,92/112,37 → p = 5,83 %, R = 139,946235, Valor = 2 540,396235.
- P = 1 234,5 con 97,255/100 → R = −33,94875, Valor = 1 200,55125.

### 1.3 Rechazos con mensaje literal

- P = 0;
- I0 = 0;
- A = P (base nula);
- A negativo;
- I no numérico;
- I infinito.

### 1.4 Factor legado

Se fijan:
- `es_factor_legado`: verdadero si el registro no tiene `criterio_factor`, falso con el criterio vigente;
- el código del criterio;
- los textos del criterio vigente y del legado.

### 1.5 Empalme ICCP → ICOCIV

Usa los datos ICCP internos del repositorio (`app_icociv/datos/iccp_historico.json`) y seis índices ICOCIV sintéticos.

| Caso | Resultado fijado |
|---|---|
| Empalme completo con Total ICCP (2019-03 → 2026-12) | Valor actualizado 19 672,224571 |
| Empalme completo con canasta «Materiales» (2020-07 → 2027-11) | 20 276,750138 |
| Solo ICCP con grupo «Pavimentaciones con asfalto» (2018-01 → 2021-06) | 12 454,173482 |
| Solo ICOCIV (2022-06 → 2027-11) | 16 689,364591 |
| Acero con Ix y q / sin Ix | 5 969,442730 (Z calculado / con observación) |
| Errores (mensaje literal) | Fechas invertidas; ICOCIV inexistente; serie ICCP que termina en 2020 («Costos indirectos»); sin serie ICCP |

Hallazgo de caracterización (documentado, no corregido): el empalme **solo ICOCIV** exige igualmente una serie ICCP válida. Sin ella responde «Seleccione un tipo de serie ICCP válido.».

## 2. Sesión y exportables (`sesion_exportables.json`)

Recorrido real en la ventana (`VentanaPrincipal`, Qt offscreen), con un **anexo 16 sintético** generado en una carpeta temporal:
- 2 grupos por tabla, de 2023-01 a 2026-12;
- grupo 1: tendencia + estacionalidad; grupo 2: exponencial suave.

### 2.1 Pasos y lo que se fija

1. **Proyectar las dos series:**
   - serie 1 a H11 → «Fourier K=1 + Holt lineal», I = 119,780385 (2027-11);
   - serie 2 a H23 → «Fourier K=1 + Exponencial/log-lineal», I = 132,311703 (2028-11).
   - El motor se ejecuta **2 veces** (espía `wraps=` sobre `ControladorPrincipal.ejecutar_analisis`).
2. **Tres actividades:**
   - «Actividad unitaria»: unitario, cantidad 2, P = 1 000, A = 100 → F = 1,0313, Valor = 928,17;
   - «Actividad total»: total, cantidad 3, P = 2 500,55, A = 0 → Valor = 2 578,817215;
   - «Actividad serie 2»: unitario, cantidad 1,5, P = 98 765,43, A = 1 234,5 → F = 1,0965, Valor = 106 942,664745.
3. **Consultar H11 → H23 → H11 en la serie 1:**
   - 0 análisis nuevos y el motor sigue en 2 ejecuciones;
   - H23 = 123,980385 (2028-11) y vuelta a H11 = 119,780385, cada uno idéntico al punto h de la trayectoria guardada;
   - las actividades no cambian.
4. **Deshacer/rehacer** un reordenamiento: deshacer restaura el orden, rehacer lo reaplica.
5. **Guardado:**
   - «Guardar como»: 1 diálogo, archivo escrito y ruta activa.
   - **Ctrl+S** real (`QTest.keyClick`): 0 diálogos, misma ruta, sin cambios pendientes.
   - «Guardar como» cancelado: devuelve falso, el archivo queda intacto byte a byte y la ruta no cambia.
   - **Error de escritura** (`os.replace` falla con `PermissionError`): devuelve falso, el archivo anterior queda intacto, aparece el aviso «siguen en memoria» y no quedan temporales (guardado atómico).
6. **Reabrir** la sesión en otra ventana con el motor **prohibido** y sin abrir el Excel de origen:
   - mismos valores, consultas de horizonte, contexto y análisis activo;
   - sin recalcular.
7. **Exportar desde la sesión reabierta** (alcance «Toda la sesión»):
   - **Excel:** exactamente 5 hojas, `Resumen`, `Valores proyectados`, `Proyecciones ICOCIV`, `Trazabilidad` y `Metodología y fórmulas`. Se fijan las celdas con sus **fórmulas** (`=1+ROUND((I/I0-1)*100,2)/100`, `=ROUND((F-1)*100,2)`, …).
   - **PDF** de la sesión: 29 páginas de texto extraído.
   - **DOCX** de la sesión: 317 párrafos y sus tablas.
8. **Factor legado:** variante sintética de la sesión, con la primera actividad con F = I/I0 sin `criterio_factor`, como un registro anterior a 4I-C.
   - Se marca como legado y se muestra el aviso «1 actividad usa el factor anterior…».
   - En Excel conserva `=L3/K3` y `=(N3-1)*100`; las demás filas usan `ROUND`.
   - Exportar no modifica nada y cancelar la actualización no cambia nada.
   - Actualizar sin motor da F = 1,0313, p = 3,13, Valor = 928,17. Deshacer restaura el legado.
9. **Informe de proyección** (`generador_reportes`, serie `tendencia_lineal_ruido`):
   - **CSV reproducible:** 96 filas, con los números comparados como flotantes;
   - **DOCX:** 42 párrafos + tablas;
   - **PDF:** 5 páginas.

### 2.2 Comprobaciones explícitas además del golden

- PDF de la sesión y DOCX del informe contienen **«1.1.2»**.
- Ninguna línea de los PDF/DOCX presenta el «±MAE» como «intervalo de confianza», salvo que diga expresamente que **no** lo es.
- **Sesión grande determinista:**
  - 300 actividades derivadas de la sesión del recorrido, con IDs deterministas;
  - abre completa sin motor, con 300 filas en la tabla;
  - la suma de valores es igual a 100× la de la base;
  - tarda menos de 120 s.

### 2.3 Normalización (lo único que no se compara literal)

| Qué | Cómo |
|---|---|
| Fechas y horas (ISO, dd/mm/aaaa, «25 de octubre de 2026», código `SAVIP-INF-aaaammdd-hhmmss`) | `<FECHA-HORA>` |
| IDs aleatorios: análisis uuid4 y cálculos de 8 hex | `<ID1>`, `<ID2>`, …, por orden de aparición en la sesión |
| Carpeta temporal del recorrido | `<TMP>` |
| Claves `fecha_calculo`, `fecha_guardado`, `creado`, `fecha`, `fecha_exportacion` y `actualizado` | `<VOLATIL>` |
| Espacios repetidos | Uno solo |
| Métricas impresas con 3+ decimales en PDF/DOCX | ≤ 1e-4 relativo o 1 unidad del último decimal. Las tablas de candidatos muestran métricas de modelos con optimizador iterativo, que difieren entre CPU (ver 02 §5 bis). Importes (2 decimales), porcentajes, páginas y recuentos se comparan exactos. |

De la sesión guardada se fijan:
- las claves de primer nivel;
- `proyecciones_icociv`: proyecto, valores completos, proyecciones, contexto, calculadora, comparación histórica, fecha común, excepciones;
- por análisis: nombre, contexto, parámetros, selección, consulta, IDs de registros y **trayectoria de 24 meses**.

El `resultado` serializado del motor (varios MB) **no** se versiona: se fija la lista de sus claves, porque el motor tiene su propio golden. Los campos `resultado_modelo`, `resultado_y_proj` y `resultado_rmse_seleccion` del resumen quedan en `null`, porque el resultado serializado usa otras claves. El modelo y el índice se fijan desde `contexto`.

## 3. Esquemas de sesión 1.1.0 / 1.1.1 / 1.1.2

- **Revisión de copias locales reales.** Las sesiones guardadas con los ejecutables 1.1.0 y 1.1.1 (copias locales con datos DANE reales, **no publicadas**) tienen **la misma estructura de claves** que la 1.1.2 hasta 4 niveles, salvo los IDs:
  - primer nivel: `archivo_excel`, `corte_dane`, `fecha_guardado`, `fuente`, `fuente_visible`, `parametros_proyeccion`, `proyecciones_icociv`, `resultado_proyeccion`, `ruta_jerarquica`, `seleccion`, `serie_historica` y `usuario`;
  - `comparacion_historica.version = 2` con `selecciones`.
- **Fixtures sintéticos.** Por eso el fixture 1.1.2 cubre la forma de los tres esquemas. La variante histórica que sí cambia el comportamiento (registros con **factor legado** anteriores a la regla 4I-C) se genera de forma determinista en `captura_gui.sesion_legado`.
- **Fuera de la Fase 0 (limitación).** La «sesión antigua sin trayectoria» (anterior a 4I-J) y las referencias externas DANE (`comparacion_historica.version = 3`, 4G) **no** tienen fixture sintético propio. Las cubren pruebas del perfil DANE que necesitan la sesión real.

## 4. Qué NO cubre

- **Slider I0 / comparación histórica con anexo posterior** (versión 3 de `comparacion_historica`). Lo cubren `test_fase_4i_p2_comparacion_consulta` (perfil esencial) y pruebas del perfil DANE.
- **Exportables del módulo Empalme** (Excel/DOCX/PDF del empalme): sin golden.
- **Aspecto visual de PDF/DOCX/Excel:** fuentes, colores, gráficas, formato de celdas. Solo se compara texto y fórmulas.
- **Ctrl+Shift+S, «Guardar y cerrar» desde el diálogo de cierre y la X de Windows.** Los cubren `test_fase_4i_g_sesiones` y `test_v112_01b_indicadores_sesiones`, que necesitan docs/ no publicados (perfil DANE).
- **Valores calculados de las fórmulas Excel:** openpyxl lee fórmulas, no resultados. La equivalencia fórmula ↔ valor se probó en fases anteriores con Excel por COM, fuera de esta red.
