"""Fase 1A (AS-006): pruebas del selector de modelo REALMENTE usado en producción.

Ruta productiva (verificada por traza dinámica, docs/fase_v112_antislop_01a_pruebas/01):
    ejecutar_proyeccion → _ejecutar_proyeccion_base → _matriz_rectangular_12_24 → _seleccionar_modelo_rectangular

Las propiedades que protegían el selector retirado `seleccionar_modelo_por_rmse_oos_global`
(test_seleccion_rmse_global, test_p0d_rmse_orden_exacto, test_rmse_global_estable) se verifican aquí sobre el
selector vigente con bancos artificiales explícitos. El defecto AS-001, registrado como xfail estricto en la Fase 1A,
se corrige en la Fase 1B: las pruebas `test_as001_*` pasan sin marcador."""

import math
import sys
from decimal import Decimal, localcontext
from fractions import Fraction
from unittest.mock import patch

import pytest

from app_icociv.proyeccion import servicio_proyeccion as sp
from tests.fixtures.fase0 import generadores as gen

SELECTOR = sp._seleccionar_modelo_rectangular


def _matriz(errores: dict[str, dict[tuple[int, int], float]], w_estrella: int, horizontes: int) -> dict:
    """Matriz mínima con la forma que produce `_matriz_rectangular_12_24`: (error, observado, predicho, escala)."""
    datos = {m: {par: (float(e), 100.0, 100.0 - float(e), 1.0) for par, e in pares.items()} for m, pares in errores.items()}
    return {"datos": datos, "w_estrella": w_estrella, "horizontes": tuple(range(1, horizontes + 1))}


def _banco(**candidatos: list[float]) -> tuple[dict, tuple[str, ...]]:
    """Cada candidato con la misma lista de errores por par (o, h): orígenes 12.., un horizonte por posición."""
    n = len(next(iter(candidatos.values())))
    pares = [(12, h) for h in range(1, n + 1)]
    return _matriz({m: dict(zip(pares, e)) for m, e in candidatos.items()}, 1, n), tuple(candidatos)


# ------------------------------------------------------------------ propiedades (selector como parámetro)
def p_minimo_sse(sel):
    m, mod = _banco(a=[1.0, 2.0, 3.0], b=[1.0, 1.0, 1.0], c=[0.5, 2.5, 0.5])
    return sel(m, mod)["modelo"] == "b"


def p_rmse_coherente(sel):
    m, mod = _banco(a=[3.0, 4.0], b=[1.0, 1.0], c=[2.0, 2.0])
    r = sel(m, mod)
    return (math.isclose(r["rmse_seleccion_oos"], 1.0) and r["modelo_segundo"] == "c" and math.isclose(r["rmse_segundo_oos"], 2.0)
            and math.isclose(r["diferencia_absoluta"], 1.0) and math.isclose(r["diferencia_porcentual"], 100.0))


def p_sse_exacto_decide_una_ulp(sel):
    # En flotante 1e16 + 1 == 1e16 + 0.81 == 1e16: solo la suma exacta distingue. Gana b (SSE menor por 0,19).
    m, mod = _banco(a=[1e8, 1.0], b=[1e8, 0.9])
    return sel(m, mod)["modelo"] == "b"


def p_empate_primer_candidato_del_banco(sel):
    m, mod = _banco(x=[1.0, -2.0], y=[2.0, 1.0], z=[-1.0, 2.0])  # SSE idéntico (5) en los tres
    return sel(m, mod)["modelo"] == "x" and sel(m, ("z", "y", "x"))["modelo"] == "z"


def p_pesos_uniformes_por_horizonte(sel):
    # a falla en h=1 y b en h=2 con el mismo tamaño: empate exacto -> primero del banco; si se ponderara 1/h,
    # el error de b (h=2) pesaría la mitad y ganaría b.
    m, mod = _banco(a=[2.0, 0.0], b=[0.0, 2.0])
    return sel(m, mod)["modelo"] == "a"


def p_solo_pares_comunes(sel):
    # b no tiene el par (12, 3), donde a falla mucho: la muestra común son (12,1) y (12,2) y ahí gana a.
    m = _matriz({"a": {(12, 1): 0.1, (12, 2): 0.1, (12, 3): 50.0}, "b": {(12, 1): 1.0, (12, 2): 1.0}}, 1, 3)
    r = sel(m, ("a", "b"))
    return r["modelo"] == "a" and r["pares_comunes"] == 2 and r["pares_esperados"] == 3


