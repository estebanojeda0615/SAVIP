# 04 · Informe de cierre de la Fase 1A (AS-006 + AS-007)

## Veredicto: **APTO CON RESERVAS**

**CI del commit final:** PENDIENTE_CI.

**Resumen:**
- **AS-006 resuelto** en lo que pedía esta fase: el selector vigente queda protegido por pruebas de contrato y de sensibilidad, y AS-001 queda reproducido como `xfail` estricto.
- **AS-007 resuelto en su mayor parte:**
  - ninguna prueba depende ya de datos DANE reales;
  - los fixtures sintéticos que vivían en `docs/` están en `tests/fixtures/`;
  - las pruebas ya no escriben en `docs/`.
- **Pendientes documentados:** expectativas de reutilización y de la metodología 12/24, evidencia histórica `.bak`, un módulo perdido y 4 pruebas de entorno o tiempo.
- **El perfil esencial pasa de 612 a 782 pruebas** y corre completo desde un clon limpio.

## 1. Cambios por archivo

**AS-006** (commit `aa4ceca`)

| Archivo | Cambio |
|---|---|
| `tests/test_fase1a_selector_rectangular.py` (nuevo) | 20 pruebas sobre `_seleccionar_modelo_rectangular`: 7 propiedades, 4 bordes, 5 mutantes detectados, referencia sin defectos, integración con la ruta productiva y AS-001 como `xfail(strict=True, raises=OverflowError)` |
| `scripts/pruebas_fase0.py` | La suite nueva entra en el perfil esencial |

**CI** (commit `ba6a3c9`)

| Archivo | Cambio |
|---|---|
| `.github/workflows/fase0-pruebas.yml` | Se dispara también en la rama de la Fase 1A; `timeout-minutes` de 90 a 150 |

**AS-007** (commits `5f40295`, `50df00e` y `cd59281`)

| Archivo | Cambio |
|---|---|
| `tests/fixtures/fase0/generadores.py` | `anexo_slider_4d`, que reproduce `ANEXO_SINTETICO.xlsx` celda a celda |
| `tests/fixtures/salidas.py` (nuevo) | Carpeta temporal para capturas y JSON de evidencia |
| `tests/fixtures/sesiones.py` (nuevo) y `tests/fixtures/sesiones_sinteticas/` (6 `.json.gz` + README) | Sesiones sintéticas trasladadas y saneadas |
| 23 archivos de prueba existentes | Lecturas desde `tests/fixtures`, escrituras al temporal y 4 expectativas del factor actualizadas a 4I-C (02 §2.3) |
| `scripts/pruebas_fase0.py` | 23 archivos al esencial y perfil `dane` vacío. Un proceso por archivo con 1200 s de límite (sustituye `AISLADOS`), JUnit por archivo y resumen. Dos carreras de tiempo del runner pasan al perfil gui (`e341515`) |

**Documentación** (commit de cierre)

| Archivo | Cambio |
|---|---|
| `docs/fase_v112_antislop_01a_pruebas/` 00–04 | Informes de la fase |
| `.gitignore` | Excepción para la carpeta de informes de la Fase 1A |

**Sin cambios:**
- `app_icociv/**`, `aplicacion.py`, `packaging/**`, `VERSION` y los `requirements*.txt` de la aplicación (diff vacío);
- `tests/fixtures/fase0/golden/*` y sus tolerancias;
- `main`, `develop/v1.1.2`, la rama de la Fase 0, el tag y el Release.

## 2. Qué quedó resuelto y qué no

| Hallazgo | Estado | Detalle |
|---|---|---|
| **AS-006** | **Resuelto en el alcance de la fase** | Las propiedades de las 37 pruebas del selector retirado están ahora sobre el vigente (01 §3). La ruta productiva usa solo el selector vigente, comprobado por espía. Las 75 pruebas que tocan código retirado se conservan; su retiro va con AS-003/AS-004, porque el código sigue existiendo y tiene consumidores en `pruebas/` |
| **AS-001** | **Reproducido, no corregido** | `xfail` estricto; pasará a PASS con la Fase 1B y obligará a retirar el marcador |
| **AS-007 (fixtures)** | **Resuelto** | 7 fixtures sintéticos regenerados o trasladados. No queda ninguna dependencia de datos DANE reales: la clasificación «DANE real» de la Fase 0 era errónea y se corrige aquí |
| **AS-007 (salidas a `docs/`)** | **Resuelto** | De 18 archivos escritos por la línea base a 0 |
| **AS-007 (expectativas)** | **Parcial** | 4 actualizadas con contrato confirmado. Pendientes de decisión: reutilización (10: 4G-B ×9, 3B ×1), metodología 12/24 (25), `test_fase_4a_c::test_d` (diálogo 4I-J) |
| **AS-007 (evidencia histórica `.bak`/`.tar`/`ANTES_*`)** | **Pendiente** (se propone retirar) | 8 pruebas que comparan contra copias del código anterior a cada fase, más 3C-B |
| **AS-007 (dependencias perdidas)** | **Pendiente** | `docs.fase_4e_b_unificada` (1) y `tests.test_p0c_retiro_intervalos_no_sustentados`, que no existe (2) |
| **Contaminación entre módulos** | **Mitigada** | Un proceso por archivo; la causa (estado global al importar) queda para la limpieza |

