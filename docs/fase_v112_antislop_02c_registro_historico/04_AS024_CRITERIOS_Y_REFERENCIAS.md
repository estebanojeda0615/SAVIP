# 04 · AS-024: fichas de `criterios.py` y referencias a código heredado

**Estado.** Esta fase **no modifica** `app_icociv/estadistica/criterios.py`. Este documento deja el diagnóstico y el cambio exacto propuesto para la 2D.

## 1. Quién consume la matriz

| Consumidor | Uso | ¿Le afecta cambiar `ubicacion`? |
|---|---|---|
| `CRITERIOS_ESTADISTICOS` / `matriz_criterios()` (criterios.py L265 y L878) | Tupla de 35 fichas | — |
| `exportar_matriz_criterios_markdown`, `generar_markdown_criterios` (L901, L909) | Exportan la tabla a Markdown | **Sin llamadas** en producción, `pruebas/`, `scripts/` ni `packaging/` (búsqueda en todo el repositorio) |
| Interfaz, informes (PDF/DOCX/CSV), sesiones | — | No leen la matriz |
| Pruebas: `test_auditoria_formulas_estadisticas`, `test_diagnostico_residual_formal`, `test_errores_extremos_descriptivos`, `test_fundamentacion_metodologica`, `test_metricas_sin_bandas` | Leen fichas por `id` y comprueban `fuente`, `justificacion`, `tipo` o la presencia de ids | **No**: ninguna lee `ubicacion` (búsqueda de `.ubicacion` en `tests/`, `pruebas/` y `scripts/`: 0 resultados) |
| Constantes del módulo (`MIN_ITERACIONES_WF`, `MIN_ITERACIONES_WF_ESCENARIO`, etc.) | Las importan producción y pruebas | **No**: el cambio solo toca cadenas de las fichas |

Cambiar el campo `ubicacion` de una ficha no altera importaciones, cálculos, tablas exportadas por la aplicación ni ninguna decisión estadística.

## 2. Fichas cuya ubicación apunta a código heredado (6 de 35)

Clasificación pedida:
- **(i)** regla vigente;
- **(ii)** regla retirada conservada por auditoría;
- **(iii)** experimental;
- **(iv)** ambigua.

| Ficha (línea en `2f70391`) | `tipo` | Ubicación actual | Qué describe | Clase |
|---|---|---|---|---|
| C-SEL-001 (L565-L610) | bibliografico | `servicio_proyeccion.py::seleccionar_modelo_por_rmse_oos_global` | Mínimo RMSE OOS global sobre la muestra común de pares (objetivo, h) en h=1..h_max | **(iv)**. El principio (mínimo error cuadrático OOS, muestra común, sin pesos, desempate por banco) **sigue vigente** en `_seleccionar_modelo_rectangular`. El **conjunto evaluado** que describe la ficha (rejilla h=1..h_max por horizonte) no es el rectángulo W*×24. No se homologa |
| C-ALC-001 (L619-L635) | derivacion_matematica | `…::_evaluar_horizontes_proyeccion` | El bucle por horizontes no se detiene en uno no recomendable (`continue`) | **(ii)**: describe un evaluador que ya no está en la ruta |
| C-ALC-002 (L636-L655) | operativo_tecnico | `…::_mayor_horizonte_con` | Horizonte máximo publicado sin prefijo consecutivo | **(ii)**: la ruta vigente no publica un máximo dinámico (alcance fijo 24) |
| C-ALC-003 (L656-L668) | operativo_tecnico | `…::_seleccionar_horizonte_permitido` | Mayor horizonte permitido ≤ solicitado | **(ii)**: la ruta vigente entrega el mes solicitado de una trayectoria única |
| C-SAL-001 (L669-L685) | operativo_interno_sin_sustento | `…::_aplicar_salvaguarda_benchmarks` | Salvaguarda como diagnóstico, no sustitución | **(ii)**: la ruta vigente no llama a la salvaguarda (`intentada = False`) |
| C-BEN-002 (L803-L821) | bibliografico | `…::peor_que_benchmark_naive` | rRMSE frente a naive > 1 como lectura descriptiva | **(iv)**: la función no está en la ruta vigente. Queda pendiente comprobar si alguna lectura equivalente se publica hoy por otra vía. No se afirma |

### Otras fichas relacionadas, sin código heredado en su ubicación

- **C-HOR-003** (L710-L736, «Niveles de evidencia OOS por horizonte»). Expresa la evidencia como `n − N0 − h + 1` por horizonte (ventana expansiva). La ruta vigente usa el rectángulo único `W* = n − N0 − H + 1`. Declara 3 y 6 como cortes descriptivos. **(iv)**: no se homologa al diseño N0=12/H24. Se propone una nota de época en 2D (§3), sin cambiar `valor` ni `accion`.
- **C-WF-001 y C-WF-002** (primer origen y mínimo de iteraciones). Siguen el bloqueo P0-E («primer origen no determinado»). No citan código heredado y **no se tocan**. Su relación con N0 = 12 la documenta el bloqueo P0-E, no esta fase.
- **C-INT-001 a C-INT-005.** Ubicación en código **vigente** que calcula el intervalo. Por P0-C el intervalo no se publica. Es AS-014, fuera de alcance.

