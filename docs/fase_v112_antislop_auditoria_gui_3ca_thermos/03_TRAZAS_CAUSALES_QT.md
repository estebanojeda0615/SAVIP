# 03 · Trazas causales Qt

## 1. Instrumentos (todos externos al código de producción y reversibles)

| Instrumento | Qué hace | Por qué no altera el orden de eventos |
|---|---|---|
| `evidencia/scripts/sonda/plugin_traza_3ca.py` | Plugin pytest **pasivo** sobre la prueba REAL. Envuelve `VentanaPrincipal.__init__` para conectar, **después** de los slots de producción, registros de `contraccion_cambiada` (con la pila de llamadas que la originó), `boton_contraer.clicked` y `_temporizador_ancho.timeout` (ancho, modo compacto y contracción tras el ajuste). Instala un filtro de eventos que anota cada `Resize` y devuelve `False`, sin consumirlo. Registra el momento de creación de cada `QSignalSpy` del test | Los slots de producción se conectaron antes y se ejecutan primero. El filtro no consume eventos. El spy real se sigue creando igual |
| `evidencia/scripts/sonda/sonda_3ca.py` | Sonda que repite la secuencia del test con los mismos registros y anota, al crear el spy del toggle, si el temporizador de ancho está activo y cuánto le queda | Ídem |
| `evidencia/scripts/sonda/control_sintetico_3ca.py` | **Control sintético** que demuestra el mecanismo de forma determinista. No se presenta como reproducción del fallo real | — |
| `evidencia/scripts/sonda/analizar_traza_3ca.py` | Para cada ventana del spy del toggle (desde su creación hasta el siguiente paso de preparación del test), cuenta los `clicked`, las emisiones con su origen (`clic` = `alternar_contraccion`, `temporizador` = `_adaptar_ancho`, `test` = llamada directa del test) y los vencimientos del temporizador dentro de la ventana | — |

## 2. Cadena de emisión (código, sin cambios)

- `navegacion.py:135`: `boton_contraer.clicked` está conectado a `alternar_contraccion`. Es una sola conexión en `__init__`.
- `navegacion.py:230-275`: `alternar_contraccion` llama a `establecer_contraccion(not self._contraida)`, que emite `contraccion_cambiada` **una vez** por llamada.
- `ventana_principal.py:308-311`: `_temporizador_ancho`, un `QTimer` de un disparo de **60 ms**, conectado a `_adaptar_ancho`.
- `ventana_principal.py:2993-3001`: cada `resizeEvent` (re)arranca el temporizador, para hacer un solo ajuste tras la ráfaga de redimensionado.
- `ventana_principal.py:3003-3030`: `_adaptar_ancho`:
  - **entra en modo compacto** si el ancho es menor de 1180 y, si la navegación no estaba contraída, la contrae con `establecer_contraccion(True)`, que es **otra emisión**;
  - sale del modo compacto si el ancho es mayor de 1260 y la expande, solo si la había contraído él (`_navegacion_auto`).

`establecer_contraccion` solo la llaman `alternar_contraccion`, `_adaptar_ancho` y el propio test (búsqueda en todo `app_icociv`).

## 3. Resultados

### 3.1 Prueba real, sin carga (sonda; ventana de 18 toggles por ejecución)

En la secuencia real, el temporizador de ancho **sigue activo** al crear el spy del toggle tras cambiar a 1366 y a 1920 px, con 8-13 ms restantes. Vence dentro o justo después de la ventana, pero a esos anchos no cruza el umbral y no emite nada. A 1100 px vence antes del toggle (unos 62 ms tras el resize, aún en la preparación), así que en este equipo y sin carga la prueba pasa (30/30, ver 02).

### 3.2 Prueba real con carga de CPU: **reproducción natural del fallo** (campaña G2, ver 02)

Los 5 fallos tienen exactamente la misma firma (`evidencia/analisis_G2_base_carga.txt`):

| Intento | Spy creado tras el resize | `clicked` en la ventana | Emisiones en la ventana (argumento, origen) | Temporizador dentro (ancho, ms tras el resize, compacto, contraída) |
|---|---|---|---|---|
| 10 | 62 ms | **1** | (False, **clic**), (True, **temporizador**) | (1100, 78, True, True) |
| 11 | 63 ms | **1** | (False, clic), (True, temporizador) | (1100, 79, True, True) |
| 19 | 47 ms | **1** | (False, clic), (True, temporizador) | (1100, 78, True, True) |
| 20 | 47 ms | **1** | (False, clic), (True, temporizador) | (1100, 63, True, True) |
| 28 | 63 ms | **1** | (False, clic), (True, temporizador) | (1100, 78, True, True) |

En las ejecuciones que pasan también hay vencimientos dentro de la ventana, pero a 1366 o 1920 px, sin emisión. **En ninguna ejecución aparece un 2.º `clicked`, una emisión de origen distinto o un `resize` dentro de la ventana.**

### 3.3 Control sintético (determinista; no es una reproducción, `evidencia/control_sintetico.txt`)

| Caso | clicked | spy.count | Argumentos | Contraída al final |
|---|---|---|---|---|
| Sin espera | 1 | 1 | [False] | False |
| `qWait(100)` **antes** de crear el spy | 1 | 1 | [False] | False |
| Bloqueo de 100 ms sin procesar eventos, antes de crear el spy | 1 | **2** | [False], **[True]** | **True** |
| Repetición | 1 | 2 | [False], [True] | True |

## 4. Escenarios del prompt

| Escenario | Veredicto | Evidencia |
|---|---|---|
| A. Dos `clicked` reales por un `mouseClick` | **Falsado** | En los 5 fallos naturales, `clicked` = 1 dentro de la ventana |
| B. Un `clicked` y dos llamadas a `establecer_contraccion` por reentrada, callback o conexión adicional | **Falsado** | La 2.ª emisión tiene como origen `_adaptar_ancho`, no `alternar_contraccion`. Hay una sola conexión de `clicked` (`navegacion.py:135`) |
| **C. Un `clicked` y una emisión independiente (evento pendiente o reconfiguración de tamaño)** | **Confirmado** | La 2.ª emisión la produce el ajuste diferido de **un redimensionado anterior** (`resize` a 1100 px), cuyo `QTimer` de 60 ms vence dentro de la ventana del spy y contrae la navegación que el clic acababa de expandir |
| D. Artefacto de aislamiento, instrumentación o vida del spy | **Falsado** | El fallo aparece igual sin el plugin (CI, y la prueba real no instrumentada falla con la misma aserción), y el plugin no altera el orden de slots |
| E. Otro mecanismo | No observado | — |

## 5. Por qué la carga de CPU lo hace visible

La prueba crea el spy del toggle entre 47 y 94 ms después del `resize`, según la ejecución. El temporizador de 60 ms se despacha en el primer punto en que el test procesa eventos tras su vencimiento.
- **Si ese punto cae antes de crear el spy**, el ajuste no afecta a la aserción.
- **Si cae dentro de la ventana del spy**, a 1100 px, aparece la 2.ª emisión.

La carga de CPU, igual que la variabilidad de un runner de CI, desplaza estos tiempos en milisegundos. La causa es la **carrera** entre el temporizador de ancho y la ventana del spy, no la carga en sí.
