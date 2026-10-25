"""Fase 0 · Golden Master del motor estadístico.

Cinco series sintéticas (tests/fixtures/fase0/generadores.py) consultadas a H11 y H23 con el motor real:
modelo elegido entre los candidatos, RMSErect de todos ellos, segundo lugar, trayectoria H1..H24,
MAE(h)/RMSE(h) por horizonte, punto consultado y rechazos. Los esperados están congelados en
tests/fixtures/fase0/golden/motor.json (commit 6672529); esta prueba nunca los reescribe."""

from copy import deepcopy

import pytest

from tests.fixtures.fase0 import captura as c
from tests.fixtures.fase0 import generadores as gen

GOLDEN = c.leer_golden("motor.json")


def _cerca(a, b):
    return abs(a - b) <= max(c.ABS_TOL, c.REL_TOL * max(abs(a), abs(b)))


def _grupo_empatado(ranking):
    """Candidatos cuyo RMSErect coincide (dentro de la tolerancia) con el mínimo."""
    return {m for m, rmse in ranking if _cerca(rmse, ranking[0][1])}


@pytest.fixture(scope="module", params=list(gen.ESCENARIOS_MOTOR))
def capturado(request):
    return request.param, c.capturar_motor(request.param)


def test_consultas_h11_y_h23_comparten_modelo_y_trayectoria(capturado):
    _, obtenido = capturado
    h11, h23 = obtenido["consultas"]["11"], obtenido["consultas"]["23"]
    assert h11["comun"] == h23["comun"], "el horizonte consultado cambió el modelo, el ranking o la trayectoria"
    for h, consulta in obtenido["consultas"].items():
        assert consulta["y_proj"] == consulta["comun"]["trayectoria_24_meses"][int(h) - 1]
        assert consulta["horizonte_solicitado"] == consulta["backtesting"]["horizonte"] == int(h)
        assert consulta["intervalos_publicados"] == [None] * 6  # intervalos no publicados (AS: documentado, no se toca)
        comun = consulta["comun"]
        assert len(comun["trayectoria_24_meses"]) == 24 and [f[0] for f in comun["tabla_horizontes"]] == list(range(1, 25))
        assert comun["modelo_codigo"] in _grupo_empatado(comun["ranking_rmse_rect"])
        assert comun["pares_comunes"] == comun["pares_esperados"] == comun["w_estrella"] * 24


def test_golden_motor(capturado):
    nombre, obtenido = deepcopy(capturado)
    esperado = deepcopy(GOLDEN["escenarios"][nombre])
    for consulta in ("11", "23"):
        e, o = esperado["consultas"][consulta]["comun"], obtenido["consultas"][consulta]["comun"]
        empate = _grupo_empatado(e["ranking_rmse_rect"])
        if len(empate) > 1:
            # Empate exacto (serie sin ruido): manda el desempate documentado -primer candidato del banco
            # entre los de SSE mínimo-. Un error de 1e-15 en otra CPU puede romper el empate exacto; por eso se
            # exige que el ganador siga en el grupo empatado del golden y sea el mínimo obtenido.
            assert o["modelo_codigo"] in empate and o["modelo_codigo"] == o["ranking_rmse_rect"][0][0]
            for clave in ("modelo_codigo", "model_name", "modelo_segundo"):
                e.pop(clave), o.pop(clave)
        rank_e, rank_o = dict(e.pop("ranking_rmse_rect")), dict(o.pop("ranking_rmse_rect"))
        assert set(rank_e) == set(rank_o)
        # Candidatos con optimizador iterativo: holgura documentada en captura.REL_TOL_OPTIMIZADOR.
        for optimizador, rel, abs_ in ((False, c.REL_TOL, c.ABS_TOL), (True, c.REL_TOL_OPTIMIZADOR, c.ABS_TOL_OPTIMIZADOR)):
            parte = [m for m in rank_e if c.es_optimizador(m) == optimizador]
            c.afirmar_igual({m: rank_e[m] for m in parte}, {m: rank_o[m] for m in parte},
                            f"{nombre}.h{consulta}.ranking", rel_tol=rel, abs_tol=abs_)
        pos = {m: i for i, m in enumerate(rank_o)}  # el dict conserva el orden del ranking obtenido

        def separados(a, b):
            rel = c.REL_TOL_OPTIMIZADOR if c.es_optimizador(a) or c.es_optimizador(b) else c.REL_TOL
            return rank_e[b] - rank_e[a] > max(rel * rank_e[b], c.ABS_TOL_OPTIMIZADOR)
        invertidos = [(a, b) for a in rank_e for b in rank_e if separados(a, b) and pos[a] > pos[b]]
        assert not invertidos, f"orden del RMSErect distinto del golden: {invertidos[:5]}"
    c.afirmar_igual(esperado, obtenido, nombre)


def test_golden_rechazos():
    c.afirmar_igual(GOLDEN["rechazos"], c.capturar_rechazos(), "rechazos")
