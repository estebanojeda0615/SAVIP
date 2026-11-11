# 07 · Informe de cierre: auditoría de la intermitencia GUI 3c_a

## 1. Dictamen: **APTO** (diagnóstico y parche de prueba probado)

- Se demostró **G3-A**: el fallo es de sincronización del test, no de producción.
- La corrección afecta **solo a la prueba**: mismo id, mismas aserciones y mismas expectativas.
- Los mutantes adversariales se siguen detectando.
- Las campañas posteriores no tienen fallos: 0 de 30 con carga, 0 de 30 sin carga y 0 de 40 en el archivo completo.
- Esencial 809/809 con el conjunto de ids idéntico; golden 29/29; AS-001 16/16; huella idéntica.
- CI del commit de código con 0 fallos en la 1.ª ejecución.
- Thermos, con dos agentes, sin hallazgos críticos, altos ni medios abiertos.

La conclusión se limita a «**intermitencia no observada en las campañas y mecanismo neutralizado**»; **no** es una demostración universal de que la prueba nunca fallará.

## 2. Causa observada de `QSignalSpy.count() == 2`

- La **2.ª emisión** de `contraccion_cambiada` no la causa el clic.
- La causa `VentanaPrincipal._adaptar_ancho`: es el **ajuste de ancho diferido** que un `QTimer` de un disparo de **60 ms** aplica tras cada `resizeEvent` (`ventana_principal.py:308-311, 2993-3030`).
- El test hace `v.resize(1100, 700)`. Si el temporizador vence **dentro de la ventana del spy** del toggle, justo después del clic que expande la navegación, `_adaptar_ancho` entra en modo compacto (por debajo de 1180 px) y **vuelve a contraerla**. Se producen así una segunda emisión (`True`) y el estado final contraído.
- El clic produce **un solo** `clicked` y **una sola** emisión (`False`).

**Pruebas que lo demuestran**
- **Reproducción natural en Windows con la prueba intacta:**
  - 5 de 30 ejecuciones con carga de CPU;
  - 2 de 40 ejecuciones del archivo completo sin carga.
- **Trazas pasivas de los 5 fallos naturales:** idénticas, con `clicked=1` y emisiones `[(False, clic), (True, _adaptar_ancho)]`.
- **Control sintético determinista:** con bloqueo da `spy=2`, y con la espera del parche da `spy=1`.
- **Escenarios:** A, B y D falsados; **C confirmado** (03).

Clasificación: **G3-A** (sincronización del test). Por qué no es G3-B, en 04 §2.

## 3. Archivos y commits

| Commit | Contenido |
|---|---|
| `72675f5` | +1 rama en el filtro de `push` del workflow y +1 excepción en `.gitignore` |
| `ffb77702` | `tests/test_interaccion_fase_3c_a.py`: espera **por condición** a que no haya ajuste de ancho pendiente, justo antes del spy del toggle (+13 líneas) |
| `06feeb48` | Renombrado del helper a `esperar_ajuste_de_ancho(v)` con límite fijo de 1 s (Thermos). **Último commit de código** |
| HEAD documental | Esta carpeta |

**Cambio total de código:** un archivo de test, +13 líneas. Ninguna aserción, expectativa, id ni perfil cambia. No hay `skip`, `xfail`, reintentos ni `qWait` arbitrarios. **Producción: diff vacío.**

**Reversión:** `git revert 06feeb4 ffb7770 72675f5`.

## 4. Antes y después

| Comprobación | Rama base `863de0c` | Rama auditada | Conclusión |
|---|---|---|---|
| `test_a`, 1.ª ejecución aislada, sin carga | 0 FAIL de 30 | 0 FAIL de 30 | Sin carga, en este equipo, no se observa en el nodo aislado |
| `test_a`, 1.ª ejecución aislada, con carga (trazas) | **5 FAIL de 30** | **0 FAIL de 30** | Los 5 fallos coinciden con el mecanismo. Con el parche, 540 ventanas sin vencimiento del temporizador dentro |
| Archivo `test_interaccion_fase_3c_a.py` completo | **2 FAIL de 40** | **0 FAIL de 40** | Mismo fallo que en CI |
| Doble emisión mutante | FAIL (la prueba lo detecta) | FAIL (lo detecta) | Contrato intacto |
| Ausencia de emisión mutante | FAIL | FAIL | Contrato intacto |
| Estado final erróneo y navegación rota | FAIL | FAIL | Contrato intacto |
| Botón inoperable | FAIL | FAIL | Contrato intacto |
| Perfil esencial | 809 | **809/809**, conjunto idéntico | Sin pérdidas |
| Golden / AS-001 | 29 / 16 | **29 / 16** | Sin cambios |
| Huella / producción | `d6be699b…` | **`d6be699b…`**, diff de producción vacío | Sin cambios |
| CI, 1.ª ejecución / reintento | 3 FAIL de 6 en la 1.ª ejecución (01) | Run 42952282245: success, 809/809, **0 fallos en la 1.ª ejecución**, sin reintentos; `test_a` PASS | Primer CI con el parche sin fallos. Es una sola ejecución: no se extrapola |
| Thermos | N/A | Dos agentes, dos pasadas | Sin hallazgos críticos, altos ni medios abiertos |

