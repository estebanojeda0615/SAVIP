# 00 · Estado base y alcance

## 1. Referencias remotas (`git ls-remote`, 2026-10-29, 03:55 UTC)

| Referencia | SHA | Estado |
|---|---|---|
| `maintenance/v1.1.2-fase2b-as003-opcion-b` (base) | `2f70391e1b920764e79fa50ec2c2da6b6b572e53` | Coincide. CI [40591163242](https://github.com/estebanojeda0615/SAVIP/actions/runs/40591163242): success |
| Fases 2A / 1B / 1A / 0 | `1848275` / `c9166c6` / `428fdc0` / `4c46a03` | Sin cambios |
| `main` / `develop/v1.1.2` | `dfdb3e0` / `6672529` | Sin cambios |
| Tag `v1.1.2-rc.1` | `08f364b` → `6672529` | Sin cambios |
| `maintenance/v1.1.2-fase2c-registro-historico` | — | No existía |

**Clon de trabajo.** Es nuevo: `Desktop\SAVIP_V112_FASE2C_REGISTRO_HISTORICO`. La rama `maintenance/v1.1.2-fase2c-registro-historico` sale de `2f70391`, con el diff inicial vacío y el árbol limpio. La identidad es solo local: Esteban Ojeda `<346522303+estebanojeda0615@users.noreply.github.com>`.

**Ejecuciones.**
- Corren en copias limpias (`git ls-files -co --exclude-standard`) bajo `C:\Pruebas SAVIP\Fase2C\`.
- El entorno es el de las fases 2A y 2B: Windows 11, AMD Family 25, Python 3.12.10 y venv con `requirements-lock.txt` + `requirements-test.txt` (`--no-deps`).
- `huella_semantica.py` escribe sus JSON fuera del repositorio (unos 155 MB) y solo con datos sintéticos.

## 2. Línea base antes de cambiar nada (`2f70391`)

| Medida | Resultado |
|---|---|
| `--listar` | esenciales 797 · dane 0 · históricas 242 + 3 errores de recolección · gui 13 · total 1 052 |
| `pytest --collect-only tests` | 1 052 ids y 3 errores de recolección previos (`test_equivalencia_presupuestal_fase_4e_b`, `test_p0c_objeto_publico_sin_intervalo`, `test_p0c_regresion_negativa_c2`) |
| Perfil esencial | **797 PASS · 0 FAIL · 0 XFAIL · 0 SKIP**. Sin reintentos ni intermitentes. 29/29 golden. 1 905 s en JUnit |
| AS-001 | 16 casos `test_as001_*` en PASS (dentro del perfil) |
| Casos GUI de temporización conocidos | Siguen en el perfil gui (13 pruebas), fuera del esencial. No se ejecutaron (fuera de alcance) |
| Huella semántica, dos capturas | **0 diferencias**. SHA-256 `d6be699b…`, el mismo de las fases 2A y 2B |
| Históricas relacionadas | 12 fallos previos ajenos a las funciones heredadas (03, «estado_antes») y 2 errores de importación `test_p0c_*` |

## 3. Alcance

**Hecho en la Fase 2C:**
- inventario (01);
- registro histórico (02);
- matriz de pruebas (03);
- AS-024 (04) y AS-028 (05) diseñados, sin aplicar;
- plan 2D (06);
- **7 pruebas nuevas de la ruta vigente** (`tests/test_fase2c_contratos_vigentes.py`), incorporadas al perfil esencial;
- la rama añadida al filtro del workflow.

**No tocado:**
- `app_icociv/**`, incluido `criterios.py`;
- `aplicacion.py`, `packaging/`, `VERSION`, `requirements*`, `pruebas/`;
- golden y tolerancias;
- las 31 definiciones heredadas, y ninguna de las 797 pruebas esenciales previas.

**Herramientas reutilizadas:**
- de 2A/2B: `grafo_as003.py`, `conjunto_retirable.py`, `espia_as003.py`, `huella_semantica.py` y `comparar_ids_esenciales.py`;
- nuevas en `evidencia/`: `pruebas_dependientes.py`, `generar_inventario_2c.py`, `generar_matriz_pruebas.py` y `sensibilidad_pruebas_nuevas.py`.
