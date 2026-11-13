# 01 · Grafo y alcance de las seis definiciones (G1)

## 1. Grafo AST revalidado sobre `8e5a62b`

Herramienta: `docs/fase_v112_antislop_02a_as003/evidencia/grafo_as003.py`. Salida: `evidencia/grafo_8e5a62b.json`. El resultado es idéntico al de AS-028 porque el árbol `app_icociv` es el mismo.

| Definición | Líneas (base) | N.º | Producción | Referenciada por (código) |
|---|---|---|---|---|
| `determinar_horizonte_maximo_estadistico` | 3274-3531 | 258 | **No** | Nadie en `app_icociv`. Solo las 8 pruebas retiradas, la guarda de la Fase 1A y los literales de `HEREDADAS` |
| `_serializar_evaluaciones_horizonte` | 3534-3603 | 70 | No | Solo `determinar_*` |
| `_item_horizonte_global` | 3606-3622 | 17 | No | Solo `determinar_*` |
| `_mayor_horizonte_con` | 3625-3650 | 26 | No | Solo `determinar_*`. Además, la histórica `test_cierre_metodologico` y la cita documental de C-ALC-002 |
| `_ultimo_horizonte_por_clasificacion` | 3687-3714 | 28 | No | Solo `determinar_*` |
| `_evidencia_horizonte` | 3717-3737 | 21 | No | Solo `determinar_*` |
| **Total** | | **420** | | El conjunto es cerrado |

**Compartidos con 2D-3, conservados**

| Definición | Uso que persiste |
|---|---|
| `_tipo_uso_horizonte` | Lo llama `_clasificar_evidencia_horizonte` (L3043 del final) |
| `_mayor_horizonte_permitido` | Lo llama `_aplicar_salvaguarda_benchmarks` (L3172 y L3227 del final) |

Todo 2D-3 sigue definido. `evidencia/ast_ausencia_y_compartidos.txt` registra su `sha256(ast.dump)` en el final.

## 2. Rutas dinámicas, exportación y packaging (`evidencia/referencias_dinamicas.txt`)

| Vía | Resultado |
|---|---|
| `getattr` / `importlib` / `__import__` / `import *` en `app_icociv` y `aplicacion.py` | Ninguna sobre `servicio_proyeccion`. El único `importlib` (`config/dependencias.py:67`) carga dependencias de terceros |
| `__all__` | `app_icociv/proyeccion/__init__.py` exporta solo `ejecutar_proyeccion` |
| `packaging/SAVIP.spec` (hiddenimports) | Ninguna referencia a las 6 |
| Texto fuera de su propio grupo | Comentarios en `analisis_series.py` L712-713 y L797, y en `presentacion_resultados.py` L1333. La ficha `C-ALC-002` (`criterios.py` L639) es una ruta documental. **Se inventarían y no se modifican** (08) |
| Sesiones | Las sesiones guardan **datos** (`horizonte_info`), no referencias a funciones. Se restauran sin recalcular (AS-028/04 §2.3) |

## 3. Espías pasivos sobre la ejecución real

Herramienta: `evidencia/scripts/sonda_claves_as004.py`. Los espías cuentan y delegan.

**Casos ejecutados** (28 más 1):
- **Ejecución normal:** fixtures drift y holt, y una serie estable de 120.
- **Historia insuficiente:** serie de 20.
- **Escenarios de error:** sin valores válidos, valor negativo y valor cero.
- Cada serie se ejecuta con h=1, 12, 18 y 24.
- **Sesión heredada:** un `horizonte_info` antiguo inyectado.

**Datos observados en cada caso:** las claves de `horizonte_info`, las 17 columnas históricas del CSV y el encabezado HTML real de la UI.

**Resultado en la base:** **0 llamadas** a las 8 funciones (6 objetivo y 2 compartidas) en los 29 casos (`evidencia/sonda_base.json`).

## 4. Ausencia: simulada (G4.0) y real (final)

| Prueba | Base `8e5a62b` con las 6 ocultas en memoria (plugin `ocultar_2d1`, sin editar) | Final `406e1dd`, con las 6 **eliminadas** |
|---|---|---|
| Colección de `tests` | 1 021, con 4 errores: los 3 históricos más `test_resultado_horizonte_solicitado`, porque su import no estaba adaptado (`evidencia/g0_collect_oculto.txt`) | 1 028, con **los 3 históricos**. Ya no aparece el de `test_resultado_horizonte_solicitado` |
| Archivos afectados | Fallan exactamente los previstos: 15 por colección, 2 de presentación, la Fase 1A y la histórica de la cascada; además, el preexistente `test_no_hay_modelo_por_horizonte` (`evidencia/g0_afectados_oculto.txt`) | Perfil esencial **801/801**. Histórica de cierre 21/1, el preexistente (06) |
| Script manual | 19 PASS / 7 FAIL | 19 PASS / 7 FAIL, idéntico id por id |
| Sonda AS-004 | 29 casos, 0 diferencias frente a la base visible (`evidencia/g0_sonda_oculto.txt`) | 29 casos, **0 diferencias** frente a la base y 0 excepciones (`evidencia/sonda_base_vs_final.txt`) |
| AST del módulo | — | 72 definiciones de nivel superior. Las 6 ausentes, **0 referencias residuales** (Name/Attribute) y los compartidos presentes (`evidencia/ast_ausencia_y_compartidos.txt`) |
| Importación de los 86 módulos y de `VentanaPrincipal` | — | OK (`evidencia/final_imports.txt`) |

**Conclusión de la puerta de alcanzabilidad:**
- no hay ningún consumidor productivo de las seis definiciones;
- no aparece ningún consumidor sin catalogar;
- no hay ningún acceso dinámico material;
- no se retira ninguna función compartida.

**La puerta se superó antes de borrar.**