**Limitación honesta:** que no aparezcan fallos en las campañas del parche no demuestra que nunca vaya a fallar. Lo que queda demostrado es que el mecanismo observado (vencimiento del temporizador dentro de la ventana del spy) **no puede ocurrir** con la espera previa, porque el temporizador está inactivo al crear el spy. Esto lo verifican las trazas y el control determinista.

## 5. Equivalencia con SAVIP

- **Rama anterior:** el código de producción es idéntico (mismo árbol `app_icociv`). Huella **ejecutada**: 0 diferencias, mismo SHA.
- **V1.1.2 original:** el oráculo de 66 escenarios **no se repitió**. Se reutiliza la evidencia de 2D-2 (65/66, con AS-001 como única diferencia), que sigue siendo válida porque el código de producción, las dependencias y los fixtures no cambian (05 §3).
- **Interfaz:** `app_icociv/interfaz` es idéntica a la de la V1.1.2 original. El ajuste diferido de ancho ya estaba en la versión empaquetada.

## 6. Thermos

Dos pasadas reales, con `thermo-nuclear-reviewer` y `thermo-nuclear-code-quality-reviewer`:
- **Corrección:** sin hallazgos altos ni medios en la 1.ª pasada y sin hallazgos en la 2.ª.
- **Calidad:** «APROBADO con observaciones» en la 1.ª pasada, con 5 medios de documentación y evidencia ya resueltos; «APROBADO con observaciones menores» en la 2.ª.

Detalle en 06.

**Reservas registradas:**
- el acoplamiento del test al atributo privado `_temporizador_ancho` (no hay alternativa pública);
- los scripts de evidencia requieren rutas absolutas.

## 7. Pendientes y decisiones del propietario

1. **Observación de producción (decidir en una fase aparte):** una expansión manual de la navegación dentro de los ~60 ms posteriores a un redimensionado que cruza 1180 px se revierte por el ajuste diferido. Aparenta ser de diseño (debounce y modo compacto) y no se califica aquí. No es parte de Anti-Slop.
2. **Misma causa en otra prueba:** `tests/test_proyecciones_redisenio_visual.py::test_layout_adaptable_y_temas_sin_cambiar_entrada` sigue en cuarentena en el perfil gui (`scripts/pruebas_fase0.py:76-78`). El helper de esta fase sería su arreglo natural en una fase futura autorizada.
3. **Carrera latente sin fallos observados:** `test_b` y `registrar_geometria` miden a 1100 px antes de que venza el ajuste. Fuera de alcance.
4. **Bucles de espera por condición repetidos en `tests/`:** posible helper común futuro.
5. **No se inició** 2D-1, 2D-3, 2D-6, AS-004, AS-007, P0-C ni ningún otro lote.

## 8. Enlaces

- Rama: https://github.com/estebanojeda0615/SAVIP/tree/maintenance/v1.1.2-auditoria-gui-3ca-thermos
- Comparación: https://github.com/estebanojeda0615/SAVIP/compare/863de0c1745af0a050a1026818c0f7b8e8a0e3c5...maintenance/v1.1.2-auditoria-gui-3ca-thermos
- CI del commit de código: https://github.com/estebanojeda0615/SAVIP/actions/runs/42952282245 (success, 0 fallos en la 1.ª ejecución). CI del HEAD documental: ver el mensaje de entrega
- No se modificaron `main`, `develop/v1.1.2`, el tag ni la release `v1.1.2-rc.1`, ni la rama del lote 2D-2 (`863de0c`). No hubo merge, PR, tag, release, EXE ni ZIP.
