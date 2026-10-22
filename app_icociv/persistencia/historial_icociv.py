"""Instantáneas JSON de resultados ya calculados, sin código ejecutable ni motor."""

import math

import numpy as np
import pandas as pd


def serializar_resultado(valor):
    if isinstance(valor, pd.DataFrame):
        return {"__savip_tipo__": "dataframe", "columnas": list(valor.columns),
                "indice": serializar_resultado(list(valor.index)),
                "tipos": [str(t) for t in valor.dtypes],
                "datos": serializar_resultado([list(fila) for fila in valor.itertuples(index=False, name=None)])}
    if isinstance(valor, np.ndarray):
        return {"__savip_tipo__": "array", "tipo": str(valor.dtype),
                "datos": serializar_resultado(valor.tolist())}
    if isinstance(valor, np.generic):
        return serializar_resultado(valor.item())
    if isinstance(valor, float) and not math.isfinite(valor):
        return {"__savip_tipo__": "no_finito", "valor": str(valor)}
    if isinstance(valor, tuple):
        return {"__savip_tipo__": "tupla", "datos": serializar_resultado(list(valor))}
    if isinstance(valor, list):
        return [serializar_resultado(v) for v in valor]
    if isinstance(valor, dict):
        if any(not isinstance(k, str) for k in valor):
            return {"__savip_tipo__": "pares", "datos":
                    [[serializar_resultado(k), serializar_resultado(v)] for k, v in valor.items()]}
        # La función del modelo no es un resultado ni se necesita para consultar la instantánea.
        return {k: None if k == "predict_func" else serializar_resultado(v) for k, v in valor.items()}
    if valor is None or isinstance(valor, (str, int, float, bool)):
        return valor
    raise ValueError(f"No se puede conservar el resultado de tipo {type(valor).__name__} en JSON.")


_ESCALARES_JSON = frozenset((str, int, float, bool, type(None)))


def recuperar_resultado(valor):
    if isinstance(valor, list):
        # Fase 4I-E: atajo para listas de escalares JSON (filas de tablas, series): la recursión
        # devolvería cada elemento sin cambios. Mismo resultado (lista nueva), sin una llamada por celda.
        if all(type(v) in _ESCALARES_JSON for v in valor):
            return list(valor)
        return [recuperar_resultado(v) for v in valor]
    if not isinstance(valor, dict):
        return valor
    tipo = valor.get("__savip_tipo__")
    if tipo == "dataframe":
        if len(valor["tipos"]) != len(valor["columnas"]) or len(valor["datos"]) != len(valor["indice"]):
            raise ValueError("Tabla guardada incompleta.")
        df = pd.DataFrame(recuperar_resultado(valor["datos"]), columns=valor["columnas"],
                          index=recuperar_resultado(valor["indice"]))
        # Fase 4I-E: solo se convierten las columnas cuyo tipo difiere, y de una vez (antes: una
        # reasignación por columna, miles en una sesión). Con nombres repetidos se usa el camino original.
        pendientes = {c: t for c, t in zip(df.columns, valor["tipos"]) if str(df[c].dtype) != t} if df.columns.is_unique else None
        if pendientes is None:
            for columna, dtype in zip(df.columns, valor["tipos"]):
                df[columna] = df[columna].astype(dtype)
        elif pendientes:
            df = df.astype(pendientes)
        return df
    if tipo == "array":
        return np.asarray(recuperar_resultado(valor["datos"]), dtype=valor["tipo"])
    if tipo == "no_finito":
        if valor["valor"] not in ("nan", "inf", "-inf"):
            raise ValueError("Número no finito guardado no reconocido.")
        return float(valor["valor"])
    if tipo == "tupla":
        return tuple(recuperar_resultado(valor["datos"]))
    if tipo == "pares":
        return {recuperar_resultado(k): recuperar_resultado(v) for k, v in valor["datos"]}
    if tipo is not None:
        raise ValueError("Tipo de resultado guardado no reconocido.")
    return {k: recuperar_resultado(v) for k, v in valor.items()}
