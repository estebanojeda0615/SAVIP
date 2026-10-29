# 08 · Informe de cierre de la Fase 2C (AS-003: registro histórico y preparación)

## Respuestas numeradas (§12 del prompt)

### 1. ¿Es la 2C APTA, APTA CON RESERVAS o NO APTA?

**APTA.** Se cumplen los siete criterios del §12:
1. Las 31 definiciones están clasificadas.
2. La trazabilidad es recuperable desde Git, con enlaces a commits inmutables y sin duplicar código.
3. Están clasificados los 95 ids o comprobaciones dependientes.
4. AS-024 y AS-028 quedan diseñados y no se aplicaron.
5. El plan 2D tiene lotes cerrados con GO/NO-GO y reversión.
6. Diff productivo vacío, 797 ids intactos, huella con 0 diferencias y CI en verde.
7. Cada lote queda pendiente de una autorización separada.

Los bloqueos encontrados (§8) **no** se presentan como resueltos: son condiciones NO-GO de la 2D.

### 2. ¿Cuántas definiciones y líneas quedan?

**31 definiciones y 1 723 líneas** en `2f70391`, como ya contaba la 2B.

**Método:** AST de nivel superior sobre `servicio_proyeccion.py` (21 definiciones, 1 391 líneas) y `modelos_interpretables.py` (10, 332), filtradas por el grafo `grafo_as003.py` («no alcanzable desde producción»). Las líneas son `end_lineno − lineno + 1`, sin separadores ni imports.

Quedan fuera `validar_serie` y `detectar_outliers_extremos` (107 líneas, contrato S). El mismo grafo sobre la raíz de GitHub `dfdb3e0` da las mismas 29 definiciones heredadas de `servicio_proyeccion.py` que había antes de las fases 2A y 2B.

### 3. ¿Cuáles son los consumidores reales restantes y cuáles solo documentan historia?

**Consumidores reales:**
- 27 ids esenciales en 9 archivos;
- 51 ids históricos recolectados;
- 17 comprobaciones de estilo script de `tests/` que no se recogen (dos `test_p0c_*` con error de importación, `bghc` y `r3`);
- el script `pruebas/prueba_horizonte_dinamico_ui_reportes.py`: 4 de sus 30 pruebas usan `determinar_…` y el selector global.

**Producción:** ninguno (grafo + espía G2).

**Solo historia:**
- 6 fichas de `criterios.py`: C-SEL-001, C-ALC-001, C-ALC-002, C-ALC-003, C-SAL-001 y C-BEN-002;
- 5 comentarios de código vigente (L720, L1431, L1502, L4464, L4979). Dos de ellos describen un bloqueo que ya no ocurre.

**Lecturas huérfanas:** `generador_reportes.py` lee claves que solo producía `determinar_…` (AS-004).

### 4. ¿Qué pruebas nuevas se agregaron y qué protegen?

**7 casos** en `tests/test_fase2c_contratos_vigentes.py`, dentro del perfil esencial, sobre la ruta vigente:
- escasez de ventanas, con el punto entregado, la advertencia solo si W* < 6 y sin intervalo (×3);
- banda no construible que no cancela el punto;
- vocabulario de `_texto_evidencia_oos`;
- sin errores finitos comunes no se fabrica un modelo;
- la ruta vigente no nombra el subsistema heredado.

Cada una dice qué prueba heredada sustituiría. Pasan con y sin el código heredado, y su sensibilidad se comprobó con 6 mutantes. **No se añadió** una prueba para «MAPE no finito no bloquea»: queda `REQUIERE CREAR`, porque exige decidir si una serie con observaciones 0 es válida.

### 5. ¿Cuántos ids esenciales había antes y después?

**797 antes y 804 después.** Los **797 originales se conservan con el mismo estado**: 0 desaparecidos y 0 cambiados. Los 7 añadidos están en 07 §1.

**Estado de los 27 esenciales que dependen del código heredado:**

| Estado | Ids |
|---|---|
| Cubierto ya | 7 |
| Prueba nueva incorporada | 6 |
| Requiere crear | 1 |
| Decisión pendiente | 3 |
| Sin equivalente / no aplica | 10 |

### 6. ¿Cómo se preservó la evidencia metodológica?

En 02, el registro con:
- la metodología vigente;
- R1–R8 con su fecha según el código y el tipo de motivo;
- trazabilidad, recuperación con `git show <SHA>:<ruta>`, riesgos de lectura y lo que se desconoce.

**Commits de referencia:**
- `2f70391e1b920764e79fa50ec2c2da6b6b572e53`: las 31 definiciones;
- `1848275`: las 3 retiradas en la 2B;
- `c9166c6`: las 6 retiradas en la 2A;
- `dfdb3e0`: raíz de 1.1.1;
- `6672529`: tag rc.1.

