"""Paleta de SAVIP en temas claro y oscuro.

Fase 4F (renovación visual): lenguaje de *dashboard técnico* inspirado en la
referencia aportada por el usuario. Barra lateral grafito continua, área de
trabajo gris muy claro, tarjetas blancas de borde discreto y pocos acentos con
significado estable:

* **Cian** (``principal``): acciones, foco y selección. El cian de la
  referencia (#13AFC0) no alcanza 4.5:1 con texto blanco, así que en claro se
  usa su variante profunda #0B7A88 y el cian luminoso queda para el acento de
  la barra lateral (#5FD4E0, sobre grafito) y los fondos suaves.
* **Violeta** (``secundario``): distinción informativa puntual y serie
  proyectada de las gráficas.
* Verde, ámbar y rojo exclusivamente para estados.

El tema oscuro es la misma estructura en grafito azulado: el fondo es el plano
más profundo y las superficies se elevan aclarando. La barra lateral es oscura
en ambos temas, por eso sus tokens ``navegacion_*`` coinciden.

Esta es la única definición de color de la interfaz; la plantilla QSS y las
gráficas la consumen por nombre de token.
"""

from __future__ import annotations

from app_icociv.interfaz.tema.tokens import (
    OPACIDAD_HOVER,
    OPACIDAD_PRESIONADO,
    OPACIDAD_SUPERFICIE,
    OPACIDAD_SUTIL,
    OPACIDAD_VELO,
)

# Tonos de la referencia, nombrados para poder citarlos desde la paleta.
REFERENCIA = {
    "grafito": "#222933",       # barra lateral
    "grafito_hover": "#303A46",
    "grafito_activo": "#3B4554",
    "cian": "#13AFC0",          # acento de la referencia (solo fondos/realces)
    "cian_profundo": "#0B7A88", # cian con contraste AA para texto blanco
    "cian_luminoso": "#5FD4E0", # acento sobre grafito
    "violeta": "#7A4BC0",
    "violeta_claro": "#B796EA",
}

CLARO: dict[str, str] = {
    # Marca
    "principal": REFERENCIA["cian_profundo"],
    "principal_intenso": "#086570",
    "principal_suave": "#E2F5F7",
    "acento_hover": "#086570",
    "acento_presionado": "#06535C",
    "secundario": REFERENCIA["violeta"],
    "secundario_suave": "#F1EBFA",
    # "acento" lo consumen los informes HTML de Resultados: se mantiene en la
    # familia cian para no introducir un segundo color de marca.
    "acento": REFERENCIA["cian_profundo"],
    "acento_suave": "#E2F5F7",
    # Estado
    "exito": "#19845B",
    "exito_suave": "#E3F4EC",
    "advertencia": "#A9620E",
    "advertencia_suave": "#FBF0E1",
    "error": "#C23D46",
    "error_suave": "#FBE9EA",
    "informacion": REFERENCIA["cian_profundo"],
    "informacion_suave": "#E2F5F7",
    # Superficies
    "fondo": "#F5F7FA",
    "fondo_secundario": "#EEF2F6",
    "barra_lateral": REFERENCIA["grafito"],
    "navegacion_texto": "#F3F6F9",
    "navegacion_secundario": "#AEB9C6",
    "navegacion_acento": REFERENCIA["cian_luminoso"],
    "navegacion_campo": "#2A323D",
    "navegacion_borde": "#36404C",
    "superficie": "#FFFFFF",
    "superficie_2": "#F7F9FB",
    "superficie_3": "#EDF1F5",
    "superficie_inversa": REFERENCIA["grafito"],
    # Tooltips: superficie clara desaturada (antes usaban la superficie inversa, casi negra).
    "tooltip_fondo": "#EEF3F7",
    "tooltip_texto": "#253746",
    "tooltip_borde": "#CAD8E2",
    # Texto
    "texto": "#26323D",
    "texto_secundario": "#56677A",
    "texto_terciario": "#728396",
    "texto_sobre_principal": "#FFFFFF",
    "texto_inverso": "#F3F6F9",
    "texto_deshabilitado": "#9AA7B4",
    # Bordes
    "borde": "#DEE6ED",
    "borde_control": "#7D8D9E",
    "borde_fuerte": "#A7B4C1",
    "deshabilitado": "#EBEFF3",
    # Datos y gráfica
    "grafica_fondo": "#FFFFFF",
    "grafica_rejilla": "#E6ECF1",
    "serie_historica": REFERENCIA["cian_profundo"],
    "serie_ajuste": "#8E9BA8",
    "serie_proyeccion": REFERENCIA["violeta"],
    "banda_intervalo": REFERENCIA["violeta"],
    "marca_calendario": "#A9620E",
    "marca_atipico": "#C23D46",
    # Interacción
    "superficie_formulario": "#FFFFFF",
    "campo": "#F8FAFC",
    "campo_hover": "#FFFFFF",
    "seleccion": "#C9EDF1",
    # Selección con la tabla sin foco: gris azulado, distinguible pero sin
    # competir con la tabla activa.
    "seleccion_inactiva": "#DCE4EC",
    "navegacion_seleccionada": REFERENCIA["grafito_activo"],
    "navegacion_hover": REFERENCIA["grafito_hover"],
    "foco": REFERENCIA["cian_profundo"],
    "sombra": "#1B2430",
}

