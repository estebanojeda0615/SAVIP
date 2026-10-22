"""Identidad de series, firmas de ejecución y fuentes DANE nuevas (Fase 4G).

Funciones puras sobre las instantáneas ya guardadas en el historial ICOCIV:
no ejecutan el motor ni modifican los análisis. Sirven para:

* agrupar el historial por **serie** (identidad taxonómica: tabla del anexo,
  columnas descriptivas de la fila fuente y ruta jerárquica completa), separada
  de la **versión de datos** (huella de la serie mensual observada);
* reconocer una ejecución equivalente ya guardada (misma serie, mismos datos,
  mismos parámetros) antes de volver a llamar al motor;
* localizar en un anexo DANE recién cargado la misma fila de la serie para
  ofrecer, solo por acción expresa, su último índice como referencia económica.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any

import pandas as pd

from app_icociv.persistencia.historial_icociv import recuperar_resultado
from app_icociv.servicios.fecha_objetivo import consulta_vigente, detalle_vigente

_PERIODO = re.compile(r"^(\d{4})[-_](\d{1,2})$")


def _periodo(valor: Any) -> str | None:
    m = _PERIODO.match(str(valor).strip()) if valor is not None else None
    if not m or not 1 <= int(m[2]) <= 12:
        return None
    return f"{int(m[1]):04d}-{int(m[2]):02d}"


def _sha(objeto: Any) -> str:
    return hashlib.sha256(json.dumps(objeto, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _descriptivas(fila: pd.DataFrame) -> list[list[str]]:
    """Columnas descriptivas de la fila fuente (sin meses ni ponderaciones).

    La ponderación puede cambiar entre publicaciones sin cambiar la serie, por
    eso no forma parte de la identidad.
    """
    pares = []
    for columna in fila.columns:
        if _periodo(columna) or "ponderacion" in str(columna).lower():
            continue
        valor = fila[columna].iloc[0]
        if isinstance(valor, float) and math.isfinite(valor) and valor.is_integer():
            valor = int(valor)
        pares.append([str(columna), str(valor).strip()])
    return pares


def _recuperado(resultado: Any) -> dict[str, Any] | None:
    if not isinstance(resultado, dict):
        return None
    datos = dict(resultado)
    for clave in ("fila", "serie_df"):
        if not isinstance(datos.get(clave), pd.DataFrame):
            datos[clave] = recuperar_resultado(datos.get(clave))
    return datos


def identidad_serie(resultado: Any) -> tuple[str | None, str]:
    """(clave determinista, motivo) de la serie de un resultado.

    Devuelve ``(None, motivo)`` cuando la instantánea no permite demostrar la
    identidad; esa entrada se muestra sola, nunca agrupada por semejanza.
    """
    datos = _recuperado(resultado)
    try:
        fila = datos["fila"]; fuente = datos["fuente"]; ruta = datos["ruta_jerarquica"]
        if not isinstance(fila, pd.DataFrame) or len(fila) != 1 or not isinstance(fuente, str) or not fuente:
            raise ValueError
        descriptivas = _descriptivas(fila)
        if not descriptivas:
            raise ValueError
        # El nivel «Tabla ICOCIV» es un rótulo derivado de `fuente` (ya en la clave) y no siempre viaja en la ruta:
        # incluirlo hacía distinta la misma serie según el camino que construyó la ruta (Fase 4I-J).
        ruta = [[str(r.get("nivel", "")), str(r.get("valor", ""))] for r in ruta if r.get("nivel") != "Tabla ICOCIV"]
    except (KeyError, TypeError, ValueError, AttributeError):
        return None, "La instantánea no conserva tabla, fila fuente o ruta verificables."
    return _sha({"tabla": fuente, "fila": descriptivas, "ruta": ruta}), ""


def huella_datos(resultado: Any) -> str | None:
    """Huella de la serie mensual observada que recibió el motor."""
    datos = _recuperado(resultado)
    serie = datos.get("serie_df") if datos else None
    if not isinstance(serie, pd.DataFrame) or not {"Periodo", "Indice"}.issubset(serie.columns):
        return None
    puntos = []
    for periodo, indice in serie[["Periodo", "Indice"]].itertuples(index=False, name=None):
        valor = pd.to_numeric(indice, errors="coerce")
        puntos.append([str(periodo), repr(float(valor)) if pd.notna(valor) else None])
    return _sha(puntos)


def firma_ejecucion(resultado: Any, parametros: dict[str, Any]) -> str | None:
    """Firma de una ejecución: serie + datos + parámetros que afectan al motor.

    ``origen_horizonte`` (manual/predeterminado) no interviene: solo rotula el
    resultado y cambia al restaurar los controles desde un análisis guardado,
    sin alterar ningún cálculo.
    """
    clave, _ = identidad_serie(resultado)
    huella = huella_datos(resultado)
    if not clave or not huella or not isinstance(parametros, dict):
        return None
    return _sha({"serie": clave, "datos": huella,
                 "parametros": {k: parametros.get(k) for k in ("anio", "mes", "horizonte")}})


def agrupar_historial(historial: list[dict], valores: list[dict]) -> list[dict]:
    """Serie → análisis (revisiones) → actividades vigentes, por IDs."""
    grupos: dict[str, dict] = {}
    for numero, analisis in enumerate(historial, 1):
        clave, motivo = identidad_serie(analisis.get("resultado"))
        contexto = analisis.get("contexto") or {}
        clave_grupo = clave or f"individual:{analisis['id']}"
        grupo = grupos.setdefault(clave_grupo, {
            "clave": clave_grupo, "verificable": bool(clave), "motivo": motivo,
            "etiqueta": contexto.get("ruta_texto") or contexto.get("serie_final") or "Serie sin ruta",
            "tabla": contexto.get("tabla_icociv", ""), "analisis": []})
        horizonte = (analisis.get("parametros") or {}).get("horizonte")
        objetivo = _periodo(contexto.get('periodo_proyectado'))
        vigente = consulta_vigente(analisis)  # Fase 4I-P: se rotula la consulta vigente, no la ejecución original
        if vigente:
            objetivo, horizonte = vigente["periodo"], vigente["horizonte"]
        revision = len(grupo["analisis"]) + 1
        actividades = [{"calculo_id": r.get("calculo_id"), "item": r.get("item", ""),
                        "componente": r.get("nombre_componente", ""), "cantidad": r.get("cantidad"),
                        "modalidad": r.get("modalidad_importe", "heredado"),
                        "valor": r.get("valor_proyectado")}
                       for r in valores if r.get("analisis_id") == analisis["id"]]
        grupo["analisis"].append({
            "id": analisis["id"], "numero": numero, "revision": revision,
            "etiqueta": f"#{numero} · {objetivo or 'objetivo s/d'} · "
                        f"{horizonte} {'mes' if horizonte == 1 else 'meses'} · revisión {revision}",
            "detalle_consulta": detalle_vigente(analisis),
            "ultimo_observado": _periodo(contexto.get("periodo_base")) or "",
            "creado": analisis.get("creado", ""), "huella_datos": huella_datos(analisis.get("resultado")),
            "actividades": actividades})
    return list(grupos.values())


def localizar_en_fuente(resultado: Any, tablas: dict[str, pd.DataFrame], periodos: list[str]) -> dict[str, Any]:
    """Busca la MISMA serie en un anexo cargado; nunca una fila parecida.

    Exige la misma tabla y exactamente una fila con las mismas columnas
    descriptivas. Devuelve la serie mensual observada de esa fila.
    """
    datos = _recuperado(resultado)
    clave, motivo = identidad_serie(datos)
    if not clave:
        raise ValueError(motivo)
    fuente = datos["fuente"]
    tabla = (tablas or {}).get(fuente)
    if not isinstance(tabla, pd.DataFrame):
        raise ValueError(f"El anexo cargado no contiene la tabla {fuente} de esta serie.")
    descriptivas = _descriptivas(datos["fila"])
    mascara = pd.Series(True, index=tabla.index)
    for columna, valor in descriptivas:
        if columna not in tabla.columns:
            raise ValueError(f"El anexo cargado no tiene la columna {columna}; la serie no es comparable.")
        mascara &= tabla[columna].map(lambda x: str(int(x) if isinstance(x, float) and math.isfinite(x) and x.is_integer() else x).strip()) == valor
    coincidencias = tabla[mascara]
    if len(coincidencias) != 1:
        raise ValueError("La serie no aparece una sola vez en el anexo cargado (ruta ausente o ambigua); "
                         "no se toma el índice de otra fila.")
    fila = coincidencias.iloc[0]
    serie = {}
    for columna in periodos or []:
        periodo = _periodo(columna)
        if periodo and columna in coincidencias.columns:
            valor = pd.to_numeric(fila[columna], errors="coerce")
            if pd.notna(valor) and math.isfinite(float(valor)) and float(valor) > 0:
                serie[periodo] = float(valor)
    if not serie:
        raise ValueError("La serie del anexo cargado no tiene meses observados válidos.")
    return {"tabla": fuente, "serie": dict(sorted(serie.items())), "huella_fuente": _sha(sorted(serie.items()))}


# ---------------------------------------------------------------------------
# Fase 4G-B: ámbitos de consulta y alcance de exportación (funciones puras)
# ---------------------------------------------------------------------------
# Un ÁMBITO es un nodo real de la jerarquía guardada (prefijo tipado de la ruta
# del análisis: [(nivel, valor), ...]) o una serie exacta (identidad_serie).
# Nunca se compara texto suelto: dos capítulos homónimos en ramas distintas
# tienen prefijos distintos y, por tanto, ámbitos distintos.

TIPOS_ALCANCE = ("sesion", "categoria", "serie", "proyeccion")


def ficha_analisis(analisis: dict, numero: int, revision: int = 1) -> dict:
    """Metadatos de consulta de un análisis, sin tocar su instantánea."""
    clave, motivo = identidad_serie(analisis.get("resultado"))
    datos = analisis.get("resultado") if isinstance(analisis.get("resultado"), dict) else {}
    ruta = datos.get("ruta_jerarquica") if isinstance(datos.get("ruta_jerarquica"), list) else []
    ruta = [(str(r.get("nivel", "")), str(r.get("valor", ""))) for r in ruta
            if isinstance(r, dict) and r.get("nivel") != "Tabla ICOCIV" and r.get("valor")]
    contexto = analisis.get("contexto") or {}
    vigente = consulta_vigente(analisis)  # Fase 4I-P: objetivo y H de la consulta vigente, si existe
    return {"id": analisis["id"], "numero": numero, "revision": revision, "serie": clave, "motivo": motivo,
            "ruta": ruta if clave else [], "tabla": str(contexto.get("tabla_icociv") or datos.get("fuente") or ""),
            "serie_final": contexto.get("serie_final") or (ruta[-1][1] if ruta else ""),
            "objetivo": vigente["periodo"] if vigente else _periodo(contexto.get("periodo_proyectado")) or "",
            "horizonte": vigente["horizonte"] if vigente else (analisis.get("parametros") or {}).get("horizonte")}


def fichas_historial(historial: list[dict]) -> list[dict]:
    """Fichas en orden del historial; la revisión cuenta dentro de cada serie."""
    contador: dict = {}; fichas = []
    for numero, a in enumerate(historial, 1):
        clave, _ = identidad_serie(a.get("resultado"))
        llave = clave or f"individual:{a['id']}"
        contador[llave] = contador.get(llave, 0) + 1
        fichas.append(ficha_analisis(a, numero, contador[llave]))
    return fichas


def etiqueta_proyeccion(ficha: dict, con_serie: bool = False) -> str:
    h = ficha["horizonte"]
    texto = f"#{ficha['numero']} · {ficha['objetivo'] or 'objetivo s/d'} · H={h} · revisión {ficha['revision']}"
    return f"{ficha['serie_final']} · {texto}" if con_serie else texto


def ambitos_disponibles(fichas: list[dict]) -> list[dict]:
    """Nodos jerárquicos y series exactas que existen en el historial.

    Cada ámbito: tipo ('categoria'|'serie'), clave estable, etiqueta visible con
    desambiguador cuando hay homónimos y contexto breve (ancestros y tabla).
    """
    nodos: dict = {}; series: dict = {}
    for f in fichas:
        for largo in range(1, len(f["ruta"]) + 1):
            prefijo = tuple(f["ruta"][:largo])
            nodos.setdefault(prefijo, {"tipo": "categoria", "clave": _sha([list(p) for p in prefijo]),
                                       "prefijo": prefijo, "nivel": prefijo[-1][0], "valor": prefijo[-1][1]})
        if f["serie"]:
            series.setdefault(f["serie"], {"tipo": "serie", "clave": f["serie"], "prefijo": tuple(f["ruta"]),
                                           "nivel": "Serie exacta", "valor": f["serie_final"], "tabla": f["tabla"]})
    ambitos = sorted(nodos.values(), key=lambda n: [p[1] for p in n["prefijo"]]) + \
        sorted(series.values(), key=lambda s: [p[1] for p in s["prefijo"]])
    # Desambiguar homónimos visibles (mismo nivel y nombre en ramas distintas).
    for a in ambitos:
        iguales = [b for b in ambitos if b["tipo"] == a["tipo"] and b["nivel"] == a["nivel"] and b["valor"] == a["valor"]]
        sufijo = ""
        if len(iguales) > 1:
            profundidad = 1
            while profundidad < len(a["prefijo"]):
                padres = {tuple(x[1] for x in b["prefijo"][-1 - profundidad:-1]) for b in iguales}
                if len(padres) == len(iguales):
                    break
                profundidad += 1
            sufijo = " — " + " › ".join(x[1] for x in a["prefijo"][-1 - profundidad:-1])
        codigo = re.match(r"\s*(A\d+(?:\.\d+)?)", a.get("tabla") or "")
        tabla = f" [{codigo[1] if codigo else a['tabla']}]" if a["tipo"] == "serie" and a.get("tabla") else ""
        a["etiqueta"] = f"{a['nivel']} · {a['valor']}{tabla}{sufijo}"
        a["contexto"] = " › ".join(x[1] for x in a["prefijo"][:-1]) or "Primer nivel"
    return ambitos


def analisis_en_ambito(fichas: list[dict], ambito: dict | None) -> list[str]:
    """IDs de análisis del ámbito, en orden del historial (None = toda la sesión)."""
    if not ambito:
        return [f["id"] for f in fichas]
    if ambito["tipo"] == "serie":
        return [f["id"] for f in fichas if f["serie"] and f["serie"] == ambito["clave"]]
    largo = len(ambito["prefijo"])
    return [f["id"] for f in fichas if len(f["ruta"]) >= largo and tuple(f["ruta"][:largo]) == tuple(ambito["prefijo"])]


def resolver_alcance(tipo: str, fichas: list[dict], valores: list[dict], ambito: dict | None = None,
                     analisis_id: str | None = None) -> dict:
    """Alcance de exportación → IDs ordenados de cálculos y análisis.

    Única fuente de verdad para Excel, PDF y Word. No depende del filtro visual
    ni del análisis activo. Conserva el orden canónico de ``valores`` y no
    repite un ``calculo_id``. Los registros sin vínculo demostrable solo entran
    en «sesion» y se informan como no atribuibles en los demás alcances.
    """
    if tipo not in TIPOS_ALCANCE:
        raise ValueError(f"Alcance desconocido: {tipo}")
    ids_historial = {f["id"] for f in fichas}
    if tipo == "sesion":
        analisis = [f["id"] for f in fichas]
    elif tipo in ("categoria", "serie"):
        if not ambito or (tipo == "serie") != (ambito["tipo"] == "serie"):
            raise ValueError("Seleccione un ámbito válido para este alcance.")
        analisis = analisis_en_ambito(fichas, ambito)
    else:
        if analisis_id not in ids_historial:
            raise ValueError("Seleccione una proyección concreta.")
        analisis = [analisis_id]
    incluidos = set(analisis); vistos = set(); calculos = []
    for r in valores:
        identificador = r.get("calculo_id")
        if identificador in vistos:
            continue
        if tipo == "sesion" or r.get("analisis_id") in incluidos:
            vistos.add(identificador); calculos.append(identificador)
    no_atribuibles = [] if tipo == "sesion" else [r.get("calculo_id") for r in valores if r.get("analisis_id") not in ids_historial]
    # Aviso (no corrección): misma actividad aparente en revisiones distintas.
    grupos: dict = {}
    for r in valores:
        if r.get("calculo_id") in vistos:
            llave = (str(r.get("item", "")).strip().lower(), str(r.get("nombre_componente", "")).strip().lower(),
                     r.get("unidad"), r.get("cantidad"))
            grupos.setdefault(llave, []).append(r)
    posibles = [[{"calculo_id": r.get("calculo_id"), "analisis_id": r.get("analisis_id")} for r in rs]
                for rs in grupos.values() if len({r.get("analisis_id") for r in rs}) > 1]
    return {"tipo": tipo, "calculos": calculos, "analisis": analisis, "no_atribuibles": no_atribuibles,
            "posibles_duplicados": posibles, "solo_tecnico": not calculos and bool(analisis)}
