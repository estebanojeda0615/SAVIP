# 05 · Informe de cierre del lote 2D-5 (AS-003)

## Dictamen: **APTO**

**Qué se retiró:**
- la función heredada `tramo_evidencia_oos`;
- sus tres constantes exclusivas, `TRAMO_OOS_SIN_EVIDENCIA`, `TRAMO_OOS_MUY_LIMITADA` y `TRAMO_OOS_DISPONIBLE`;
- el único id esencial que solo probaba esa API.

Ninguno tenía consumidores en producción ni en scripts.

**Qué se conservó:**
- `_texto_evidencia_oos`, con el cuerpo idéntico;
- `ventanas_oos_disponibles`;
- `MIN_ITERACIONES_WF_ESCENARIO`;
- `test_ps03_w_es_cero…`;
- r3, completo.

La nota HGRID pasa al docstring de la función vigente que redacta los tramos.

**Verificación:**
- **Comportamiento:** huella exacta con 0 diferencias y los 29 golden en verde.
- **Pruebas esenciales:** 812 → 811 ids. Solo desaparece el autorizado y los otros 811 pasan sin cambiar de estado.
- **Recolección:** de 1 067 a 1 066, con los mismos 3 errores.
- **r3:** 21/27, idéntico a la base.
- **CI:** verde en el primer intento.
- **Thermos:** tres pasadas con los dos agentes. Ningún hallazgo crítico, alto ni medio queda abierto.

## 1. Evidencia por puerta

| Puerta | Resultado | Dónde |
|---|---|---|
| §2, inspección de la ejecución detenida | La ejecución P0-C no dejó cambios parciales. El repositorio de desarrollo del usuario, el clon P0-C-R y el borrador cancelado se conservan intactos y fuera del diff | 00 |
| G1, consumidores | **GO.** El único consumidor ejecutable es el id PS-03 autorizado. El resto son menciones de texto o nombres parecidos, sin usos dinámicos | 01 |
| G2, comportamiento vigente | **GO.** Con el retiro simulado, `_texto_evidencia_oos` y las pruebas sustitutas siguen correctos y `test_ps03_w_es_cero…` pasa | 02 §3 |
| Ejecución reducida | 5 archivos: −29/+13 en producción, −20/+2 y −11/+14 en pruebas, y +1/+1 de configuración. El retiro, el id y W=10 van en el mismo commit atómico `a056d9f` | 02 §1–2 |
| Pruebas y equivalencia | 811/811 en local y en CI. Golden 29/29, AS-001 16/16, huella con 0 diferencias. Recolección 1 066 con 3 errores. r3 21/27. Diff vacío en las áreas vetadas | 03 |
| Thermos | Tres pasadas con `thermo-nuclear-reviewer` y `thermo-nuclear-code-quality-reviewer`. En la última, corrección no encuentra nada y calidad dice «APROBADO» | 04 |
| GitHub | Commits pequeños, solo en la rama nueva, sin trailers. Sin merge, PR, tag ni release | 03 §4 |

## 2. Cifras

| Indicador | Valor |
|---|---|
| Definiciones retiradas | 1 función (11 líneas) y 3 constantes |
| Producción | `servicio_proyeccion.py`: −29 / +13, de 5 871 a 5 855 líneas. Lo añadido es solo docstring |
| Pruebas | 1 id esencial retirado; 1 test ampliado con el mismo id (W=10 y ancla del corte) |
| Ids esenciales | **812 → 811** |
| AS-003 restante | 20 definiciones en `servicio_proyeccion.py`, en los lotes 2D-1, 2D-2 y 2D-3 (no iniciados) |

## 3. Rama, commits y enlaces

- **Rama:** https://github.com/estebanojeda0615/SAVIP/tree/maintenance/v1.1.2-fase2d-lote5-thermos
- **Comparación con la base:** https://github.com/estebanojeda0615/SAVIP/compare/dfcaaa9be1f50cbe529daa3483bd23a10344bfdc...maintenance/v1.1.2-fase2d-lote5-thermos

| Commit | Contenido |
|---|---|
| `9ff51e3` | Filtro del CI y `.gitignore` |
| `a056d9f` | Retiro atómico |
| `1c8c952` | Correcciones de la 1.ª pasada de Thermos |
| `cae9f04` | Correcciones de la 2.ª pasada de Thermos (último commit de código) |
| HEAD documental | Esta carpeta |

**CI del código:** [41766294797](https://github.com/estebanojeda0615/SAVIP/actions/runs/41766294797), [41766989903](https://github.com/estebanojeda0615/SAVIP/actions/runs/41766989903) y [41767344083](https://github.com/estebanojeda0615/SAVIP/actions/runs/41767344083). Los tres dieron success con 811/811, sin reintentos. El CI del HEAD documental figura en el mensaje de entrega.

**Reversión:** `git revert cae9f04 1c8c952 a056d9f`. La rama base no se ha modificado.

## 4. Pendientes fuera de alcance (no se declaran resueltos)

1. **Reconstrucción del IC95 desde métricas publicadas (P0-C).** Es un hallazgo **preexistente**, documentado en la fase P0-C-R (rama `maintenance/v1.1.2-p0c-residual-ic95-thermos`, `fde777f`). Este lote no lo trata y la corrección P0-C está cancelada.
2. **Columna CSV `tramo_evidencia_oos_horizonte_solicitado` siempre vacía** (`generador_reportes.py:381`). Nadie produce esa clave, ni antes ni después de este lote; la aserción HG4 de r3 la espera. Es preexistente y lo decide el propietario.
3. **Comentarios obsoletos** en `tests/test_residuales_auditoria_independiente_r3.py:513-514` («candidata a retiro en el lote 2D-5») y en `tests/test_as007_contratos_r3_vigentes.py:14`. No se tocaron porque el prompt prohíbe cambiar r3 y limita el diff de pruebas.
4. **`_texto_evidencia_oos` en la ruta vigente** solo se llama con 0. Sus otras ramas dependen de `_clasificar_evidencia_horizonte`, que pertenece al lote 2D-3. Hay que tenerlo en cuenta cuando se ejecute ese lote.
5. **AS-007 sigue abierto:** r3 (6 fallos heredados), los dos `test_p0c_*`, `bghc` y PS-02/anexo DANE.
6. **Los 3 errores históricos de recolección** y las intermitentes conocidas (`test_interaccion_fase_3c_a::test_a` y `pdf_sesion`), que no aparecieron en este lote.

## 5. Ramas y versión

No se modificaron `main` (`dfdb3e0`), `develop/v1.1.2` (`6672529`), el tag ni el release `v1.1.2-rc.1` (`08f364b`), las ramas de fases anteriores, el ejecutable publicado ni el ZIP. No hubo merge, PR, tag, release, EXE ni ZIP.

**No se iniciaron los lotes 2D-1, 2D-2, 2D-3 ni 2D-6; no hubo merge ni release.**
