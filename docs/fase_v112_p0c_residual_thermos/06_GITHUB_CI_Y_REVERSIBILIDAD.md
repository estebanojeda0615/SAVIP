# 06 · GitHub, CI y reversibilidad

## Rama y commits

Rama: [`maintenance/v1.1.2-p0c-residual-ic95-thermos`](https://github.com/estebanojeda0615/SAVIP/tree/maintenance/v1.1.2-p0c-residual-ic95-thermos). Sale de `dfcaaa9`.

Autor y confirmador de todos los commits: `Esteban Ojeda <346522303+estebanojeda0615@users.noreply.github.com>`, sin trailers. Todos se publicaron con push normal: sin force-push, merge, PR, tag ni release.

| Commit | Contenido |
|---|---|
| `12319df` | GATE 0 NO-GO. Docs 00–03, diagnóstico y prueba adversarial. Workflow +1 línea (la rama) y `.gitignore` +1 excepción |
| `f8c8336` | Correcciones de la 1.ª pasada de Thermos: vías A' y B4, evidencia unificada en `caso_ic95.py` y docs 04, 05 y 07 |
| HEAD documental final | Correcciones de la 2.ª pasada de Thermos: vía B5, tolerancias declaradas y guarda de calendario. Doc 06 y ajustes de 01–05 y 07 |

**No hay commit de código de producción.** `git diff dfcaaa9 HEAD -- app_icociv aplicacion.py packaging VERSION requirements*.txt tests scripts` está vacío.

## CI (GitHub Actions, `fase0-pruebas`, perfil esencial completo)

| Run | Commit | Resultado |
|---|---|---|
| [41574968635](https://github.com/estebanojeda0615/SAVIP/actions/runs/41574968635) | `12319df` | success · 812/812 · 0 fallos en la 1.ª ejecución · intermitentes: ninguna · 1.er intento |
| [41577041743](https://github.com/estebanojeda0615/SAVIP/actions/runs/41577041743) | `f8c8336` | success · 812/812 · 0 · ninguna · 1.er intento |
| — | HEAD documental final | Se informa en el mensaje de entrega |

Detalle en [`evidencia/ci_resumen.txt`](evidencia/ci_resumen.txt).

- **Golden Masters:** forman parte del perfil esencial.
- **Intermitentes conocidas** (`test_interaccion_fase_3c_a::test_a` y `pdf_sesion`): no aparecieron.
- **Prueba adversarial:** el CI no la ejecuta, porque está fuera de la recolección y de los perfiles (03).

## Ramas protegidas (`git ls-remote` al cerrar)

| Ref | SHA | Estado |
|---|---|---|
| `main` | `dfdb3e046126093e23b045147f789fbc52961a73` | intacto |
| `develop/v1.1.2` | `66725293f304426ae6edf144b8f4dadbcbeefe10` | intacto |
| tag `v1.1.2-rc.1` | `08f364b0571726be7fb7c2432b8a316068ea7204` | intacto, junto con su release y su ZIP |
| `maintenance/v1.1.2-as007-preparacion-2d5-thermos` | `dfcaaa9be1f50cbe529daa3483bd23a10344bfdc` | intacta |

## Reversibilidad

No hay cambio de producción que revertir.

Para retirar la documentación y la configuración de esta fase basta con `git revert` de sus commits en esta rama, o con no fusionarla. La rama anterior no se ha modificado.
