# 01 · Inventario de pruebas y dependencias

**Caracterización en un clon limpio sin `docs/`:**
- copia de los archivos rastreados de `6672529`;
- entorno `venv-test` = las 32 versiones de `requirements-lock.txt` + `requirements-test.txt`, instaladas con `--no-deps` (`pip check` sin problemas);
- Qt offscreen;
- cada archivo de prueba en su propio proceso, con 900 s de límite (ninguno se agotó).

**Detalle por prueba:** `01_INVENTARIO_PRUEBAS.csv`, separado por `;`, con columnas `archivo`, `prueba`, `estado_clon_limpio`, `categoria`, `perfil` y `motivo`.

## 1. Cifras

**Antes de la Fase 0:**
- 108 archivos `test_*.py`, de ellos 105 recolectables, más 2 que son scripts sin pruebas para pytest;
- **1000 pruebas**: **809 pasan**, **188 fallan** y **3 errores de recolección**.

**Después de la Fase 0:**
- +3 archivos de Golden Master (**29 pruebas**);
- **1029 pruebas** en 108 + 3 archivos.

| Categoría (prompt B1) | Pruebas | Estado en clon limpio | Comentario |
|---|---|---|---|
| **a** Productivas y autónomas | 769 + 29 nuevas | Pasan | 585 viven en archivos que pasan completos (perfil esencial). Otras 184 pasan dentro de archivos que también tienen fallos (perfiles histórico, DANE y GUI). |
| **b** Expectativas obsoletas | 36 | Fallan | Detalle en §2 |
| **c** Dependen de `docs/` o de fixtures no publicados (AS-007) | 61 + 3 errores de recolección | Fallan | Detalle en §3 |
| **c-DANE** Necesitan la sesión con datos DANE reales | 87 | Fallan | `docs/fase_4d_slider/fixtures/TRES_ANALISIS_REALES.json` (15 MB, no publicable) |
| **d** Dependientes del entorno gráfico | 4 | Fallan | `test_v112_01c_dialogos_legibles`, casos de 50 y 200 líneas: offscreen sin fuentes Segoe registradas mide mal el ancho. Pasan 8/8 si antes se importa un módulo que registra Segoe (`test_v112_01b_indicadores_sesiones`). |
| **e** Protegen el selector retirado (AS-006) | 40 | Pasan | `test_rmse_global_estable` (11), `test_seleccion_rmse_global` (16) y `test_p0d_rmse_orden_exacto` (13): ejercitan `seleccionar_modelo_por_rmse_oos_global` y `_rmse_global_estable`, que el flujo productivo ya no usa para elegir el modelo. |
| **f** Carencias esenciales | — | — | Se cubrieron con los Golden Masters (§5); lo que sigue sin cubrir está en §6 |

## 2. Expectativas obsoletas (b), documentadas sin corregir

| Grupo | Pruebas | Evidencia |
|---|---|---|
| Reejecución del motor sobre la misma serie y los mismos datos | `test_fase_4g_b_consulta_exportacion` (9), `test_proyecciones_fase_3b::test_tres_proyecciones…` (1) | Esperan `proyectar() == 1` análisis nuevo y obtienen 0, o el mensaje «Proyección reutilizada sin recalcular». Desde 4I-J la trayectoria guardada se reutiliza: es el comportamiento vigente y está protegido por `test_fase_4i_j_reutilizacion` y por el golden de sesión. |
| Factor sin redondeo | `test_fase_4g_historial_dane_fechas::test_B_…` (1) | Espera `1.0128 == 128.393…/126.766…`. La regla vigente (4I-C) es `1 + ROUND(p; 2)/100`. |
| Metodología anterior a 12/24 | 25 en `test_horizonte_evidencia_reducida` (3), `test_informes_serie_bloqueada` (2), `test_integracion_fhg` (2), `test_p0g_desacople_punto_intervalo` (6), `test_p0g_ui_csv_estado_metodologico` (2), `test_publicacion_horizonte` (3), `test_salvaguarda_benchmarks` (2), `test_dependencia_statsmodels` (1), `test_cierre_metodologico` (1), `test_informes_rediseno` (2), `test_ajuste_salto_anual` (1) | Proyectan series de menos de 36 meses (hoy rechazadas con la explicación 12/24). Buscan claves retiradas (`horizonte_maximo_evaluado`, `horizonte_maximo_recomendado`, `horizonte_maximo_publicable_continuo`), textos de fuente anteriores u horizontes mayores que 24. **Certeza media:** la causa es coherente con la metodología vigente, pero no se reconstruyó cada expectativa. |

## 3. Dependencias no publicadas (c y c-DANE)

| Archivo que falta | Pruebas | Naturaleza |
|---|---|---|
| `docs/fase_4d_slider/fixtures/TRES_ANALISIS_REALES.json` | 87 | Sesión real con datos DANE (no publicable) → perfil **dane** |
| `docs/fase_4d_slider/fixtures/ANEXO_SINTETICO.xlsx` | 18 | Anexo sintético de desarrollo. Podría regenerarse en `tests/fixtures/`, pero los mismos archivos también necesitan la sesión real. |
| `docs/fase_4a_excel_formulas_simples/FIXTURE_DATOS.json` | 17 | Volcado de sesión de desarrollo (~20 MB) |
| `docs/fase_4a_d/FIXTURE_DATOS.json`, `docs/fase_4a_c/…`, `docs/fase_4b/…` | 9 | Volcados de sesión de desarrollo |
| `docs/*/respaldo_inicio/*.bak` y `.tar` | 8 | Copias del código anterior a cada fase, usadas para comparar antes/después |
| `docs/fase_3b/EJEMPLOS_NUMERICOS.json`, `docs/fase_3c_b/*`, `docs/fase_4g/MATRIZ_TRAZABILIDAD.json`, `docs/auditoria_better_ui_v11/temporal/…` | 8 | Evidencias de fases anteriores |
| Anexo creado por una prueba anterior del mismo archivo (`test_visual_fase_3c_b::test_c…`) | 1 | Esa prueba previa falla por `docs/` |
| Módulo `tests.test_p0c_retiro_intervalos_no_sustentados` | 2 errores de recolección | **No existe** ni en el repositorio ni en el árbol de desarrollo |
| Paquete `docs.fase_4e_b_unificada` | 1 error de recolección | Código de soporte en `docs/` |

