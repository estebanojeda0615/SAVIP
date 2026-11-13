# Contexto Thermos — Lote 2D-1, PASADA 2 (final, último commit de código 406e1dd)

MODO SOLO LECTURA (temporales en tu directorio). Contexto completo: `C:/Pruebas SAVIP/L1D1/thermos/contexto_pasada1.md`.
Diff COMPLETO desde la base: `C:/Pruebas SAVIP/L1D1/thermos/diff_pasada2.patch` (= git diff 8e5a62b 406e1dd). No hubo
commits de corrección tras la pasada 1 (ambos agentes: APROBADO, sin crítico/alto/medio; bajos/info registrados como deuda
fuera de alcance: docstring de la histórica de cierre, `_evaluacion_horizonte_ui` sin uso, C-ALC-002, comentarios de
producción que citan la función retirada, import sin uso `_lineas_determinacion_horizonte`, nombre `retirados`).
Por eso la pasada 2 revisa el mismo último commit de código, con toda la evidencia de G5 ya disponible.

## Evidencia G5 (copia limpia `C:/Pruebas SAVIP/L1D1/final_406e1dd`, resultados en `C:/Pruebas SAVIP/L1D1/g5/`)
- Esencial local 801/801, 0 fallos 1.ª ejecución, sin intermitentes; comparación por (classname, name) con la base:
  8 bajas exactas, 0 altas, 0 cambios (`g5/comparacion_ids_801.txt`); 29 golden, 16 AS-001, 9 vigentes y guarda 1A PASS.
- AST (`g5/ast_ausencia_y_compartidos.txt`), imports (`g5/final_imports.txt`), collect 1028 + 3 errores históricos,
  script 19/7, cierre 21/1 (preexistente), huella 0 dif d6be699b…, compileall y pip check OK.
- Oráculo 66 (`C:/Pruebas SAVIP/L2/oraculo/salidas/cmp_*406e1dd*.txt`): 406e1dd r1=r2; 8e5a62b→406e1dd 66/66
  (hash 766a34b8…); original 6672529 r4/r2 → 406e1dd: solo AS-001; frente a r1 de la original, además el salto de línea
  no determinista del PDF de sesión (la original r1≠r2; texto concatenado idéntico). Golden exacto 0; umbral AS-001 igual.
- Sonda AS-004 (`g5/sonda_base_vs_final.txt`): 29 casos, 0 diferencias, 0 excepciones, 6 definiciones ausentes en final.
- CI del último commit de código: run 43304324537 en curso. Perfil histórico base/final en curso.

## Pedido
Pasada final sobre el diff completo y sobre la cobertura de contratos y la evidencia de equivalencia. Confirma o refuta
con verificación propia (puedes comparar los JSON del oráculo y releer el diff). Hallazgos priorizados con archivo:línea;
veredicto final. Sé conciso. Responde en español.
