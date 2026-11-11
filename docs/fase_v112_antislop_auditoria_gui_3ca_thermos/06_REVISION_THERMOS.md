# 06 · Revisión Thermos

| Dato | Valor |
|---|---|
| Plugin | `thermos@thermos-claude-plugin` 1.1.0, ya instalado; no se reinstaló. Claude Code 2.1.238, sin `--effort` |
| Invocación | Skill `thermos:thermos`, con los dos agentes en paralelo y en segundo plano: `thermos:thermo-nuclear-reviewer` y `thermos:thermo-nuclear-code-quality-reviewer` |
| Entrada | Diff exacto contra **`863de0c`**, sin docs, guardado en un `.patch` fuera del repositorio. Además, los archivos completos, el borrador de 00/01/03/04 y las evidencias. Contexto: producción intocable, prohibiciones de debilitar aserciones, mecanismo G2 y clasificación G3-A |
| Modo | Solo lectura. Los agentes ejecutaron `pytest` del archivo y sus propias sondas pasivas, fuera del repositorio |

> **Thermos solo revisa diffs.** No sustituye a la reproducción, las trazas, los mutantes ni el perfil esencial (02-05).

## Pasadas

| Pasada | SHA revisados | Corrección | Calidad |
|---|---|---|---|
| 1.ª | `863de0c...ffb77702` | **Sin hallazgos altos ni medios.** Con su propia sonda confirmó: no hay resize dentro de la ventana del spy; ningún otro spy está expuesto (`nav_spy` ve vencer el temporizador a 1366 px, pero `_adaptar_ancho` no emite `seleccion_cambiada`); la espera por condición es correcta (`isActive()` sigue en True hasta despachar el timeout) y no es un sleep encubierto; sigue siendo G3-A | **«APROBADO con observaciones»**. M1-M5 y B1-B4 |
| 2.ª | `863de0c...06feeb48` (delta `ffb7770..06feeb4`) | **Sin hallazgos de ninguna prioridad.** El delta es un renombrado sin cambio de comportamiento; no quedan referencias antiguas; 4/4 tests pasan | **«APROBADO con observaciones menores»**. O1-O4, sin bloqueantes |

## Hallazgos y estado

| Id | Severidad | Hallazgo | Nuevo / preexistente | Estado |
|---|---|---|---|---|
| M1 (calidad) | Medio | 04 no explicaba por qué no se esperaba en `settle()`; carrera latente en `test_b`/`registrar_geometria` | Nuevo (docs) / preexistente (latente) | **Resuelto** en 04 §3. La latente queda registrada fuera de alcance |
| M2 (calidad) | Medio | La cuarentena de `scripts/pruebas_fase0.py:76-78` tiene la misma causa | Preexistente | **Registrado** en 04 §3, con el criterio para promover el helper |
| M3 (calidad) | Medio | Los scripts de campaña tenían rutas fijas | Nuevo (evidencia) | **Resuelto**: variables `PYTHON_3CA`, `SALIDA_3CA` y `SONDA_3CA` |
| M4 (calidad) | Medio | Faltaba el control determinista positivo del parche | Nuevo (evidencia) | **Resuelto**: con bloqueo de 100 ms y la espera, `spy=1` (2/2) |
| M5 (calidad) | Medio | Referencias a documentos todavía inexistentes | Nuevo (borrador) | **Resuelto** con el commit documental completo |
| B1/B2 (calidad) | Bajo | Nombre del helper y parámetro sin uso | Nuevo | **Resuelto** en `06feeb4`: `esperar_ajuste_de_ancho(v)`, límite fijo de 1 s |
| B3 (calidad) | Bajo | Matices del acoplamiento: falta de `qWaitFor`, conducir frente a observar, segundo ajuste diferido | Nuevo (docs) | **Resuelto** en 04 §4 |
| B4 (calidad) | Bajo | Ningún mutante prueba la rama de fallo del helper | Nuevo | No se hace (opcional) |
| Info (corrección) | Info | Acoplamiento al atributo privado `_temporizador_ancho` | Nuevo, aceptable | Documentado (04 §4) |
| Info (corrección) | Info | Carrera de producción teórica (clic menos de 60 ms después de un resize que cruza 1180 px) | Preexistente | **Observación para el propietario** (04 §2); fuera de alcance |
| O1 (calidad, 2.ª) | Menor | Redacción de la alternativa «esperar tras `resize()`» | Nuevo (docs) | **Resuelto** en 04 §3 |
| O2/O3 (calidad, 2.ª) | Menor | `AQUI` sin uso en `campana.sh`; las variables de entorno relativas no se normalizan | Nuevo (evidencia) | **Registrado y sin cambio**: los scripts versionados son exactamente los que se ejecutaron (uno estaba corriendo durante la revisión). **Las variables deben ser rutas absolutas** |
| O4 (calidad, 2.ª) | Menor | Varios bucles de espera por condición escritos a mano en `tests/` | Preexistente | Propuesta futura de un `esperar_hasta` común; fuera de alcance |
| — | — | P0-C / IC95 | No aparece | Fuera de alcance. P0-C sigue cancelado |

**Criterio:** no queda abierto ningún hallazgo crítico, alto ni medio del propio diff. Las dos pasadas cubren el último commit de código, `06feeb4`.
