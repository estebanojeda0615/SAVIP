# 08 · NO-GO previo: discrepancia anterior a 2D-2

## Dictamen: **NO-GO** (G0). El lote 2D-2 no se ejecutó.

**La base original sí quedó verificada.**
- La V1.1.2 empaquetada se identificó y autenticó: ZIP con su SHA-256, bytecode de los 87 módulos `app_icociv` idéntico a la fuente `6672529`, y librerías numéricas idénticas.
- La V1.1.1 (`dfdb3e0`) produce los mismos resultados que la V1.1.2 en todo lo comparado. Solo difiere la etiqueta de versión.

**Por qué es NO-GO.** El oráculo exacto encontró **una diferencia funcional preexistente** entre la V1.1.2 original y la rama Anti-Slop actual (`5478958`).
- **Dónde aparece:** solo con series de magnitud extrema, índices del orden de 1e150 o más.
- **Qué ocurre:**
  - la original lanza `OverflowError`;
  - Anti-Slop devuelve «no calculable» (de 1e150 a 1e153) o **genera una proyección** (desde 1e154).
- **Origen:** la corrección AS-001 de la Fase 1B (commit `8159d52`).
- **Por qué impide seguir:** tu condición fue que cualquier diferencia numérica o funcional detuviera el lote. El prompt (§2) añade que una diferencia, aunque sea previa a 2D-2, impide declarar la equivalencia hasta que tú decidas.

Por eso **no se tocó producción**. No se ejecutaron G1–G5, no se retiró ninguna función y no se pasó Thermos, porque no hay diff de código que revisar.

## 1. Versión original comparada

| Dato | Valor |
|---|---|
| Fuente | `66725293f304426ae6edf144b8f4dadbcbeefe10` (tag `v1.1.2-rc.1`, `develop/v1.1.2`) |
| ZIP | `cee5897f82753d5ca1b6650023da81384bc1bfb50b5a5468ddbb26e5e7a94600`. Verificado antes de extraer y no modificado |
| EXE | `fa5d6676…de6ca`. **No se ejecutó**: es una aplicación gráfica sin línea de comandos. Su contenido se demostró igual a la fuente 6672529 por bytecode (87/87 módulos y `aplicacion`) y por binarios nativos (228/228 `.pyd` y las DLL BLAS). Lo que se ejecutó fue esa fuente, con los mismos paquetes |
| V1.1.1 | `dfdb3e0` (`main`, VERSION 1.1.1), sin tag ni release. Se ejecutó su fuente |

## 2. Comparaciones (antes de cualquier cambio)

| Comparación | Escenarios | Resultado | Hashes y evidencia | Limitaciones |
|---|---|---|---|---|
| **B. V1.1.2 original ↔ Anti-Slop anterior `5478958`** | 66 filas: 35 de motor, 22 de series extra, 6 de fixtures, rechazos, economía y empalme, y el recorrido GUI con sesión y exportables | **65 iguales y 1 DIFERENTE** (`extremo_finito_x1e150\|h11`). Además, 0 diferencias exactas frente a los Golden Masters de 6672529 | `evidencia/cmp_6672529_5478958.txt`, `tabla_comparador_G0.csv`, `sha256_capturas.txt` y `golden_exacto_*.txt` | Fuente del paquete, no ejecución del EXE. Igualdad comprobada en N escenarios, no universal |
| **A. V1.1.2 original ↔ lote 2D-2 final** | — | **NO VERIFICADO**: el lote no se ejecutó | — | — |
| **C. Anti-Slop anterior ↔ lote 2D-2 final** | — | **NO VERIFICADO**: el lote no se ejecutó | — | — |
| **D. V1.1.1 ↔ V1.1.2 original** | Las mismas 66 filas | **Idénticas** en motor, series (también en el extremo, donde ambas lanzan `OverflowError`), fixtures, rechazos, economía y empalme. En la GUI solo cambia la etiqueta de versión, en 9 lugares | `evidencia/cmp_6672529_dfdb3e0.txt` | La 1.1.1 no tiene artefacto empaquetado que verificar |

**Determinismo:** 5478958 y dfdb3e0 dan capturas idénticas dos veces. En 6672529, una de las dos capturas parte de forma distinta una línea del PDF de sesión: el texto unido es idéntico y el corte depende de la anchura de un identificador aleatorio (01 §2).

## 3. Diagnóstico de la discrepancia

| Aspecto | Hecho |
|---|---|
| Cambio | `_seleccionar_modelo_rectangular`: de `math.sqrt(float(sse) / n)` a `_rmse_desde_sse(sse, n)`. Esa función devuelve exactamente la misma expresión y solo, cuando `float(sse)` desborda, calcula la raíz con `Decimal` |
| Origen | Fase 1B, AS-001, commit `8159d52` (26-10-2026), autorizada en su momento como corrección del aborto por desbordamiento |
| Rango ordinario | Bit a bit idéntico, por construcción del código (la rama `try`) y por medición (65 escenarios y el barrido de 10^0 a 10^148) |
| Dominio diferente | Cuando el SSE exacto supera el máximo de `float`. En el barrido, a partir de una serie de 10^150. La original aborta el análisis con un error en pantalla; Anti-Slop responde «no calculable» o, desde 10^154, entrega una proyección |
| ¿Lo produce 2D-2? | **No.** 2D-2 retiraría `seleccionar_modelo_por_rmse_oos_global` y `_errores_oos_por_par`, que no intervienen en ese cálculo. La discrepancia ya existe en `5478958` |
| ¿Se corrigió algo aquí? | **No.** No se modificó el motor ni se revirtió AS-001 |

## 4. Decisión que necesito

1. **Aceptar AS-001 como excepción preexistente documentada** y autorizar la continuación de 2D-2 (G1–G5).
   - La equivalencia con la V1.1.2 original se declararía «exacta en todos los escenarios comparados, salvo el dominio de desbordamiento de AS-001 (series de magnitud ≥ ~1e150), donde la original aborta».
   - Es mi recomendación: el dominio es inalcanzable con índices reales y AS-001 ya fue autorizada.
2. **Exigir equivalencia estricta también en ese dominio.**
   - Haría falta revertir AS-001 en producción. Es un cambio funcional fuera de Anti-Slop y de 2D-2, y necesitaría una autorización propia y su propio lote.
   - El efecto sería volver a lanzar `OverflowError` con series extremas.
   - No lo hago sin tu orden.
3. **Mantener el NO-GO** y no continuar con 2D-2.

## 5. Estado de Git

- **Rama:** `maintenance/v1.1.2-fase2d-lote2-equivalencia-original-thermos`, creada desde `54789587d0fa7714b4dc464ec48ca8f2ce254611`.
- **Commits:**
  - `be46ca9`: +1 línea del filtro del CI y +1 excepción en `.gitignore`;
  - el commit de esta carpeta de documentación.
- **Sin cambios** en `app_icociv/`, `tests/`, `scripts/` ni `pruebas/`.
- No se modificaron `main`, `develop/v1.1.2`, el tag ni la release `v1.1.2-rc.1`, el ZIP publicado ni las ramas anteriores.
- No hubo merge, PR, tag, release, EXE, ZIP ni cambio de versión.
- El ZIP y el EXE originales **no** se suben al repositorio. Solo constan sus SHA-256.

## 6. Pendientes, sin iniciar

- **Lotes:** 2D-2 (bloqueado por esta decisión), 2D-1, 2D-3 y 2D-6.
- **Otros pendientes:** AS-004; AS-007; AS-028 para 2D-1.
- **P0-C:** el residual del IC95 es preexistente y su corrección sigue cancelada.