def p_invariante_al_orden_de_entrada(sel):
    base = {"a": [3.0, 1.0, 2.0], "b": [1.0, 1.5, 1.0], "c": [2.0, 2.0, 0.1]}
    m, mod = _banco(**base)
    referencia = sel(m, mod)
    invertido = _matriz({k: dict(reversed(list(v.items()))) for k, v in
                         {kk: dict(zip([(12, h) for h in (1, 2, 3)], e)) for kk, e in base.items()}.items()}, 1, 3)
    return all(sel(mm, orden)["modelo"] == referencia["modelo"] for mm in (m, invertido)
               for orden in (mod, tuple(reversed(mod)), ("c", "a", "b")))


PROPIEDADES = [p_minimo_sse, p_rmse_coherente, p_sse_exacto_decide_una_ulp, p_empate_primer_candidato_del_banco,
               p_pesos_uniformes_por_horizonte, p_solo_pares_comunes, p_invariante_al_orden_de_entrada]


@pytest.mark.parametrize("propiedad", PROPIEDADES, ids=lambda f: f.__name__)
def test_selector_vigente_cumple(propiedad):
    assert propiedad(SELECTOR)


# ------------------------------------------------------------------ casos de borde del contrato vigente
def test_sin_muestra_comun_o_banco_vacio_devuelve_none():
    assert SELECTOR(_matriz({"a": {(12, 1): 1.0}, "b": {(12, 2): 1.0}}, 1, 2), ("a", "b")) is None
    assert SELECTOR({"datos": {}, "w_estrella": 1, "horizontes": (1,)}, ()) is None


def test_un_error_no_finito_excluye_solo_a_ese_candidato():
    for malo in (math.inf, -math.inf, math.nan):
        m, mod = _banco(a=[malo, 0.1], b=[1.0, 1.0])
        r = SELECTOR(m, mod)
        assert r["modelo"] == "b" and r["modelo_segundo"] is None and math.isclose(r["rmse_seleccion_oos"], 1.0)


def test_candidato_sano_gana_frente_a_divergente_en_rango_representable():
    # 1e150 al cuadrado (1e300) cabe en float: el selector vigente lo ordena bien y no aborta.
    m, mod = _banco(divergente=[1e150, 1e150], sano=[1.0, 2.0])
    r = SELECTOR(m, mod)
    assert r["modelo"] == "sano" and r["modelo_segundo"] == "divergente" and math.isfinite(r["rmse_segundo_oos"])


def test_es_reproducible_y_no_muta_la_matriz():
    m, mod = _banco(a=[1.0, 2.0], b=[2.0, 0.5])
    copia = {k: dict(v) for k, v in m["datos"].items()}
    assert SELECTOR(m, mod) == SELECTOR(m, mod) and m["datos"] == copia


def test_rmse_reportado_coincide_con_sse_exacto():
    errores = [0.1, 0.2, 0.30000000000000004, 1e-12, 7.5]
    m, mod = _banco(a=errores, b=[e * 2 for e in errores])
    sse = sum(Fraction(e) ** 2 for e in errores)
    assert SELECTOR(m, mod)["rmse_seleccion_oos"] == math.sqrt(float(sse) / len(errores))


# ------------------------------------------------------------------ AS-001 (corregido en la Fase 1B)
# El SSE exacto de errores finitos enormes no cabe en float; el RMSE sí (RMSE <= max|e| <= DBL_MAX). La selección
# sigue ordenando por SSE exacto y el RMSE informado debe ser finito, sin excepción. Todas pasan por SELECTOR, de
# modo que contra el código anterior a la corrección fallan con OverflowError (evidencia en docs/fase_v112_antislop_01b_as001).
MAXIMO = sys.float_info.max


def _rmse_referencia(errores: list[float]) -> float:
    """sqrt(SSE/n) desde la fracción exacta con Decimal a 100 dígitos: referencia independiente del selector."""
    sse = sum(Fraction(e) ** 2 for e in errores)
    with localcontext() as ctx:
        ctx.prec = 100
        return float((Decimal(sse.numerator) / Decimal(sse.denominator) / len(errores)).sqrt())


