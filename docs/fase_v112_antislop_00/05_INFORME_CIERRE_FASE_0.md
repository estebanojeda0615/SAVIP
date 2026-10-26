# 05 · Informe de cierre de la Fase 0 (SAVIP 1.1.2)

## Dictamen: **APTO CON RESERVAS**

> **Desde GitHub puedo clonar, reconstruir el ejecutable 1.1.2 y ejecutar una red de regresión esencial autónoma. Esa red permite simplificar código sin alterar resultados.**

Evidencia de la frase:
- **Build:** clon limpio → build oficial con código 0 → EXE aislado con autocomprobación 7/7.
- **Paquete:** funcionalmente idéntico al del Release.
- **CI:** perfil esencial de **612 pruebas, 29 de ellas Golden Masters**, verde en GitHub Actions.

**Reservas (no impiden la recuperación):**
- quedan pendientes el perfil DANE real y la verificación física de la interfaz;
- algunos contratos de B4/B5 no tienen golden propio (§4).

## 1. Criterios de aceptación (§5 del encargo)

| # | Criterio | Estado | Evidencia |
|---|---|---|---|
| 1 | Remoto, tag, commit y Release verificados; Release sin modificar | **Cumple** | 00 §1. Al cierre: `main` `dfdb3e0`, `develop/v1.1.2` `6672529`, tag `08f364b0`→`6672529`. Release 423554929 `prerelease = true`, sigue sin ser «latest», ZIP 131 810 202 bytes con digest `cee5897f…` y `.sha256` con digest `bc435928…`, sin cambios |
| 2 | Compilación oficial desde clon limpio | **Cumple** | `build_portatil.ps1` con código 0 en 415 s; lock 32/32; ZIP de 1618 entradas (00 §3.2) |
| 3 | Paquete abierto y autocomprobado aislado | **Cumple, con limitación de plataforma** | Autocomprobación 7/7 y ventana real 10/10 con cierre 0, sin variables de Python y con PATH mínimo. El equipo sí tiene Python instalado: falta la prueba física en un equipo sin Python |
| 4 | Esenciales sin `docs/`; pasan en copia limpia y CI; heredadas inventariadas | **Cumple** | CI [40245287987](https://github.com/estebanojeda0615/SAVIP/actions/runs/40245287987): 612/612. Corrida local final en copia limpia: 612/612. Las 1029 pruebas están en `01_INVENTARIO_PRUEBAS.csv` |
| 5 | Golden masters del motor (3–5 series, H24), economía, sesiones y exportables; esperado congelado en git con SHA de referencia y no generado por el test | **Cumple** | 5 series + rechazos; trayectoria H1..H24 y MAE(h) h = 1..24. `golden/metadatos.json` → `6672529`, árbol `8af9547d…`. Lo genera `generar_golden.py` (aparte); las pruebas solo leen |
| 6 | El conjunto focalizado no cambia ningún resultado funcional respecto de `6672529` | **Cumple** | Los golden se generaron sobre `6672529` sin diferencias productivas y pasan en local y en el runner, con las tolerancias justificadas en 02 §5 |
| 7 | Sin cambios en producción, selección, contratos, paquetes ni `main`/`develop` | **Cumple** | Diff productivo vacío (04 §1). Solo se publicó la rama nueva |
| 8 | Archivos publicados sin datos privados, anexos, binarios ni directorios enormes | **Cumple** | Búsqueda en los 23 archivos de la rama: `Users`, `AppData`, `Desktop`, el usuario del equipo y el correo personal. Solo aparecen el nombre del repositorio, la autoría autorizada y nombres de carpetas de evidencia local sin usuario (`C:\Pruebas SAVIP\Fase0`). Golden JSON de texto, 449 KB en total. Sin xlsx, sesiones reales ni builds |
| 9 | Rama publicada y clonable; SHA final y enlace al CI | **Cumple** | Ver §5 |

## 2. Pruebas: números exactos

**Ejecución del perfil esencial:**

| Entorno | Resultado |
|---|---|
| **GitHub Actions** (`windows-latest`, Python 3.12.10, `.venv-test` del lock), commit `d6daa3f` | **595 pasan + 17/17 aisladas = 612/612**; 2 deseleccionadas (pasan al perfil gui) |
| **Clon limpio local, corrida final** (Windows 11, copia de `d6daa3f` sin `docs/`) | **595 pasan + 17/17 aisladas = 612/612**, código 0, 34 min |
| GitHub Actions, commit `edff801` (solo docs) | success ([40256137859](https://github.com/estebanojeda0615/SAVIP/actions/runs/40256137859)) |

**Golden Masters, 29 pruebas:**

| Archivo | Pruebas | Qué cubre |
|---|---|---|
| `test_fase0_golden_motor.py` | 11 | 5 escenarios × (invariantes + golden) + rechazos |
| `test_fase0_golden_economico.py` | 6 | 5 secciones + exactitud `Decimal` |
| `test_fase0_golden_sesion_exportables.py` | 12 | 8 secciones + invariantes del flujo + Excel de 5 hojas con `ROUND` + versión 1.1.2 y ±MAE no presentado como intervalo + sesión grande de 300 actividades |

**Perfiles (`scripts/pruebas_fase0.py --listar`, idéntico en local y en el runner):**

| Perfil | Pruebas | Estado |
|---|---|---|
| esenciales | 612 | Pasan |
| dane | 133 | 22 pasan, 111 necesitan la sesión DANE real |
| historicas | 271 + 3 errores de recolección | 198 pasan, 73 fallan |
| gui | 10 + lista manual | — |
| **Total** | **1026** | |

## 3. Publicado en GitHub y comprobado / preparado localmente

**Publicado y comprobado en GitHub:**
- la rama, sus 5 commits y los archivos de §5;
- el workflow y sus 3 runs: el último commit de código, `d6daa3f`, en verde;
- el Release intacto.

**Solo local** (`C:\Pruebas SAVIP\Fase0\`, no publicado a propósito):
- logs del build, ZIP reconstruido y comparación archivo por archivo con el Release;
- ejecuciones aisladas del EXE;
- corridas completas de caracterización por archivo;
- las dos generaciones de golden descartadas;
- el espía de contaminación;
- logs descargados del CI.

## 4. Brechas y reservas (lo que esta red NO cubre)

1. **Datos DANE reales:** 111 pruebas del perfil `dane` necesitan `TRES_ANALISIS_REALES.json`, que no es publicable. Ningún golden usa series reales.
2. **B4 sin golden propio:**
   - slider I0 antes y después de cambiar la fecha objetivo (lo cubre `test_fase_4i_p2_comparacion_consulta`, en el perfil esencial);
   - fecha común con orígenes DANE distintos (`test_fase_4i_j_fecha_comun`, perfil DANE);
   - restricciones de invalidación económica.
3. **B5 sin golden propio:**
   - revisiones de análisis («Actualizar con DANE más reciente»);
   - borradores del Empalme;
   - `comparacion_historica` v3 (referencias DANE externas);
   - sesión antigua sin trayectoria;
   - «Guardar y cerrar» desde el diálogo de cierre.

   Las variantes de esquema 1.1.0/1.1.1 se cubren solo por forma (03 §3) y por el **factor legado** sintético. **No se afirma compatibilidad con todas las sesiones reales de terceros.**
4. **B6:** solo se comparan texto, tablas y fórmulas. Quedan fuera los estilos de Excel, el aspecto visual de PDF/DOCX y los exportables del Empalme. Tampoco se comprueban los valores calculados de las fórmulas Excel (openpyxl no evalúa).
5. **Reproducibilidad entre CPU** (hallazgo nuevo, 02 §5 bis): los candidatos con optimizador iterativo (Holt, Huber) difieren hasta 5e-7 en RMSErect y 3,5e-5 en métricas impresas. Hoy no cambia ninguna selección, pero no es bit a bit. Sus comparaciones usan 1e-4 relativo.
6. **Pruebas con carreras de tiempo y contaminación heredadas:**
   - `test_layout_adaptable_…` y `test_integracion_sesion_con_excel_…` pasaron al perfil gui;
   - `test_interfaz_componentes` corre en un proceso propio.

   Ninguna se modificó.
7. **Sin golden dentro del EXE:** se ejecutan desde fuente. El binario solo tiene su autocomprobación 7/7 y la ventana real (más el arnés 191/191 del release, no repetido aquí).
8. **Plataforma física:** falta probar en un equipo sin Python, con escalas 125/150 %, segundo monitor, Snap y revisión visual.
9. **Determinismo del build:** el ZIP no es bit a bit idéntico al del Release (3 archivos con marcas de compilación; 00 §3.4).
10. **Hallazgos Anti-Slop documentados y sin corregir:**
    - AS-001: desborde con un candidato divergente;
    - AS-006: 40 pruebas del selector retirado, en el perfil histórico;
    - AS-007: dependencias de `docs/`;
    - AS-014;
    - AS-017: `build_exe.ps1` recomienda `package_release.ps1`;
    - las 36 expectativas obsoletas (01 §2).

## 5. Publicación

| Dato | Valor |
|---|---|
| Rama | https://github.com/estebanojeda0615/SAVIP/tree/maintenance/v1.1.2-fase0-reproducibilidad |
| Comparación con `develop/v1.1.2` | https://github.com/estebanojeda0615/SAVIP/compare/develop/v1.1.2...maintenance/v1.1.2-fase0-reproducibilidad |
| Commits | `78fe2c1`, `41d35c8`, `d6daa3f`, `edff801` (docs 04) y el commit de este informe; todos de Esteban Ojeda `<346522303+estebanojeda0615@users.noreply.github.com>` y sin trailers |
| CI verde de referencia | https://github.com/estebanojeda0615/SAVIP/actions/runs/40245287987 (`d6daa3f`, success, 612/612) |
| Release existente, sin cambios | https://github.com/estebanojeda0615/SAVIP/releases/tag/v1.1.2-rc.1 |

**Archivos publicados:**
- `.github/workflows/fase0-pruebas.yml`;
- `requirements-test.txt`;
- `scripts/pruebas_fase0.py`;
- `tests/fixtures/fase0/`: `README.md`, `generadores.py`, `captura.py`, `captura_gui.py`, `generar_golden.py` y `golden/{metadatos,motor,economico,sesion_exportables}.json`;
- `tests/test_fase0_golden_{motor,economico,sesion_exportables}.py`;
- `tests/test_historial_empalme_fase_4b.py` (modificado);
- `.gitignore` (excepción de `docs/fase_v112_antislop_00/`);
- `docs/fase_v112_antislop_00/` (00 a 05 y `01_INVENTARIO_PRUEBAS.csv`).

**No se generó** `CAMBIOS_FASE_0.diff`: el enlace de comparación de GitHub muestra el mismo diff, que es casi todo los golden JSON.

## 6. Siguientes fases recomendadas

1. **Anti-Slop, Fase 1**, con esta red como freno: correr `python scripts/pruebas_fase0.py esenciales` antes y después de cada cambio.
   - Primero: reapuntar o retirar las pruebas de AS-006 y las 36 obsoletas.
   - Luego: mover a `tests/fixtures/` los fixtures sintéticos de `docs/` (AS-007), por ejemplo `ANEXO_SINTETICO.xlsx`, que ya tiene generador.
2. **Corregir AS-001** (desborde en `_sse_exacto` con candidatos divergentes). Exige decisión, porque toca el motor; su golden ya existe.
3. **Estabilizar las 3 pruebas** con carreras de tiempo o contaminación, esperando el temporizador o la carga y sin estado global al importar. Después, devolverlas al perfil esencial.
4. **Decidir la política** de tolerancia y semilla de los optimizadores Holt/Huber (02 §5 bis).
5. **Prueba física** de la lista gui en un equipo sin Python.
