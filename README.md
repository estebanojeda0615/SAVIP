# SAVIP — Sistema de Análisis de Variaciones de Precios

**Versión 1.1.1** · Aplicación de escritorio para Windows x64 · Autor: **Esteban Ojeda**

> **Rama `develop/v1.1.2`: en desarrollo, no es una versión publicada.** Contiene la 1.1.1 más los indicadores de carga con esqueleto (Skeleton Loaders), diálogos que se ajustan a la ventana e indicadores al abrir, guardar y cerrar sesiones. Tiene pruebas automáticas, pero aún faltan la revisión manual y la aprobación del autor. `VERSION` sigue en 1.1.1 y no hay ZIP de 1.1.2. La versión estable es la de `main`.

SAVIP ayuda a actualizar precios de presupuestos de obra civil con los índices **ICOCIV** (Índice de Costos de la Construcción de Obras Civiles) que publica el DANE en Colombia. Carga el anexo oficial del DANE, proyecta la serie elegida hasta la fecha objetivo del presupuesto y calcula el valor actualizado de cada actividad. Guarda el trabajo en sesiones y exporta el resultado a Excel, PDF o Word.

## Qué hace

- **Carga del anexo ICOCIV del DANE** (`.xlsx` o `.xlsb`), que el usuario descarga de la página del DANE. El repositorio no incluye ese archivo.
- **Proyecciones ICOCIV.** Proyecta la serie hasta 24 meses (H24) desde el último dato observado. Compiten 21 candidatos: 10 modelos base (interpretables y de referencia), sus variantes con estacionalidad anual Fourier K=1 y Seasonal Naive. Se elige el de menor RMSE fuera de muestra, medido con *backtesting* rectangular y ventana expansiva común a todos.
- **Fecha objetivo consultable.** Se puede cambiar el horizonte (por ejemplo H11 → H23) sobre la trayectoria ya calculada, sin volver a ejecutar el motor. Se puede deshacer y rehacer.
- **Comparación histórica de I0.** Un deslizador explora escenarios de índice base. Los valores registrados no se modifican.
- **Empalme ICCP → ICOCIV.** Lleva presupuestos con base en el antiguo ICCP al ICOCIV. La serie histórica ICCP viaja con la aplicación (`app_icociv/datos/iccp_historico.json`).
- **Resultados, sesiones y exportación.** Las sesiones se guardan en `.json`. Se exporta a Excel (5 hojas, con fórmulas), PDF y DOCX. El tema claro u oscuro se recuerda entre usos.
- Los importes se redondean con la regla económica `ROUND_HALF_UP`.

## Limitaciones estadísticas y responsabilidad

- La banda **±MAE(h)** que acompaña cada punto proyectado es el error absoluto medio histórico del *backtesting* para ese horizonte. **No es un intervalo de confianza** ni una probabilidad de cobertura.
- Las proyecciones son estimaciones a partir de la serie publicada. No garantizan el valor que el DANE publique después. Si llega un anexo más reciente, conviene actualizar los análisis con él.
- SAVIP es una herramienta de apoyo. Las cifras de cualquier presupuesto deben ser revisadas y aprobadas por el profesional responsable. El autor no asume responsabilidad por decisiones tomadas solo con los resultados del programa.

## Usar la versión portátil

1. Extraiga **todo** el ZIP `SAVIP_1.1.1_Portatil_Windows_x64.zip`. No ejecute el programa desde dentro del ZIP.
2. Abra `SAVIP_1.1.1_Portatil\SAVIP.exe`. No hace falta instalar Python. La carpeta `_internal\` debe quedar siempre junto al EXE.
3. Cargue el anexo ICOCIV del DANE (botón «Cargar archivo Excel»). Luego use Proyecciones, Empalme y Resultados.

El ejecutable no tiene firma digital, así que Windows SmartScreen puede advertir «editor desconocido». Las instrucciones para el usuario final están en [`packaging/LEEME_PORTATIL.txt`](packaging/LEEME_PORTATIL.txt), que también va dentro del ZIP.

## Compilar desde este repositorio

Requisitos:

- Windows 10/11 x64.
- Python **3.12** de 64 bits (la referencia es 3.12.10).
- Git y acceso a PyPI.

Desde PowerShell:

```powershell
git clone https://github.com/estebanojeda0615/SAVIP.git
cd SAVIP
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_portatil.ps1
```

Resultado: `release\SAVIP_1.1.1_Portatil_Windows_x64.zip` (junto con su `.sha256`) y la carpeta `dist\SAVIP\`. La guía completa, con los errores típicos y cómo verificar el EXE, está en **[COMPILACION_WINDOWS.md](COMPILACION_WINDOWS.md)**.

También se puede compilar en GitHub Actions. Vaya a *Actions › build-windows › Run workflow* y descargue el artefacto con el ZIP.

## Estructura

| Ruta | Contenido |
|---|---|
| `aplicacion.py` | Punto de entrada (interfaz o `--autocomprobacion`) |
| `app_icociv/` | Código de la aplicación: `estadistica/`, `proyeccion/`, `validacion/` (backtesting), `servicios/` (fecha objetivo, empalme, actualización), `interfaz/` (PySide6, tema, recursos SVG/PNG), `reportes/`, `exportables/`, `persistencia/` (sesiones), `datos/` (ICCP histórico) |
| `packaging/` | `SAVIP.spec` (PyInstaller, onedir), icono, metadatos de versión del EXE, `LEEME_PORTATIL.txt` |
| `scripts/` | `build_portatil.ps1` (una orden), `build_exe.ps1`, `empaquetar_portatil.py`, `verificar_lock.py`, `clean_build.ps1`, `package_release.ps1` |
| `requirements-lock.txt` | Las 32 dependencias de ejecución con versión exacta |
| `requirements-build.txt` | PyInstaller 6.22.3 y sus dependencias, con versión exacta |
| `tests/`, `pruebas/` | Pruebas automatizadas y guiones de prueba manual |
| `VERSION` | Fuente única del número de versión |

## Pruebas

pytest no es una dependencia del producto. Algunas suites traen su propio ejecutor (`python tests\<archivo>.py`) y otras se ejecutan con pytest.

Varias suites de interfaz leen *fixtures* sintéticas grandes de `docs/` que este repositorio no publica, entre ellas las de las fases 4I-P y 4I-P2. Otras necesitan un anexo DANE real. En un clon limpio, esas suites no se pueden ejecutar. Las que sí funcionan sin archivos externos, como `tests\test_rutas_empaquetado.py` y las tres pruebas previas de `build_exe.ps1`, se listan en [COMPILACION_WINDOWS.md](COMPILACION_WINDOWS.md#5-pruebas-focalizadas).

## Licencia

Este repositorio todavía no declara una licencia de código abierto. Las dependencias de terceros conservan sus propias licencias: PySide6/Qt (LGPL), NumPy, pandas, SciPy, scikit-learn, statsmodels, matplotlib, ReportLab, python-docx, openpyxl, pyxlsb y otras. Quien redistribuya el ejecutable debe cumplir esas licencias. El paquete compilado incluye solo algunos de esos avisos, por ejemplo el de NumPy.
