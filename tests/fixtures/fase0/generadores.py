"""Fase 0: datos sintéticos deterministas para los Golden Masters (sin datos DANE ni sesiones personales).

Todo se genera en memoria o en una carpeta temporal a partir de fórmulas y semillas fijas: no hay
archivos binarios versionados. Los valores esperados están en ``golden/`` y solo los escribe
``generar_golden.py`` (ejecución manual, una vez, sobre el código congelado)."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from openpyxl import Workbook

from app_icociv.utilidades.utilidades import COLUMNAS_FIJAS_TABLAS


def _periodos(n: int, anio: int = 2020) -> list[str]:
    return [f"{anio + i // 12}_{i % 12 + 1}" for i in range(n)]


def _tendencia_lineal_ruido(n=60):
    rng = np.random.default_rng(7)
    return [100.0 + 0.5 * i + rng.normal(0, 1.2) for i in range(n)]


def _estacional(n=72):
    rng = np.random.default_rng(11)
    return [100.0 + 0.3 * i + 2.0 * math.sin(2 * math.pi * i / 12) + rng.normal(0, 0.4) for i in range(n)]


def _exponencial(n=48):
    rng = np.random.default_rng(3)
    return [100.0 * math.exp(0.01 * i) * (1 + rng.normal(0, 0.002)) for i in range(n)]


def _paseo_aleatorio(n=40):
    rng = np.random.default_rng(5)
    return list(100.0 + np.cumsum(rng.normal(0.1, 0.8, n)))


def _lineal_exacta(n=36):
    return [100.0 + 0.5 * i for i in range(n)]


#: Escenarios del motor: (n, generador, horizontes consultados). ``lineal_exacta`` (ruido 0) produce
#: empates exactos entre candidatos y ejercita el desempate por orden del banco.
ESCENARIOS_MOTOR = {
    "tendencia_lineal_ruido": _tendencia_lineal_ruido,
    "estacional": _estacional,
    "exponencial": _exponencial,
    "paseo_aleatorio": _paseo_aleatorio,
    "lineal_exacta_empate": _lineal_exacta,
}
#: Rechazo: historia menor que N0 + H = 36 meses.
ESCENARIO_INSUFICIENTE = ("historia_insuficiente_30", 30)


def serie(nombre: str) -> pd.DataFrame:
    if nombre == ESCENARIO_INSUFICIENTE[0]:
        rng = np.random.default_rng(2)
        valores = [100.0 + 0.5 * i + rng.normal(0, 1.2) for i in range(ESCENARIO_INSUFICIENTE[1])]
    else:
        valores = ESCENARIOS_MOTOR[nombre]()
    return pd.DataFrame({"Periodo": _periodos(len(valores)), "Indice": [float(v) for v in valores]})


def objetivo(serie_df: pd.DataFrame, h: int) -> tuple[int, int]:
    """(año, mes) situado ``h`` meses después de la última observación."""
    anio, mes = map(int, serie_df["Periodo"].iloc[-1].split("_"))
    total = anio * 12 + (mes - 1) + h
    return total // 12, total % 12 + 1


def anexo_sintetico(ruta, meses: int = 48):
    """Anexo 16 sintético con la estructura del DANE (2 grupos por tabla, desde 2023-01).

    Grupo 1: tendencia lineal con estacionalidad anual. Grupo 2: crecimiento exponencial suave."""
    libro = Workbook(); hoja = libro.active; hoja.title = "Anexo 16"
    periodos = _periodos(meses, 2023)
    curvas = {1: [100 + 0.35 * i + 0.6 * math.sin(2 * math.pi * i / 12) for i in range(meses)],
              2: [100 * math.exp(0.004 * i) + 0.2 * math.cos(i / 2) for i in range(meses)]}
    for tag, columnas in COLUMNAS_FIJAS_TABLAS.items():
        hoja.append([tag + ". PRUEBA - datos sintéticos"]); hoja.append(columnas + periodos)
        for grupo in (1, 2):
            hoja.append([100.0 if "Ponderacion" in c else grupo if "cod" in c.lower() else f"{c} sintético {grupo}" for c in columnas]
                        + [round(v, 6) for v in curvas[grupo]])
        for _ in range(3):
            hoja.append([None])
    libro.save(ruta)
    return ruta


#: Vectores económicos: (I, I0) elegidos en las fronteras de ROUND_HALF_UP y con representación binaria
#: inexacta, más bases con decimales y casos de importe unitario/total.
VECTORES_FACTOR = [
    (110.0, 100.0), (102.741, 100.0), (102.745, 100.0), (102.744, 100.0), (97.255, 100.0), (100.0, 100.0),
    (100.005, 100.0), (99.995, 100.0), (133.3333, 123.4567), (118.92, 112.37), (150.0, 149.99), (87.654321, 91.2345),
]
VECTORES_IMPORTE = [  # (precio P, anticipo A, I, I0, cantidad)
    (1000.0, 0.0, 110.0, 100.0, None), (1000.0, 200.0, 110.0, 100.0, 1.0), (100000.0, 0.0, 102.745, 100.0, 3.5),
    (2500.55, 100.1, 118.92, 112.37, 12.0), (0.01, 0.0, 133.3333, 123.4567, 1000.0), (987654321.99, 12345.67, 150.0, 149.99, 2.0),
    (1234.5, 0.0, 97.255, 100.0, 0.25),
]
