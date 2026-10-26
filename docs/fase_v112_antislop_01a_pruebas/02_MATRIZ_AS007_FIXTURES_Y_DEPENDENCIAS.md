# 02 · AS-007: fixtures y dependencias de `docs/`

## 1. Hallazgo que corrige a la Fase 0

La Fase 0 clasificó 87 pruebas como **«c-DANE: necesitan la sesión con datos DANE reales, no publicable»**, a partir de `docs/fase_4d_slider/fixtures/TRES_ANALISIS_REALES.json`. **Esa clasificación era errónea.**

- **La sesión es sintética:**
  - sus series son «Grupos_Obra sintético 1/2», del anexo sintético `ANEXO_SINTETICO.xlsx`;
  - su `GENERACION.json` dice «Anexo completamente sintético, no datos oficiales DANE»;
  - «REALES» se refiere a que los 3 análisis se ejecutaron con el **motor real**.
- **Los demás fixtures de `docs/` son igual de sintéticos:** los `FIXTURE_DATOS.json` de 4A, 4A-C, 4B y 4C, y la sesión de auditoría de UI. Mismas series, motor real, usuario «QA4B» / «Prueba Fase 3».
- **Por qué no se publicaron:**
  - pesan entre 15 y 21 MB cada uno;
  - sus campos `archivo_excel` llevan la ruta absoluta del equipo de desarrollo, con el nombre de usuario.

Esa ruta es lo único personal: se buscaron usuario, `Users`, `Desktop` y correos en el JSON completo.

**Consecuencia:** **ninguna prueba del repositorio necesita datos DANE reales.** El perfil `dane` queda vacío.

## 2. Acciones realizadas

### 2.1 Fixtures sintéticos trasladados o regenerados

| Fixture | Acción | Verificación |
|---|---|---|
| `docs/fase_4d_slider/fixtures/ANEXO_SINTETICO.xlsx` (2 grupos × tabla, 2024-01..2026-12) | **Regenerado** con `tests/fixtures/fase0/generadores.anexo_slider_4d` (mismo patrón que `_anexo` de `test_fase_4i_j_fecha_comun`) | Celda a celda contra el original: **3726 celdas, 0 distintas** |
| `TRES_ANALISIS_REALES.json` | **Trasladado** a `tests/fixtures/sesiones_sinteticas/TRES_ANALISIS_SINTETICOS.json.gz` (952 KB) | Solo cambian 3 `archivo_excel`: ruta absoluta → `docs\fase_4d_slider\fixtures\ANEXO_SINTETICO.xlsx`, relativa e inexistente en un clon. El resto es idéntico |
| `fase_4a_excel_formulas_simples/FIXTURE_DATOS.json` = `fase_4a_d/FIXTURE_DATOS.json` (mismo SHA) | Trasladado como `FASE_4A_FIXTURE_DATOS.json.gz` | 3 rutas saneadas |
| `fase_4a_c/FIXTURE_DATOS.json` | `FASE_4A_C_FIXTURE_DATOS.json.gz` | 3 rutas |
| `fase_4b/FIXTURE_DATOS.json` | `FASE_4B_FIXTURE_DATOS.json.gz` | 4 rutas |
| `fase_4c/FIXTURE_DATOS.json` | `FASE_4C_FIXTURE_DATOS.json.gz` | 4 rutas |
| `auditoria_better_ui_v11/temporal/sesion_auditoria.json` | `SESION_AUDITORIA_UI.json.gz` | 4 rutas |

- **Procedencia:** SHA-256 de origen y destino en `tests/fixtures/sesiones_sinteticas/README.md`. Total ~7 MB.
- **Fuente:** copia de solo lectura de `docs/` del repositorio 1.1 local. `SAVIP_V1_1_2_DESARROLLO` no se usó.
- **Por qué no se regeneraron con el motor actual:** son sesiones de versiones anteriores (factor legado sin `criterio_factor` y `resultado` del motor de entonces). Regenerarlas cambiaría la semántica que esas pruebas comprueban: condición de parada §5.
- **Cargador:** `tests/fixtures/sesiones.py`, con `cargar(nombre)` y `ruta_temporal(nombre)`.

### 2.2 Salidas que las pruebas escribían en `docs/` → temporal del sistema

Con el ayudante `tests/fixtures/salidas.carpeta_salida(nombre)`, todo va a `%TEMP%\savip_pruebas_salidas\…`:

