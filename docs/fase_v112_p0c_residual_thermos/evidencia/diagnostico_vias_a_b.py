"""P0-C-R, GATE 0: ¿se reconstruye el IC95 retirado desde la salida pública de `ejecutar_proyeccion`?

Uso (desde la raíz del repositorio, Qt offscreen):  python docs/fase_v112_p0c_residual_thermos/evidencia/diagnostico_vias_a_b.py

Para cada escenario se ejecuta `ejecutar_proyeccion` real. Los límites internos (`ci95_lo`/`ci95_hi`) se capturan con un
espía sobre `_retirar_intervalo_de_publicacion` ANTES de que los vacíe; después se intenta reconstruirlos SOLO desde el
objeto público devuelto:

  Vía A  : `backtesting_comparativo[<ganador>_h<h>].metricas.errores_extremos.observaciones[*].error_absoluto`.
  Vía B1 : el agregado `backtesting_comparativo[<ganador>_h<h>].metricas.rmse` y su `iteraciones` (sin leer el vector).
  Vía B2 : `desviacion_error` y `error_medio` de la misma entrada, sin `rmse` ni el vector.
  Vía B3 : `backtesting.metricas.rmse` (muestra rectangular común W*) con n = W*. Es la misma cifra que la fila h de
           `horizonte_info.tabla_horizontes` (`rmse`, `W`), la columna `rmse_horizonte` del CSV y la sesión JSON.

En todas: límites = y_proj ± c(n)·sigma·factor, con c(n) = `_multiplicador_intervalo(0.95, n)` (función pública del módulo)
y `factor` = 1 salvo ajuste de calendario (se informa). Se compara con igualdad EXACTA (==) y se da la diferencia absoluta.
"""
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import app_icociv.proyeccion.servicio_proyeccion as sp  # noqa: E402


def serie(valores, anio=2021):
    return pd.DataFrame({"Periodo": [f"{anio + i // 12}_{i % 12 + 1}" for i in range(len(valores))],
                         "Indice": [float(v) for v in valores]})


def ondulada(n):
    return serie([100.0 + 0.4 * i + 3.0 * math.sin(i * 0.7) for i in range(n)])


def ruidosa(n, semilla=7):
    rng = np.random.default_rng(semilla)
    return serie([120.0 + 0.6 * i + rng.normal(0.0, 2.5) for i in range(n)])


def estacional(n, semilla=3):
    rng = np.random.default_rng(semilla)
    return serie([100.0 + 0.3 * i + 6.0 * math.cos(2 * math.pi * i / 12) + rng.normal(0.0, 0.8) for i in range(n)])


ESCENARIOS = [
    ("ondulada n=48 h=6 (caso B-A1)", ondulada(48), 6),
    ("ruidosa n=72 h=12 (errores no triviales)", ruidosa(72), 12),
    ("ondulada n=38 h=24 (pocos pares: 3 errores en el paso 24)", ondulada(38), 24),
    ("estacional n=60 h=9", estacional(60), 9),
    ("ondulada n=48 h=24 (H máximo: W* coincide con la muestra del intervalo)", ondulada(48), 24),
    ("ruidosa n=72 h=24 (H máximo)", ruidosa(72), 24),
    ("ruidosa n=30 h=3 (historia insuficiente)", ruidosa(30), 3),
]

_capturado = {}
_original = sp._retirar_intervalo_de_publicacion


def _espia(resultado, *a, **k):
    _capturado.clear()
    _capturado.update({c: resultado.get(c) for c in ("ci95_lo", "ci95_hi", "y_proj")})
    return _original(resultado, *a, **k)


sp._retirar_intervalo_de_publicacion = _espia


def objetivo(df, h):
    anio, mes = map(int, df.iloc[-1]["Periodo"].split("_")[:2])
    total = anio * 12 + mes - 1 + h
    return total // 12, total % 12 + 1