En 01, cada definición enlaza a `blob/2f70391…#Lini-Lfin`.

**Hecho relevante:** en GitHub no hay ninguna versión en la que esas reglas decidieran el resultado. Su época productiva es anterior a `dfdb3e0` y queda como **desconocida**.

### 7. ¿Qué fichas AS-024 y qué scripts AS-028 exigen intervención?

**AS-024:**
- reubicar como `HISTORICO …@2f70391…` las 6 fichas citadas, cada una en el commit que retire su símbolo;
- nota de época en C-HOR-003;
- laguna: no existe una ficha del selector vigente (C-SEL-002 propuesta; su `tipo`, `fuente` y `justificacion` los decide el responsable metodológico).

**AS-028:**
- `prueba_horizonte_dinamico_ui_reportes.py`: retirar, o migrar lo vigente. Hoy está en 22 PASS / 8 FAIL previos;
- `ejemplo_uso.py`: parche propuesto para `ci_lo=None`. Se conserva la API `ejecutar_analisis`;
- `prueba_estadistica.py`: no se toca.

### 8. ¿Qué lotes de la 2D podrían autorizarse y cuáles siguen bloqueados?

**Autorizables con condiciones mínimas:**
- **2D-4** (selector por evidencia, 332 líneas): requiere autorizar que se retire 1 id esencial que solo exige existencia.
- **2D-5** (`tramo_evidencia_oos`, 11 líneas): requiere autorizar que se retire PS03 y decidir AS-007 sobre `r3`.

**Bloqueados (NO-GO) hasta decidir:**
- **2D-2** (selector global, 107): por AS-028.
- **2D-1** (horizonte máximo, 420): por AS-028 y AS-004.
- **2D-3** (evaluación, clasificación y salvaguarda, 853): por la regla del **punto no finito**, que solo existe en el clasificador heredado y la ruta vigente no aplica. También dependen de la decisión «MAPE no calculable» y de AS-007.

### 9. ¿Hay 0 diferencias semánticas y Golden Masters intactos?

**Sí.** La huella exacta da el SHA-256 `d6be699b…` en la base (dos capturas) y en el final, con 0 diferencias. Los 29 golden pasan con `tests/fixtures` sin diff. AS-001 sigue en PASS.

### 10. ¿Cuál es el SHA publicado?

- **Código:** `7acd0ce`, con CI [40816459661](https://github.com/estebanojeda0615/SAVIP/actions/runs/40816459661): success, 804/804, ninguna intermitente.
- **HEAD documental final:** se informa en el mensaje de entrega, con su CI.
- Rama: https://github.com/estebanojeda0615/SAVIP/tree/maintenance/v1.1.2-fase2c-registro-historico
- Comparación: https://github.com/estebanojeda0615/SAVIP/compare/maintenance/v1.1.2-fase2b-as003-opcion-b...maintenance/v1.1.2-fase2c-registro-historico

### 11. ¿Siguen sin cambios `main`, `develop/v1.1.2`, el tag y el Release?

**Sí.** `main` `dfdb3e0`, `develop/v1.1.2` `6672529` y el tag `v1.1.2-rc.1` (`08f364b` → `6672529`) no cambiaron, y tampoco las ramas de las fases 0 a 2B. No hubo merge, PR, tag, release, ejecutable ni ZIP.

### 12. Confirmación

**«No se inició la Fase 2D ni se eliminó código del subsistema heredado en 2C.»**

## Decisiones pendientes del propietario (antes de la 2D)

1. **Regla del punto no finito**, que hoy solo está en el código heredado: ¿se mantiene en la ruta vigente, con un cambio de producción autorizado, o se abandona?
2. **Advertencia «MAPE/sMAPE no calculable»:** ¿se publica en la ruta vigente?
3. **AS-028:** destino de `pruebas/prueba_horizonte_dinamico_ui_reportes.py`.
4. **AS-007:** los 4 archivos de estilo script de `tests/` que importan funciones heredadas. Y el caso PS02, que pasa sin comprobar nada en un clon limpio, sin el anexo DANE.
5. **AS-004:** las lecturas de `horizonte_maximo_*` en `generador_reportes.py`.
6. **Autorización por lote** para retirar los ids esenciales listados en 06, con la política de 06 §4.
7. *(Opcional)* La ficha C-SEL-002.

**Solicitud concreta para la 2D:** autorizar primero **2D-4** y, si se decide AS-007 sobre `r3`, **2D-5**. Mantener 2D-1, 2D-2 y 2D-3 en NO-GO hasta resolver los puntos 1 a 5.