- `test_fase_4i_n`, `test_fase_4i_p`, `test_fase_4i_j_fecha_comun`, `test_fase_4i_j_k_actividades` y `test_fase_4i_g_sesiones` (capturas);
- `test_proyecciones_fase_3` (capturas + `INTEGRACION_REAL.json`);
- `test_proyecciones_fase_3b` (capturas, `EJEMPLOS_NUMERICOS.json`, `INTEGRACION_REAL.json`);
- `test_interaccion_fase_3c_a` (capturas, `*_MEDIDAS.json`, ajustes Qt y matplotlib);
- `test_fase_4g_b_consulta_exportacion` y `test_fase_4g_historial_dane_fechas` (evidencia JSON);
- `test_fase_4a_c`: modo script, carpeta temporal.

**Evidencia:**
- **Línea base:** el perfil esencial escribió **18 archivos** en `docs/` de la copia (`fase_3`, `fase_4i_n`, `fase_4i_p`, `fase_4i_j_k`, `fase_3c_a`).
- **Tras los cambios:** **0**. La copia solo conserva `docs/fase_v112_antislop_00`.
- **Regresión corregida antes de cerrar:** en la primera corrida tras el cambio falló 1 prueba (`test_proyecciones_fase_3`), porque quedaba una segunda escritura a `docs/fase_3/capturas` (L218). Se corrigió en el commit siguiente.

**Lo que no se tocó:**
- las lecturas de evidencia histórica (`respaldo_inicio/*.bak`, `ANTES_*` de 3C-B), que se marcan `HISTORICO`;
- `test_fase_4i_c` L208: guarda una captura solo si `docs/fase_4i_c/capturas` existe; en un clon no escribe nada.

### 2.3 Expectativas obsoletas actualizadas (solo contra el contrato confirmado)

| Prueba | Antes | Ahora | Contrato confirmado en |
|---|---|---|---|
| `test_fase_4g_historial_dane_fechas::test_B…` | `factor == I/I0` en el escenario con I0 de octubre | `factor == F(4I-C)` = `factor_aplicado(I, I0)` | `comparacion_historica.escenario_registro`: «Fase 4I-C: el escenario usa el MISMO factor aplicado» → `aplicar_factor`; golden económico |
| `test_base_valor_presupuestal_fase_4e_a::test_05…` | Excel `=L3/K3`, `=(M3-1)*100` | `=1+ROUND((L3/K3-1)*100,2)/100`, `=ROUND((M3-1)*100,2)` | El registro lo crea el calculador vigente (`sintetico()` → `boton_calcular`), luego no es legado. `_generar_excel_alcance`: ROUND salvo `es_factor_legado` |
| `test_microcorreccion_fase_4d_c::test_excel_15…` | `=M/K` y `=(O-1)*100` en todas las filas | Por fila: I/I0 si el registro exportado es legado; ROUND si no | El Excel exporta `escenario_registro(r)[0]`, y con la referencia 2024-02 seleccionada cada escenario se recalcula con 4I-C |
| `test_fase_4g_historial_dane_fechas::test_C…` | `=I/I0` en todas las filas | Ídem, por fila con `es_factor_legado` | Ídem |

Cada cambio deja un comentario «Fase 1A (AS-007)» con el motivo en la propia prueba.

**Se conservan sin cambio, pendientes de decisión:**
- **reutilización de trayectoria** (`test_fase_4g_b` ×9, `test_proyecciones_fase_3b` ×1): esperan que el motor vuelva a correr. Reescribirlas cambia su escenario: o usar datos distintos o aceptar la reutilización;
- **metodología anterior a 12/24** (25 pruebas, 01 §2 de la Fase 0).

## 3. Matriz por prueba y dependencia (estado final en clon limpio)

