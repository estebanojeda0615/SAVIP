# 02 · Mapa de dependencias y contratos

## 1. Método

**G1, grafo de referencias.** Lo calcula [`evidencia/grafo_as003.py`](evidencia/grafo_as003.py), que parsea por AST todas las definiciones de nivel superior de `app_icociv/**` (826 en `c9166c6`). Para ser conservador, **sobrestima** el uso:
- Cuenta como referencia todo nombre resuelto por import (`from X import a as b`, `import X`, `alias.a`), en cualquier nivel, también dentro de funciones.
- Cuenta todo atributo `.a` y toda cadena literal **igual** al nombre de una definición. Así cubre `getattr`, `patch`, tablas de despacho y conexiones Qt por nombre, y enlaza con *todas* las definiciones homónimas.
- Cada clase es un nodo que contiene todos sus métodos, lo que cubre los callbacks Qt.

**Raíces del grafo.**
- **Producción:** el nivel de módulo de `aplicacion.py` y de cada módulo de `app_icociv`.
- **S:** `pruebas/*.py` y `scripts/*.py`.
- **T:** `tests/**`.

**Citas documentales.** Las cadenas `"ruta.py::nombre"` de las fichas de `criterios.py` **no** son llamadas. Se registran aparte como contrato D.

**Comprobaciones adicionales.**
- `grep` de cada nombre en todo el repositorio, incluidos `docs/`, `packaging/` y `.spec`.
- Búsqueda de acceso dinámico: `globals()`, `getattr(módulo…)`, `importlib`, `eval`, `exec`. Solo existe `importlib.import_module` en `config/dependencias.py`, que importa **módulos** de terceros, no funciones.
- Los `__init__.py` de `proyeccion` y `estadistica` reexportan únicamente `ejecutar_proyeccion` y funciones de `analisis_series`.

**G2, espía en tiempo de ejecución.** El plugin [`evidencia/espia_as003.py`](evidencia/espia_as003.py) envuelve las 42 candidatas y se ejecutó sobre el **perfil esencial completo** (797 pruebas, que terminaron 797 PASS). Resultado en [`evidencia/g2_espia_esenciales.txt`](evidencia/g2_espia_esenciales.txt):
- **ninguna prueba de flujo productivo ejecuta una candidata**: ni los 29 golden del motor, sesiones y exportables, ni la GUI ni la integración de 21 candidatos;
- solo las ejecutan las pruebas unitarias que las llaman por su nombre.

## 2. Ruta productiva (no se tocó)

```
aplicacion.py → VentanaPrincipal → ControladorPrincipal.ejecutar_analisis
    → servicio_proyeccion.ejecutar_proyeccion
        → _ejecutar_proyeccion_base
            → _matriz_rectangular_12_24 (N0 = 12, H = 24, W*×24)
            → _seleccionar_modelo_rectangular
                → _sse_exacto (orden exacto; desempate por orden del banco)
                → _rmse_desde_sse (RMSErect informado, AS-001)
            → trayectoria H1–H24, tabla por horizonte (MAE(h), RMSE, sesgo), banda ±MAE(h)
```

Antes y después de los retiros es idéntica: la huella semántica exacta coincide byte a byte (04 §1).

## 3. API secundaria `ejecutar_analisis` del servicio

| Pregunta | Respuesta |
|---|---|
| ¿Es una API documentada? | **Sí.** Su docstring la presenta como «FUNCIÓN CENTRAL (entry point)», con un ejemplo de uso |
| ¿Quién la importa? | Solo `pruebas/ejemplo_uso.py`, verificado con `grep` de imports y de accesos `sp.` y `servicio_proyeccion.` |
| ¿La usa la GUI? | **No.** La GUI usa `ControladorPrincipal.ejecutar_analisis`, un método homónimo con otra firma. El grafo conservador los funde, y por eso marca la del servicio como alcanzable |
| ¿Qué llama? | Solo la ruta vigente: `cargar_todas_tablas`, `resolver_fila_seleccionada`, `construir_serie`, `ejecutar_proyeccion` |
| ¿Cuánto código heredado obliga a conservar? | **Ninguno** |
| Decisión | **MANTENER** (contrato S, sin coste heredado) |

**Ejecución real, antes y después.** Se ejecutó `pruebas/ejemplo_uso.py` con un anexo sintético de 40 meses:
- `ejecutar_analisis` responde;
- el script se cae después en la línea 87, al formatear `proj['ci_lo']`, que vale `None` desde que P0-C retiró el intervalo;
- ese defecto es **previo** y propio de `pruebas/` (AS-028), y la salida es idéntica antes y después.

## 4. Subsistema heredado: por qué casi todo queda anclado

Calculado con [`evidencia/conjunto_retirable.py`](evidencia/conjunto_retirable.py). Una candidata es retirable solo si nadie fuera del conjunto retirable la referencia, es decir, si el conjunto está cerrado.

