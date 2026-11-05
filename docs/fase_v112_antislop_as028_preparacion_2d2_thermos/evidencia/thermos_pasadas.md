# Thermos: salidas de cada pasada

Las salidas están condensadas sin alterar los hallazgos. Cada agente trabajó en solo lectura sobre el `.patch` guardado fuera del repositorio y sobre los archivos completos.

## 1.ª pasada · diff `56c75a6...0929b29`

### `thermos:thermo-nuclear-reviewer` (corrección)

**Resultado:** sin hallazgos críticos, altos ni medios.

**Comprobaciones propias del agente:**
- `pytest` del script en HEAD: **21 PASS / 8 FAIL**, los mismos 8 fallos que en la base.
- `main()` llama exactamente a los 29 `def test_` del archivo.
- La lápida no contiene la cadena que vigila el test de hermeticidad, y ese test pasa.
- Tras el retiro no quedan imports huérfanos (`np`, `pd` y `_periodos` siguen en uso). El archivo sigue sin CR y sin BOM.
- Producción intacta. El par sigue definido en `servicio_proyeccion.py:3112/:3142`.
- Los cuatro tests de cobertura citados existen en `test_fase1a_selector_rectangular.py`: L91, L226, L291 y L298.
- El CI añade la rama solo en `on.push.branches`, con `permissions: contents: read`.
- `git check-ignore` confirma que la carpeta de docs no queda ignorada.

**Hallazgos:**
- **BAJO, nuevo:** la lápida (`:282`) cita «docs/…/03», un documento que aún no existe y cuyo nombre es ambiguo.
- **INFORMATIVO, preexistente:** el docstring retirado decía que ganaba `exponencial_log_lineal`, y hoy gana `drift`. Refuerza que el test pasaba por coincidencia.
- **INFORMATIVO, preexistente y fuera de alcance:** otras pruebas históricas siguen atadas al selector:
  - `test_p0d_rmse_orden_exacto.py:46-50`, con importación a nivel de módulo;
  - `test_horizonte_evidencia_reducida.py:375-389`, un gemelo del test retirado;
  - `test_cierre_metodologico.py:414,437`.

  El mensaje del commit dice «único test»; es cierto para el script, no para el repositorio.
- **INFORMATIVO:** P0-C/IC95 no aparece en el diff.

### `thermos:thermo-nuclear-code-quality-reviewer` (calidad)

**Veredicto:** «APROBADO con observaciones». No hay hallazgos críticos ni altos.

- **M1, medio, nuevo:** la lápida apunta a `…/03`, que no existe en la rama. «/03» no es una ruta.
- **M2, medio, nuevo:** la lápida vuelve a escribir en el script el nombre `seleccionar_modelo_por_rmse_oos_global`. Un grep de cierre de 2D-2 («símbolo = 0 fuera de docs») lo encontraría. Hay que referirse a la ficha C-SEL-001 sin nombrar el símbolo.
- **B1, bajo, nuevo:** cuatro líneas de lápida repiten lo que ya dicen el commit y el inventario; bastan 1-2.
- **B2, bajo, preexistente:** `main()` es un registro manual que aborta en el primer FAIL. Se deja para el saneamiento posterior del script.
- **B3, bajo, preexistente:** las listas del workflow y de `.gitignore` crecen en cada fase. Mantener el patrón es aceptable.
- **B4, observación:** el CI no ejecuta `pruebas/`. Falta guardar la ejecución posterior del script (21/8) junto a la base.
- **Sobre no migrar los 19 vigentes:** «razonable, y desde la rúbrica es la opción correcta». La propiedad vigente está cubierta «con más fuerza» en `test_fase1a…:296-322`.

### Resolución

| Hallazgo | Verificación propia | Estado |
|---|---|---|
| M1 y BAJO de corrección (referencia a «03») | Confirmado | **Resuelto en `5acb09f`**: se cita la ruta completa `…/03_CAMBIOS_Y_MIGRACIONES.md`, que entra en el commit documental |
| M2 (símbolo en la lápida) | Confirmado: era la única coincidencia en `pruebas/` | **Resuelto en `5acb09f`**: la lápida dice «selector heredado de C-SEL-001». `grep` del par en el script da 0 |
| B1 (longitud) | Confirmado | **Resuelto en `5acb09f`**: 3 líneas con el id, el commit de origen, la cobertura y el documento |
| B4 (ejecución posterior) | Confirmado | **Resuelto**: `evidencia/script_final_pytest.xml` (G4) |
| B2 y B3 | Preexistentes | Sin cambio. Se registran como deuda (07 §4) |
| «Único test» en el mensaje del commit | El mensaje habla del script, no del repositorio | Se aclara en 03. No se reescribe el historial |

## 2.ª pasada · diff `56c75a6...5acb09f` (delta: la lápida de `5acb09f`)

### `thermos:thermo-nuclear-reviewer` (corrección)

**Resultado:** sin hallazgos nuevos de ninguna severidad. Las tres correcciones de la 1.ª pasada son correctas.

**Comprobaciones del agente:**
- **Ruta completa.** El archivo existe en disco. Hasta el commit documental la referencia solo resuelve en local; es lo previsto y no lo cuenta como hallazgo.
- **Símbolos.** Ninguno de los dos símbolos del par aparece en la lápida. El nombre del test retirado no los contiene como subcadena.
- **C-SEL-001.** La ficha existe en `criterios.py:566`.
- **Longitud.** Líneas de 111, 94 y 84 columnas. El archivo base ya tenía 7 líneas de más de 120.
- **Hermeticidad.** El agente reprodujo la lógica de `test_ninguna_prueba_depende_de_reportes_generados` y las dos condiciones dan False.
- **Regresión del script más `test_fase1a_selector_rectangular.py`.** 56 PASS / 8 FAIL. El script recoge 29 tests, y los 8 fallos son exactamente los 8 históricos.
- **Ruptura intencionada.** Se pierde un control cruzado contra el selector heredado. Es el objetivo declarado de AS-028 y la regla vigente sigue cubierta por Fase 1A, que pasa.

### `thermos:thermo-nuclear-code-quality-reviewer` (calidad)

**Veredicto:** **«APROBADO»**.

- **M1:** resuelto, con una condición: que el commit con `03_CAMBIOS_Y_MIGRACIONES.md` llegue junto a `5acb09f`.
- **M2:** resuelto. `grep -cE` del par en el script da 0.
- **B1:** resuelto (3 líneas).
- **B4:** pendiente de G4.
- **B2 y B3:** preexistentes; quedan como deuda.
- Sin regresiones estructurales. El script baja a 984 líneas y `pyflakes` no da ninguna salida.
- Recuerda que el glob para el workflow y `.gitignore` es deuda antigua, ajena a este diff.

### Resolución

- **03 junto a `5acb09f`.** `03_CAMBIOS_Y_MIGRACIONES.md` va en el commit documental, que se publica justo después del código. El push del código es independiente para que el CI corra sobre el último commit de código. Ver 04 §5.
- **B4.** `evidencia/script_final_pytest.xml` queda guardado (G4).
- **Cobertura de la pasada.** Desde `5acb09f` no hay más commits de código, así que la 2.ª pasada cubre el HEAD de código.
