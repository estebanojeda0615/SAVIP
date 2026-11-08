# 00 · Identificación de la V1.1.2 original empaquetada y de la V1.1.1

> **Historia de G0.** El primer dictamen de G0 fue **NO-GO previo** (discrepancia anterior a 2D-2: AS-001), publicado en
> `02426ef`. El 05-11-2026 a las 22:40 UTC el propietario eligió la opción A: **aceptó AS-001 como única excepción
> preexistente**, limitada al desbordamiento de `float(sse)`, y exigió igualdad exacta en todos los casos que la
> original completa. Con esa decisión G0 pasó a GO y el lote continuó (02-08). Este documento conserva la
> identificación tal como se hizo antes de cualquier cambio.

## 1. Tabla de procedencia

| Referencia | Commit completo y árbol | Fuente comprobada | Artefacto y SHA-256 | Entorno y dependencias | ¿Ejecutable? | Límites de verificación |
|---|---|---|---|---|---|---|
| **V1.1.2 ORIGINAL empaquetada** | `66725293f304426ae6edf144b8f4dadbcbeefe10`, árbol `b484bd4f8df7c4ba48566b6293c33f5b69a1f9ba` | Tag anotado `v1.1.2-rc.1` (objeto `08f364b`, firmado por Esteban Ojeda: «SAVIP 1.1.2-rc.1: compilación de prueba Windows x64»). La pre-release de GitHub tiene `target_commitish` = 6672529. `VERSION` = 1.1.2, y también `_internal/VERSION` del paquete. **Bytecode: los 87 módulos `app_icociv` y el script `aplicacion` del EXE son estructuralmente idénticos a los compilados desde la fuente 6672529** (§2) | ZIP `SAVIP_1.1.2_Portatil_Windows_x64.zip`, 131 810 202 bytes, SHA-256 `cee5897f82753d5ca1b6650023da81384bc1bfb50b5a5468ddbb26e5e7a94600`. Coincide con el digest de GitHub y con el `.sha256` de la release. `SAVIP.exe`: `fa5d66761817549d5af076204230c9c4b04202ded412134d86ce9fa9dcdde6ca` | Runtime Python 3.12 (`python312.dll`, magic pyc `cb0d0d0a`), numpy 2.4.2, scipy 1.17.1, pandas 2.3.3, statsmodels 0.14.6, scikit-learn 1.8.0 y matplotlib 3.10.9. **Los 228 binarios nativos (`.pyd`) de numpy, scipy, pandas, statsmodels y sklearn, y las DLL OpenBLAS/MSVC de `*.libs`, son idénticos byte a byte a los del entorno de pruebas** | La fuente 6672529 se ejecutó en el entorno de pruebas. **El EXE no se ejecutó**: es una aplicación gráfica sin interfaz de línea de comandos | La equivalencia del EXE se apoya en la identidad del bytecode y de los binarios numéricos, no en ejecutarlo. Por eso, en sentido estricto, es «equivalencia con la fuente demostrada de la V1.1.2 empaquetada». Los módulos puros de terceros dentro del PYZ (por ejemplo el código Python de pandas o statsmodels) no se compararon uno a uno; sí sus versiones declaradas |
| **V1.1.1** | `dfdb3e046126093e23b045147f789fbc52961a73` (`main`) | `VERSION` = 1.1.1. Commit «SAVIP 1.1.1: código fuente reconstruible para Windows x64». Las notas de la release 1.1.2 dicen que «la 1.1.1… sigue siendo la de `main`». Es ancestro directo de 6672529. **No tiene tag ni release propios** | No hay artefacto empaquetado de la 1.1.1 en GitHub. No se inventa ninguno | El mismo entorno de pruebas | Sí, la fuente | Frente al EXE 1.1.2 solo difieren 3 módulos de interfaz, y 2 de interfaz son nuevos en la 1.1.2. Ningún módulo de estadística, proyección, economía, reportes ni exportables cambia |
| **Anti-Slop anterior** | `54789587d0fa7714b4dc464ec48ca8f2ce254611` | Git (rama `maintenance/v1.1.2-as028-preparacion-2d2-thermos`, CI 41954109682) | No se empaqueta | El mismo entorno de pruebas | Sí | Frente al EXE difieren exactamente 3 módulos de producción: `modelos_interpretables`, `validacion_series` y `servicio_proyeccion` |
| **Lote 2D-2 nuevo** | `49106f95bacd96699c5233101490586738f5f32d` (último commit de código; producción idéntica a `55ba5646`) | Git, misma rama | No se empaqueta | El mismo entorno de pruebas | Sí | Ver 05 y 06 |

## 2. Cómo se demostró la procedencia del EXE

1. Descargué el ZIP a una carpeta temporal aislada (`C:\Pruebas SAVIP\L2\zip_original`), verifiqué el SHA-256 **antes de extraer** y lo extraje en otra carpeta. El ZIP no se modificó y no se sube al repositorio.
2. Escribí un lector propio, de solo lectura, del archivo PyInstaller embebido en `SAVIP.exe` (`evidencia/scripts/leer_pyinstaller.py`), sin instalar herramientas.
   - El CArchive contiene el PYZ y el script `aplicacion` (`evidencia/carchive_toc.txt`).
   - El PYZ contiene 2 433 módulos, de los que 87 son `app_icociv` (`evidencia/pyinstaller.txt`).
3. `procedencia_bytecode.py` compila cada módulo de la fuente con el mismo `co_filename` y `optimize=0` y compara el objeto de código completo con el empaquetado, de forma recursiva:
   - bytecode, nombres y variables;
   - tablas de líneas y de excepciones, flags, aridad y stacksize;
   - constantes con su tipo (los float, en hex);
   - objetos de código anidados.

   Dos ajustes de diagnóstico, documentados en el script:
   - `marshal.dumps` no sirve para comparar, porque sus bytes dependen del internado del proceso;
   - los `frozenset` constantes se ordenan antes de comparar, porque su `repr` varía con el hash aleatorio.

   Cada comparación se repitió dos veces, con el mismo resultado:

   | Fuente | Iguales | Distintos | Ausentes en la fuente |
   |---|---|---|---|
   | 6672529 | **87/87** | 0 | 0 |
   | dfdb3e0 | 82 | 3, de interfaz | 2, de interfaz |
   | 5478958 | 84 | 3, de producción, retocados por Anti-Slop | 0 |

   `aplicacion` es igual en las tres (`evidencia/procedencia_*.txt`).
4. Las versiones de las dependencias se leyeron de los propios módulos de versión del PYZ, y los binarios nativos se compararon con `cmp` frente al venv de pruebas: 228/228 `.pyd` idénticos y las 4 DLL de `numpy.libs`, `scipy.libs` y `pandas.libs` idénticas.

## 3. Copias de las bases

Las tres fuentes se extrajeron con `git archive` a `C:\Pruebas SAVIP\L2\fuentes\{6672529,dfdb3e0,5478958}`. Son copias separadas y de solo lectura en la práctica: ningún archivo de ellas se editó, y el oráculo solo las importa. No se hizo checkout destructivo y no se tocaron ramas, tags ni la release.

## 4. Datos DANE

No hizo falta ningún anexo DANE real. Todas las entradas son sintéticas y explícitas:
- las series del arnés Fase 0, con semilla;
- 8 series adicionales con semilla, definidas en el oráculo;
- los dos fixtures versionados `serie_drift.csv` y `serie_holt.csv`, idénticos en 6672529 y en 5478958;
- el anexo sintético que genera el arnés para el recorrido GUI.

No se atribuyen datos ficticios al DANE.
