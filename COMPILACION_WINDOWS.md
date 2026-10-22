# Compilar SAVIP 1.1.1 en Windows x64

Esta guía produce `SAVIP.exe` y el ZIP portátil desde un clon limpio de este repositorio. Solo se necesita lo que está versionado, Python y las dependencias de PyPI. No hace falta ningún archivo del equipo donde se desarrolló SAVIP.

> El anexo ICOCIV del DANE **no** se necesita para compilar. Sí se necesita para **usar** el programa: el usuario lo descarga de la página del DANE (anexo ICOCIV, `.xlsx` o `.xlsb`) y lo carga con «Cargar archivo Excel».

## 1. Requisitos

| Requisito | Versión | Notas |
|---|---|---|
| Windows | 10 u 11, x64 | Compilación y destino |
| Python | **3.12.x de 64 bits**, referencia **3.12.10** | El lock fija ruedas `cp312` para Windows x64. Con otra versión menor (3.11, 3.13) no se instala. El instalador de python.org y el de Microsoft Store sirven |
| Git | cualquiera reciente | Para clonar |
| Internet | acceso a PyPI | Ruedas de PySide6, SciPy, NumPy, pandas, etc. (varios cientos de MB la primera vez) |
| Espacio en disco | ≥ 3 GB libres | Medido: `.venv-build` 1,2 GB; `build/` 71 MB; `dist/` 298 MB; `release/` 722 MB |
| PowerShell | Windows PowerShell 5.1 (incluido en Windows) | |

Dependencias con versión exacta:

- `requirements-lock.txt`: 32 paquetes de ejecución (PySide6 6.11.0, numpy 2.4.2, pandas 2.3.3, scipy 1.17.1, scikit-learn 1.8.0, statsmodels 0.14.6, matplotlib 3.10.9, reportlab 5.0.0, python-docx 1.2.0, openpyxl 3.1.5, pyxlsb 1.0.10, …).
- `requirements-build.txt`: PyInstaller 6.22.3, pyinstaller-hooks-contrib 2026.8, altgraph, pefile, pywin32-ctypes y setuptools.

## 2. Construcción en una orden

```powershell
git clone https://github.com/estebanojeda0615/SAVIP.git
cd SAVIP
python --version
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_portatil.ps1
```

`python --version` debe mostrar `Python 3.12.x`. Si `python` no está en el PATH, instale Python 3.12 x64 y marque «Add python.exe to PATH».

Qué hace `build_portatil.ps1`:

1. **`scripts\build_exe.ps1`**
   - Comprueba Python 3.12 de 64 bits.
   - Crea desde cero `.venv-build\` dentro del clon.
   - Instala `requirements-lock.txt` y `requirements-build.txt` con `--no-deps` y ejecuta `pip check`.
   - Verifica las 32 versiones con `scripts\verificar_lock.py` y deja el registro en `release\verificacion_lock.json`.
   - Ejecuta 3 pruebas previas.
   - Limpia `build\` y `dist\` y ejecuta `PyInstaller packaging\SAVIP.spec --noconfirm --clean`.
   - Comprueba los recursos empaquetados y ejecuta `SAVIP.exe --autocomprobacion`. La compilación se aborta si falla.
2. **`scripts\empaquetar_portatil.py`**
   - Arma `release\SAVIP_1.1.1_Portatil_Windows_x64.zip` con una sola carpeta raíz `SAVIP_1.1.1_Portatil\`, que contiene `SAVIP.exe`, `_internal\` y `LEEME_PORTATIL.txt`.
   - Verifica el CRC de todas las entradas y escribe el `.sha256`.
3. **Prueba del ZIP extraído.** Lo extrae en una carpeta temporal y ejecuta allí `SAVIP.exe --autocomprobacion`, sin variables `PYTHON*`, `VIRTUAL_ENV` ni `CONDA*`.

Tiempo medido en el equipo de referencia (Windows 11, Python 3.12.10) desde un clon limpio: **6 minutos** en total, con la caché de pip del equipo ya poblada. Sin caché, la descarga de las ruedas añade un tiempo que depende de la conexión.

## 3. Salidas

| Ruta | Contenido |
|---|---|
| `dist\SAVIP\` | Distribución *onedir*: `SAVIP.exe` + `_internal\` (unos 1617 archivos) |
| `release\SAVIP_1.1.1_Portatil_Windows_x64.zip` | Paquete portátil para entregar (unos 126 MiB, 1618 entradas) |
| `release\SAVIP_1.1.1_Portatil_Windows_x64.zip.sha256` | Huella SHA-256 del ZIP |
| `release\SAVIP-1.1.1-windows\` | Copia de `dist\SAVIP` con `VERSION.txt` (la genera `build_exe.ps1`) |
| `release\verificacion_lock.json`, `release\autocomprobacion.txt` | Evidencia de la compilación |

`SAVIP.exe` necesita su carpeta `_internal\` al lado. No distribuya el EXE solo.

El SHA-256 del ZIP **no** coincide bit a bit con el de otra compilación, porque PyInstaller y el ZIP guardan marcas de tiempo. La reproducibilidad que se garantiza es funcional: las mismas versiones, los mismos archivos y la misma autocomprobación.

## 4. Verificar el EXE

```powershell
$v = Get-Content VERSION
(Get-Item "dist\SAVIP\SAVIP.exe").VersionInfo.ProductVersion
Start-Process dist\SAVIP\SAVIP.exe -ArgumentList --autocomprobacion -Wait -NoNewWindow -PassThru -RedirectStandardOutput auto.txt | Select-Object ExitCode
Get-Content auto.txt
Get-FileHash "release\SAVIP_${v}_Portatil_Windows_x64.zip" -Algorithm SHA256
```

- `ProductVersion` debe ser `1.1.1`.
- `ExitCode` debe ser `0`, y `auto.txt` debe mostrar «Autocomprobacion de SAVIP 1.1.1» con 7/7 comprobaciones.
- Después, abra `SAVIP.exe` con doble clic. La ventana se titula «SAVIP v1.1.1 — Sistema de Análisis de Variaciones de Precios».

## 5. Pruebas focalizadas

`build_exe.ps1` ya ejecuta 3 pruebas antes de compilar:

- `test_imports_modulos.py`
- `test_empalme_iccp_icociv.py`
- `test_auditoria_formulas_estadisticas.py`

La prueba de rutas de empaquetado se ejecuta así, desde la raíz del clon y con el entorno que crea el script:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\.venv-build\Scripts\python.exe -m pip install pytest==9.1.1
.\.venv-build\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_rutas_empaquetado.py
```

