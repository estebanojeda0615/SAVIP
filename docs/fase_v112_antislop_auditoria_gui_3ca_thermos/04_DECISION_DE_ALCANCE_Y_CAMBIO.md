# 04 · Decisión de alcance y cambio

## 1. Clasificación: **G3-A**, defecto de sincronización del test

| Requisito de G3-A | Evidencia |
|---|---|
| Hay reproducción | Prueba real intacta con carga de CPU: **5 de 30** ejecuciones fallan con la misma aserción que en CI (02) |
| Una sonda prueba que la aplicación emite la señal correcta para la interacción | En los 5 fallos, el clic produce **un** `clicked` y **una** emisión (`False`, origen `alternar_contraccion`) (03 §3.2) |
| La aserción observa una condición ajena a esa interacción | La 2.ª emisión (`True`) la produce `_adaptar_ancho`, el ajuste diferido del **`resize` anterior**, cuyo temporizador vence dentro de la ventana del spy (03 §3.2 y §4) |

**Ficha de autorización lógica** (cita la sonda de G2):
- Traza `evidencia/analisis_G2_base_carga.txt`, intentos 10, 11, 19, 20 y 28.
- En los cinco: `clicked = 1`, `emisiones = [(False, clic), (True, temporizador)]` y `temporizador_en_ventana = [(1100, 63-79 ms, compacto=True, contraída=True)]`.
- Escenarios A, B y D falsados; C confirmado (03 §4).
- Diff de producción: vacío.

## 2. Por qué no es G3-B (y observación de producción)

G3-B exige que **una interacción legítima** emita dos señales o provoque dos cambios de estado. Lo observado es distinto:

- **El clic emite exactamente una vez.** No hay doble `clicked`, ni reentrada, ni doble conexión.
- La 2.ª emisión pertenece a **otra interacción** que hizo el test: el `v.resize(*size)` anterior. Su efecto se aplica de forma diferida por diseño. El código lo documenta como «un solo ajuste tras la ráfaga de redimensionado» (`ventana_principal.py:3001`) y como «modo compacto con histéresis» (`:3004`).
- Ese ajuste ya existe en la **V1.1.2 original empaquetada**: `app_icociv/interfaz` es idéntica a 6672529, y lo introdujo `bf7745a` en el desarrollo de la 1.1.2.

**Observación de producción, para decisión del propietario.** No se califica aquí como defecto ni como no-defecto definitivo.

- **Qué pasa:** si un usuario expande manualmente la navegación dentro de los **~60 ms** posteriores a un redimensionado que **cruza el umbral compacto**, `_adaptar_ancho` revierte esa expansión. Hay dos cambios de estado y dos emisiones en esa ventana: uno por el clic y otro por el ajuste.
- **Por qué parece de diseño:** el ajuste se aplica tras la ráfaga de redimensionado, y al entrar en modo compacto la navegación se contrae si no lo estaba.
- **Lo que no se evaluó:** si un usuario real puede encadenar en menos de 60 ms un redimensionado que cruza el umbral y un clic, y si en ese caso debería prevalecer su acción. Hace falta una decisión de producto que esta fase no puede tomar.
- **Si se quisiera cambiar:** sería una fase aparte, fuera de Anti-Slop. No se toca aquí.

## 3. Cambio: solo en `tests/test_interaccion_fase_3c_a.py`

```diff
@@ imports
+import time
@@ tras settle()
+def esperar_ajuste_de_ancho(v):
+    """Espera a que se aplique el ajuste de ancho diferido de la ventana (QTimer de un disparo tras cada resize). …"""
+    fin = time.monotonic() + 1.0
+    while v._temporizador_ancho.isActive() and time.monotonic() < fin:
+        QTest.qWait(5)
+    assert not v._temporizador_ancho.isActive(), 'el ajuste de ancho sigue pendiente'
@@ test_a, antes del spy del toggle
                         assert nav_spy.count()==1 and v.tabs_principales.currentIndex()==1
+                        esperar_ajuste_de_ancho(v)
                         toggle_spy=QSignalSpy(v.navegacion.contraccion_cambiada)
```

**Qué no cambia:**
- No cambia ninguna aserción, expectativa ni umbral. Sigue exigiendo `toggle_spy.count()==1` y `not esta_contraida()`.
- Mismo id de pytest y mismo perfil (esencial).
- No se añaden `skip`, `xfail` ni reintentos.
- No se usa un `qWait` arbitrario. La espera es **por condición**: el ajuste pendiente se ha aplicado. Tiene un límite de 1 s y una **aserción** que falla si no se cumple.
- El temporizador se despacha por su ruta real (el bucle de eventos). El test no llama a `_adaptar_ancho` ni lo sustituye.

**Por qué en ese punto:** es el único spy que observa `contraccion_cambiada`, la señal que puede emitir el ajuste de ancho. El spy de `seleccion_cambiada` no se ve afectado, porque `_adaptar_ancho` no emite esa señal.

