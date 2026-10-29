"""Fase 2C (AS-003): contratos de la ruta VIGENTE que hoy solo se afirman sobre el subsistema heredado.

Cada prueba ejerce `ejecutar_proyeccion` o una función alcanzable desde producción y pasa con el código heredado
presente o ausente: no lo importa ni lo invoca. Indica qué prueba sobre código heredado permitiría sustituir en la
Fase 2D (docs/fase_v112_antislop_02c_registro_historico/03_MATRIZ_MIGRACION_PRUEBAS.csv). Datos sintéticos y
deterministas.
"""
import ast
import inspect
import math
import re
import textwrap
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from app_icociv.estadistica.criterios import MIN_ITERACIONES_WF, MIN_ITERACIONES_WF_ESCENARIO
from app_icociv.proyeccion import servicio_proyeccion as sp
from tests.fixtures.fase0 import generadores as gen

#: Definiciones heredadas pendientes de la Fase 2D (inventario 01 de la Fase 2C, commit 2f70391), salvo los cuatro
#: auxiliares de nombre genérico de modelos_interpretables (_numero, _ratio, _fmt, _mejor_por), que tienen homónimos
#: ajenos al subsistema. Se citan como
#: texto: la prueba no exige que existan ni que falten.
HEREDADAS = (
    "tramo_evidencia_oos", "_backtesting_por_modelo_horizonte", "_tipo_uso_horizonte", "_estado_por_horizonte",
    "peor_que_benchmark_naive", "_comparacion_desde_backtesting", "_evaluar_horizontes_proyeccion",
    "_clasificar_evidencia_horizonte", "_errores_oos_por_par", "seleccionar_modelo_por_rmse_oos_global",
    "_puntaje_rmse_ponderado", "_aplicar_salvaguarda_benchmarks", "_seleccionar_horizonte_permitido",
    "determinar_horizonte_maximo_estadistico", "_serializar_evaluaciones_horizonte", "_item_horizonte_global",
    "_mayor_horizonte_con", "_mayor_horizonte_permitido", "_ultimo_horizonte_por_clasificacion",
    "_evidencia_horizonte", "_mensaje_horizonte_no_permitido", "seleccionar_modelo_por_evidencia",
    "_benchmark_dominante", "comparar_modelo_con_benchmarks", "resumir_ranking_backtesting",
    "_mejor_candidato_no_elegible", "_razones_descartes",
)
#: Ruta productiva vigente (Fase 1A) y sus auxiliares directos del rectángulo y de la estructura publicada.
RUTA_VIGENTE = ("ejecutar_proyeccion", "_ejecutar_proyeccion_base", "_matriz_rectangular_12_24",
                "_seleccionar_modelo_rectangular", "_metricas_horizonte_rectangular",
                "_backtesting_horizonte_desde_rectangulo", "_estructurar_resultado_horizontes")


