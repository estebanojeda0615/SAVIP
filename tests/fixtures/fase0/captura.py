"""Fase 0: captura del comportamiento observable de SAVIP para compararlo con los Golden Masters.

Las mismas funciones sirven a ``generar_golden.py`` (que escribe ``golden/*.json`` una sola vez sobre el
código congelado) y a las pruebas (que solo leen). Ninguna sustituye el algoritmo: el motor, las reglas
económicas y los exportables se ejecutan reales; los espías ``wraps=`` solo observan argumentos."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from unittest.mock import patch

from app_icociv.proyeccion import servicio_proyeccion as sp
from app_icociv.servicios import actualizacion_icociv as act
from app_icociv.servicios import empalme_iccp_icociv as emp
from tests.fixtures.fase0 import generadores as gen

GOLDEN = Path(__file__).resolve().parent / "golden"
#: Tolerancia de los flotantes: el lock fija las versiones, pero los núcleos BLAS/LAPACK de numpy/scipy
#: eligen rutas SIMD según la CPU (AVX2/AVX-512) y pueden diferir en los últimos bits (~1e-15 relativo).
#: 1e-9 relativo deja seis órdenes de margen sobre ese ruido y queda muy por debajo de lo que la
#: aplicación muestra (2 a 4 decimales). Textos, códigos, enteros, booleanos y órdenes: exactos.
REL_TOL, ABS_TOL = 1e-9, 1e-12
#: Candidatos ajustados con un optimizador iterativo (Holt lineal/amortiguado vía statsmodels, Huber vía
#: scikit-learn, y sus variantes Fourier): su resultado solo está determinado hasta la tolerancia de
#: convergencia, y la ruta SIMD de cada CPU la recorre distinto. Medido frente al equipo de referencia en
#: runners de GitHub: run 40240413329 hasta 5e-7 en RMSErect y 3,5e-5 en MAE/MASE impresos; run 40258877105
#: hasta 1,2e-3 (Holt amortiguado: 6,2673 frente a 6,2750). Se admite 1e-2 relativo (≈8 veces lo observado)
#: para ellos y para las métricas impresas en PDF/DOCX; ningún modelo ganador, trayectoria, punto consultado
#: ni cifra económica necesitó holgura (siguen a 1e-9).
REL_TOL_OPTIMIZADOR, ABS_TOL_OPTIMIZADOR = 1e-2, 1e-8
FAMILIAS_OPTIMIZADOR = ("holt", "huber")
HORIZONTES_CONSULTA = (11, 23)


def es_optimizador(codigo: str) -> bool:
    return any(f in codigo for f in FAMILIAS_OPTIMIZADOR)


_NUMERO_TEXTO = re.compile(r"^-?(\d{1,3}(\.\d{3})+|\d+)(,(\d+))?$")


def _numero_texto(token: str) -> tuple[float, int] | None:
    """«2,0026» o «1.234,5» → (valor, decimales); None si el token no es un número en formato es-CO."""
    m = _NUMERO_TEXTO.match(token)
    if not m:
        return None
    return float(token.replace(".", "").replace(",", ".")), len(m.group(4) or "")


def textos_numericos_equivalentes(e: str, o: str) -> bool:
    """Mismo texto salvo métricas impresas con 3+ decimales que difieren en ≤ REL_TOL_OPTIMIZADOR relativo o 1 unidad del último decimal."""
    te, to = e.split(), o.split()
    if len(te) != len(to):
        return False
    for a, b in zip(te, to):
        if a == b:
            continue
        na, nb = _numero_texto(a), _numero_texto(b)
        if na is None or nb is None or na[1] != nb[1]:
            return False
        # Solo las métricas impresas con 3+ decimales (MAE, RMSE, MASE…) admiten holgura; importes (2 decimales),
        # porcentajes, páginas y recuentos deben coincidir exactos.
        if na[1] < 3 or abs(na[0] - nb[0]) > max(REL_TOL_OPTIMIZADOR * max(abs(na[0]), abs(nb[0])), 10 ** -na[1] + 1e-12):
            return False
    return True


# ----------------------------------------------------------------------------------- comparación
def diferencias(esperado, obtenido, ruta="$", limite=25, rel_tol=REL_TOL, abs_tol=ABS_TOL, texto_numerico=False) -> list[str]:
    """Lista de diferencias (vacía si coinciden) con la tolerancia documentada para flotantes.
    ``texto_numerico``: en textos de PDF/DOCX, los números impresos se comparan con ``textos_numericos_equivalentes``."""
    salida: list[str] = []

    def rec(e, o, r):
        if len(salida) >= limite:
            return
        if isinstance(e, bool) or isinstance(o, bool) or e is None or o is None or isinstance(e, str):
            if e != o or type(e) is not type(o):
                if not (texto_numerico and isinstance(e, str) and isinstance(o, str) and textos_numericos_equivalentes(e, o)):
                    salida.append(f"{r}: esperado {e!r}, obtenido {o!r}")
        elif isinstance(e, (int, float)) and isinstance(o, (int, float)):
            if isinstance(e, int) and isinstance(o, int):
                if e != o:
                    salida.append(f"{r}: esperado {e}, obtenido {o}")
            elif not (math.isclose(e, o, rel_tol=rel_tol, abs_tol=abs_tol) or (math.isnan(e) and math.isnan(o))):
                salida.append(f"{r}: esperado {e!r}, obtenido {o!r}")
        elif isinstance(e, dict) and isinstance(o, dict):
            if set(e) != set(o):
                salida.append(f"{r}: claves distintas; faltan {sorted(set(e) - set(o))[:8]}, sobran {sorted(set(o) - set(e))[:8]}")
            for k in e:
                if k in o:
                    rec(e[k], o[k], f"{r}.{k}")
        elif isinstance(e, list) and isinstance(o, list):
            if len(e) != len(o):
                salida.append(f"{r}: longitud esperada {len(e)}, obtenida {len(o)}")
            for i, (a, b) in enumerate(zip(e, o)):
                rec(a, b, f"{r}[{i}]")
        else:
            salida.append(f"{r}: tipos distintos {type(e).__name__} / {type(o).__name__}")

    rec(esperado, obtenido, ruta)
    return salida


def afirmar_igual(esperado, obtenido, ruta="$", **opciones) -> None:
    """``assert`` con la lista completa de diferencias en el mensaje (pytest trunca las listas largas)."""
    lista = diferencias(esperado, obtenido, ruta, **opciones)
    assert not lista, f"{len(lista)} diferencia(s) con el golden:\n" + "\n".join(lista)


def json_estable(objeto):
    """Ida y vuelta por JSON: tuplas → listas, NaN → None, claves en texto (lo que guarda el golden)."""
    def limpio(x):
        if isinstance(x, float) and not math.isfinite(x):
            return None
        if isinstance(x, dict):
            return {str(k): limpio(v) for k, v in x.items()}
        if isinstance(x, (list, tuple)):
            return [limpio(v) for v in x]
        if hasattr(x, "item"):  # escalares numpy
            return limpio(x.item())
        return x
    return json.loads(json.dumps(limpio(objeto), ensure_ascii=False))


def leer_golden(nombre: str) -> dict:
    return json.loads((GOLDEN / nombre).read_text(encoding="utf-8"))


# ----------------------------------------------------------------------------------- motor
def _ranking(matriz, modelos) -> list[list]:
    """RMSErect de TODOS los candidatos sobre la muestra común, ordenado como lo ordena la selección
    (SSE exacto con Fraction; ante empate exacto, orden del banco por estabilidad del sort)."""
    datos = matriz["datos"]
    comunes = set.intersection(*(set(datos.get(m, {})) for m in modelos))
    filas = []
    for m in modelos:
        valores = [datos[m][par][0] for par in comunes]
        sse = sp._sse_exacto(valores)
        filas.append((m, sse, math.sqrt(float(sse) / len(valores))))
    filas.sort(key=lambda x: x[1])
    return [[m, rmse] for m, _, rmse in filas]


def capturar_motor(nombre: str) -> dict:
    df = gen.serie(nombre)
    salida = {"n": len(df), "ultimo_periodo": df["Periodo"].iloc[-1], "consultas": {}}
    for h in HORIZONTES_CONSULTA:
        anio, mes = gen.objetivo(df, h)
        with patch.object(sp, "_seleccionar_modelo_rectangular", wraps=sp._seleccionar_modelo_rectangular) as espia:
            r = sp.ejecutar_proyeccion(df, anio, mes, 2020)
        matriz, modelos = espia.call_args.args
        info = r["horizonte_info"]
        comun = {
            "proyeccion_generada": r["proyeccion_generada"],
            "modelo_codigo": r["modelo_codigo"], "model_name": r["model_name"],
            "modelo_segundo": r["modelo_segundo"], "rmse_seleccion_oos": r["rmse_seleccion_oos"],
            "rmse_segundo_oos": r["rmse_segundo_oos"], "diferencia_porcentual_segundo": r["diferencia_porcentual_segundo"],
            "w_estrella": info["w_estrella"], "pares_comunes": info["pares_comunes"], "pares_esperados": info["pares_esperados"],
            "candidatos_evaluados": list(modelos),
            "ranking_rmse_rect": _ranking(matriz, modelos),
            "trayectoria_24_meses": list(r["trayectoria_24_meses"]),
            "tabla_horizontes": [[f["horizonte"], f["W"], f["rmse"], f["mae"]] for f in info["tabla_horizontes"]],
        }
        bt = r["backtesting"]
        salida["consultas"][str(h)] = {
            "comun": comun,
            "periodo_proj": r["periodo_proj"], "horizonte_solicitado": r["horizonte_solicitado"],
            "y_proj": r["y_proj"], "factor_actualizacion": r["factor_actualizacion"],
            "variacion_acumulada": r["variacion_acumulada"],
            "backtesting": {"horizonte": bt["horizonte"], "iteraciones": bt["iteraciones"],
                            "rmse": bt["metricas"]["rmse"], "mae": bt["metricas"]["mae"]},
            "intervalos_publicados": [r[k] for k in ("ci_lo", "ci_hi", "ci80_lo", "ci80_hi", "ci95_lo", "ci95_hi")],
        }
    return json_estable(salida)


def capturar_rechazos() -> dict:
    nombre, _ = gen.ESCENARIO_INSUFICIENTE
    df = gen.serie(nombre)
    anio, mes = gen.objetivo(df, 11)
    r = sp.ejecutar_proyeccion(df, anio, mes, 2020)
    horizontes = {}
    for valor in (24, "12", 25, 0, -1, "1.5", 1.5, "", None, True, "abc"):
        try:
            horizontes[repr(valor)] = ["aceptado", sp.validar_horizonte_solicitado(valor)]
        except ValueError as exc:
            horizontes[repr(valor)] = ["rechazado", str(exc)]
    return json_estable({
        nombre: {"n": len(df), "proyeccion_generada": r["proyeccion_generada"], "model_name": r["model_name"],
                 "explicacion": r["explicacion"], "w_estrella": r["horizonte_info"]["w_estrella"],
                 "historia_suficiente_12_24": r["horizonte_info"]["historia_suficiente_12_24"], "y_proj": r.get("y_proj")},
        "validar_horizonte_solicitado": horizontes,
    })


# ----------------------------------------------------------------------------------- económico
def _sin_reloj(d: dict) -> dict:
    return {k: v for k, v in d.items() if k != "fecha_calculo"}


def capturar_economico() -> dict:
    factores = []
    for i, i0 in gen.VECTORES_FACTOR:
        p, f = act.factor_aplicado(i, i0)
        factores.append({"I": i, "I0": i0, "p": str(p), "F": str(f), "con_base_1000": act.aplicar_factor(1000.0, i, i0)})
    importes = []
    for precio, anticipo, i, i0, cantidad in gen.VECTORES_IMPORTE:
        entrada = {"precio_base": precio, "anticipo_amortizado": anticipo, "i0_icociv": i0, "i_icociv": i, "item": "Ítem sintético",
                   "unidad": "m3", "cantidad": cantidad, "horizonte": 11, "periodo_base": "2026_12", "periodo_proyectado": "2027_11"}
        importes.append(_sin_reloj(act.calcular_actualizacion_icociv(entrada)))
    rechazos = {}
    for nombre, entrada in {
        "precio_cero": {"precio_base": 0, "i0_icociv": 100, "i_icociv": 110},
        "i0_cero": {"precio_base": 1000, "i0_icociv": 0, "i_icociv": 110},
        "anticipo_igual_precio": {"precio_base": 1000, "anticipo_amortizado": 1000, "i0_icociv": 100, "i_icociv": 110},
        "anticipo_negativo": {"precio_base": 1000, "anticipo_amortizado": -1, "i0_icociv": 100, "i_icociv": 110},
        "indice_texto": {"precio_base": 1000, "i0_icociv": 100, "i_icociv": "x"},
        "indice_infinito": {"precio_base": 1000, "i0_icociv": 100, "i_icociv": float("inf")},
    }.items():
        try:
            act.calcular_actualizacion_icociv(entrada); rechazos[nombre] = "aceptado"
        except ValueError as exc:
            rechazos[nombre] = str(exc)
    legado = {"registro_sin_criterio": act.es_factor_legado({"factor_icociv": 1.1}),
              "registro_criterio_vigente": act.es_factor_legado({"criterio_factor": act.CRITERIO_FACTOR}),
              "criterio": act.CRITERIO_FACTOR, "texto_criterio": act.TEXTO_CRITERIO_FACTOR, "texto_legado": act.TEXTO_FACTOR_LEGADO}
    return json_estable({"factores": factores, "importes": importes, "rechazos": rechazos, "factor_legado": legado,
                         "empalme": capturar_empalme()})


ICOCIV_SINTETICO = {"2021_6": 95.5, "2021_12": 100.0, "2022_6": 112.345, "2023_12": 131.7, "2026_12": 158.204, "2027_11": 166.66}


def capturar_empalme() -> dict:
    total, canasta, grupo = "Total ICCP", "Materiales", "Pavimentaciones con asfalto"
    casos = {
        "empalme_completo_total": {"fecha_inicial": "2019-03", "fecha_final": "2026-12", "serie_iccp": total},
        "empalme_completo_canasta": {"fecha_inicial": "2020-07", "fecha_final": "2027-11", "canasta_general_iccp": canasta},
        "solo_iccp_grupo": {"fecha_inicial": "2018-01", "fecha_final": "2021-06", "grupo_obra_iccp": grupo},
        "solo_icociv": {"fecha_inicial": "2022-06", "fecha_final": "2027-11", "serie_iccp": total},
        "acero": {"calculo_acero": True, "p0": 4200.0, "ix": 5100.0, "q": 3.0, "fecha_inicial": "2020-01", "fecha_final": "2023-12",
                  "serie_iccp": total},
        "acero_sin_ix": {"calculo_acero": True, "p0": 4200.0, "fecha_inicial": "2020-01", "fecha_final": "2023-12", "serie_iccp": total},
        "error_fechas_invertidas": {"fecha_inicial": "2026-12", "fecha_final": "2020-01", "serie_iccp": total},
        "error_dos_series_iccp": {"fecha_inicial": "2019-03", "fecha_final": "2026-12", "canasta_general_iccp": canasta,
                                  "grupo_obra_iccp": grupo},
        "error_icociv_inexistente": {"fecha_inicial": "2022-06", "fecha_final": "2025-01", "serie_iccp": total},
        "error_serie_iccp_terminada_2020": {"fecha_inicial": "2019-03", "fecha_final": "2026-12", "canasta_general_iccp": "Costos indirectos"},
        "error_sin_serie_iccp": {"fecha_inicial": "2022-06", "fecha_final": "2027-11"},
    }
    salida = {"series_iccp": {"total": total, "canasta": canasta, "grupo": grupo}}
    for nombre, extra in casos.items():
        entrada = {"precio_base": 12500.75, "anticipo_amortizado": 1250.5, "ruta_icociv": "A16 > Grupo sintético",
                   "item": "Ítem empalme", **extra}
        try:
            salida[nombre] = _sin_reloj(emp.calcular_empalme_iccp_icociv(entrada, ICOCIV_SINTETICO))
        except ValueError as exc:
            salida[nombre] = {"error": str(exc)}
    return salida


# ----------------------------------------------------------------------------------- normalización de textos
_PATRONES = [
    (re.compile(r"SAVIP-INF-\d{8}-\d{6}"), "SAVIP-INF-<FECHA-HORA>"),
    (re.compile(r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?\b"), "<FECHA-HORA>"),
    (re.compile(r"\b\d{1,2}/\d{1,2}/\d{4}( \d{1,2}:\d{2}(:\d{2})?)?\b"), "<FECHA-HORA>"),
    # «25 de octubre de 2026, 14:02» (admite saltos de línea: en el PDF la celda puede partirla)
    (re.compile(r"\b\d{1,2}\s+de\s+[a-záéíóú]+\s+de\s+\d{4}(\s*(,|a\s+las)\s*\d{1,2}\s*:\s*\d{2}(\s*:\s*\d{2})?)?\b", re.I), "<FECHA-HORA>"),
    (re.compile(r"\b[0-9a-f]{32}\b"), "<ID>"),
    (re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"), "<ID>"),
]


def normalizar_texto(texto: str, rutas: tuple[str, ...] = (), reemplazos: tuple[tuple[str, str], ...] = ()) -> str:
    """Quita lo que cambia en cada ejecución: rutas temporales, identificadores aleatorios ya conocidos
    (``reemplazos``), fechas/horas e IDs hexadecimales; compacta espacios."""
    for viejo, nuevo in reemplazos:
        texto = texto.replace(viejo, nuevo)
    for ruta in rutas:
        for variante in {ruta, ruta.replace("\\", "/"), ruta.replace("/", "\\")}:
            texto = texto.replace(variante, "<TMP>")
    for patron, reemplazo in _PATRONES:
        texto = patron.sub(reemplazo, texto)
    return re.sub(r"[ \t ]+", " ", texto).strip()