**Alternativas descartadas:**
- **Esperar dentro de `settle()`.** `settle` también estabiliza un `VisorGraficaDialog`, que no tiene `_temporizador_ancho`, así que exigiría una rama `hasattr`. Además cambiaría la temporización de `test_b` y de `registrar_geometria` (medidas y capturas). Ninguna de las dos ha fallado y quedan fuera del alcance autorizado.
- **Esperar justo después de `v.resize()`.** En la primera iteración la ventana está oculta y el `resizeEvent` que arma el temporizador llega en el `show()` de `settle`, así que la espera pasaría antes de que el temporizador se arme. En las demás iteraciones la espera quedaría lejos del spy, separada por `settle` y por el bucle de acciones.

La sincronización va pegada al punto de observación (Thermos, ambos agentes, la considera el punto correcto y mínimo).

**Observación preexistente, fuera de alcance:** `test_b` y `registrar_geometria` miden a 1100 px unos 20 ms después del `resize`, antes de que venza el temporizador de 60 ms. Pueden medir antes o después del modo compacto según la carga. No se observó ningún fallo por ello y no se toca.

**El mismo patrón en otra prueba (preexistente):** `scripts/pruebas_fase0.py:76-78` ya saca del perfil esencial `tests/test_proyecciones_redisenio_visual.py::test_layout_adaptable_y_temas_sin_cambiar_entrada`, con la misma causa citada («resizeEvent -> _temporizador_ancho»). Esto refuerza que el patrón está en los tests y no en una interacción. Si en el futuro se arregla esa prueba, el helper debería pasar a `tests/fixtures/` en lugar de copiarse. Aquí no se toca.

## 4. Acoplamiento a un detalle interno

El parche lee `v._temporizador_ancho.isActive()`, un atributo **privado** de producción.

- **Condición pública equivalente:** ninguna. La ventana no expone si tiene un ajuste de ancho pendiente.
- **Alternativas descartadas:**
  - `qWait(60)` o un valor mayor: sería una espera arbitraria, prohibida, y no garantiza el despacho.
  - Llamar a `_adaptar_ancho()` directamente: también es privado y sustituye la ruta real del temporizador.
  - Esperar a que cambie `esta_contraida()`: no sirve, porque cuando el ajuste no cambia nada no hay nada que observar.
- **Antecedentes en el mismo archivo:** el test ya usa APIs internas, como `v._aplicar_tema` y `v._cambiar_seccion`.
- **Por qué no `QTest.qWaitFor`:** PySide6 6.11.0 no lo expone (`hasattr(QTest, 'qWaitFor')` da `False`). El bucle manual sigue el patrón de espera por condición de otros archivos de test.
- **Matiz del antecedente:** `_aplicar_tema` y `_cambiar_seccion` *conducen* el estado. Este atributo se usa para *observar* la planificación interna, que es un acoplamiento algo más fuerte.
- **Riesgo:**
  - si producción renombra o elimina `_temporizador_ancho`, el test falla con un `AttributeError` explícito, no en silencio;
  - si producción añadiera **otro** ajuste diferido conservando este atributo, el helper no lo cubriría, pero la aserción `count()==1` volvería a delatarlo.

Queda sometido a Thermos (06).

## 5. Demostración de que el contrato no se debilitó (mutaciones adversariales temporales)

Las mutaciones se aplican en memoria del proceso de prueba (`evidencia/scripts/sonda/plugin_mutantes_3ca.py`) y nunca en producción ni en el commit. Resultados en `evidencia/mutantes_resumen.tsv`.

| Mutante | Base `863de0c` | Rama auditada |
|---|---|---|
| Sin mutante | PASS | PASS |
| `doble_emision`: un clic válido emite dos veces, con el estado final correcto | **FAIL** `assert (2 == 1)` | **FAIL** `assert (2 == 1)` |
| `sin_emision`: el clic cambia el estado sin emitir | **FAIL** `assert (0 == 1)` | **FAIL** `assert (0 == 1)` |
| `estado_erroneo`: el clic deja la navegación contraída | **FAIL** `assert (1 == 1 and not True)` | **FAIL** igual |
| `navegacion_rota`: el clic de navegación no notifica | **FAIL** `assert (0 == 1)` (spy de selección) | **FAIL** igual |
| `boton_inoperable`: el botón «contraer» no responde | **FAIL** `assert (0 == 1)` | **FAIL** igual |

**Control determinista positivo del parche** (`evidencia/control_sintetico.txt`). Con el mismo bloqueo de 100 ms que provoca `spy=2` en la base, la espera del parche antes del spy da **`spy=1`, `[False]`** y la navegación queda expandida al final (2 de 2). Un `QTimer` vencido pero sin despachar sigue con `isActive()==True`, y la espera lo despacha por su ruta real.