def _a_una_ulp(valor: float, referencia: float) -> bool:
    return abs(valor - referencia) <= math.ulp(referencia)


def test_as001_candidato_divergente_no_aborta_la_seleccion():
    # Errores finitos del orden del hallazgo (1,2258e240): su cuadrado (~1,5e480) no cabe en float.
    m, mod = _banco(divergente=[1.2258e240, 1.2258e240], sano=[1.0, 2.0])
    r = SELECTOR(m, mod)
    assert r["modelo"] == "sano" and r["modelo_segundo"] == "divergente"
    assert r["rmse_seleccion_oos"] == math.sqrt(2.5) and r["rmse_segundo_oos"] == 1.2258e240
    assert math.isfinite(r["diferencia_absoluta"]) and math.isfinite(r["diferencia_porcentual"])
    assert r["diferencia_absoluta"] == 1.2258e240 - math.sqrt(2.5)


def test_as001_dos_candidatos_enormes_ordenados_por_sse_exacto_y_rmse_preciso():
    errores = {"a": [1.2258e240, 1e240, -3e239], "b": [1.2258e240, 1.1e240, -3e239], "c": [1e300, 1e300, 1e300]}
    m, mod = _banco(**errores)
    r = SELECTOR(m, mod)
    assert (r["modelo"], r["modelo_segundo"]) == ("a", "b")
    assert _a_una_ulp(r["rmse_seleccion_oos"], _rmse_referencia(errores["a"]))
    assert _a_una_ulp(r["rmse_segundo_oos"], _rmse_referencia(errores["b"]))
    assert r["diferencia_absoluta"] > 0 and math.isfinite(r["diferencia_porcentual"])


def test_as001_empate_exacto_a_escala_extrema_gana_el_primero_del_banco():
    m, mod = _banco(x=[1e300, -2e300], y=[-2e300, 1e300], z=[1e300, 2e300])  # SSE idéntico (5e600) en los tres
    assert SELECTOR(m, mod)["modelo"] == "x" and SELECTOR(m, ("z", "y", "x"))["modelo"] == "z"
    r = SELECTOR(m, mod)
    assert r["rmse_seleccion_oos"] == r["rmse_segundo_oos"] and r["diferencia_absoluta"] == 0.0 == r["diferencia_porcentual"]


def test_as001_una_ulp_en_el_borde_de_dbl_max():
    # Errores de ~1,7976e308: el SSE exacto distingue una ULP y el RMSE de cada uno es exactamente su error.
    menor = math.nextafter(MAXIMO, 0.0)
    m, mod = _banco(a=[MAXIMO] * 3, b=[menor] * 3)
    r = SELECTOR(m, mod)
    assert (r["modelo"], r["modelo_segundo"]) == ("b", "a")
    assert r["rmse_seleccion_oos"] == menor and r["rmse_segundo_oos"] == MAXIMO
    assert r["diferencia_absoluta"] == math.ulp(menor)


def test_as001_errores_no_finitos_siguen_excluidos_junto_a_enormes():
    m, mod = _banco(infinito=[math.inf, 0.1], nan=[math.nan, 0.1], enorme=[1.2258e240, 1.0], sano=[1.0, 1.0])
    r = SELECTOR(m, mod)
    assert (r["modelo"], r["modelo_segundo"]) == ("sano", "enorme") and math.isfinite(r["rmse_segundo_oos"])


def test_as001_muestra_comun_y_pesos_uniformes_a_escala_extrema():
    # b no tiene el par (12, 3), donde a tiene un error enorme: no cuenta y gana a en la muestra común.
    m = _matriz({"a": {(12, 1): 1e200, (12, 2): 1e200, (12, 3): 1e308}, "b": {(12, 1): 1e201, (12, 2): 1e201}}, 1, 3)
    r = SELECTOR(m, ("a", "b"))
    assert r["modelo"] == "a" and r["pares_comunes"] == 2 and r["pares_esperados"] == 3 and r["rmse_seleccion_oos"] == 1e200
    # Mismo error enorme en h=1 o en h=2: empate exacto (pesos uniformes) -> primero del banco.
    m, mod = _banco(a=[2e200, 0.0], b=[0.0, 2e200])
    assert SELECTOR(m, mod)["modelo"] == "a"


