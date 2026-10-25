# 00 · Estado remoto y reproducibilidad de SAVIP 1.1.2 desde GitHub

**Pregunta:** ¿se puede reconstruir el ejecutable y recuperar el funcionamiento de SAVIP 1.1.2 usando **solo** lo publicado en GitHub y las dependencias documentadas?

**Respuesta: sí.** Desde un clon nuevo de `estebanojeda0615/SAVIP` en el commit `6672529`, con el script oficial y el lock:
- el build terminó con código 0;
- la autocomprobación del ejecutable aislado dio 7/7;
- la ventana real abrió y cerró bien;
- el paquete es funcionalmente idéntico al del Release `v1.1.2-rc.1`: **1618/1618 archivos; solo 3 difieren** y por marcas de compilación.

Fecha de la verificación: 2026-10-25, hora de Colombia. Equipo: Windows 11 Home 10.0.26200, x64; Python 3.12.10.

## 1. Estado remoto verificado (antes de la Fase 0)

| Referencia | Valor |
|---|---|
| Repositorio | https://github.com/estebanojeda0615/SAVIP |
| `main` (estable 1.1.1) | `dfdb3e046126093e23b045147f789fbc52961a73` |
| `develop/v1.1.2` | `66725293f304426ae6edf144b8f4dadbcbeefe10` |
| Tag `v1.1.2-rc.1` (anotado) | objeto `08f364b0571726be7fb7c2432b8a316068ea7204` → `66725293…` |
| Release `v1.1.2-rc.1` | id 423554929, **prerelease = true**, draft = false |
| Asset ZIP | `SAVIP_1.1.2_Portatil_Windows_x64.zip`, 131 810 202 bytes, digest `sha256:cee5897f82753d5ca1b6650023da81384bc1bfb50b5a5468ddbb26e5e7a94600` |
| Asset `.sha256` | 104 bytes, con el mismo valor |

## 2. A1 · Inventario del contenido publicado (commit `6672529`)

### 2.1 Qué contiene

**253 archivos rastreados:**

| Carpeta o archivo | Archivos |
|---|---|
| `app_icociv/` | 112 |
| `tests/` | 111 |
| `pruebas/` (scripts manuales) | 9 |
| `scripts/` | 7 |
| `packaging/` | 4 |
| `.github/workflows/build-windows.yml` | 1 |
| Raíz: `aplicacion.py`, `VERSION` (= `1.1.2`), `requirements*.txt` (3), `README.md`, `COMPILACION_WINDOWS.md`, `.gitignore`, `.gitattributes` | 9 |

### 2.2 Comprobaciones

| Comprobación | Resultado |
|---|---|
| Importaciones dinámicas | Una sola: `app_icociv/config/dependencias.py:67` (`importlib.import_module` sobre la lista declarada de dependencias). Los `hiddenimports` del spec cubren el backend Qt de matplotlib, `pyxlsb`, `openpyxl`, `sklearn.linear_model` (+4 internos), `docx`, `reportlab` (+2) y `statsmodels.stats.diagnostic`. |
| Recursos de datos | `app_icociv/datos/iccp_historico.json`, `interfaz/tema/plantilla.qss`, `interfaz/recursos/` (22 archivos) y `VERSION`. Todos en el repositorio y declarados en `datas` del spec con rutas relativas a la raíz. |
| Rutas locales en spec, scripts y workflow | Ninguna. Se buscaron rutas absolutas, `Desktop`, `Users`, el nombre de usuario y `PYTHONPATH`, sin resultados. |
| Fuentes del PDF | Las incluye `reportlab` (Vera). No dependen de fuentes del sistema. |
| Secretos | Ninguno: no hay tokens, contraseñas ni `.env`. El README solo contiene el nombre del autor. |
| Datos rastreados | Solo `iccp_historico.json` (público, ICCP histórico) y los CSV sintéticos de `tests/fixtures/horizonte_dinamico/`. Ningún anexo del DANE ni sesiones. |
| Documentación frente a scripts | **Divergencia conocida (AS-017).** `scripts/build_portatil.ps1` es el camino oficial y empaqueta con `empaquetar_portatil.py`. Pero `build_exe.ps1:248` recomienda «Siguiente paso: `package_release.ps1`», y ese mensaje aparece también en el log de este build. No impide reconstruir. |
| CI publicado | `build-windows.yml`: solo `workflow_dispatch`; ejecuta `build_portatil.ps1` en `windows-latest` con Python 3.12.10. |

