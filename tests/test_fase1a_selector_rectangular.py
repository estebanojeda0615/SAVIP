"""Fase 1A (AS-006): pruebas del selector de modelo REALMENTE usado en producción.

Ruta productiva (verificada por traza dinámica, docs/fase_v112_antislop_01a_pruebas/01):
    ejecutar_proyeccion → _ejecutar_proyeccion_base → _matriz_rectangular_12_24 → _seleccionar_modelo_rectangular

Las propiedades que protegían el selector retirado `seleccionar_modelo_por_rmse_oos_global`
(test_seleccion_rmse_global, test_p0d_rmse_orden_exacto, test_rmse_global_estable) se verifican aquí sobre el
selector vigente con bancos artificiales explícitos. No se modifica el motor: el defecto AS-001 queda registrado
como xfail estricto (`test_as001_*`), que pasará a PASS —y obligará a quitar el marcador— cuando se corrija."""

import math
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


# ------------------------------------------------------------------ AS-001 (defecto conocido, NO corregido)
@pytest.mark.xfail(strict=True, raises=OverflowError,
                   reason="AS-001: _seleccionar_modelo_rectangular calcula el RMSE informativo con float(Fraction) y "
                          "lanza OverflowError si el SSE exacto de un candidato no cabe en float. Corrección autorizada "
                          "solo en la Fase 1B; al corregirla esta prueba pasará y el marcador xfail debe retirarse.")
def test_as001_candidato_divergente_no_aborta_la_seleccion():
    # Errores finitos del orden del hallazgo (1,2258e240): su cuadrado (~1,5e480) no cabe en float.
    m, mod = _banco(divergente=[1.2258e240, 1.2258e240], sano=[1.0, 2.0])
    r = SELECTOR(m, mod)
    # Contrato esperado tras la corrección: la selección (por SSE exacto) no cambia y no hay excepción.
    assert r["modelo"] == "sano" and r["modelo_segundo"] == "divergente"


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