| Dependencia | Clasificación | Archivos (pruebas afectadas) | Estado tras la Fase 1A |
|---|---|---|---|
| `TRES_ANALISIS_REALES.json` | **Fixture sintético reproducible/trasladable** (antes «DANE real») | 20 archivos del antiguo perfil `dane` (87 pruebas que fallaban; 111 con las que fallaban en cadena) | Trasladado; los archivos pasan (§4) |
| `ANEXO_SINTETICO.xlsx` | Fixture sintético reproducible | `test_switch_tema_sesion_dane`, slider, y por importación 01B, 4I-G, 4I-H y 4I-I | Regenerado |
| `FIXTURE_DATOS.json` (4A/4A-C/4B/4C) | Fixture sintético trasladable | `test_historial_empalme_fase_4b` (+ las 4I que lo importan), `componente_empalme_4b_a`, `empalme_fase_4c`, `excel_formulas_principales`, `fase_4a_d`, `fase_4i_c`, `fase_4i_i`, `importes_4e`, `referencia_economica_4d_b`, slider | Trasladados |
| `sesion_auditoria.json` | Fixture sintético trasladable | `test_fase_4a_c` (3), `test_visual_fase_3c_b` | Trasladado. `test_fase_4a_c::test_d` se **bloquea** en el diálogo de confirmación de exportación de 4I-J, que la prueba no contempla: pendiente de decisión, perfil histórico |
| Capturas / JSON de salida | **Salida temporal** | 11 archivos (§2.2) | → `tmp` |
| `respaldo_inicio/*.bak`, `.tar` | **Evidencia histórica no necesaria** (copias del código anterior a cada fase para comparar antes/después) | `test_empalme_fase_4a` (1), `test_variacion_indice_empalme` (2), `test_numericos_icociv` (1), `test_proyecciones_fase_3b` (1), slider (1), `test_fase_4i_e` (1), `test_visual_fase_3c_b` (1) | Sin cambio, perfil histórico. Propuesta: retirarlas en la limpieza, porque comparan contra código ya superado |
| `docs/fase_3c_b/ANTES_*`, `DESPUES_*`; `docs/fase_3b/EJEMPLOS_NUMERICOS.json`; `docs/fase_4g/MATRIZ_TRAZABILIDAD.json` | Evidencia histórica | `test_visual_fase_3c_b` (5), `test_proyecciones_fase_3b`, `test_fase_4g_historial…` | Sin cambio (3C-B, histórico). La lectura de `MATRIZ_TRAZABILIDAD` en 4G ya no falla en clon limpio |
| `docs.fase_4e_b_unificada` (paquete Python en `docs/`) | Código de soporte no publicado | `test_equivalencia_presupuestal_fase_4e_b` (error de recolección) | Pendiente |
| `tests.test_p0c_retiro_intervalos_no_sustentados` (módulo inexistente) | Dependencia perdida | `test_p0c_*` (2 errores de recolección) | Pendiente; el módulo no existe en ningún árbol |
| Expectativas obsoletas | Desactualizadas | §2.3 | 4 actualizadas; 10 de reutilización y 25 de metodología pendientes |
| `test_v112_01c` (fuentes Segoe) y 3 carreras de tiempo | Entorno o tiempo | Perfil gui | Sin cambio |

## 4. Resultado de la migración (caracterización por archivo, clon limpio sin `docs/`)

Ejecución por archivo, 3 en paralelo y 1200 s de límite, sobre los 54 archivos de los perfiles `dane`, `historicas` y `gui`:
- **Antes (Fase 0):** en los perfiles `dane` + `historicas` + `gui` (414 pruebas + 3 errores de recolección), 224 pasaban, 188 fallaban y había 3 errores.
- **Después:** **359 pasan**, 54 fallan y 3 errores de recolección. Además, `test_fase_4a_c` (3 pruebas) agota su límite (bloqueo en el diálogo). Son los mismos archivos salvo `test_fase_4i_h_encabezado` (4 pruebas), que ya había pasado al esencial.
- **Después de los últimos cambios:** de esos 54 fallos, 3 eran las expectativas del factor ya actualizadas (§2.3, comprobadas 3/3). El resto (§3) son pendientes documentados: reutilización, metodología 12/24, evidencia histórica, fuentes, módulo perdido y la carrera de `test_B`.

**Archivos completos que pasan al perfil esencial: 23.**
- 20 del antiguo perfil `dane`, menos el slider, que tiene 1 `.bak`, y `test_fase_4i_e`, que tiene 1 `.tar`;
- `test_historial_empalme_fase_4b`, `test_componente_empalme_fase_4b_a`, `test_empalme_fase_4c`, `test_excel_formulas_principales` y `test_fase_4a_d`;
- antes, en el commit de AS-007 parte 1: `test_fase_4i_h_encabezado`.

Lista exacta: `ESENCIALES` en `scripts/pruebas_fase0.py`.
