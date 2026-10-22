"""Formato de salida ICOCIV; nunca transforma los datos de cálculo o exportación."""

import math
from numbers import Real
import re


def numero_ui(valor, decimales=3, ausente="No disponible"):
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return ausente
    if not math.isfinite(numero):
        return ausente
    decimales = min(3, max(0, decimales))
    texto = f"{numero:,.{decimales}f}"
    if decimales:
        texto = texto.rstrip("0").rstrip(".")
    if texto in ("0", "-0") and numero != 0:
        limite = f"{10 ** -decimales:.{decimales}f}"
        return f"< {limite}" if numero > 0 else f"> -{limite}"
    return "0" if texto == "-0" else texto


def pesos_ui(valor, ausente="No disponible"):
    """Pesos colombianos enteros para MOSTRAR (redondeo al peso, mitad hacia arriba).

    Solo presentación: el valor interno conserva su precisión completa.
    """
    from decimal import Decimal, ROUND_HALF_UP
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return ausente
    if not math.isfinite(numero):
        return ausente
    entero = int(Decimal(repr(numero)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return f"{entero:,}"


def porcentaje_ui(valor, ausente="No disponible"):
    """Porcentaje con máximo dos decimales, redondeado (no truncado)."""
    return numero_ui(valor, 2, ausente)


def detalle_ui(valor):
    if isinstance(valor, Real) and not isinstance(valor, bool):
        return numero_ui(valor, ausente="")
    if isinstance(valor, dict):
        return " · ".join(f"{k}: {detalle_ui(v)}" for k, v in valor.items())
    if isinstance(valor, (tuple, list)):
        return ", ".join(detalle_ui(v) for v in valor)
    return str(valor)


def formula_ui(texto):
    return re.sub(r"(?<![\w.])[-+]?\d+\.\d+(?:[eE][+-]?\d+)?(?![\w.])",
                  lambda m: numero_ui(m.group()), str(texto))


def numero_tecnico_ui(valor):
    """Las filas técnicas anteriores almacenan cifras es-CO como texto."""
    if isinstance(valor, str):
        texto = valor.replace("$", "").replace("%", "").strip()
        if "," in texto:
            texto = texto.replace(".", "").replace(",", ".")
        formato = numero_ui(texto, ausente="")
        return ("$ " if "$" in valor else "") + formato + (" %" if "%" in valor else "") if formato else valor
    return numero_ui(valor, ausente="")