### Laguna: el selector vigente no tiene ficha propia

Ninguna de las 35 fichas tiene ubicación en `_seleccionar_modelo_rectangular` ni en `_matriz_rectangular_12_24`. La regla que decide hoy no está fichada. Para 2D se propone una ficha nueva (§3.2), que exige autorización: añade una fila a la matriz.

## 3. Cambio propuesto para la Fase 2D (NO aplicado)

### 3.1 Reubicación histórica de las 6 fichas

Se cambia **solo** el tercer argumento (`ubicacion`). Se conservan `id`, `criterio`, `tipo`, `valor`, `fuente`, `justificacion` y `accion`.

```diff
-        "app_icociv/proyeccion/servicio_proyeccion.py::seleccionar_modelo_por_rmse_oos_global",
+        "HISTORICO: app_icociv/proyeccion/servicio_proyeccion.py::seleccionar_modelo_por_rmse_oos_global"
+        " @2f70391e1b920764e79fa50ec2c2da6b6b572e53 L3158-L3236 (retirado en la Fase 2D; regla vigente:"
+        " _seleccionar_modelo_rectangular). Ver docs/fase_v112_antislop_02c_registro_historico/02, R3",
```

Las otras cinco siguen el mismo patrón:

| Ficha | Nueva `ubicacion` |
|---|---|
| C-ALC-001 | `HISTORICO: …::_evaluar_horizontes_proyeccion @2f70391e… L2549-L2753 (retirado en la Fase 2D). Ver 02, R4` |
| C-ALC-002 | `HISTORICO: …::_mayor_horizonte_con @2f70391e… L3752-L3777 (retirado en la Fase 2D). Ver 02, R5` |
| C-ALC-003 | `HISTORICO: …::_seleccionar_horizonte_permitido @2f70391e… L3390-L3398 (retirado en la Fase 2D). Ver 02, R5` |
| C-SAL-001 | `HISTORICO: …::_aplicar_salvaguarda_benchmarks @2f70391e… L3269-L3387 (retirado en la Fase 2D). Ver 02, R6` |
| C-BEN-002 | `HISTORICO: …::peor_que_benchmark_naive @2f70391e… L2467-L2499 (retirado en la Fase 2D). Ver 02, R4` |

**Orden.** Cada ficha se actualiza **en el mismo commit** que retire su símbolo, para que la ubicación nunca apunte a un código inexistente sin la marca `HISTORICO`.

**Herramienta de grafo.** `grafo_as003.py` sigue tratando estas cadenas como cita documental (contienen `::`), sin arista de llamada.

### 3.2 Ficha nueva para la regla vigente (requiere autorización expresa en 2D)

```text
CriterioEstadistico(
    "C-SEL-002",
    "Seleccion del modelo por RMSE rectangular (metodologia 12/24)",
    "app_icociv/proyeccion/servicio_proyeccion.py::_seleccionar_modelo_rectangular; ::_matriz_rectangular_12_24",
    TIPO_<a decidir: bibliografico o derivacion_matematica, como C-SEL-001>,
    "m* = argmin SSE exacto sobre la muestra comun W* x 24 (N0 = 12, H = 24); desempate por orden del banco",
    "<misma fuente que C-SEL-001>",
    "<texto a redactar por el responsable metodologico; no lo inventa esta fase>",
    "Mantener.",
)
```

`tipo`, `fuente` y `justificacion` quedan **pendientes de decisión**: elegirlos es una decisión metodológica, no de mantenimiento.

### 3.3 Nota de época en C-HOR-003 (opcional)

Añadir al final de `justificacion`: «Nota (Fase 2C): esta ficha describe ventanas por horizonte (n − N0 − h + 1). La metodología 12/24 vigente evalúa un rectángulo único W* = n − N0 − H + 1». No cambia `valor` ni `accion`.

## 4. Riesgos y comprobación en 2D

- **Pruebas que leen fichas.** Ninguna lee `ubicacion`. Tras el cambio deben seguir en PASS las de `test_fundamentacion_metodologica` que leen `fuente` y `justificacion` de C-SEL-001.
- **`validar_tipos_criterios`.** No cambia ningún `tipo`.
- **Exportación a Markdown.** `exportar_matriz_criterios_markdown`, que nadie llama, mostraría la nueva ubicación.
- **Aceptación en 2D:** `git diff` de `criterios.py` limitado al tercer argumento de las fichas afectadas (más la ficha nueva solo si se autoriza), los 797 + 7 ids esenciales en PASS y la huella exacta igual.