OSCURO: dict[str, str] = {
    # Marca: los tonos luminosos sostienen el contraste sobre grafito.
    "principal": "#3CC4D2",
    "principal_intenso": "#6DD6E1",
    "principal_suave": "#123A41",
    "acento_hover": "#6DD6E1",
    "acento_presionado": "#9AE4EC",
    "secundario": REFERENCIA["violeta_claro"],
    "secundario_suave": "#2A2340",
    "acento": "#3CC4D2",
    "acento_suave": "#123A41",
    # Estado
    "exito": "#4CC397",
    "exito_suave": "#12291F",
    "advertencia": "#E0A54B",
    "advertencia_suave": "#2E2414",
    "error": "#ED8177",
    "error_suave": "#311C1C",
    "informacion": "#3CC4D2",
    "informacion_suave": "#123A41",
    # Superficies: el fondo es el plano más profundo y cada nivel aclara.
    "fondo": "#12161C",
    "fondo_secundario": "#161B22",
    "barra_lateral": "#181D25",
    "navegacion_texto": "#F3F6F9",
    "navegacion_secundario": "#AEB9C6",
    "navegacion_acento": REFERENCIA["cian_luminoso"],
    "navegacion_campo": "#222933",
    "navegacion_borde": "#2C3440",
    "superficie": "#1B2129",
    "superficie_2": "#212833",
    "superficie_3": "#28303C",
    "superficie_inversa": "#E6EBF0",
    # Tooltips: gris azulado medio (no negro ni blanco brillante).
    "tooltip_fondo": "#35495A",
    "tooltip_texto": "#F2F6FA",
    "tooltip_borde": "#617588",
    # Texto: blanco suave, nunca blanco puro.
    "texto": "#E6EBF0",
    "texto_secundario": "#A6B2BF",
    "texto_terciario": "#8592A0",
    "texto_sobre_principal": "#0A1A1E",
    "texto_inverso": "#181D25",
    "texto_deshabilitado": "#5D6977",
    # Bordes
    "borde": "#2C3440",
    "borde_control": "#6C7A8B",
    "borde_fuerte": "#5A6676",
    "deshabilitado": "#151A20",
    # Datos y gráfica
    "grafica_fondo": "#1B2129",
    "grafica_rejilla": "#2C3440",
    "serie_historica": "#3CC4D2",
    "serie_ajuste": "#8592A0",
    "serie_proyeccion": REFERENCIA["violeta_claro"],
    "banda_intervalo": REFERENCIA["violeta_claro"],
    "marca_calendario": "#E0A54B",
    "marca_atipico": "#ED8177",
    # Interacción
    "superficie_formulario": "#1A2029",
    "campo": "#0F1318",
    "campo_hover": "#141920",
    "seleccion": "#1D5058",
    "seleccion_inactiva": "#303946",
    "navegacion_seleccionada": "#2E3743",
    "navegacion_hover": "#252C36",
    "foco": "#7FDCE6",
    "sombra": "#000000",
}

