"""Anexos DANE SINTÉTICOS para la Fase 4G (no son cifras publicadas por el DANE).

Generan la estructura real del Anexo 16 (mismas tablas y columnas fijas que el
cargador) con valores inventados y rotulados como sintéticos. Permiten simular
una publicación hasta 2026-08 y otra hasta 2026-10 con agosto revisado.
"""
from __future__ import annotations

import math

import pandas as pd
from openpyxl import Workbook

from app_icociv.utilidades.utilidades import COLUMNAS_FIJAS_TABLAS

PAVIMENTOS = "Pavimentos asfálticos / concreto"


def valor_sintetico(grupo: int, i: int) -> float:
    return 100 + grupo + i * .2 + math.sin(i / 3) * .1


BASES = "Bases granulares (sintético)"


def anexo_dane_sintetico(ruta, fin="2026-08", revision=0.0, mismo_rotulo=False, sin_ruta=False, inicio="2016-01",
                         capitulo_extra=False):
    """Escribe un anexo sintético que va de ``inicio`` a ``fin`` (serie larga para H=10).

    ``revision`` suma ese valor a todos los meses ya publicados (revisión
    retrospectiva sintética). ``mismo_rotulo`` pone la etiqueta de capítulo
    PAVIMENTOS a los dos grupos (rutas distintas con el mismo texto visible).
    ``sin_ruta`` cambia los códigos del grupo 1 para que la serie deje de existir.
    ``capitulo_extra`` (Fase 4G-B) añade en A16.3 un segundo capítulo, BASES, bajo la
    misma tipología del grupo 1: una tipología con dos series.
    """
    periodos = [f"{p.year}_{p.month}" for p in pd.period_range(inicio, fin, freq="M")]
    libro = Workbook()
    hoja = libro.active
    hoja.title = "Anexo 16"
    for tag, columnas in COLUMNAS_FIJAS_TABLAS.items():
        hoja.append([tag + ". PRUEBA - datos sintéticos, no oficiales"])
        hoja.append(columnas + periodos)
        for grupo in (1, 2):
            codigo = grupo + (90 if sin_ruta and grupo == 1 else 0)
            valores = []
            for c in columnas:
                if "Ponderacion" in c:
                    valores.append(100.0)
                elif "cod" in c.lower():
                    valores.append(codigo)
                elif c == "Cap_const" and (grupo == 1 or mismo_rotulo):
                    valores.append(PAVIMENTOS)
                else:
                    valores.append(f"{c} sintético {codigo}")
            serie = [valor_sintetico(grupo, i) + revision for i in range(len(periodos))]
            hoja.append(valores + serie)
            if capitulo_extra and tag == "A16.3" and grupo == 1:
                extra = [3 if c in ("Cod_Cap_const", "cod_agreg_niv_obra_cap") else BASES if c == "Cap_const" else v
                         for c, v in zip(columnas, valores)]
                hoja.append(extra + [valor_sintetico(3, i) + revision for i in range(len(periodos))])
        for _ in range(3):
            hoja.append([None])
    libro.save(ruta)
    return ruta