def _serie(n: int, semilla: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(semilla)
    valores = 100.0 + 0.8 * np.arange(n) + rng.normal(0.0, 0.5, n)
    return pd.DataFrame({"Periodo": [f"{2020 + i // 12}_{i % 12 + 1}" for i in range(n)], "Indice": valores})


def _textos(objeto):
    if isinstance(objeto, dict):
        for v in objeto.values():
            yield from _textos(v)
    elif isinstance(objeto, (list, tuple)):
        for v in objeto:
            yield from _textos(v)
    elif isinstance(objeto, str):
        yield objeto


# W* = n − N0 − H + 1 con N0 = 12 y H = 24: n = 36, 37 → W* = 1, 2 (escasez); n = 41 → W* = 6 (= MIN_ITERACIONES_WF).
@pytest.mark.parametrize("n", [36, 37, 41])
def test_escasez_de_ventanas_entrega_el_punto_con_advertencia_y_sin_intervalo(n):
    """P0-G/P0-C sobre la ruta vigente: pocas ventanas OOS no cancelan el punto; se advierten y no se publica intervalo.

    Sustituiría: test_cierre_semantico_ps01_ps05::test_ps03_la_escasez_de_evidencia_no_equivale_a_su_inexistencia
    (sobre `tramo_evidencia_oos`), test_fundamentacion_metodologica::test_sin_ventanas_suficientes_el_punto_sigue_pero_
    el_intervalo_no y test_presentacion_resultados::test_iteraciones_insuficientes_limitan_el_intervalo_no_el_horizonte
    (ambas sobre `_clasificar_evidencia_horizonte`). La banda se sigue calculando como diagnóstico interno; lo que se
    comprueba es que no se publica (`_retirar_intervalo_de_publicacion`). El umbral vigente de la advertencia es
    MIN_ITERACIONES_WF (6), no el de los tramos heredados (MIN_ITERACIONES_WF_ESCENARIO, 3): ver
    02_REGISTRO_HISTORICO_METODOLOGICO.md.
    """
    df = _serie(n)
    r = sp.ejecutar_proyeccion(df, *gen.objetivo(df, 11), 2020)
    w = r["horizonte_info"]["w_estrella"]
    assert w == n - 36 + 1
    assert r["proyeccion_generada"] is True
    assert math.isfinite(r["y_proj"]) and len(r["trayectoria_24_meses"]) == 24
    assert all(math.isfinite(v) for v in r["trayectoria_24_meses"])
    assert [r[k] for k in ("ci_lo", "ci_hi", "ci80_lo", "ci80_hi", "ci95_lo", "ci95_hi")] == [None] * 6
    aviso = f"El backtesting de referencia tiene {w} ventanas de validación."
    con_aviso = [t for t in _textos(r) if aviso in t]
    if w < MIN_ITERACIONES_WF:
        assert con_aviso, f"W*={w}: falta la advertencia de escasez"
        # La advertencia niega la validación; no la afirma.
        assert all("no existe un mínimo metodológicamente sustentado para declarar validada" in t for t in con_aviso)
    else:
        assert not con_aviso, f"W*={w}: advertencia de escasez sin escasez"


def test_banda_no_construible_no_cancela_el_punto():
    """P0-G sobre la ruta vigente: si la banda no se puede construir, el punto finito se entrega igual.

    Con datos sintéticos la banda siempre es construible, así que se fuerza el fallo del componente real
    `_intervalos_prediccion` (ValueError, como hace cuando un paso no reúne errores OOS) y se ejerce la rama de
    `_ejecutar_proyeccion_base` que lo captura. El motivo queda como diagnóstico interno, no en las advertencias
    publicadas. Sustituiría la dirección 1 de test_vocabulario_vc::test_la_banda_ausente_no_bloquea_el_punto_pero_el_
    punto_no_finito_si y test_fundamentacion_metodologica::test_banda_no_valida_se_declara_sin_bloquear_el_punto
    (sobre `_clasificar_evidencia_horizonte`).
    """
    df = gen.serie("tendencia_lineal_ruido")
    referencia = sp.ejecutar_proyeccion(df, *gen.objetivo(df, 11), 2020)
    with patch.object(sp, "_intervalos_prediccion", side_effect=ValueError("paso sin errores fuera de muestra")):
        r = sp.ejecutar_proyeccion(df, *gen.objetivo(df, 11), 2020)
    assert r["proyeccion_generada"] is True
    assert r["modelo_codigo"] == referencia["modelo_codigo"] and r["y_proj"] == referencia["y_proj"]
    assert r["trayectoria_24_meses"] == referencia["trayectoria_24_meses"]
    assert [r[k] for k in ("ci_lo", "ci_hi", "ci95_lo", "ci95_hi")] == [None] * 4
    # El motivo no llega a ningún texto del objeto publicado (P0-C: se describe un objeto que no se entrega).
    assert not [t for t in _textos(r) if "paso sin errores fuera de muestra" in t]


def test_texto_evidencia_oos_tres_tramos_sin_vocabulario_de_validacion():
    """Redacción vigente del tamaño de la muestra OOS (`_texto_evidencia_oos`, alcanzable desde producción).

    Sustituiría la parte de vocabulario de test_cierre_semantico_ps01_ps05::test_ps03_… (sobre `tramo_evidencia_oos`):
    W = 0 es «sin evidencia», 1 ≤ W < MIN_ITERACIONES_WF_ESCENARIO es «muy limitada», el resto «disponible», y ningún
    tramo se llama validado ni certificado.
    """
    textos = {w: sp._texto_evidencia_oos(w) for w in (0, 1, MIN_ITERACIONES_WF_ESCENARIO - 1,
                                                       MIN_ITERACIONES_WF_ESCENARIO, 50)}
    assert textos[0].startswith("Sin evidencia fuera de muestra")
    for w in (1, MIN_ITERACIONES_WF_ESCENARIO - 1):
        assert "muy limitada" in textos[w] and f"(n={w})" in textos[w]
    for w in (MIN_ITERACIONES_WF_ESCENARIO, 50):
        assert textos[w] == f"Evidencia fuera de muestra disponible (n={w})."
    for w, texto in textos.items():
        assert not re.search(r"valid|certific", texto, re.IGNORECASE), (w, texto)
    assert sp._texto_evidencia_oos(None) == sp._texto_evidencia_oos("x") == textos[0]


def test_sin_errores_finitos_comunes_no_se_fabrica_un_modelo():
    """C-SEL-001 sin decisión: si ningún candidato tiene errores finitos comunes, no se entrega proyección.

    Sustituiría test_fundamentacion_metodologica::test_sin_evidencia_comparable_el_horizonte_no_se_entrega, que lo
    comprueba leyendo la fuente de `_evaluar_horizontes_proyeccion` (heredada). Aquí sobre la ruta vigente: todos los
    errores del rectángulo pasan a NaN y no debe aparecer ningún modelo ni valor proyectado finito.
    """
    df = gen.serie("tendencia_lineal_ruido")
    original = sp._matriz_rectangular_12_24

    def sin_errores_finitos(*args, **kwargs):
        matriz = original(*args, **kwargs)
        for modelo, pares in matriz["datos"].items():
            matriz["datos"][modelo] = {par: (float("nan"),) + fila[1:] for par, fila in pares.items()}
        return matriz

    with patch.object(sp, "_matriz_rectangular_12_24", side_effect=sin_errores_finitos):
        r = sp.ejecutar_proyeccion(df, *gen.objetivo(df, 11), 2020)
    assert r["proyeccion_generada"] is False
    assert not r.get("modelo_codigo")
    assert r.get("y_proj") is None or not math.isfinite(float(r["y_proj"]))
    assert "errores finitos comunes" in (r.get("explicacion") or "")


def test_la_ruta_vigente_no_referencia_el_subsistema_heredado():
    """Ninguna función de la ruta vigente nombra (llama, importa o lee) una definición heredada.

    Sustituiría test_fundamentacion_metodologica::test_la_ruta_productiva_no_invoca_el_selector_de_respaldo (lee la
    fuente de `_evaluar_horizontes_proyeccion`) y completa al espía de test_fase1a_selector_rectangular, que solo
    observa una ejecución. Se analiza el AST: comentarios y docstrings no cuentan, porque documentan historia.
    """
    usos = {}
    for nombre in RUTA_VIGENTE:
        arbol = ast.parse(textwrap.dedent(inspect.getsource(getattr(sp, nombre))))
        ids = {n.id for n in ast.walk(arbol) if isinstance(n, ast.Name)}
        ids |= {n.attr for n in ast.walk(arbol) if isinstance(n, ast.Attribute)}
        usos[nombre] = sorted(ids & set(HEREDADAS))
    assert usos == dict.fromkeys(RUTA_VIGENTE, []), usos