@pytest.mark.parametrize("escala", [1e-150, 1e-20, 1e-3, 1.0, 37.5, 1e6, 1e50, 1e150])
def test_as001_rango_ordinario_rmse_identico_bit_a_bit(escala):
    # En el rango ordinario el RMSE informado es la expresión de siempre, sin ningún cambio de redondeo.
    a = [escala * f for f in (0.1, -0.7, 2.3, 1e-3, -1.9, 0.30000000000000004)]
    b = [e * 3 for e in a]
    m, mod = _banco(a=a, b=b)
    r = SELECTOR(m, mod)
    assert r["rmse_seleccion_oos"] == math.sqrt(float(sp._sse_exacto(a)) / len(a))
    assert r["rmse_segundo_oos"] == math.sqrt(float(sp._sse_exacto(b)) / len(b))


def test_as001_diferencia_porcentual_no_representable_es_inf_y_los_consumidores_la_omiten():
    # Ganador con RMSE diminuto y segundo enorme: la razón (~1e400) no cabe en float. La división flotante devuelve
    # inf sin excepción; el contrato no cambia y los consumidores ya tratan los no finitos como "no disponible".
    from app_icociv.interfaz.presentacion_resultados import formatear_porcentaje
    from app_icociv.persistencia.gestor_sesiones import _convertir_json_seguro
    from app_icociv.reportes.modelo import es_numero

    m, mod = _banco(fino=[1e-100, 1e-100], enorme=[1e300, 1e300])
    r = SELECTOR(m, mod)
    assert r["modelo"] == "fino" and math.isfinite(r["rmse_segundo_oos"]) and math.isfinite(r["diferencia_absoluta"])
    assert r["diferencia_porcentual"] == math.inf
    assert formatear_porcentaje(r["diferencia_porcentual"]) == "No disponible"
    assert not es_numero(r["diferencia_porcentual"]) and _convertir_json_seguro(r["diferencia_porcentual"]) is None


def test_as001_ruta_productiva_con_21_candidatos_y_uno_divergente():
    # Un candidato que no es ganador ni segundo pasa a tener errores de 1,2258e240 en todos los pares: la proyección
    # completa no aborta y el ganador, el segundo, sus RMSE y la trayectoria de 24 meses son idénticos.
    serie = gen.serie("tendencia_lineal_ruido")
    original = sp._matriz_rectangular_12_24
    with patch.object(sp, "_matriz_rectangular_12_24", wraps=original) as espia:
        base = sp.ejecutar_proyeccion(serie, *gen.objetivo(serie, 11), 2020)
    modelos = espia.call_args.args[1]
    elegido = next(c for c in modelos if c not in (base["modelo_codigo"], base["modelo_segundo"]))

    def con_divergente(*args, **kwargs):
        matriz = original(*args, **kwargs)
        matriz["datos"][elegido] = {par: (1.2258e240,) + fila[1:] for par, fila in matriz["datos"][elegido].items()}
        return matriz

    assert len(modelos) == 21
    # Con el divergente, cambiar el horizonte consultado (11, 1 o 24 meses) no cambia la selección ni la trayectoria
    # y cada ejecución llama una sola vez al selector rectangular.
    for h in (11, 1, 24):
        with patch.object(sp, "_matriz_rectangular_12_24", side_effect=con_divergente), \
             patch.object(sp, "_seleccionar_modelo_rectangular", wraps=SELECTOR) as vigente:
            r = sp.ejecutar_proyeccion(serie, *gen.objetivo(serie, h), 2020)
        assert vigente.call_count == 1, h
        for clave in ("modelo_codigo", "rmse_seleccion_oos", "modelo_segundo", "rmse_segundo_oos", "trayectoria_24_meses"):
            assert r[clave] == base[clave], (h, clave)


