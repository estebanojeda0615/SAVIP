"""Fase 4I-J: fecha objetivo común del presupuesto sobre trayectorias YA calculadas (sin motor).

Cada análisis guarda en su instantánea `proyeccion.trayectoria_24_meses`: 24 índices proyectados por el
modelo seleccionado desde el último mes observado de su serie (H1 = mes siguiente). Consultar otra fecha
es leer el punto H = meses entre ese origen y la fecha objetivo; no reentrena, no repite backtesting y no
fabrica puntos que no existan. La métrica que eligió el modelo es el RMSE agregado de 1 a 24 meses, por
lo que el modelo no depende del H consultado; la evidencia por horizonte (tabla_horizontes) es informativa.
"""

from __future__ import annotations

import re
from typing import Any

H_MAXIMO = 24
_MESES = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")


def periodo_iso(valor: Any) -> str:
    """'2026_8', '2026-08' → '2026-08'; vacío si no es un mes válido."""
    m = re.fullmatch(r"\s*(\d{4})[-_/](\d{1,2})\s*", str(valor or ""))
    return f"{int(m[1]):04d}-{int(m[2]):02d}" if m and 1 <= int(m[2]) <= 12 else ""


def periodo_visible(valor: Any) -> str:
    iso = periodo_iso(valor)
    return f"{_MESES[int(iso[5:]) - 1]}-{iso[:4]}" if iso else str(valor or "")


def meses_entre(origen: Any, destino: Any) -> int:
    a, b = periodo_iso(origen), periodo_iso(destino)
    if not a or not b:
        raise ValueError("Periodo no válido.")
    return (int(b[:4]) - int(a[:4])) * 12 + int(b[5:]) - int(a[5:])


def origen_analisis(analisis: dict[str, Any]) -> str:
    """Último mes observado que originó la trayectoria (no el I0 elegido por el usuario)."""
    contexto = analisis.get("contexto") or {}
    return periodo_iso(contexto.get("fecha_final_serie") or contexto.get("periodo_base"))


def trayectoria(analisis: dict[str, Any]) -> list[float]:
    proyeccion = (analisis.get("resultado") or {}).get("proyeccion") or {}
    valores = proyeccion.get("trayectoria_24_meses") or []
    return [float(v) for v in valores] if isinstance(valores, list) else []


def consultar(analisis: dict[str, Any], periodo_objetivo: str) -> dict[str, Any]:
    """Punto guardado de la trayectoria para `periodo_objetivo`. ValueError con el motivo si no existe."""
    origen = origen_analisis(analisis)
    if not origen:
        raise ValueError("no tiene un último mes observado identificable")
    h = meses_entre(origen, periodo_objetivo)
    if h < 1:
        raise ValueError(f"{periodo_visible(periodo_objetivo)} ya es un mes observado para su origen "
                         f"({periodo_visible(origen)}); elija un mes futuro")
    if h > H_MAXIMO:
        raise ValueError(f"{periodo_visible(periodo_objetivo)} está a {h} meses de su origen "
                         f"({periodo_visible(origen)}); el máximo es {H_MAXIMO}")
    puntos = trayectoria(analisis)
    if len(puntos) < h:
        raise ValueError(f"su instantánea guarda {len(puntos)} meses de trayectoria y {periodo_visible(periodo_objetivo)} "
                         f"requiere H{h}; ejecute de nuevo la proyección de esa serie")
    return {"periodo": periodo_iso(periodo_objetivo), "horizonte": h, "indice": puntos[h - 1], "origen": origen}