def comparar(nombre, lo, hi, interno):
    ilo, ihi = interno
    exacto = (lo == ilo) and (hi == ihi)
    print(f"    {nombre:<7} lo={lo!r} hi={hi!r}  exacto={exacto}  |dif|=({abs(lo - ilo):.3e}, {abs(hi - ihi):.3e})")
    return exacto


def main():
    for titulo, df, h in ESCENARIOS:
        print(f"== {titulo}")
        try:
            r = sp.ejecutar_proyeccion(df, *objetivo(df, h), 2021)
        except Exception as exc:  # historia insuficiente: se informa, no se oculta
            print(f"    ejecutar_proyeccion lanza {type(exc).__name__}: {exc}")
            continue
        interno = (_capturado.get("ci95_lo"), _capturado.get("ci95_hi"))
        print(f"    proyeccion_generada={r.get('proyeccion_generada')} modelo={r.get('modelo_codigo')} "
              f"y_proj={r.get('y_proj')!r}  IC95 interno={interno}  publicado=({r.get('ci95_lo')}, {r.get('ci95_hi')})")
        if interno[0] is None:
            print("    sin banda interna: no hay nada que reconstruir")
            continue
        clave = f"{r['modelo_codigo']}_h{h}"
        entrada = (r.get("backtesting_comparativo") or {}).get(clave) or {}
        met = entrada.get("metricas") or {}
        y = float(r["y_proj"])
        cal = r.get("ajuste_calendario") or {}
        aplicado = bool(cal.get("aplicado") or cal.get("ajuste_calendario_aplicado"))
        factor = 1.0
        print(f"    entrada {clave}: iteraciones={entrada.get('iteraciones')} rmse={met.get('rmse')!r} "
              f"ajuste_calendario_aplicado={aplicado}")

        # Vía A
        obs = ((met.get("errores_extremos") or {}).get("observaciones")) or []
        ea = np.array([o["error_absoluto"] for o in obs if isinstance(o, dict) and "error_absoluto" in o], float)
        ea = ea[np.isfinite(ea)]
        if len(ea):
            s = float(np.sqrt(np.mean(ea ** 2)))
            c = sp._multiplicador_intervalo(sp.NIVEL_NOMINAL_95, len(ea))
            comparar("Vía A", y - c * s * factor, y + c * s * factor, interno)
            print(f"            n={len(ea)} sigma={s!r}")
        else:
            print("    Vía A  : sin observaciones con error_absoluto")

        # Vía B1
        n = int(met.get("iteraciones") or entrada.get("iteraciones") or 0)
        if met.get("rmse") is not None and n:
            s = float(met["rmse"])
            c = sp._multiplicador_intervalo(sp.NIVEL_NOMINAL_95, n)
            comparar("Vía B1", y - c * s * factor, y + c * s * factor, interno)

        # Vía B2: sigma^2 = media^2 + varianza poblacional; `desviacion_error` se prueba con ddof=1 y ddof=0
        if met.get("desviacion_error") is not None and met.get("error_medio") is not None and n:
            m, de = float(met["error_medio"]), float(met["desviacion_error"])
            c = sp._multiplicador_intervalo(sp.NIVEL_NOMINAL_95, n)
            for ddof in (1, 0):
                var_pob = de ** 2 * (n - ddof) / n
                s = math.sqrt(m ** 2 + var_pob)
                comparar(f"B2 dd{ddof}", y - c * s * factor, y + c * s * factor, interno)

        # Vía B3: RMSE rectangular publicado (otra muestra)
        bt = r.get("backtesting") or {}
        rm, w = (bt.get("metricas") or {}).get("rmse"), bt.get("iteraciones")
        if rm is not None and w:
            c = sp._multiplicador_intervalo(sp.NIVEL_NOMINAL_95, int(w))
            comparar("Vía B3", y - c * float(rm) * factor, y + c * float(rm) * factor, interno)
            print(f"            n=W*={w} rmse_rectangular={rm!r}")


if __name__ == "__main__":
    main()