# ------------------------------------------------------------------ sensibilidad: el conjunto detecta mutantes
def _referencia(matriz, modelos, *, flotante=False, ultimo_en_empate=False, peso_1_h=False, todos_los_pares=False, rmse_sin_n=False):
    """Reimplementación del contrato con UN defecto activable, para comprobar que las propiedades lo detectan.
    No reemplaza ni parchea el selector productivo."""
    datos = matriz["datos"]
    comunes = set.intersection(*(set(datos[m]) for m in modelos)) if modelos else set()
    filas = []
    for m in modelos:
        pares = sorted(datos[m]) if todos_los_pares else sorted(comunes)
        valores = [datos[m][p][0] for p in pares]
        if not valores or not all(math.isfinite(v) for v in valores):
            continue
        pesos = [1 / p[1] if peso_1_h else 1 for p in pares]
        sse = sum(w * v * v for w, v in zip(pesos, valores)) if flotante else sum(Fraction(w) * Fraction(v) ** 2 for w, v in zip(pesos, valores))
        filas.append((m, sse, math.sqrt(float(sse) / (1 if rmse_sin_n else len(valores)))))
    if not filas:
        return None
    filas.sort(key=lambda x: x[1], reverse=False)
    if ultimo_en_empate:
        minimo = filas[0][1]
        empatados = [f for f in filas if f[1] == minimo]
        filas = [empatados[-1]] + [f for f in filas if f is not empatados[-1]]
    (g, _, rg), seg = filas[0], (filas[1] if len(filas) > 1 else (None, None, None))
    return {"modelo": g, "rmse_seleccion_oos": rg, "modelo_segundo": seg[0], "rmse_segundo_oos": seg[2],
            "diferencia_absoluta": None if seg[2] is None else seg[2] - rg,
            "diferencia_porcentual": None if seg[2] is None else (seg[2] - rg) / rg * 100 if rg else float("nan"),
            "pares_comunes": len(comunes), "pares_esperados": int(matriz["w_estrella"]) * len(matriz["horizontes"])}


MUTANTES = {"suma_flotante": {"flotante": True}, "ultimo_en_empate": {"ultimo_en_empate": True},
            "peso_1_h": {"peso_1_h": True}, "todos_los_pares": {"todos_los_pares": True}, "rmse_sin_n": {"rmse_sin_n": True}}


def test_la_referencia_sin_defectos_cumple_todas_las_propiedades():
    assert all(p(_referencia) for p in PROPIEDADES)


@pytest.mark.parametrize("mutante", list(MUTANTES))
def test_cada_mutante_es_detectado(mutante):
    selector = lambda m, mod: _referencia(m, mod, **MUTANTES[mutante])  # noqa: E731
    fallan = [p.__name__ for p in PROPIEDADES if not p(selector)]
    assert fallan, f"ninguna propiedad detecta el mutante {mutante}"


# ------------------------------------------------------------------ integración con la ruta productiva
def test_la_ruta_productiva_usa_el_selector_rectangular_y_ningun_selector_retirado():
    serie = gen.serie("tendencia_lineal_ruido")
    anio, mes = gen.objetivo(serie, 11)
    retirados = ("seleccionar_modelo_por_rmse_oos_global", "_rmse_global_estable", "_modelo_consistente_desde_comparativo",
                 "_modelo_trayectoria_consistente", "determinar_horizonte_maximo_estadistico", "_evaluar_horizontes_proyeccion")
    espias = {n: patch.object(sp, n, wraps=getattr(sp, n)) for n in retirados}
    with patch.object(sp, "_seleccionar_modelo_rectangular", wraps=SELECTOR) as vigente, \
         patch.object(sp, "_matriz_rectangular_12_24", wraps=sp._matriz_rectangular_12_24) as matriz:
        activos = {n: p.start() for n, p in espias.items()}
        try:
            r = sp.ejecutar_proyeccion(serie, anio, mes, 2020)
        finally:
            for p in espias.values():
                p.stop()
    assert vigente.call_count == 1 and matriz.call_count == 1
    assert {n: m.call_count for n, m in activos.items()} == dict.fromkeys(retirados, 0)
    m_rect, modelos = vigente.call_args.args
    seleccion = SELECTOR(m_rect, modelos)  # determinista: misma entrada, mismo resultado que en la corrida
    assert r["modelo_codigo"] == seleccion["modelo"] and r["rmse_seleccion_oos"] == seleccion["rmse_seleccion_oos"]
    # Conservación: 21 candidatos evaluados, 24 horizontes y muestra común completa W* × 24.
    assert len(modelos) == 21 and m_rect["horizontes"] == tuple(range(1, 25))
    assert seleccion["pares_comunes"] == seleccion["pares_esperados"] == m_rect["w_estrella"] * 24
