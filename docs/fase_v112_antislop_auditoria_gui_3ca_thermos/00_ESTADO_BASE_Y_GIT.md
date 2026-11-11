# 00 · Estado base y Git

## 1. Base y aislamiento

| Dato | Valor |
|---|---|
| Base | `863de0c1745af0a050a1026818c0f7b8e8a0e3c5` (rama `maintenance/v1.1.2-fase2d-lote2-equivalencia-original-thermos`, 08-11-2026), verificada con `git ls-remote` antes de empezar |
| Último commit de código de la base | `49106f95bacd96699c5233101490586738f5f32d`. `git diff 49106f9 863de0c` fuera de `docs/` está vacío |
| Rama nueva | `maintenance/v1.1.2-auditoria-gui-3ca-thermos`, creada exactamente desde `863de0c`. No existía en remoto |
| Clon | `C:\Users\Esteban\Desktop\SAVIP_V112_AUDITORIA_3CA`, clon nuevo y aislado. `git status --porcelain` vacío al empezar |
| Copias de prueba | `C:\Pruebas SAVIP\3CA\base` (863de0c) y `C:\Pruebas SAVIP\3CA\parche` (con el parche del test), fuera del repositorio |
| Otras carpetas | No se tocaron el repositorio de desarrollo, la carpeta `SAVIP_V112_AUDITORIA_ANTISLOP` ni los clones de fases anteriores |
| Referencias protegidas | `main` `dfdb3e0`, `develop/v1.1.2` `6672529`, tag `v1.1.2-rc.1` `08f364b`. Sin cambios |

## 2. Procedencia de la prueba y del código implicado

| Archivo | Último commit que lo cambió |
|---|---|
| `tests/test_interaccion_fase_3c_a.py` | `5f40295` (25-10-2026, Fase 1A, AS-007) |
| `app_icociv/interfaz/componentes/navegacion.py` | `dfdb3e0` (V1.1.1) |
| `app_icociv/interfaz/ventana_principal.py` (ajuste de ancho diferido) | `bf7745a` (24-10-2026, desarrollo de la 1.1.2) |

`git diff 6672529 863de0c -- app_icociv/interfaz` está **vacío**: la interfaz es idéntica a la de la V1.1.2 original empaquetada.

## 3. Áreas vetadas: árboles Git en la base

| Ruta | Árbol o blob en `863de0c` |
|---|---|
| `app_icociv` | `f4f0a0c752e9bb37b0e9fd2b79b4afd9c9ac906a` |
| `aplicacion.py` | `4e97d63adafdbf4e9a465cb2f1667bd99719aee1` |
| `VERSION` | `45a1b3f44523206e2b1e6a7ca0e279026c3a2b55` |
| `requirements.txt` / `requirements-test.txt` | `87e1c5af…` / `46f14103…` |
| `packaging` | `06d19ddaa4e84e4be1965a5c125508546e185943` |
| `tests/fixtures` | `a4218d636f2f507e6b346aa1dff7f02229efbc85` |
| `scripts/pruebas_fase0.py` | `de42054dacda12f0ed33f8fdd1161a7e0f399a47` |
| `tests/test_interaccion_fase_3c_a.py` (antes del parche) | `c545cd745992c4b5a283720d002e819d39633564` |

Detalle en `evidencia/arboles_vetados.txt`. En el cierre se comprueba que todos siguen idénticos (05).

## 4. Entorno

| Elemento | Local (este equipo) | CI (`fase0-pruebas.yml`) |
|---|---|---|
| SO | Windows 11, 10.0.26300, 16 núcleos lógicos | `windows-latest` |
| Python | 3.12.10 | 3.12.10 |
| PySide6 / Qt | 6.11.0 / 6.11.0 | Lock del repositorio (mismas versiones) |
| Plugin Qt | `QT_QPA_PLATFORM=offscreen` | `offscreen` |
| Fuentes | Segoe registradas por el propio test desde `C:/Windows/Fonts` | Ídem |
| QSettings | INI en una carpeta temporal del test (`tests/fixtures/salidas/fase_3c_a/temporal`) | Ídem |
| Movimiento reducido | `establecer_movimiento_reducido(True)`: el ancho de la navegación se aplica sin animación | Ídem |
| Temporizador de ancho de la ventana | `QTimer` de un disparo, **60 ms**, arrancado en cada `resizeEvent` (`ventana_principal.py:308-311, 2993-3001`) | Ídem |

## 5. Línea base de SAVIP (heredada del lote 2D-2, sin cambios de código)

- 809 ids esenciales en CI, con 0 fallos en la 1.ª ejecución en el run 42426437658.
- Golden 29/29 y AS-001 16/16.
- Huella `d6be699b700b3fa3379c743cc9d0ccbf5c185cacfa228208dbb95c2735370191`.
- Oráculo: 66/66 frente a la rama anterior y 65/66 frente a la V1.1.2 original (excepción AS-001).

Esta fase no cambia producción. Ver 05 para la verificación.
