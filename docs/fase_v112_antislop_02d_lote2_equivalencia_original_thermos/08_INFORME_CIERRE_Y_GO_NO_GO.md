# 08 · Informe de cierre del lote 2D-2 y GO/NO-GO

## 1. Dictamen: **APTO CON RESERVAS no críticas**

**Qué se retiró.** De `servicio_proyeccion.py` salen `seleccionar_modelo_por_rmse_oos_global` y `_errores_oos_por_par`: 107 líneas de definición y 4 separadores. **Nada más cambia en producción**, salvo el localizador interno, no publicado, de la ficha C-SEL-001.

**Equivalencia con la V1.1.2 original empaquetada.** Es exacta en todos los escenarios comparados en los que la original completa el cálculo. La única diferencia es la **excepción AS-001**, preexistente y aceptada por el propietario el 05-11-2026; el lote no la amplía ni la cambia.

**Equivalencia con la rama Anti-Slop anterior:** total, 66 de 66 escenarios.

**Pruebas y Thermos**
- 809/809 esenciales, sin cambios de estado.
- Golden 29/29 y exacto con tolerancia cero.
- AS-001 16/16.
- Huella con SHA idéntico.
- Dos pasadas de Thermos, sin hallazgos críticos, altos ni medios abiertos.

**Reservas no críticas**
1. El EXE original no se ejecutó, porque es una aplicación gráfica. Se demostró que contiene exactamente la fuente `6672529` (bytecode 87/87 y binarios numéricos idénticos), y lo que se ejecutó fue esa fuente. Por tanto, en sentido estricto se trata de «equivalencia con la fuente demostrada de la V1.1.2 empaquetada».
2. Queda una deuda menor que introduce el lote, D-2D2-1 (§4), que no afecta a resultados ni a ids.
3. La igualdad se ha comprobado en 66 escenarios representativos. No es una demostración universal.

## 2. Versión original comparada

| Dato | Valor |
|---|---|
| V1.1.2 original | Fuente `66725293f304426ae6edf144b8f4dadbcbeefe10` (tag `v1.1.2-rc.1`, objeto `08f364b`). ZIP `cee5897f82753d5ca1b6650023da81384bc1bfb50b5a5468ddbb26e5e7a94600`, verificado antes de extraer. EXE `fa5d66761817549d5af076204230c9c4b04202ded412134d86ce9fa9dcdde6ca`, no ejecutado (bytecode y binarios idénticos a la fuente, 00) |
| V1.1.1 | `dfdb3e046126093e23b045147f789fbc52961a73` (`main`, VERSION 1.1.1). Sin tag, release ni artefacto. Se ejecutó su fuente |
| Anti-Slop anterior | `54789587d0fa7714b4dc464ec48ca8f2ce254611` |
| Lote 2D-2 final | `49106f95bacd96699c5233101490586738f5f32d` (último commit de código) |

## 3. Las cuatro comparaciones (66 escenarios)

| Comparación | Resultado | Hash de datos | Limitaciones |
|---|---|---|---|
| **A. V1.1.2 original ↔ final** | **65/66 idénticos.** El distinto es `extremo_finito_x1e150\|h11`, AS-001: la original lanza `OverflowError` y el final da «no calculable», exactamente como 5478958 | `5d74b128…` frente a `766a34b8…` | Fuente del EXE, no el EXE ejecutado |
| **B. V1.1.2 original ↔ anterior** | 65/66: el mismo caso | `5d74b128…` frente a `766a34b8…` | Ídem |
| **C. Anterior ↔ final** | **66/66 idénticos** | `766a34b8…` en los dos | — |
| **D. V1.1.1 ↔ V1.1.2** | Idénticas en estadística, proyección, economía y empalme (también en el caso extremo). En la GUI solo cambia la etiqueta de versión | `0943387e…` frente a `5d74b128…` | Sin artefacto de la 1.1.1 |

**Excepción AS-001, anterior a este lote.**
- Commit `8159d52` (Fase 1B).
- Solo actúa cuando `float(sse)` desborda: en el barrido, a partir de series de 10^150.
- No modifica los resultados ordinarios. Lo demuestran el barrido de 10^0 a 10^148, idéntico bit a bit, los 65 escenarios ordinarios idénticos y los golden con 0 diferencias exactas en las tres versiones (01 §4 y 05).

## 4. Cambios reales en producción

| Archivo | Cambio |
|---|---|
| `app_icociv/proyeccion/servicio_proyeccion.py` | −111 líneas: las dos definiciones y sus separadores. **No cambian** `_seleccionar_modelo_rectangular`, `_matriz_rectangular_12_24`, `_sse_exacto`, `_rmse_desde_sse` ni `_ejecutar_proyeccion_base` |
| `app_icociv/estadistica/criterios.py` | C-SEL-001, campo `ubicacion`: `…::seleccionar_modelo_por_rmse_oos_global` → `…::_seleccionar_modelo_rectangular`. Es un metadato no publicado (03 §3) |

**El selector vigente no cambió**: los espías hicieron 44 llamadas en la base y la huella y el oráculo dan 0 diferencias.