| Ancla | Qué obliga a conservar |
|---|---|
| **Pruebas esenciales** que llaman directamente funciones heredadas (9 archivos) | `test_presentacion_resultados`, `test_resultado_horizonte_solicitado` → `determinar_horizonte_maximo_estadistico` y sus 6 auxiliares |
| | `test_fundamentacion_metodologica`, `test_vocabulario_vc`, `test_remediacion_r2_h1_h2_h3_h7`, `test_presentacion_resultados` → `_clasificar_evidencia_horizonte` (305 líneas), `_estado_por_horizonte`, `_tipo_uso_horizonte`, `_mensaje_horizonte_no_permitido` |
| | `test_remediacion_r2_h1_h2_h3_h7` → `_aplicar_salvaguarda_benchmarks` (y `_puntaje_rmse_ponderado`, `_backtesting_por_modelo_horizonte`) |
| | `test_nmin_adversarial`, `test_origen_inicial_backtesting` → `seleccionar_modelo_por_rmse_oos_global`, `_errores_oos_por_par` |
| | `test_fundamentacion_metodologica::test_el_selector_retirado_conserva_su_definicion_para_auditoria` → exige **expresamente** que exista `seleccionar_modelo_por_evidencia` (y 9 auxiliares de `modelos_interpretables`) |
| | `test_fase1a_selector_rectangular` (espía de la Fase 1A) → `_evaluar_horizontes_proyeccion`, `_rmse_global_estable`, `_modelo_consistente_desde_comparativo`, `_modelo_trayectoria_consistente` |
| | `test_cierre_semantico_ps01_ps05::test_ps03` → `tramo_evidencia_oos` |
| **Scripts S** de `pruebas/` | `prueba_horizonte_dinamico_ui_reportes.py` → `seleccionar_modelo_por_rmse_oos_global`, `determinar_horizonte_maximo_estadistico` |
| | `prueba_estadistica.py` → `validar_serie` (→ `detectar_outliers_extremos`) |
| **Fichas D** de `criterios.py` (matriz de auditoría metodológica) | `C-SEL-001` → `seleccionar_modelo_por_rmse_oos_global` |
| | `C-ALC-001` → `_evaluar_horizontes_proyeccion` |
| | otras fichas → `_mayor_horizonte_con`, `_seleccionar_horizonte_permitido`, `_aplicar_salvaguarda_benchmarks`, `peor_que_benchmark_naive` |

**Cuánto se libera según la decisión.**

| Escenario | Retirable (cerrado) |
|---|---|
| Sin tocar pruebas esenciales, scripts ni fichas | **6 definiciones, 183 líneas** (Lote 1, ejecutado) |
| Más adaptar la prueba esencial de la Fase 1A (opción B, pendiente de decisión) | 9 definiciones, 287 líneas |
| Ignorando las 9 pruebas esenciales (no permitido: perdería casos esenciales) | 20 definiciones, 630 líneas |
| Todo el subsistema | Exige además decidir sobre `pruebas/` (AS-028) y las fichas de `criterios.py` (AS-024) |

**La misma conclusión en la auditoría.** Su recomendación literal es «Decidir si el "registro de auditoría" debe vivir en código ejecutable», y el plan (04, fase 2, paso 5) dice «previa decisión sobre el "registro de auditoría"». Las pruebas esenciales que ejercen el subsistema son ese registro. Retirarlo es una decisión metodológica que no corresponde tomar en esta fase.

## 5. Valor de auditoría histórica

- **Las funciones conservadas documentan reglas retiradas** (la salvaguarda de benchmarks, la escalera de horizontes, la selección por RMSE global con peso…). Las fichas de `criterios.py` y las pruebas esenciales las usan como **evidencia ejecutable** de que esas reglas ya no rigen.
- **Las 6 funciones retiradas no tenían ese papel:**
  - ninguna prueba, ficha ni documento las cita;
  - `_metricas_desde_predicciones` ni siquiera podía ejecutarse, porque usaba el nombre no definido `detectar_errores_extremos`;
  - su historia queda en Git: `c9166c6` y los commits `d7429df` y `c6ca863`.

## 6. Después de los retiros

Grafo recalculado sobre el Lote 1:
- no aparece **ninguna** definición nueva inalcanzable, y ninguna cambia de alcance (producción, scripts o pruebas);
- `pyflakes` del módulo muestra los mismos avisos previos, salvo el nombre indefinido `detectar_errores_extremos`, que desaparece con `_metricas_desde_predicciones`;
- los 6 imports que solo usaban las funciones retiradas (`hashlib`, `datetime`, `timezone`, `TOLERANCIA_DETERIORO_AJUSTE_CALENDARIO`, `evaluar_ajuste_en_backtesting`, `calcular_escala_naive_insample`) se retiraron. Nadie los leía como `sp.X`.

**Quedan sin tocar** los avisos que ya existían en `c9166c6`:
- 5 imports sin uso;
- 2 variables locales no usadas en la ruta vigente.

No los produjo esta fase, y tocar la ruta vigente está prohibido.

**Un efecto derivado, fuera de alcance.** `calendario_anual.evaluar_ajuste_en_backtesting` ya era inalcanzable desde producción en `c9166c6`. Ahora además no la llama ninguna función, y la sigue usando una prueba no esencial. Se registra como FUERA DE ALCANCE.
