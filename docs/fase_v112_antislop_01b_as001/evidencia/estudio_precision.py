"""Fase 1B: precisión del RMSE informado en el camino de desbordamiento (AS-001)."""
import math
import random
import sys
import time
from decimal import Decimal, localcontext
from fractions import Fraction

sys.path.insert(0, sys.argv[1])
from app_icociv.proyeccion import servicio_proyeccion as sp  # noqa: E402


def referencia(errores):
    sse = sum(Fraction(e) ** 2 for e in errores)
    with localcontext() as ctx:
        ctx.prec = 100
        return float((Decimal(sse.numerator) / Decimal(sse.denominator) / len(errores)).sqrt())


def escalado(errores):  # alternativa descartada: reescalar por max|e| en flotante
    s = max(abs(e) for e in errores)
    return s * math.sqrt(sum((e / s) ** 2 for e in errores) / len(errores))


def ulps(x, ref):
    return abs(x - ref) / math.ulp(ref)


rng = random.Random(20261026)
casos = 0
peor_fix = peor_esc = 0.0
distintos_fix = distintos_esc = 0
desbordes = 0
t_fix = 0.0
for _ in range(20000):
    n = rng.choice((2, 24, 48, 240, 480))
    exp = rng.uniform(155, 308.2)
    errores = [rng.choice((-1, 1)) * rng.uniform(0.01, 1.0) * 10 ** min(exp, 308.25) for _ in range(n)]
    errores = [e for e in errores if math.isfinite(e)]
    sse = sp._sse_exacto(errores)
    t0 = time.perf_counter()
    r = sp._rmse_desde_sse(sse, len(errores))
    t_fix += time.perf_counter() - t0
    try:
        float(sse)
    except OverflowError:
        desbordes += 1
    ref = referencia(errores)
    assert math.isfinite(r)
    u = ulps(r, ref)
    peor_fix = max(peor_fix, u)
    distintos_fix += r != ref
    v = escalado(errores)
    w = ulps(v, ref)
    peor_esc = max(peor_esc, w)
    distintos_esc += v != ref
    casos += 1

# Rango ordinario: la alternativa de escalado cambiaría bits respecto a la expresión de siempre.
cambia_ordinario = 0
for _ in range(20000):
    n = rng.choice((2, 24, 240))
    errores = [rng.gauss(0, 10 ** rng.uniform(-6, 6)) for _ in range(n)]
    original = math.sqrt(float(sp._sse_exacto(errores)) / n)
    assert sp._rmse_desde_sse(sp._sse_exacto(errores), n) == original
    cambia_ordinario += escalado(errores) != original

print(f"casos extremos: {casos}, con float(sse) desbordado: {desbordes}")
print(f"corrección (Decimal 60 dígitos): peor error {peor_fix:.3f} ULP, distintos del redondeo correcto: {distintos_fix}")
print(f"alternativa escalado max|e|: peor error {peor_esc:.3f} ULP, distintos del redondeo correcto: {distintos_esc}")
print(f"tiempo medio del camino Decimal: {t_fix / casos * 1e6:.1f} us por candidato")
print(f"rango ordinario (20000 casos): corrección idéntica bit a bit en todos; escalado difiere en {cambia_ordinario}")
