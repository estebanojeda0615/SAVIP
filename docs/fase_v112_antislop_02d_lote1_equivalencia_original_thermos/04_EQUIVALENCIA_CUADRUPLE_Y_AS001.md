# 04 · Equivalencia cuádruple y AS-001 (G5)

## 1. Oráculo: arnés, entorno y procedencia

**Arnés.** `C:\Pruebas SAVIP\L2\oraculo\oraculo.py` (SHA-256 `42941b9319e6…`), **idéntico byte a byte** al versionado en 2D-2. Se acompaña de la copia externa del arnés de fixtures, cuyo SHA está en `arnes_sha256.txt`, de `golden_exacto.py` (`db633a2e…`) y de `umbral_as001.py` (`812cf944…`). Copias en `evidencia/scripts/`.

**Entorno.** El mismo equipo, Python 3.12.10 y el mismo lock y orden de casos para todas las versiones (`correr.sh`). Cada fuente se extrae con `git archive` a `C:\Pruebas SAVIP\L2\fuentes\<sha7>`, junto con `.fuente_git.txt` (SHA del commit y del árbol `app_icociv`):

| Fuente | Commit | Árbol `app_icociv` |
|---|---|---|
| Original | `6672529` | `b484bd4f…` |
| Base | `8e5a62b` | `f4f0a0c7…` |
| Final | `406e1dd` | `4092c8df…` |

**Qué compara, sin tolerancia** (`float.hex` para los finitos y cadenas exactas para SSE, `NaN`, `inf` y `None`):
- **35 escenarios de motor y 22 series adicionales.** Para cada uno: la selección del modelo ganador y del segundo, los 21 candidatos con su orden, W*, los pares comunes, la SSE exacta por candidato, RMSErect, MAE(h), MASE, sesgo, la trayectoria H1-H24, `y_proj`, el horizonte solicitado y el permitido, la factibilidad y los mensajes. Las series adicionales incluyen las de dominio extremo de AS-001.
- **6 casos con fixtures de horizonte dinámico.**
- **Rechazos y errores de validación.**
- **Economía y empalme:** ICOCIV/ICCP, factor, valores unitarios y totales.
- **`gui_sesion_exportables`:** un recorrido real de la GUI, con:
  - sesión guardada y restaurada **sin recalcular** (invariantes, historial y contexto);
  - consultas, informe de proyección (**CSV reproducible completo**, incluidas las 17 columnas históricas, y DOCX y PDF), Excel de sesión (hojas, fórmulas y valores), DOCX y PDF de sesión, y factor heredado.

Son **66 casos** en total.

**Normalización documentada:** las rutas temporales, los relojes y el identificador aleatorio del análisis activo (`uuid4().hex`) se sustituyen por `<ID1>`. **No se normalizan** números, fórmulas, columnas, filas ni textos de resultados.

## 2. Resultados (todos **ejecutados** en esta fase, salvo D)

| Comparación | Capturas | Resultado | Criterio |
|---|---|---|---|
| Determinismo del final | `406e1dd` r1 frente a r2 | **66/66 idénticos**; hash de datos `766a34b8a8968b02c1db35fb2dcdb7a94ebbf61b9450f70e415985e69ca1bb3f` | — |
| **C. Base inmediata `8e5a62b` → final `406e1dd`** | `8e5a62b` r1 frente a `406e1dd` r1 | **66/66 idénticos, bit a bit; mismo hash de datos.** Los JSON solo difieren en el bloque `meta` (fuente y raíz), como confirmó Thermos | **Cumple** |
| **A. V1.1.2 ORIGINAL `6672529` → final** | `6672529` r4 (**ejecutada en esta fase**) frente a `406e1dd` r1 | **65/66 idénticos.** La única diferencia es `series_extra.extremo_finito_x1e150\|h11` (**AS-001**): 11 subclaves, todas de ese caso. La original lanza `OverflowError`; Anti-Slop entrega un resultado | **Cumple** |
| A, con otra captura de la original | `6672529` r2 (2D-2) frente a `406e1dd` r1 | 65/66, solo AS-001 | Confirma |
| A, con la captura r1 de la original | `6672529` r1 frente a `406e1dd` r1 | AS-001, más el salto de línea del texto del PDF de sesión (`texto[122]` / `[123]`) | §3 |
| **B. V1.1.2 ORIGINAL → base `8e5a62b`** | `6672529` r4 frente a `8e5a62b` r1 | **Solo AS-001** (las mismas 11 subclaves) | **Cumple**: ya era la única antes del retiro |
| **D. V1.1.1 `dfdb3e0` → V1.1.2 original** | `cmp_6672529_dfdb3e0.txt` (2D-2) | **Evidencia inmutable reutilizada, NO se repitió en esta fase.** Ninguna de las dos fuentes cambia. Resultado registrado en 2D-2: **motor 35/35, series adicionales 22/22, fixtures 6/6, rechazos y economía/empalme idénticos**. Las 9 diferencias de `gui_sesion_exportables` son todas la **etiqueta de versión** «1.1.2» frente a «1.1.1» en tablas y textos de DOCX y PDF | Reutilizada |
| AS-001 con la rama anterior | `8e5a62b` frente a `406e1dd`, caso x1e150 | **Idénticos**: AS-001 no cambia ni se amplía | **Cumple** |

**Detalle:** `evidencia/oraculo/cmp_*.txt` y `evidencia/oraculo/sha256_capturas.txt`. Las capturas JSON no se versionan por tamaño; sus SHA-256 están registrados.

## 3. El salto de línea del PDF no es una diferencia funcional

- **La propia original** produce las dos variantes en ejecuciones distintas: r1 = r3, mientras que r2 = r4 coincide con Anti-Slop.
- El texto concatenado y normalizado del PDF de sesión es **idéntico** en todas las capturas.
- Causa: el identificador aleatorio de 32 caracteres (`uuid4().hex`) tiene un **ancho renderizado** variable con fuente proporcional, y eso mueve el corte de línea.
- Es exactamente el metadato no determinista que admite §6 del prompt.
- No se normalizó ningún número ni contenido.

## 4. Comprobaciones complementarias

| Comprobación | Resultado |
|---|---|
| Golden Masters (perfil esencial) | **29/29 PASS** |
| Golden con **tolerancia cero** (`golden_exacto.py`) | **0 diferencias** en el final (`evidencia/oraculo/golden_exacto_406e1dd.txt`), igual que en la base |
| AS-001 (perfil esencial) | **16/16 PASS** |
| Umbral AS-001 (`umbral_as001.py`): magnitudes 1e0…1e300 | **Idéntico** línea a línea en base y final. La excepción sigue limitada al desbordamiento de `float(SSE)` (≥ ~1e150) |
| Huella semántica (20 escenarios) | **0 diferencias.** SHA-256 `d6be699b700b3fa3379c743cc9d0ccbf5c185cacfa228208dbb95c2735370191` idéntico (`evidencia/huella_final.txt`) |
| Sonda AS-004, con las 6 definiciones ausentes | 29 casos, **0 diferencias** (05) |

## 5. Límites honestos

- Se ejecutó la **fuente** `6672529`, no el EXE. La correspondencia del bytecode del EXE con esa fuente (87/87) es evidencia de 2D-2.
- 66 casos más la huella y la sonda **no** demuestran una igualdad universal. Sí demuestran que, en una muestra amplia que incluye extremos, errores, sesiones y exportables, el retiro **no cambia ni un bit**.
- Además, los AST demuestran que el código conservado es idéntico (01, 03).
- La comparación D es heredada.