### 2.3 Árbol local de desarrollo

`SAVIP_V1_1_2_DESARROLLO` solo se inspeccionó, sin escribir:
- HEAD `dfdb3e0`, rama `develop/v1.1.2-skeleton-dialogos`;
- 348 entradas en `git status`;
- `VERSION` 1.1.1.

No se usó como fuente: todo sale del clon de GitHub.

## 3. A2 · Reconstrucción limpia

### 3.1 Procedimiento (reproducible)

```bash
git clone https://github.com/estebanojeda0615/SAVIP.git SAVIP_V112_FASE0_REPRODUCIBILIDAD
```

```bash
git -C SAVIP_V112_FASE0_REPRODUCIBILIDAD checkout -b maintenance/v1.1.2-fase0-reproducibilidad origin/develop/v1.1.2
```

```bash
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_portatil.ps1
```

### 3.2 Resultado del build

Log: `C:\Pruebas SAVIP\Fase0\build_portatil.log`. Hay copia UTF-8 en `build_portatil_utf8.log`.

| Paso | Resultado |
|---|---|
| Intérprete | Python 3.12.10 en `.venv-build` nuevo |
| `requirements-lock.txt` | **32/32** versiones exactas (`verificacion_lock.json`) |
| Pruebas previas del script | OK: `test_imports_modulos`, `test_empalme_iccp_icociv`, `test_auditoria_formulas_estadisticas` |
| PyInstaller con `packaging/SAVIP.spec` | OK. Se excluyó material de pruebas de terceros (83 archivos); quedan 1239 datos empaquetados |
| Verificaciones del script | Ejecutable y recursos (`iccp_historico.json`, `plantilla.qss`, `VERSION`) presentes |
| Autocomprobación en `dist` | **«SAVIP 1.1.2» 7/7** |
| ZIP | `SAVIP_1.1.2_Portatil_Windows_x64.zip`, **131 811 208 bytes**, 1618 entradas, CRC correcto, raíz única `SAVIP_1.1.2_Portatil/` |
| SHA-256 del ZIP reconstruido | `767f0dee34f11bef178d9bcd2ebc1ea28130debf0223df2db129f9a52bb1a0c2` |
| Autocomprobación del ZIP extraído (por el script) | 7/7 |
| Código de salida y duración | **0 en 415 s** |

**Nota.** El script oficial escribe `.venv-build/`, `build/`, `dist/` y `release/` dentro del clon, por diseño. Las cuatro carpetas están en `.gitignore` y no entran en ningún commit. El ZIP se copió fuera del clon para todas las pruebas.

### 3.3 Ejecutable aislado, fuera del clon

