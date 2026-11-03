"""P0-C-R, GATE 0: ¿se reconstruye el IC95 retirado desde la salida pública de `ejecutar_proyeccion`?

Uso, desde la raíz del repositorio:  python docs/fase_v112_p0c_residual_thermos/evidencia/diagnostico_vias_a_b.py

Para cada escenario de `caso_ic95.ESCENARIOS` se ejecuta `ejecutar_proyeccion` real, se captura el IC95 interno antes de que
se vacíe y se reconstruye con `y ± c(n)·sigma` desde cada vía de `caso_ic95.vias`:

  A  : vector `backtesting_comparativo[<ganador>_h<h>].metricas.errores_extremos.observaciones[*].error_absoluto`.
  A' : el mismo vector sin `error_absoluto`: |e| = mediana + z_modificado·MAD/factor (campos de `errores_extremos`).
  B1 : agregado `…metricas.rmse` con `…metricas.iteraciones` (sin leer el vector).
  B2 : `…metricas.desviacion_error` (ddof=1) y `…metricas.error_medio` con n: sigma² = media² + desv²·(n−1)/n.
  B4 : `…metricas.mae` y `…metricas.estabilidad_error` (= std(|e|, ddof=1)/mean(|e|)): sigma² = mae²·(1 + estab²·(n−1)/n).
  B3 : RMSE_h de `horizonte_info.tabla_horizontes` con su `W` (muestra rectangular). Es la misma cifra que
       `backtesting.metricas.rmse`, la columna `rmse_horizonte` del CSV, la sesión JSON, la interfaz y los informes.

Igualdad EXACTA (==); se informa además la diferencia absoluta.
"""
from caso_ic95 import ESCENARIOS, banda, proyectar, sin_calendario, vias


def main():
    for nombre in ESCENARIOS:
        publico, interno, h = proyectar(nombre)
        print(f"== {nombre}: proyeccion_generada={publico.get('proyeccion_generada')} "
              f"modelo={publico.get('modelo_codigo')} y_proj={publico.get('y_proj')!r}")
        if interno is None:
            print("    sin banda interna finita: no hay nada que reconstruir")
            continue
        if not sin_calendario(publico):
            print("    ajuste de calendario aplicado: la fórmula sin factor no se comprueba aquí")
            continue
        print(f"    IC95 interno={interno}  publicado=({publico.get('ci95_lo')}, {publico.get('ci95_hi')})")
        for via, (sigma, n) in vias(publico, h).items():
            lo, hi = banda(publico, sigma, n)
            exacto = (lo, hi) == interno
            semiancho = (interno[1] - interno[0]) / 2
            print(f"    {via:<30} n={n:<3} sigma={sigma!r:<22} exacto={exacto!s:<5} "
                  f"|dif|=({abs(lo - interno[0]):.3e}, {abs(hi - interno[1]):.3e}) "
                  f"= {abs(hi - interno[1]) / semiancho:.1%} del semiancho")


if __name__ == "__main__":
    main()