**Cambio de prueba de la Fase 0 (único).** `tests/test_historial_empalme_fase_4b.py` leía `FIXTURE_DATOS.json` **al importarse**. Su ausencia rompía la recolección de este archivo y la de las suites 4I que lo importan.
- Ahora carga el fixture solo si existe. Si falta, un centinela hace fallar únicamente los casos que lo usan, con un mensaje explícito.
- Con el fixture presente, el comportamiento es idéntico.
- Efecto: los errores de recolección sin `docs/` bajaron de 11 archivos (Fase A) a 3.

## 4. Perfiles (`scripts/pruebas_fase0.py`)

Recuento real de `python scripts/pruebas_fase0.py --listar` en un clon limpio:

| Perfil | Archivos | Pruebas | Estado en clon limpio | Dónde corre |
|---|---|---|---|---|
| **esenciales**: tests autocontenidos esenciales | 55 (3 golden + 52 existentes) | **614** | **Todas pasan** (ver 04) | GitHub Actions (`fase0-pruebas.yml`) y local |
| **dane**: integración externa con DANE | 20 | 133 | 22 pasan, 111 fallan sin la sesión real | Solo con `docs/` locales |
| **historicas**: pruebas históricas obsoletas | 32 | 271 (+3 errores de recolección) | 198 pasan; 73 fallan y 3 errores (b, c, e) | Local, informativo |
| **gui**: ejecución GUI física Windows | 1 + lista manual | 8 | 4 pasan, 4 dependen de las fuentes | Local; la parte física es manual |
| **Total** | 108 | 1026 recolectadas | | |

1026 = 1029 − 3, porque los archivos con errores de recolección no aportan pruebas.

**Contaminación entre módulos (heredada, documentada sin corregir).**
- `tests/test_proyecciones_redisenio_visual.py` llama a `establecer_sombras(False)` y `establecer_movimiento_reducido(True)` **al importarse**.
- Lo importan, directa o transitivamente, `test_numericos_icociv`, `test_horizonte_editable`, `test_proyecciones_fase_2b`, `test_proyecciones_fase_3` y otros 10 archivos.
- Si pytest recolecta cualquiera de ellos junto con `test_interfaz_componentes.py`, falla `test_sombras_se_pueden_desactivar_por_completo`. Así pasó en las dos primeras ejecuciones completas del perfil esencial (612 + 2 fallos y 613 + 1 fallo). La segunda falla de la primera ejecución era una comprobación de esta fase, ya corregida.
- Un plugin espía (`sombras_habilitadas()` tras cada prueba) lo localizó: las sombras ya estaban apagadas al terminar la primera prueba, es decir, desde la recolección.
- Es la «falla heredada que depende del entorno» del informe del release.
- Solución: `scripts/pruebas_fase0.py` ejecuta la víctima (`test_interfaz_componentes.py`) en un proceso propio (`AISLADOS`), sin modificar ninguna prueba existente.

**Lista manual del perfil gui:**
- equipo sin Python;
- escalas 125/150 %;
- segundo monitor;
- Snap con teclado y diálogo de cierre en un tercio de pantalla;
- revisión visual de temas, gráfica y diálogos largos con fuentes reales.

## 5. Carencias esenciales cubiertas en esta fase (f)

| Carencia | Cubierta por |
|---|---|
| Ninguna prueba fijaba el modelo, ranking ni trayectoria del motor sin datos DANE | `test_fase0_golden_motor` (5 escenarios × H11/H23 + rechazos) |
| Reglas económicas sin vectores de frontera ROUND_HALF_UP versionados | `test_fase0_golden_economico` |
| Guardar, Ctrl+S, cancelar, error atómico y reabrir sin motor, sin `docs/` | `test_fase0_golden_sesion_exportables` |
| Excel/PDF/DOCX/CSV sin salida de referencia publicada | Ídem (texto, fórmulas y CSV normalizados) |
| Sesión grande | Ídem: 300 actividades, apertura sin motor en menos de 120 s |

## 6. Lo que sigue sin cubrir

- La sesión real del DANE y las 111 pruebas del perfil **dane**. Para cubrirlas habría que construir fixtures sintéticos equivalentes, lo que exige reescribir esas pruebas (fuera del alcance de la Fase 0).
- Los 61 casos y 3 errores de recolección de la categoría c: necesitan mover o regenerar fixtures (AS-007).
- Reapuntar o retirar las 40 pruebas de AS-006 al selector vigente.
- Actualizar o retirar las 36 expectativas obsoletas.
- Los 2 scripts sin pruebas para pytest (`test_regresiones_auditoria_independiente_bghc.py` y `test_residuales_auditoria_independiente_r3.py`): son scripts con `__main__`; pytest recolecta 0 pruebas de ellos.
- `pruebas/` (9 scripts manuales en la raíz): no se ejecutan en ningún perfil.