TEMAS_DISPONIBLES = ("claro", "oscuro")


def normalizar_tema(tema: str | None) -> str:
    """Cualquier valor no reconocido cae en el tema claro."""
    return "oscuro" if str(tema).strip().lower() == "oscuro" else "claro"


def paleta(tema: str | None) -> dict[str, str]:
    """Devuelve una copia de la paleta del tema para evitar mutaciones externas."""
    return dict(OSCURO if normalizar_tema(tema) == "oscuro" else CLARO)


def hex_a_rgb(color: str) -> tuple[int, int, int]:
    texto = str(color).strip().lstrip("#")
    if len(texto) == 3:
        texto = "".join(c * 2 for c in texto)
    if len(texto) != 6:
        raise ValueError(f"Color hexadecimal inválido: {color!r}")
    return int(texto[0:2], 16), int(texto[2:4], 16), int(texto[4:6], 16)


def rgba(color: str, alfa: float) -> str:
    """Expresa un color con transparencia en la sintaxis que acepta QSS."""
    r, g, b = hex_a_rgb(color)
    return f"rgba({r}, {g}, {b}, {max(0.0, min(1.0, float(alfa))):.3f})"


def mezclar(color_a: str, color_b: str, proporcion: float) -> str:
    """Interpola dos colores; `proporcion` 0 devuelve el primero y 1 el segundo."""
    p = max(0.0, min(1.0, float(proporcion)))
    ra, ga, ba = hex_a_rgb(color_a)
    rb, gb, bb = hex_a_rgb(color_b)
    return "#{:02x}{:02x}{:02x}".format(
        round(ra + (rb - ra) * p),
        round(ga + (gb - ga) * p),
        round(ba + (bb - ba) * p),
    )


def _luminancia_relativa(color: str) -> float:
    """Luminancia relativa según WCAG 2.1."""

    def canal(v: int) -> float:
        s = v / 255.0
        return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4

    r, g, b = hex_a_rgb(color)
    return 0.2126 * canal(r) + 0.7152 * canal(g) + 0.0722 * canal(b)


def contraste(color_a: str, color_b: str) -> float:
    """Razón de contraste WCAG entre dos colores (1.0 a 21.0)."""
    la, lb = _luminancia_relativa(color_a), _luminancia_relativa(color_b)
    claro, oscuro = max(la, lb), min(la, lb)
    return (claro + 0.05) / (oscuro + 0.05)


def derivados(tema: str | None) -> dict[str, str]:
    """Colores compuestos que dependen de la paleta base.

    Se calculan una sola vez por tema en lugar de repetir expresiones rgba() por
    toda la hoja de estilos.
    """
    p = paleta(tema)
    return {
        "hover_principal": rgba(p["principal"], OPACIDAD_HOVER),
        "presionado_principal": rgba(p["principal"], OPACIDAD_PRESIONADO),
        "hover_superficie": rgba(p["texto"], OPACIDAD_SUTIL),
        "velo_superficie": rgba(p["superficie"], OPACIDAD_VELO),
        "velo_fondo": rgba(p["fondo"], OPACIDAD_VELO),
        "cabecera_fondo": rgba(p["superficie"] if normalizar_tema(tema) == "claro" else p["barra_lateral"], 0.94),
        "separador": rgba(p["borde"], 0.85),
        "sombra_suave": rgba(p["sombra"], OPACIDAD_SUPERFICIE),
    }
