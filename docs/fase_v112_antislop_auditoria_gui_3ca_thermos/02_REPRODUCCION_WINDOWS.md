# 02 · Reproducción en Windows

## 1. Protocolo

- **Equipo:** Windows 11 (10.0.26300), 16 núcleos lógicos, Python 3.12.10, PySide6/Qt 6.11.0 y `QT_QPA_PLATFORM=offscreen` (00 §4).
- **Ejecución:** **un proceso fresco de pytest por intento**, sin el runner `scripts/pruebas_fase0.py` y por tanto **sin reintentos**:
  `python -m pytest -p no:cacheprovider -q -rA <objetivo> --junitxml=<intento>.xml`
  Todos los fallos se cuentan.
- **Scripts:** `evidencia/scripts/campana.sh` y, con el plugin pasivo de trazas, `evidencia/scripts/campana_traza.sh`. Cada intento deja un manifiesto con inicio UTC, duración, código de salida y resultado (`evidencia/campanas/*.tsv`), y además su salida y su JUnit.
- **Rutas de los scripts:** las de la ejecución original. Se pueden cambiar con `PYTHON_3CA`, `SALIDA_3CA` y `SONDA_3CA`.
- **Carga controlada:** 16 procesos de cálculo en paralelo (`evidencia/scripts/sonda/carga_cpu.py`), lanzados 1 s antes de cada intento. Se usaron para **desplazar los tiempos** y comprobar si la carrera es real. No se emplean como argumento estadístico.
- **Copias:** `base` (863de0c, prueba intacta) y `parche` (prueba con la espera por condición). El código de producción es idéntico en las dos (`diff -rq` de `app_icociv` vacío).

## 2. Resultados

| Campaña | Árbol | Objetivo | Carga | Intentos | FAIL | Firma de los fallos |
|---|---|---|---|---|---|---|
| G1 | base | nodo `test_a` | no | 30 | **0** | — |
| G2 | base | nodo `test_a`, con trazas | 16 procesos | 30 | **5** (intentos 10, 11, 19, 20 y 28) | `assert (2 == 1)` en `:140` |
| G1 | base | archivo completo (4 tests) | no | 10 | **2** (intentos 3 y 10) | `assert (2 == 1)` en `:140` |
| G1 | base | archivo completo | no | 30 | **0** | — |
| G5 | parche | nodo `test_a`, con trazas | 16 procesos | 30 | **0** | — |
| G5 | parche | nodo `test_a` | no | 30 | **0** | — |
| G5 | parche | archivo completo | no | 10 | **0** | — |
| G5 | parche | archivo completo | no | 30 | **0** | — |

Notas:
- Ventanas del spy del toggle trazadas:
  - **Base (G2):** 5 ventanas anómalas entre las trazadas, todas con la 2.ª emisión de origen `_adaptar_ancho`. Cada ejecución que falla se detiene en esa ventana.
  - **Parche (G5):** 540 ventanas (30 ejecuciones × 18), 0 anómalas, y el temporizador **nunca** vence dentro de la ventana del spy.
  - Detalle en `evidencia/analisis_G2_base_carga.txt` y `analisis_G5_parche_carga.txt`.
- Las campañas G5 del nodo y la de 10 ejecuciones del archivo se hicieron sobre `ffb7770`. La de 30 ejecuciones del archivo y el perfil esencial, sobre `06feeb4`, que solo renombra el helper sin cambiar su comportamiento (06).
- En G2, los intentos 1-9 se ejecutaron con una versión anterior del plugin que no registraba la creación del spy. Sus resultados PASS y FAIL son válidos, pero sus trazas no delimitan la ventana. Los 5 fallos (intentos 10 en adelante) sí la delimitan.
- La campaña inicial del archivo completo en la base (2 de 10) y la posterior (0 de 30) muestran una frecuencia variable sin carga: **2 de 40**. No se infiere ninguna tasa.

## 3. Conclusión de G1

**El fallo se reproduce en Windows con la prueba intacta**, con la misma aserción y el mismo recuento que en CI:
- sin carga, al ejecutar el archivo completo: 2 de 40;
- con carga, al ejecutar el nodo: 5 de 30.

El mecanismo está en 03.
