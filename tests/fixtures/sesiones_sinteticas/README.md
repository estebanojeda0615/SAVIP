# Sesiones sintéticas de desarrollo (Fase 1A, AS-007)

Seis sesiones JSON comprimidas con gzip, que las pruebas leían de `docs/`, carpeta que no se publica en GitHub.

**No contienen datos del DANE ni datos personales.**
- Las series son las del anexo sintético («Grupos_Obra sintético 1/2», «Subclases sintético 2»).
- Se generaron con el motor real de SAVIP en fases de desarrollo anteriores. Por eso conservan sus particularidades: factor legado sin `criterio_factor` y `resultado` de esa versión del motor.
- No se regeneran con el código actual porque eso cambiaría la semántica que las pruebas comprueban (sesiones antiguas, factor legado).

## Única transformación aplicada

- **Qué cambia:** en los campos `archivo_excel`, la ruta absoluta del equipo de desarrollo (`C:\Users\<usuario>\Desktop\<carpeta>\…`) se reduce a su parte relativa `docs\…`. Esa ruta tampoco existe en un clon, así que se conserva la semántica «el Excel original no está disponible».
- **Qué no cambia:** ningún otro valor. Se verificó con el comparador de la Fase 0 (`captura.diferencias`): solo difieren esos campos.
- **Formato:** JSON compacto (sin sangría) dentro de gzip con `mtime = 0`, reproducible byte a byte.

## Procedencia y hashes

**Fuente:** copia local de solo lectura de `docs/` del repositorio de desarrollo 1.1. **Scripts:** `sanear_tres.py` y `sanear_fixtures.py` (evidencia local de la fase).

| Archivo | Ruta original en `docs/` | SHA-256 de la fuente | Rutas saneadas | SHA-256 del JSON saneado |
|---|---|---|---|---|
| `TRES_ANALISIS_SINTETICOS.json.gz` | `fase_4d_slider/fixtures/TRES_ANALISIS_REALES.json` («REALES» = motor real, no datos reales) | `03b27745498af0c715113f57d760013c06aec48fc5df15a996c62eadb99c4d3d` | 3 | `aed91ab258b8991eead080756f6798596aaeee9051e0eea3617e438b4acc8742` |
| `FASE_4A_FIXTURE_DATOS.json.gz` | `fase_4a_excel_formulas_simples/FIXTURE_DATOS.json` = `fase_4a_d/FIXTURE_DATOS.json` (idénticos) | `fa23f76914ac0673450f5cb121c3a2c4a5ba4c82c880b3af74b7aa4bb39a2725` | 3 | `fa80a2d9badd906582e8835b9cb93408bcc9d538f2e5141eec0fb4462de3c1c3` |
| `FASE_4A_C_FIXTURE_DATOS.json.gz` | `fase_4a_c/FIXTURE_DATOS.json` | `f9a4a4e68ad8a8c4c25cded5a86f1c21ad7c55ee976ffd4f5513c9bb62f71830` | 3 | `5cc0d1506019e7bc71ed5f4ff2762823a5ae0e341b8cf378ca46bfac6b5c6dfa` |
| `FASE_4B_FIXTURE_DATOS.json.gz` | `fase_4b/FIXTURE_DATOS.json` | `3313140ea05aba2675bf23fbac621843199187896146063269e373c9f4331aa1` | 4 | `aa63faff466831dba454720730c86ef399c524e8c46b7f52f0909a1edc4226ab` |
| `FASE_4C_FIXTURE_DATOS.json.gz` | `fase_4c/FIXTURE_DATOS.json` | `b72e93eb5d1428091f518264f6076718cda54f60d1a67c5cbe3cf3aa7ab1fb06` | 4 | `b71fa3ffb901eba48d053d3ad4a51df53f6e4bc3b65956080d9f160ece316d88` |
| `SESION_AUDITORIA_UI.json.gz` | `auditoria_better_ui_v11/temporal/sesion_auditoria.json` | `5d65f3fe7860db62d882aa59ae9fc2df155596f50282b71fa0bfc282120e7826` | 4 | `b33b9c85c75fae7c19316f04769af0c884e7e165b69ce065dc8e1c7fb99f3a20` |

**Uso:** `tests/fixtures/sesiones.py`.
- `cargar(nombre)` devuelve una copia nueva del diccionario.
- `ruta_temporal(nombre)` lo escribe como `.json` en una carpeta temporal, para las pruebas que abren la sesión desde disco.

**Anexo de esas sesiones:** el anexo sintético `docs/fase_4d_slider/fixtures/ANEXO_SINTETICO.xlsx` no se copia: lo regenera `tests/fixtures/fase0/generadores.anexo_slider_4d`, idéntico celda a celda (3726 celdas).
