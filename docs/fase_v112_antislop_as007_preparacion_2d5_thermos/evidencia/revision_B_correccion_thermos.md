# Thermos B (1.ª pasada) · thermos:thermo-nuclear-reviewer · alcance 6ac158d...febd981

**Invocación.** Skill `thermos:thermos` (Thermos 1.1.0), que lanzó el agente `thermos:thermo-nuclear-reviewer` en segundo plano sobre el diff `diff_B_codigo.patch`. Claude Code 2.1.238. Revisión de solo lectura; los sondeos se ejecutaron con `PYTHONDONTWRITEBYTECODE` y Qt offscreen.

Lo que sigue es la salida del revisor, condensada sin alterar los hallazgos.

## Comprobaciones que hizo

- Pruebas nuevas: 9 PASS en 10,5 s.
- r3: 21/27, con los 6 fallos de siempre.
- Retiro de 2D-5 simulado en memoria: r3 se importa sin error.
- `_tramo()` frente a `tramo_evidencia_oos()`: 0 discrepancias con `None`, `"x"`, `""`, 0, −1, 1, 2, 2.9, `"2"`, 3, 3.5, `True`, `False`, 6 y 10**6.
- Ninguna llamada muta el dict que comparte `lru_cache`.

## Hallazgos

**ALTO**

**A1. Falso verde en C1 (defecto demostrado).**
- Dónde: `tests/test_as007_contratos_p0c_vigentes.py:100-108`, `:78-97` y `:142-148`, frente a la promesa del docstring en `:3-4`.
- Evidencia: `ejecutar_proyeccion(_ondulada(48), h=6)` publica `backtesting_comparativo["exponencial_log_lineal_h6"]["metricas"]["errores_extremos"]["observaciones"]`, 31 dicts con `error_absoluto`. Con `sigma = sqrt(mean(e²))` y `_multiplicador_intervalo(0.95, 31)` se obtiene IC95 = (117.69742214273187, 125.47330550648688), idéntico bit a bit al interno. Ocurre en todas las entradas modelo×horizonte.
  - `_retirar_errores_oos_de_publicacion` (`servicio_proyeccion.py:794-811`) solo limpia `predicciones`.
  - La prueba no lo detecta porque `_tablas_de_ventanas`/`_errores_recuperables` solo miran DataFrames con columnas Origen u Horizonte.
  - La sesión JSON y el CSV están limpios.
- Origen: punto ciego heredado de r3 C1. El diff lo convierte en garantía esencial.
- Remedio: escalarlo como residual P0-C nuevo, y además endurecer la detección (que falle hoy) o acotar el docstring y el nombre y registrar la fuga como DECISIÓN PENDIENTE. No dejar el texto actual con verde.

**MEDIO.** Ninguno.

**BAJO**
- **B1. `_texto_informe` (`:124-139`) no lee los campos que el PDF sí dibuja.** Fuera quedan `Formula` (etiqueta, general, resultado, sustitucion), `Imagen.pie`, `Ficha.destacados` e `informe.pie`: unos 1 071 caracteres. Hueco demostrado; hoy no oculta ninguna fuga.
- **B2. Encabezados del DOCX comparados por igualdad (`:221`).** No detecta `Error_abs`, `Error_pct` ni similares. Hipótesis.
- **B3. Código muerto (`:55-75`, `:32-33`).** `_hojas` y `CLAVES_DECLARACION`. Demostrado.
- **B4. `_tramo()` depende del texto (`r3:518-522`).** Hoy es equivalente. Si cambiara la redacción caería en DISPONIBLE: los HG fallarían de forma visible, pero el mensaje sería engañoso. Hipótesis.
- **B5. `lru_cache` comparte un dict mutable (`:46-52`).** Hoy nadie lo muta. Hipótesis.
- **B6. La aserción de `model_name` puede volverse vacía (`:205`).** Hipótesis.

## Sin hallazgos

- CI y perfil esencial: 10,5 s frente a 1 200 s por archivo; Qt offscreen; mismo patrón de imports que la Fase 2C; sin skip ni xfail.
- Archivos temporales: todos dentro de `TemporaryDirectory`.
- Workflow: `permissions: contents: read` y sin secretos.
- Seguridad: ninguna credencial en el diff.
- Perfiles: r3 sigue en históricas.
- Discusión del PR: no consultada porque `gh` no está instalado (y no hay PR).