## 3. Propiedades vigentes mejor protegidas

- **Selector vigente:**
  - orden por SSE exacto, sensible a 1 ULP;
  - desempate por orden del banco;
  - pesos uniformes y muestra común;
  - invariancia al orden de entrada;
  - errores no finitos;
  - coherencia del RMSErect informado;
  - 21 candidatos, 24 horizontes y W*·24 pares en la ruta real.
- **Defecto AS-001:** queda detectado.
- **Flujos GUI con sesiones (4I-A/B/C/D/G/I/J y 01B):** 148 pruebas más en el perfil esencial cubren deshacer/rehacer, pegado, factor legado, guardar/abrir/cerrar, tema, borradores Empalme, fecha común, indicadores de sesión, Excel de 5 hojas y referencias económicas, todo desde un clon limpio.

## 4. Riesgos

- **Fixtures de versiones anteriores del motor:** las sesiones trasladadas tienen `resultado` de motores anteriores. Las pruebas que las usan comprueban apertura y edición sin recalcular, no cifras del motor actual (las fija el Golden Master).
- **Duración del CI:** el perfil esencial tarda ~1 h en el runner; el límite es de 150 min.
- **Variación entre CPU (Fase 0, 02 §5 bis):** Holt/Huber pueden variar entre runners. La serie 1 de la sesión golden tiene un ganador Holt lineal comparado a 1e-9; hasta ahora sin fallos.
- **Pruebas intermitentes:** el perfil esencial reintenta una vez cada prueba fallida y lista por nombre las que pasan al reintento. Así se evitan rojos falsos del runner, como `test_interaccion_fase_3c_a::test_a` en el run 40385457727, sin ocultar fallos deterministas. Riesgo: una regresión que falle solo a veces podría pasar al reintento; por eso la lista de intermitentes debe revisarse en cada run. En el perfil gui quedan 5 carreras de tiempo heredadas. Tres son de guardado tras una carga: `test_B` de 4G, la integración de 2B y la principal de 4I-J. Las otras dos: el layout de rediseño y `T01B_5`, que depende de la velocidad. Estabilizarlas esperando el fin de la carga requiere decidir la prueba, no el producto.

## 5. ¿Listos para AS-001 (Fase 1B)?

**Sí, con una condición: que el CI del commit final quede verde.**

Ya existen:
- la prueba de regresión `test_as001_candidato_divergente_no_aborta_la_seleccion`;
- las 7 propiedades del selector y los 5 mutantes, que detectarían un cambio de orden o del RMSErect;
- los 29 Golden Masters del motor, la economía, las sesiones y los exportables.

**Recomendación para la Fase 1B:**
1. Calcular el RMSE informativo sin `float(Fraction)` completo; por ejemplo, `OverflowError` → `inf`, o la raíz con aritmética de `Fraction`/`Decimal`. **Sin tocar el orden por SSE exacto.**
2. Retirar el marcador `xfail` en el mismo commit.
3. Ejecutar el perfil esencial y comprobar Golden Masters idénticos.

## 6. Enlaces

| Qué | Enlace |
|---|---|
| Rama | https://github.com/estebanojeda0615/SAVIP/tree/maintenance/v1.1.2-fase1a-as006-as007 |
| Comparación con la Fase 0 | https://github.com/estebanojeda0615/SAVIP/compare/maintenance/v1.1.2-fase0-reproducibilidad...maintenance/v1.1.2-fase1a-as006-as007 |
| Commits | `aa4ceca`, `ba6a3c9`, `5f40295`, `50df00e`, `cd59281`, `e341515`, `3e63cab` (docs), `a1ed3f3` (reintento) y el commit de documentación de cierre |
| CI | Runs en 03 §2.2; run del commit final: PENDIENTE_CI |