**Ubicación:** el ZIP se copió a `C:\Pruebas SAVIP\Fase0\reconstruccion\zip_reconstruido\` y se extrajo en `C:\Pruebas SAVIP\Fase0\reconstruccion\Portatil reconstruido\` (ruta con espacios).

**Entorno de ejecución:**
- sin variables `PYTHON*`, `VIRTUAL_ENV`, `CONDA*` ni `QT_*`;
- `PATH = C:\Windows\System32;C:\Windows`;
- directorio de trabajo `C:\`.

| Prueba | Resultado |
|---|---|
| `SAVIP.exe --autocomprobacion` | **Código 0, 7/7**: statsmodels 0.14.6 y Ljung-Box, recursos internos, ICCP (14 grupos), empalme, proyección (Lineal OLS), exportables DOCX/PDF/CSV, escritura fuera del bundle |
| Ventana real | Título «SAVIP v1.1.2 — Sistema de Análisis de Variaciones de Precios»; **responde 10/10** sondeos (`IsHungAppWindow`); cierre con `WM_CLOSE` y **código 0** |
| Mismo protocolo con el EXE del Release | 7/7 |

**Limitación.** Este equipo tiene Python instalado. El aislamiento es por variables de entorno y `PATH`, no por una máquina sin Python.

### 3.4 Comparación funcional con el Release `v1.1.2-rc.1`

El ZIP del Release se descargó de GitHub: **131 810 202 bytes**, SHA-256 `cee5897f…a94600`, **idéntico al publicado**. Ambos ZIP se extrajeron y se compararon archivo por archivo (`comparar_con_release.py`).

| Aspecto | Reconstruido | Release | Igual |
|---|---|---|---|
| Archivos | 1618 | 1618 | Sí: ninguno sobra ni falta |
| `_internal/VERSION` | `1.1.2` | `1.1.2` | Sí, byte a byte |
| `iccp_historico.json`, `plantilla.qss` | — | — | Sí, byte a byte |
| Recursos de interfaz | 22 | 22 | Sí, todos byte a byte |
| Archivos con contenido distinto | 3 | | Ver abajo |

Los 3 archivos que difieren, con el mismo tamaño:

1. **`SAVIP.exe`** (22 378 099 bytes). Solo **6 bytes** distintos, en los offsets 264–265 y 344–345 (marca de tiempo y suma de comprobación de la cabecera PE) y 273 076–273 077 (marca del archivo PKG). Son marcas de compilación de PyInstaller.
2. **`_internal/base_library.zip`** (1 333 717 bytes): marcas de tiempo internas de los `.pyc`.
3. **`_internal/numpy-2.4.2.dist-info/RECORD`**. Difieren los hashes de `f2py.exe` y `numpy-config.exe`. Son lanzadores que pip genera con la ruta del entorno virtual, que cambia entre equipos. No se ejecutan desde SAVIP.

**Conclusión.** La reconstrucción reproduce el paquete publicado salvo marcas de compilación. Por eso el SHA-256 del ZIP no coincide (`767f0dee…` frente a `cee5897f…`): es lo esperado sin un build bit a bit determinista, y el prompt pide comparación funcional, no de SHA. El código fuente, las dependencias, los recursos y la configuración son los mismos.

## 4. Pruebas desde fuente frente a pruebas del EXE aislado

| Tipo | Qué ejercita | Dónde |
|---|---|---|
| Desde fuente | El código Python de `app_icociv` con el entorno del lock (`venv-test`, mismas 32 versiones + `requirements-test.txt`) | Perfiles de `scripts/pruebas_fase0.py` y GitHub Actions (ver 01 y 04) |
| EXE aislado | El binario congelado con su `_internal/` | Autocomprobación 7/7 y ventana real (§3.3); arnés congelado del release (191/191, `Desktop\SAVIP_V112_RELEASE_EVIDENCIA`, no repetido en esta fase) |

Los Golden Masters se ejecutan desde fuente. No hay un arnés que los ejecute dentro del EXE: queda como limitación (ver 05).

## 5. Evidencias locales (no publicadas, en `C:\Pruebas SAVIP\Fase0\`)

- `build_portatil.log` y `build_portatil_utf8.log`;
- `reconstruccion\comparacion_release.txt` y `.json`;
- `reconstruccion\aislado_autocomprobacion.txt`, `aislado_ventana.txt` y `release_autocomprobacion.txt`;
- `reconstruccion\zip_reconstruido\` (ZIP y `.sha256`) y `zip_release_github\` (ZIP descargado del Release);
- scripts usados: `reconstruccion\comparar_con_release.py` y `reconstruccion\ejecutar_aislado.py`.