pytest no forma parte del lock. Si lo instala en `.venv-build`, `verificar_lock.py` lo detectaría como paquete adicional, pero no pasa nada: `build_exe.ps1` recrea el entorno desde cero en cada compilación.

**Suites que no se pueden ejecutar desde un clon limpio:**

- Las de interfaz de las fases 4I-G, 4I-J, 4I-P y 4I-P2 (`test_fase_4i_*.py`) importan utilidades de pruebas anteriores. Esas utilidades leen *fixtures* sintéticas de `docs/` al importarse: `docs/fase_4a_excel_formulas_simples/FIXTURE_DATOS.json` y `docs/fase_4d_slider/fixtures/*`. Esas fixtures no se publican, por su tamaño (unos 37 MB) y porque son volcados de sesiones de desarrollo. Sin ellas, pytest se detiene al recolectar.
- Otras pruebas históricas necesitan evidencias de fases de desarrollo o un anexo DANE real.

Estas limitaciones afectan a las pruebas, no a la compilación ni al producto.

## 6. Errores típicos

| Síntoma | Causa y solución |
|---|---|
| `Se requiere Python 3.12` | `python` apunta a otra versión. Instale Python 3.12 x64 o ponga su ruta primero en el PATH |
| `No se pudo ejecutar scripts…` / «la ejecución de scripts está deshabilitada» | Use `powershell -ExecutionPolicy Bypass -File …`, como en el paso 2 |
| `Fallo la instalacion de requirements-lock.txt` | Sin acceso a PyPI, proxy, o Python que no es 3.12 x64 |
| `El entorno de compilacion no reproduce requirements-lock.txt` | Un paquete difiere o sobra (por ejemplo, pytest instalado a mano). Vuelva a ejecutar el script: recrea `.venv-build` |
| `La autocomprobacion fallo` | Revise `release\autocomprobacion.txt` y `%LOCALAPPDATA%\SAVIP\logs`. Para depurar con consola: `.\scripts\build_exe.ps1 -Diagnostico` (genera `SAVIP-debug.exe`) |
| Mensajes `NativeCommandError` con `INFO:` de PyInstaller | No son errores: PyInstaller escribe sus mensajes por stderr. Lo que cuenta es el código de salida |
| SmartScreen «editor desconocido» al abrir el EXE | El EXE no está firmado. «Más información › Ejecutar de todas formas» si lo compiló usted |
| Ruta del clon muy larga | Clone en una ruta corta, por ejemplo `C:\src\SAVIP` |

## 7. GitHub Actions

`.github/workflows/build-windows.yml` se ejecuta solo a mano (*Actions › build-windows › Run workflow*):

- Usa `windows-latest` x64, Python 3.12.10 y `scripts\build_portatil.ps1`.
- Publica como artefacto el ZIP, su `.sha256`, `verificacion_lock.json` y `autocomprobacion.txt`.
- No hace commits, push ni releases, y no usa secretos.

El *runner* puede cambiar de imagen de Windows. Las versiones de Python y de todas las dependencias quedan fijadas.

## 8. Limpieza

```powershell
.\scripts\clean_build.ps1 -TodoIncluidoRelease
Remove-Item .venv-build -Recurse -Force
```
