"""P0-C-R · sensibilidad del detector `vectores_por_ventana` y de la vía B (mutaciones en memoria, sin tocar producción).

Uso (desde la raíz, Qt offscreen):  python docs/fase_v112_p0c_residual_thermos/evidencia/mutaciones_adversarial.py
"""
import copy
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from adversarial_p0c_residual_ic95 import _banda, _ejecutar, vectores_por_ventana  # noqa: E402


def sin_observaciones(publico):
    """La «corrección parcial»: retirar el vector de todas las entradas del comparativo."""
    for entrada in publico["backtesting_comparativo"].values():
        extremos = (entrada.get("metricas") or {}).get("errores_extremos")
        if isinstance(extremos, dict):
            extremos.pop("observaciones", None)
    return publico


def main():
    base, interno, h = _ejecutar("n48_h6")
    clave = f"{base['modelo_codigo']}_h{h}"

    corregido = sin_observaciones(copy.deepcopy({k: v for k, v in base.items() if k != "predict_func"}))
    print(f"M0 base: vectores={len(vectores_por_ventana(base))}")
    print(f"M1 sin observaciones (corrección parcial): vectores={len(vectores_por_ventana(corregido))} "
          "-> la prueba RED pasaría a verde")
    met = corregido["backtesting_comparativo"][clave]["metricas"]
    print(f"   ...pero vía B sigue exacta: {_banda(corregido, float(met['rmse']), met['iteraciones']) == (interno['lo'], interno['hi'])}")

    m2 = copy.deepcopy(corregido)
    m2["diagnostico_extra"] = [{"origen": i, "Error": 0.1 * i} for i in range(5)]
    print(f"M2 lista de registros con 'Error' en otra ruta: vectores={vectores_por_ventana(m2)}")

    m3 = copy.deepcopy(corregido)
    m3["backtesting"]["predicciones"] = m3["backtesting"]["predicciones"].assign(Predicho=1.0)
    print(f"M3 columna 'Predicho' en backtesting.predicciones: vectores={vectores_por_ventana(m3)}")

    m4 = copy.deepcopy(corregido)
    m4["backtesting_comparativo"][clave]["metricas"]["errores_extremos"]["error_absoluto"] = [0.5, 0.7, 0.9]
    print(f"M4 clave 'error_absoluto' con secuencia numérica: vectores={vectores_por_ventana(m4)}")

    m5 = copy.deepcopy(corregido)
    m5["anidado"] = {"tabla": pd.DataFrame({"Origen": [1, 2], "Observado": [1.0, 2.0]})}
    print(f"M5 DataFrame anidado con 'Observado': vectores={vectores_por_ventana(m5)}")

    m6 = copy.deepcopy(corregido)
    m6["solo_uno"] = [{"error_absoluto": 0.3}]
    print(f"M6 un único registro (no es vector): vectores={vectores_por_ventana(m6)}  (esperado: vacío)")


if __name__ == "__main__":
    main()
