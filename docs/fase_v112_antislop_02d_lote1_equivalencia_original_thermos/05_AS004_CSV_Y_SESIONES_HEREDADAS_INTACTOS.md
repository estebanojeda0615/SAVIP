# 05 · AS-004: CSV reproducible y sesiones heredadas intactos

## 1. No modificación

```bash
git diff 8e5a62b 406e1dd -- app_icociv/reportes app_icociv/interfaz app_icociv/persistencia app_icociv/servicios app_icociv/exportables app_icociv/estadistica
```

está **vacío**. No cambian:
- `generador_reportes.py`, que incluye `construir_dataframe_reproducibilidad`, `_lineas_*` y `generar_reporte_html`;
- `contenido.py`, `presentacion_resultados.py` (y con él `mensaje_ui` y el encabezado), `criterios.py` (incluida `C-ALC-002`) ni la persistencia de sesiones.

En `servicio_proyeccion.py` se conservan **sin cambios** dos piezas, comprobado por AST:
- la plantilla por defecto de `_resultado_sin_proyeccion`, con las claves de valor `0`, `[]` y `"bloquear"`;
- `_estructurar_resultado_horizontes`, con su `sha256(ast.dump)` (`evidencia/ast_ausencia_y_compartidos.txt`).

## 2. Medición: sonda AS-004 con las seis definiciones realmente ausentes

**Herramienta:** `evidencia/scripts/sonda_claves_as004.py`. Es la misma sonda de AS-028, con una adaptación mínima: espía solo las definiciones que existen y registra las ausentes. Además, lee las 43 claves históricas de la fuente de la base.

**Casos:** 7 series × h ∈ {1, 12, 18, 24}, más la sesión heredada.

| Campo comparado (base `8e5a62b` frente a final `406e1dd`) | Resultado |
|---|---|
| `proyeccion_generada` | Igual en 29/29 |
| Claves históricas presentes en `horizonte_info`, con sus valores | Iguales en 29/29 |
| Valores de las **17 columnas históricas** del CSV reproducible, en todas sus filas | Iguales en 29/29. Con resultados nuevos valen `''` (y `False` en `horizonte_solicitado_cubierto`); con la plantilla (`sin_valores_validos`), `0`; con la sesión heredada, los valores antiguos |
| Fuente del encabezado de la UI (observada en el HTML) | Igual: `razon_principal` en 28 casos y `mensaje_ui` en la sesión heredada |
| Excepciones | 0 |
| Definiciones ausentes en el final | Las 6 |

Detalle en `evidencia/sonda_base_vs_final.txt`, `evidencia/sonda_base.json` y `evidencia/sonda_final.json`.

## 3. Exportables completos, incluidas las 17 columnas

- El oráculo de 66 escenarios compara, en `gui_sesion_exportables`, el CSV reproducible completo (columnas, orden y valores), el Excel, el PDF y el DOCX de sesión, las sesiones guardadas y restauradas y los datos de la GUI. **Base y final son idénticos** (04).
- El Golden `sesion_exportables`, que incluye la cabecera del CSV con las 17 columnas, está en PASS.
- `test_presentacion_resultados::test_exportable_diferencia_recomendado_evaluado_y_limite_operativo`, que fija 4 lecturas históricas del CSV, también está en PASS (06).

## 4. Declaración

Este lote **no** retira ni renombra columnas del CSV y no cambia ninguna lectura de clave. Tampoco cambia el tratamiento de `0` frente a `''`, el encabezado de las sesiones restauradas, `mensaje_ui`, `firma_serie_sha256` ni `version_criterios`. **AS-004 sigue sin ejecutar**; su dictamen sigue siendo el de AS-028: NO-GO por dependencias.
