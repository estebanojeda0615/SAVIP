# 02 · G5: pruebas afectadas

| Id | Perfil | Antes | Después | Decisión |
|---|---|---|---|---|
| `tests/test_fundamentacion_metodologica.py::test_el_selector_retirado_conserva_su_definicion_para_auditoria` | esencial | PASS | **retirada** | Solo exigía que `seleccionar_modelo_por_evidencia` existiera y que su docstring dijera «RETIRADA COMO SELECTOR». Su papel de registro de auditoría pasa a Git (`2f70391`, L280-L444) y a `docs/fase_v112_antislop_02c_registro_historico/02` (R1). En su lugar queda un comentario con esa trazabilidad. Matriz 2C: `SIN EQUIVALENTE / NO APLICA` |
| `test_fundamentacion_metodologica::test_la_ruta_productiva_no_invoca_el_selector_de_respaldo` | esencial | PASS | PASS | Sin cambios. Busca el texto `seleccionar_modelo_por_evidencia(` en la fuente de `_evaluar_horizontes_proyeccion`; no requiere que exista |
| `test_fundamentacion_metodologica::test_el_selector_de_respaldo_no_se_importa_en_la_ruta_productiva` | esencial | PASS | PASS | Sin cambios (comprobación textual) |
| `test_nmin_adversarial::test_p0a_p0b_p0d_intactos` | esencial | PASS | PASS | Sin cambios (comprobación textual de P0-A) |
| `test_origen_inicial_backtesting::test_p0a_el_selector_de_respaldo_sigue_retirado` | esencial | PASS | PASS | Sin cambios |
| `test_fase2c_contratos_vigentes::test_la_ruta_vigente_no_referencia_el_subsistema_heredado` | esencial | PASS | PASS | Sin cambios: los nombres retirados siguen en `HEREDADAS` como texto, y la prueba sigue exigiendo que la ruta vigente no los nombre |
| `test_integracion_fhg::test_p0abd_intactos` | histórica | PASS | PASS | Sin cambios |

**Recuentos:**
- perfil esencial: **804 → 803** (−1, el id retirado);
- `pytest --collect-only tests`: **1 059 → 1 058**. El único id que desaparece es el retirado, y los 3 errores de recolección previos siguen igual.

Ninguna otra prueba se modificó.
