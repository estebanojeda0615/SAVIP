# 02 · Cambios y pruebas

## 1. Archivos y líneas (`git diff --numstat dfcaaa9 cae9f04`)

| Archivo | + | − | Contenido |
|---|---|---|---|
| `app_icociv/proyeccion/servicio_proyeccion.py` | 13 | 29 | Retira `TRAMO_OOS_SIN_EVIDENCIA`, `TRAMO_OOS_MUY_LIMITADA` y `TRAMO_OOS_DISPONIBLE` (3 líneas). Retira `tramo_evidencia_oos` (11 líneas de definición) y sus separadores. El bloque de comentario HGRID (10 líneas `#:`) pasa al docstring de `_texto_evidencia_oos`, que deja de decir «Ver `TRAMO_OOS_SIN_EVIDENCIA`». **El cuerpo de `_texto_evidencia_oos` no cambia**: Thermos lo comprobó extrayéndolo con `ast` y comparando su SHA-256 con el de la base |
| `tests/test_cierre_semantico_ps01_ps05.py` | 2 | 20 | Retira solo `test_ps03_la_escasez_de_evidencia_no_equivale_a_su_inexistencia` y deja en su lugar una referencia de 2 líneas. `test_ps03_w_es_cero_exactamente_cuando_el_dato_no_existe` sigue intacto |
| `tests/test_fase2c_contratos_vigentes.py` | 14 | 11 | Mismo id. Añade W=10 a las tuplas y fija el corte con `assert MIN_ITERACIONES_WF_ESCENARIO == 3`. Los docstrings pasan a presente para lo ya sustituido y cada id va completo en su línea. Todas las aserciones de la base se conservan |
| `.github/workflows/fase0-pruebas.yml` | 1 | 0 | Añade la rama al filtro de `push` |
| `.gitignore` | 1 | 0 | Excepción para esta carpeta |

**Sin cambios:**
- `scripts/pruebas_fase0.py`, porque el perfil selecciona por archivo y no hay ningún manifiesto de ids;
- r3 (`tests/test_residuales_auditoria_independiente_r3.py`);
- `tests/fixtures/**`, `VERSION`, `requirements*`, `packaging/` y `aplicacion.py`;
- reportes, interfaz, estadística, validación, persistencia, servicios y exportables.

La comprobación `git diff --stat` sobre todas esas rutas sale vacía. `servicio_proyeccion.py` baja de 5 871 a 5 855 líneas.

## 2. Commits

| Commit | Contenido |
|---|---|
| `9ff51e3` | `ci(2d-5)`: filtro del workflow (+1) y `.gitignore` (+1). Va antes del código para que el CI corra sobre el propio commit de código |
| `a056d9f` | `refactor(AS-003 2D-5)`: **commit atómico** con el retiro de la función, las constantes y el id PS-03, el traslado de HGRID y W=10 |
| `1c8c952` | `test(2d-5)`: correcciones de la 1.ª pasada de Thermos (docstrings, ancla del corte y lápida) |
| `cae9f04` | `test(2d-5)`: correcciones de la 2.ª pasada de Thermos (ancla explícita e ids completos). **Último commit de código** |
| HEAD documental | Esta carpeta |

## 3. Cobertura sustituta del id retirado

| Aserción del id retirado (`tramo_evidencia_oos`) | Cobertura vigente |
|---|---|
| W=0 → sin evidencia | `test_texto_evidencia_oos_tres_tramos_sin_vocabulario_de_validacion`: `textos[0].startswith("Sin evidencia…")`, y también `None` y `"x"` |
| W=1 y W=2 → muy limitada | Mismo test: W ∈ {1, `MIN−1`} contienen «muy limitada» y `(n=W)` |
| W=3 y W=50 → disponible | Mismo test: W ∈ {`MIN`, 10, 50} dan el texto exacto «Evidencia fuera de muestra disponible (n=W).» |
| Corte literal en 3 | `assert MIN_ITERACIONES_WF_ESCENARIO == 3`, con mensaje. Una mutación a 2 o a 4 falla |
| W=3, 10 y 50 no se llaman «validado» ni «certificado» | Mismo test, sobre el **texto publicado**, con W = 0/1/2/3/10/50 |
| (Docstring: «W en {1,2} entrega con advertencia») | `test_escasez_de_ventanas_entrega_el_punto_con_advertencia_y_sin_intervalo[36\|37\|41]`: con W* = 1 y 2 se entrega el punto con advertencia y sin intervalo; con W* = 6 no hay advertencia. El umbral de la advertencia es `MIN_ITERACIONES_WF` (6), distinto del corte descriptivo 3 |

**G2, con el retiro simulado en memoria antes de tocar el código** ([`evidencia/g2_retiro_simulado.txt`](evidencia/g2_retiro_simulado.txt)):
- `_texto_evidencia_oos` da «sin evidencia» con −1, 0, `None` y `"x"`; «muy limitada (n=W)» con 1 y 2; «disponible (n=W)» con 3, 10 y 50.
- Las pruebas sustitutas y `test_ps03_w_es_cero…` pasan.
- Solo falla, con `ImportError`, el id autorizado.

## 4. r3 y errores históricos

- **r3 directo** (`python tests/test_residuales_auditoria_independiente_r3.py`): **21/27** en la base y en el final, con la misma salida línea a línea. Los seis fallos heredados son **C12, HG4, HG5, HG6, B y G**. No se resuelven ni se presentan como éxito. Los 27 controles quedan intactos y r3 no forma parte del diff.
- **Errores de recolección:** siguen siendo **3**, los mismos:
  - `test_equivalencia_presupuestal_fase_4e_b`;
  - `test_p0c_objeto_publico_sin_intervalo`;
  - `test_p0c_regresion_negativa_c2`.

  No hay un cuarto y no se declaran resueltos.

Evidencia: [`evidencia/r3_ejecucion_directa_base.txt`](evidencia/r3_ejecucion_directa_base.txt), [`evidencia/r3_ejecucion_directa_final.txt`](evidencia/r3_ejecucion_directa_final.txt) y [`evidencia/coleccion_diff.txt`](evidencia/coleccion_diff.txt).
