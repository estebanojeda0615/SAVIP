# 01 · G1: referencias y decisión

**Herramientas usadas:**
- `git grep -n -w` sobre todo el repositorio en `dfcaaa9`, sin `docs/` para los consumidores y con `docs/` para las menciones;
- el grafo AST conservador de la Fase 2A (`docs/fase_v112_antislop_02a_as003/evidencia/grafo_as003.py`);
- búsqueda de usos dinámicos (`getattr`, `setattr`, `patch`, `globals`, `importlib` y cadenas de despacho).

Evidencia: [`evidencia/g1_grep.txt`](evidencia/g1_grep.txt) y [`evidencia/g1_grafo_extracto.txt`](evidencia/g1_grafo_extracto.txt).

## 1. Símbolo → consumidores → decisión

| Símbolo | Tipo | Consumidor ejecutable en producción o scripts | Pruebas sobre la API | Menciones solo de texto | Decisión |
|---|---|---|---|---|---|
| `tramo_evidencia_oos` (`servicio_proyeccion.py:2047-2057`, 11 líneas) | `def` | **Ninguno.** Grafo AST: `produccion: false`, `scripts: false`, `referenciado_por: []` | `tests/test_cierre_semantico_ps01_ps05.py:181-195`, en el id PS-03 autorizado | Tupla `HEREDADAS` (`test_fase2c_contratos_vigentes.py:28`, «se cita como texto, no exige que exista»), docstrings de 2C (`:67`, `:117`), `test_as007_contratos_r3_vigentes.py:14`, comentario de r3 (`:514`) | **Retirar** |
| `TRAMO_OOS_SIN_EVIDENCIA`, `TRAMO_OOS_MUY_LIMITADA`, `TRAMO_OOS_DISPONIBLE` (`:2042-2044`) | Constantes de módulo | **Ninguno**, fuera de la propia función | Solo PS-03 (`:182-192`) | Docstring de `_texto_evidencia_oos` («Ver `TRAMO_OOS_SIN_EVIDENCIA`») | **Retirar**. Se elimina la referencia colgante |
| Bloque de comentario HGRID (`:2032-2041`) | Comentario | — | — | — | **Trasladar** al docstring de `_texto_evidencia_oos` |
| `_texto_evidencia_oos` (`:2060-2070`) | `def` vigente | `_estructurar_resultado_horizontes` y `_clasificar_evidencia_horizonte` | `test_fase2c_contratos_vigentes`, r3 | — | **Conservar** el cuerpo; solo cambia el docstring |
| `ventanas_oos_disponibles` (`:1996-2029`) | `def` vigente | `_limites_auditoria_horizontes` | PS-02/PS-03 (`w_es_cero`), r3 | — | **Conservar sin tocar** |
| `MIN_ITERACIONES_WF_ESCENARIO` | Constante (`criterios.py:70`) | `_texto_evidencia_oos`, `_intervalos_prediccion` y otros | 2C, r3 | — | **Conservar sin tocar** |

## 2. Nombres parecidos que no son el símbolo retirado

| Nombre | Dónde | Por qué no es consumidor |
|---|---|---|
| `tramo_evidencia_oos_horizonte_solicitado` | `app_icociv/reportes/generador_reportes.py:381` (lista de claves del CSV), `tests/fixtures/fase0/golden/sesion_exportables.json:6753`, r3 `:566` | Es una clave de diccionario o columna que se lee con `.get(...)`. No llama a la función. **Nadie la produce**, ni en la base ni ahora: es un hallazgo preexistente (05 §4) |
| «tramo» en `criterios.py:210` y en `pruebas/prueba_horizonte_dinamico_ui_reportes.py:648,939` | Comentarios | Es otra acepción de la palabra |

## 3. Usos dinámicos, reexportaciones y empaquetado

| Búsqueda | Resultado |
|---|---|
| `getattr`, `setattr` y `patch` con `tramo`/`TRAMO` | Ninguno |
| `globals()` e `importlib` | Solo usos genéricos: el runner de pruebas por `test_*`, `dependencias.py` y `MIN_ERRORES_COBERTURA_EMPIRICA`. Ninguno con estos nombres |
| `__all__` y reexportación en `app_icociv/proyeccion/__init__.py` | No existen |
| `packaging/`, `*.spec`, `pruebas/`, `scripts/` | Ninguna referencia |

## 4. r3 y PS-03

- `tests/test_residuales_auditoria_independiente_r3.py` **ya estaba desacoplado** desde AS-007. No importa la función ni las constantes, y solo menciona `tramo_evidencia_oos` en un comentario. **Queda fuera del diff.**
- `test_cierre_semantico_ps01_ps05.py`: solo `test_ps03_la_escasez_…` referencia los nombres. `test_ps03_w_es_cero_exactamente_cuando_el_dato_no_existe` usa `ventanas_oos_disponibles` y **se conserva**.

## 5. Conclusión de G1

**GO.** No hay ningún consumidor real fuera de los elementos que se autoriza retirar.
