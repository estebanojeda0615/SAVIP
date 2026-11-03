# 04 · Comparación semántica y Golden Masters

**El comparador con lista blanca no aplica.** El GATE 0 terminó en NO-GO (01), así que no se retiró ni se vació ninguna ruta pública y no hay excepciones que poner en una lista blanca.

## Huella completa

Sin cambios de producción, la huella original tiene que seguir exactamente igual. Así es:

| Comprobación | Resultado |
|---|---|
| `huella_semantica.py` (Fase 2A) sobre la rama | 20/20 casos, **0 diferencias exactas** frente a la base |
| SHA-256 de la base `dfcaaa9` | `d6be699b700b3fa3379c743cc9d0ccbf5c185cacfa228208dbb95c2735370191` |
| SHA-256 de la rama | `d6be699b700b3fa3379c743cc9d0ccbf5c185cacfa228208dbb95c2735370191` (idéntico) |

Comandos en [`evidencia/huella_resumen.txt`](evidencia/huella_resumen.txt).

## Golden Masters, perfil esencial, AS-001 y r3

La rama no toca `app_icociv/**`, `tests/**`, `scripts/**` ni `tests/fixtures/**`. Por tanto:

| Control | Resultado |
|---|---|
| Golden Masters y perfil esencial (812 ids), AS-001 (16/16) | Mismo código que `dfcaaa9`, cuyo CI dio 812/812 con 29/29 golden. El CI de esta rama vuelve a ejecutarlos (06) |
| Recolección (`pytest --collect-only -q` en la rama) | 1 067 recolectadas y los **3 errores históricos**, igual que en la base. Ni la prueba ni los scripts de `docs/` se recolectan |
| `scripts/pruebas_fase0.py --listar` | Esenciales: 82 entradas y 812 pruebas, sin cambios (verificado por la revisión Thermos de corrección, 05) |
| r3 directo | Mismo código. No se ejecutó de nuevo porque no puede cambiar: sigue en 21/27, como en `dfcaaa9` |