def vigentes(historial: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Análisis no reemplazados por una revisión posterior (enlace `revision_de`)."""
    reemplazados = {a.get("revision_de") for a in historial if a.get("revision_de")}
    return [a for a in historial if a.get("id") not in reemplazados]


def fecha_vigente(analisis: dict[str, Any]) -> str:
    """Fecha que usará la calculadora para ese análisis: la consultada o la de su ejecución."""
    consulta = analisis.get("consulta_horizonte") or {}
    return periodo_iso(consulta.get("periodo") or (analisis.get("contexto") or {}).get("periodo_proyectado"))


def contexto_consultado(contexto: dict[str, Any], consulta: dict[str, Any]) -> dict[str, Any]:
    """Contexto de la calculadora con el punto consultado (el contexto original del análisis no cambia)."""
    return {**contexto, "indice_proyectado": consulta["indice"], "periodo_proyectado": consulta["periodo"],
            "fecha_final_proyeccion": consulta["periodo"], "horizonte_solicitado": consulta["horizonte"],
            "consulta_trayectoria": True}


def proyeccion_consultada(proyeccion: dict[str, Any], consulta: dict[str, Any]) -> dict[str, Any]:
    """Fase 4I-N: copia TRANSITORIA de `proyeccion` para dibujar el H consultado (no se guarda).

    Proyección = primeros H puntos de `trayectoria_24_meses`, en los H meses siguientes al origen.
    Serie observada, ajuste histórico y `tabla_horizontes` (MAE_h de la banda) quedan como estaban.
    """
    import numpy as np
    import pandas as pd
    from app_icociv.utilidades.utilidades import periodo_a_t, t_a_periodo

    h = int(consulta["horizonte"])
    puntos = [float(v) for v in proyeccion["trayectoria_24_meses"][:h]]
    if len(puntos) < h:
        raise ValueError(f"la trayectoria guardada tiene {len(puntos)} meses y se requieren {h}")
    t_origen = periodo_a_t(consulta["origen"].replace("-", "_"))
    t_futuro = range(t_origen + 1, t_origen + h + 1)
    y_fit_obs = [float(v) for v in proyeccion["y_fit_obs"]]
    tabla = pd.DataFrame({"periodo": [t_a_periodo(t) for t in t_futuro], "indice_proyectado": puntos})
    # Fase 4I-P: mismas columnas descriptivas que la tabla original (índice / último observado), para Resultados.
    y_obs = list(proyeccion.get("y_obs", []))
    if y_obs and float(y_obs[-1]):
        tabla["factor_actualizacion"] = tabla["indice_proyectado"] / float(y_obs[-1])
        tabla["variacion_acumulada_pct"] = (tabla["factor_actualizacion"] - 1.0) * 100.0
    return {**proyeccion,
            "proyecciones": tabla,
            "t_full": np.arange(int(min(proyeccion["t_obs"])), t_origen + h + 1, dtype=float),
            "y_fit_full": np.asarray(y_fit_obs + puntos, dtype=float),
            "periodo_proj": consulta["periodo"], "horizonte_solicitado": h}


# ---------------------------------------------------------------------------
# Fase 4I-P: una sola lectura de la CONSULTA VIGENTE para historial, Resultados y gráfica.
# La ejecución original (nombre, contexto, resultado guardado) nunca se modifica: estas funciones
# devuelven textos o copias transitorias para mostrar.
# ---------------------------------------------------------------------------
_SUFIJO_NOMBRE = re.compile(r" · \d{4}-\d{2} · \d+ mes(es)?$")


def consulta_vigente(analisis: dict[str, Any]) -> dict[str, Any] | None:
    """Consulta aplicada al análisis, verificada contra su trayectoria guardada; None si no hay o no es válida."""
    consulta = (analisis or {}).get("consulta_horizonte")
    if not consulta:
        return None
    try:
        return consultar(analisis, consulta["periodo"])
    except (KeyError, TypeError, ValueError):
        return None


def nombre_vigente(analisis: dict[str, Any]) -> str:
    """Nombre del análisis con la fecha y el H de la consulta vigente (el `nombre` guardado no cambia)."""
    nombre = str((analisis or {}).get("nombre", ""))
    c = consulta_vigente(analisis)
    if not c:
        return nombre
    texto = f" · {c['periodo']} · {c['horizonte']} {'mes' if c['horizonte'] == 1 else 'meses'}"
    nuevo, n = _SUFIJO_NOMBRE.subn(texto, nombre)
    return nuevo if n else nombre + texto


def detalle_vigente(analisis: dict[str, Any]) -> str:
    """Línea breve «Consulta actual … / Ejecución original …» para tooltips y fichas; vacía sin consulta."""
    c = consulta_vigente(analisis)
    if not c:
        return ""
    contexto = (analisis or {}).get("contexto") or {}
    original = periodo_iso(contexto.get("periodo_proyectado"))
    h0 = contexto.get("horizonte_solicitado")
    return (f"Consulta actual: {c['periodo']} · H{c['horizonte']} · I = {c['indice']:.3f} (trayectoria guardada desde "
            f"{c['origen']}) / Ejecución original: {original or 's/d'} · H{h0}")


def resultado_consultado(resultado: dict[str, Any], analisis: dict[str, Any]) -> dict[str, Any]:
    """Copia TRANSITORIA de `resultado` para mostrar en Resultados la consulta vigente; sin consulta, el mismo objeto.

    Índice, periodo y H salen de `trayectoria_24_meses[H-1]`. Las métricas del paso consultado se toman de la
    fila H de `tabla_horizontes` de la MISMA ejecución (no es una validación nueva); si esa fila no existe, quedan
    vacías y no se sustituyen por las del H original. El resultado guardado no se modifica.
    """
    c = consulta_vigente(analisis)
    proyeccion = (resultado or {}).get("proyeccion") or {}
    if not c or not proyeccion.get("trayectoria_24_meses"):
        return resultado
    h = int(c["horizonte"])
    vista = proyeccion_consultada(proyeccion, c)
    solicitado = dict(proyeccion.get("resultado_horizonte_solicitado") or {})
    original = {"periodo": periodo_iso(solicitado.get("periodo_proyectado") or proyeccion.get("periodo_proj")),
                "horizonte": solicitado.get("horizonte_solicitado") or proyeccion.get("horizonte_solicitado")}
    solicitado.update(horizonte_solicitado=h, indice_proyectado=c["indice"], periodo_proyectado=c["periodo"],
                      consulta_vigente={**c, "periodo_original": original["periodo"],
                                        "horizonte_original": original["horizonte"]},
                      razon_principal=(f"Consulta vigente: H{h} ({c['periodo']}), punto {h} de la trayectoria de 24 meses "
                                       f"guardada desde {c['origen']}. Ejecución original: H{original['horizonte']} "
                                       f"({original['periodo']}). No es una nueva validación estadística."))
    info = proyeccion.get("horizonte_info") or {}
    fila = next((x for x in info.get("tabla_horizontes") or [] if x.get("horizonte") == h), None)
    metricas = ({"mae": fila.get("mae"), "rmse": fila.get("rmse"), "smape": fila.get("smape"), "mase": fila.get("mase"),
                 "sesgo_medio": fila.get("sesgo"), "mape": None} if fila else {})
    vista.update(resultado_horizonte_solicitado=solicitado, y_proj=c["indice"], horizonte_permitido=h,
                 backtesting={"ejecutado": bool(fila), "horizonte": h, "metricas": metricas,
                              "iteraciones": fila.get("W") if fila else None,
                              "metodo": "Fila H de la tabla por horizonte de la ejecución original",
                              "fuente_metricas": "tabla_horizontes"})
    return {**resultado, "proyeccion": vista}


def advertencia_fechas(registros: list[dict[str, Any]], fecha_presupuesto: str = "") -> str:
    """Texto de advertencia si los registros a exportar tienen fechas objetivo distintas entre sí o
    distintas de la fecha declarada del presupuesto; vacío si son homogéneos y coherentes."""
    conteo: dict[str, int] = {}
    for r in registros:
        iso = periodo_iso(r.get("periodo_proyectado"))
        if iso:
            conteo[iso] = conteo.get(iso, 0) + 1
    if not conteo:
        return ""
    plural = lambda n: f"{n} actividad" + ("es" if n != 1 else "")
    partes = " y ".join(f"{periodo_visible(p)} ({plural(n)})" for p, n in sorted(conteo.items()))
    if len(conteo) > 1:
        texto = f"El conjunto seleccionado incluye resultados con fechas objetivo diferentes: {partes}."
        if fecha_presupuesto and fecha_presupuesto not in conteo:
            texto += f" La fecha objetivo declarada del presupuesto es {periodo_visible(fecha_presupuesto)}."
        return texto
    unico = next(iter(conteo))
    if fecha_presupuesto and unico != periodo_iso(fecha_presupuesto):
        return (f"La fecha objetivo del presupuesto es {periodo_visible(fecha_presupuesto)}, pero las actividades "
                f"a exportar están calculadas para {partes}; requieren actualización expresa para cambiar de fecha.")
    return ""


if __name__ == "__main__":  # autocomprobación mínima
    a = {"contexto": {"fecha_final_serie": "2026_8"}, "resultado": {"proyeccion": {"trayectoria_24_meses": list(range(1, 25))}}}
    assert consultar(a, "2027-07") == {"periodo": "2027-07", "horizonte": 11, "indice": 11.0, "origen": "2026-08"}
    b = {**a, "contexto": {"fecha_final_serie": "2026_10"}}
    assert consultar(b, "2027-07")["horizonte"] == 9
    for malo in ("2026-08", "2028-09"):
        try:
            consultar(a, malo)
        except ValueError:
            pass
        else:
            raise AssertionError(malo)
    assert advertencia_fechas([{"periodo_proyectado": "2027-07"}] * 10 + [{"periodo_proyectado": "2027-09"}]).startswith("El conjunto")
    assert advertencia_fechas([{"periodo_proyectado": "2027-07"}] * 3, "2027-07") == ""
    assert "requieren actualización" in advertencia_fechas([{"periodo_proyectado": "2027-07"}], "2027-09")
    # Fase 4I-P: nombre visible con la consulta vigente; el guardado no cambia.
    c = {**a, "nombre": "1. Serie · 2027-07 · 11 meses", "consulta_horizonte": {"periodo": "2028-07"}}
    assert nombre_vigente(c) == "1. Serie · 2028-07 · 23 meses" and c["nombre"].endswith("11 meses")
    assert nombre_vigente({**c, "consulta_horizonte": None}) == "1. Serie · 2027-07 · 11 meses"
    print("ok")