**Deuda registrada, no resuelta en el lote**
- **D-2D2-1.** Las guardias de umbrales `test_cierre_metodologico::test_la_seleccion_no_consulta_ningun_umbral` y `test_seleccion_rmse_global::test_la_regla_no_consulta_umbrales_ni_identidad` inspeccionan ahora la misma función, y la primera queda contenida en la segunda. Propuesta: fusionarlas en un lote de saneamiento de pruebas.
- **Inspecciones de fuente (M2 de Thermos).** D11, D12 y las dos guardias buscan cadenas en el código, como ya hacían en la base. Las garantías reales son las propiedades y los mutantes de Fase 1A.
- **Preexistentes, no tocados:**
  - imports sin uso en `servicio_proyeccion` (`UMBRAL_RRMSE_PEOR_BENCHMARK`, `TOLERANCIA_RRMSE_BENCHMARK`, `aplicar_ajuste_calendario`, `eneros_en_horizonte`, `calcular_metricas`);
  - variables muertas `comparacion_benchmarks` y `sesgo`;
  - el docstring de `_puntaje_rmse_ponderado`;
  - `struct` y `math` sin uso en pruebas;
  - fichas de criterios con rutas sin `::` (AS-024);
  - listas del CI y de `.gitignore` que crecen con cada fase.

## 5. Pruebas

| Concepto | Resultado |
|---|---|
| Esenciales | 811 → **809**. Bajas: los 2 ids autorizados. Altas: 0. **0 cambios de estado**. 0 fallos en la 1.ª ejecución y sin intermitentes en local |
| Golden / AS-001 | **29/29**, `tests/fixtures/**` sin cambios / **16/16** |
| Huella | 20/20 con 0 diferencias; SHA-256 `d6be699b…0191` idéntico |
| Oráculo ampliado | 66 escenarios: motor 35, series extra 22, fixtures 6, rechazos, economía y empalme, GUI con sesión y exportables (05) |
| Históricas | JUnit 241 → **213**: 28 retiradas, todas PASS en la base y cada una con su sustituto vigente. 47 FAIL y 3 ERROR, iguales en base y final, **0 cambios de estado** (06 §3) |
| Recolección | 1 066 → 1 036, con los **mismos 3 errores** (tratamiento consciente de pruebas, no corrección funcional) |
| Script histórico `pruebas/prueba_horizonte…` | 21/8, con los mismos ids y estados |
| `ejemplo_uso` y `prueba_estadistica` | Misma salida que en la base (errores preexistentes; sin anexo DANE, no comparables con datos reales) |
| imports, `VentanaPrincipal`, `pip check` y `compileall` | OK |
| CI | Ver §7 |

## 6. Thermos

Dos pasadas reales, cada una con los dos agentes: `thermo-nuclear-reviewer` y `thermo-nuclear-code-quality-reviewer`. Detalle en 07.

- **1.ª pasada:**
  - corrección, sin hallazgos críticos, altos ni medios;
  - calidad, «APROBADO CON OBSERVACIONES», con 3 medios y varios bajos.
- **Correcciones** en `49106f95`, solo en pruebas.
- **2.ª pasada, sobre el último commit de código:**
  - corrección, sin hallazgos nuevos;
  - calidad, **«APROBADO»**.

Thermos solo revisa diffs y no sustituye la prueba contra la original.

## 7. Git y CI

- **Rama:** https://github.com/estebanojeda0615/SAVIP/tree/maintenance/v1.1.2-fase2d-lote2-equivalencia-original-thermos, creada desde `54789587d0fa7714b4dc464ec48ca8f2ce254611`.
- **Comparación:** https://github.com/estebanojeda0615/SAVIP/compare/54789587d0fa7714b4dc464ec48ca8f2ce254611...maintenance/v1.1.2-fase2d-lote2-equivalencia-original-thermos
- **Commits:** `be46ca9` (CI), `02426ef` (G0 preliminar), `a3cd8e6` (preparatorio), `55ba564` (retiro atómico), `49106f9` (correcciones de Thermos) y el HEAD documental (04 §1).
- **CI del último commit de código** (`49106f95`): run [42426437658](https://github.com/estebanojeda0615/SAVIP/actions/runs/42426437658), **success**, 809/809, 0 fallos en la 1.ª ejecución, sin intermitentes, 1.er intento.
- **CI del informe preliminar** (`02426ef`, código = 5478958): run 42108454515, **failure** por la intermitente GUI conocida `test_interaccion_fase_3c_a::test_a`, que falló también en el reintento; no se relanzó (06 §5).
- **CI del HEAD documental:** ver el mensaje de entrega.
- **Sin cambios** en `main` (`dfdb3e0`), `develop/v1.1.2` (`6672529`), el tag y la release `v1.1.2-rc.1` (`08f364b`), el ZIP publicado, la rama AS-028 (`5478958`) ni las ramas anteriores.
- No hubo merge, PR, tag, release, EXE, ZIP ni cambio de versión.
- El ZIP y el EXE originales no se subieron.

## 8. Pendientes (no iniciados)

- **Lotes sin abrir:** **2D-1** (`determinar_horizonte_maximo_estadistico`; además, AS-028 para 2D-1 sigue abierto en el script histórico), **2D-3** (`_clasificar_evidencia_horizonte`) y **2D-6**.
- **AS-004:** funciones `_lineas_*` de `generador_reportes`.
- **AS-007:** r3, bghc, los `test_p0c_*` y los 3 errores de recolección.
- **AS-024:** fichas de criterios.
- **P0-C:** el residual del IC95 es preexistente y su corrección **sigue cancelada**.
- **Intermitente GUI** `test_interaccion_fase_3c_a::test_a`: preexistente (06 §5).

**No se inició ningún otro lote.**
