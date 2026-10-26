# 00 · Estado inicial y alcance de la Fase 1A (AS-006 + AS-007)

## 1. Punto de partida verificado (2026-10-25/26, hora de Colombia)

| Referencia | Valor | Comprobación |
|---|---|---|
| `main` | `dfdb3e046126093e23b045147f789fbc52961a73` | `git ls-remote`, sin cambios |
| `develop/v1.1.2` | `66725293f304426ae6edf144b8f4dadbcbeefe10` | Sin cambios |
| Tag `v1.1.2-rc.1` | objeto `08f364b0…` → `66725293…` | Sin cambios; Release 423554929 intacto |
| Rama Fase 0 | `maintenance/v1.1.2-fase0-reproducibilidad` = **`4c46a03a9fc85a624cdd5c74563eaca6a02582b1`** | El prompt esperaba `9ed97c6`; el remoto manda. `4c46a03` es el commit de la Fase 0 que recalibró la holgura Holt/Huber |
| CI de `4c46a03` | [40263623668](https://github.com/estebanojeda0615/SAVIP/actions/runs/40263623668): **success**, 595 + 17 aisladas = **612/612**, 2 deseleccionadas | API de GitHub |
| Rama nueva | `maintenance/v1.1.2-fase1a-as006-as007`, creada **exactamente** desde `4c46a03` | Clon nuevo en `Desktop\SAVIP_V112_FASE1A_PRUEBAS`; árbol limpio |

**Línea base local.** En una copia limpia de `4c46a03`, sin `docs/` y con `venv-test` (lock + `requirements-test.txt`):
- `python scripts/pruebas_fase0.py esenciales` → **595 pasan + 17/17 aisladas = 612/612**, código 0 (36 min);
- esa corrida escribió **18 archivos en `docs/`** dentro de la copia (`fase_3`, `fase_4i_n`, `fase_4i_p`, `fase_4i_j_k`, `fase_3c_a`): es la escritura a `docs/` de AS-007.

**Fuentes no usadas:** `SAVIP_V1_1_2_DESARROLLO` no se usó como fuente ni se escribió. Se leyeron, sin escribir, copias de `docs/` del repositorio 1.1 local solo para conocer la procedencia de los fixtures sintéticos (ver 02).

## 2. Perfiles de partida (Fase 0, `scripts/pruebas_fase0.py --listar`)

| Perfil | Pruebas | Estado en clon limpio |
|---|---|---|
| esenciales | 612 | 612 pasan |
| dane | 133 | 22 pasan, 111 fallan («requieren sesión DANE real»: clasificación **errónea**, ver 02 §1) |
| historicas | 271 + 3 errores de recolección | 198 pasan, 73 fallan |
| gui | 10 | 4 dependen de fuentes; 2 carreras de tiempo |
| **Total** | **1026** | |

## 3. Hallazgos bajo examen y alcance

- **AS-006:** pruebas que protegen selectores o funciones retiradas mientras el selector vigente queda sin protección; AS-001 aparece como síntoma.
- **AS-007:** pruebas que leen o escriben `docs/` no publicado; expectativas antiguas.

**Fuera de alcance (no se tocaron):**
- `app_icociv/**`, `aplicacion.py`, `packaging/**`, `VERSION`, los `requirements*.txt` de la aplicación;
- los Golden Masters (`tests/fixtures/fase0/golden/*.json`) y sus tolerancias;
- el workflow de build, `main`, `develop/v1.1.2` y la rama de la Fase 0;
- el tag y el Release.

No se recompiló el EXE ni se publicó ningún ZIP. AS-001 **no** se corrige: solo se reproduce como `xfail` estricto.
