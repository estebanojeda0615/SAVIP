# 00 · Estado inicial y referencias

## 1. Punto de partida verificado (2026-10-27, 03:02 UTC, `git ls-remote`)

| Referencia | SHA | Estado |
|---|---|---|
| `maintenance/v1.1.2-fase1b-as001` (base) | `c9166c639a279cacf95a0dde842f2b3f01aa0852` | Coincide con el esperado |
| `maintenance/v1.1.2-fase1a-as006-as007` | `428fdc0` | Sin cambios |
| `maintenance/v1.1.2-fase0-reproducibilidad` | `4c46a03` | Sin cambios |
| `main` / `develop/v1.1.2` | `dfdb3e0` / `6672529` | Sin cambios |
| Tag `v1.1.2-rc.1` | `08f364b` → `6672529` | Sin cambios |
| `maintenance/v1.1.2-fase2a-as003` | — | No existía antes de esta fase |

**El clon.**
- Es nuevo: `Desktop\SAVIP_V112_FASE2A_AS003`.
- La rama `maintenance/v1.1.2-fase2a-as003` se creó desde `c9166c6`, con diff inicial vacío y árbol limpio.
- La identidad es solo local: `Esteban Ojeda <346522303+estebanojeda0615@users.noreply.github.com>`.
- No se usaron la carpeta de desarrollo ni los clones de las fases 0, 1A y 1B, ni se hicieron copias de respaldo: GitHub conserva el estado previo.

**Las ejecuciones.**
- Corren en copias limpias, con `git ls-files -co --exclude-standard`, bajo `C:\Pruebas SAVIP\Fase2A\<etapa>`.
- Esas copias no contienen `docs/` excluido ni dependen de rutas `C:\Users\...`.

**CI de referencia.**
- Run [40422903577](https://github.com/estebanojeda0615/SAVIP/actions/runs/40422903577) sobre `c9166c6`: success, 797/797, ninguna intermitente.

## 2. Entorno

| Elemento | Valor |
|---|---|
| Sistema y CPU | Windows 11 10.0.26200, AMD64 Family 25 Model 97 (AuthenticAMD) |
| Python | 3.12.10 (venv de pruebas instalado con `requirements-lock.txt` + `requirements-test.txt`, `--no-deps`) |
| Versiones clave | numpy 2.4.2, pandas 2.3.3, scipy 1.17.1, statsmodels 0.14.6, PySide6 6.11.0, openpyxl 3.1.5, reportlab 5.0.0, python-docx 1.2.0, pytest 9.1.1 |
| `requirements-lock.txt` | SHA-256 `ab30ed94c5549699…` (sin cambios) |
| Variables | `QT_QPA_PLATFORM=offscreen`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONIOENCODING=utf-8` |

## 3. Línea base antes de cambiar código (`c9166c6`)

| Medida | Resultado |
|---|---|
| `scripts/pruebas_fase0.py --listar` | esenciales 797 · dane 0 · históricas 251 + 3 errores de recolección · gui 13 · total 1 061 |
| `pytest --collect-only tests` | 1 061 pruebas recolectadas y 3 errores de recolección: los mismos 3 archivos históricos de siempre |
| Perfil esencial (copia limpia) | **797 PASS · 0 FAIL · 0 XFAIL · 0 SKIP**. Intermitentes: ninguna. 80 archivos, 1 838 s en JUnit |
| Huella semántica (04 §1) | Capturada dos veces: **0 diferencias exactas**, archivos idénticos byte a byte |
| Históricas relacionadas con AS-003 (11 archivos) | 12 fallos y 2 errores de recolección, **previos** a esta fase (04 §4) |
| `pruebas/prueba_estadistica.py` con anexo sintético de 40 meses | Termina bien (código 0) |
| `pruebas/ejemplo_uso.py` | `ejecutar_analisis` responde, pero el script se cae después al formatear `ci_lo=None`, porque P0-C retiró el intervalo. Defecto **previo** de `pruebas/` (AS-028) |

## 4. Documentos consultados

**Auditoría original.** Está en `Desktop\SAVIP_V112_AUDITORIA_ANTISLOP\`, fuera del repositorio. Los documentos son:
- `02_AUDITORIA_INTEGRAL_ANTISLOP.md`;
- `03_MATRIZ_HALLAZGOS_ANTISLOP.csv`, fila AS-003;
- `04_PLAN_DE_SIMPLIFICACION_POR_FASES.md`, fase 2, paso 5.

Lo que dicen:
- AS-003 abarca 29 definiciones (1 665 líneas) de `servicio_proyeccion.py`, el rango 280–597 y 1352–1381 de `modelos_interpretables.py` y el rango 15–181 de `validacion_series.py`.
- La recomendación literal es: «Decidir si el "registro de auditoría" debe vivir en código ejecutable». El riesgo documental se califica de «medio», porque `criterios.py` y las pruebas citan estas funciones.

**Informes de fases anteriores**, presentes en el clon:
- `docs/fase_v112_antislop_00/`;
- `docs/fase_v112_antislop_01a_pruebas/`;
- `docs/fase_v112_antislop_01b_as001/`.

## 5. Desviaciones respecto del prompt

- El prompt sitúa `ejecutar_analisis` como consumida solo por `pruebas/ejemplo_uso.py`. Es correcto para la función del **servicio**. La GUI llama a otro método con el mismo nombre, `ControladorPrincipal.ejecutar_analisis`; el grafo conservador los funde. Ver 02 §3.
- Según la auditoría, `validacion_series.py` 15–181 es código muerto. Sin embargo, `validar_serie` y `detectar_outliers_extremos` las usa el script `pruebas/prueba_estadistica.py`: son un contrato S y se mantienen.
