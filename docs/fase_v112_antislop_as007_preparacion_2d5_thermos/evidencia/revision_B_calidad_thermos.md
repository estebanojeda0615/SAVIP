# Thermos B · thermos:thermo-nuclear-code-quality-reviewer · alcance 6ac158d...febd981

Invocación: skill `thermos:thermos` (Thermos 1.1.0), con el agente `thermos:thermo-nuclear-code-quality-reviewer` en segundo plano y diff en `diff_B_codigo.patch`. Claude Code 2.1.238. Salida literal del revisor:

Veredicto: no aprobar tal cual. Copiar helpers en vez de importar r3 es correcto, pero lo copiado no es lo canónico: el nuevo archivo esencial hereda el extractor de texto incompleto de r3 cuando `tests/` ya tiene uno completo, y arrastra código muerto.

1. ALTO — C7 (PDF) solo inspecciona parte del informe; ya existe un helper completo en `tests/` (demostrado). `tests/test_as007_contratos_p0c_vigentes.py:124-139` (`_texto_informe`), usado en `:232`. La copia lee texto/titulo/nota/fuente, items/encabezados y filas. `tests/test_informes_rediseno.py:79` ya tiene `_texto_informe` que además lee pie, etiqueta, general, resultado, roles, sustitucion y destacados ("los ocho tipos de bloque de modelo.py"). Sobre el informe técnico de la prueba (n=48, h=6) la copia deja fuera 15 líneas, entre ellas `Intervalo de predicción | No se publica en esta versión`, la fórmula general y la de sustitución de `Formula` y los pies de imagen. Con el extractor canónico la prueba sigue pasando hoy. Impacto: `Formula.general`/`sustitucion` son justo los campos donde reaparecería una fórmula con σ̂ o cuantil, y C7 no mira ahí. Remedio: extraer a `tests/fixtures/informes.py` o, como mínimo, `from tests.test_informes_rediseno import _texto_informe`.

2. MEDIO — código muerto copiado: `_hojas` (`:55-75`) y `CLAVES_DECLARACION` (`:31-33`) (demostrado). Nadie los usa; en r3 sirven a `_textos_publicos`/`_fuga_de_vocabulario` (C8-C11, HG4), que no se migraron. Remedio: borrar ambos.

3. MEDIO — duplicación abierta y sin fecha de cierre; las copias ya divergen (demostrado). `_tablas_de_ventanas` (semántica de `vistos`), `_errores_recuperables` (tipo de retorno) y mensajes de aserción perdidos (C2 `:158`). Siete contratos viven dos veces y ningún documento dice cuándo se elimina la segunda copia. Remedio: borrar C1-C7 y sus helpers de r3 ahora o con un disparador explícito en el inventario ("se elimina de r3 al cerrar 2D-5"); eso también eliminaría `_multiplicador_intervalo`/`NIVEL_NOMINAL_95` (fila IMPORT_DIAG).

4. BAJO-MEDIO — `_tramo()` reconstruye un enum a partir de la prosa publicada y la rama DISPONIBLE acepta cualquier texto (demostrado). `r3:513-521`. Las aserciones `== DISPONIBLE` solo comprueban "no contiene muy limitada". Remedio: comprobar el texto directamente con una aserción positiva por tramo o, como mínimo, que la tercera rama verifique el prefijo y lance `AssertionError(texto)` si no lo reconoce. No usar las constantes está justificado (evita el ImportError de 2D-5).

5. BAJO — el nombre del archivo (`_p0c_`) no refleja que también contiene P0-E (`:236`). Renombrar, por ejemplo, a `test_as007_contratos_r3_vigentes.py`.

6. BAJO — el filtro del workflow crece una línea por fase (`.github/workflows/fase0-pruebas.yml:9-16`). Remedio: patrón `maintenance/v1.1.2-**`.

Sin hallazgos: `scripts/pruebas_fase0.py`; tamaños (264 y 757 líneas, < 1 000); `lru_cache` comparte un dict mutable, pero ninguna prueba lo muta.

Fuera de alcance (producción): `servicio_proyeccion.py:2047-2069` duplica la coerción y las fronteras entre `tramo_evidencia_oos` y `_texto_evidencia_oos` (desaparece con 2D-5); `generador_reportes.py:381-385` lee claves de traza que ya nadie produce (DECISIÓN PENDIENTE HG4/HG5).
